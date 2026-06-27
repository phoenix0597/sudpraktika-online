# Batch state: 2026-06-27-zpp-next

- current_phase: complete_with_hold_review
- priority_basis: дозаполнение слабых и перспективных кластеров на основе динамического покрытия базы (2026-06-27)
- priority_clusters: [work_service_defect_art29, work_service_delay_art28, prepaid_goods_delay_art23_1, info_violation_art10_12, distance_sale_return_art26_1]
- active_candidates_csv: data/parse_batches/2026-06-27-zpp-next/new_candidates.csv
- structure_report_csv: data/parse_batches/2026-06-27-zpp-next/structure_report.csv
- candidate_rows: 119
- raw_available: 112
- structured_available: 112
- missing_raw_or_not_fetched: 7
- indexable_cases: 87
- hold_cases: 25
- overlap_with_batch_2026-06-27-zpp-next-2: 32
- registry_updated_at: 2026-06-27
- next_action: решить, какие hold-кандидаты переобрабатывать/расширять словарём ситуаций; следующий парсинг запускать с учётом дедупликации по уже известным docid.
- blockers: нет блокеров для текущей валидации корпуса; есть отложенные редакционные решения по hold-кандидатам.

Итог проверок после исправлений Codex:
- `validate_structures.py`: 217/217 OK, ошибок 0.
- `verify_all.py`: 217/217 OK, подозрительных правовых ссылок 0.
- Enum-поля соответствуют `data/reference/zpp_enum_dictionary.json`.
- 17 ранее скачанных, но не структурированных raw-актов закрыты hold-заготовками с причиной `raw_fetched_but_not_structured_needs_reprocessing`, чтобы корпус и очередь не оставались в поломанном промежуточном состоянии.
