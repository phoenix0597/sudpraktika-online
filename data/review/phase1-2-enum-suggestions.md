# Фаза 1.2 — предложения по нормализации enum

Статус: предложения для ручного выбора/коррекции, не автоприменение.

Задача: вместо ручного заполнения с нуля выбрать нормализованные значения для ключевых enum-полей.

## Словари значений

### dispute_type_code

- `goods_defect_art18` — товар с недостатком (ЗоЗПП ст. 18)
- `prepaid_goods_delay_art23_1` — нарушение срока передачи предварительно оплаченного товара (ЗоЗПП ст. 23.1)
- `distance_sale_return_art26_1` — отказ от товара при дистанционной продаже (ЗоЗПП ст. 26.1)
- `info_violation_art10_12` — ненадлежащая информация о товаре, услуге, продавце или агрегаторе (ЗоЗПП ст. 10, ЗоЗПП ст. 12)
- `aggregator_prepayment_art12_2_2` — возврат предоплаты через владельца агрегатора (ЗоЗПП ст. 12 п. 2.2)
- `work_service_defect_art29` — недостатки работы или услуги (ЗоЗПП ст. 29)
- `work_service_delay_art28` — нарушение сроков выполнения работы или оказания услуги (ЗоЗПП ст. 28)
- `service_refusal_art32` — отказ потребителя от договора работ или услуг (ЗоЗПП ст. 32)
- `contract_validity_non_zpp` — спор о заключенности или исполнении договора вне самостоятельного способа защиты ЗоЗПП
- `non_consumer_hold` — непотребительский спор

### claim_type_codes

- `refund_price` — возврат цены или предоплаты (ЗоЗПП ст. 18, ЗоЗПП ст. 23.1, ЗоЗПП ст. 26.1, ЗоЗПП ст. 28, ЗоЗПП ст. 29, ЗоЗПП ст. 32)
- `replacement` — замена товара (ЗоЗПП ст. 18)
- `repair_or_defect_cure` — безвозмездное устранение недостатков (ЗоЗПП ст. 18, ЗоЗПП ст. 29)
- `price_reduction` — соразмерное уменьшение цены (ЗоЗПП ст. 18, ЗоЗПП ст. 29)
- `repeat_work` — повторное выполнение работы или изготовление вещи (ЗоЗПП ст. 29)
- `price_difference` — разница в цене (ЗоЗПП ст. 24)
- `penalty` — неустойка (ЗоЗПП ст. 23, ЗоЗПП ст. 23.1, ЗоЗПП ст. 28, ЗоЗПП ст. 31)
- `damages` — убытки (ЗоЗПП ст. 13, ЗоЗПП ст. 18, ЗоЗПП ст. 29)
- `moral_damage` — компенсация морального вреда (ЗоЗПП ст. 15)
- `consumer_fine` — штраф 50% (ЗоЗПП ст. 13 п. 6)
- `expenses` — судебные, экспертные и иные расходы
- `compel_transfer` — обязать передать товар (ЗоЗПП ст. 23.1)
- `information_disclosure` — обязать предоставить информацию (ЗоЗПП ст. 10, ЗоЗПП ст. 12)
- `contract_recognition` — признать договор заключенным или незаключенным
- `insurance_premium_refund` — возврат страховой премии (ЗоЗПП ст. 32)
- `debt_dispute` — оспаривание задолженности или начислений
- `hold` — нецелевой для основного сайта спор

### result_type

- `satisfied` — требования удовлетворены полностью или почти полностью
- `partially_satisfied` — требования удовлетворены частично
- `rejected` — в иске отказано
- `mixed` — смешанный исход: разные ответчики или требования решены по-разному
- `hold` — дело не подходит для основного индекса/вертикали

### publication_index_policy

- `index` — можно индексировать после обычной редакционной проверки
- `hold` — держать вне индекса/основного сайта до отдельного решения

## Как править

- Если предложение корректно — в CSV можно поставить `review_decision = ok`.
- Если нужно исправить — поставить `review_decision = fix` и указать значение в `review_comment`.
- Если дело не нужно основному сайту — `suggested_result_type = hold`, `suggested_index_policy = hold`, `suggested_main_site_fit = False`.

## Предложения по делам

### 1. `yQ8qgPoesvWJ`

- `dispute_type`: 'спор об ответственности владельца агрегатора перед потребителем'
  - предложение: `info_violation_art10_12` — ответственность маркетплейса/агрегатора за товар продавца
- `claim_type`: 'взыскание разницы в стоимости товара, убытков, неустойки, компенсации морального вреда'
  - предложение: `price_difference; damages; penalty; moral_damage; consumer_fine`
- `result_type`: 'отказ в удовлетворении иска'; `focus_party_result`: 'проигрыш'
  - предложение: `rejected`
- `platform_or_company`: 'Ozon (ООО «Интернет Решения»)'
  - предложение: `Ozon`
- `object_type`: 'видеокарта'
  - предложение: `видеокарта`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: отказ к Ozon из-за статуса агрегатора, полезный отказной кейс
- решение юриста: 
- комментарий: 

### 2. `FuXzeJou9YYT`

- `dispute_type`: 'односторонний отказ продавца от исполнения договора купли-продажи, нарушение срока передачи предварительно оплаченного товара'
  - предложение: `prepaid_goods_delay_art23_1` — маркетплейс/продавец не передал оплаченный товар
- `claim_type`: 'обязание передать товар, взыскание неустойки, компенсации морального вреда, штрафа, судебных расходов'
  - предложение: `compel_transfer; penalty; moral_damage; consumer_fine; expenses`
- `result_type`: 'иск удовлетворён частично'; `focus_party_result`: 'иск удовлетворён частично (к ИП ФИО2); в иске к ООО «Интернет Решения» отказано'
  - предложение: `mixed`
- `platform_or_company`: 'Ozon (ООО «Интернет Решения»)'
  - предложение: `Ozon`
- `object_type`: 'товар'
  - предложение: `товар маркетплейса`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: иск удовлетворён к продавцу, но отказан к Ozon
- решение юриста: 
- комментарий: 

### 3. `Yse5NQ5b8YbO`

- `dispute_type`: 'возврат денег за некачественный телевизор, приобретенный дистанционно'
  - предложение: `goods_defect_art18` — возврат денег за некачественный телевизор с маркетплейса
- `claim_type`: 'возврат цены товара с недостатками, неустойка, компенсация морального вреда, штраф, возмещение расходов'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine; expenses`
- `result_type`: 'частичное удовлетворение иска'; `focus_party_result`: 'частично удовлетворены'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'ООО «Интернет Решения» (Ozon)'
  - предложение: `Ozon`
- `object_type`: 'Телевизор'
  - предложение: `телевизор`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: частичный успех, есть астрент/возврат товара
- решение юриста: 
- комментарий: 

### 4. `yz0M6YZip7Qn`

- `dispute_type`: 'возврат стоимости авиабилетов при вынужденном отказе от перевозки'
  - предложение: `service_refusal_art32` — возврат авиабилетов и ответственность агента/перевозчика
- `claim_type`: 'возврат стоимости билетов, компенсация морального вреда, штраф'
  - предложение: `refund_price; moral_damage; consumer_fine`
- `result_type`: 'частично удовлетворено'; `focus_party_result`: 'частичное удовлетворение (против авиакомпании, отказ в иске к агенту, отказ во взыскании штрафа)'
  - предложение: `mixed`
- `platform_or_company`: 'Ozon Travel, Air Serbia'
  - предложение: `Ozon Travel / Air Serbia`
- `object_type`: 'авиабилеты'
  - предложение: `авиабилеты`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: частично против перевозчика, отказ к агенту и в штрафе
- решение юриста: 
- комментарий: 

### 5. `LEkG8QMUg0gC`

- `dispute_type`: 'возврат товара надлежащего качества, приобретенного дистанционным способом'
  - предложение: `distance_sale_return_art26_1` — возврат товара надлежащего качества при дистанционной покупке
- `claim_type`: 'возврат стоимости товара, неустойка, штраф, компенсация морального вреда, судебные расходы'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine; expenses`
- `result_type`: 'partially_satisfied'; `focus_party_result`: 'partially_satisfied'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'Ozon'
  - предложение: `Ozon`
- `object_type`: 'телевизор'
  - предложение: `телевизор`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: классический дистанционный отказ без недостатка
- решение юриста: 
- комментарий: 

### 6. `DvLR6OZqCqt`

- `dispute_type`: 'спор о раскрытии информации агрегатором'
  - предложение: `info_violation_art10_12` — требование раскрыть информацию о продавцах на маркетплейсах
- `claim_type`: 'обязание предоставить информацию, компенсация морального вреда, неустойка'
  - предложение: `information_disclosure; moral_damage; penalty`
- `result_type`: 'отказ в удовлетворении иска'; `focus_party_result`: 'проигрыш'
  - предложение: `rejected`
- `platform_or_company`: 'Lamoda.ru, Яндекс.Маркет, Ozon.ru, Wildberries.ru'
  - предложение: `несколько маркетплейсов`
- `object_type`: ''
  - предложение: `информация о продавце`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: важный отказной кейс по информационным обязанностям агрегаторов
- решение юриста: 
- комментарий: 

### 7. `qVUccWRuFprb`

- `dispute_type`: 'отсутствие обязательной информации о товаре на сайте агрегатора'
  - предложение: `info_violation_art10_12` — недостаточная информация о товаре на маркетплейсе
- `claim_type`: 'компенсация морального вреда'
  - предложение: `moral_damage`
- `result_type`: 'отказ в удовлетворении иска'; `focus_party_result`: 'проигрыш'
  - предложение: `rejected`
- `platform_or_company`: 'Wildberries'
  - предложение: `Wildberries`
- `object_type`: 'зарядные устройства'
  - предложение: `зарядное устройство`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: информационный спор, отказ из-за недоказанности нарушения
- решение юриста: 
- комментарий: 

### 8. `1w89Nc1UMNmm`

- `dispute_type`: 'возврат игровой приставки ненадлежащего качества'
  - предложение: `goods_defect_art18` — возврат игровой приставки с недостатком
- `claim_type`: 'расторжение договора купли-продажи, возврат уплаченной за товар суммы, компенсация морального вреда, штраф, неустойка'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine`
- `result_type`: 'satisfied'; `focus_party_result`: 'satisfied_partially'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'Wildberries'
  - предложение: `Wildberries`
- `object_type`: 'игровая консоль'
  - предложение: `игровая приставка`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: формально satisfied в JSON, но суммы/штраф обычно требуют частичной квалификации
- решение юриста: 
- комментарий: 

### 9. `LEM5MFXCKK6L`

- `dispute_type`: 'признание договора купли-продажи заключенным и понуждение к исполнению договора'
  - предложение: `contract_validity_non_zpp` — понуждение маркетплейса к исполнению заказа
- `claim_type`: 'признание договора заключенным, понуждение к исполнению договора'
  - предложение: `contract_recognition; compel_transfer`
- `result_type`: 'defeated'; `focus_party_result`: 'defeated'
  - предложение: `rejected`
- `platform_or_company`: 'Wildberries'
  - предложение: `Wildberries`
- `object_type`: 'смартфон'
  - предложение: `смартфон`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: иск проигран, полезно для сценария «заказ не считается заключённым»
- решение юриста: 
- комментарий: 

### 10. `fNiaUxW2zu1p`

- `dispute_type`: 'возврат цены при отказе от товара, купленного дистанционно'
  - предложение: `distance_sale_return_art26_1` — возврат товара при отказе от дистанционной покупки
- `claim_type`: 'возврат цены, проценты, моральный вред, штраф'
  - предложение: `refund_price; moral_damage; consumer_fine`
- `result_type`: 'частичное удовлетворение'; `focus_party_result`: 'частичное удовлетворение иска'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'ООО "Вайлдберриз"'
  - предложение: `Wildberries`
- `object_type`: ''
  - предложение: `товар дистанционной продажи`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: дистанционный отказ, частичное удовлетворение
- решение юриста: 
- комментарий: 

### 11. `7hRq36xc81l6`

- `dispute_type`: 'возврат стоимости товара ненадлежащего качества'
  - предложение: `goods_defect_art18` — возврат смартфона с заявленным недостатком
- `claim_type`: 'возврат цены, неустойка, компенсация морального вреда, штраф'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine`
- `result_type`: 'отказ в удовлетворении иска'; `focus_party_result`: 'проиграл'
  - предложение: `rejected`
- `platform_or_company`: 'Яндекс.Маркет'
  - предложение: `Яндекс.Маркет`
- `object_type`: 'смартфон'
  - предложение: `смартфон`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: отказной кейс по доказательствам недостатка
- решение юриста: 
- комментарий: 

### 12. `v0m4w50eZy5n`

- `dispute_type`: 'возврат стоимости некачественного товара, расторжение договора купли-продажи технически сложного товара из-за существенного недостатка'
  - предложение: `goods_defect_art18` — возврат технически сложного товара с недостатком
- `claim_type`: 'возврат цены, разница в цене, неустойка, моральный вред, судебные расходы'
  - предложение: `refund_price; price_difference; penalty; moral_damage; expenses`
- `result_type`: 'частичное удовлетворение'; `focus_party_result`: 'частичное удовлетворение'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'Яндекс.Маркет'
  - предложение: `Яндекс.Маркет`
- `object_type`: 'планшет'
  - предложение: `планшет`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: технически сложный товар, частичный успех
- решение юриста: 
- комментарий: 

### 13. `yc651JdA4PJC`

- `dispute_type`: 'ненадлежащее качество технически сложного товара'
  - предложение: `goods_defect_art18` — возврат ноутбука ненадлежащего качества
- `claim_type`: 'возврат стоимости товара, неустойка, штраф, компенсация морального вреда, убытки, расходы на экспертизу'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine; damages; expenses`
- `result_type`: 'частичное удовлетворение'; `focus_party_result`: 'частичное удовлетворение'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'Яндекс.Маркет'
  - предложение: `Яндекс.Маркет`
- `object_type`: 'ноутбук'
  - предложение: `ноутбук`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: частичное удовлетворение с низкой присуждённой суммой
- решение юриста: 
- комментарий: 

### 14. `3mMKR7CNUYQ8`

- `dispute_type`: 'возврат денег за онлайн-обучение'
  - предложение: `service_refusal_art32` — возврат денег за онлайн-обучение
- `claim_type`: 'возврат уплаченной по договору денежной суммы, штраф'
  - предложение: `refund_price; consumer_fine`
- `result_type`: 'satisfied'; `focus_party_result`: 'satisfied'
  - предложение: `satisfied`
- `platform_or_company`: 'Skillbox'
  - предложение: `Skillbox`
- `object_type`: 'онлайн-курс'
  - предложение: `онлайн-курс`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: услуги, не товар; полезно как расширение ЗоПП
- решение юриста: 
- комментарий: 

### 15. `flVxOoBiwCr8`

- `dispute_type`: 'Спор о заключенности договора оказания услуг связи и оплате фактически оказанных услуг'
  - предложение: `contract_validity_non_zpp` — спор по договору услуг связи и начислениям
- `claim_type`: 'Признание договора незаключенным, оспаривание задолженности, требование о признании прав потребителя'
  - предложение: `contract_recognition; debt_dispute`
- `result_type`: 'отказ в иске'; `focus_party_result`: 'В удовлетворении исковых требований отказано в полном объёме.'
  - предложение: `rejected`
- `platform_or_company`: 'ПАО «Ростелеком»'
  - предложение: `Ростелеком`
- `object_type`: 'Услуги связи и оборудование'
  - предложение: `услуги связи`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: полный отказ, полезно проверить нецелевые/слабые требования
- решение юриста: 
- комментарий: 

### 16. `Pde5A0X4dlZj`

- `dispute_type`: 'отказ в возврате страховой премии при досрочном отказе от страхования'
  - предложение: `service_refusal_art32` — возврат страховой премии
- `claim_type`: 'возврат уплаченной суммы, неустойка, компенсация морального вреда, штраф'
  - предложение: `insurance_premium_refund; penalty; moral_damage; consumer_fine`
- `result_type`: 'satisfaction_partially'; `focus_party_result`: 'частичное удовлетворение иска'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'ООО «СК «Ренессанс Жизнь»'
  - предложение: `Ренессанс Жизнь`
- `object_type`: 'страховая премия'
  - предложение: `страховая услуга`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: пограничная, но потребительская услуга; оставить на проверку
- решение юриста: 
- комментарий: 

### 17. `qNPGP4ky266p`

- `dispute_type`: 'взыскание задолженности по договору поставки'
  - предложение: `non_consumer_hold` — непотребительский спор по договору поставки
- `claim_type`: 'возврат суммы предварительной оплаты'
  - предложение: `hold`
- `result_type`: 'полное удовлетворение иска'; `focus_party_result`: 'положительный'
  - предложение: `hold`
- `platform_or_company`: 'ООО «ОЗОН»'
  - предложение: `Ozon`
- `object_type`: 'товар'
  - предложение: `поставка товара`
- `publication`: index_policy='hold', main_site_fit=False
  - предложение: index_policy=`hold`, main_site_fit=`False`
- причина: дело уже помечено как непотребительское; оставить контрольным исключением
- решение юриста: 
- комментарий: 

### 18. `qx9K417NRkWN`

- `dispute_type`: 'возврат уплаченной суммы за автомобиль с существенными недостатками, взыскание убытков, неустойки, морального вреда'
  - предложение: `goods_defect_art18` — возврат автомобиля с существенными недостатками
- `claim_type`: 'возврат стоимости товара, убытки, неустойка, моральный вред, штраф'
  - предложение: `refund_price; damages; penalty; moral_damage; consumer_fine`
- `result_type`: 'частичное удовлетворение'; `focus_party_result`: 'иск удовлетворен частично'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'ООО «УАЗ»'
  - предложение: `УАЗ`
- `object_type`: 'автомобиль'
  - предложение: `автомобиль`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: крупные суммы, классический авто-дефект
- решение юриста: 
- комментарий: 

### 19. `0qwM485PLa1s`

- `dispute_type`: 'возврат автомобиля ненадлежащего качества'
  - предложение: `goods_defect_art18` — возврат автомобиля ненадлежащего качества
- `claim_type`: 'возврат уплаченной за товар суммы, компенсация морального вреда, штраф'
  - предложение: `refund_price; moral_damage; consumer_fine`
- `result_type`: 'satisfied_after_filing'; `focus_party_result`: 'satisfied_partially'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'ООО «Автомир-Трейд»'
  - предложение: `Автомир-Трейд`
- `object_type`: 'автомобиль'
  - предложение: `автомобиль`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: требования удовлетворены после подачи иска, лучше не считать полным выигрышем без проверки
- решение юриста: 
- комментарий: 

### 20. `82RMC7eXBpH4`

- `dispute_type`: 'возврат стоимости некачественного технически сложного товара, взыскание неустойки, компенсации морального вреда и штрафа'
  - предложение: `goods_defect_art18` — возврат технически сложного товара с недостатком
- `claim_type`: 'возврат цены, неустойка, моральный вред, штраф'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine`
- `result_type`: 'полное удовлетворение'; `focus_party_result`: 'полностью удовлетворены'
  - предложение: `satisfied`
- `platform_or_company`: 'ООО «МВМ»'
  - предложение: `М.Видео`
- `object_type`: 'телевизор'
  - предложение: `телевизор`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: сильный потребительский кейс, почти полное удовлетворение
- решение юриста: 
- комментарий: 

### 21. `BRRlQN72V9V6`

- `dispute_type`: 'возврат стоимости технически сложного товара из-за производственного недостатка по истечении гарантийного срока, но в пределах двух лет'
  - предложение: `goods_defect_art18` — возврат технически сложного товара после гарантии, но в пределах двух лет
- `claim_type`: 'возврат цены, неустойка, компенсация морального вреда, возмещение расходов, штраф'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine; expenses`
- `result_type`: 'смешанный'; `focus_party_result`: 'частичное удовлетворение'
  - предложение: `mixed`
- `platform_or_company`: 'ООО «ДНС Ритейл»'
  - предложение: `ДНС`
- `object_type`: 'смартфон'
  - предложение: `смартфон`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: смешанный/частичный исход; проверить бремя доказывания
- решение юриста: 
- комментарий: 

### 22. `PulUoivdYENP`

- `dispute_type`: 'Непоставка предварительно оплаченного товара'
  - предложение: `prepaid_goods_delay_art23_1` — непоставка предварительно оплаченного товара
- `claim_type`: 'возврат предоплаты, неустойка, компенсация морального вреда, штраф'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine`
- `result_type`: 'Удовлетворено'; `focus_party_result`: 'Иск удовлетворен полностью'
  - предложение: `satisfied`
- `platform_or_company`: ''
  - предложение: `не указан`
- `object_type`: 'Кухонный гарнитур'
  - предложение: `кухонный гарнитур`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: полное удовлетворение, хороший positive-case
- решение юриста: 
- комментарий: 

### 23. `MmtWiS16N45R`

- `dispute_type`: 'нарушение срока передачи предварительно оплаченного товара'
  - предложение: `prepaid_goods_delay_art23_1` — нарушение срока передачи предварительно оплаченного товара
- `claim_type`: 'возврат аванса, неустойка, компенсация морального вреда, штраф, судебные расходы'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine; expenses`
- `result_type`: 'partially_granted'; `focus_party_result`: 'частично удовлетворено'
  - предложение: `partially_satisfied`
- `platform_or_company`: ''
  - предложение: `не указан`
- `object_type`: 'бревенчатый сруб дома'
  - предложение: `бревенчатый сруб дома`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: частичное удовлетворение по предоплате/срокам
- решение юриста: 
- комментарий: 

### 24. `YFjMxNYLsLlX`

- `dispute_type`: 'product_defect_and_refund'
  - предложение: `goods_defect_art18` — комплектность мебели и возврат расходов
- `claim_type`: 'refund_and_penalties'
  - предложение: `refund_price; penalty; moral_damage; consumer_fine; damages; expenses`
- `result_type`: 'judgment_for_plaintiff'; `focus_party_result`: 'partially_satisfied'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'ООО «Торговый Дом «Лазурит»'
  - предложение: `Лазурит`
- `object_type`: 'furniture'
  - предложение: `мебель`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: текущее JSON содержит англоязычные enum; требуется нормализация
- решение юриста: 
- комментарий: 

### 25. `OzQpzlDiDWZ`

- `dispute_type`: 'refusal to accept return of quality goods bought online, misleading about store location, wrongful deadline calculation'
  - предложение: `distance_sale_return_art26_1` — отказ принять возврат товара надлежащего качества онлайн
- `claim_type`: 'refund of purchase price, moral damages, statutory fine'
  - предложение: `refund_price; moral_damage; consumer_fine`
- `result_type`: 'иск удовлетворен в части: обязан принять товар, взысканы стоимость, моральный вред и штраф; в требовании о неустойке отказано'; `focus_party_result`: 'частично удовлетворены'
  - предложение: `partially_satisfied`
- `platform_or_company`: 'ООО «Ашан»'
  - предложение: `Ашан`
- `object_type`: 'швабра'
  - предложение: `швабра`
- `publication`: index_policy='index', main_site_fit=True
  - предложение: index_policy=`index`, main_site_fit=`True`
- причина: текущее JSON содержит англоязычные enum; полезен для дистанционного возврата
- решение юриста: 
- комментарий: 
