# ЗАДАЧА ДЛЯ ANTIGRAVITY: проверка enum-предложений Фазы 1.2

Этот файл — отдельная задача для ИИ-агента Antigravity.  
Используй встроенную модель Antigravity/Gemini. Не вызывай DeepSeek API, OpenAI API
или другие внешние LLM/API.

## 0. Сначала восстанови контекст проекта

Перед началом прочитай:

1. `AGENTS.md`
2. `START-HERE.md`
3. `assistant-memory.md`
4. `technical-specification-mvp.md`
5. `memory/current-work-queue.md`
6. `memory/2026-06-25.md`
7. `data/reference/zpp_enum_dictionary.json`
8. `data/review/phase1-2-gold-sample.md`
9. `data/review/phase1-2-enum-suggestions.md`
10. `data/review/phase1-2-enum-suggestions.csv`

Если какой-то файл отсутствует — отметь это в итоговом отчёте и продолжай по
доступным данным.

## 1. Цель задачи

Проверить предложения по нормализации enum для 25 дел эталонной выборки.

Нужно определить, подходят ли предложенные значения:

- `suggested_dispute_type_code`
- `suggested_claim_type_codes`
- `suggested_result_type`
- `suggested_platform_norm`
- `suggested_object_type_norm`
- `suggested_index_policy`
- `suggested_main_site_fit`

Подход должен быть юридически прагматичным:

- `dispute_type_code` выбирается преимущественно по конструкции Закона РФ
  «О защите прав потребителей», а не по маркетплейсу, товару или бренду.
- `claim_type_codes` выбираются по способам защиты/требованиям.
- Ситуационные детали вроде Ozon/Wildberries/Яндекс.Маркет, автомобиль, мебель,
  авиабилеты, онлайн-курс должны оставаться в `platform_or_company`,
  `object_type`, `object_name`, `situation_tags`, а не превращаться в отдельные
  `dispute_type_code`.
- Не добавляй новые enum-коды без крайней необходимости. Если кажется, что
  новый код нужен, предложи его в отчёте, но не меняй словарь автоматически.

## 2. Что можно читать для каждого дела

Для каждого `docid` из `data/review/phase1-2-gold-sample.md` можно использовать:

- `data/structured/structure_<docid>.json`
- `data/structured/user_story_<docid>.md`
- `data/structured/practice_<docid>.md`
- `data/raw_acts/act_<docid>.txt`

Рекомендуемый порядок:

1. Сначала смотри `structure_<docid>.json`, `user_story_<docid>.md` и
   `practice_<docid>.md`.
2. Открывай сырой акт `act_<docid>.txt` только если по готовым файлам нельзя
   уверенно проверить enum.

## 3. Что нельзя делать

- Не изменяй `data/structured/structure_*.json`.
- Не изменяй `data/raw_acts/`.
- Не изменяй `data/reference/zpp_enum_dictionary.json`.
- Не редактируй проектную память (`assistant-memory.md`, `memory/*.md`).
- Не переписывай `data/review/phase1-2-enum-suggestions.csv` как единственный экземпляр.
  Создай отдельный reviewed-файл.
- Не выдумывай ссылки на нормы/практику. Если правовая конструкция не ясна из
  материалов дела — ставь `fix` или `needs_human`.

## 4. Выходные файлы

Создай два файла:

1. `data/review/phase1-2-enum-suggestions.reviewed.csv`
2. `data/review/phase1-2-enum-review-by-antigravity.md`

### 4.1 CSV

Возьми исходный `data/review/phase1-2-enum-suggestions.csv` и сохрани копию с
добавленными/заполненными колонками:

- `review_decision`
- `review_comment`
- `final_dispute_type_code`
- `final_claim_type_codes`
- `final_result_type`
- `final_platform_norm`
- `final_object_type_norm`
- `final_index_policy`
- `final_main_site_fit`

Значения `review_decision`:

- `ok` — предложение можно принять без правки.
- `fix` — предложение в целом полезно, но в final-колонках нужна правка.
- `needs_human` — нужна ручная юридическая проверка.
- `exclude` — дело не подходит основному ЗоПП-сайту и должно быть `hold`.

Если `review_decision = ok`, final-колонки должны повторять suggested-значения.

Если `review_decision = fix`, заполни final-колонки исправленными значениями и
кратко объясни причину в `review_comment`.

### 4.2 Markdown-отчёт

Создай краткий отчёт:

```md
# Проверка enum-предложений Antigravity

## Итог
- всего проверено:
- ok:
- fix:
- needs_human:
- exclude:

## Частые замечания
- ...

## Дела с правками

### <docid>
- было:
- стало:
- почему:

## Предложения по словарю
- новые коды не требуются / требуются: ...
```

## 5. Критерии проверки по ключевым enum

### `dispute_type_code`

Сверяй с `data/reference/zpp_enum_dictionary.json`.

Главные варианты для текущей партии:

- `goods_defect_art18` — товар с недостатком.
- `prepaid_goods_delay_art23_1` — предоплаченный товар не передан вовремя.
- `distance_sale_return_art26_1` — отказ от товара при дистанционной продаже.
- `info_violation_art10_12` — спор об информации о товаре/продавце/агрегаторе.
- `aggregator_prepayment_art12_2_2` — специальный возврат предоплаты через
  владельца агрегатора.
- `work_service_defect_art29` — недостатки работы/услуги.
- `work_service_delay_art28` — нарушение сроков работы/услуги.
- `service_refusal_art32` — отказ потребителя от договора работ/услуг.
- `contract_validity_non_zpp` — спор о заключённости/исполнении договора, не
  являющийся самостоятельным способом защиты по ЗоЗПП.
- `non_consumer_hold` — непотребительский спор, вне основного сайта.

### `claim_type_codes`

Это список. Можно использовать несколько кодов:

- `refund_price`
- `replacement`
- `repair_or_defect_cure`
- `price_reduction`
- `repeat_work`
- `price_difference`
- `penalty`
- `damages`
- `moral_damage`
- `consumer_fine`
- `expenses`
- `compel_transfer`
- `information_disclosure`
- `contract_recognition`
- `insurance_premium_refund`
- `debt_dispute`
- `hold`

### `result_type`

- `satisfied` — требования удовлетворены полностью или почти полностью.
- `partially_satisfied` — требования удовлетворены частично.
- `rejected` — в иске отказано.
- `mixed` — разные ответчики/требования решены по-разному.
- `hold` — дело нецелевое для основного индекса/вертикали.

## 6. Особое внимание

Проверь особенно внимательно:

- `yQ8qgPoesvWJ` — Ozon как агрегатор; возможно `info_violation_art10_12` или
  иной код, но не отдельный брендовый код.
- `FuXzeJou9YYT` — частичный успех к продавцу и отказ к Ozon; вероятно `mixed`.
- `yz0M6YZip7Qn` — Ozon Travel / Air Serbia; важно не смешать агентскую
  ответственность и отказ от услуги.
- `LEM5MFXCKK6L` — понуждение к исполнению заказа; проверить, не лучше ли
  `contract_validity_non_zpp`.
- `flVxOoBiwCr8` — услуги связи и спор о заключённости договора/задолженности.
- `Pde5A0X4dlZj` — страховая премия; пограничная тема.
- `qNPGP4ky266p` — уже помечен как непотребительский `hold`; проверить и,
  вероятно, оставить вне основного сайта.
- `YFjMxNYLsLlX` и `OzQpzlDiDWZ` — в исходных JSON были англоязычные значения;
  проверить нормализацию.

## 7. Стиль результата

Пиши коротко и прикладно. Не нужно длинное правовое заключение по каждому делу.
Нужны проверенные enum-решения, которые можно затем применить скриптом к JSON.
