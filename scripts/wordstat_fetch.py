"""Сбор данных Wordstat API (Yandex Cloud) для валидации поискового спроса.

Фаза 0, Шаг 1. На входе — список фраз (CSV/TXT), на выходе — CSV с:
  - топом запросов (объём спроса + родственные фразы),
  - динамикой частоты по месяцам (тренд: растёт ли боль),
  - распределением по регионам (география).

Переиспользуемая инфраструктура: тот же скрипт работает на Фазе 5 (семантическое ядро).

Лимит-менеджмент (Wordstat API: ~1000 запросов/сутки):
  - суточный счётчик в .wordstat_counter.json (дата + расход),
  - буфер безопасности WORDSTAT_DAILY_BUDGET (по умолчанию 950),
  - возобновляемость: результаты дописываются в CSV по ходу, недоделанные
    фразы остаются в очереди на следующий прогон.

Безопасность: токен берётся только из переменной окружения YANDEX_API_KEY
(или .env), никогда не пишется в код/логи/память проекта.

Использование:
  py scripts/wordstat_fetch.py --input scripts/clusters_step1.txt --output output/wordstat_step1.csv
"""

from __future__ import annotations

import argparse
import csv
import calendar
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    # python-dotenv опционален: ключ можно задать системной переменной окружения
    pass

import requests

# --- Константы эндпоинта (формат подтверждён тестовым вызовом 2026-06-24) ---
BASE = "https://searchapi.api.cloud.yandex.net/v2/wordstat"
TOP_URL = f"{BASE}/topRequests"
DYNAMICS_URL = f"{BASE}/dynamics"
REGIONS_URL = f"{BASE}/regions"
# Dynamics: period enum = PERIOD_MONTHLY/PERIOD_WEEKLY/PERIOD_DAILY.
# Даты RFC3339; MONTHLY требует from=1-е число, to=последний день месяца;
# WEEKLY — from=понедельник; DAILY — окно ≤60 дней.

COUNTER_PATH = Path(__file__).parent / ".wordstat_counter.json"
# Число вызовов на одну фразу: Top + Dynamics + Regions
CALLS_PER_PHRASE = 3
RATE_DELAY = 0.5  # пауза между вызовами, сек — бережём лимит rps


def load_env() -> tuple[str, str, int]:
    """Возвращает (api_key, folder_id, daily_budget). Ключ — только из окружения."""
    key = os.environ.get("YANDEX_API_KEY", "").strip()
    if not key:
        sys.exit("ОШИБКА: YANDEX_API_KEY не задан. "
                 "Установите переменную окружения или заполните scripts/.env")
    folder_id = os.environ.get("YANDEX_FOLDER_ID", "").strip()
    try:
        budget = int(os.environ.get("WORDSTAT_DAILY_BUDGET", "950"))
    except ValueError:
        budget = 950
    return key, folder_id, budget


def read_counter(budget: int) -> int:
    """Читает расход за сегодня; возвращает остаток лимита."""
    today = date.today().isoformat()
    if not COUNTER_PATH.exists():
        return budget
    try:
        data = json.loads(COUNTER_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return budget
    if data.get("date") != today:
        # Новый день — счётчик сбрасывается
        return budget
    return budget - int(data.get("spent", 0))


def write_counter(spent: int) -> None:
    COUNTER_PATH.write_text(
        json.dumps({"date": date.today().isoformat(), "spent": spent},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_phrases(input_path: Path) -> list[str]:
    """Читает фразы по одной на строку; пропускает пустые и комментарии."""
    phrases = []
    for raw in input_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            phrases.append(line)
    return phrases


def done_phrases(output_path: Path) -> set[str]:
    """Возвращает множество фраз, уже обработанных в выводе (возобновляемость)."""
    if not output_path.exists():
        return set()
    done = set()
    with output_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("phrase"):
                done.add(row["phrase"])
    return done


def api_call(url: str, key: str, payload: dict, folder_id: str = "") -> dict:
    """POST к Wordstat API с обработкой типичных ошибок и паузой."""
    if folder_id:
        payload = {**payload, "folderId": folder_id}
    headers = {"Authorization": f"Api-Key {key}",
               "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload)
    time.sleep(RATE_DELAY)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code} на {url}: {resp.text[:300]}")
    return resp.json()


def _month_range(months_back: int = 17) -> tuple[str, str]:
    """Возвращает (from, to) для PERIOD_MONTHLY: from=1-е число N мес назад,
    to=последний день предыдущего месяца. По правилам Yandex Wordstat Dynamics.
    """
    today = date.today()
    # to = последний день прошлого месяца
    if today.month == 1:
        to_last = date(today.year - 1, 12, 31)
    else:
        to_last = date(today.year, today.month, 1) - timedelta(days=1)
    # from = 1-е число, на months_back месяцев раньше to_last
    ym = to_last.year * 12 + (to_last.month - 1) - months_back
    fy, fm = divmod(ym, 12)
    from_first = date(fy, fm + 1, 1)
    return from_first.isoformat() + "T00:00:00Z", to_last.isoformat() + "T00:00:00Z"


def _trend_from_dynamics(series: list[dict]) -> str:
    """Первый vs последний месяц → строка тренда '37763→43162 (+14%)'."""
    if len(series) < 2:
        return ""
    first = int(series[0].get("count") or 0)
    last = int(series[-1].get("count") or 0)
    if not first:
        return f"{first}→{last}"
    pct = (last - first) / first * 100
    return f"{first}→{last} ({pct:+.0f}%)"


def fetch_phrase(phrase: str, key: str, folder_id: str = "") -> dict:
    """Три вызова Wordstat для одной фразы. Возвращает агрегированную запись.

    Форматы ответов подтверждены живыми вызовами 2026-06-24:
      - GetTop: {results:[{phrase,count}], associations:[...], totalCount}
      - GetRegionsDistribution: {results:[{region,count,share}]}  (region = код)
      - GetDynamics: {results:[{date,count,share}]} (PERIOD_MONTHLY, месяцы)
    """
    common = {"phrase": phrase}
    record = {
        "phrase": phrase,
        "total_shows": "",      # totalCount из GetTop — суммарный объём спроса
        "top_phrases": "",      # топ релевантных запросов с частотами
        "top_shows": "",        # частота точной фразы
        "dynamics_trend": "",   # тренд: первый vs последний месяц, %
        "regions_top": "",      # топ-5 регионов по числу запросов (код:кол-во)
    }

    # 1. Топ запросов: объём спроса + родственные фразы
    top = api_call(TOP_URL, key, {**common, "num_phrases": 30,
                                  "devices": ["DEVICE_ALL"]}, folder_id)
    results = top.get("results") or []
    record["total_shows"] = top.get("totalCount", "")
    if results:
        exact = next((r for r in results if r.get("phrase") == phrase), results[0])
        record["top_shows"] = exact.get("count", "")
        record["top_phrases"] = " | ".join(
            f"{r.get('phrase', '?')}:{r.get('count', 0)}" for r in results[:15]
        )

    # 2. Динамика: тренд за последние ~18 месяцев
    from_d, to_d = _month_range(months_back=17)
    dyn = api_call(DYNAMICS_URL, key, {**common, "period": "PERIOD_MONTHLY",
                                       "from_date": from_d, "to_date": to_d},
                   folder_id)
    record["dynamics_trend"] = _trend_from_dynamics(dyn.get("results") or [])

    # 3. Распределение по регионам: топ-5 по числу запросов
    regs = api_call(REGIONS_URL, key, common, folder_id)
    reg_items = regs.get("results") or []
    if reg_items:
        reg_sorted = sorted(
            reg_items,
            key=lambda r: int(r.get("count") or 0),
            reverse=True,
        )[:5]
        record["regions_top"] = " | ".join(
            f"{r.get('region', '?')}:{r.get('count', 0)}"
            for r in reg_sorted
        )
    return record


def fetch_top_only(phrase: str, key: str, folder_id: str = "") -> dict:
    """Только GetTop (1 запрос) — режим breadth для максимального покрытия тем.

    Для рыночного замера: охватить максимум фраз в рамках лимита, потому что
    каждая seed-фраза через GetTop раскрывает весь кластер родственных запросов.
    """
    record = {
        "phrase": phrase,
        "total_shows": "",
        "top_shows": "",
        "top_phrases": "",
        "regions_top": "",
    }
    top = api_call(TOP_URL, key, {"phrase": phrase, "num_phrases": 40,
                                  "devices": ["DEVICE_ALL"]}, folder_id)
    results = top.get("results") or []
    record["total_shows"] = top.get("totalCount", "")
    if results:
        exact = next((r for r in results if r.get("phrase") == phrase), results[0])
        record["top_shows"] = exact.get("count", "")
        record["top_phrases"] = " | ".join(
            f"{r.get('phrase', '?')}:{r.get('count', 0)}" for r in results[:20]
        )
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description="Сбор данных Wordstat API")
    ap.add_argument("--input", required=True, help="CSV/TTXT: фразы по одной на строку")
    ap.add_argument("--output", required=True, help="Выходной CSV")
    ap.add_argument("--breadth", action="store_true",
                    help="Режим breadth: только GetTop (1 запрос/фраза) для "
                         "максимального покрытия тем вместо глубины")
    args = ap.parse_args()

    key, folder_id, budget = load_env()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    phrases = read_phrases(input_path)
    done = done_phrases(output_path)
    todo = [p for p in phrases if p not in done]

    calls_each = 1 if args.breadth else CALLS_PER_PHRASE
    needed = len(todo) * calls_each
    remaining = read_counter(budget)
    print(f"Режим: {'breadth (только GetTop)' if args.breadth else 'полный (Top+Regions)'}")
    print(f"Фраз всего: {len(phrases)} | уже готово: {len(done)} | "
          f"к сбору: {len(todo)} | запросов нужно: {needed}")
    print(f"Лимит сегодня: остаток {remaining} (бюджет {budget})")

    if needed > remaining:
        sys.exit(f"НЕДОСТАТОЧНО ЛИМИТА: нужно {needed}, осталось {remaining}. "
                 f"Доработайте завтра или повысьте WORDSTAT_DAILY_BUDGET.")

    spent_today = budget - remaining
    fields = ["phrase", "total_shows", "top_shows", "top_phrases", "dynamics_trend", "regions_top"]
    write_header = not output_path.exists()

    with output_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            writer.writeheader()
        for i, phrase in enumerate(todo, 1):
            try:
                record = (fetch_top_only(phrase, key, folder_id) if args.breadth
                          else fetch_phrase(phrase, key, folder_id))
            except RuntimeError as e:
                print(f"  [{i}/{len(todo)}] ОШИБКА '{phrase}': {e}")
                break  # сохраняем то, что уже собрано; продолжим завтра
            writer.writerow(record)
            f.flush()
            spent_today += calls_each
            write_counter(spent_today)
            print(f"  [{i}/{len(todo)}] {phrase}: "
                  f"total={record['total_shows']}, "
                  f"exact={record['top_shows']}")

    print(f"Готово. Результат: {output_path} | потрачено сегодня: {spent_today}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
