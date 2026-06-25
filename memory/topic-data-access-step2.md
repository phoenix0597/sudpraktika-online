---
title: Доступность данных (Шаг 2) — судебные акты доступны программно
created: 2026-06-24
updated: 2026-06-24
status: active
tags: [phase0, data-access, feasibility, strategy]
related:
  - memory/topic-market-sizing.md
  - memory/topic-demand-validation-step1.md
  - technical-specification-mvp.md
---

# Доступность данных (Шаг 2) — судебные акты доступны программно

## Вердикт: GO (оба kill-switch сняты)

Шаг 2 доказал, что судебные акты по теме ЗоПП **можно находить и получать программно** — пайплайн Фазы 1 (сбор актов) технически реализуем.

## Доказанный пайплайн

**1. Обнаружение дел** — Yandex Search API (`searchapi.api.cloud.yandex.net/v2/web/search`):
- Тело: `{query:{search_type:"SEARCH_TYPE_RU", query_text:"<бытовая формулировка> site:sudact.ru"}}`
- Оператор `site:` **критически важен**: без него по бытовому запросу отдаётся ~1 акт на 10 результатов (выдача забита справочниками/юр.фирмами); с `site:sudact.ru` — 20 релевантных актов на 2 страницы.
- Ответ: XML в base64 (`rawData`), парсится в список {url, title, domain, passage}.

**2. Получение полного текста** — прямой HTTP к URL акта:
- `sudact.ru` доступен из песочницы (HTTP 200, UTF-8, ~53KB) — в отличие от `bsr.sudrf.ru`, который таймаутится из песочницы.
- Полный текст акта присутствует в HTML; метаданные (номер дела, суд, дата) — в `<meta>` и JSON-LD.

## Ключевые находки

### Поиск по бытовым запросам неэффективен без оператора site:
Тест «возврат товара озон» (без site:): из 10 документов только 1 судебный акт (sudact.ru), остальное — справочники (pravo.ru, zpp.rospotrebnadzor.ru), юр.фирмы (els24, myurist), медиа (dzen, t-j, vc). Это подтверждает «окно для входа»: ниши бытового изложения судебной практики нет. Но для **сбора данных** нужен оператор `site:`.

### sudact.ru — рабочий источник, sudrf.ru — таймаут из песочницы
- `sudact.ru`: HTTP 200, стабилен, UTF-8, полный текст в HTML. ✅
- `bsr.sudrf.ru`: ConnectTimeout из песочницы. ⚠️ Ограничение среды, не сайта.

Наше правовое положение (подтверждено юристом): доступ к **отдельным актам** правомерен (акт не охраняется АП ст. 1225; право изготовителя базы ст. 1334 защищает компиляцию, не единичный документ). sudact.ru как промежуточный источник для нахождения номера дела/URL допустим; при необходимости финальный текст сверяется с sudrf.ru.

## Масштабируемость
- 20 актов за 2 страницы выдачи по одной теме → десятки актов на тему без упора в лимиты.
- Та же механика для всех вертикалей пилота (Озон, ВБ, маркетплейсы, процессуальные).
- Лимиты: Yandex Search API расходует квоту отдельно от Wordstat (проверить тариф).

## Инструменты (переиспользуемые на Фазу 1)
- `scripts/find_cases.py` — поиск + фильтр по судебным доменам, вывод в CSV.
- `scripts/probe_search_api.py` — зонд формата (тестовый).
- Оператор `site:sudact.ru` — обязательный паттерн запроса.

## Открытые вопросы
- Парсер полнотекстового HTML акта (извлечение фабулы, мотивировки, резолютивки) — задача Фазы 1.
- Проверить лимиты Yandex Search API (отдельно от Wordstat).
- Возможно ли и нужно ли получать текст напрямую с sudrf.ru (таймаут только из песочницы — проверить вне её).

## Сырой результат
- `output/cases_ozon_sudact.csv` — 20 актов по теме «возврат товара озон».
- `output/cases_ozon.csv` — тест без site: (1 акт, для сравнения).

## Найденные акты (20, тема «возврат товара озон», фиксация для консистентности)

| Домен | Заголовок | URL |
|---|---|---|
| sudact.ru | Решение от 26.06.2025 по делу № А40-156308/2024 | sudact.ru/arbitral/doc/pHK2J1Q5qjbb/ |
| sudact.ru | Решение от 03.11.2023 | sudact.ru/arbitral/doc/HMVLgP7obYxt/ |
| sudact.ru | Решение № 2-80/2025 (Усть-Коксинский р-суд, Респ. Алтай) | sudact.ru/regular/doc/yQ8qgPoesvWJ/ |
| sudact.ru | Решение от 12.10.2023 | sudact.ru/arbitral/doc/EDbxmRULlJ5M/ |
| sudact.ru | Решение от 14.12.2023 | sudact.ru/arbitral/doc/P3qbgNbA12VK/ |
| sudact.ru | Решение № 2-1121/2019 | sudact.ru/regular/doc/qNPGP4ky266p/ |
| sudact.ru | Решение от 07.08.2023 | sudact.ru/arbitral/doc/25D8KATRSBYO/ |
| sudact.ru | Решение от 13.02.2023 | sudact.ru/arbitral/doc/C5MDXu7XJy5Y/ |
| sudact.ru | Решение от 11.11.2022 | sudact.ru/arbitral/doc/LSixwXZ0QQYu/ |
| sudact.ru | Решение от 08.09.2023 | sudact.ru/arbitral/doc/XitULdZGdfW8/ |
| sudact.ru | Решение № 2-1399/2024 (2-84/2025) | sudact.ru/regular/doc/FuXzeJou9YYT/ |
| sudact.ru | Постановление № 1-71/2025 от 29.07.2025 | sudact.ru/regular/doc/HR49frUO6S1C/ |
| sudact.ru | Решение от 30.05.2023 по делу № А40-200880/2022 | sudact.ru/arbitral/doc/mxgH7dmcjLNW/ |
| sudact.ru | Решение от 17.06.2025 по делу № А40-50006/2025 | sudact.ru/arbitral/doc/WwN0jF7FNAlx/ |
| sudact.ru | Решение от 28.03.2023 по делу № А56-80615/2022 | sudact.ru/arbitral/doc/87ISlgLBFjxT/ |
| sudact.ru | Решение № 2-1667/2018 | sudact.ru/regular/doc/vlVLxbMLgTw/ |
| sudact.ru | Решение № 2-1947/2018 (2-58/2019) | sudact.ru/regular/doc/hGeBUQ3DtW1C/ |
| sudact.ru | Решение от 24.06.2025 по делу № А40-251082/2024 | sudact.ru/arbitral/doc/Aj5FA7k2fkJw/ |
| sudact.ru | Решение № 2-4404/2023 | sudact.ru/regular/doc/qVUccWRuFprb/ |

Замечание: есть дубли по делу № 2-1121/2019 (два URL) — нужна дедупликация по
идентичности дела (Фаза 2, уже заложена в ТЗ).
