# Batch state: 2026-06-26-zpp-next

- current_phase: structuring_complete
- priority_basis: стартовая партия по ранее найденным кандидатам из `output/cases_ozon_regular.csv`; приоритеты определялись до введения динамического правила покрытия кластеров
- priority_clusters: [distance_sale_return_art26_1, info_violation_art10_12, service_refusal_art32, prepaid_goods_delay_art23_1, work_service_defect_art29, goods_defect_art18]
- active_candidates_csv: `data/parse_batches/2026-06-26-zpp-next/new_candidates.csv`
- registry_updated_at: 2026-06-26
- raw_downloaded_new: 37
- raw_skipped_existing: 0
- structured_new: 37
- hold_new: 3
- needs_human: 0
- last_processed_docid: ZLwdZCW9EtVP
- next_action: перейти к генерации SSG-прототипа (Шаг 1.5) с учётом новой партии судебных дел
- blockers: none

Следующая команда:

```powershell
python scripts\generate_ssg_prototype.py
```
