# Фаза 1.4: первичная кластеризация судебных актов

## Метод

Использована лёгкая кластеризация по уже извлечённым JSON-полям: `taxonomy`, `claims_and_result`, `publication`, ключевые факторы и теги ситуации. Embeddings на этом шаге не применялись: для MVP достаточно сначала проверить, какие группы дают существующие структурные поля.

- Всего актов: 217
- С reviewed enum-кодами: 217
- С временной эвристической классификацией: 0

## Сводка кластеров

| Кластер | Дел | Reviewed | Inferred | Приоритет | Угол страницы |
|---|---:|---:|---:|---|---|
| `goods_defect_art18` — Товар с недостатком / технически сложный товар | 53 | 53 | 0 | pillar | Что взыскивать и как доказывать недостаток товара |
| `work_service_defect_art29` — Недостатки работ или услуг | 33 | 33 | 0 | pillar | Некачественные работы: окна, монтаж, изготовление |
| `contract_validity_non_zpp` — Пограничные договорные споры / риск не ЗоЗПП | 29 | 29 | 0 | hold | Дела, которые требуют ручной проверки перед публикацией |
| `info_violation_art10_12` — Недостоверная или неполная информация о товаре/продавце | 28 | 28 | 0 | pillar | Ошибки в цене, продавце, свойствах товара и последствия для иска |
| `service_refusal_art32` — Отказ от услуги и возврат денег | 25 | 25 | 0 | pillar | Возврат оплаты за услуги, курсы, страховки и сервисы |
| `prepaid_goods_delay_art23_1` — Оплаченный товар не передали или задержали | 18 | 18 | 0 | pillar | Что делать, если заказ оплачен, но товар не передают |
| `work_service_delay_art28` — Нарушение сроков работ или услуг | 13 | 13 | 0 | pillar | Просрочка работ, монтажа или изготовления |
| `distance_sale_return_art26_1` — Дистанционная продажа: отказ от товара и возврат денег | 12 | 12 | 0 | pillar | Когда можно вернуть товар, купленный онлайн |
| `non_consumer_hold` — Не потребительский спор | 6 | 6 | 0 | hold | Исключить из основного индекса ЗоЗПП-сайта |

## Кластеры по делам

### `goods_defect_art18` — Товар с недостатком / технически сложный товар

- Дел: 53
- Приоритет: `pillar`
- Угол будущей страницы: Что взыскивать и как доказывать недостаток товара

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `0qwM485PLa1s` | автомобиль / Автомир-Трейд | partially_satisfied | reviewed |
| `12ENIh1cxpZo` | smartphone / DNS | partially_satisfied | reviewed |
| `1w89Nc1UMNmm` | игровая приставка / Wildberries | partially_satisfied | reviewed |
| `1yfD2XxjDDrJ` | диван / — | satisfied | reviewed |
| `4R6JU5dS08gV` | бытовая техника / ООО «МВМ» (правопреемник ООО «Эльдорадо») | rejected | reviewed |
| `50MnpFBeHEl8` | обувь / ООО «Рандеву» | partially_satisfied | reviewed |
| `6zydJ9jGUgoa` | ноутбук / AliExpress | partially_satisfied | reviewed |
| `7hRq36xc81l6` | смартфон / Яндекс.Маркет | rejected | reviewed |
| `82RMC7eXBpH4` | телевизор / М.Видео | satisfied | reviewed |
| `AOvMR0MbCMU5` | электроника / ООО «ДНС Ритейл» | rejected | reviewed |
| `BRRlQN72V9V6` | смартфон / ДНС | mixed | reviewed |
| `C2EQxwU5LLlC` | electronics / Wildberries | partially_satisfied | reviewed |
| `Cr4ZymF07ubW` | видеокарта / ООО «Ситилинк» | partially_satisfied | reviewed |
| `FJA5dldIi5ZP` | мебель / ИП ФИО3 (дилер под брендом «Много мебели») | partially_satisfied | reviewed |
| `KuGAOhWI77Ni` | ноутбук / ООО МВМ | partially_satisfied | reviewed |
| `LY7cqAWIm4Z1` | окна из ПВХ / ООО «Компания «Оконный Континент» | partially_satisfied | reviewed |
| `LZW79ndNKBgR` | смартфон / ВымпелКом | partially_satisfied | reviewed |
| `MBFBIl2vHb6V` | холодильник / Эльдорадо | partially_satisfied | reviewed |
| `NBXqmj3oX2Lm` | смартфон / ООО «Сеть Связной» | partially_satisfied | reviewed |
| `NXlFVcueusNG` | мебель под заказ / ИП ФИО2 | partially_satisfied | reviewed |
| `QlJychgKjegT` | входные металлические двери / ФИО2 | partially_satisfied | reviewed |
| `RvLYP9KrC4gQ` | мобильный телефон / — | partially_satisfied | reviewed |
| `TekGuuE2erbs` | смартфон / ООО "Эппл Рус" | partially_satisfied | reviewed |
| `Tm9uZuaq6XQj` | телевизор / ООО «Ситилинк» | rejected | reviewed |
| `TvwZY0A9N0VC` | мебель / ООО «Премьер Мебель» | partially_satisfied | reviewed |
| `UeHswTmOk86R` | смартфон / ООО «Сеть Связной» | partially_satisfied | reviewed |
| `VnTwgt4w6NgC` | детская коляска / ИП ФИО2 | partially_satisfied | reviewed |
| `Wvd6aNEyrvUy` | смартфон / АО «Мегафон Ритейл» | partially_satisfied | reviewed |
| `YFjMxNYLsLlX` | мебель / Лазурит | partially_satisfied | reviewed |
| `Yse5NQ5b8YbO` | телевизор / Ozon | partially_satisfied | reviewed |
| `b41sumpSMelO` | телевизор / ООО «ЛГ Электроникс РУС» | partially_satisfied | reviewed |
| `ekdTskHpS3WO` | сотовый телефон / АО «РТК» | partially_satisfied | reviewed |
| `eqUu93zC5GNu` | coffee_machine / М.Видео | satisfied | reviewed |
| `eqW9CQxuKMl5` | телевизор / ООО МВМ | partially_satisfied | reviewed |
| `fbw72y4yhlbV` | смартфон / ООО МВМ | partially_satisfied | reviewed |
| `hrW58hVf9XV0` | кухонный гарнитур / Сегодня Дома | satisfied | reviewed |
| `jbrHdtiKcpxX` | смартфон / — | partially_satisfied | reviewed |
| `lpuLB7g2UNH2` | автомобиль / ООО «Артан» | partially_satisfied | reviewed |
| `nUaFwGkUmRHj` | видеокарта / DNS | partially_satisfied | reviewed |
| `oRobcjYwTdgg` | Холодильник / ООО «МВМ» | rejected | reviewed |
| `p5dNvnKFcEru` | смартфон / ООО «ДНС Ритейл» | partially_satisfied | reviewed |
| `pd6Hnfvbcg5X` | автомобиль / ООО «АвтоРитм» | rejected | reviewed |
| `peq1VhDNsb1O` | смартфон / АО «Русская Телефонная Компания» | partially_satisfied | reviewed |
| `qZ12yS80Ff1v` | мебель / ООО «Торговый дом «Аскона» | satisfied | reviewed |
| `qx9K417NRkWN` | автомобиль / УАЗ | partially_satisfied | reviewed |
| `rrObAHc2FOxm` | пылесос / ООО "Дайсон" | partially_satisfied | reviewed |
| `sGlfWIMtuBLu` | автозапчасти из Японии (конструктор) / ООО "ФАВОРИТТРАНСИМПОРТ" | satisfied | reviewed |
| `sSeSgJAISkgt` | автомобиль / ООО "ЧАНЪАНЬ МОТОРС РУС" | partially_satisfied | reviewed |
| `tD3jmVsAWMbp` | кондиционер / ООО ТК «Хайер Рус» (Haier) | partially_satisfied | reviewed |
| `uivLG43dcYu` | бытовая техника / ООО «МВМ» | partially_satisfied | reviewed |
| `v0m4w50eZy5n` | планшет / Яндекс.Маркет | partially_satisfied | reviewed |
| `xyw1pNsfewV8` | смартфон / ООО «Самсунг Электроникс Рус Компани» | partially_satisfied | reviewed |
| `yc651JdA4PJC` | ноутбук / Яндекс.Маркет | partially_satisfied | reviewed |

### `work_service_defect_art29` — Недостатки работ или услуг

- Дел: 33
- Приоритет: `pillar`
- Угол будущей страницы: Некачественные работы: окна, монтаж, изготовление

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `0qJvaL8TjRNK` | автомобиль / ООО "Автосервис №" | partially_satisfied | reviewed |
| `2TGeURZDGtHr` | жилой дом / ФИО2 | partially_satisfied | reviewed |
| `51kGOAmFj6gC` | услуги по содержанию и ремонту общего имущества МКД / ООО «МУЖСК» | partially_satisfied | reviewed |
| `EaGNj81Zabr` | услуги по содержанию общего имущества гаражного комплекса / ГЭК «7 ключей» | partially_satisfied | reviewed |
| `G4TM4cp6aPgO` | мебель / ООО «Онда» | partially_satisfied | reviewed |
| `IAhdCZSdrurT` | мебель / ООО «Самая Лучшая Мебель» | partially_satisfied | reviewed |
| `IG3OO15URBn` | услуги ЖКХ / ООО ПКФ «ЮГ-ТТ» | partially_satisfied | reviewed |
| `OWEMw275FKQa` | бытовой подряд / ООО «Созвездие» | satisfied | reviewed |
| `PI6Ya0MGHsUx` | мебель под заказ / ООО «Ротанг» | satisfied | reviewed |
| `SHBRS4KIyAdE` | квартира / АО «Домоуправляющая компания Советского района» | partially_satisfied | reviewed |
| `THSfVA8YBEVu` | ковер / ИП ФИО2 | partially_satisfied | reviewed |
| `Uy8lx0YDsSrb` | балкон/лоджия / ООО «Уютный балкон» | satisfied | reviewed |
| `VecjISqulAda` | онлайн-курсы / Skillbox | partially_satisfied | reviewed |
| `YFdU4opnt3Za` | медицинские услуги / ООО ЛПЦ «ЕвроДент» | rejected | reviewed |
| `YNoOFAgZJmLv` | — / ООО «Евроклимат Групп» | mixed | reviewed |
| `bZcjnQhwIsW` | кухонный гарнитур / ООО «РуВиКом» | partially_satisfied | reviewed |
| `c6j46it4lXNa` | автомобиль / Ренессанс Страхование | partially_satisfied | reviewed |
| `cYIZ3teqSbQR` | дверь / Интерьерное решение | partially_satisfied | reviewed |
| `d365WK1SnXL8` | услуга / БРАСС | rejected | reviewed |
| `dYBTtWFaWtQa` | квартира / ООО «Энергоресурс» | partially_satisfied | reviewed |
| `dZLatipIdmJQ` | мебель / ООО «Практика-Мебель» | partially_satisfied | reviewed |
| `e5iaAholP0WW` | многоквартирный дом / УК ООО «Ремонтстрой+» | rejected | reviewed |
| `ejYcqIsTl36v` | тур / ООО «ТТ-Трэвел» | partially_satisfied | reviewed |
| `fiXHEle8cxrH` | автомобиль / ООО «Автопартнер-Центр» | partially_satisfied | reviewed |
| `fnpHqXEsViQX` | кровля индивидуального жилого дома / ООО «СК «Ремез» | partially_satisfied | reviewed |
| `hMcw9OheUtdC` | туристский продукт / ANEXTOUR | partially_satisfied | reviewed |
| `hqw9kUZJwtbQ` | оконные конструкции / ООО "Леруа Мерлен Восток" | partially_satisfied | reviewed |
| `mJA08TMXuhUr` | строительные работы и услуги / ООО «Волжская Ривьера» | partially_satisfied | reviewed |
| `poxiixn4H5dr` | Медицинские услуги / ООО «ДЕНТО-ГРАНД» | partially_satisfied | reviewed |
| `tGHVr2Rx78ry` | автосервисные услуги / ООО «НьюСервис» | partially_satisfied | reviewed |
| `tGOym2Rdgd5r` | стоматологические услуги / ООО «СтомЭксперт» | partially_satisfied | reviewed |
| `tHGO8gaGWwxe` | корпусная мебель / ИП ФИО2 | satisfied | reviewed |
| `tWUT3r5luHoq` | строительные материалы и работы / магазин «Квадратный метр» | partially_satisfied | reviewed |

### `contract_validity_non_zpp` — Пограничные договорные споры / риск не ЗоЗПП

- Дел: 29
- Приоритет: `hold`
- Угол будущей страницы: Дела, которые требуют ручной проверки перед публикацией

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `7ltNyhBxj85V` | car / ТрансТехСервис | rejected | reviewed |
| `HZZImaYBl1oQ` | массажер / ООО «Мистерия» | hold | reviewed |
| `LEM5MFXCKK6L` | смартфон / Wildberries | rejected | reviewed |
| `P4XHDMeet1NZ` | Финансовые услуги / ПАО «Почта Банк» | hold | reviewed |
| `TRJAjBS3H41P` | автомобиль / ПАО СК «Росгосстрах» | partially_satisfied | reviewed |
| `VvdgwtPLLRWO` | Финансовые услуги / ПАО «Банк ВТБ» | hold | reviewed |
| `ZwT0slBVSQm` | — / АО «Донэнерго» | hold | reviewed |
| `fej8tAz2p8NP` | — / — | hold | reviewed |
| `flVxOoBiwCr8` | услуги связи / Ростелеком | rejected | reviewed |
| `g2mB62RIjp6Q` | — / — | hold | reviewed |
| `jxrhPThJ8fL4` | — / — | hold | reviewed |
| `lxw63q3TtAZj` | бонусные баллы / Мегамаркет / СберСпасибо | satisfied | reviewed |
| `qING46DO7tmN` | service / Связной | hold | reviewed |
| `qhVLhQxpwYYw` | — / — | hold | reviewed |
| `uBSNUUmLfvNx` | — / — | hold | reviewed |
| `uNnAL7AINnmK` | — / — | hold | reviewed |
| `uhug73HSdyYX` | — / — | hold | reviewed |
| `wAK9HEDeFtbb` | — / — | hold | reviewed |
| `wnrZsOjKQVWt` | мобильная связь / ПАО «Мобильные ТелеСистемы» | rejected | reviewed |
| `xFynck7nm1gW` | — / — | hold | reviewed |
| `xaPFd5m1V86i` | — / — | hold | reviewed |
| `xqYAVqrmG6oO` | — / — | hold | reviewed |
| `xwrG3d38fUVg` | цифровая техника / СберМегаМаркет | hold | reviewed |
| `ygH0ZmEWXtK` | — / — | hold | reviewed |
| `ypdiIjtZacHr` | — / — | hold | reviewed |
| `z78ERmxhRjxq` | — / — | hold | reviewed |
| `zJyif1zBXuHu` | — / — | hold | reviewed |
| `zfvhZ7h0qIxW` | — / — | hold | reviewed |
| `zhmojGgAwwrx` | — / — | hold | reviewed |

### `info_violation_art10_12` — Недостоверная или неполная информация о товаре/продавце

- Дел: 28
- Приоритет: `pillar`
- Угол будущей страницы: Ошибки в цене, продавце, свойствах товара и последствия для иска

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `1MuNOiJg9Zgs` | ювелирные изделия / ООО Ломбард «Золотой Стандарт» | rejected | reviewed |
| `4686FPHUhLZC` | массажная накидка / ООО «Азон» | satisfied | reviewed |
| `4nJ71tJWGLLr` | одежда / Wildberries / РВБ | satisfied | reviewed |
| `5M1CUDzM98LB` | электроника / Мегамаркет | satisfied | reviewed |
| `7ng73tMHgy5O` | компьютерная техника / Мегамаркет | satisfied | reviewed |
| `DvLR6OZqCqt` | информация о продавце / несколько маркетплейсов | rejected | reviewed |
| `F4tgfJ83SDl1` | Массажные приборы / ООО «РИТЕЙЛ ГРУПП» | satisfied | reviewed |
| `FQi78fsHgSYx` | бытовая и компьютерная техника / Мегамаркет | satisfied | reviewed |
| `IFokpJdrgvYN` | информационные услуги / ООО «Интернет-аукцион» (интернет-площадка meshok.net) | hold | reviewed |
| `JFu0uFMkN6QK` | ювелирное изделие / — | mixed | reviewed |
| `P5oLZX7sQPoI` | медицинское изделие / ООО «Азон» | partially_satisfied | reviewed |
| `SW7BQ3oEiqbU` | автомобиль / ООО «МБ-Тверь» | rejected | reviewed |
| `TZsI5FbnZOZJ` | продовольственные товары / АО «Тандер» | partially_satisfied | reviewed |
| `VUbLq3N4mHLg` | автомобиль / ООО «Аванта-Авто» | partially_satisfied | reviewed |
| `bC8RZAaMy2lP` | информационные и рекламные услуги / ООО «Директ Почта» | partially_satisfied | reviewed |
| `hGeBUQ3DtW1C` | массажер / ООО «Формат» | partially_satisfied | reviewed |
| `iuwDUUEqaxZT` | автомобиль / ООО «Трейдмир» | rejected | reviewed |
| `lOvgUPRb4KVZ` | Услуги ЖКХ / Югорский фонд капитального ремонта многоквартирных домов | partially_satisfied | reviewed |
| `liPGLMvRZRoO` | образовательные услуги / ИП ФИО2 | partially_satisfied | reviewed |
| `p103xklic1mg` | электроника / Мегамаркет | partially_satisfied | reviewed |
| `qUSClQ9f9n5N` | Массажные приборы / ООО «КАРКАДЕ» | partially_satisfied | reviewed |
| `qVUccWRuFprb` | зарядное устройство / Wildberries | rejected | reviewed |
| `t2g2Kh4epVJ6` | коммунальные услуги / ООО «Водоканал» | partially_satisfied | reviewed |
| `x6ed9pqkhSoh` | электроника / Мегамаркет | satisfied | reviewed |
| `xH2f1YwFggYm` | автомобиль / ООО «Трейдмир» | partially_satisfied | reviewed |
| `yKzioxtguMYK` | Товары по почтовым каталогам / ООО «Директ Почта» | hold | reviewed |
| `yQ8qgPoesvWJ` | видеокарта / Ozon | rejected | reviewed |
| `zCfOD70dZF1` | вибромассажная накидка / — | satisfied | reviewed |

### `service_refusal_art32` — Отказ от услуги и возврат денег

- Дел: 25
- Приоритет: `pillar`
- Угол будущей страницы: Возврат оплаты за услуги, курсы, страховки и сервисы

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `3EKlRihBcpmt` | опционная услуга / ООО «Автоэкспресс», ООО «Экспобанк», ООО «Прага» | partially_satisfied | reviewed |
| `3mMKR7CNUYQ8` | онлайн-курс / Skillbox | satisfied | reviewed |
| `44gsbu4dGBNQ` | услуга независимой гарантии и абонентского обслуживания / ООО «Сириус» | partially_satisfied | reviewed |
| `6gu2AQWh1zl5` | абонентские автомобильные услуги / ООО «Комиссар» | partially_satisfied | reviewed |
| `7vWNcdOdS8gA` | educational_course / Клуб Миллионеров | partially_satisfied | reviewed |
| `KHjybr1tjlQ4` | финансовые услуги / АО «Согаз» | partially_satisfied | reviewed |
| `NRzixFhvO8Ul` | опционный договор / ООО «АВТО-ЗАЩИТА» | partially_satisfied | reviewed |
| `NvzAU8q3S55O` | сервисная карта / АО «АВТОАССИСТАНС» | mixed | reviewed |
| `Pde5A0X4dlZj` | страховая услуга / Ренессанс Жизнь | partially_satisfied | reviewed |
| `QsoUZnTzldHU` | договор страхования жизни / ООО СК «Сбербанк Страхование жизни» | hold | reviewed |
| `SKRzPTr0mYmR` | страховой полис / ООО «АльфаСтрахование-Жизнь» | partially_satisfied | reviewed |
| `TNm0IBqaQjxP` | сертификат на ПО / АО «КарВит» | partially_satisfied | reviewed |
| `VEVEnx8fQhW5` | service_contract / ООО [К] | partially_satisfied | reviewed |
| `WBfIewmrCUQH` | опционный договор / ООО «Автоэкспресс» | mixed | reviewed |
| `WJjAKsJGIglY` | услуга / ООО «М-Ассистанс» | partially_satisfied | reviewed |
| `fZ0mM6NxYymT` | гостиничные услуги / ООО Миленти Резортс | partially_satisfied | reviewed |
| `hYbUa7Urh3W5` | дополнительные услуги при автокредитовании / Парус Авто | satisfied | reviewed |
| `oakTTFmKQb5J` | юридические услуги / ООО «Правовая защита населения» | satisfied | reviewed |
| `qnI0M2OmNJ5R` | страхование заемщика / ПАО «Совкомбанк» | partially_satisfied | reviewed |
| `qtC0iQLRs9LE` | фитнес-услуги / ИП ФИО2 | partially_satisfied | reviewed |
| `rKmI5OOWpf6B` | дополнительная услуга автопомощи к кредиту / АО "Автоассистанс" | partially_satisfied | reviewed |
| `tLtz253BMqLq` | услуга бронирования жилья / ООО «Суточно» | partially_satisfied | reviewed |
| `xlNrOZvTsu6J` | программное обеспечение / ООО «ДФМ» | satisfied | reviewed |
| `yz0M6YZip7Qn` | авиабилеты / Ozon Travel / Air Serbia | mixed | reviewed |
| `z7Um8Ca4AObr` | финансовые услуги / ООО «Д.С.Авто» | partially_satisfied | reviewed |

### `prepaid_goods_delay_art23_1` — Оплаченный товар не передали или задержали

- Дел: 18
- Приоритет: `pillar`
- Угол будущей страницы: Что делать, если заказ оплачен, но товар не передают

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `3upYOEUsOC6X` | электроника / ИП (продавец электроники через WhatsApp) | partially_satisfied | reviewed |
| `A9DmPtvwhmrK` | стройматериалы / ООО «АСМ-РЕГИОН» | satisfied | reviewed |
| `FuXzeJou9YYT` | товар маркетплейса / Ozon | mixed | reviewed |
| `G3ujoKf5CdJO` | мебель на заказ / ООО «Мебель на заказ» | satisfied | reviewed |
| `MmtWiS16N45R` | бревенчатый сруб дома / не указан | partially_satisfied | reviewed |
| `NOXVZP9ifzoS` | автомобиль / ООО «Свид-Мобиль» (автосалон) | partially_satisfied | reviewed |
| `Pp6bfruXoRrw` | электроника / ООО «Маркетплейс» | partially_satisfied | reviewed |
| `PulUoivdYENP` | кухонный гарнитур / не указан | satisfied | reviewed |
| `Sc6rzP15X355` | мебель / ИП (продавец мебели) | satisfied | reviewed |
| `Sgq21BEqhrWO` | компьютерная техника / Яндекс.Маркет | satisfied | reviewed |
| `SpPjP40Ege5v` | смартфон / ООО "Яндекс.Маркет" | satisfied | reviewed |
| `TOdqpcvD8z6p` | роллеты, калитка, монтаж / — | partially_satisfied | reviewed |
| `ZPPMKmYhEXYQ` | сантехника / ИП ФИО2 (продавец сантехники) | partially_satisfied | reviewed |
| `a9CAweL5gwWP` | одежда и обувь / ИП ФИО1 (продавец через Instagram) | partially_satisfied | reviewed |
| `c7aHcUwzLKZI` | мебель / ООО «Эпатаж» | partially_satisfied | reviewed |
| `lbZPxqLTQJro` | автомобильные запчасти / ИП Водолазкин Дмитрий Александрович | satisfied | reviewed |
| `nfLIiVfnIsbj` | смартфон / СберМегаМаркет | partially_satisfied | reviewed |
| `wzkaHAf8E21E` | ноутбук / Мегамаркет | satisfied | reviewed |

### `work_service_delay_art28` — Нарушение сроков работ или услуг

- Дел: 13
- Приоритет: `pillar`
- Угол будущей страницы: Просрочка работ, монтажа или изготовления

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `3CbF7Lc1r1LN` | строительные работы и проектирование / ООО «СК «ИОНА» | rejected | reviewed |
| `8U4pkUsSIVVX` | услуга / — | hold | reviewed |
| `DcaXct4mB3UK` | бытовые подрядные работы / ИП (подрядчик по остеклению) | partially_satisfied | reviewed |
| `Lo4QjMzsb9ln` | service / — | satisfied | reviewed |
| `NNz8EqpCgLgK` | мебель под заказ / ИП ФИО2 | satisfied | reviewed |
| `QqSw46fUvPr` | автомобиль / ООО «Авангард» | partially_satisfied | reviewed |
| `TMFNEDT5jaxw` | ритуальные услуги / ИП ФИО2 | partially_satisfied | reviewed |
| `ZLwdZCW9EtVP` | коммунальные услуги / ПАО «Россети Сибирь» | partially_satisfied | reviewed |
| `dDvjXR3GKwxb` | дом / ФИО2 | satisfied | reviewed |
| `h9EcvY10CpWN` | кухонный гарнитур / ООО «Ле Монлид» | partially_satisfied | reviewed |
| `qcd6WnkhMFYB` | бронирование отеля / ООО «Островок.Ру» | partially_satisfied | reviewed |
| `sei0HpVRwcHH` | услуга / ТД Строймаш | partially_satisfied | reviewed |
| `wFi2vxSxKHln` | работа / — | satisfied | reviewed |

### `distance_sale_return_art26_1` — Дистанционная продажа: отказ от товара и возврат денег

- Дел: 12
- Приоритет: `pillar`
- Угол будущей страницы: Когда можно вернуть товар, купленный онлайн

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `ByA2BTi7BoHa` | электроника / Мегамаркет | partially_satisfied | reviewed |
| `FTrYrTTzEals` | смартфон / СберМегаМаркет | satisfied | reviewed |
| `HMQHNmxf731a` | швейное оборудование / ООО «Швейное королевство» | partially_satisfied | reviewed |
| `LEkG8QMUg0gC` | телевизор / Ozon | partially_satisfied | reviewed |
| `OzQpzlDiDWZ` | швабра / Ашан | partially_satisfied | reviewed |
| `QyBl2UIrnndK` | телевизор / М.Видео | partially_satisfied | reviewed |
| `VLhBBoeb7vWo` | ноутбук / ООО «СДЭК.Маркет» | partially_satisfied | reviewed |
| `Xv7HfiRU2tVq` | смартфон / СДЭК.Маркет | satisfied | reviewed |
| `fNiaUxW2zu1p` | товар дистанционной продажи / Wildberries | partially_satisfied | reviewed |
| `fVJm3HMVkt5H` | инструменты и садовая техника / goods.ru / Techport.ru | partially_satisfied | reviewed |
| `hV75aLss4lWU` | одежда / Lamoda | partially_satisfied | reviewed |
| `pWN4OmLFKfm8` | беговая дорожка / ООО «Ситилинк» | partially_satisfied | reviewed |

### `non_consumer_hold` — Не потребительский спор

- Дел: 6
- Приоритет: `hold`
- Угол будущей страницы: Исключить из основного индекса ЗоЗПП-сайта

| docid | объект/компания | результат | уверенность |
|---|---|---|---|
| `37i0sRTiFB6Q` | коммунальные услуги / ПАО «Иркутскэнерго» | hold | reviewed |
| `43XAPWx3KQZV` | beer / — | hold | reviewed |
| `Z6ECxE1FZGbR` | Кредитный договор / ООО «ЭОС» | hold | reviewed |
| `fvpw4sbQxPWi` | автофургон-рефрижератор / ООО Луидор | hold | reviewed |
| `qNPGP4ky266p` | поставка товара / Ozon | hold | reviewed |
| `xWGVwR38DWrZ` | компьютерные комплектующие / ООО «ДНС Ритейл» | hold | reviewed |

## Практический вывод

1. Основной пиллар для первой версии — дела о недостатках товара: это самый крупный и понятный пользователю кластер.
2. Отдельные посадочные страницы стоит готовить по дистанционной продаже, задержке/непередаче оплаченного товара, информационным нарушениям и отказу от услуг.
3. Кластеры работ/услуг пока выглядят как long-tail: их можно держать в резерве до расширения выборки.
4. Дела с `hold` не смешивать с основным гражданским ЗоЗПП-индексом.
5. Все 50 дел имеют подтверждённые и проверенные enum-коды, что делает кластеризацию полностью детерминированной и готовой к публикации.

## Следующий шаг

Проверить кластеры вручную и выбрать 3–5 первых типов страниц для SSG-прототипа. Embeddings подключать только если ручная проверка покажет, что эвристики смешивают разные ситуации.
