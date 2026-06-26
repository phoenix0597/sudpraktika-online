# -*- coding: utf-8 -*-
"""Проверка полноты структурированных результатов по судебным актам.

Проверяет для каждого data/raw_acts/act_<docid>.txt:
- наличие user_story_<docid>.md;
- наличие practice_<docid>.md;
- наличие валидного structure_<docid>.json;
- обязательные верхнеуровневые ключи JSON v2;
- source-поля и статус semantic JSON.
"""
import argparse
import json
from pathlib import Path

import verify_citations


RAW_DIR = Path("data/raw_acts")
STRUCTURED_DIR = Path("data/structured")

REQUIRED_TOP_LEVEL = [
    "schema_version",
    "source",
    "court",
    "taxonomy",
    "parties",
    "case_summary",
    "claims_and_result",
    "legal_analysis",
    "publication",
    "processing",
]

REQUIRED_SOURCE_FIELDS = [
    "docid",
    "source_url",
    "source_domain",
    "raw_act_path",
    "raw_text_sha256",
    "source_type",
]


class ErrorLog:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.count = 0

    def add(self, message: str) -> None:
        self.count += 1
        if self.count <= self.limit:
            print(f"[ERR] {message}")

    def finish(self) -> None:
        hidden = self.count - self.limit
        if hidden > 0:
            print(f"[ERR] ...и ещё {hidden} ошибок скрыто")


def docid_from_act_file(path: Path) -> str:
    return path.name[len("act_"):-len(".txt")]


def non_empty(value: object) -> bool:
    return value is not None and value != ""


def validate_json_citations(docid: str, data: dict, act_text: str,
                            errors: ErrorLog) -> bool:
    legal_analysis = data.get("legal_analysis")
    if not isinstance(legal_analysis, dict):
        return True

    text_for_check = json.dumps(legal_analysis, ensure_ascii=False)
    citations = verify_citations.extract_citations(text_for_check)
    if not citations:
        return True

    results = verify_citations.verify(act_text, citations)
    bad = [cit for cit, result in results.items() if result is False]
    if bad:
        errors.add(f"{docid}: legal_analysis содержит ссылки не из текста акта: {', '.join(bad)}")
        return False
    return True


def validate_structure(docid: str, path: Path, act_text: str, errors: ErrorLog,
                       allow_incomplete: bool, skip_citation_check: bool) -> bool:
    if not path.exists():
        errors.add(f"{docid}: нет {path.as_posix()}")
        return False

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.add(f"{docid}: невалидный JSON ({exc})")
        return False

    ok = True
    if data.get("schema_version") != "2.0":
        errors.add(f"{docid}: schema_version != 2.0")
        ok = False

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.add(f"{docid}: нет top-level ключа {key}")
            ok = False

    source = data.get("source") if isinstance(data.get("source"), dict) else {}
    for key in REQUIRED_SOURCE_FIELDS:
        if not non_empty(source.get(key)):
            errors.add(f"{docid}: пустой source.{key}")
            ok = False

    if source.get("docid") and source.get("docid") != docid:
        errors.add(f"{docid}: source.docid не совпадает с именем файла")
        ok = False

    processing = data.get("processing") if isinstance(data.get("processing"), dict) else {}
    status = processing.get("status")
    if not allow_incomplete and status != "complete":
        errors.add(f"{docid}: processing.status = {status!r}, нужен 'complete'")
        ok = False

    if not skip_citation_check and not validate_json_citations(docid, data, act_text, errors):
        ok = False

    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate structured case outputs.")
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Не считать ошибкой processing.status != complete (для проверки заготовок).",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=40,
        help="Сколько ошибок вывести подробно.",
    )
    parser.add_argument(
        "--skip-citation-check",
        action="store_true",
        help="Не проверять правовые ссылки внутри structure_*.json.",
    )
    args = parser.parse_args()

    act_files = sorted(RAW_DIR.glob("act_*.txt"))
    errors = ErrorLog(args.max_errors)
    stats = {
        "acts": len(act_files),
        "user_story_ok": 0,
        "practice_ok": 0,
        "structure_ok": 0,
    }

    for act_file in act_files:
        docid = docid_from_act_file(act_file)
        act_text = act_file.read_text(encoding="utf-8")
        user_story = STRUCTURED_DIR / f"user_story_{docid}.md"
        practice = STRUCTURED_DIR / f"practice_{docid}.md"
        structure = STRUCTURED_DIR / f"structure_{docid}.json"

        if user_story.exists() and user_story.stat().st_size > 0:
            stats["user_story_ok"] += 1
        else:
            errors.add(f"{docid}: нет или пустой {user_story.as_posix()}")

        if practice.exists() and practice.stat().st_size > 0:
            stats["practice_ok"] += 1
        else:
            errors.add(f"{docid}: нет или пустой {practice.as_posix()}")

        if validate_structure(
            docid,
            structure,
            act_text,
            errors,
            args.allow_incomplete,
            args.skip_citation_check,
        ):
            stats["structure_ok"] += 1

    errors.finish()

    print("\n=== ИТОГИ ПРОВЕРКИ STRUCTURED ===")
    print(f"Всего raw актов: {stats['acts']}")
    print(f"  user_story ok: {stats['user_story_ok']}")
    print(f"  practice ok: {stats['practice_ok']}")
    print(f"  structure ok: {stats['structure_ok']}")
    print(f"  ошибок: {errors.count}")

    return 1 if errors.count else 0


if __name__ == "__main__":
    raise SystemExit(main())
