# -*- coding: utf-8 -*-
"""Разовый тестовый зонд Yandex Search API для Шага 2.

Запрос читается из внешнего UTF-8 файла (probe_query.txt), чтобы обойти
проблему кодировки кириллицы в cmd/исходнике Python на Windows.
"""
import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")
KEY = os.environ["YANDEX_API_KEY"].strip()

# Читаем запрос из файла — гарантированный UTF-8, независимо от кодировки консоли
query = (Path(__file__).parent / "probe_query.txt").read_text(encoding="utf-8").strip()

url = "https://searchapi.api.cloud.yandex.net/v2/web/search"
headers = {"Authorization": "Api-Key " + KEY, "Content-Type": "application/json"}

# Значения enum SearchType получены через DeepSeek (гибридный поиск).
# RU — российский поиск.
payload = {"query": {"search_type": "SEARCH_TYPE_RU", "query_text": query}}
data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
print("QUERY:", query)
r = requests.post(url, headers=headers, data=data, timeout=30)
print("STATUS", r.status_code)
print(r.text[:2500])
