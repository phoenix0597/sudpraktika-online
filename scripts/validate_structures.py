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
import re
from pathlib import Path

import verify_citations


RAW_DIR = Path("data/raw_acts")
STRUCTURED_DIR = Path("data/structured")
ENUM_DICTIONARY_PATH = Path("data/reference/zpp_enum_dictionary.json")

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

ENUM_FIELDS = {
    "taxonomy.dispute_type_code": ("taxonomy", "dispute_type_code"),
    "taxonomy.claim_type_codes": ("taxonomy", "claim_type_codes"),
    "claims_and_result.outcome.result_type": ("claims_and_result", "outcome", "result_type"),
    "publication.index_policy": ("publication", "index_policy"),
}

STORY_SECTION_HEADINGS = (
    "Кто участвовал",
    "Обстоятельства и развитие событий",
    "Результат для потребителя",
    "Итог суда",
    "Что сделано не так и как поступить правильно",
)

ORG_PATTERN = re.compile(r"(?:ООО|АО|ПАО|ОАО|ЗАО)\s+[«\"]([^»\"]{2,100})[»\"]", re.IGNORECASE)

ANCHOR_STOPWORDS = {
    "потребитель",
    "потребителя",
    "покупатель",
    "покупателя",
    "ответчик",
    "ответчика",
    "истец",
    "истца",
    "исполнитель",
    "продавец",
    "суд",
    "закон",
    "защите",
    "права",
    "требование",
    "требования",
    "стоимость",
    "компенсация",
    "морального",
    "вреда",
    "неустойка",
    "штраф",
    "расходы",
    "рублей",
    "договор",
    "товар",
    "работа",
    "услуга",
    "услуги",
    "online",
    "return",
    "quality",
    "goods",
    "refusal",
    "accept",
    "deadline",
    "calculation",
    "compensation",
    "damages",
    "statutory",
    "fine",
    "fetched",
    "needs",
    "reprocessing",
    "structured",
}


def load_enum_values() -> dict[str, set[str]]:
    if not ENUM_DICTIONARY_PATH.exists():
        return {}
    data = json.loads(ENUM_DICTIONARY_PATH.read_text(encoding="utf-8"))
    fields = data.get("fields", {})
    result: dict[str, set[str]] = {}
    for field_name, spec in fields.items():
        values = spec.get("values", {}) if isinstance(spec, dict) else {}
        if isinstance(values, dict):
            result[field_name] = set(values)
    return result


def nested_get(data: dict, path: tuple[str, ...]) -> object:
    current: object = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


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


class WarningLog:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.count = 0

    def add(self, message: str) -> None:
        self.count += 1
        if self.count <= self.limit:
            print(f"[WARN] {message}")

    def finish(self) -> None:
        hidden = self.count - self.limit
        if hidden > 0:
            print(f"[WARN] ...и ещё {hidden} предупреждений скрыто")


def docid_from_act_file(path: Path) -> str:
    return path.name[len("act_"):-len(".txt")]


def non_empty(value: object) -> bool:
    return value is not None and value != ""


def normalize_match_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е"))


def iter_text_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result: list[str] = []
        for child in value.values():
            result.extend(iter_text_values(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(iter_text_values(child))
        return result
    return []


def normalize_story_heading(line: str) -> str:
    value = line.strip()
    value = re.sub(r"^#{1,6}\s+", "", value).strip()
    value = re.sub(r"^\*\*(.+?)\*\*$", r"\1", value).strip()
    value = re.sub(r"^\*(.+?)\*$", r"\1", value).strip()
    value = value.rstrip(":").strip()
    return re.sub(r"\s+", " ", value)


def validate_user_story_markdown_format(docid: str, path: Path, log: object) -> bool:
    text = path.read_text(encoding="utf-8")
    headings = {normalize_story_heading(line) for line in text.splitlines() if line.strip()}
    missing = [heading for heading in STORY_SECTION_HEADINGS if heading not in headings]
    if missing:
        log.add(f"{docid}: user_story.md без стандартных подзаголовков: {', '.join(missing)}")
        return False
    return True


def case_anchor_terms(data: dict) -> set[str]:
    taxonomy = data.get("taxonomy") if isinstance(data.get("taxonomy"), dict) else {}
    parties = data.get("parties") if isinstance(data.get("parties"), dict) else {}

    sources: list[object] = [
        taxonomy.get("platform_or_company"),
        taxonomy.get("object_type"),
        taxonomy.get("object_name"),
        parties.get("opponents"),
    ]
    raw_text = " ".join(
        part
        for source in sources
        for part in iter_text_values(source)
        if part
    )
    terms = {
        word.lower().replace("ё", "е")
        for word in re.findall(r"[A-Za-zА-Яа-яЁё0-9]{4,}", raw_text)
    }
    return {term for term in terms if term not in ANCHOR_STOPWORDS}


def validate_markdown_case_consistency(docid: str, kind: str, path: Path, data: dict,
                                       act_text: str, log: object) -> bool:
    """Ловит технические признаки рассинхрона markdown-артефакта с делом.

    Это не полноценная юридическая проверка смысла. Цель — поймать случаи,
    когда `practice_*.md` или `user_story_*.md` явно попали от другого docid:
    чужие организации, чужие названия объектов и отсутствие якорей текущего дела.
    """
    text = path.read_text(encoding="utf-8")
    normalized_text = normalize_match_text(text)
    corpus = normalize_match_text(act_text + " " + json.dumps(data, ensure_ascii=False))
    ok = True

    if kind == "practice":
        anchors = case_anchor_terms(data)
        anchor_hits = sorted(term for term in anchors if term in normalized_text)

        foreign_orgs = []
        for match in ORG_PATTERN.finditer(text):
            org_name = normalize_match_text(match.group(1))
            full_org = normalize_match_text(match.group(0))
            if org_name not in corpus and full_org not in corpus:
                foreign_orgs.append(match.group(0))

        if foreign_orgs and not anchor_hits:
            log.add(
                f"{docid}: practice.md похож на чужой разбор: нет якорей текущего дела, "
                f"есть сторонняя организация {', '.join(sorted(set(foreign_orgs)))}"
            )
            ok = False

    return ok


def normalize_practice_line(line: str) -> str:
    value = line.strip()
    if value.startswith(("* ", "- ")):
        value = value[2:].strip()
    value = re.sub(r"^\*+", "", value).strip()
    value = re.sub(r"^\*\*(.+?)\*\*", r"\1", value).strip()
    value = re.sub(r"^\*(.+?)\*", r"\1", value).strip()
    return value


def practice_note_label(line: str) -> str | None:
    value = normalize_practice_line(line)
    for label in (
        "Значение в деле",
        "Применение судом",
        "Что означает в деле",
        "Как применена судом",
    ):
        if value.startswith(f"{label}:"):
            return label
    return None


def is_canonical_practice_note(line: str, label: str) -> bool:
    return bool(re.match(rf"^\s{{2,}}[*-]\s+\*\*{re.escape(label)}:\*\*\s+\S", line))


def is_norms_section_heading(line: str) -> bool:
    value = line.strip().rstrip(":")
    return bool(
        re.match(
            r"^(?:#{1,6}\s+|\d+\.\s*)Нормы, на которые сослался суд$",
            value,
            flags=re.IGNORECASE,
        )
    )


def is_practice_top_section_heading(line: str) -> bool:
    value = line.strip()
    return bool(re.match(r"^#{1,6}\s+\S", value) or re.match(r"^\d+\.\s+\S", value))


def validate_practice_markdown_format(docid: str, path: Path, log: object) -> bool:
    """Проверяет единообразие markdown-формата блока норм в practice_*.md.

    Это не проверка юридической корректности. Юридические ссылки проверяются
    verify_all.py / verify_citations.py. Здесь ловим только формат, который
    влияет на единообразный рендеринг страниц.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    section_start = None
    for idx, line in enumerate(lines):
        if is_norms_section_heading(line):
            section_start = idx + 1
            break

    if section_start is None:
        log.add(f"{docid}: practice.md не содержит раздел 'Нормы, на которые сослался суд'")
        return False

    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in lines[section_start:]:
        if is_practice_top_section_heading(line):
            break
        if re.match(r"^\s*[*-]\s+\*\*.+?\*\*", line) and practice_note_label(line) is None:
            if current:
                blocks.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current:
        blocks.append(current)

    if not blocks:
        log.add(f"{docid}: в блоке норм не найдено пунктов вида '* **Норма**'")
        return False

    ok = True
    noncanonical_reported = False
    for index, block in enumerate(blocks, start=1):
        labels = [label for line in block[1:] if (label := practice_note_label(line))]
        if not labels:
            if not noncanonical_reported:
                log.add(
                    f"{docid}: старый или неканонический формат блока норм; нужен '* **Норма**' "
                    "с вложенными '* **Значение в деле:**' и '* **Применение судом:**'"
                )
                noncanonical_reported = True
            ok = False
            continue

        has_meaning = any(label in {"Значение в деле", "Что означает в деле"} for label in labels)
        has_application = any(label in {"Применение судом", "Как применена судом"} for label in labels)

        if not has_meaning:
            log.add(f"{docid}: норма #{index} без пояснения 'Значение в деле'")
            ok = False
        if not has_application:
            log.add(f"{docid}: норма #{index} без пояснения 'Применение судом'")
            ok = False

        canonical_meaning = any(is_canonical_practice_note(line, "Значение в деле") for line in block[1:])
        canonical_application = any(is_canonical_practice_note(line, "Применение судом") for line in block[1:])
        if (has_meaning or has_application) and not (canonical_meaning and canonical_application):
            if not noncanonical_reported:
                log.add(
                    f"{docid}: неканонический формат блока норм; нужен '* **Норма**' "
                    "с вложенными '* **Значение в деле:**' и '* **Применение судом:**'"
                )
                noncanonical_reported = True
            ok = False

    return ok


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


def validate_enum_fields(docid: str, data: dict, enum_values: dict[str, set[str]],
                         errors: ErrorLog) -> bool:
    if not enum_values:
        return True

    ok = True
    for field_name, path in ENUM_FIELDS.items():
        allowed = enum_values.get(field_name)
        if not allowed:
            continue
        value = nested_get(data, path)
        if field_name == "taxonomy.claim_type_codes":
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                errors.add(f"{docid}: taxonomy.claim_type_codes must be a list of strings")
                ok = False
                continue
            invalid = [item for item in value if item not in allowed]
            if invalid:
                errors.add(f"{docid}: invalid taxonomy.claim_type_codes: {', '.join(invalid)}")
                ok = False
            continue
        if not isinstance(value, str) or value not in allowed:
            errors.add(f"{docid}: invalid {field_name}: {value!r}")
            ok = False

    main_site_fit = nested_get(data, ("publication", "main_site_fit"))
    if not isinstance(main_site_fit, bool):
        errors.add(f"{docid}: publication.main_site_fit must be boolean")
        ok = False

    index_policy = nested_get(data, ("publication", "index_policy"))
    dispute_type_code = nested_get(data, ("taxonomy", "dispute_type_code"))
    claim_type_codes = nested_get(data, ("taxonomy", "claim_type_codes"))
    if index_policy == "index":
        if main_site_fit is not True:
            errors.add(f"{docid}: publication.index_policy='index' requires main_site_fit=true")
            ok = False
        if dispute_type_code in {"contract_validity_non_zpp", "non_consumer_hold"}:
            errors.add(f"{docid}: {dispute_type_code} cannot be indexed")
            ok = False
        if isinstance(claim_type_codes, list) and "hold" in claim_type_codes:
            errors.add(f"{docid}: indexed case cannot use service claim_type_code 'hold'")
            ok = False
    elif index_policy == "hold" and main_site_fit is not False:
        errors.add(f"{docid}: publication.index_policy='hold' requires main_site_fit=false")
        ok = False

    return ok


def validate_structure(docid: str, path: Path, act_text: str, errors: ErrorLog,
                       enum_values: dict[str, set[str]],
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

    if not validate_enum_fields(docid, data, enum_values, errors):
        ok = False

    publication = data.get("publication") if isinstance(data.get("publication"), dict) else {}
    if publication.get("index_policy") == "index":
        serialized = json.dumps(data, ensure_ascii=False)
        if "????" in serialized:
            errors.add(f"{docid}: indexed JSON contains suspicious mojibake marker '????'")
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
    parser.add_argument(
        "--docid",
        action="append",
        default=[],
        help="Проверить только указанные docid. Можно передавать несколько раз или через запятую.",
    )
    parser.add_argument(
        "--check-practice-format",
        action="store_true",
        help="Проверять единый markdown-формат блока норм в practice_*.md.",
    )
    parser.add_argument(
        "--strict-practice-format",
        action="store_true",
        help="Считать предупреждения по формату practice_*.md ошибками.",
    )
    parser.add_argument(
        "--check-user-story-format",
        action="store_true",
        help="Проверять наличие стандартных подзаголовков в user_story_*.md.",
    )
    parser.add_argument(
        "--strict-user-story-format",
        action="store_true",
        help="Считать отсутствие стандартных подзаголовков user_story_*.md ошибкой.",
    )
    parser.add_argument(
        "--check-md-consistency",
        action="store_true",
        help="Проверять технические признаки соответствия user_story/practice текущему делу.",
    )
    parser.add_argument(
        "--strict-md-consistency",
        action="store_true",
        help="Считать рассинхрон markdown-артефактов с делом ошибкой.",
    )
    args = parser.parse_args()

    act_files = sorted(RAW_DIR.glob("act_*.txt"))
    if args.docid:
        wanted_docids = {
            value.strip()
            for item in args.docid
            for value in item.split(",")
            if value.strip()
        }
        act_files = [path for path in act_files if docid_from_act_file(path) in wanted_docids]

    errors = ErrorLog(args.max_errors)
    warnings = WarningLog(args.max_errors)
    enum_values = load_enum_values()
    stats = {
        "acts": len(act_files),
        "user_story_ok": 0,
        "user_story_format_ok": 0,
        "practice_ok": 0,
        "practice_format_ok": 0,
        "md_consistency_ok": 0,
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
            if args.check_user_story_format or args.strict_user_story_format:
                story_format_log = errors if args.strict_user_story_format else warnings
                if validate_user_story_markdown_format(docid, user_story, story_format_log):
                    stats["user_story_format_ok"] += 1
        else:
            errors.add(f"{docid}: нет или пустой {user_story.as_posix()}")

        if practice.exists() and practice.stat().st_size > 0:
            stats["practice_ok"] += 1
            if args.check_practice_format or args.strict_practice_format:
                format_log = errors if args.strict_practice_format else warnings
                if validate_practice_markdown_format(docid, practice, format_log):
                    stats["practice_format_ok"] += 1
        else:
            errors.add(f"{docid}: нет или пустой {practice.as_posix()}")

        if validate_structure(
            docid,
            structure,
            act_text,
            errors,
            enum_values,
            args.allow_incomplete,
            args.skip_citation_check,
        ):
            stats["structure_ok"] += 1

        if args.check_md_consistency or args.strict_md_consistency:
            consistency_log = errors if args.strict_md_consistency else warnings
            try:
                data_for_consistency = json.loads(structure.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data_for_consistency = {}
            md_ok = True
            if user_story.exists() and user_story.stat().st_size > 0:
                md_ok = validate_markdown_case_consistency(
                    docid, "user_story", user_story, data_for_consistency, act_text, consistency_log
                ) and md_ok
            if practice.exists() and practice.stat().st_size > 0:
                md_ok = validate_markdown_case_consistency(
                    docid, "practice", practice, data_for_consistency, act_text, consistency_log
                ) and md_ok
            if md_ok:
                stats["md_consistency_ok"] += 1

    errors.finish()
    warnings.finish()

    print("\n=== ИТОГИ ПРОВЕРКИ STRUCTURED ===")
    print(f"Всего raw актов: {stats['acts']}")
    print(f"  user_story ok: {stats['user_story_ok']}")
    if args.check_user_story_format or args.strict_user_story_format:
        print(f"  user_story format ok: {stats['user_story_format_ok']}")
    print(f"  practice ok: {stats['practice_ok']}")
    if args.check_practice_format or args.strict_practice_format:
        print(f"  practice format ok: {stats['practice_format_ok']}")
    if args.check_md_consistency or args.strict_md_consistency:
        print(f"  markdown consistency ok: {stats['md_consistency_ok']}")
    print(f"  structure ok: {stats['structure_ok']}")
    print(f"  ошибок: {errors.count}")
    if (
        (args.check_practice_format and not args.strict_practice_format)
        or (args.check_user_story_format and not args.strict_user_story_format)
        or (args.check_md_consistency and not args.strict_md_consistency)
    ):
        print(f"  предупреждений: {warnings.count}")

    return 1 if errors.count else 0


if __name__ == "__main__":
    raise SystemExit(main())
