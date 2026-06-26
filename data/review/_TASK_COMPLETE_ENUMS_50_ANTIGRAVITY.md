# Задача: довести enum-разметку до всех 50 structure JSON

## Контекст

Проект: сайт по судебной практике о защите прав потребителей.

Уже сделано:

- Есть 50 файлов `data/structured/structure_<docid>.json`.
- 25 дел эталонной выборки уже прошли reviewed enum-разметку:
  - `data/review/phase1-2-enum-suggestions.reviewed.csv`
  - `data/review/phase1-2-enum-review-by-antigravity.md`
- Эти reviewed-значения уже перенесены в 25 JSON скриптом `scripts/sync_reviewed_enums.py`.
- Коммиты:
  - `e8e278e` — reviewed CSV и отчёт;
  - `8638488` — перенос reviewed enum в 25 JSON.
- В остальных 25 JSON пока нет `taxonomy.dispute_type_code` и `taxonomy.claim_type_codes`.

Канонический словарь enum:

- `data/reference/zpp_enum_dictionary.json`

## Цель

Добавить недостающие enum-поля во все оставшиеся `structure_*.json`, чтобы по итогам работы все 50 JSON имели:

- `taxonomy.dispute_type_code`
- `taxonomy.claim_type_codes`
- нормализованный `claims_and_result.outcome.result_type`
- `publication.index_policy`
- `publication.main_site_fit`

## Принцип работы

1. Прочитай `data/reference/zpp_enum_dictionary.json`.

2. Пройди по всем 50 `data/structured/structure_*.json`.

3. Если JSON уже содержит `taxonomy.dispute_type_code` и `taxonomy.claim_type_codes`:

   - не переоценивай эти поля;
   - не меняй reviewed-разметку без явной критической причины;
   - в отчёте отметь такие дела как `already_reviewed`.

4. Если JSON не содержит enum-кодов:

   - определи `taxonomy.dispute_type_code` по правовой конструкции ЗоЗПП, а не по маркетплейсу/товару;
   - определи `taxonomy.claim_type_codes` по требованиям истца/способам защиты;
   - нормализуй `claims_and_result.outcome.result_type` одним из значений словаря;
   - проверь `publication.index_policy` и `publication.main_site_fit`.

5. Используй только значения из `data/reference/zpp_enum_dictionary.json`.

6. Не добавляй новые enum-коды. Если словаря явно не хватает, не меняй словарь, а вынеси проблему в отчёт.

## Что именно обновлять в JSON

Для недостающих 25 JSON добавить/обновить:

- `taxonomy.dispute_type_code`
- `taxonomy.claim_type_codes`
  - JSON-формат: массив строк, например `["refund_price", "penalty", "moral_damage"]`
- `claims_and_result.outcome.result_type`
- `publication.index_policy`
- `publication.main_site_fit`
  - JSON-формат: boolean `true`/`false`, не строка

Если в JSON уже есть `taxonomy.platform_or_company` и `taxonomy.object_type`, можно аккуратно нормализовать явные технические значения вроде `None`, `null`, `electronics`, но не стирать полезные конкретные значения.

Не трогать:

- `source`
- `court`
- `parties`
- `case_summary`
- `legal_analysis`
- `processing`
- `user_story_*.md`
- `practice_*.md`
- memory-файлы

## Особые правила

- `qNPGP4ky266p` уже признан непотребительским спором и должен остаться:
  - `taxonomy.dispute_type_code`: `non_consumer_hold`
  - `taxonomy.claim_type_codes`: `["hold"]`
  - `claims_and_result.outcome.result_type`: `hold`
  - `publication.index_policy`: `hold`
  - `publication.main_site_fit`: `false`

- Арбитражные/хозяйственные или явно непотребительские дела не смешивать с основным ЗоЗПП-индексом: использовать `non_consumer_hold` / `hold`, если это подтверждается материалами JSON.

- Пограничные договорные споры, которые формально связаны с потребителем, но плохо ложатся в типовую структуру ЗоЗПП, можно помечать `contract_validity_non_zpp`, если это соответствует словарю.

## Выходные артефакты

Создать:

1. `data/review/phase1-4-enum-completion.csv`

   Колонки:

   - `docid`
   - `status` (`already_reviewed`, `added`, `needs_human`, `exclude_or_hold`)
   - `dispute_type_code`
   - `claim_type_codes`
   - `result_type`
   - `index_policy`
   - `main_site_fit`
   - `reason`

2. `data/review/phase1-4-enum-completion-by-antigravity.md`

   В отчёте указать:

   - сколько JSON было уже reviewed;
   - сколько JSON обновлено;
   - сколько дел отправлено в `hold`;
   - есть ли `needs_human`;
   - список спорных решений с кратким обоснованием.

## Проверки

После изменений запустить:

```powershell
py scripts/validate_structures.py
py scripts/verify_all.py
```

Дополнительно проверить:

- во всех 50 `structure_*.json` есть `taxonomy.dispute_type_code`;
- во всех 50 `structure_*.json` есть `taxonomy.claim_type_codes`;
- `taxonomy.claim_type_codes` везде массив строк;
- `publication.main_site_fit` везде boolean;
- все enum-значения входят в `data/reference/zpp_enum_dictionary.json`.

Ожидаемый результат:

- `validate_structures.py`: 50/50 без ошибок;
- `verify_all.py`: 50/50, 0 подозрительных ссылок;
- enum-поля заполнены в 50/50 JSON.

## Коммит

Если всё успешно, сделать отдельный git-коммит:

`complete enum taxonomy for all structure JSON`

## Важно

Не менять memory-файлы без отдельного подтверждения пользователя.
