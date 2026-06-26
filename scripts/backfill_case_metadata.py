# -*- coding: utf-8 -*-
"""Восстановление source-метаданных и заготовок JSON v2 для уже скачанных актов.

Зачем это нужно:
1) ссылка на первоисточник, домен, путь и хэш текста фиксируются детерминированно;
2) LLM-агент получает готовый source-блок и заполняет только смысловую часть JSON;
3) старая партия актов не требует повторного парсинга ради source_url.

Использование:
  py scripts/backfill_case_metadata.py --csv output/cases_ozon_regular.csv --seed-structures
"""
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


RAW_DIR = Path("data/raw_acts")
STRUCTURED_DIR = Path("data/structured")
QUEUE_PATH = Path("data/inbox/_queue.json")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def docid_from_act_file(path: Path) -> str:
    name = path.name
    if not name.startswith("act_") or not name.endswith(".txt"):
        raise ValueError(f"Неожиданное имя файла акта: {name}")
    return name[len("act_"):-len(".txt")]


def docid_from_url(url: str) -> str | None:
    match = re.search(r"/regular/doc/([^/]+)/?", urlparse(url).path)
    return match.group(1) if match else None


def reconstruct_sudact_url(docid: str) -> str:
    return f"https://sudact.ru/regular/doc/{docid}/"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_search_rows(csv_path: Path | None) -> dict[str, dict]:
    if not csv_path or not csv_path.exists():
        return {}
    result: dict[str, dict] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            url = (row.get("url") or "").strip()
            docid = docid_from_url(url)
            if docid:
                result[docid] = row
    return result


def build_metadata(docid: str, act_file: Path, search_row: dict | None) -> dict:
    search_row = search_row or {}
    url = (search_row.get("url") or "").strip() or reconstruct_sudact_url(docid)
    parsed = urlparse(url)
    text = act_file.read_text(encoding="utf-8")
    return {
        "docid": docid,
        "source_url": url,
        "source_domain": (search_row.get("domain") or parsed.netloc or "sudact.ru").strip(),
        "source_title": (search_row.get("title") or "").strip() or None,
        "source_passage": (search_row.get("passage") or "").strip() or None,
        "raw_act_path": act_file.as_posix(),
        "raw_text_sha256": sha256_text(text),
        "source_type": "court_act",
        "metadata_updated_at": now_iso(),
    }


def write_act_metadata(act_file: Path, metadata: dict) -> None:
    act_file.with_suffix(".meta.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def empty_structure_v2(metadata: dict) -> dict:
    return {
        "schema_version": "2.0",
        "source": {
            "docid": metadata["docid"],
            "source_url": metadata["source_url"],
            "source_domain": metadata["source_domain"],
            "source_title": metadata.get("source_title"),
            "source_passage": metadata.get("source_passage"),
            "raw_act_path": metadata["raw_act_path"],
            "raw_text_sha256": metadata["raw_text_sha256"],
            "source_type": metadata.get("source_type", "court_act"),
        },
        "court": {
            "case_number": "",
            "court_name": "",
            "court_level": "",
            "court_system": "general_jurisdiction",
            "region": "",
            "city_or_locality": None,
            "decision_date": "",
            "instance": "",
        },
        "taxonomy": {
            "legal_domain": "consumer_protection",
            "procedure_type": "civil",
            "audience_segment": "citizen",
            "topic_vertical": "marketplaces",
            "dispute_type_code": "",
            "dispute_type": "",
            "claim_type_codes": [],
            "claim_type": "",
            "platform_or_company": None,
            "object_type": None,
            "object_name": None,
            "situation_tags": [],
        },
        "parties": {
            "focus_party": {
                "role": "consumer",
                "name_raw": None,
            },
            "opponents": [],
            "third_parties": [],
        },
        "case_summary": {
            "situation": "",
            "timeline": [],
            "key_factors": [],
            "practical_takeaways": [],
            "unusual_points": [],
        },
        "claims_and_result": {
            "remedy": "",
            "outcome": {
                "focus_party_result": "",
                "result_type": "",
                "short_reason": "",
            },
            "amounts": {
                "claimed_total": None,
                "awarded_total": None,
                "items_claimed": [],
                "items_awarded": [],
            },
        },
        "legal_analysis": {
            "holding": "",
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
        "processing": {
            "status": "metadata_seeded",
            "processed_by": None,
            "processed_at": None,
        },
    }


def migrate_v1_to_v2(existing: dict, metadata: dict) -> dict:
    result = empty_structure_v2(metadata)
    old_meta = existing.get("metadata") or {}
    amounts = existing.get("amounts") or {}

    result["court"].update({
        "case_number": old_meta.get("case_number") or "",
        "court_name": old_meta.get("court") or "",
        "court_level": old_meta.get("court_level") or "",
        "region": old_meta.get("region") or "",
        "decision_date": old_meta.get("date") or "",
        "instance": old_meta.get("instance") or "",
    })
    result["taxonomy"]["topic_vertical"] = old_meta.get("vertical") or "marketplaces"
    result["case_summary"]["situation"] = existing.get("situation") or ""
    result["case_summary"]["timeline"] = existing.get("timeline") or []
    result["case_summary"]["key_factors"] = existing.get("key_factors") or []
    result["claims_and_result"]["remedy"] = existing.get("remedy") or ""
    result["claims_and_result"]["amounts"]["claimed_total"] = amounts.get("claimed")
    result["claims_and_result"]["amounts"]["awarded_total"] = amounts.get("awarded")
    result["legal_analysis"]["holding"] = existing.get("holding") or ""
    result["legal_analysis"]["arguments_rejected"] = (
        existing.get("defendant_arguments_rejected") or []
    )
    result["processing"] = {
        "status": "migrated_from_v1_needs_review",
        "processed_by": "legacy_json_v1",
        "processed_at": now_iso(),
    }
    return result


def merge_structure(structure_path: Path, metadata: dict) -> str:
    if not structure_path.exists():
        structure_path.write_text(
            json.dumps(empty_structure_v2(metadata), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return "created"

    try:
        existing = json.loads(structure_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = structure_path.with_suffix(".invalid.json")
        backup.write_text(structure_path.read_text(encoding="utf-8"), encoding="utf-8")
        structure_path.write_text(
            json.dumps(empty_structure_v2(metadata), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return "replaced_invalid"

    if existing.get("schema_version") != "2.0":
        migrated = migrate_v1_to_v2(existing, metadata)
        structure_path.write_text(
            json.dumps(migrated, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return "migrated_v1"

    changed = False
    source = existing.setdefault("source", {})
    for key, value in empty_structure_v2(metadata)["source"].items():
        if source.get(key) != value:
            source[key] = value
            changed = True
    if changed:
        structure_path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return "updated_source"
    return "unchanged"


def update_queue(metadata_by_docid: dict[str, dict]) -> int:
    if not QUEUE_PATH.exists():
        return 0
    queue_doc = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    queue_doc["_description"] = (
        "Очередь актов на обработку ИИ-агентом (Antigravity/ZCode). "
        "Пополняется Python-пайплайном, обрабатывается агентом. "
        "status: done допустим только после user_story, practice и structure JSON."
    )
    queue_doc["_workflow"] = (
        "1) Python кладёт акт в data/raw_acts/, пишет source-метаданные и добавляет "
        "запись сюда. 2) Агент читает _TASK.md, берёт pending-акты или done-акты "
        "с неполным комплектом, пишет user_story_<docid>.md + practice_<docid>.md + "
        "structure_<docid>.json в data/structured/. 3) Python-верификаторы "
        "verify_all.py и validate_structures.py проверяют результат."
    )
    queue_doc["_last_updated"] = datetime.now().date().isoformat()

    updated = 0
    for item in queue_doc.get("queue", []):
        docid = item.get("docid")
        metadata = metadata_by_docid.get(docid)
        if not metadata:
            continue
        meta_path = Path(metadata["raw_act_path"]).with_suffix(".meta.json")
        patch = {
            "source_url": metadata["source_url"],
            "source_domain": metadata["source_domain"],
            "source_title": metadata.get("source_title"),
            "source_passage": metadata.get("source_passage"),
            "raw_text_sha256": metadata["raw_text_sha256"],
            "source_meta_path": meta_path.as_posix(),
        }
        for key, value in patch.items():
            if item.get(key) != value:
                item[key] = value
                updated += 1

    QUEUE_PATH.write_text(
        json.dumps(queue_doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill source metadata and optional JSON v2 skeletons."
    )
    parser.add_argument("--csv", default="", help="CSV поиска с колонками url/domain/title/passage")
    parser.add_argument(
        "--seed-structures",
        action="store_true",
        help="Создать/обновить data/structured/structure_<docid>.json source-блоками",
    )
    parser.add_argument(
        "--no-queue-update",
        action="store_true",
        help="Не обновлять data/inbox/_queue.json source-метаданными",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else None
    search_rows = load_search_rows(csv_path)
    metadata_by_docid: dict[str, dict] = {}
    stats = {
        "meta_written": 0,
        "structure_created": 0,
        "structure_migrated_v1": 0,
        "structure_updated_source": 0,
        "structure_unchanged": 0,
        "structure_replaced_invalid": 0,
    }

    STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)

    for act_file in sorted(RAW_DIR.glob("act_*.txt")):
        docid = docid_from_act_file(act_file)
        metadata = build_metadata(docid, act_file, search_rows.get(docid))
        metadata_by_docid[docid] = metadata
        write_act_metadata(act_file, metadata)
        stats["meta_written"] += 1

        if args.seed_structures:
            structure_path = STRUCTURED_DIR / f"structure_{docid}.json"
            action = merge_structure(structure_path, metadata)
            stats[f"structure_{action}"] += 1

    queue_updates = 0 if args.no_queue_update else update_queue(metadata_by_docid)

    print("Готово.")
    print(f"  source metadata written: {stats['meta_written']}")
    if args.seed_structures:
        print(f"  structure created: {stats['structure_created']}")
        print(f"  structure migrated v1: {stats['structure_migrated_v1']}")
        print(f"  structure source updated: {stats['structure_updated_source']}")
        print(f"  structure unchanged: {stats['structure_unchanged']}")
        print(f"  structure invalid replaced: {stats['structure_replaced_invalid']}")
    print(f"  queue fields updated: {queue_updates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
