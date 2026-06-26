# Задача для ИИ-агента: следующая партия парсинга и структурирования дел ЗоЗПП

Дата постановки: 2026-06-26  
Рабочая папка партии: `data/parse_batches/2026-06-26-zpp-next/`

## 0. Восстановление контекста

Перед стартом прочитай:

1. `START-HERE.md`
2. `memory/current-work-queue.md`
3. `memory/topic-parsing-strategy.md`
4. `memory/topic-parsing-deduplication.md`
5. `data/review/_TASK_PARSE_NEXT_BATCH_AGY.md` — этот файл
6. `data/inbox/_TASK.md` — контракт структурирования одного raw-акта
7. `data/reference/zpp_enum_dictionary.json`

Если работа уже начата другим агентом, не начинай заново. Сначала прочитай:

- `data/parse_batches/2026-06-26-zpp-next/batch_state.md`, если есть;
- `data/parse_batches/2026-06-26-zpp-next/new_candidates.csv`, если есть;
- `data/parse_batches/2026-06-26-zpp-next/fetch_report.csv`, если есть;
- `data/parse_batches/2026-06-26-zpp-next/structure_report.csv`, если есть;
- `data/inbox/_queue.json`.

Продолжай с первого незавершённого шага.

Если в ходе работы нужно принять решение, не описанное прямо в этом файле, сначала сверяйся с `memory/topic-parsing-strategy.md`. Если решение меняет источник, лимиты, JSON-схему, контракт структурирования или критерии включения/hold — остановись и запроси подтверждение пользователя.

## 1. Цель партии

Расширить корпус судебных актов по защите прав потребителей для следующих страниц/кластеров:

1. `distance_sale_return_art26_1` — дистанционная продажа, отказ от товара, возврат денег.
2. `info_violation_art10_12` — недостоверная/неполная информация, цена, продавец, характеристики.
3. `service_refusal_art32` — отказ от услуги, курса, страховки, сервиса, сертификата.
4. `prepaid_goods_delay_art23_1` — предоплата, товар не передан или задержан.
5. `work_service_defect_art29` — недостатки работ/услуг: окна, двери, мебель на заказ, ремонт, установка.
6. `goods_defect_art18` — товар с недостатком; только дозаполнение, не основной фокус.

Регионы пока не квотировать жёстко. Регион фиксировать как метаданные и отразить распределение в отчёте.

## 2. Лимиты партии

Жёсткие лимиты:

- не скачивать больше 100 новых raw-актов;
- не структурировать больше 60 новых дел;
- целевой объём структурирования: 50 новых дел;
- если 3 подряд сетевых ошибки или блокер с ключами/API — остановиться и описать точку продолжения;
- не трогать уже готовые 50 дел, кроме чтения и дедупликации.

Если заканчиваются лимиты среды, модели или агентной сессии, остановись на ближайшей безопасной точке и обнови `batch_state.md`.

## 3. Дедупликация и реестр

Перед любыми поисками/скачиванием обнови реестр:

```powershell
python scripts\build_case_registry.py
```

Основной реестр:

- `data/registry/case_registry.csv`

Ключи дедупликации:

1. `docid` из `https://sudact.ru/regular/doc/<docid>/`
2. нормализованный `source_url` без хвостового `/`
3. `raw_text_sha256` после скачивания

Не fetch-ить дело, если:

- `docid` уже есть в `data/registry/case_registry.csv`;
- или `data/raw_acts/act_<docid>.txt` уже существует;
- или `data/structured/structure_<docid>.json` уже существует с `processing.status: "complete"`.

## 4. Стартовая партия кандидатов

Сначала используй уже найденные ранее кандидаты:

- вход: `output/cases_ozon_regular.csv`
- после дедупликации должно остаться около 37 новых кандидатов.

Команда:

```powershell
python scripts\filter_case_candidates.py --input output\cases_ozon_regular.csv --output data\parse_batches\2026-06-26-zpp-next\new_candidates.csv
```

Если `new_candidates.csv` уже есть, не перезаписывай без причины: сначала проверь, что в нём.

## 5. Добор поиском

Если после стартовых 37 кандидатов raw-актов меньше целевого диапазона 80–100, добери поиском по `sudact.ru/regular/doc/`.

Используй отдельный CSV на каждый поисковый запрос:

```powershell
python scripts\find_cases.py --query "<запрос>" --pages 3 --output data\parse_batches\2026-06-26-zpp-next\search_<slug>.csv
```

Потом объединяй и фильтруй:

```powershell
python scripts\filter_case_candidates.py --input data\parse_batches\2026-06-26-zpp-next\new_candidates.csv --input data\parse_batches\2026-06-26-zpp-next\search_<slug>.csv --output data\parse_batches\2026-06-26-zpp-next\new_candidates_merged.csv
```

Если делаешь merge, дальше работай с последним актуальным CSV и укажи это в `batch_state.md`.

### Приоритетные поисковые запросы

Дистанционная продажа:

- `site:sudact.ru/regular/doc/ "статья 26.1" "защите прав потребителей" "маркетплейс"`
- `site:sudact.ru/regular/doc/ "дистанционным способом" "возврат товара" "защите прав потребителей"`
- `site:sudact.ru/regular/doc/ "Wildberries" "статья 26.1" "защите прав потребителей"`
- `site:sudact.ru/regular/doc/ "Ozon" "статья 26.1" "защите прав потребителей"`

Недостоверная информация:

- `site:sudact.ru/regular/doc/ "статья 10" "статья 12" "защите прав потребителей" "недостоверная информация"`
- `site:sudact.ru/regular/doc/ "непредоставление информации" "продавец" "защите прав потребителей"`
- `site:sudact.ru/regular/doc/ "цена товара" "статья 12" "защите прав потребителей"`

Отказ от услуги:

- `site:sudact.ru/regular/doc/ "статья 32" "защите прав потребителей" "онлайн-курс"`
- `site:sudact.ru/regular/doc/ "статья 32" "защите прав потребителей" "страховка"`
- `site:sudact.ru/regular/doc/ "статья 32" "защите прав потребителей" "сертификат"`
- `site:sudact.ru/regular/doc/ "отказ от услуги" "возврат денег" "защите прав потребителей"`

Предоплата и задержка товара:

- `site:sudact.ru/regular/doc/ "статья 23.1" "защите прав потребителей" "предварительная оплата"`
- `site:sudact.ru/regular/doc/ "оплаченный товар" "не передан" "защите прав потребителей"`
- `site:sudact.ru/regular/doc/ "предоплата" "не поставил товар" "защите прав потребителей"`

Недостатки работ/услуг:

- `site:sudact.ru/regular/doc/ "статья 29" "защите прав потребителей" "окна"`
- `site:sudact.ru/regular/doc/ "статья 29" "защите прав потребителей" "мебель на заказ"`
- `site:sudact.ru/regular/doc/ "статья 29" "защите прав потребителей" "ремонт"`
- `site:sudact.ru/regular/doc/ "недостатки выполненной работы" "защите прав потребителей"`

Товар с недостатком — только дозаполнение:

- `site:sudact.ru/regular/doc/ "статья 18" "защите прав потребителей" "маркетплейс"`
- `site:sudact.ru/regular/doc/ "технически сложный товар" "статья 18" "защите прав потребителей"`

## 6. Скачивание raw-актов

Скачивай из актуального CSV кандидатов:

```powershell
python scripts\extract_act_text.py --csv data\parse_batches\2026-06-26-zpp-next\new_candidates.csv --output-dir data\raw_acts --limit 100 --delay 1.0
```

Если работа возобновляется, не скачивай заново уже существующие `data/raw_acts/act_<docid>.txt`: `extract_act_text.py` по умолчанию пропускает такие файлы.

После скачивания:

```powershell
python scripts\build_case_registry.py
python scripts\queue_for_agent.py
python scripts\queue_for_agent.py --status
```

Создай/обнови `fetch_report.csv` в рабочей папке партии.

Минимальные поля `fetch_report.csv`:

- `docid`
- `source_url`
- `status`: `fetched`, `skipped_existing`, `fetch_error`, `not_target`
- `raw_act_path`
- `raw_text_sha256`
- `note`

## 7. Структурирование raw-актов

Структурируй только pending-акты из `data/inbox/_queue.json`, относящиеся к новой партии.

Используй контракт:

- `data/inbox/_TASK.md`

На каждый акт должны появиться три файла:

- `data/structured/user_story_<docid>.md`
- `data/structured/practice_<docid>.md`
- `data/structured/structure_<docid>.json`

Не помечай запись в `_queue.json` как `done`, пока все три файла не созданы и не прошли самопроверку.

После структурирования запускай:

```powershell
python scripts\validate_structures.py
python scripts\verify_all.py
python scripts\build_case_registry.py
```

Создай/обнови `structure_report.csv`.

Минимальные поля `structure_report.csv`:

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

## 8. Критерии включения и hold

В основной индекс подходят:

- гражданские дела судов общей юрисдикции;
- потребитель — гражданин;
- спор реально относится к ЗоЗПП;
- есть содержательная ситуация, полезная для одной из целевых страниц.

Ставь `publication.index_policy: "hold"` и `publication.main_site_fit: false`, если:

- спор между юрлицами/ИП без потребительского контекста;
- арбитражное/хозяйственное дело;
- дело не про ЗоЗПП;
- акт слишком процессуальный и не содержит полезной фактуры;
- качество текста не позволяет безопасно извлечь структуру.

Hold-дела всё равно структурируй минимально, если raw уже скачан, чтобы они были учтены и не всплывали повторно.

## 9. Batch-state и handoff

Создай и регулярно обновляй:

- `data/parse_batches/2026-06-26-zpp-next/batch_state.md`

Минимальный шаблон:

```md
# Batch state: 2026-06-26-zpp-next

- current_phase:
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

Если останавливаешься из-за лимита, ошибки или конца сессии, последней строкой в `batch_state.md` укажи точную команду/действие для следующего агента.

## 10. Что нельзя делать

- Не удаляй существующие raw/structured-файлы.
- Не перегенерируй готовые `user_story_*.md`, `practice_*.md`, `structure_*.json` без явной причины.
- Не меняй `data/inbox/_TASK.md` и memory-файлы без отдельного подтверждения пользователя.
- Не коммить изменения без отдельного подтверждения пользователя.
- Не используй внешний LLM API без отдельного разрешения пользователя. Если задача выполняется в агентной среде с собственной моделью, структурирование выполняй силами этой среды.

## 11. Итоговый отчёт

В конце сообщи:

1. сколько новых кандидатов найдено после дедупликации;
2. сколько raw-актов скачано;
3. сколько дел структурировано;
4. сколько дел ушло в hold;
5. какие кластеры усилены;
6. распределение по регионам;
7. результаты `validate_structures.py` и `verify_all.py`;
8. где остановился и что делать следующему агенту.
