# Batch state: 2026-06-27-zpp-next-3

- current_phase: structured_validated_enum_expanded
- priority_basis: расширение словаря ЗоЗПП-ситуаций по подтверждённым пользователем кандидатам batch-3 (2026-06-28)
- priority_clusters: [proper_quality_goods_exchange_art25, unfair_terms_imposed_services_art16, harm_from_defect_art14, consumer_material_damage_art35]
- active_candidates_csv: data/parse_batches/2026-06-27-zpp-next-3/new_candidates.csv
- registry_updated_at: 2026-06-28
- raw_downloaded_new: 80
- raw_skipped_existing: 0
- structured_new: 80
- promoted_from_hold_after_enum_expansion: 45
- hold_remaining: 1
- needs_human: 0
- next_action: пересобрать реестр, кластеры и SSG; затем прогнать validate_structures.py и verify_all.py
- blockers: none

## Итог после решения пользователя по новым ситуациям

- В `data/reference/zpp_enum_dictionary.json` добавлены 4 новых `dispute_type_code`.
- 45 hold-кандидатов batch-3 переведены в соответствующие новые ситуации и отмечены как индексируемые.
- Один hold-кейс вне этих 4 ситуаций оставлен без изменения; один кандидат остался со статусом `error` из-за отсутствия raw.

### Новые ситуации
| code | promoted cases |
|---|---:|
| `proper_quality_goods_exchange_art25` | 2 |
| `unfair_terms_imposed_services_art16` | 11 |
| `harm_from_defect_art14` | 9 |
| `consumer_material_damage_art35` | 23 |

### Распределение batch-3 по status
| status | count |
|---|---:|
| `structured` | 79 |
| `error` | 1 |
| `hold` | 1 |

### Распределение batch-3 по index_policy
| policy | count |
|---|---:|
| `index` | 79 |
| `` | 1 |
| `hold` | 1 |

### Распределение batch-3 по dispute_type_code
| code | count |
|---|---:|
| `consumer_material_damage_art35` | 23 |
| `unfair_terms_imposed_services_art16` | 11 |
| `service_refusal_art32` | 10 |
| `work_service_defect_art29` | 10 |
| `harm_from_defect_art14` | 9 |
| `goods_defect_art18` | 7 |
| `info_violation_art10_12` | 5 |
| `proper_quality_goods_exchange_art25` | 2 |
| `work_service_delay_art28` | 2 |
| `contract_validity_non_zpp` | 1 |
