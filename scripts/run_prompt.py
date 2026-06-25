# -*- coding: utf-8 -*-
"""Прогон произвольного промпта по тексту акта через DeepSeek.

Обобщение extract_structure.py для Фазы 1.2: позволяет тестировать разные
промпты (пользовательская история, анализ практики) на одном акте и сравнивать
качество. Используется для A/B-теста DeepSeek vs эталона Gemini.

Использование:
  py scripts/run_prompt.py --act data/raw_acts/act_yQ8qgPoesvWJ.txt --prompt scripts/prompt_user_story.txt --output output/test_user_story.md
"""
import argparse
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
KEY = os.environ["DEEPSEEK_API_KEY"].strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Прогон промпта по акту через DeepSeek")
    ap.add_argument("--act", required=True, help="Файл с текстом акта (UTF-8)")
    ap.add_argument("--prompt", required=True, help="Файл промпта (UTF-8)")
    ap.add_argument("--output", required=True, help="Выходной файл")
    ap.add_argument("--model", default="deepseek-v4-pro",
                    help="Модель DeepSeek (pro=точнее для сложного анализа)")
    ap.add_argument("--max-tokens", type=int, default=3000)
    args = ap.parse_args()

    prompt = Path(args.prompt).read_text(encoding="utf-8")
    act_text = Path(args.act).read_text(encoding="utf-8")
    print(f"Промпт: {len(prompt)} символов | Акт: {len(act_text)} | Модель: {args.model}")

    full_prompt = prompt + "\n\n" + act_text

    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.3,  # чуть больше креативности для живого нарратива
        "max_tokens": args.max_tokens,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    print("Запрос к DeepSeek...")
    r = requests.post(url, headers=headers, data=data, timeout=180)
    if r.status_code != 200:
        print(f"ОШИБКА HTTP {r.status_code}: {r.text[:500]}")
        return 1

    content = r.json()["choices"][0]["message"]["content"]
    print(f"Ответ: {len(content)} символов")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"Сохранено: {out}\n")
    print("=" * 60)
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
