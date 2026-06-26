# -*- coding: utf-8 -*-
"""Извлечение структуры из судебного акта через DeepSeek (Фаза 1.1).

Доказательство ядра: умеет ли LLM извлекать структуру по блокам из ТЗ
из полного текста судебного акта.

Промпт читается из prompt_extract.txt (UTF-8), текст акта — из act-файла.
Промпт, технические метаданные источника и текст акта объединяются и отправляются
в DeepSeek. Ответ сохраняется в JSON.

Использование:
  py scripts/extract_structure.py --act output/act_2-80_2025.txt --output output/structure_2-80_2025.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
KEY = os.environ["DEEPSEEK_API_KEY"].strip()


def docid_from_act_path(path: Path) -> str:
    name = path.name
    if name.startswith("act_") and name.endswith(".txt"):
        return name[len("act_"):-len(".txt")]
    return path.stem


def load_source_metadata(act_path: Path) -> dict:
    meta_path = act_path.with_suffix(".meta.json")
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    docid = docid_from_act_path(act_path)
    return {
        "docid": docid,
        "source_url": f"https://sudact.ru/regular/doc/{docid}/",
        "source_domain": "sudact.ru",
        "source_title": None,
        "source_passage": None,
        "raw_act_path": act_path.as_posix(),
        "raw_text_sha256": "",
        "source_type": "court_act",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Извлечение структуры акта через DeepSeek")
    ap.add_argument("--act", required=True, help="Файл с чистым текстом акта (UTF-8)")
    ap.add_argument("--prompt", default="scripts/prompt_extract.txt",
                    help="Файл промпта извлечения")
    ap.add_argument("--output", required=True,
                    help="Выходной JSON (обычно data/structured/structure_<номер>.json)")
    ap.add_argument("--model", default="deepseek-v4-pro",
                    help="Модель DeepSeek")
    args = ap.parse_args()

    prompt = Path(args.prompt).read_text(encoding="utf-8")
    act_path = Path(args.act)
    act_text = act_path.read_text(encoding="utf-8")
    source_metadata = load_source_metadata(act_path)
    print(f"Промпт: {len(prompt)} символов | Акт: {len(act_text)} символов | Модель: {args.model}")

    # Объединяем промпт + детерминированные метаданные + текст акта
    full_prompt = (
        prompt
        + "\n\nТехнические метаданные источника:\n"
        + json.dumps(source_metadata, ensure_ascii=False, indent=2)
        + "\n\nТекст судебного акта:\n"
        + act_text
    )

    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    print("Запрос к DeepSeek...")
    r = requests.post(url, headers=headers, data=data, timeout=120)

    if r.status_code != 200:
        print(f"ОШИБКА HTTP {r.status_code}: {r.text[:500]}")
        return 1

    content = r.json()["choices"][0]["message"]["content"]
    print(f"Ответ получен: {len(content)} символов")

    # Сохраняем сырой ответ
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"Сохранено: {out}")

    # Пытаемся распарсить как JSON и показать структуру
    try:
        parsed = json.loads(content)
        print("\n=== ИЗВЛЕЧЁННАЯ СТРУКТУРА ===")
        for key in ["source", "court", "taxonomy", "case_summary",
                    "claims_and_result", "legal_analysis", "publication",
                    "processing"]:
            val = parsed.get(key)
            if isinstance(val, (dict, list)):
                print(f"\n[{key}]")
                print(json.dumps(val, ensure_ascii=False, indent=2)[:600])
            else:
                print(f"\n[{key}]: {str(val)[:400]}")
    except json.JSONDecodeError as e:
        print(f"Ответ не валидный JSON: {e}")
        print(content[:500])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
