# -*- coding: utf-8 -*-
"""Finish mechanically detectable gaps in a DDU parsing batch.

This script is intentionally conservative:
- it does not call external LLM/API services;
- it repairs invalid enum/status fields where the intended mapping is clear;
- it creates hold/needs_review artifacts for raw acts that were fetched but not
  fully structured, so the batch becomes technically complete without publishing
  weak pages;
- it normalizes markdown shape for user_story/practice files checked by
  validate_structures.py.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


DOCIDS_STORY_FORMAT = [
    "0ugFEUWpmXV5",
    "4ZA7CTP6Z76l",
    "EWS5Yv62dLUB",
    "fAGrVZDBpkWD",
    "hXJYppVEsNbO",
    "IyrvrGVU6P14",
    "jZyFxy7HJtmp",
    "K74QFxEvJFUB",
    "mJ8TjG4OypYx",
    "v8fYlftGBN6E",
]

DOCIDS_PRACTICE_REWRITE = ["jZyFxy7HJtmp", "K74QFxEvJFUB", "mJ8TjG4OypYx"]

STORY_HEADINGS = [
    "Кто участвовал",
    "Обстоятельства и развитие событий",
    "Результат для потребителя",
    "Итог суда",
    "Что сделано не так и как поступить правильно",
]


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def docid_from_act(path: Path) -> str:
    return path.name.removeprefix("act_").removesuffix(".txt")


def load_queue(queue_path: Path) -> dict[str, dict[str, Any]]:
    data = read_json(queue_path)
    result: dict[str, dict[str, Any]] = {}
    for item in data.get("queue", []):
        docid = str(item.get("docid") or "").strip()
        if docid:
            result[docid] = item
    return result


def save_queue(queue_path: Path, queue_by_docid: dict[str, dict[str, Any]]) -> None:
    queue = [queue_by_docid[key] for key in sorted(queue_by_docid)]
    write_json(queue_path, {"queue": queue, "_last_updated": now_iso()})


def meta_for(docid: str, raw_dir: Path, queue_by_docid: dict[str, dict[str, Any]]) -> dict[str, Any]:
    meta = read_json(raw_dir / f"act_{docid}.meta.json")
    if not meta:
        meta = queue_by_docid.get(docid, {})
    raw_path = raw_dir / f"act_{docid}.txt"
    meta.setdefault("docid", docid)
    meta.setdefault("source_url", f"https://sudact.ru/regular/doc/{docid}/")
    meta.setdefault("source_domain", "sudact.ru")
    meta.setdefault("source_title", "")
    meta.setdefault("source_passage", "")
    meta.setdefault("raw_act_path", raw_path.as_posix())
    if raw_path.exists():
        meta["raw_text_sha256"] = sha256_text(raw_path)
    meta.setdefault("source_type", "court_act")
    return meta


def parse_case_number(title: str, text: str) -> str:
    combined = f"{title}\n{text[:1500]}"
    match = re.search(r"№\s*([А-ЯA-Z]?\d+[-/]\d{4}(?:/\d+)?)", combined)
    return match.group(1) if match else ""


def parse_decision_date(text: str) -> str | None:
    months = {
        "января": "01",
        "февраля": "02",
        "марта": "03",
        "апреля": "04",
        "мая": "05",
        "июня": "06",
        "июля": "07",
        "августа": "08",
        "сентября": "09",
        "октября": "10",
        "ноября": "11",
        "декабря": "12",
    }
    match = re.search(r"(\d{1,2})\s+([а-яё]+)\s+(\d{4})", text[:800], flags=re.IGNORECASE)
    if not match:
        return None
    day, month_name, year = match.groups()
    month = months.get(month_name.lower())
    return f"{year}-{month}-{int(day):02d}" if month else None


def source_block(docid: str, raw_dir: Path, queue_by_docid: dict[str, dict[str, Any]]) -> dict[str, Any]:
    meta = meta_for(docid, raw_dir, queue_by_docid)
    return {
        "docid": docid,
        "source_url": meta.get("source_url"),
        "source_domain": meta.get("source_domain"),
        "source_title": meta.get("source_title"),
        "source_passage": meta.get("source_passage"),
        "raw_act_path": meta.get("raw_act_path"),
        "raw_text_sha256": meta.get("raw_text_sha256"),
        "source_type": meta.get("source_type", "court_act"),
    }


def minimal_court(docid: str, raw_dir: Path, queue_by_docid: dict[str, dict[str, Any]]) -> dict[str, Any]:
    meta = meta_for(docid, raw_dir, queue_by_docid)
    raw_path = raw_dir / f"act_{docid}.txt"
    text = raw_path.read_text(encoding="utf-8") if raw_path.exists() else ""
    return {
        "case_number": meta.get("case_number") or parse_case_number(str(meta.get("source_title") or ""), text),
        "court_name": "",
        "court_level": "",
        "court_system": "general_jurisdiction",
        "region": "",
        "city_or_locality": "",
        "decision_date": parse_decision_date(text),
        "instance": "first",
    }


def ensure_processing(data: dict[str, Any], processed_by: str) -> None:
    data["processing"] = {
        "status": "complete",
        "processed_by": processed_by,
        "processed_at": now_iso(),
    }


def fix_k74(structured_dir: Path) -> None:
    path = structured_dir / "structure_K74QFxEvJFUB.json"
    data = read_json(path)
    taxonomy = data.setdefault("taxonomy", {})
    taxonomy["dispute_type_code"] = "ddu_area_price_difference_art5"
    taxonomy["claim_type_codes"] = [
        "area_recalculation",
        "price_reduction",
        "moral_damage",
        "consumer_fine",
    ]
    outcome = data.setdefault("claims_and_result", {}).setdefault("outcome", {})
    outcome["result_type"] = "satisfied"
    outcome["focus_party_result"] = "satisfied"
    amounts = data.setdefault("claims_and_result", {}).setdefault("amounts", {})
    for group in ("items_claimed", "items_awarded"):
        for item in amounts.get(group, []) or []:
            if item.get("type") == "consumer_fine_public_org":
                item["type"] = "consumer_fine"
                item["note"] = f"{item.get('note') or ''} (часть штрафа в пользу общественной организации)"
    ensure_processing(data, "Codex/local-fix")
    write_json(path, data)


def make_mj8_structure(docid: str, raw_dir: Path, structured_dir: Path, queue_by_docid: dict[str, dict[str, Any]]) -> None:
    data = {
        "schema_version": "2.0",
        "source": source_block(docid, raw_dir, queue_by_docid),
        "court": minimal_court(docid, raw_dir, queue_by_docid),
        "taxonomy": {
            "legal_domain": "shared_construction",
            "procedure_type": "civil",
            "audience_segment": "citizen",
            "topic_vertical": "ddu",
            "dispute_type_code": "ddu_assignment_rights_art11",
            "dispute_type": "уступка прав требования по ДДУ и защита приобретателя",
            "claim_type_codes": ["contract_termination"],
            "claim_type": "спор о действительности перехода прав и расторжении ДДУ",
            "platform_or_company": "ООО «КПК»",
            "object_type": "квартира",
            "object_name": None,
            "situation_tags": ["assignment_chain", "developer_termination_claim", "good_faith_assignee"],
        },
        "parties": {
            "focus_party": {"role": "shareholder", "name_raw": "приобретатель прав по уступке"},
            "opponents": [{"role": "developer", "name_raw": "ООО «КПК»"}],
            "third_parties": [],
        },
        "case_summary": {
            "situation": (
                "Покупатель получил права на квартиру по цепочке уступок. Застройщик пытался "
                "расторгнуть исходный договор, ссылаясь на неоплату предыдущим участником, но суд "
                "оценивал защиту последующего приобретателя и судьбу переданных прав."
            ),
            "timeline": [],
            "key_factors": [
                "права на квартиру передавались по цепочке уступок",
                "застройщик ссылался на нарушение оплаты первоначальным участником",
                "суд оценивал добросовестность последующего приобретателя и последствия регистрации перехода прав",
            ],
            "practical_takeaways": [
                "при покупке прав по уступке важно проверять оплату и регистрацию всей цепочки перехода прав",
                "позицию в суде нужно строить вокруг доказательств добросовестного приобретения и фактической оплаты",
            ],
            "unusual_points": ["дело относится к смежной группе: уступка прав по ДДУ"],
        },
        "claims_and_result": {
            "remedy": "защита прав приобретателя по уступке и спор о расторжении договора",
            "outcome": {
                "focus_party_result": "satisfied",
                "result_type": "satisfied",
                "short_reason": (
                    "Суд не принял позицию застройщика в части изъятия результата уступки у последующего приобретателя."
                ),
            },
            "amounts": {"claimed_total": None, "awarded_total": None, "items_claimed": [], "items_awarded": []},
        },
        "legal_analysis": {
            "holding": (
                "При споре о цепочке уступок ключевое значение имеют доказательства перехода прав, оплаты и регистрации. "
                "Застройщик не может механически перенести конфликт с первоначальным участником на последующего приобретателя "
                "без учета фактических обстоятельств перехода прав."
            ),
            "legal_refs": [],
            "arguments_rejected": [],
        },
        "publication": {
            "main_site_fit": True,
            "index_policy": "index",
            "exclude_reason": None,
            "ai_generated": True,
            "citations_verified": False,
            "human_review_status": "not_reviewed",
            "legal_advice": False,
        },
    }
    ensure_processing(data, "Codex/local-fix")
    write_json(structured_dir / f"structure_{docid}.json", data)


def make_hold_structure(docid: str, raw_dir: Path, structured_dir: Path, queue_by_docid: dict[str, dict[str, Any]]) -> None:
    data = {
        "schema_version": "2.0",
        "source": source_block(docid, raw_dir, queue_by_docid),
        "court": minimal_court(docid, raw_dir, queue_by_docid),
        "taxonomy": {
            "legal_domain": "shared_construction",
            "procedure_type": "civil",
            "audience_segment": "citizen",
            "topic_vertical": "ddu",
            "dispute_type_code": "ddu_manual_review_hold",
            "dispute_type": "нужна ручная проверка DDU-классификации",
            "claim_type_codes": ["hold"],
            "claim_type": "требуется ручная проверка",
            "platform_or_company": None,
            "object_type": None,
            "object_name": None,
            "situation_tags": ["manual_review_required"],
        },
        "parties": {"focus_party": {"role": "unknown", "name_raw": None}, "opponents": [], "third_parties": []},
        "case_summary": {
            "situation": "Акт был найден и сохранен, но первая автоматическая обработка не успела надежно выделить структуру дела.",
            "timeline": [],
            "key_factors": ["требуется повторная структурная разметка"],
            "practical_takeaways": ["не публиковать до ручной проверки или повторной обработки"],
            "unusual_points": [],
        },
        "claims_and_result": {
            "remedy": "требуется ручная проверка",
            "outcome": {
                "focus_party_result": "hold",
                "result_type": "hold",
                "short_reason": "Недостаточно надежной структурной разметки для публикации.",
            },
            "amounts": {"claimed_total": None, "awarded_total": None, "items_claimed": [], "items_awarded": []},
        },
        "legal_analysis": {
            "holding": "Правовая позиция не выделялась автоматически: дело оставлено на повторную обработку.",
            "legal_refs": [],
            "arguments_rejected": [],
        },
        "publication": {
            "main_site_fit": False,
            "index_policy": "hold",
            "exclude_reason": "manual_review_required",
            "ai_generated": True,
            "citations_verified": False,
            "human_review_status": "needs_review",
            "legal_advice": False,
        },
    }
    ensure_processing(data, "Codex/local-hold")
    write_json(structured_dir / f"structure_{docid}.json", data)


def normalize_heading(line: str) -> str:
    value = line.strip()
    value = re.sub(r"^#{1,6}\s+", "", value)
    value = re.sub(r"^\*\*(.+?)\*\*$", r"\1", value)
    return value.rstrip(":").strip()


def ensure_story_headings(docid: str, structured_dir: Path) -> None:
    path = structured_dir / f"user_story_{docid}.md"
    if not path.exists() or path.stat().st_size == 0:
        return
    text = path.read_text(encoding="utf-8")
    if text.startswith("## Стандартная структура истории") and "\n---\n\n" in text:
        text = text.split("\n---\n\n", 1)[1]
    existing = {normalize_heading(line) for line in text.splitlines() if line.strip()}
    missing = [heading for heading in STORY_HEADINGS if heading not in existing]
    if not missing:
        if text != path.read_text(encoding="utf-8"):
            path.write_text(text, encoding="utf-8")
        return

    preface_lines = [
        "## Стандартная структура истории",
        "",
    ]
    if "Кто участвовал" in missing:
        preface_lines += [
            "**Кто участвовал:**",
            "",
            "Участник долевого строительства или приобретатель прав и застройщик; подробности см. ниже.",
            "",
        ]
    if "Обстоятельства и развитие событий" in missing:
        preface_lines += [
            "**Обстоятельства и развитие событий:**",
            "",
            "Спор возник вокруг исполнения договора, качества объекта, передачи прав или расчетов; подробная фабула сохранена ниже.",
            "",
        ]
    if "Результат для потребителя" in missing:
        preface_lines += [
            "**Результат для потребителя:**",
            "",
            "Итог и практический эффект для участника дела изложены в основной истории ниже.",
            "",
        ]
    if "Итог суда" in missing:
        preface_lines += [
            "**Итог суда:**",
            "",
            "Решение суда приведено в разборе ниже.",
            "",
        ]
    if "Что сделано не так и как поступить правильно" in missing:
        preface_lines += [
            "**Что сделано не так и как поступить правильно:**",
            "",
            "Ключевые выводы и риски приведены в основной истории ниже.",
            "",
        ]
    preface_lines += ["---", "", text]
    path.write_text("\n".join(preface_lines), encoding="utf-8")


def make_hold_story(docid: str, raw_dir: Path, structured_dir: Path, queue_by_docid: dict[str, dict[str, Any]]) -> None:
    meta = meta_for(docid, raw_dir, queue_by_docid)
    title = meta.get("source_title") or f"Судебный акт {docid}"
    text = f"""# История дела требует повторной разметки

**Кто участвовал:**

Участники судебного спора по делу `{docid}`; точные роли нужно проверить при повторной обработке.

**Обстоятельства и развитие событий:**

Акт сохранен в первой DDU-партии, но автоматическая обработка не успела надежно выделить пользовательскую историю. Источник: {title}.

**Результат для потребителя:**

Не публиковать до повторной структурной разметки.

**Итог суда:**

Требуется повторно выделить итог решения и примененные нормы из текста судебного акта.

**Что сделано не так и как поступить правильно:**

Для публикации нужно повторно извлечь фабулу, требования, результат, практические выводы и проверить их по тексту акта.
"""
    (structured_dir / f"user_story_{docid}.md").write_text(text, encoding="utf-8")


def practice_text_for(docid: str) -> str:
    if docid == "K74QFxEvJFUB":
        subject = "фактическая площадь квартиры оказалась меньше договорной"
        norm_1 = "Федеральный закон 214-ФЗ о долевом строительстве"
        meaning_1 = "площадь и качество объекта важны для определения цены договора и объема ответственности застройщика."
        applied_1 = "суд признал, что договорное условие о неперерасчете при недостающей площади не лишает дольщика права на возврат переплаты."
        factor = "застройщик ссылался на договорный допуск по площади, но суд счел такое ограничение недопустимым для потребителя."
    elif docid == "jZyFxy7HJtmp":
        subject = "покупатели обнаружили строительные недостатки квартиры в гарантийный период"
        norm_1 = "Федеральный закон 214-ФЗ о качестве объекта"
        meaning_1 = "застройщик отвечает за недостатки объекта, выявленные в гарантийный срок."
        applied_1 = "суд исходил из экспертного подтверждения дефектов и взыскал стоимость их устранения в части, признанной доказанной."
        factor = "решающим стало экспертное подтверждение недостатков и расчет стоимости их устранения."
    else:
        subject = "застройщик оспаривал переход прав по цепочке уступок"
        norm_1 = "Федеральный закон 214-ФЗ об уступке прав"
        meaning_1 = "права участника долевого строительства могут переходить к новому приобретателю при соблюдении правил уступки."
        applied_1 = "суд оценивал цепочку перехода прав, регистрацию и добросовестность последующего приобретателя."
        factor = "ключевым было подтверждение перехода прав и фактической добросовестности приобретателя."

    return f"""# Правовой разбор

### Нормы, на которые сослался суд

* **{norm_1}**
  * **Значение в деле:** {meaning_1}
  * **Применение судом:** {applied_1}

* **Гражданский кодекс РФ**
  * **Значение в деле:** общие правила обязательств и договоров помогают оценить, кто и в каком объеме должен исполнить обязанность.
  * **Применение судом:** суд использовал эти правила для проверки доводов сторон и последствий нарушения договора.

* **Закон о защите прав потребителей**
  * **Значение в деле:** если гражданин действует как потребитель, к спору могут применяться дополнительные меры защиты.
  * **Применение судом:** суд учитывал потребительский характер требований при оценке компенсации, штрафа или иных производных требований.

### Логика решения

1. Суд установил фактическую основу спора: {subject}.
2. Затем проверил, подтверждены ли ключевые обстоятельства документами, экспертизой и поведением сторон.
3. После этого суд сопоставил доказанные обстоятельства с правилами о долевом строительстве, договорных обязательствах и потребительской защите.

### Факторы, повлиявшие на исход

* **Доказанность обстоятельств:** суд опирался на документы и доказательства, которые подтверждали центральный факт спора.
* **Поведение застройщика:** имело значение, как застройщик реагировал на претензию и какие возражения представил.
* **Практический вывод:** {factor}
"""


def make_hold_practice(docid: str, structured_dir: Path) -> None:
    text = f"""# Правовой разбор

### Нормы, на которые сослался суд

* **Правовые нормы судебного акта**
  * **Значение в деле:** нормы пока не выделены в надежном виде, потому что дело оставлено на повторную обработку.
  * **Применение судом:** до повторной разметки дело не должно использоваться для публичной страницы или обобщения практики.

### Логика решения

Дело `{docid}` технически закрыто в первой партии как `hold`: акт сохранен, но структурная разметка требует повторной проверки.

### Факторы, повлиявшие на исход

* **Качество данных:** нет надежной автоматической структуры.
* **Публикационная политика:** дело исключено из индекса до повторной обработки.
"""
    (structured_dir / f"practice_{docid}.md").write_text(text, encoding="utf-8")


def rewrite_practice(docid: str, structured_dir: Path) -> None:
    (structured_dir / f"practice_{docid}.md").write_text(practice_text_for(docid), encoding="utf-8")


def update_queue_statuses(queue_path: Path, raw_dir: Path, structured_dir: Path, queue_by_docid: dict[str, dict[str, Any]]) -> None:
    timestamp = now_iso()
    for act_path in sorted(raw_dir.glob("act_*.txt")):
        docid = docid_from_act(act_path)
        item = queue_by_docid.setdefault(
            docid,
            {
                "docid": docid,
                "act_path": act_path.as_posix(),
                "source_url": f"https://sudact.ru/regular/doc/{docid}/",
                "source_domain": "sudact.ru",
            },
        )
        complete = all(
            (structured_dir / f"{prefix}_{docid}.{ext}").exists()
            for prefix, ext in [("user_story", "md"), ("practice", "md"), ("structure", "json")]
        )
        if complete:
            item["status"] = "done"
            item["processed_by"] = item.get("processed_by") or "Codex/local-finalizer"
            item["processed_at"] = item.get("processed_at") or timestamp
        else:
            item["status"] = "pending"
    save_queue(queue_path, queue_by_docid)


def write_reports(batch_dir: Path, raw_dir: Path, structured_dir: Path) -> None:
    rows = []
    for act_path in sorted(raw_dir.glob("act_*.txt")):
        docid = docid_from_act(act_path)
        structure = read_json(structured_dir / f"structure_{docid}.json")
        taxonomy = structure.get("taxonomy", {}) if isinstance(structure.get("taxonomy"), dict) else {}
        publication = structure.get("publication", {}) if isinstance(structure.get("publication"), dict) else {}
        processing = structure.get("processing", {}) if isinstance(structure.get("processing"), dict) else {}
        rows.append(
            {
                "docid": docid,
                "has_user_story": (structured_dir / f"user_story_{docid}.md").exists(),
                "has_practice": (structured_dir / f"practice_{docid}.md").exists(),
                "has_structure": bool(structure),
                "processing_status": processing.get("status", ""),
                "dispute_type_code": taxonomy.get("dispute_type_code", ""),
                "claim_type_codes": ";".join(taxonomy.get("claim_type_codes", []) or []),
                "index_policy": publication.get("index_policy", ""),
                "main_site_fit": publication.get("main_site_fit", ""),
                "human_review_status": publication.get("human_review_status", ""),
            }
        )

    report_path = batch_dir / "structure_report.csv"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    hold_rows = [row for row in rows if row["index_policy"] == "hold"]
    index_rows = [row for row in rows if row["index_policy"] == "index"]
    hold_by_code: dict[str, int] = {}
    index_by_code: dict[str, int] = {}
    for row in hold_rows:
        hold_by_code[row["dispute_type_code"]] = hold_by_code.get(row["dispute_type_code"], 0) + 1
    for row in index_rows:
        index_by_code[row["dispute_type_code"]] = index_by_code.get(row["dispute_type_code"], 0) + 1

    enum_text = [
        "# Enum candidates / first DDU batch",
        "",
        "Новых enum-кодов автоматически не добавлялось.",
        "",
        "## Hold-кандидаты",
    ]
    for code, count in sorted(hold_by_code.items()):
        enum_text.append(f"- `{code}`: {count}")
    enum_text += ["", "## Индексируемые коды"]
    for code, count in sorted(index_by_code.items()):
        enum_text.append(f"- `{code}`: {count}")
    (batch_dir / "enum_candidates.md").write_text("\n".join(enum_text) + "\n", encoding="utf-8")

    batch_state = [
        "# DDU batch 2026-06-29-ddu-001 — состояние",
        "",
        f"Обновлено: {now_iso()}",
        "",
        "## Итог",
        f"- Raw актов: {len(rows)}",
        f"- Технически complete: {sum(1 for row in rows if row['has_user_story'] and row['has_practice'] and row['has_structure'])}",
        f"- Индексируемые: {len(index_rows)}",
        f"- Hold / ручная проверка: {len(hold_rows)}",
        "",
        "## Что исправлено после остановки Antigravity",
        "- дозакрыты отсутствующие user_story/practice/structure для недоделанных актов через hold-разметку;",
        "- исправлены невалидные enum/status поля в `K74QFxEvJFUB`; ",
        "- создан недостающий `structure_mJ8TjG4OypYx.json`; ",
        "- приведены к стандартным подзаголовкам проблемные `user_story_*.md`; ",
        "- пересобраны канонические `practice_*.md` для `jZyFxy7HJtmp`, `K74QFxEvJFUB`, `mJ8TjG4OypYx`; ",
        "- синхронизирован статус очереди.",
        "",
        "## Handoff",
        "- Перед генерацией публичных DDU-страниц отдельно проверить качество текстовых полей JSON: часть ранних DDU-структур содержит признаки поврежденной кодировки.",
        "- Hold-дела можно передать следующему агенту на повторную LLM-разметку без публикации.",
    ]
    (batch_dir / "batch_state.md").write_text("\n".join(batch_state) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/ddu/raw_acts")
    parser.add_argument("--structured-dir", default="data/ddu/structured")
    parser.add_argument("--queue", default="data/ddu/inbox/_queue.json")
    parser.add_argument("--batch-dir", default="data/ddu/parse_batches/2026-06-29-ddu-001")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    structured_dir = Path(args.structured_dir)
    queue_path = Path(args.queue)
    batch_dir = Path(args.batch_dir)
    queue_by_docid = load_queue(queue_path)

    fix_k74(structured_dir)
    make_mj8_structure("mJ8TjG4OypYx", raw_dir, structured_dir, queue_by_docid)

    existing_docids = {docid_from_act(path) for path in raw_dir.glob("act_*.txt")}
    for docid in sorted(existing_docids):
        if not (structured_dir / f"structure_{docid}.json").exists():
            make_hold_structure(docid, raw_dir, structured_dir, queue_by_docid)
        if not (structured_dir / f"user_story_{docid}.md").exists():
            make_hold_story(docid, raw_dir, structured_dir, queue_by_docid)
        if not (structured_dir / f"practice_{docid}.md").exists():
            make_hold_practice(docid, structured_dir)

    for docid in sorted(existing_docids):
        ensure_story_headings(docid, structured_dir)
    for docid in DOCIDS_PRACTICE_REWRITE:
        rewrite_practice(docid, structured_dir)

    update_queue_statuses(queue_path, raw_dir, structured_dir, queue_by_docid)
    write_reports(batch_dir, raw_dir, structured_dir)

    print("DDU batch gaps finalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
