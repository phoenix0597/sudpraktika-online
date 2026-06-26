# -*- coding: utf-8 -*-
"""Генерация предложений по нормализации enum-полей для Фазы 1.2.

Скрипт читает выбранные docid из data/review/phase1-2-gold-sample.md,
берёт текущие значения из structure_<docid>.json и формирует два файла:

- data/review/phase1-2-enum-suggestions.md
- data/review/phase1-2-enum-suggestions.csv

Это не автоприменение правок, а список предложений для юридического выбора.
"""
import csv
import json
import re
from pathlib import Path


SAMPLE_PATH = Path("data/review/phase1-2-gold-sample.md")
OUT_MD = Path("data/review/phase1-2-enum-suggestions.md")
OUT_CSV = Path("data/review/phase1-2-enum-suggestions.csv")
STRUCTURED_DIR = Path("data/structured")
ENUM_DICTIONARY_PATH = Path("data/reference/zpp_enum_dictionary.json")


def load_enum_dictionary() -> dict[str, dict[str, str]]:
    """Берёт человекочитаемый словарь enum из канонического JSON-файла."""
    data = json.loads(ENUM_DICTIONARY_PATH.read_text(encoding="utf-8"))
    fields = data["fields"]

    result: dict[str, dict[str, str]] = {}
    field_aliases = {
        "taxonomy.dispute_type_code": "dispute_type_code",
        "taxonomy.claim_type_codes": "claim_type_codes",
        "claims_and_result.outcome.result_type": "result_type",
        "publication.index_policy": "publication_index_policy",
    }

    for source_field, alias in field_aliases.items():
        values = fields[source_field]["values"]
        normalized_values = {}
        for code, meta in values.items():
            if isinstance(meta, dict):
                label = meta.get("label") or meta.get("description") or ""
                basis = meta.get("legal_basis") or []
                suffix = f" ({', '.join(basis)})" if basis else ""
                normalized_values[code] = f"{label}{suffix}"
            else:
                normalized_values[code] = str(meta)
        result[alias] = normalized_values
    return result


ENUM_DICTIONARY = load_enum_dictionary()


SUGGESTIONS = {
    "yQ8qgPoesvWJ": {
        "dispute_type_code": "info_violation_art10_12",
        "dispute_type_label": "ответственность маркетплейса/агрегатора за товар продавца",
        "claim_type_codes": ["price_difference", "damages", "penalty", "moral_damage", "consumer_fine"],
        "result_type": "rejected",
        "platform_norm": "Ozon",
        "object_type_norm": "видеокарта",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "отказ к Ozon из-за статуса агрегатора, полезный отказной кейс",
    },
    "FuXzeJou9YYT": {
        "dispute_type_code": "prepaid_goods_delay_art23_1",
        "dispute_type_label": "маркетплейс/продавец не передал оплаченный товар",
        "claim_type_codes": ["compel_transfer", "penalty", "moral_damage", "consumer_fine", "expenses"],
        "result_type": "mixed",
        "platform_norm": "Ozon",
        "object_type_norm": "товар маркетплейса",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "иск удовлетворён к продавцу, но отказан к Ozon",
    },
    "Yse5NQ5b8YbO": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "возврат денег за некачественный телевизор с маркетплейса",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine", "expenses"],
        "result_type": "partially_satisfied",
        "platform_norm": "Ozon",
        "object_type_norm": "телевизор",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "частичный успех, есть астрент/возврат товара",
    },
    "yz0M6YZip7Qn": {
        "dispute_type_code": "service_refusal_art32",
        "dispute_type_label": "возврат авиабилетов и ответственность агента/перевозчика",
        "claim_type_codes": ["refund_price", "moral_damage", "consumer_fine"],
        "result_type": "mixed",
        "platform_norm": "Ozon Travel / Air Serbia",
        "object_type_norm": "авиабилеты",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "частично против перевозчика, отказ к агенту и в штрафе",
    },
    "LEkG8QMUg0gC": {
        "dispute_type_code": "distance_sale_return_art26_1",
        "dispute_type_label": "возврат товара надлежащего качества при дистанционной покупке",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine", "expenses"],
        "result_type": "partially_satisfied",
        "platform_norm": "Ozon",
        "object_type_norm": "телевизор",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "классический дистанционный отказ без недостатка",
    },
    "DvLR6OZqCqt": {
        "dispute_type_code": "info_violation_art10_12",
        "dispute_type_label": "требование раскрыть информацию о продавцах на маркетплейсах",
        "claim_type_codes": ["information_disclosure", "moral_damage", "penalty"],
        "result_type": "rejected",
        "platform_norm": "несколько маркетплейсов",
        "object_type_norm": "информация о продавце",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "важный отказной кейс по информационным обязанностям агрегаторов",
    },
    "qVUccWRuFprb": {
        "dispute_type_code": "info_violation_art10_12",
        "dispute_type_label": "недостаточная информация о товаре на маркетплейсе",
        "claim_type_codes": ["moral_damage"],
        "result_type": "rejected",
        "platform_norm": "Wildberries",
        "object_type_norm": "зарядное устройство",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "информационный спор, отказ из-за недоказанности нарушения",
    },
    "1w89Nc1UMNmm": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "возврат игровой приставки с недостатком",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine"],
        "result_type": "partially_satisfied",
        "platform_norm": "Wildberries",
        "object_type_norm": "игровая приставка",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "формально satisfied в JSON, но суммы/штраф обычно требуют частичной квалификации",
    },
    "LEM5MFXCKK6L": {
        "dispute_type_code": "contract_validity_non_zpp",
        "dispute_type_label": "понуждение маркетплейса к исполнению заказа",
        "claim_type_codes": ["contract_recognition", "compel_transfer"],
        "result_type": "rejected",
        "platform_norm": "Wildberries",
        "object_type_norm": "смартфон",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "иск проигран, полезно для сценария «заказ не считается заключённым»",
    },
    "fNiaUxW2zu1p": {
        "dispute_type_code": "distance_sale_return_art26_1",
        "dispute_type_label": "возврат товара при отказе от дистанционной покупки",
        "claim_type_codes": ["refund_price", "moral_damage", "consumer_fine"],
        "result_type": "partially_satisfied",
        "platform_norm": "Wildberries",
        "object_type_norm": "товар дистанционной продажи",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "дистанционный отказ, частичное удовлетворение",
    },
    "7hRq36xc81l6": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "возврат смартфона с заявленным недостатком",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine"],
        "result_type": "rejected",
        "platform_norm": "Яндекс.Маркет",
        "object_type_norm": "смартфон",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "отказной кейс по доказательствам недостатка",
    },
    "v0m4w50eZy5n": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "возврат технически сложного товара с недостатком",
        "claim_type_codes": ["refund_price", "price_difference", "penalty", "moral_damage", "expenses"],
        "result_type": "partially_satisfied",
        "platform_norm": "Яндекс.Маркет",
        "object_type_norm": "планшет",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "технически сложный товар, частичный успех",
    },
    "yc651JdA4PJC": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "возврат ноутбука ненадлежащего качества",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine", "damages", "expenses"],
        "result_type": "partially_satisfied",
        "platform_norm": "Яндекс.Маркет",
        "object_type_norm": "ноутбук",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "частичное удовлетворение с низкой присуждённой суммой",
    },
    "3mMKR7CNUYQ8": {
        "dispute_type_code": "service_refusal_art32",
        "dispute_type_label": "возврат денег за онлайн-обучение",
        "claim_type_codes": ["refund_price", "consumer_fine"],
        "result_type": "satisfied",
        "platform_norm": "Skillbox",
        "object_type_norm": "онлайн-курс",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "услуги, не товар; полезно как расширение ЗоПП",
    },
    "flVxOoBiwCr8": {
        "dispute_type_code": "contract_validity_non_zpp",
        "dispute_type_label": "спор по договору услуг связи и начислениям",
        "claim_type_codes": ["contract_recognition", "debt_dispute"],
        "result_type": "rejected",
        "platform_norm": "Ростелеком",
        "object_type_norm": "услуги связи",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "полный отказ, полезно проверить нецелевые/слабые требования",
    },
    "Pde5A0X4dlZj": {
        "dispute_type_code": "service_refusal_art32",
        "dispute_type_label": "возврат страховой премии",
        "claim_type_codes": ["insurance_premium_refund", "penalty", "moral_damage", "consumer_fine"],
        "result_type": "partially_satisfied",
        "platform_norm": "Ренессанс Жизнь",
        "object_type_norm": "страховая услуга",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "пограничная, но потребительская услуга; оставить на проверку",
    },
    "qNPGP4ky266p": {
        "dispute_type_code": "non_consumer_hold",
        "dispute_type_label": "непотребительский спор по договору поставки",
        "claim_type_codes": ["hold"],
        "result_type": "hold",
        "platform_norm": "Ozon",
        "object_type_norm": "поставка товара",
        "index_policy": "hold",
        "main_site_fit": False,
        "reason": "дело уже помечено как непотребительское; оставить контрольным исключением",
    },
    "qx9K417NRkWN": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "возврат автомобиля с существенными недостатками",
        "claim_type_codes": ["refund_price", "damages", "penalty", "moral_damage", "consumer_fine"],
        "result_type": "partially_satisfied",
        "platform_norm": "УАЗ",
        "object_type_norm": "автомобиль",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "крупные суммы, классический авто-дефект",
    },
    "0qwM485PLa1s": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "возврат автомобиля ненадлежащего качества",
        "claim_type_codes": ["refund_price", "moral_damage", "consumer_fine"],
        "result_type": "partially_satisfied",
        "platform_norm": "Автомир-Трейд",
        "object_type_norm": "автомобиль",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "требования удовлетворены после подачи иска, лучше не считать полным выигрышем без проверки",
    },
    "82RMC7eXBpH4": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "возврат технически сложного товара с недостатком",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine"],
        "result_type": "satisfied",
        "platform_norm": "М.Видео",
        "object_type_norm": "телевизор",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "сильный потребительский кейс, почти полное удовлетворение",
    },
    "BRRlQN72V9V6": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "возврат технически сложного товара после гарантии, но в пределах двух лет",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine", "expenses"],
        "result_type": "mixed",
        "platform_norm": "ДНС",
        "object_type_norm": "смартфон",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "смешанный/частичный исход; проверить бремя доказывания",
    },
    "PulUoivdYENP": {
        "dispute_type_code": "prepaid_goods_delay_art23_1",
        "dispute_type_label": "непоставка предварительно оплаченного товара",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine"],
        "result_type": "satisfied",
        "platform_norm": "не указан",
        "object_type_norm": "кухонный гарнитур",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "полное удовлетворение, хороший positive-case",
    },
    "MmtWiS16N45R": {
        "dispute_type_code": "prepaid_goods_delay_art23_1",
        "dispute_type_label": "нарушение срока передачи предварительно оплаченного товара",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine", "expenses"],
        "result_type": "partially_satisfied",
        "platform_norm": "не указан",
        "object_type_norm": "бревенчатый сруб дома",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "частичное удовлетворение по предоплате/срокам",
    },
    "YFjMxNYLsLlX": {
        "dispute_type_code": "goods_defect_art18",
        "dispute_type_label": "комплектность мебели и возврат расходов",
        "claim_type_codes": ["refund_price", "penalty", "moral_damage", "consumer_fine", "damages", "expenses"],
        "result_type": "partially_satisfied",
        "platform_norm": "Лазурит",
        "object_type_norm": "мебель",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "текущее JSON содержит англоязычные enum; требуется нормализация",
    },
    "OzQpzlDiDWZ": {
        "dispute_type_code": "distance_sale_return_art26_1",
        "dispute_type_label": "отказ принять возврат товара надлежащего качества онлайн",
        "claim_type_codes": ["refund_price", "moral_damage", "consumer_fine"],
        "result_type": "partially_satisfied",
        "platform_norm": "Ашан",
        "object_type_norm": "швабра",
        "index_policy": "index",
        "main_site_fit": True,
        "reason": "текущее JSON содержит англоязычные enum; полезен для дистанционного возврата",
    },
}


def sample_docids() -> list[str]:
    text = SAMPLE_PATH.read_text(encoding="utf-8")
    ids = []
    for line in text.splitlines():
        match = re.match(r"\|\s*\d+\s*\|\s*`([A-Za-z0-9]+)`", line)
        if match:
            ids.append(match.group(1))
    return ids


def load_structure(docid: str) -> dict:
    return json.loads((STRUCTURED_DIR / f"structure_{docid}.json").read_text(encoding="utf-8"))


def current_row(docid: str, data: dict, suggestion: dict) -> dict:
    taxonomy = data.get("taxonomy", {})
    outcome = data.get("claims_and_result", {}).get("outcome", {}) or {}
    publication = data.get("publication", {})
    return {
        "docid": docid,
        "current_dispute_type": taxonomy.get("dispute_type") or "",
        "suggested_dispute_type_code": suggestion["dispute_type_code"],
        "suggested_dispute_type_label": suggestion["dispute_type_label"],
        "current_claim_type": taxonomy.get("claim_type") or "",
        "suggested_claim_type_codes": "; ".join(suggestion["claim_type_codes"]),
        "current_result_type": outcome.get("result_type") or "",
        "current_focus_party_result": outcome.get("focus_party_result") or "",
        "suggested_result_type": suggestion["result_type"],
        "current_platform": taxonomy.get("platform_or_company") or "",
        "suggested_platform_norm": suggestion["platform_norm"],
        "current_object_type": taxonomy.get("object_type") or "",
        "suggested_object_type_norm": suggestion["object_type_norm"],
        "current_index_policy": publication.get("index_policy"),
        "suggested_index_policy": suggestion["index_policy"],
        "current_main_site_fit": publication.get("main_site_fit"),
        "suggested_main_site_fit": suggestion["main_site_fit"],
        "reason": suggestion["reason"],
        "review_decision": "",
        "review_comment": "",
    }


def write_csv(rows: list[dict]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict]) -> None:
    lines = [
        "# Фаза 1.2 — предложения по нормализации enum",
        "",
        "Статус: предложения для ручного выбора/коррекции, не автоприменение.",
        "",
        "Задача: вместо ручного заполнения с нуля выбрать нормализованные значения для ключевых enum-полей.",
        "",
        "## Словари значений",
        "",
    ]
    for enum_name, values in ENUM_DICTIONARY.items():
        lines.append(f"### {enum_name}")
        lines.append("")
        for key, desc in values.items():
            lines.append(f"- `{key}` — {desc}")
        lines.append("")

    lines.extend([
        "## Как править",
        "",
        "- Если предложение корректно — в CSV можно поставить `review_decision = ok`.",
        "- Если нужно исправить — поставить `review_decision = fix` и указать значение в `review_comment`.",
        "- Если дело не нужно основному сайту — `suggested_result_type = hold`, `suggested_index_policy = hold`, `suggested_main_site_fit = False`.",
        "",
        "## Предложения по делам",
        "",
    ])

    for idx, row in enumerate(rows, 1):
        lines.extend([
            f"### {idx}. `{row['docid']}`",
            "",
            f"- `dispute_type`: {row['current_dispute_type']!r}",
            f"  - предложение: `{row['suggested_dispute_type_code']}` — {row['suggested_dispute_type_label']}",
            f"- `claim_type`: {row['current_claim_type']!r}",
            f"  - предложение: `{row['suggested_claim_type_codes']}`",
            f"- `result_type`: {row['current_result_type']!r}; `focus_party_result`: {row['current_focus_party_result']!r}",
            f"  - предложение: `{row['suggested_result_type']}`",
            f"- `platform_or_company`: {row['current_platform']!r}",
            f"  - предложение: `{row['suggested_platform_norm']}`",
            f"- `object_type`: {row['current_object_type']!r}",
            f"  - предложение: `{row['suggested_object_type_norm']}`",
            f"- `publication`: index_policy={row['current_index_policy']!r}, main_site_fit={row['current_main_site_fit']!r}",
            f"  - предложение: index_policy=`{row['suggested_index_policy']}`, main_site_fit=`{row['suggested_main_site_fit']}`",
            f"- причина: {row['reason']}",
            "- решение юриста: ",
            "- комментарий: ",
            "",
        ])

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = []
    for docid in sample_docids():
        if docid not in SUGGESTIONS:
            raise SystemExit(f"Нет предложения для {docid}")
        rows.append(current_row(docid, load_structure(docid), SUGGESTIONS[docid]))
    write_csv(rows)
    write_markdown(rows)
    print(f"Сгенерировано: {OUT_MD}")
    print(f"Сгенерировано: {OUT_CSV}")
    print(f"Дел в выборке: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
