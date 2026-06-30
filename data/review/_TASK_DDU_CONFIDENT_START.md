# Задача для агента: первая партия судебных актов по ДДУ

## Цель

Начать наполнение `ddu-online.ru` судебной практикой по ДДУ/долевому строительству в режиме **уверенного старта**.

Ориентир полного старта:

- 150–250 валидных дел;
- 8–12 страниц-ситуаций;
- 3–5 сильных страниц с 20+ делами.

Эта задача — первая партия, не весь корпус сразу.

## Важные ограничения

- Не использовать внешние LLM API, платные API или скрипты, вызывающие такие API, без отдельного явного разрешения пользователя в текущей задаче.
- Не смешивать ДДУ-данные с текущим ЗоПП-корпусом.
- Не менять enum-словарь молча. Если встретилась повторяемая новая ситуация вне словаря — зафиксировать кандидата в отчёте партии.
- Все создаваемые `.md`, `.json`, `.csv`, `.txt` сохранять в UTF-8. Перед сдачей партии обязательно запустить strict-проверку кодировки из раздела «Проверки». Если валидатор находит mojibake/сломанные символы, не считать задачу завершённой: исправить артефакты или явно зафиксировать блокер.

## Канонические файлы для этой задачи

- Словарь ситуаций: `data/reference/ddu_enum_dictionary.json`.
- План наполнения: `memory/topic-ddu-online-fill-plan.md`.
- Общий контракт парсинга: `memory/topic-parsing-strategy.md`.
- DDU user story prompt: `scripts/prompt_user_story_ddu.txt`.
- DDU structure prompt: `scripts/prompt_extract_ddu.txt`.
- Правовой разбор: `scripts/prompt_practice_analysis.txt`.
- Конфиг сайта: `sites/ddu/site.json`.

## Рабочие каталоги

Использовать отдельный DDU-слой:

- batch: `data/ddu/parse_batches/YYYY-MM-DD-ddu-001/`;
- raw acts: `data/ddu/raw_acts/`;
- structured: `data/ddu/structured/`;
- inbox queue: `data/ddu/inbox/_queue.json`;
- registry: `data/ddu/registry/case_registry.csv`.

## Приоритеты первой партии

Собирать судебные акты по приоритетам:

1. Просрочка передачи квартиры / неустойка.
2. Претензия и иск к застройщику.
3. Расторжение ДДУ / возврат денег.
4. Недостатки квартиры / качество объекта.
5. Приёмка квартиры с недостатками.
6. Площадь квартиры / доплаты / перерасчёт.
7. Эскроу и банкротство — только если находятся понятные и полезные гражданские ситуации.

## Размер первой партии

Целевой объём первой партии:

- найти 80–120 кандидатов;
- скачать 50–80 новых судебных актов;
- структурировать столько актов, сколько позволяет лимит агента, но не менее 20, если лимит не исчерпан;
- по итогам дать отчёт, сколько дел реально подходит для индекса.

Если лимиты заканчиваются — остановиться в чистом состоянии и оставить отчёт, где именно продолжать.

## Поиск

Перед поиском обновить DDU-реестр:

```powershell
python scripts/build_case_registry.py --raw-dir data/ddu/raw_acts --structured-dir data/ddu/structured --output data/ddu/registry/case_registry.csv
```

Использовать Yandex Search API через существующий скрипт, если доступны ключи:

```powershell
python scripts/find_cases.py --query "<запрос>" --output data/ddu/parse_batches/YYYY-MM-DD-ddu-001/search_<slug>.csv --pages 2 --registry data/ddu/registry/case_registry.csv
```

Если ключи недоступны, сформировать запросы и зафиксировать блокер в отчёте.

Базовые запросы:

```text
site:sudact.ru/regular/doc/ "214-ФЗ" "неустойка" "застройщик"
site:sudact.ru/regular/doc/ "договор участия в долевом строительстве" "неустойка"
site:sudact.ru/regular/doc/ "просрочка передачи квартиры" "застройщик" "неустойка"
site:sudact.ru/regular/doc/ "статья 6" "214-ФЗ" "неустойка"
site:sudact.ru/regular/doc/ "претензия застройщику" "ДДУ"
site:sudact.ru/regular/doc/ "иск к застройщику" "ДДУ"
site:sudact.ru/regular/doc/ "расторжение договора участия в долевом строительстве"
site:sudact.ru/regular/doc/ "статья 9" "214-ФЗ" "расторжение"
site:sudact.ru/regular/doc/ "недостатки квартиры" "застройщик" "214-ФЗ"
site:sudact.ru/regular/doc/ "статья 7" "214-ФЗ" "недостатки"
site:sudact.ru/regular/doc/ "акт приема-передачи" "недостатки" "застройщик"
site:sudact.ru/regular/doc/ "статья 8" "214-ФЗ" "акт приема-передачи"
site:sudact.ru/regular/doc/ "площадь квартиры" "ДДУ" "застройщик"
site:sudact.ru/regular/doc/ "доплата за площадь" "ДДУ"
site:sudact.ru/regular/doc/ "эскроу" "ДДУ" "застройщик"
site:sudact.ru/regular/doc/ "банкротство застройщика" "дольщик"
```

Перед скачиванием актов провести лёгкий отбор кандидатов:

- целевой кандидат должен содержать сильные признаки ДДУ/214-ФЗ: `214-ФЗ`, `договор участия в долевом строительстве`, `ДДУ`, `участник долевого строительства`, `дольщик`, `застройщик`;
- желательно наличие признака конкретной ситуации: `неустойка`, `просрочка передачи`, `расторжение`, `недостатки`, `акт приема-передачи`, `площадь`, `эскроу`;
- очевидно нецелевые кандидаты не скачивать полностью, но фиксировать в отчёте как `rejected_before_fetch` с причиной;
- сомнительные кандидаты не удалять: помечать как `maybe_target` и включать в небольшую контрольную выборку, чтобы не потерять потенциально целевые дела;
- в `batch_state.md` указать эффективность запросов: сколько кандидатов найдено, сколько скачано, сколько стало `index`, сколько ушло в `hold`.

## Скачивание актов

```powershell
python scripts/extract_act_text.py --csv data/ddu/parse_batches/YYYY-MM-DD-ddu-001/new_candidates.csv --output-dir data/ddu/raw_acts --limit 80 --delay 1
```

## Очередь обработки

```powershell
python scripts/queue_for_agent.py --raw-dir data/ddu/raw_acts --queue data/ddu/inbox/_queue.json
```

## Структурирование

Для каждого обработанного акта создать:

- `data/ddu/structured/user_story_<docid>.md`;
- `data/ddu/structured/practice_<docid>.md`;
- `data/ddu/structured/structure_<docid>.json`.

В JSON:

- `taxonomy.legal_domain = "shared_construction"`;
- `taxonomy.topic_vertical = "ddu"`;
- `parties.focus_party.role = "shareholder"`, если фокусная сторона — дольщик/участник долевого строительства;
- `taxonomy.dispute_type_code` и `taxonomy.claim_type_codes` брать только из `data/reference/ddu_enum_dictionary.json`;
- source-поля брать из `.meta.json`, не придумывать.

## Проверки

После обработки запустить:

```powershell
python scripts/validate_structures.py --raw-dir data/ddu/raw_acts --structured-dir data/ddu/structured --enum-dictionary data/reference/ddu_enum_dictionary.json --check-practice-format --check-user-story-format --check-md-consistency --strict-encoding
python scripts/verify_all.py --raw-dir data/ddu/raw_acts --structured-dir data/ddu/structured
```

## Отчёт партии

Создать в batch-каталоге:

- `batch_state.md` — что сделано, где остановка, какие команды запускались;
- `new_candidates.csv` — итоговый список кандидатов;
- `fetch_report.csv` — результаты скачивания;
- `structure_report.csv` — какие акты структурированы и с каким статусом;
- `enum_candidates.md` — кандидаты в новые ситуации/коды, если появились.

В отчёте обязательно указать:

- сколько кандидатов найдено;
- сколько актов скачано;
- сколько структурировано;
- сколько дел `index`, сколько `hold`;
- распределение по `dispute_type_code`;
- какие ситуации требуют ручного решения;
- можно ли после этой партии считать словарь достаточным для масштабирования.
