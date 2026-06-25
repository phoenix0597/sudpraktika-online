# -*- coding: utf-8 -*-
"""Гибридный поиск фактов через DeepSeek API.

Экономит месячную квоту MCP (WebSearch/webReader). Для устойчивых знаний:
значения enum, структуры API, отраслевые диапазоны, практики, форматы.

Использование:
  py scripts/hybrid_lookup.py "ваш вопрос"

Вопрос можно передать аргументом или ввести интерактивно. Кириллица работает:
вопрос пишется во временный UTF-8 файл, читается обратно — обход кодировки cmd.

Паттерн: оффлайн-знание (DeepSeek) → прицельный HTTP → MCP только в крайнем случае.
"""
import os
import sys
import json
import tempfile
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
if not KEY:
    sys.exit("ОШИБКА: DEEPSEEK_API_KEY не задан в scripts/.env")

# Вопрос: из аргументов командной строки или интерактивно через временный файл
if len(sys.argv) > 1:
    question = " ".join(sys.argv[1:])
else:
    print("Введите вопрос (Ctrl+Z в новой строке для завершения):")
    raw = sys.stdin.read()
    question = raw.strip()
if not question:
    sys.exit("Вопрос пуст.")

url = "https://api.deepseek.com/chat/completions"
headers = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "Отвечай кратко и по делу. Если не уверен — скажи, что не знаешь, не выдумывай."},
        {"role": "user", "content": question},
    ],
    "temperature": 0,
    "max_tokens": 800,
}
data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

try:
    r = requests.post(url, headers=headers, data=data, timeout=60)
except requests.RequestException as e:
    sys.exit(f"Ошибка сети: {e}")

if r.status_code != 200:
    sys.exit(f"HTTP {r.status_code}: {r.text[:500]}")

answer = r.json()["choices"][0]["message"]["content"]
print(answer)
