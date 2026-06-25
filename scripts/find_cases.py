# -*- coding: utf-8 -*-
"""Поиск и извлечение судебных дел через Yandex Search API (Шаг 2, Фаза 0).

Цель: доказать, что можно находить релевантные судебные акты по теме
(маркетплейсы/ЗоПП) программно и получать их URL/реквизиты.

Пайплайн:
  1. Yandex Search API → XML в base64 → список {url, title, domain, passage}.
  2. Фильтр по доменам судебных источников (sudrf.ru, sudact.ru, rospravosudie).
  3. Сохранение в CSV для последующего получения полных текстов.

Не расходует MCP-квоту: обычный HTTP через requests + Yandex API key.

Использование:
  py scripts/find_cases.py --query "возврат товара озон" --output output/cases_ozon.csv
"""
import argparse
import base64
import csv
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
KEY = os.environ["YANDEX_API_KEY"].strip()

SEARCH_URL = "https://searchapi.api.cloud.yandex.net/v2/web/search"
# Домены, где лежат судебные акты. sudrf.ru — первичный официальный источник.
COURT_DOMAINS = ("sudrf.ru", "sudact.ru", "rospravosudie", "sudrf.ru")
JUNK_DOMAINS = ("yandex.ru", "vk.com", "youtube", "instagram", "facebook", "9111",
                "consultant.ru", "garant.ru", "zakonrf")


def search(query: str, page: int = 0) -> list[dict]:
    """Вызов Yandex Search API. Возвращает список {url,title,domain,passage}."""
    headers = {"Authorization": "Api-Key " + KEY, "Content-Type": "application/json"}
    payload = {"query": {"search_type": "SEARCH_TYPE_RU", "query_text": query,
                         "page": page}}
    data = __import__("json").dumps(payload, ensure_ascii=False).encode("utf-8")
    r = requests.post(SEARCH_URL, headers=headers, data=data, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    raw = r.json().get("rawData", "")
    if not raw:
        return []
    xml_text = base64.b64decode(raw).decode("utf-8", errors="replace")
    return parse_xml(xml_text)


def parse_xml(xml_text: str) -> list[dict]:
    """Парсит XML выдачи Yandex в список документов."""
    results = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"XML parse error: {e}", file=sys.stderr)
        return results
    # Документы внутри <grouping><group><doc> или <results><grouping>...
    for doc in root.iter("doc"):
        url_el = doc.find("url")
        if url_el is None:
            continue
        url = (url_el.text or "").strip()
        domain_el = doc.find("domain")
        domain = (domain_el.text or "").strip() if domain_el is not None else ""
        title_el = doc.find("title")
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""
        passages = ["".join(p.itertext()).strip()
                    for p in doc.iter("passage")]
        results.append({
            "url": url, "domain": domain,
            "title": title, "passage": " | ".join(passages[:2]),
        })
    return results


def is_court_source(url: str, domain: str) -> bool:
    d = (domain or "").lower()
    u = (url or "").lower()
    if any(j in d for j in JUNK_DOMAINS):
        return False
    return any(c in d or c in u for c in COURT_DOMAINS)


def main() -> int:
    ap = argparse.ArgumentParser(description="Поиск судебных дел через Yandex Search API")
    ap.add_argument("--query", default="", help="Поисковый запрос (строка)")
    ap.add_argument("--query-file", default="", help="Файл с запросом (UTF-8, для кириллицы)")
    ap.add_argument("--output", required=True, help="Выходной CSV")
    ap.add_argument("--pages", type=int, default=1, help="Число страниц выдачи")
    args = ap.parse_args()

    query = args.query
    if args.query_file:
        query = Path(args.query_file).read_text(encoding="utf-8").strip()
    if not query:
        sys.exit("Нужен --query или --query-file")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    all_results = []
    for page in range(args.pages):
        try:
            hits = search(query, page=page)
        except RuntimeError as e:
            print(f"Страница {page}: {e}")
            break
        print(f"Страница {page}: найдено {len(hits)} документов всего")
        all_results.extend(hits)

    court_hits = [h for h in all_results if is_court_source(h["url"], h["domain"])]
    print(f"Из них от судебных источников: {len(court_hits)}")
    print(f"Прочие (не-суд): {len(all_results) - len(court_hits)}")

    fields = ["url", "domain", "title", "passage"]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for h in court_hits:
            w.writerow(h)

    print(f"\nСохранено {len(court_hits)} судебных дел: {out_path}")
    for h in court_hits[:10]:
        print(f"  [{h['domain']}] {h['title'][:70]}")
        print(f"    {h['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
