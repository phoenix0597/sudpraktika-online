# Технический долг проекта

Файл фиксирует только актуальный технический долг, который влияет на качество
регрессионного тестирования, публикацию или масштабирование. Закрытые долги не
раздуваются подробностями; подробная хронология остаётся в ежедневных заметках.

## TD-001 — legacy-формат `practice_*.md` в ЗоПП

Статус на 2026-06-30: открыт.

Симптом:

- `python scripts\validate_structures.py --check-practice-format --check-user-story-format --check-md-consistency` проходит без ошибок, но даёт 78 предупреждений;
- `practice format ok: 233/297`;
- 64 `practice_*.md` не соответствуют текущему каноническому markdown-формату блока норм.

Типы предупреждений:

- 32 файла не содержат раздел `Нормы, на которые сослался суд`;
- 31 файл использует старый или неканонический формат блока норм;
- часть файлов имеет отдельные пропуски `Значение в деле` / `Применение судом` по конкретным нормам.

Влияние:

- текущий сайт не должен ломаться, потому что генератор нормализует legacy/new
  формат на уровне рендера;
- но долг мешает включить полный строгий gate `--strict-practice-format` для
  всего ЗоПП-корпуса.

Критерий закрытия:

- `practice format ok: 297/297`;
- полный прогон `validate_structures.py` с проверкой practice-формата не даёт
  предупреждений по ЗоПП.

Docid с debt:

`0qwM485PLa1s`, `df0QBtIxrbYt`, `e43iAjG2IkUx`, `f2vYzeWwzilv`,
`flVxOoBiwCr8`, `fNiaUxW2zu1p`, `FuXzeJou9YYT`, `g2mB62RIjp6Q`,
`hDVwlrm5jIbg`, `hqw9kUZJwtbQ`, `hV75aLss4lWU`, `iiFrae5lHbdp`,
`j10Le5fy4ebd`, `jbrHdtiKcpxX`, `jxrhPThJ8fL4`, `LEkG8QMUg0gC`,
`LEM5MFXCKK6L`, `lofHMAbow961`, `luQO6RgzTBmC`, `LY7cqAWIm4Z1`,
`MmtWiS16N45R`, `NBXqmj3oX2Lm`, `oRobcjYwTdgg`, `OzQpzlDiDWZ`,
`p5dNvnKFcEru`, `P5oLZX7sQPoI`, `Pde5A0X4dlZj`, `PulUoivdYENP`,
`pWN4OmLFKfm8`, `qhVLhQxpwYYw`, `qNPGP4ky266p`, `qVUccWRuFprb`,
`qx9K417NRkWN`, `QyBl2UIrnndK`, `RvLYP9KrC4gQ`, `Sgq21BEqhrWO`,
`sXx6jwskcamO`, `t4XCCvkBMnU1`, `tD3jmVsAWMbp`, `TNm0IBqaQjxP`,
`TOdqpcvD8z6p`, `uBSNUUmLfvNx`, `uhug73HSdyYX`, `uNnAL7AINnmK`,
`uPBnfGYfIAmK`, `VUbLq3N4mHLg`, `wAK9HEDeFtbb`, `WBfIewmrCUQH`,
`wKVnsHe6BpbT`, `xaPFd5m1V86i`, `xFynck7nm1gW`, `xljcgUano8Ys`,
`xqYAVqrmG6oO`, `YFjMxNYLsLlX`, `ygH0ZmEWXtK`, `yKzioxtguMYK`,
`ypdiIjtZacHr`, `yQ8qgPoesvWJ`, `Yse5NQ5b8YbO`, `yz0M6YZip7Qn`,
`z78ERmxhRjxq`, `zfvhZ7h0qIxW`, `zhmojGgAwwrx`, `zJyif1zBXuHu`.

## TD-002 — legacy encoding/mojibake в части ЗоПП-артефактов

Статус на 2026-06-30: открыт.

Симптом:

- полный запуск `validate_structures.py --strict-encoding` на всём ЗоПП-корпусе
  выявляет 45 encoding-issue в 22 docid;
- распределение по артефактам: `raw` — 5, `user_story` — 4, `practice` — 18,
  `structure` — 18.

Влияние:

- strict-кодировка уже обязательна для новых/изменённых docid партий;
- но полный `--strict-encoding` на весь старый ЗоПП-корпус нельзя включать в CI,
  пока этот debt не закрыт.

Критерий закрытия:

- полный запуск `validate_structures.py --strict-encoding` по ЗоПП проходит без
  ошибок.

Docid с debt:

`3EKlRihBcpmt`, `K5LBBWYaIFUW`, `WBfIewmrCUQH`, `awc1JLDcrjU1`,
`fej8tAz2p8NP`, `g2mB62RIjp6Q`, `hMcw9OheUtdC`, `jxrhPThJ8fL4`,
`qhVLhQxpwYYw`, `uBSNUUmLfvNx`, `uNnAL7AINnmK`, `uhug73HSdyYX`,
`wAK9HEDeFtbb`, `xFynck7nm1gW`, `xaPFd5m1V86i`, `xqYAVqrmG6oO`,
`ygH0ZmEWXtK`, `ypdiIjtZacHr`, `z78ERmxhRjxq`, `zJyif1zBXuHu`,
`zfvhZ7h0qIxW`, `zhmojGgAwwrx`.

## Уже закрыто

- Legacy `user_story_*.md` без стандартных подзаголовков: закрыто, 297/297 OK.
- Долг по неполному `Применение судом` на опубликованных страницах: закрыто,
  `data/review/practice-norm-application-debt.txt` пустой.
