# -*- coding: utf-8 -*-
"""Дозаполнение structure_<docid>.json через DeepSeek API.

Назначение: добить только JSON v2 по актам, где Antigravity остановился из-за
лимитов. Готовые user_story_*.md и practice_*.md не перегенерируются.

Использование:
  py scripts/complete_structures_deepseek.py --model deepseek-v4-pro
  py scripts/complete_structures_deepseek.py --limit 1 --model deepseek-v4-pro
  py scripts/complete_structures_deepseek.py --docid yQ8qgPoesvWJ --model deepseek-v4-pro
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests


API_URL = "https://api.deepseek.com/chat/completions"
RAW_DIR = Path("data/raw_acts")
STRUCTURED_DIR = Path("data/structured")
PROMPT_PATH = Path("scripts/prompt_extract.txt")
ENV_PATH = Path("scripts/.env")

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


def load_api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DEEPSEEK_API_KEY не найден в окружении или scripts/.env")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def structure_path(docid: str) -> Path:
    return STRUCTURED_DIR / f"structure_{docid}.json"


def act_path(docid: str, existing: dict) -> Path:
    source = existing.get("source") if isinstance(existing.get("source"), dict) else {}
    raw_act_path = source.get("raw_act_path") or f"data/raw_acts/act_{docid}.txt"
    return Path(raw_act_path)


def docid_from_structure(path: Path) -> str:
    return path.name[len("structure_"):-len(".json")]


def incomplete_structure_paths(docid: str = "") -> list[Path]:
    if docid:
        paths = [structure_path(docid)]
    else:
        paths = sorted(STRUCTURED_DIR.glob("structure_*.json"))

    result = []
    for path in paths:
        if not path.exists():
            result.append(path)
            continue
        try:
            data = load_json(path)
        except json.JSONDecodeError:
            result.append(path)
            continue
        processing = data.get("processing")
        if not isinstance(processing, dict) or processing.get("status") != "complete":
            result.append(path)
    return result


def build_user_prompt(docid: str, existing: dict, act_text: str,
                      user_story: str, practice: str) -> str:
    source = existing.get("source") or {}
    existing_json = json.dumps(existing, ensure_ascii=False, indent=2)
    source_json = json.dumps(source, ensure_ascii=False, indent=2)
    return f"""
Задача: дозаполни JSON v2 по одному судебному акту.

Правила:
- Верни только один валидный JSON-объект.
- Сохрани `source` строго таким, как передан ниже. Не меняй `source_url`, `docid`, `raw_act_path`, `raw_text_sha256`.
- Не перегенерируй markdown-историю и правовой анализ; используй их только как вспомогательный контекст.
- Заполни пустые смысловые поля в `court`, `taxonomy`, `parties`, `case_summary`, `claims_and_result`, `legal_analysis`, `publication`.
- Правовые ссылки бери только из текста судебного акта. Не добавляй ссылки на внешнюю практику из знаний модели.
- `publication.legal_advice` должно быть false.
- В конце поставь:
  - `processing.status`: "complete"
  - `processing.processed_by`: "DeepSeek API / deepseek-v4-pro"
  - `processing.processed_at`: "{now_iso()}"

Docid: {docid}

Source-блок, который нужно сохранить без изменений:
{source_json}

Текущий JSON-заготовка:
{existing_json}

Уже готовая пользовательская история:
{user_story}

Уже готовый правовой анализ:
{practice}

Текст судебного акта:
{act_text}
""".strip()


def extract_json_object(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        raise


def validate_shape(docid: str, data: dict) -> None:
    if data.get("schema_version") != "2.0":
        raise ValueError(f"{docid}: schema_version должен быть 2.0")
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in data]
    if missing:
        raise ValueError(f"{docid}: нет top-level ключей: {', '.join(missing)}")
    processing = data.get("processing")
    if not isinstance(processing, dict) or processing.get("status") != "complete":
        raise ValueError(f"{docid}: processing.status не complete")


def call_deepseek(api_key: str, model: str, prompt_template: str,
                  user_prompt: str, max_tokens: int) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    prompt_template
                    + "\n\nТы обязан вернуть JSON. Не добавляй markdown, пояснения или текст вне JSON."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    response = requests.post(API_URL, headers=headers, json=payload, timeout=180)
    if response.status_code != 200:
        raise RuntimeError(f"DeepSeek HTTP {response.status_code}: {response.text[:500]}")
    content = response.json()["choices"][0]["message"]["content"]
    if not content.strip():
        raise RuntimeError("DeepSeek вернул пустой content")
    return extract_json_object(content)


def complete_one(api_key: str, model: str, path: Path, prompt_template: str,
                 max_tokens: int, retries: int, sleep_s: float) -> bool:
    docid = docid_from_structure(path)
    if not path.exists():
        print(f"[SKIP] {docid}: нет JSON-заготовки {path.as_posix()}")
        return False

    existing = load_json(path)
    raw_path = act_path(docid, existing)
    user_story_path = STRUCTURED_DIR / f"user_story_{docid}.md"
    practice_path = STRUCTURED_DIR / f"practice_{docid}.md"

    if not raw_path.exists():
        print(f"[SKIP] {docid}: нет акта {raw_path.as_posix()}")
        return False
    if not user_story_path.exists() or not practice_path.exists():
        print(f"[SKIP] {docid}: нет user_story/practice")
        return False

    act_text = raw_path.read_text(encoding="utf-8")
    user_story = user_story_path.read_text(encoding="utf-8")
    practice = practice_path.read_text(encoding="utf-8")
    user_prompt = build_user_prompt(docid, existing, act_text, user_story, practice)
    expected_source = existing.get("source") or {}

    for attempt in range(1, retries + 1):
        try:
            data = call_deepseek(api_key, model, prompt_template, user_prompt, max_tokens)
            data["source"] = expected_source
            data.setdefault("processing", {})
            data["processing"]["status"] = "complete"
            data["processing"]["processed_by"] = f"DeepSeek API / {model}"
            data["processing"]["processed_at"] = now_iso()
            validate_shape(docid, data)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[OK] {docid}")
            return True
        except Exception as exc:
            print(f"[ERR] {docid}: попытка {attempt}/{retries}: {exc}")
            if attempt < retries:
                time.sleep(sleep_s * attempt)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Complete structure JSONs with DeepSeek.")
    parser.add_argument("--model", default="deepseek-v4-pro", help="DeepSeek model id")
    parser.add_argument("--docid", default="", help="Обработать один docid")
    parser.add_argument("--limit", type=int, default=0, help="Лимит незавершённых JSON; 0 = все")
    parser.add_argument("--max-tokens", type=int, default=12000, help="max_tokens для ответа")
    parser.add_argument("--retries", type=int, default=3, help="Повторы на один акт")
    parser.add_argument("--sleep", type=float, default=2.0, help="Пауза между актами, сек.")
    args = parser.parse_args()

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    targets = incomplete_structure_paths(args.docid)
    if args.limit:
        targets = targets[:args.limit]

    print(f"Модель: {args.model}")
    print(f"Незавершённых JSON к обработке: {len(targets)}")
    if not targets:
        return 0

    api_key = load_api_key()
    ok = 0
    failed = 0
    for idx, path in enumerate(targets, 1):
        print(f"\n[{idx}/{len(targets)}] {path.name}")
        if complete_one(api_key, args.model, path, prompt_template,
                        args.max_tokens, args.retries, args.sleep):
            ok += 1
        else:
            failed += 1
        if idx < len(targets) and args.sleep > 0:
            time.sleep(args.sleep)

    print("\n=== ИТОГ ===")
    print(f"Успешно: {ok}")
    print(f"Ошибок: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
