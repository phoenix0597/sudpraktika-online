# -*- coding: utf-8 -*-
"""Build a lightweight local registry of already collected court acts.

The registry is a generated CSV index. The source of truth remains:
- data/raw_acts/act_<docid>.meta.json / .txt
- data/structured/structure_<docid>.json

Usage:
  python scripts/build_case_registry.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(".")
RAW_DIR = ROOT / "data/raw_acts"
STRUCTURED_DIR = ROOT / "data/structured"
DEFAULT_OUTPUT = ROOT / "data/registry/case_registry.csv"

FIELDS = [
    "docid",
    "source_url",
    "normalized_source_url",
    "source_domain",
    "raw_act_path",
    "raw_text_sha256",
    "has_raw",
    "has_structure",
    "processing_status",
    "index_policy",
    "main_site_fit",
    "court_system",
    "court_level",
    "region",
    "court_name",
    "case_number",
    "decision_date",
    "dispute_type_code",
    "claim_type_codes",
]


def normalize_url(url: str | None) -> str:
    return (url or "").strip().rstrip("/")


def docid_from_url(url: str | None) -> str:
    path = urlparse(url or "").path
    match = re.search(r"/regular/doc/([^/]+)/?", path)
    return match.group(1) if match else ""


def docid_from_act_file(path: Path) -> str:
    stem = path.stem
    return stem[4:] if stem.startswith("act_") else stem


def docid_from_meta_file(path: Path) -> str:
    name = path.name
    if name.startswith("act_") and name.endswith(".meta.json"):
        return name.removeprefix("act_").removesuffix(".meta.json")
    return path.stem


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def sha256_text_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    except OSError:
        return ""


def empty_row(docid: str) -> dict[str, str]:
    row = {field: "" for field in FIELDS}
    row["docid"] = docid
    row["has_raw"] = "false"
    row["has_structure"] = "false"
    return row


def upsert(registry: dict[str, dict[str, str]], docid: str, values: dict[str, Any]) -> None:
    if not docid:
        return
    row = registry.setdefault(docid, empty_row(docid))
    for field, value in values.items():
        if field not in FIELDS or value in (None, ""):
            continue
        if isinstance(value, bool):
            row[field] = "true" if value else "false"
        elif isinstance(value, list):
            row[field] = ";".join(str(item) for item in value if item not in (None, ""))
        else:
            row[field] = str(value)

    row["docid"] = docid
    row["normalized_source_url"] = normalize_url(row.get("source_url"))


def collect_raw(registry: dict[str, dict[str, str]]) -> None:
    for meta_path in sorted(RAW_DIR.glob("act_*.meta.json")):
        metadata = read_json(meta_path)
        docid = str(metadata.get("docid") or docid_from_meta_file(meta_path)).strip()
        upsert(
            registry,
            docid,
            {
                "source_url": metadata.get("source_url"),
                "source_domain": metadata.get("source_domain"),
                "raw_act_path": metadata.get("raw_act_path") or f"data/raw_acts/act_{docid}.txt",
                "raw_text_sha256": metadata.get("raw_text_sha256"),
                "has_raw": True,
            },
        )

    for act_path in sorted(RAW_DIR.glob("act_*.txt")):
        docid = docid_from_act_file(act_path)
        meta_path = act_path.with_suffix(".meta.json")
        if meta_path.exists():
            continue
        upsert(
            registry,
            docid,
            {
                "source_url": f"https://sudact.ru/regular/doc/{docid}/",
                "source_domain": "sudact.ru",
                "raw_act_path": act_path.as_posix(),
                "raw_text_sha256": sha256_text_file(act_path),
                "has_raw": True,
            },
        )


def collect_structured(registry: dict[str, dict[str, str]]) -> None:
    for structure_path in sorted(STRUCTURED_DIR.glob("structure_*.json")):
        data = read_json(structure_path)
        source = data.get("source", {}) if isinstance(data.get("source"), dict) else {}
        court = data.get("court", {}) if isinstance(data.get("court"), dict) else {}
        processing = data.get("processing", {}) if isinstance(data.get("processing"), dict) else {}
        publication = data.get("publication", {}) if isinstance(data.get("publication"), dict) else {}
        taxonomy = data.get("taxonomy", {}) if isinstance(data.get("taxonomy"), dict) else {}

        docid = str(source.get("docid") or structure_path.stem.removeprefix("structure_")).strip()
        upsert(
            registry,
            docid,
            {
                "source_url": source.get("source_url"),
                "source_domain": source.get("source_domain"),
                "raw_act_path": source.get("raw_act_path"),
                "raw_text_sha256": source.get("raw_text_sha256"),
                "has_raw": bool(source.get("raw_act_path") or (RAW_DIR / f"act_{docid}.txt").exists()),
                "has_structure": True,
                "processing_status": processing.get("status"),
                "index_policy": publication.get("index_policy"),
                "main_site_fit": publication.get("main_site_fit"),
                "court_system": court.get("court_system"),
                "court_level": court.get("court_level"),
                "region": court.get("region"),
                "court_name": court.get("court_name"),
                "case_number": court.get("case_number"),
                "decision_date": court.get("decision_date"),
                "dispute_type_code": taxonomy.get("dispute_type_code"),
                "claim_type_codes": taxonomy.get("claim_type_codes"),
            },
        )


def build_registry() -> list[dict[str, str]]:
    registry: dict[str, dict[str, str]] = {}
    collect_raw(registry)
    collect_structured(registry)
    return [registry[docid] for docid in sorted(registry)]


def write_registry(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Собрать CSV-реестр уже известных судебных актов")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Куда записать CSV-реестр")
    args = parser.parse_args()

    rows = build_registry()
    output = Path(args.output)
    write_registry(rows, output)

    raw_count = sum(1 for row in rows if row["has_raw"] == "true")
    structured_count = sum(1 for row in rows if row["has_structure"] == "true")
    print(f"Реестр: {output}")
    print(f"Всего docid: {len(rows)}; raw: {raw_count}; structured: {structured_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
