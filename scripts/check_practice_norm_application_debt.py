from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_ssg_prototype import split_legacy_application

STRUCTURED_DIR = ROOT / "data" / "structured"
DEBT_FILE = ROOT / "data" / "review" / "practice-norm-application-debt.txt"

NORMS_HEADING = "\u043d\u043e\u0440\u043c\u044b, \u043d\u0430 \u043a\u043e\u0442\u043e\u0440\u044b\u0435 \u0441\u043e\u0441\u043b\u0430\u043b\u0441\u044f \u0441\u0443\u0434"
LEGACY_NORM_RE = re.compile(r"^\*\*(.+?)\*\*\s*(?::|[\u2014-])\s*(.+)$")


def clean_heading(line: str) -> str:
    value = line.strip().rstrip(":").strip()
    value = re.sub(r"^#{1,6}\s+", "", value)
    value = re.sub(r"^\d+\.\s+", "", value)
    return value.strip()


def is_top_section_heading(line: str) -> bool:
    value = line.strip()
    return bool(re.match(r"^#{1,6}\s+\S", value) or re.match(r"^\d+\.\s+\S", value))


def is_indexable_case(docid: str) -> bool:
    path = STRUCTURED_DIR / f"structure_{docid}.json"
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    publication = data.get("publication") if isinstance(data, dict) else None
    if not isinstance(publication, dict):
        return False
    return publication.get("index_policy") != "hold" and publication.get("main_site_fit") is not False


def norms_section_lines(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    section_start: int | None = None
    for index, line in enumerate(lines):
        if clean_heading(line).lower() == NORMS_HEADING:
            section_start = index + 1
            break
    if section_start is None:
        return []

    result: list[str] = []
    for line in lines[section_start:]:
        if is_top_section_heading(line):
            break
        result.append(line)
    return result


def missing_application_count(path: Path) -> int:
    missing = 0
    for line in norms_section_lines(path):
        bullet = re.match(r"^\s*[*-]\s+(.+)$", line)
        if not bullet:
            continue

        legacy_norm = LEGACY_NORM_RE.match(bullet.group(1).strip())
        if not legacy_norm:
            continue

        details = legacy_norm.group(2).strip()
        _meaning, application = split_legacy_application(details)
        if not application:
            missing += 1

    return missing


def load_expected_debt() -> dict[str, int]:
    expected: dict[str, int] = {}
    for line in DEBT_FILE.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        docid, count = [part.strip() for part in value.split(",", 1)]
        expected[docid] = int(count)
    return expected


def detect_debt() -> dict[str, int]:
    actual: dict[str, int] = {}
    for path in sorted(STRUCTURED_DIR.glob("practice_*.md")):
        docid = path.stem.removeprefix("practice_")
        if not is_indexable_case(docid):
            continue
        count = missing_application_count(path)
        if count:
            actual[docid] = count
    return actual


def main() -> int:
    expected = load_expected_debt()
    actual = detect_debt()

    if actual == expected:
        print(
            f"practice norm application debt: {len(actual)} known pages, "
            f"{sum(actual.values())} norm items"
        )
        return 0

    expected_keys = set(expected)
    actual_keys = set(actual)
    new_docids = sorted(actual_keys - expected_keys)
    fixed_docids = sorted(expected_keys - actual_keys)
    changed_counts = sorted(
        docid for docid in expected_keys & actual_keys if expected[docid] != actual[docid]
    )

    print("practice norm application debt changed")
    if new_docids:
        print("new debt:")
        for docid in new_docids:
            print(f"  {docid},{actual[docid]}")
    if fixed_docids:
        print("debt fixed but still listed:")
        for docid in fixed_docids:
            print(f"  {docid},{expected[docid]}")
    if changed_counts:
        print("changed counts:")
        for docid in changed_counts:
            print(f"  {docid}: expected {expected[docid]}, actual {actual[docid]}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
