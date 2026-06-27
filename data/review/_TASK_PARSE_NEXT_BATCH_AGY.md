# Контракт для ИИ-агента: парсинг очередной партии судебных актов

Этот файл — повторяемый контракт. Его задача: позволить любому ИИ-агенту после короткой команды пользователя вроде «Восстанови контекст. Сделай парсинг очередной партии судебных актов» самостоятельно найти точку продолжения, при необходимости создать новый batch-каталог и пройти весь цикл без дополнительных инструкций.

Имя файла историческое (`_AGY`), но содержание универсально для любого ИИ-агента.

## 0. Границы самостоятельных решений

Общий контекст проекта агент восстанавливает по стандартной архитектуре памяти проекта. Этот файл не дублирует общий протокол старта, а регулирует только парсинг очередной партии.

Если нужно принять решение, не описанное прямо здесь, сначала сверяйся с `memory/topic-parsing-strategy.md`.

Если решение меняет источник, лимиты, JSON-схему, контракт структурирования, критерии включения/hold или общий технологический подход — остановись и запроси подтверждение пользователя.

## 1. Общий принцип

Работа должна быть идемпотентной:

- не скачивать повторно уже известные дела;
- не перегенерировать готовые `user_story_*.md`, `practice_*.md`, `structure_*.json` без явной причины;
- не начинать новую партию, если есть незавершённая;
- при остановке всегда оставлять `batch_state.md`, по которому следующий агент сможет продолжить без догадок.

## 2. Найти или создать batch

Рабочие партии лежат в:

```text
data/parse_batches/
```

### 2.1. Сначала найди активную незавершённую партию

Просмотри все файлы:

```text
data/parse_batches/*/batch_state.md
```

Если есть партия, где `current_phase` не равен одному из финальных статусов:

- `structuring_complete`
- `complete`
- `aborted`

продолжай именно её.

Фазы, которые считаются незавершёнными:

- `initialized`
- `candidate_search`
- `ready_for_fetch`
- `fetching`
- `raw_fetched`
- `queue_prepared`
- `structuring`
- `validation_failed`
- `paused`

Если несколько незавершённых партий — остановись и попроси пользователя выбрать.

### 2.2. Если активной партии нет — создай новую

Создай каталог:

```text
data/parse_batches/YYYY-MM-DD-zpp-next/
```

Если такой каталог уже есть, добавь суффикс:

```text
data/parse_batches/YYYY-MM-DD-zpp-next-2/
data/parse_batches/YYYY-MM-DD-zpp-next-3/
```

В новой папке создай:

- `README.md`
- `batch_state.md`

Минимальный `README.md`:

```md
# Batch: <batch-id>

Рабочая папка партии парсинга и структурирования дел ЗоЗПП.

Канонический контракт: `data/review/_TASK_PARSE_NEXT_BATCH_AGY.md`.

## Роль файлов

- `search_*.csv` — сырые результаты отдельных поисковых запросов.
- `new_candidates.csv` — новые URL-кандидаты после дедупликации.
- `new_candidates_merged.csv` — объединённый актуальный CSV, если было несколько поисков.
- `fetch_report.csv` — отчёт по скачиванию raw-актов.
- `structure_report.csv` — отчёт по структурированию.
- `batch_state.md` — точка возобновления.
```

Минимальный `batch_state.md`:

```md
# Batch state: <batch-id>

- current_phase: initialized
- priority_basis: null
- priority_clusters: []
- active_candidates_csv: null
- registry_updated_at: null
- raw_downloaded_new: 0
- raw_skipped_existing: 0
- structured_new: 0
- hold_new: 0
- needs_human: 0
- last_processed_docid: null
- next_action: обновить реестр и сформировать кандидатов
- blockers: none

Следующая команда:

```powershell
python scripts\build_case_registry.py
```
```

## 3. Обновить реестр и дедупликацию

Перед поиском и перед скачиванием всегда обнови реестр:

```powershell
python scripts\build_case_registry.py
```

Реестр:

```text
data/registry/case_registry.csv
```

Не fetch-ить дело, если:

- `docid` уже есть в реестре;
- или `data/raw_acts/act_<docid>.txt` уже существует;
- или `data/structured/structure_<docid>.json` уже существует с `processing.status: "complete"`.

Подробнее: `memory/topic-parsing-deduplication.md`.

## 4. Сформировать кандидатов

### 4.1. Сначала проверь уже имеющиеся CSV

Если в batch-папке уже есть `new_candidates.csv` или `new_candidates_merged.csv`, не перезаписывай его автоматически. Проверь:

- сколько там строк;
- не скачаны ли они уже;
- соответствует ли `batch_state.md` фактическому состоянию.

Если CSV есть и по нему ещё не выполнен fetch, переходи к скачиванию.

### 4.2. Если кандидатов нет — выполни поиск

Основной источник ближайших партий:

```text
sudact.ru/regular/doc/
```

Поисковые запросы бери из `memory/topic-parsing-strategy.md` и из списка ниже.

Каждый запрос сохраняй в отдельный CSV:

```powershell
python scripts\find_cases.py --query "<запрос>" --pages 3 --output data\parse_batches\<batch-id>\search_<slug>.csv
```

Если нет ключа `YANDEX_API_KEY` или поиск недоступен — остановись, зафиксируй blocker в `batch_state.md`.

### 4.3. Объедини и отфильтруй кандидатов

После одного или нескольких поисков создай/обнови актуальный CSV:

```powershell
python scripts\filter_case_candidates.py --input data\parse_batches\<batch-id>\search_<slug_1>.csv --input data\parse_batches\<batch-id>\search_<slug_2>.csv --output data\parse_batches\<batch-id>\new_candidates.csv
```

Если добавляешь новые поисковые CSV к уже существующему `new_candidates.csv`, пиши результат в:

```text
new_candidates_merged.csv
```

и укажи этот файл как `active_candidates_csv` в `batch_state.md`.

## 5. Приоритеты поиска

Цель партий — не максимум актов, а усиление слабых и перспективных ситуаций.

Перед поиском определи текущие приоритеты:

1. Посчитай дела по `taxonomy.dispute_type_code` во всех `data/structured/structure_*.json`.
2. Основной счёт веди по публикационно пригодным делам: `publication.index_policy == "index"` и `publication.main_site_fit == true`.
3. Высший приоритет — кластеры с 0–5 пригодными делами и новые повторяющиеся ЗоЗПП-ситуации.
4. Средний приоритет — кластеры с 6–10 пригодными делами.
5. Сильные кластеры добирай только точечно: если новые дела дают новый подтип, регион, компанию, объект, исход или правовую ситуацию.
6. Если встретилась повторяющаяся ЗоЗПП-ситуация вне текущего словаря, не меняй словарь сам: зафиксируй кандидат на новый кластер в отчёте партии.

Перечень кластеров открытый. Не считай список `dispute_type_code` закрытым навсегда.

Базовые запросы ниже — стартовый набор, а не обязательный закрытый список. Выбирай и адаптируй их по текущим приоритетам:

```text
site:sudact.ru/regular/doc/ "статья 29" "защите прав потребителей" "окна"
site:sudact.ru/regular/doc/ "статья 29" "защите прав потребителей" "мебель на заказ"
site:sudact.ru/regular/doc/ "статья 29" "защите прав потребителей" "ремонт"
site:sudact.ru/regular/doc/ "недостатки выполненной работы" "защите прав потребителей"
site:sudact.ru/regular/doc/ "статья 28" "защите прав потребителей" "срок выполнения работ"
site:sudact.ru/regular/doc/ "нарушение срока выполнения работ" "защите прав потребителей"
site:sudact.ru/regular/doc/ "статья 26.1" "защите прав потребителей" "маркетплейс"
site:sudact.ru/regular/doc/ "дистанционным способом" "возврат товара" "защите прав потребителей"
site:sudact.ru/regular/doc/ "статья 10" "статья 12" "защите прав потребителей" "недостоверная информация"
site:sudact.ru/regular/doc/ "статья 32" "защите прав потребителей" "онлайн-курс"
site:sudact.ru/regular/doc/ "статья 32" "защите прав потребителей" "страховка"
site:sudact.ru/regular/doc/ "статья 23.1" "защите прав потребителей" "предварительная оплата"
```

Регионы пока не квотировать жёстко. Регион фиксировать в отчёте.

## 6. Лимиты партии

Если пользователь не дал иных лимитов:

- найти после дедупликации: 100–150 URL-кандидатов;
- скачать raw-акты: максимум 80–100;
- структурировать: максимум 50–60 дел;
- целевой результат: около 50 новых структурированных дел.

Если в партии уже достигнуты лимиты — не расширяй её самовольно. Заверши партию и укажи следующий шаг.

Если заканчиваются лимиты среды, модели или сессии — остановись на ближайшей безопасной точке и обнови `batch_state.md`.

## 7. Скачать raw-акты

Скачивай из актуального CSV:

```powershell
python scripts\extract_act_text.py --csv <active_candidates_csv> --output-dir data\raw_acts --limit 100 --delay 1.0
```

`extract_act_text.py` по умолчанию пропускает уже существующие `act_<docid>.txt`.

После fetch:

```powershell
python scripts\build_case_registry.py
python scripts\queue_for_agent.py
python scripts\queue_for_agent.py --status
```

Создай или обнови:

```text
<batch-dir>/fetch_report.csv
```

Минимальные поля:

- `docid`
- `source_url`
- `status`: `fetched`, `skipped_existing`, `fetch_error`, `not_target`
- `raw_act_path`
- `raw_text_sha256`
- `note`

Обнови `batch_state.md`:

- `current_phase: raw_fetched` или `paused`;
- `raw_downloaded_new`;
- `raw_skipped_existing`;
- `next_action`.

## 8. Структурировать акты

Структурируй только новые pending-акты текущей партии.

Ориентиры:

- `active_candidates_csv`;
- `fetch_report.csv`;
- `data/inbox/_queue.json`;
- наличие/отсутствие тройки файлов в `data/structured/`.

Для каждого акта используй контракт:

```text
data/inbox/_TASK.md
```

На каждый акт должны появиться:

- `data/structured/user_story_<docid>.md`
- `data/structured/practice_<docid>.md`
- `data/structured/structure_<docid>.json`

Не помечай запись в `_queue.json` как `done`, пока все три файла не созданы и не прошли самопроверку.

Создай или обнови:

```text
<batch-dir>/structure_report.csv
```

Минимальные поля:

- `docid`
- `status`: `structured`, `hold`, `needs_human`, `error`
- `dispute_type_code`
- `claim_type_codes`
- `result_type`
- `index_policy`
- `main_site_fit`
- `validation_status`
- `verification_status`
- `note`

## 9. Критерии index / hold

В индекс подходят:

- гражданские дела судов общей юрисдикции;
- потребитель — гражданин;
- спор относится к ЗоЗПП;
- есть полезная фактическая ситуация;
- дело усиливает один из целевых кластеров.

Ставь `publication.index_policy: "hold"` и `publication.main_site_fit: false`, если:

- спор между юрлицами/ИП без потребительского контекста;
- арбитражное/хозяйственное дело;
- дело не относится к ЗоЗПП;
- акт почти полностью процессуальный;
- текст битый/слишком короткий;
- правовая природа сомнительна и без человека рискованно включать дело в индекс.

Если raw уже скачан, hold-дело всё равно лучше минимально структурировать, чтобы оно попало в реестр и не возвращалось повторно.

## 10. Проверки

После структурирования партии:

```powershell
python scripts\validate_structures.py
python scripts\verify_all.py
python scripts\build_case_registry.py
```

Если проверки не проходят:

- не скрывай ошибку;
- обнови `batch_state.md`;
- укажи проблемные `docid`;
- остановись или исправь только очевидную локальную проблему.

## 11. Завершение партии

Партия считается завершённой, когда:

- новые raw-акты скачаны или корректно пропущены;
- новые акты структурированы либо явно отмечены как `hold`/`needs_human`/`error`;
- `validate_structures.py` и `verify_all.py` проходят либо ошибки явно зафиксированы;
- `data/registry/case_registry.csv` обновлён;
- `fetch_report.csv`, `structure_report.csv`, `batch_state.md` актуальны.

Финальный `batch_state.md` должен содержать:

```md
- current_phase: structuring_complete
- priority_basis:
- priority_clusters:
- active_candidates_csv:
- registry_updated_at:
- raw_downloaded_new:
- raw_skipped_existing:
- structured_new:
- hold_new:
- needs_human:
- last_processed_docid:
- next_action:
- blockers:
```

`next_action` после завершения партии обычно:

```text
пересобрать SSG-прототип и оценить покрытие кластеров
```

## 12. Что нельзя делать без отдельного подтверждения

- Удалять существующие raw/structured-файлы.
- Перегенерировать готовые артефакты старых дел.
- Менять JSON-схему.
- Менять `data/inbox/_TASK.md`.
- Подключать новый источник судебных актов.
- Расширять лимиты партии сверх заданных.
- Использовать внешний LLM API, если задача дана агентной среде с собственной моделью и пользователь не разрешил API явно.
- Делать git commit.

## 13. Итоговый отчёт агенту-человеку

В конце сообщи:

1. какой batch-каталог использован;
2. сколько новых кандидатов найдено после дедупликации;
3. сколько raw-актов скачано;
4. сколько дел структурировано;
5. сколько дел ушло в hold / needs_human / error;
6. какие кластеры усилены;
7. распределение по регионам;
8. результаты `validate_structures.py` и `verify_all.py`;
9. точную точку продолжения, если работа не завершена.
