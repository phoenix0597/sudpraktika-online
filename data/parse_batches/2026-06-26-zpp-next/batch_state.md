# Batch state: 2026-06-26-zpp-next

- current_phase: ready_for_fetch
- active_candidates_csv: `data/parse_batches/2026-06-26-zpp-next/new_candidates.csv`
- registry_updated_at: 2026-06-26
- raw_downloaded_new: 0
- raw_skipped_existing: 0
- structured_new: 0
- hold_new: 0
- needs_human: 0
- last_processed_docid: null
- next_action: скачать raw-акты из `new_candidates.csv`, затем обновить реестр и очередь `data/inbox/_queue.json`
- blockers: none

Следующая команда:

```powershell
python scripts\extract_act_text.py --csv data\parse_batches\2026-06-26-zpp-next\new_candidates.csv --output-dir data\raw_acts --limit 100 --delay 1.0
```
