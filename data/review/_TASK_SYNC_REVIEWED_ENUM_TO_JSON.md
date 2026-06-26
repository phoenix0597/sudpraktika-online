# Задача: синхронизировать reviewed enum-разметку с JSON

## Контекст

- Reviewed-разметка по 25 делам уже проверена и сохранена в `data/review/phase1-2-enum-suggestions.reviewed.csv`.
- Отчёт проверки: `data/review/phase1-2-enum-review-by-antigravity.md`.
- Словарь допустимых значений: `data/reference/zpp_enum_dictionary.json`.
- Сейчас в `data/structured/structure_*.json` ещё нет полей `taxonomy.dispute_type_code` и `taxonomy.claim_type_codes`.

## Цель

Перенести финальные reviewed-значения из CSV в соответствующие `structure_<docid>.json` по 25 делам и проверить, что JSON остаются валидными.

## Что нужно сделать

1. Прочитать `data/review/phase1-2-enum-suggestions.reviewed.csv`.

2. Для каждой строки найти файл:
   `data/structured/structure_<docid>.json`

3. Внести или обновить поля:

   - `taxonomy.dispute_type_code`
     ← `final_dispute_type_code`

   - `taxonomy.claim_type_codes`
     ← `final_claim_type_codes`

     Важно: в CSV значения разделены `;`, в JSON нужно сохранить как массив строк.

   - `claims_and_result.outcome.result_type`
     ← `final_result_type`

   - `publication.index_policy`
     ← `final_index_policy`

   - `publication.main_site_fit`
     ← `final_main_site_fit`

     Важно: в JSON это boolean, то есть `true`/`false`, а не строка.

4. Если в JSON есть поля `taxonomy.platform_or_company` и `taxonomy.object_type`, аккуратно синхронизировать их с:

   - `final_platform_norm`
   - `final_object_type_norm`

   Не трогать более детальные поля вроде `object_name` и `situation_tags`, если они уже заполнены.

5. Для дела `qNPGP4ky266p` сохранить логику исключения:

   - `taxonomy.dispute_type_code`: `non_consumer_hold`
   - `taxonomy.claim_type_codes`: `["hold"]`
   - `claims_and_result.outcome.result_type`: `hold`
   - `publication.index_policy`: `hold`
   - `publication.main_site_fit`: `false`

## Ограничения

- Не перегенерировать JSON целиком.
- Не менять `user_story_*.md` и `practice_*.md`.
- Не менять словарь `data/reference/zpp_enum_dictionary.json`, если не обнаружена явная ошибка.
- Не менять memory-файлы без отдельного подтверждения.
- Сохранять существующие `source`, `court`, `parties`, `legal_analysis`, `processing` без изменений.
- Не добавлять новые enum-коды вне словаря.

## Проверки

После изменений запустить:

```powershell
py scripts/validate_structures.py
py scripts/verify_all.py
```

Ожидаемый результат:

- `validate_structures.py`: 50/50 без ошибок.
- `verify_all.py`: 50/50, 0 подозрительных ссылок.

Дополнительно проверить скриптом или командой:

- в 25 JSON из reviewed CSV появились `taxonomy.dispute_type_code`;
- в 25 JSON из reviewed CSV появились `taxonomy.claim_type_codes`;
- все значения входят в `data/reference/zpp_enum_dictionary.json`.

## Результат работы

Создать короткий отчёт в ответе:

- сколько JSON обновлено;
- список обновлённых `docid`;
- отдельно отметить `qNPGP4ky266p`;
- результаты двух проверок;
- были ли отклонения или ручные решения.

Если всё успешно — сделать отдельный git-коммит с сообщением:

`sync reviewed enum markup into structure JSON`
