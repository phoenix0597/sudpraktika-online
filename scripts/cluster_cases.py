# -*- coding: utf-8 -*-
"""Первичная кластеризация structure_*.json по практическим ситуациям.

Скрипт не меняет исходные JSON. Основная группировка строится по
`taxonomy.dispute_type_code`; эвристический fallback оставлен только как
защита на случай неполной разметки.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


STRUCTURED_DIR = Path("data/structured")
OUT_CSV = Path("data/review/phase1-4-case-clusters.csv")
OUT_MD = Path("data/review/phase1-4-cluster-summary.md")


@dataclass(frozen=True)
class Cluster:
    code: str
    name: str
    page_angle: str
    default_priority: str


CLUSTERS: dict[str, Cluster] = {
    "goods_defect_art18": Cluster(
        "goods_defect_art18",
        "Товар с недостатком / технически сложный товар",
        "Что взыскивать и как доказывать недостаток товара",
        "pillar",
    ),
    "distance_sale_return_art26_1": Cluster(
        "distance_sale_return_art26_1",
        "Дистанционная продажа: отказ от товара и возврат денег",
        "Когда можно вернуть товар, купленный онлайн",
        "landing",
    ),
    "prepaid_goods_delay_art23_1": Cluster(
        "prepaid_goods_delay_art23_1",
        "Оплаченный товар не передали или задержали",
        "Что делать, если заказ оплачен, но товар не передают",
        "landing",
    ),
    "info_violation_art10_12": Cluster(
        "info_violation_art10_12",
        "Недостоверная или неполная информация о товаре/продавце",
        "Ошибки в цене, продавце, свойствах товара и последствия для иска",
        "landing",
    ),
    "service_refusal_art32": Cluster(
        "service_refusal_art32",
        "Отказ от услуги и возврат денег",
        "Возврат оплаты за услуги, курсы, страховки и сервисы",
        "landing",
    ),
    "work_service_defect_art29": Cluster(
        "work_service_defect_art29",
        "Недостатки работ или услуг",
        "Некачественные работы: окна, монтаж, изготовление",
        "long_tail",
    ),
    "work_service_delay_art28": Cluster(
        "work_service_delay_art28",
        "Нарушение сроков работ или услуг",
        "Просрочка работ, монтажа или изготовления",
        "long_tail",
    ),
    "contract_validity_non_zpp": Cluster(
        "contract_validity_non_zpp",
        "Пограничные договорные споры / риск не ЗоЗПП",
        "Дела, которые требуют ручной проверки перед публикацией",
        "hold",
    ),
    "non_consumer_hold": Cluster(
        "non_consumer_hold",
        "Не потребительский спор",
        "Исключить из основного индекса ЗоЗПП-сайта",
        "hold",
    ),
    "manual_review": Cluster(
        "manual_review",
        "Требует ручной кластеризации",
        "Недостаточно данных для уверенной автоматической группировки",
        "hold",
    ),
}


def text_blob(data: dict) -> str:
    taxonomy = data.get("taxonomy", {})
    case_summary = data.get("case_summary", {})
    claims = data.get("claims_and_result", {})
    parts: list[str] = [
        taxonomy.get("dispute_type", ""),
        taxonomy.get("claim_type", ""),
        taxonomy.get("platform_or_company", ""),
        taxonomy.get("object_type", ""),
        taxonomy.get("object_name", ""),
        claims.get("remedy", ""),
        claims.get("holding", ""),
        case_summary.get("situation", ""),
        " ".join(taxonomy.get("situation_tags") or []),
        " ".join(case_summary.get("key_factors") or []),
    ]
    return " ".join(str(p) for p in parts if p).lower()


def has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def infer_cluster(data: dict) -> tuple[str, str, str]:
    """Return (cluster_code, confidence, reason)."""
    taxonomy = data.get("taxonomy", {})
    code = taxonomy.get("dispute_type_code")
    if code:
        return code, "reviewed", "Взят reviewed enum-код из JSON"

    text = text_blob(data)

    if has_any(text, ("поставка между юрлицами", "между юридическими лицами")):
        return "non_consumer_hold", "inferred_high", "Признаки непотребительского спора"

    if has_any(text, ("непредоставление информации", "информац", "цена на витрине", "цены на витрине", "на кассе", "недостоверн")):
        return "info_violation_art10_12", "inferred_high", "Спор построен вокруг информации о товаре/цене/продавце"

    if has_any(text, ("дистанцион", "онлайн", "lamoda", "сдэк.маркет")) and has_any(
        text,
        ("отказ от товара", "надлежащего качества", "возврат уплаченной суммы", "возврат цены"),
    ):
        return "distance_sale_return_art26_1", "inferred_high", "Отказ/возврат при дистанционной покупке"

    if has_any(text, ("аннулирование заказа", "понуждение к передаче", "не передал", "не передан", "сроков поставки")):
        if has_any(text, ("монтаж", "работ", "изготовлен", "роллет", "калитк")):
            return "work_service_delay_art28", "inferred_medium", "Просрочка смешана с работами/монтажом"
        return "prepaid_goods_delay_art23_1", "inferred_high", "Оплаченный товар не передан или заказ аннулирован"

    if has_any(text, ("сертификат", "страхов", "онлайн-курс", "услуг", "услуга")) and has_any(
        text,
        ("отказ", "возврат денежных средств", "возврат уплаченной суммы", "расторжение"),
    ):
        return "service_refusal_art32", "inferred_medium", "Отказ от услуги или возврат платы за услугу"

    if has_any(text, ("окна", "окон", "монтаж", "изготовлен", "работ")) and has_any(
        text,
        ("недостат", "не соответствует", "некачествен", "отклонение"),
    ):
        return "work_service_defect_art29", "inferred_medium", "Недостатки работ/изготовления/монтажа"

    if has_any(
        text,
        (
            "недостат",
            "ненадлежащего качества",
            "технически слож",
            "гарантийного ремонта",
            "существенн",
            "дефект",
            "ремонт",
        ),
    ):
        return "goods_defect_art18", "inferred_high", "Недостаток товара или спор о гарантийном ремонте"

    return "manual_review", "manual_review", "Эвристика не дала уверенного кластера"


def normalize_result(data: dict) -> str:
    outcome = data.get("claims_and_result", {}).get("outcome", {})
    result_type = str(outcome.get("result_type") or "").strip()
    focus = str(outcome.get("focus_party_result") or "").strip()
    text = " ".join([result_type, focus]).lower()

    if result_type in {"satisfied", "partially_satisfied", "rejected", "mixed", "hold"}:
        return result_type
    if "отказ" in text or "проигрыш" in text:
        return "rejected"
    if "част" in text:
        return "partially_satisfied"
    if "удовлетвор" in text or "выигрыш" in text:
        return "satisfied"
    return result_type or focus or "unknown"


def priority_for(cluster_code: str, count: int) -> str:
    if cluster_code in {"non_consumer_hold", "contract_validity_non_zpp", "manual_review"}:
        return "hold"
    if count >= 10:
        return "pillar"
    if count >= 3:
        return "landing"
    return "long_tail"


def main() -> int:
    files = sorted(STRUCTURED_DIR.glob("structure_*.json"))
    rows: list[dict[str, str]] = []

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        source = data.get("source", {})
        court = data.get("court", {})
        taxonomy = data.get("taxonomy", {})
        case_summary = data.get("case_summary", {})
        claims = data.get("claims_and_result", {})
        outcome = claims.get("outcome", {})
        publication = data.get("publication", {})

        docid = source.get("docid") or path.stem.replace("structure_", "")
        cluster_code, confidence, reason = infer_cluster(data)
        cluster = CLUSTERS.get(cluster_code, CLUSTERS["manual_review"])
        key_factors = case_summary.get("key_factors") or []
        if not isinstance(key_factors, list):
            key_factors = [str(key_factors)]

        rows.append(
            {
                "docid": docid,
                "case_number": court.get("case_number", ""),
                "decision_date": court.get("decision_date", ""),
                "region": court.get("region", ""),
                "source_url": source.get("source_url", ""),
                "cluster_code": cluster_code,
                "cluster_name": cluster.name,
                "cluster_confidence": confidence,
                "cluster_reason": reason,
                "page_angle": cluster.page_angle,
                "dispute_type_code": taxonomy.get("dispute_type_code", ""),
                "dispute_type_code_original": taxonomy.get("dispute_type_code", ""),
                "dispute_type": taxonomy.get("dispute_type", ""),
                "claim_type_codes": "; ".join(taxonomy.get("claim_type_codes") or []),
                "claim_type": taxonomy.get("claim_type", ""),
                "platform_or_company": taxonomy.get("platform_or_company", ""),
                "object_type": taxonomy.get("object_type", ""),
                "object_name": taxonomy.get("object_name", ""),
                "result_type": normalize_result(data),
                "result_type_normalized": normalize_result(data),
                "result_type_original": outcome.get("result_type", ""),
                "focus_party_result": outcome.get("focus_party_result", ""),
                "index_policy": publication.get("index_policy", ""),
                "main_site_fit": publication.get("main_site_fit", ""),
                "situation_tags": "; ".join(taxonomy.get("situation_tags") or []),
                "key_factors_short": " | ".join(key_factors[:3]),
            }
        )

    cluster_counts = Counter(row["cluster_code"] for row in rows)
    for row in rows:
        row["page_priority"] = priority_for(row["cluster_code"], cluster_counts[row["cluster_code"]])

    fieldnames = [
        "docid",
        "case_number",
        "decision_date",
        "region",
        "source_url",
        "cluster_code",
        "cluster_name",
        "cluster_confidence",
        "cluster_reason",
        "page_priority",
        "page_angle",
        "dispute_type_code",
        "dispute_type_code_original",
        "dispute_type",
        "claim_type_codes",
        "claim_type",
        "platform_or_company",
        "object_type",
        "object_name",
        "result_type",
        "result_type_normalized",
        "result_type_original",
        "focus_party_result",
        "index_policy",
        "main_site_fit",
        "situation_tags",
        "key_factors_short",
    ]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["page_priority"], r["cluster_code"], r["docid"])))

    write_markdown(rows)

    print(f"Всего дел: {len(rows)}")
    print(f"CSV: {OUT_CSV.as_posix()}")
    print(f"Отчёт: {OUT_MD.as_posix()}")
    for code, count in cluster_counts.most_common():
        print(f"{code}: {count}")
    return 0


def write_markdown(rows: list[dict[str, str]]) -> None:
    cluster_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        cluster_rows[row["cluster_code"]].append(row)

    total = len(rows)
    reviewed = sum(1 for row in rows if row["cluster_confidence"] == "reviewed")
    inferred = total - reviewed

    lines: list[str] = [
        "# Фаза 1.4: первичная кластеризация судебных актов",
        "",
        "## Метод",
        "",
        "Использована лёгкая кластеризация по уже извлечённым JSON-полям: `taxonomy`, `claims_and_result`, `publication`, ключевые факторы и теги ситуации. Embeddings на этом шаге не применялись: для MVP достаточно сначала проверить, какие группы дают существующие структурные поля.",
        "",
        f"- Всего актов: {total}",
        f"- С reviewed enum-кодами: {reviewed}",
        f"- С временной эвристической классификацией: {inferred}",
        "",
        "## Сводка кластеров",
        "",
        "| Кластер | Дел | Reviewed | Inferred | Приоритет | Угол страницы |",
        "|---|---:|---:|---:|---|---|",
    ]

    for code, items in sorted(cluster_rows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        cluster = CLUSTERS.get(code, CLUSTERS["manual_review"])
        reviewed_count = sum(1 for row in items if row["cluster_confidence"] == "reviewed")
        inferred_count = len(items) - reviewed_count
        priority = priority_for(code, len(items))
        lines.append(
            f"| `{code}` — {cluster.name} | {len(items)} | {reviewed_count} | {inferred_count} | {priority} | {cluster.page_angle} |"
        )

    lines.extend(
        [
            "",
            "## Кластеры по делам",
            "",
        ]
    )

    for code, items in sorted(cluster_rows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        cluster = CLUSTERS.get(code, CLUSTERS["manual_review"])
        priority = priority_for(code, len(items))
        lines.extend(
            [
                f"### `{code}` — {cluster.name}",
                "",
                f"- Дел: {len(items)}",
                f"- Приоритет: `{priority}`",
                f"- Угол будущей страницы: {cluster.page_angle}",
                "",
                "| docid | объект/компания | результат | уверенность |",
                "|---|---|---|---|",
            ]
        )
        for row in sorted(items, key=lambda r: r["docid"]):
            company = row["platform_or_company"] or "—"
            obj = row["object_type"] or "—"
            result = row["result_type_normalized"]
            confidence = row["cluster_confidence"]
            lines.append(f"| `{row['docid']}` | {obj} / {company} | {result} | {confidence} |")
        lines.append("")

    lines.extend(
        [
            "## Практический вывод",
            "",
            "1. Основной пиллар для первой версии — дела о недостатках товара: это самый крупный и понятный пользователю кластер.",
            "2. Отдельные посадочные страницы стоит готовить по дистанционной продаже, задержке/непередаче оплаченного товара, информационным нарушениям и отказу от услуг.",
            "3. Кластеры работ/услуг уже пригодны для отдельных страниц; их нужно расширять точечно по подтипам, регионам и судам.",
            "4. Дела с `hold` не смешивать с основным гражданским ЗоЗПП-индексом.",
            "5. Кластеризация строится по проверенным enum-кодам из JSON; новые кандидатные ситуации без утверждённого кода остаются в `hold` до отдельного решения.",
            "",
            "## Следующий шаг",
            "",
            "Проверить, какие кандидатные ситуации из `hold` пора переводить в словарь, и только после этого генерировать новые страницы-ситуации.",
        ]
    )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
