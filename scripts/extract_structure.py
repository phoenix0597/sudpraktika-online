# -*- coding: utf-8 -*-
"""Извлечение структуры из судебного акта через DeepSeek (Фаза 1.1).

Доказательство ядра: умеет ли LLM извлекать структуру по блокам из ТЗ
из полного текста судебного акта.

Промпт читается из prompt_extract.txt (UTF-8), текст акта — из act-файла.
Оба объединяются и отправляются в DeepSeek. Ответ сохраняется в JSON.

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


def main() -> int:
    ap = argparse.ArgumentParser(description="Извлечение структуры акта через DeepSeek")
    ap.add_argument("--act", required=True, help="Файл с чистым текстом акта (UTF-8)")
    ap.add_argument("--prompt", default="scripts/prompt_extract.txt",
                    help="Файл промпта извлечения")
    ap.add_argument("--output", required=True,
                    help="Выходной JSON (обычно data/structured/structure_<номер>.json)")
    ap.add_argument("--model", default="deepseek-v4-flash",
                    help="Модель DeepSeek (flash=быстро/дёшево, pro=точнее)")
    args = ap.parse_args()

    prompt = Path(args.prompt).read_text(encoding="utf-8")
    act_text = Path(args.act).read_text(encoding="utf-8")
    print(f"Промпт: {len(prompt)} символов | Акт: {len(act_text)} символов | Модель: {args.model}")

    # Объединяем промпт + текст акта
    full_prompt = prompt + "\n\n" + act_text

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
        for key in ["situation", "remedy", "holding", "amounts", "timeline",
                    "metadata"]:
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
