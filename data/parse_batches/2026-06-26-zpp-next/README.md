# Batch: 2026-06-26-zpp-next

Рабочая папка следующей партии парсинга и структурирования дел ЗоЗПП.

Каноническая задача для агента: `data/review/_TASK_PARSE_NEXT_BATCH_AGY.md`.

## Роль файлов

- `new_candidates.csv` — новые URL-кандидаты после дедупликации по `data/registry/case_registry.csv`.
- `search_*.csv` — сырые результаты отдельных поисковых запросов.
- `fetch_report.csv` — отчёт по скачиванию raw-актов.
- `structure_report.csv` — отчёт по структурированию актов агентом.
- `batch_state.md` — короткое состояние партии и точка возобновления.

## Правило возобновления

Если работа прервана, следующий агент:

1. читает `data/review/_TASK_PARSE_NEXT_BATCH_AGY.md`;
2. читает `batch_state.md`, если файл уже создан;
3. сверяет `new_candidates.csv`, `fetch_report.csv`, `structure_report.csv`;
4. продолжает с первого незавершённого шага, не перезапуская готовые шаги.

Готовые raw/structured-артефакты не перегенерировать без причины.
