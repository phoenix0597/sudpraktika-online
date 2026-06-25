# -*- coding: utf-8 -*-
"""Зонд гибридного поиска фактов через DeepSeek API.

Цель: проверить, знает ли DeepSeek значение enum SearchType для Yandex Search API,
чтобы снять блокер Шага 2 без расхода MCP-квоты. Если паттерн работает —
формализуем как навык.

Паттерн: оффлайн-знание (DeepSeek) → прицельный HTTP → MCP только в крайнем случае.
"""
import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")
KEY = os.environ["DEEPSEEK_API_KEY"].strip()

# Вопрос читаем из файла — гарантированный UTF-8 (обход кодировки cmd)
question = (
    "Для Yandex Search API (searchapi.api.cloud.yandex.net) метод web/search "
    "требует поле query.search_type типа enum SearchType. "
    "Какие существуют валидные значения этого enum? "
    "Перечисли все возможные значения строки enum. Ответ кратко."
)

url = "https://api.deepseek.com/chat/completions"
headers = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
payload = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": question}],
    "temperature": 0,
    "max_tokens": 400,
}
data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

r = requests.post(url, headers=headers, data=data, timeout=60)
print("STATUS", r.status_code)
if r.status_code == 200:
    answer = r.json()["choices"][0]["message"]["content"]
    print(answer)
else:
    print(r.text[:800])
