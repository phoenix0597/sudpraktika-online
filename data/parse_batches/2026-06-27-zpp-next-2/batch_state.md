# Batch state: 2026-06-27-zpp-next-2

- current_phase: complete_with_hold_review
- priority_basis: дозаполнение слабых и перспективных кластеров на основе динамического покрытия базы (2026-06-27)
- priority_clusters: [work_service_delay_art28, info_violation_art10_12, distance_sale_return_art26_1]
- active_candidates_csv: data/parse_batches/2026-06-27-zpp-next-2/new_candidates.csv
- structure_report_csv: data/parse_batches/2026-06-27-zpp-next-2/structure_report.csv
- candidate_rows: 50
- overlap_with_batch_2026-06-27-zpp-next: 32
- globally_new_candidate_docids: 18
- raw_available: 50
- structured_available: 50
- indexable_cases: 39
- hold_cases: 11
- registry_updated_at: 2026-06-27
- next_action: не публиковать hold-дела без отдельного решения; при следующем парсинге обязательно сверять кандидатов с существующей очередью/реестром docid до fetch.
- blockers: нет блокеров для текущей валидации корпуса; есть отложенные решения по candidate-ситуациям и по делам, обработанным через внешний API без разрешения.

Итог проверок после исправлений Codex:
- `validate_structures.py`: 217/217 OK, ошибок 0.
- `verify_all.py`: 217/217 OK, подозрительных правовых ссылок 0.
- Enum-поля соответствуют `data/reference/zpp_enum_dictionary.json`.
- Удалены неподтверждённые ссылки из practice/JSON: `qING46DO7tmN` — `123-ФЗ`; `QsoUZnTzldHU` — `4015-1`.
- Дела, обработанные через внешний DeepSeek API без разрешения текущей задачи, оставлены вне публикации через `publication.index_policy = hold`: `8U4pkUsSIVVX`, `QsoUZnTzldHU`, `qING46DO7tmN`.
