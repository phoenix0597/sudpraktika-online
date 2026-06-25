# -*- coding: utf-8 -*-
"""Извлечение чистого текста судебного акта из HTML sudact.ru.

Для Фазы 1.1 (доказательство ядра). Берёт полный HTML страницы акта,
выделяет тело (от «Именем Российской Федерации» до конца резолютивной части),
очищает от навигации/рекламы/скриптов.

Использование:
  py scripts/extract_act_text.py --url https://sudact.ru/regular/doc/yQ8qgPoesvWJ/ --output output/act_2-80_2025.txt
"""
import argparse
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def fetch_html(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    r = requests.get(url, headers=headers, timeout=20)
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Извлечение текста акта из sudact.ru")
    ap.add_argument("--url", required=True, help="URL акта на sudact.ru")
    ap.add_argument("--output", required=True,
                    help="Выходной .txt файл (обычно data/raw_acts/act_<номер>.txt)")
    args = ap.parse_args()

    print(f"Загрузка: {args.url}")
    html = fetch_html(args.url)
    print(f"HTML получен: {len(html)} символов")

    text = extract_act_text(html)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    print(f"Чистый текст: {len(text)} символов → {out}")
    # Превью: начало и конец
    print("\n--- НАЧАЛО (первые 400 символов) ---")
    print(text[:400])
    print("\n--- КОНЕЦ (последние 400 символов) ---")
    print(text[-400:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
