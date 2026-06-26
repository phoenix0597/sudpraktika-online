# Фаза 1.4: первичная кластеризация судебных актов

## Метод

Использована лёгкая кластеризация по уже извлечённым JSON-полям: `taxonomy`, `claims_and_result`, `publication`, ключевые факторы и теги ситуации. Embeddings на этом шаге не применялись: для MVP достаточно сначала проверить, какие группы дают существующие структурные поля.

- Всего актов: 50
- С reviewed enum-кодами: 50
- С временной эвристической классификацией: 0

## Сводка кластеров

| Кластер | Дел | Reviewed | Inferred | Приоритет | Угол страницы |
|---|---:|---:|---:|---|---|
| `goods_defect_art18` — Товар с недостатком / технически сложный товар | 24 | 24 | 0 | pillar | Что взыскивать и как доказывать недостаток товара |
| `distance_sale_return_art26_1` — Дистанционная продажа: отказ от товара и возврат денег | 7 | 7 | 0 | landing | Когда можно вернуть товар, купленный онлайн |
| `info_violation_art10_12` — Недостоверная или неполная информация о товаре/продавце | 6 | 6 | 0 | landing | Ошибки в цене, продавце, свойствах товара и последствия для иска |
| `service_refusal_art32` — Отказ от услуги и возврат денег | 5 | 5 | 0 | landing | Возврат оплаты за услуги, курсы, страховки и сервисы |
| `prepaid_goods_delay_art23_1` — Оплаченный товар не передали или задержали | 4 | 4 | 0 | landing | Что делать, если заказ оплачен, но товар не передают |
| `contract_validity_non_zpp` — Пограничные договорные споры / риск не ЗоЗПП | 2 | 2 | 0 | hold | Дела, которые требуют ручной проверки перед публикацией |
| `non_consumer_hold` — Не потребительский спор | 1 | 1 | 0 | hold | Исключить из основного индекса ЗоЗПП-сайта |
| `work_service_defect_art29` — Недостатки работ или услуг | 1 | 1 | 0 | long_tail | Некачественные работы: окна, монтаж, изготовление |

## Кластеры по делам

### `goods_defect_art18` — Товар с недостатком / технически сложный товар

- Дел: 24
- Приоритет: `pillar`
- Угол будущей страницы: Что взыскивать и как доказывать недостаток товара

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `0qwM485PLa1s` | автомобиль / Автомир-Трейд | partially_satisfied | reviewed |
| `1w89Nc1UMNmm` | игровая приставка / Wildberries | partially_satisfied | reviewed |
| `1yfD2XxjDDrJ` | диван / — | satisfied | reviewed |
| `50MnpFBeHEl8` | обувь / ООО «Рандеву» | partially_satisfied | reviewed |
| `7hRq36xc81l6` | смартфон / Яндекс.Маркет | rejected | reviewed |
| `82RMC7eXBpH4` | телевизор / М.Видео | satisfied | reviewed |
| `BRRlQN72V9V6` | смартфон / ДНС | mixed | reviewed |
| `C2EQxwU5LLlC` | electronics / Wildberries | partially_satisfied | reviewed |
| `Cr4ZymF07ubW` | видеокарта / ООО «Ситилинк» | partially_satisfied | reviewed |
| `LY7cqAWIm4Z1` | окна из ПВХ / ООО «Компания «Оконный Континент» | partially_satisfied | reviewed |
| `NBXqmj3oX2Lm` | смартфон / ООО «Сеть Связной» | partially_satisfied | reviewed |
| `RvLYP9KrC4gQ` | мобильный телефон / — | partially_satisfied | reviewed |
| `Wvd6aNEyrvUy` | смартфон / АО «Мегафон Ритейл» | partially_satisfied | reviewed |
| `YFjMxNYLsLlX` | мебель / Лазурит | partially_satisfied | reviewed |
| `Yse5NQ5b8YbO` | телевизор / Ozon | partially_satisfied | reviewed |
| `b41sumpSMelO` | телевизор / ООО «ЛГ Электроникс РУС» | partially_satisfied | reviewed |
| `ekdTskHpS3WO` | сотовый телефон / АО «РТК» | partially_satisfied | reviewed |
| `jbrHdtiKcpxX` | смартфон / — | partially_satisfied | reviewed |
| `oRobcjYwTdgg` | Холодильник / ООО «МВМ» | rejected | reviewed |
| `qx9K417NRkWN` | автомобиль / УАЗ | partially_satisfied | reviewed |
| `tD3jmVsAWMbp` | кондиционер / ООО ТК «Хайер Рус» (Haier) | partially_satisfied | reviewed |
| `v0m4w50eZy5n` | планшет / Яндекс.Маркет | partially_satisfied | reviewed |
| `xyw1pNsfewV8` | смартфон / ООО «Самсунг Электроникс Рус Компани» | partially_satisfied | reviewed |
| `yc651JdA4PJC` | ноутбук / Яндекс.Маркет | partially_satisfied | reviewed |

### `distance_sale_return_art26_1` — Дистанционная продажа: отказ от товара и возврат денег

- Дел: 7
- Приоритет: `landing`
- Угол будущей страницы: Когда можно вернуть товар, купленный онлайн

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `LEkG8QMUg0gC` | телевизор / Ozon | partially_satisfied | reviewed |
| `OzQpzlDiDWZ` | швабра / Ашан | partially_satisfied | reviewed |
| `QyBl2UIrnndK` | телевизор / М.Видео | partially_satisfied | reviewed |
| `VLhBBoeb7vWo` | ноутбук / ООО «СДЭК.Маркет» | partially_satisfied | reviewed |
| `fNiaUxW2zu1p` | товар дистанционной продажи / Wildberries | partially_satisfied | reviewed |
| `hV75aLss4lWU` | одежда / Lamoda | partially_satisfied | reviewed |
| `pWN4OmLFKfm8` | беговая дорожка / ООО «Ситилинк» | partially_satisfied | reviewed |

### `info_violation_art10_12` — Недостоверная или неполная информация о товаре/продавце

- Дел: 6
- Приоритет: `landing`
- Угол будущей страницы: Ошибки в цене, продавце, свойствах товара и последствия для иска

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `4686FPHUhLZC` | массажная накидка / ООО «Азон» | satisfied | reviewed |
| `DvLR6OZqCqt` | информация о продавце / несколько маркетплейсов | rejected | reviewed |
| `P5oLZX7sQPoI` | медицинское изделие / ООО «Азон» | partially_satisfied | reviewed |
| `TZsI5FbnZOZJ` | продовольственные товары / АО «Тандер» | partially_satisfied | reviewed |
| `qVUccWRuFprb` | зарядное устройство / Wildberries | rejected | reviewed |
| `yQ8qgPoesvWJ` | видеокарта / Ozon | rejected | reviewed |

### `service_refusal_art32` — Отказ от услуги и возврат денег

- Дел: 5
- Приоритет: `landing`
- Угол будущей страницы: Возврат оплаты за услуги, курсы, страховки и сервисы

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `3mMKR7CNUYQ8` | онлайн-курс / Skillbox | satisfied | reviewed |
| `Pde5A0X4dlZj` | страховая услуга / Ренессанс Жизнь | partially_satisfied | reviewed |
| `TNm0IBqaQjxP` | сертификат на ПО / АО «КарВит» | partially_satisfied | reviewed |
| `WJjAKsJGIglY` | услуга / ООО «М-Ассистанс» | partially_satisfied | reviewed |
| `yz0M6YZip7Qn` | авиабилеты / Ozon Travel / Air Serbia | mixed | reviewed |

### `prepaid_goods_delay_art23_1` — Оплаченный товар не передали или задержали

- Дел: 4
- Приоритет: `landing`
- Угол будущей страницы: Что делать, если заказ оплачен, но товар не передают

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `FuXzeJou9YYT` | товар маркетплейса / Ozon | mixed | reviewed |
| `MmtWiS16N45R` | бревенчатый сруб дома / не указан | partially_satisfied | reviewed |
| `PulUoivdYENP` | кухонный гарнитур / не указан | satisfied | reviewed |
| `TOdqpcvD8z6p` | роллеты, калитка, монтаж / — | partially_satisfied | reviewed |

### `contract_validity_non_zpp` — Пограничные договорные споры / риск не ЗоЗПП

- Дел: 2
- Приоритет: `hold`
- Угол будущей страницы: Дела, которые требуют ручной проверки перед публикацией

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `LEM5MFXCKK6L` | смартфон / Wildberries | rejected | reviewed |
| `flVxOoBiwCr8` | услуги связи / Ростелеком | rejected | reviewed |

### `non_consumer_hold` — Не потребительский спор

- Дел: 1
- Приоритет: `hold`
- Угол будущей страницы: Исключить из основного индекса ЗоЗПП-сайта

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `qNPGP4ky266p` | поставка товара / Ozon | hold | reviewed |

### `work_service_defect_art29` — Недостатки работ или услуг

- Дел: 1
- Приоритет: `long_tail`
- Угол будущей страницы: Некачественные работы: окна, монтаж, изготовление

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `hqw9kUZJwtbQ` | оконные конструкции / ООО "Леруа Мерлен Восток" | partially_satisfied | reviewed |

## Практический вывод

1. Основной пиллар для первой версии — дела о недостатках товара: это самый крупный и понятный пользователю кластер.
2. Отдельные посадочные страницы стоит готовить по дистанционной продаже, задержке/непередаче оплаченного товара, информационным нарушениям и отказу от услуг.
3. Кластеры работ/услуг пока выглядят как long-tail: их можно держать в резерве до расширения выборки.
4. Дела с `hold` не смешивать с основным гражданским ЗоЗПП-индексом.
5. Все 50 дел имеют подтверждённые и проверенные enum-коды, что делает кластеризацию полностью детерминированной и готовой к публикации.

## Следующий шаг

Проверить кластеры вручную и выбрать 3–5 первых типов страниц для SSG-прототипа. Embeddings подключать только если ручная проверка покажет, что эвристики смешивают разные ситуации.
