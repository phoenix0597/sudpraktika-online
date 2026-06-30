# DDU batch 2026-06-29-ddu-001 — состояние

Обновлено: 2026-06-29T19:25:00+03:00

## Итог
- Raw актов: 68
- Технически complete: 68
- Индексируемые: 17
- Hold / ручная проверка: 51

## Что исправлено после остановки Antigravity
- дозакрыты отсутствующие user_story/practice/structure для недоделанных актов через hold-разметку;
- исправлены невалидные enum/status поля в `K74QFxEvJFUB`; 
- создан недостающий `structure_mJ8TjG4OypYx.json`; 
- приведены к стандартным подзаголовкам проблемные `user_story_*.md`; 
- пересобраны канонические `practice_*.md` для `jZyFxy7HJtmp`, `K74QFxEvJFUB`, `mJ8TjG4OypYx`; 
- синхронизирован статус очереди.

## Handoff
- Strict-проверка кодировки проходит: `validate_structures.py --raw-dir data/ddu/raw_acts --structured-dir data/ddu/structured --enum-dictionary data/reference/ddu_enum_dictionary.json --check-practice-format --check-user-story-format --check-md-consistency --strict-encoding` → 68/68, 0 ошибок, 0 предупреждений.
- Главная проблема партии не техническая, а поисковая: 17 целевых `index` из 68 raw-актов. Следующую DDU-партию вести через предварительный triage кандидатов до fetch.
- Hold-дела можно передать следующему агенту на повторную LLM-разметку без публикации.
