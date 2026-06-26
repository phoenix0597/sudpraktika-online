# -*- coding: utf-8 -*-
"""Merge and filter court-act candidate CSV files against the local registry.

Use this after one or more find_cases.py runs, or to reuse an old search CSV.

Example:
  python scripts/filter_case_candidates.py \
    --input output/cases_ozon_regular.csv \
    --output data/parse_batches/2026-06-26-zpp-next/new_candidates.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from find_cases import (
    DEFAULT_REGISTRY,
    dedupe_by_url,
    docid_from_url,
    exclude_known_cases,
    load_known_cases,
)


FIELDS = ["docid", "url", "domain", "title", "passage"]


def read_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                url = (row.get("url") or "").strip()
                if not url:
                    continue
                rows.append(
                    {
                        "docid": (row.get("docid") or docid_from_url(url)).strip(),
                        "url": url,
                        "domain": (row.get("domain") or "").strip(),
                        "title": (row.get("title") or "").strip(),
                        "passage": (row.get("passage") or "").strip(),
                    }
                )
    return rows


def write_rows(rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Отфильтровать CSV кандидатов по локальному реестру")
    parser.add_argument("--input", action="append", required=True, help="Входной CSV; можно указать несколько раз")
    parser.add_argument("--output", required=True, help="Выходной CSV с новыми кандидатами")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="CSV-реестр известных актов")
    parser.add_argument("--include-known", action="store_true", help="Не исключать уже известные дела")
    args = parser.parse_args()

    input_paths = [Path(value) for value in args.input]
    rows = read_rows(input_paths)
    unique_rows = dedupe_by_url(rows)

    skipped_known = 0
    if args.include_known:
        filtered_rows = unique_rows
    else:
        known_docids, known_urls = load_known_cases(Path(args.registry))
        filtered_rows, skipped_known = exclude_known_cases(unique_rows, known_docids, known_urls)

    write_rows(filtered_rows, Path(args.output))

    print(f"Входных строк: {len(rows)}")
    print(f"Уникальных URL: {len(unique_rows)}")
    print(f"Исключено известных: {skipped_known}")
    print(f"Новых кандидатов: {len(filtered_rows)}")
    print(f"CSV: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
