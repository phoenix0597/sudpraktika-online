# Проверка enum-предложений Antigravity

## Итог
- всего проверено: 25
- ok: 17
- fix: 7
- needs_human: 0
- exclude: 1

## Частые замечания
- В некоторых делах в `suggested_claim_type_codes` отсутствовали требования, которые были заявлены истцом согласно материалам дела (например, неустойка `penalty` или расходы `expenses`). Эти требования были восстановлены и добавлена информация в `final_claim_type_codes` для обеспечения полноты данных.
- Непотребительский спор по договору поставки (`qNPGP4ky266p`) был исключён с установкой статуса `exclude`, `dispute_type_code = non_consumer_hold` и переводом всех зависимых полей в `hold` / `False`.
- Нормализация англоязычных enum для дел `YFjMxNYLsLlX` и `OzQpzlDiDWZ` выполнена корректно, при этом в `OzQpzlDiDWZ` добавлена неустойка (`penalty`), которая заявлялась истцом, но была отклонена судом по существу.

## Дела с правками

### DvLR6OZqCqt
- **Было (suggested_claim_type_codes):** `information_disclosure; moral_damage; penalty`
- **Стало (final_claim_type_codes):** `information_disclosure; moral_damage; penalty; consumer_fine`
- **Почему:** Добавлены отсутствующие коды требований: consumer_fine

### 1w89Nc1UMNmm
- **Было (suggested_claim_type_codes):** `refund_price; penalty; moral_damage; consumer_fine`
- **Стало (final_claim_type_codes):** `refund_price; penalty; moral_damage; consumer_fine; expenses`
- **Почему:** Добавлены отсутствующие коды требований: expenses

### fNiaUxW2zu1p
- **Было (suggested_claim_type_codes):** `refund_price; moral_damage; consumer_fine`
- **Стало (final_claim_type_codes):** `refund_price; moral_damage; consumer_fine; expenses`
- **Почему:** Добавлены отсутствующие коды требований: expenses

### 7hRq36xc81l6
- **Было (suggested_claim_type_codes):** `refund_price; penalty; moral_damage; consumer_fine`
- **Стало (final_claim_type_codes):** `refund_price; penalty; moral_damage; consumer_fine; expenses`
- **Почему:** Добавлены отсутствующие коды требований: expenses

### qNPGP4ky266p (Исключено)
- **Было:** suggested_dispute_type_code = `non_consumer_hold`, suggested_index_policy = `hold`
- **Стало:** final_dispute_type_code = `non_consumer_hold`, final_index_policy = `hold`, final_main_site_fit = `False`
- **Почему:** Непотребительский спор по договору поставки (между юрлицами/ИП). Исключено из индекса.

### qx9K417NRkWN
- **Было (suggested_claim_type_codes):** `refund_price; damages; penalty; moral_damage; consumer_fine`
- **Стало (final_claim_type_codes):** `refund_price; damages; penalty; moral_damage; consumer_fine; expenses`
- **Почему:** Добавлены отсутствующие коды требований: expenses

### 82RMC7eXBpH4
- **Было (suggested_claim_type_codes):** `refund_price; penalty; moral_damage; consumer_fine`
- **Стало (final_claim_type_codes):** `refund_price; penalty; moral_damage; consumer_fine; expenses`
- **Почему:** Добавлены отсутствующие коды требований: expenses

### OzQpzlDiDWZ
- **Было (suggested_claim_type_codes):** `refund_price; moral_damage; consumer_fine`
- **Стало (final_claim_type_codes):** `refund_price; moral_damage; consumer_fine; penalty`
- **Почему:** Добавлен код penalty в claim_type_codes, так как неустойка заявлялась в иске.

## Предложения по словарю
- Новые коды не требуются. Все проверенные дела отлично укладываются в существующую таксономию `data/reference/zpp_enum_dictionary.json`.
