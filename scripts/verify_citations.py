# -*- coding: utf-8 -*-
"""Верификация извлечённых ссылок против исходного текста акта (анти-галлюцинация).

После извлечения структуры/анализа акта LLM — проверяет, что каждая правовая
ссылка (статья, постановление, номер дела) буквально присутствует в тексте акта.
Помечает отсутствующие как подозрительные (вероятная галлюцинация).

Принцип верифицируемости: LLM извлекает только то, что есть в тексте. Что не
нашлось в тексте — флаг на ручную проверку или отбраковку.

Использование:
  py scripts/verify_citations.py --act data/raw_acts/act_yQ8qgPoesvWJ.txt --analysis output/test_practice_ds.md
"""
import argparse
import re
from pathlib import Path


# Шаблоны правовых ссылок для извлечения из анализа
CITATION_PATTERNS = [
    # Статьи законов: "ст. 18 ЗоЗПП", "статья 1005 ГК РФ", "п. 2.1 ст. 12"
    re.compile(r"(?:ст\.|статья)\s*\d+(?:[\.\s]\d+)*(?:\s*[А-Яа-яЁё\s]{0,20}?(?:ЗоЗПП|ГК\s*РФ|Закона|УПК|ГПК|АПК|КоАП))?", re.IGNORECASE),
    # Постановления пленумов: "Постановление Пленума ВС РФ № 17", "Пленум ВС № 17"
    re.compile(r"(?:Постановление\s*)?Пленум[а-я]*\s*(?:ВС|Верховного\s*Суда)?\s*(?:РФ)?\s*№?\s*\d+", re.IGNORECASE),
    # Номера дел: "№ 2-664/2022", "дело № А40-156308/2024", "№ 2-80/2025"
    re.compile(r"(?:дело\s*)?№\s*[А-ЯA-Z]*\d+[\-/]\d+(/\d+)?", re.IGNORECASE),
    # Федеральные законы: "Федеральный закон № 250-ФЗ", "№ 262-ФЗ"
    re.compile(r"(?:Федеральный\s*закон\s*)?№\s*\d+-ФЗ", re.IGNORECASE),
]


def extract_citations(text: str) -> list[str]:
    """Извлекает все правовые ссылки из текста анализа."""
    found = set()
    for pat in CITATION_PATTERNS:
        for m in pat.finditer(text):
            found.add(m.group(0).strip())
    return sorted(found)


def normalize(s: str) -> str:
    """Нормализация для сравнения: нижний регистр, схлопывание пробелов."""
    return re.sub(r"\s+", " ", s.lower().strip())


def verify(act_text: str, citations: list[str]) -> dict:
    """Проверяет наличие каждой ссылки в тексте акта. Возвращает {citation: found}."""
    norm_act = normalize(act_text)
    result = {}
    for cit in citations:
        nc = normalize(cit)
        # Точное совпадение нормализованной строки
        found = nc in norm_act
        # Доп. проверка: ключевая часть (номер статьи/дела) присутствует
        if not found:
            # Извлекаем «ядро» ссылки — номер
            core = re.search(r"\d+(?:[\.\-]\d+)*(/\d+)?", cit)
            if core and core.group(0) in norm_act:
                # Номер есть, но контекст другой — частичное совпадение
                found = "partial"
        result[cit] = found
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Верификация ссылок против текста акта")
    ap.add_argument("--act", required=True, help="Текст акта (UTF-8)")
    ap.add_argument("--analysis", required=True, help="Анализ LLM для проверки")
    args = ap.parse_args()

    act_text = Path(args.act).read_text(encoding="utf-8")
    analysis = Path(args.analysis).read_text(encoding="utf-8")

    citations = extract_citations(analysis)
    print(f"Извлечено ссылок из анализа: {len(citations)}")

    if not citations:
        print("Ссылок не найдено — нечего проверять.")
        return 0

    result = verify(act_text, citations)
    ok = sum(1 for v in result.values() if v is True)
    partial = sum(1 for v in result.values() if v == "partial")
    bad = sum(1 for v in result.values() if v is False)

    print(f"\n✅ Подтверждены текстом акта: {ok}")
    print(f"⚠️  Частичное совпадение (только номер): {partial}")
    print(f"❌ НЕ найдены в акте (подозрение на галлюцинацию): {bad}")

    if bad:
        print("\n--- ПОДОЗРИТЕЛЬНЫЕ ССЫЛКИ ---")
        for cit, v in result.items():
            if v is False:
                print(f"  ❌ {cit}")
    if partial:
        print("\n--- ЧАСТИЧНЫЕ СОВПАДЕНИЯ (проверить вручную) ---")
        for cit, v in result.items():
            if v == "partial":
                print(f"  ⚠️  {cit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
