# -*- coding: utf-8 -*-
"""Извлечение чистого текста судебного акта из HTML sudact.ru.

Для Фазы 1.1 (доказательство ядра). Берёт полный HTML страницы акта,
выделяет тело (от «Именем Российской Федерации» до конца резолютивной части),
очищает от навигации/рекламы/скриптов.

Использование:
  py scripts/extract_act_text.py --url https://sudact.ru/regular/doc/yQ8qgPoesvWJ/ --output output/act_2-80_2025.txt
"""
import argparse
import csv
import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_DELAY = 1.0
MAX_RETRIES = 3


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Connection": "close",
    }
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.get(url, headers=headers, timeout=20)
        except requests.RequestException:
            if attempt < MAX_RETRIES:
                wait_s = min(30, 2 ** attempt)
                print(f"Сетевая ошибка: повтор через {wait_s} сек. ({url})", file=sys.stderr)
                time.sleep(wait_s)
                continue
            raise
        if r.status_code == 429 and attempt < MAX_RETRIES:
            raw_retry_after = r.headers.get("Retry-After", "")
            try:
                wait_s = max(1, int(raw_retry_after))
            except ValueError:
                wait_s = 60 * (attempt + 1)
            print(f"429 rate limit: повтор через {wait_s} сек. ({url})", file=sys.stderr)
            time.sleep(wait_s)
            continue
        if r.status_code >= 500 and attempt < MAX_RETRIES:
            wait_s = min(30, 2 ** attempt)
            print(f"HTTP {r.status_code}: повтор через {wait_s} сек. ({url})", file=sys.stderr)
            time.sleep(wait_s)
            continue
        break
    r.raise_for_status()
    return r.text


def extract_act_text(html: str) -> str:
    """Выделяет чистый текст судебного акта из HTML sudact.ru."""
    soup = BeautifulSoup(html, "html.parser")

    # Удаляем шум: скрипты, стили, навигацию
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Нормализуем переносы и пробелы
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    # Тело судебного акта начинается с «Именем Российской Федерации».
    # Всё до этого — заголовки/меню sudact.ru.
    start_markers = ["Именем Российской Федерации", "ИМЕНЕМ РОССИЙСКОЙ ФЕДЕРАЦИИ"]
    start_idx = -1
    for m in start_markers:
        idx = text.find(m)
        if idx > 0:
            start_idx = idx
            break

    if start_idx > 0:
        text = text[start_idx:]

    # Резолютивная часть заканчивается подписью судьи / реквизитами дела.
    # Обрезаем хвост после типичных конечных маркеров (если найдены).
    end_markers = [
        "\nКопия верна", "\nПравильность заверения",
        "\nРешение не вступило", "\nРешение вступило",
    ]
    for m in end_markers:
        idx = text.find(m)
        if idx > 0:
            text = text[:idx]
            break

    return text.strip()


def docid_from_url(url: str) -> str:
    """sudact.ru/regular/doc/<docid>/ -> <docid>."""
    path = urlparse(url).path
    match = re.search(r"/regular/doc/([^/]+)/?", path)
    if not match:
        raise ValueError(f"Не удалось извлечь docid из URL: {url}")
    return match.group(1)


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def meta_path_for(output: Path) -> Path:
    return output.with_suffix(".meta.json")


def write_source_metadata(url: str, output: Path, text: str,
                          source_row: dict | None = None) -> None:
    """Пишет технические метаданные источника рядом с сырым актом.

    Это детерминированная часть JSON-контракта: ссылка, домен, путь и хэш текста
    не должны извлекаться LLM из памяти или догадок.
    """
    source_row = source_row or {}
    docid = docid_from_url(url)
    parsed = urlparse(url)
    metadata = {
        "docid": docid,
        "source_url": url,
        "source_domain": (source_row.get("domain") or parsed.netloc).strip(),
        "source_title": (source_row.get("title") or "").strip() or None,
        "source_passage": (source_row.get("passage") or "").strip() or None,
        "raw_act_path": output.as_posix(),
        "raw_text_sha256": text_sha256(text),
        "source_type": "court_act",
        "fetched_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    meta_path_for(output).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def extract_to_file(url: str, output: Path, source_row: dict | None = None) -> int:
    print(f"Загрузка: {url}")
    html = fetch_html(url)
    text = extract_act_text(html)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    write_source_metadata(url, output, text, source_row)
    print(f"Чистый текст: {len(text)} символов -> {output}")
    if len(text) < 1000:
        print(f"ПРЕДУПРЕЖДЕНИЕ: короткий текст ({len(text)} символов), проверь извлечение: {url}",
              file=sys.stderr)
    return len(text)


def read_rows_from_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f)
        result = []
        seen = set()
        for row in rows:
            url = (row.get("url") or "").strip()
            key = url.rstrip("/")
            if not url or key in seen:
                continue
            seen.add(key)
            result.append(row)
        return result


def extract_batch(csv_path: Path, output_dir: Path, limit: int, delay: float,
                  skip_existing: bool) -> int:
    rows = read_rows_from_csv(csv_path)
    processed = 0
    failed = 0
    skipped = 0
    for row in rows:
        url = (row.get("url") or "").strip()
        if limit and processed >= limit:
            break
        try:
            docid = docid_from_url(url)
        except ValueError as e:
            failed += 1
            print(str(e), file=sys.stderr)
            continue
        output = output_dir / f"act_{docid}.txt"
        if skip_existing and output.exists():
            meta_path = meta_path_for(output)
            if not meta_path.exists():
                existing_text = output.read_text(encoding="utf-8")
                write_source_metadata(url, output, existing_text, row)
            skipped += 1
            continue
        if processed > 0 and delay > 0:
            time.sleep(delay)
        try:
            extract_to_file(url, output, row)
            processed += 1
        except requests.RequestException as e:
            failed += 1
            print(f"ОШИБКА загрузки {url}: {e}", file=sys.stderr)
    print(f"\nИтого: скачано {processed}, пропущено существующих {skipped}, ошибок {failed}")
    return processed


def main() -> int:
    ap = argparse.ArgumentParser(description="Извлечение текста акта из sudact.ru")
    ap.add_argument("--url", default="", help="URL акта на sudact.ru")
    ap.add_argument("--output", default="",
                    help="Выходной .txt файл (обычно data/raw_acts/act_<номер>.txt)")
    ap.add_argument("--csv", default="", help="CSV с колонкой url для batch-извлечения")
    ap.add_argument("--output-dir", default="data/raw_acts",
                    help="Каталог для batch-вывода act_<docid>.txt")
    ap.add_argument("--limit", type=int, default=0,
                    help="Максимум новых актов для batch-извлечения; 0 = без лимита")
    ap.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                    help="Пауза между загрузками в batch-режиме, сек.")
    ap.add_argument("--no-skip-existing", action="store_true",
                    help="Не пропускать уже существующие act_<docid>.txt")
    args = ap.parse_args()

    if args.csv:
        extract_batch(
            csv_path=Path(args.csv),
            output_dir=Path(args.output_dir),
            limit=args.limit,
            delay=args.delay,
            skip_existing=not args.no_skip_existing,
        )
        return 0

    if not args.url or not args.output:
        sys.exit("Нужны либо --csv, либо пара --url и --output")

    out = Path(args.output)
    extract_to_file(args.url, out)
    text = out.read_text(encoding="utf-8")
    # Превью: начало и конец
    print("\n--- НАЧАЛО (первые 400 символов) ---")
    print(text[:400])
    print("\n--- КОНЕЦ (последние 400 символов) ---")
    print(text[-400:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
