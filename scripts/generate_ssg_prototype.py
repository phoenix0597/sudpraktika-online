# -*- coding: utf-8 -*-
"""Генератор первого статического прототипа страниц-ситуаций.

Читает:
- data/review/phase1-4-case-clusters.csv
- data/structured/structure_<docid>.json
- data/reference/zpp_enum_dictionary.json

Пишет:
- site_prototype/index.html
- site_prototype/assets/prototype.css
- site_prototype/praktika/<slug>/index.html
- site_prototype/dela/<docid>/index.html

Это не финальный фронтенд, а проверочный SSG-прототип: он нужен, чтобы быстро
посмотреть структуру страниц, карточки дел, сводки и фильтры на реальных данных.
"""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(".")
CLUSTERS_CSV = ROOT / "data/review/phase1-4-case-clusters.csv"
STRUCTURED_DIR = ROOT / "data/structured"
ENUM_DICT = ROOT / "data/reference/zpp_enum_dictionary.json"
OUT_DIR = ROOT / "site_prototype"
SITE_BRAND = "Дела о защите прав потребителей"
PROTOTYPE_DISCLAIMER = (
    "Прототип. Не является юридической консультацией. Материалы основаны на судебных актах "
    "и обработаны алгоритмом для систематизации и обобщения текущей судебной практики судов разных инстанций."
)


@dataclass(frozen=True)
class SituationPage:
    code: str
    slug: str
    h1: str
    short_problem: str
    page_type: str

    @property
    def route(self) -> str:
        return f"/praktika/{self.slug}/"

    @property
    def output_path(self) -> Path:
        return OUT_DIR / "praktika" / self.slug / "index.html"


PAGES: list[SituationPage] = [
    SituationPage(
        "goods_defect_art18",
        "nekachestvennyy-tovar",
        "Некачественный товар: как вернуть деньги, взыскать неустойку и штраф",
        "Потребитель купил товар, но он сломался, оказался с недостатком или продавец отказался исполнять гарантийные обязанности.",
        "pillar",
    ),
    SituationPage(
        "distance_sale_return_art26_1",
        "vozvrat-tovara-online",
        "Как вернуть товар, купленный онлайн",
        "Покупка была дистанционной: через сайт, маркетплейс или интернет-магазин, а потребитель хочет отказаться от товара и вернуть деньги.",
        "landing",
    ),
    SituationPage(
        "info_violation_art10_12",
        "nedostovernaya-informatsiya",
        "Неверная цена, продавец или информация о товаре: что решил суд",
        "Покупателю дали неполную или недостоверную информацию о цене, продавце, свойствах товара или условиях покупки.",
        "landing",
    ),
    SituationPage(
        "service_refusal_art32",
        "vozvrat-deneg-za-uslugu",
        "Как отказаться от услуги и вернуть деньги",
        "Потребитель хочет отказаться от услуги, курса, страховки, сертификата или сервиса и вернуть оплату.",
        "landing",
    ),
    SituationPage(
        "prepaid_goods_delay_art23_1",
        "oplatili-tovar-ne-peredali",
        "Оплатили товар, но его не передали: что можно взыскать",
        "Заказ был оплачен заранее, но продавец задержал передачу, отменил заказ или не вернул предоплату.",
        "landing",
    ),
]


RESULT_LABELS = {
    "satisfied": "удовлетворено",
    "partially_satisfied": "частично удовлетворено",
    "rejected": "отказано",
    "mixed": "смешанный результат",
    "hold": "не публиковать",
}


RELATED = {
    "goods_defect_art18": ["distance_sale_return_art26_1", "info_violation_art10_12"],
    "distance_sale_return_art26_1": ["goods_defect_art18", "info_violation_art10_12", "prepaid_goods_delay_art23_1"],
    "info_violation_art10_12": ["distance_sale_return_art26_1", "service_refusal_art32", "goods_defect_art18"],
    "service_refusal_art32": ["info_violation_art10_12"],
    "prepaid_goods_delay_art23_1": ["distance_sale_return_art26_1", "goods_defect_art18"],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_enum_labels() -> dict[str, dict[str, str]]:
    data = read_json(ENUM_DICT)
    fields = data.get("fields", {})
    result: dict[str, dict[str, str]] = {
        "claim_type_codes": {},
        "dispute_type_code": {},
        "result_type": RESULT_LABELS.copy(),
    }

    claim_values = fields.get("taxonomy.claim_type_codes", {}).get("values", {})
    for code, meta in claim_values.items():
        result["claim_type_codes"][code] = meta.get("label", code) if isinstance(meta, dict) else str(meta)

    dispute_values = fields.get("taxonomy.dispute_type_code", {}).get("values", {})
    for code, meta in dispute_values.items():
        result["dispute_type_code"][code] = meta.get("label", code) if isinstance(meta, dict) else str(meta)

    result_values = fields.get("claims_and_result.outcome.result_type", {}).get("values", {})
    for code, label in result_values.items():
        result["result_type"][code] = str(label)

    return result


def parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.min
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.min


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def number(value: Any) -> float | None:
    if value in (None, "", [], {}):
        return None
    if isinstance(value, (int, float)):
        if math.isnan(value):
            return None
        return float(value)
    text = str(value).replace("\xa0", "").replace(" ", "").replace(",", ".")
    text = re.sub(r"[^\d.\-]", "", text)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def money(value: Any) -> str:
    n = number(value)
    if n is None:
        return "не указано"
    if abs(n) >= 1000:
        s = f"{n:,.0f}".replace(",", " ")
    else:
        s = f"{n:.2f}".rstrip("0").rstrip(".")
    return f"{s} ₽"


def court_acts_label(count: int) -> str:
    last_two = count % 100
    last = count % 10
    if 11 <= last_two <= 14:
        word = "судебных актов"
    elif last == 1:
        word = "судебный акт"
    elif 2 <= last <= 4:
        word = "судебных акта"
    else:
        word = "судебных актов"
    return f"{count} {word}"


def short(text: Any, limit: int = 320) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= limit:
        return value
    cut = value[: limit - 1].rstrip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"


def sentence_excerpt(text: Any, max_sentences: int = 2, limit: int = 220) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return ""
    protected = re.sub(
        r"\b(руб|мес|тыс|млн|млрд|г|ст|п|ч)\.",
        lambda match: f"{match.group(1)}§",
        value,
        flags=re.IGNORECASE,
    )
    sentences = [part.replace("§", ".") for part in re.split(r"(?<=[.!?…])\s+", protected)]
    excerpt = " ".join(sentences[:max_sentences]).strip()
    return short(excerpt or value, limit)


def uppercase_first_letter(text: Any) -> str:
    value = str(text or "").strip()
    for idx, char in enumerate(value):
        if char.isalpha():
            return value[:idx] + char.upper() + value[idx + 1 :]
    return value


def slug_attr(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def html_page(title: str, body: str, stylesheet_href: str) -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="{escape(stylesheet_href)}">
</head>
<body>
{body}
<script>
document.querySelectorAll('[data-filter]').forEach((select) => {{
  select.addEventListener('change', () => {{
    applyFilters();
  }});
}});
document.querySelectorAll('[data-quick-filter]').forEach((chip) => {{
  chip.addEventListener('click', () => {{
    const field = chip.dataset.quickFilter;
    const value = chip.dataset.quickValue || '';
    const select = document.querySelector(`[data-filter="${{field}}"]`);
    if (!select) return;
    select.value = value;
    applyFilters();
    document.querySelector('[data-case-list]')?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }});
}});
document.querySelectorAll('[data-reset-filters]').forEach((button) => {{
  button.addEventListener('click', () => {{
    document.querySelectorAll('[data-filter]').forEach((filter) => {{
      filter.value = '';
    }});
    applyFilters();
  }});
}});
function applyFilters() {{
    const cards = Array.from(document.querySelectorAll('[data-case-card]'));
    const filters = Array.from(document.querySelectorAll('[data-filter]'));
    cards.forEach((card) => {{
      const visible = filters.every((filter) => {{
        if (!filter.value) return true;
        const field = filter.dataset.filter;
        const value = (card.dataset[field] || '');
        return value.split('||').includes(filter.value);
      }});
      card.hidden = !visible;
    }});
}}
</script>
</body>
</html>
"""


def page_href(page: SituationPage, current_page: SituationPage | None = None) -> str:
    if current_page is None:
        return f"praktika/{page.slug}/index.html"
    if page.code == current_page.code:
        return "index.html"
    return f"../{page.slug}/index.html"


def page_link(page: SituationPage, label: str | None = None, current_page: SituationPage | None = None) -> str:
    return f'<a href="{escape(page_href(page, current_page))}">{escape(label or page.h1)}</a>'


def case_page_href(docid: str) -> str:
    return f"../../dela/{docid}/index.html"


def load_cases() -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    rows = read_csv(CLUSTERS_CSV)
    cases: list[dict[str, Any]] = []

    for row in rows:
        docid = row["docid"]
        data = read_json(STRUCTURED_DIR / f"structure_{docid}.json")
        publication = data.get("publication", {})
        if row.get("page_priority") == "hold":
            continue
        if publication.get("index_policy") == "hold" or not as_bool(publication.get("main_site_fit", True)):
            continue
        row["_json"] = data
        cases.append(row)

    by_cluster: dict[str, list[dict[str, Any]]] = {}
    for page in PAGES:
        page_cases = [row for row in cases if row["cluster_code"] == page.code]
        page_cases.sort(key=case_sort_key)
        by_cluster[page.code] = page_cases

    return cases, by_cluster


def case_sort_key(row: dict[str, Any]) -> tuple[int, int, int, str]:
    data = row["_json"]
    amounts = data.get("claims_and_result", {}).get("amounts", {})
    awarded = number(amounts.get("awarded_total"))
    date = parse_date(data.get("court", {}).get("decision_date") or row.get("decision_date"))
    has_named_object = 1 if row.get("object_type") and row.get("platform_or_company") else 0
    return (0 if awarded is not None else 1, -date.toordinal(), -has_named_object, row["docid"])


def counter_list(
    items: Counter[str],
    labels: dict[str, str],
    max_items: int = 8,
    filter_field: str | None = None,
) -> str:
    parts = []
    for code, count in items.most_common(max_items):
        if code in (None, ""):
            continue
        label = labels.get(code, code)
        if filter_field:
            parts.append(
                f'<button type="button" class="chip chip-button" data-quick-filter="{escape(filter_field)}" '
                f'data-quick-value="{escape(data_value(code))}">{escape(label)} <b>{count}</b></button>'
            )
        else:
            parts.append(f'<span class="chip">{escape(label)} <b>{count}</b></span>')
    return "\n".join(parts) if parts else '<span class="muted">Нет данных</span>'


def make_options(values: list[str], labels: dict[str, str] | None = None) -> str:
    labels = labels or {}
    options = ['<option value="">Все</option>']
    for value in sorted({v for v in values if v and v != "не указан"}):
        options.append(f'<option value="{escape(value)}">{escape(labels.get(value, value))}</option>')
    if any(v == "не указан" or not v for v in values):
        options.append('<option value="не указан">Не указано</option>')
    return "\n".join(options)


def data_value(value: Any) -> str:
    value = slug_attr(value)
    return value if value else "не указан"


def render_filters(cases: list[dict[str, Any]], labels: dict[str, dict[str, str]]) -> str:
    results = [data_value(row["result_type"]) for row in cases]
    companies = [data_value(row["platform_or_company"]) for row in cases]
    objects = [data_value(row["object_type"]) for row in cases]
    regions = [data_value(row["region"]) for row in cases]
    claim_codes: list[str] = []
    for row in cases:
        claim_codes.extend([c.strip() for c in row.get("claim_type_codes", "").split(";") if c.strip()])

    return f"""
<section class="panel filters">
  <h2>Фильтры по делам</h2>
  <div class="filter-grid">
    <label>Результат<select data-filter="result">{make_options(results, labels['result_type'])}</select></label>
    <label>Компания<select data-filter="company">{make_options(companies)}</select></label>
    <label>Объект<select data-filter="object">{make_options(objects)}</select></label>
    <label>Требование<select data-filter="claims">{make_options(claim_codes, labels['claim_type_codes'])}</select></label>
    <label>Регион<select data-filter="region">{make_options(regions)}</select></label>
  </div>
  <div class="filter-actions">
    <button type="button" class="button secondary" data-reset-filters>Сбросить фильтры</button>
  </div>
</section>
"""


def render_case_card(row: dict[str, Any], labels: dict[str, dict[str, str]]) -> str:
    data = row["_json"]
    source = data.get("source", {})
    court = data.get("court", {})
    taxonomy = data.get("taxonomy", {})
    summary = data.get("case_summary", {})
    claims = data.get("claims_and_result", {})
    outcome = claims.get("outcome", {})
    amounts = claims.get("amounts", {})

    docid = source.get("docid") or row["docid"]
    key_factors = summary.get("key_factors") or []
    if not isinstance(key_factors, list):
        key_factors = [str(key_factors)]
    claim_codes = taxonomy.get("claim_type_codes") or []
    claim_labels = [labels["claim_type_codes"].get(code, code) for code in claim_codes]
    result = outcome.get("result_type") or row.get("result_type")
    result_label = RESULT_LABELS.get(result, result)
    source_url = source.get("source_url") or "#"
    object_text = taxonomy.get("object_name") or taxonomy.get("object_type") or "объект не указан"
    company = taxonomy.get("platform_or_company") or "не указано"
    card_title = make_case_card_title(data)
    region = court.get("region")
    region_html = (
        f'<button type="button" class="meta-filter" data-quick-filter="region" '
        f'data-quick-value="{escape(data_value(region))}">{escape(str(region))}</button>'
        if region
        else '<span>регион не указан</span>'
    )

    factor_html = ""
    if key_factors:
        factor_html = "<ul>" + "".join(f"<li>{escape(short(f, 180))}</li>" for f in key_factors[:2]) + "</ul>"
    else:
        factor_html = '<p class="muted">Ключевые факторы не выделены.</p>'

    chips = " ".join(
        f'<button type="button" class="chip chip-button small" data-quick-filter="claims" '
        f'data-quick-value="{escape(data_value(code))}">{escape(label)}</button>'
        for code, label in zip(claim_codes[:6], claim_labels[:6])
        if code
    )
    data_claims = "||".join(claim_codes)

    return f"""
<article class="case-card"
  data-case-card
  data-result="{escape(data_value(result))}"
  data-company="{escape(data_value(company))}"
  data-object="{escape(data_value(taxonomy.get('object_type')))}"
  data-region="{escape(data_value(court.get('region')))}"
  data-claims="{escape(data_claims)}">
  <div class="case-card__header">
    <div>
      <h3>{escape(card_title)}</h3>
      <p class="meta">{region_html} <span>· {escape(court.get('decision_date') or 'дата не указана')} · дело {escape(court.get('case_number') or docid)}</span></p>
    </div>
    <button type="button" class="result result-{escape(str(result))}" data-quick-filter="result" data-quick-value="{escape(data_value(result))}">{escape(result_label)}</button>
  </div>
  <p>{escape(make_case_card_excerpt(data))}</p>
  <dl class="case-facts">
    <div><dt>Объект</dt><dd>{escape(object_text)}</dd></div>
    <div><dt>Компания</dt><dd>{escape(company)}</dd></div>
    <div><dt>Присуждено</dt><dd>{escape(money(amounts.get('awarded_total')))}</dd></div>
  </dl>
  <div class="chips">{chips}</div>
  <h4>Что повлияло на исход</h4>
  {factor_html}
  <div class="case-links">
    <a class="button case-primary-link" href="{escape(case_page_href(docid))}">Разобрать это дело →</a>
    <a class="source-link" href="{escape(source_url)}" target="_blank" rel="noopener">↗ Судебный акт</a>
  </div>
</article>
"""


def clean_markdown_text(text: str) -> str:
    value = re.sub(r"^#{1,6}\s+", "", text.strip())
    value = re.sub(r"^\*\*(.+)\*\*$", r"\1", value)
    value = re.sub(r"\*\*(.+?)\*\*", r"\1", value)
    return value.strip()


GENERIC_STORY_HEADINGS = {
    "кто участвовал",
    "обстоятельства и развитие событий",
    "что произошло",
    "что произошло (шаг за шагом)",
    "результат для потребителя",
    "итог суда",
    "что решил суд",
    "что сделано не так и как поступить правильно",
}


def first_markdown_line(markdown: str) -> tuple[int, str] | None:
    lines = markdown.splitlines()
    for idx, line in enumerate(lines):
        if line.strip():
            return idx, line
    return None


def is_story_title(line: str) -> bool:
    stripped = line.strip()
    cleaned = clean_markdown_text(stripped)
    if not cleaned or cleaned.lower() in GENERIC_STORY_HEADINGS:
        return False
    if stripped.startswith("###"):
        return False
    return len(cleaned) >= 24


def extract_story_title_and_body(markdown: str, fallback: str) -> tuple[str, str]:
    first = first_markdown_line(markdown)
    if not first:
        return fallback, ""
    idx, line = first
    lines = markdown.splitlines()
    if is_story_title(line):
        return clean_markdown_text(line), "\n".join(lines[idx + 1 :]).strip()
    return fallback, markdown.strip()


def make_case_title(data: dict[str, Any]) -> str:
    taxonomy = data.get("taxonomy", {})
    summary = data.get("case_summary", {})
    outcome = data.get("claims_and_result", {}).get("outcome", {})
    object_text = taxonomy.get("object_name") or taxonomy.get("object_type")
    company = taxonomy.get("platform_or_company")
    if object_text and company:
        return short(f"{object_text}: что решил суд в споре с {company}", 120)
    if object_text:
        return short(f"{object_text}: что решил суд", 120)
    if outcome.get("short_reason"):
        return short(outcome["short_reason"], 120)
    return short(summary.get("situation"), 120) or "Разбор судебного дела"


CARD_PROBLEM_LABELS = {
    "goods_defect_art18": "спор о недостатке товара",
    "distance_sale_return_art26_1": "отказ от дистанционной покупки",
    "info_violation_art10_12": "спор о недостоверной информации",
    "service_refusal_art32": "отказ от услуги и возврат денег",
    "prepaid_goods_delay_art23_1": "оплаченный товар не передали",
    "work_service_defect_art29": "спор о качестве работ или услуг",
}


def make_case_card_title(data: dict[str, Any]) -> str:
    taxonomy = data.get("taxonomy", {})
    summary = data.get("case_summary", {})
    object_text = taxonomy.get("object_name") or taxonomy.get("object_type")
    company = taxonomy.get("platform_or_company")
    problem = CARD_PROBLEM_LABELS.get(taxonomy.get("dispute_type_code")) or taxonomy.get("dispute_type")

    if object_text and problem:
        return uppercase_first_letter(short(f"{object_text}: {problem}", 140))
    if company and problem:
        return uppercase_first_letter(short(f"{company}: {problem}", 140))
    if problem:
        return uppercase_first_letter(short(str(problem), 140))
    return uppercase_first_letter(sentence_excerpt(summary.get("situation"), max_sentences=1, limit=140) or make_case_title(data))


def make_case_card_excerpt(data: dict[str, Any]) -> str:
    summary = data.get("case_summary", {})
    return sentence_excerpt(summary.get("situation"), max_sentences=2, limit=360)


def make_case_lead(data: dict[str, Any], result_label: str) -> str:
    taxonomy = data.get("taxonomy", {})
    outcome = data.get("claims_and_result", {}).get("outcome", {})
    object_text = taxonomy.get("object_name") or taxonomy.get("object_type")
    company = taxonomy.get("platform_or_company")
    problem = CARD_PROBLEM_LABELS.get(taxonomy.get("dispute_type_code")) or taxonomy.get("dispute_type")

    if object_text and company:
        subject = f"Разбор спора о {object_text} с {company}."
    elif object_text:
        subject = f"Разбор спора о {object_text}."
    elif company:
        subject = f"Разбор спора с {company}."
    elif problem:
        subject = f"Разбор дела: {problem}."
    else:
        subject = "Разбор судебного дела из текущей выборки."

    result = f"Итог для потребителя: {result_label}." if result_label else ""
    reason = sentence_excerpt(outcome.get("short_reason"), max_sentences=1, limit=220)
    reason_text = f"Ключевой вопрос: {reason}." if reason else ""
    return " ".join(part for part in [subject, result, reason_text] if part)


def inline_markdown(text: str) -> str:
    html = escape(text.strip())
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    return html


def markdown_to_html(markdown: str) -> str:
    html: list[str] = []
    list_type: str | None = None

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            html.append(f"</{list_type}>")
            list_type = None

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            close_list()
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            close_list()
            level = min(len(heading.group(1)) + 1, 4)
            html.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            continue

        bullet = re.match(r"^[*-]\s+(.+)$", line)
        if bullet:
            if list_type != "ul":
                close_list()
                html.append("<ul>")
                list_type = "ul"
            html.append(f"<li>{inline_markdown(bullet.group(1))}</li>")
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", line)
        if ordered:
            if list_type != "ol":
                close_list()
                html.append("<ol>")
                list_type = "ol"
            html.append(f"<li>{inline_markdown(ordered.group(1))}</li>")
            continue

        close_list()
        html.append(f"<p>{inline_markdown(line)}</p>")

    close_list()
    return "\n".join(html)


def render_plain_list(items: Any, empty_text: str = "Нет данных") -> str:
    if not isinstance(items, list) or not items:
        return f'<p class="muted">{escape(empty_text)}</p>'
    return "<ul>" + "".join(f"<li>{escape(short(item, 260))}</li>" for item in items if str(item).strip()) + "</ul>"


def render_timeline(timeline: Any) -> str:
    if not isinstance(timeline, list) or not timeline:
        return '<p class="muted">Таймлайн по этому делу не выделен.</p>'
    items = []
    for item in timeline:
        if not isinstance(item, dict):
            continue
        date = item.get("date") or "дата не указана"
        event = item.get("event") or ""
        if event:
            items.append(
                f"""
<li>
  <time>{escape(str(date))}</time>
  <span>{escape(short(event, 220))}</span>
</li>
"""
            )
    return f'<ol class="timeline">{"".join(items)}</ol>' if items else '<p class="muted">Таймлайн по этому делу не выделен.</p>'


def has_timeline(timeline: Any) -> bool:
    if not isinstance(timeline, list):
        return False
    for item in timeline:
        if isinstance(item, dict) and str(item.get("event") or "").strip():
            return True
    return False


def render_amount_items(items: Any, title: str) -> str:
    if not isinstance(items, list) or not items:
        return ""
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type") or "требование"
        amount = money(item.get("amount"))
        note = item.get("note") or ""
        rows.append(
            f"""
<li>
  <span>{escape(str(item_type))}</span>
  <b>{escape(amount)}</b>
  <small>{escape(short(note, 180))}</small>
</li>
"""
        )
    return f"<h3>{escape(title)}</h3><ul class=\"amount-list\">{''.join(rows)}</ul>" if rows else ""


LEGAL_APPLICATION_PLACEHOLDERS = {
    "да",
    "yes",
    "true",
    "нет",
    "no",
    "false",
    "применена",
    "применено",
    "применялась",
    "применялось",
    "упомянута",
    "упомянуто",
    "разъяснено",
}


def legal_application_text(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, bool):
        return ""
    text = str(value).strip()
    normalized = re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip(" .;:")
    if normalized in LEGAL_APPLICATION_PLACEHOLDERS:
        return ""
    return short(text, 360)


def render_legal_refs(legal_refs: Any) -> str:
    if not isinstance(legal_refs, list) or not legal_refs:
        return '<p class="muted">Применённые нормы в JSON не выделены.</p>'
    cards = []
    for ref in legal_refs:
        if not isinstance(ref, dict):
            continue
        application = legal_application_text(ref.get("applied_by_court"))
        application_html = (
            f"  <p><b>Роль в деле:</b> {escape(application)}</p>\n"
            if application
            else ""
        )
        cards.append(
            f"""
<article class="legal-ref">
  <h3>{escape(str(ref.get('ref') or 'Норма права'))}</h3>
  <p><b>Что значит:</b> {escape(short(ref.get('context'), 360))}</p>
{application_html.rstrip()}
</article>
"""
        )
    return '<div class="legal-ref-list">' + "".join(cards) + "</div>"


def root_page_link(page: SituationPage, label: str | None = None) -> str:
    return f'<a href="../../praktika/{escape(page.slug)}/index.html">{escape(label or page.h1)}</a>'


def render_case_detail_page(
    row: dict[str, Any],
    parent_page: SituationPage,
    labels: dict[str, dict[str, str]],
) -> str:
    data = row["_json"]
    source = data.get("source", {})
    court = data.get("court", {})
    taxonomy = data.get("taxonomy", {})
    summary = data.get("case_summary", {})
    claims = data.get("claims_and_result", {})
    outcome = claims.get("outcome", {})
    amounts = claims.get("amounts", {})
    legal = data.get("legal_analysis", {})

    docid = source.get("docid") or row["docid"]
    story_path = STRUCTURED_DIR / f"user_story_{docid}.md"
    practice_path = STRUCTURED_DIR / f"practice_{docid}.md"
    story_markdown = story_path.read_text(encoding="utf-8") if story_path.exists() else ""
    practice_markdown = practice_path.read_text(encoding="utf-8") if practice_path.exists() else ""

    fallback_title = make_case_title(data)
    title, story_body = extract_story_title_and_body(story_markdown, fallback_title)
    result = outcome.get("result_type") or row.get("result_type")
    result_label = RESULT_LABELS.get(result, result or "итог не указан")
    claim_labels = [
        labels["claim_type_codes"].get(code, code)
        for code in taxonomy.get("claim_type_codes") or []
    ]
    chips = " ".join(f'<span class="chip small">{escape(label)}</span>' for label in claim_labels[:8])
    source_url = source.get("source_url") or "#"
    claims_panel = f"""
    <div class="panel">
      <h2>Что требовал потребитель</h2>
      <p>{escape(short(claims.get('remedy'), 700))}</p>
      {render_amount_items(amounts.get('items_claimed'), 'Состав требований')}
      {render_amount_items(amounts.get('items_awarded'), 'Что присуждено')}
    </div>
"""
    if has_timeline(summary.get("timeline")):
        timeline_and_claims_section = f"""
  <section class="grid two">
    <div class="panel">
      <h2>Что произошло по датам</h2>
      {render_timeline(summary.get('timeline'))}
    </div>
{claims_panel}
  </section>
"""
    else:
        timeline_and_claims_section = f"""
  <section>
{claims_panel}
  </section>
"""

    body = f"""
<header class="site-header">
  <a class="brand" href="../../index.html">{escape(SITE_BRAND)}</a>
  <nav>
    {root_page_link(parent_page, "Назад к ситуации")}
  </nav>
</header>
<main>
  <section class="hero case-hero">
    <p class="eyebrow">Разбор судебного дела · {escape(court.get('region') or 'регион не указан')} · {escape(court.get('decision_date') or 'дата не указана')}</p>
    <h1>{escape(title)}</h1>
    <p class="lead">{escape(make_case_lead(data, str(result_label)))}</p>
    <p class="disclosure">Это пользовательская история на основе судебного акта. Она помогает понять жизненную ситуацию, ошибки сторон и значение применённых норм, но не является юридической консультацией.</p>
  </section>

  <section class="grid two">
    <div class="panel">
      <h2>Итог дела</h2>
      <dl class="case-facts stacked">
        <div><dt>Результат</dt><dd><span class="result result-{escape(str(result))}">{escape(str(result_label))}</span></dd></div>
        <div><dt>Заявлено</dt><dd>{escape(money(amounts.get('claimed_total')))}</dd></div>
        <div><dt>Присуждено</dt><dd>{escape(money(amounts.get('awarded_total')))}</dd></div>
        <div><dt>Суд</dt><dd>{escape(court.get('court_name') or 'не указан')}</dd></div>
        <div><dt>Дело</dt><dd>{escape(court.get('case_number') or docid)}</dd></div>
      </dl>
      <div class="case-links">
        <a href="{escape(source_url)}" target="_blank" rel="noopener">Открыть судебный акт</a>
        {root_page_link(parent_page, "Все похожие дела")}
      </div>
    </div>
    <div class="panel">
      <h2>Что важно вынести</h2>
      {render_plain_list(summary.get('practical_takeaways'), 'Практические выводы не выделены.')}
      <div class="chips">{chips}</div>
    </div>
  </section>

{timeline_and_claims_section}

  <section class="panel story-content">
    <h2>История дела простым языком</h2>
    {markdown_to_html(story_body)}
  </section>

  <section class="grid two">
    <div class="panel">
      <h2>Почему суд так решил</h2>
      <p>{escape(short(legal.get('holding'), 900))}</p>
      <h3>Ключевые факторы</h3>
      {render_plain_list(summary.get('key_factors'), 'Ключевые факторы не выделены.')}
    </div>
    <div class="panel">
      <h2>Ошибки и риски</h2>
      {render_plain_list(summary.get('unusual_points') or legal.get('arguments_rejected'), 'Отдельные риски не выделены.')}
    </div>
  </section>

  <section class="panel story-content">
    <h2>Подробный правовой разбор</h2>
    {markdown_to_html(practice_markdown)}
  </section>
</main>
<footer class="site-footer">
  <p>{escape(PROTOTYPE_DISCLAIMER)}</p>
</footer>
"""
    return html_page(title, body, "../../assets/prototype.css")


def render_situation_page(page: SituationPage, cases: list[dict[str, Any]], labels: dict[str, dict[str, str]]) -> str:
    result_counts = Counter(row.get("result_type") for row in cases)
    claim_counts: Counter[str] = Counter()
    object_counts: Counter[str] = Counter()
    company_counts: Counter[str] = Counter()
    awarded_values: list[float] = []
    factors: list[str] = []

    for row in cases:
        data = row["_json"]
        taxonomy = data.get("taxonomy", {})
        amounts = data.get("claims_and_result", {}).get("amounts", {})
        for code in taxonomy.get("claim_type_codes") or []:
            claim_counts[code] += 1
        if taxonomy.get("object_type"):
            object_counts[taxonomy["object_type"]] += 1
        if taxonomy.get("platform_or_company"):
            company_counts[taxonomy["platform_or_company"]] += 1
        awarded = number(amounts.get("awarded_total"))
        if awarded is not None:
            awarded_values.append(awarded)
        key_factors = data.get("case_summary", {}).get("key_factors") or []
        if isinstance(key_factors, list):
            factors.extend(str(x) for x in key_factors[:2])

    awarded_summary = "нет достаточных данных"
    if awarded_values:
        awarded_summary = f"от {money(min(awarded_values))} до {money(max(awarded_values))}; медиана — {money(median(awarded_values))}"

    factor_items = []
    seen: set[str] = set()
    for factor in factors:
        key = short(factor, 120)
        if key and key not in seen:
            seen.add(key)
            factor_items.append(key)
        if len(factor_items) >= 6:
            break

    page_by_code = {p.code: p for p in PAGES}
    related_links = " ".join(
        f'<span class="related">{page_link(page_by_code[code], current_page=page)}</span>'
        for code in RELATED.get(page.code, [])
        if code in page_by_code
    )

    cards = "\n".join(render_case_card(row, labels) for row in cases)
    body = f"""
<header class="site-header">
  <a class="brand" href="../../index.html">{escape(SITE_BRAND)}</a>
  <nav>{' '.join(page_link(p, p.slug, current_page=page) for p in PAGES)}</nav>
</header>
<main>
  <section class="hero">
    <p class="eyebrow">{escape(court_acts_label(len(cases)))} в выборке</p>
    <h1>{escape(page.h1)}</h1>
    <p class="lead">{escape(page.short_problem)}</p>
    <p class="disclosure">Практика собрана из судебных актов. Обработка данных выполнена алгоритмически; ссылки на первоисточники сохранены в карточках дел.</p>
  </section>

  <div class="situation-layout">
    <aside class="filter-sidebar">
      {render_filters(cases, labels)}
    </aside>
    <div class="situation-content">
      <section class="grid two">
        <div class="panel">
          <h2>Краткое резюме практики</h2>
          <ul class="summary-list">
            <li>Дел в выборке: <b>{len(cases)}</b></li>
            <li>Присуждённые суммы: <b>{escape(awarded_summary)}</b></li>
            <li><span>Результаты:</span> <span class="inline-chips">{counter_list(result_counts, labels['result_type'], 5, 'result')}</span></li>
          </ul>
          <p class="hint">Примечание: показатели являются не статистикой по всей судебной практике, а сводкой по текущей выборке судебных актов.</p>
        </div>
        <div class="panel">
          <h2>Что обычно требует потребитель</h2>
          <div class="chips">{counter_list(claim_counts, labels['claim_type_codes'], 10, 'claims')}</div>
        </div>
      </section>

      <section class="grid two">
        <div class="panel">
          <h2>Типичные объекты</h2>
          <div class="chips">{counter_list(object_counts, {}, 10, 'object')}</div>
        </div>
        <div class="panel">
          <h2>Компании и платформы</h2>
          <div class="chips">{counter_list(company_counts, {}, 10, 'company')}</div>
        </div>
      </section>

      <section class="panel">
        <h2>Почему суд удовлетворяет или отказывает</h2>
        <ul>{''.join(f'<li>{escape(item)}</li>' for item in factor_items)}</ul>
      </section>

      <section>
        <h2>Дела в этой выборке</h2>
        <div class="case-list" data-case-list>{cards}</div>
      </section>

      <section class="panel checklist">
        <h2>Проверить перед спором</h2>
        <ul>
          <li>Есть ли договор, чек, заказ, переписка или претензия.</li>
          <li>Можно ли определить продавца, исполнителя или владельца агрегатора.</li>
          <li>Какие требования подходят: возврат денег, неустойка, штраф, убытки, расходы.</li>
          <li>Есть ли риск отказа: ненадлежащий ответчик, пропущенные доказательства, оплата вне платформы.</li>
        </ul>
      </section>

      <section class="panel">
        <h2>Связанные ситуации</h2>
        <div class="related-list">{related_links}</div>
      </section>
    </div>
  </div>
</main>
<footer class="site-footer">
  <p>{escape(PROTOTYPE_DISCLAIMER)}</p>
</footer>
"""
    return html_page(page.h1, body, "../../assets/prototype.css")


def render_index(by_cluster: dict[str, list[dict[str, Any]]]) -> str:
    cards = []
    for page in PAGES:
        count = len(by_cluster.get(page.code, []))
        cards.append(
            f"""
<article class="index-card">
  <p class="eyebrow">{escape(court_acts_label(count))} в выборке</p>
  <h2>{page_link(page)}</h2>
  <p>{escape(page.short_problem)}</p>
  <a class="button" href="{escape(page_href(page))}">Открыть страницу</a>
</article>
"""
        )
    body = f"""
<header class="site-header">
  <a class="brand" href="index.html">{escape(SITE_BRAND)}</a>
</header>
<main>
  <section class="hero">
    <p class="eyebrow">SSG-прототип</p>
    <h1>Первые страницы судебной практики по ЗоЗПП</h1>
    <p class="lead">Пять страниц-ситуаций собраны из 46 индексируемых судебных актов первой партии. Цель — проверить структуру, карточки и данные перед полноценным фронтендом.</p>
  </section>
  <section class="index-grid">
    {''.join(cards)}
  </section>
</main>
<footer class="site-footer">
  <p>{escape(PROTOTYPE_DISCLAIMER)}</p>
</footer>
"""
    return html_page("SSG-прототип страниц практики", body, "assets/prototype.css")


def write_css() -> None:
    css = """
:root {
  --bg: #f6f3ed;
  --paper: #fffdf8;
  --ink: #1f2933;
  --muted: #687381;
  --line: #ded6c8;
  --accent: #8b5e34;
  --accent-2: #294b63;
  --good: #236b4a;
  --bad: #8f2f2f;
  --mixed: #8a651c;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: var(--bg);
  line-height: 1.55;
}
a { color: var(--accent-2); text-decoration: none; }
a:hover { text-decoration: underline; }
.site-header, .site-footer {
  max-width: 1180px;
  margin: 0 auto;
  padding: 22px 24px;
}
.site-header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
}
.site-header nav {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 14px;
}
.brand { font-weight: 750; color: var(--ink); }
main { max-width: 1180px; margin: 0 auto; padding: 0 24px 48px; }
.hero {
  background: linear-gradient(135deg, #fffdf8, #efe5d5);
  border: 1px solid var(--line);
  border-radius: 28px;
  padding: 38px;
  margin: 16px 0 24px;
}
.hero h1 { font-size: clamp(32px, 4vw, 56px); line-height: 1.05; margin: 8px 0 16px; }
.lead { font-size: 20px; max-width: 820px; color: #344150; }
.eyebrow { text-transform: uppercase; letter-spacing: .08em; color: var(--accent); font-size: 13px; font-weight: 700; }
.disclosure, .hint, .muted { color: var(--muted); }
.case-hero h1 { max-width: 980px; }
.situation-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 22px;
  align-items: start;
}
.situation-content { grid-column: 1; grid-row: 1; min-width: 0; }
.filter-sidebar {
  grid-column: 2;
  grid-row: 1;
  position: sticky;
  top: 16px;
  align-self: start;
  max-height: calc(100vh - 32px);
  overflow: auto;
}
.grid.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin: 18px 0; }
.panel, .case-card, .index-card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 24px;
  box-shadow: 0 10px 30px rgba(31, 41, 51, .04);
}
.summary-list { padding-left: 20px; }
.summary-list li { margin-bottom: 10px; }
.inline-chips {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 8px;
  vertical-align: middle;
  margin-top: 6px;
}
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.chip {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  padding: 7px 10px;
  background: #efe8dc;
  border-radius: 999px;
  font-size: 14px;
}
.chip-button {
  border: 0;
  cursor: pointer;
  color: var(--ink);
  font: inherit;
}
.chip-button:hover, .chip-button:focus {
  background: #e2d6c3;
  outline: 2px solid rgba(41, 75, 99, .16);
}
.chip.small { font-size: 12px; padding: 5px 8px; }
.filters { margin: 24px 0; }
.filter-sidebar .filters { margin: 0; }
.filter-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
.filter-sidebar .filter-grid { grid-template-columns: 1fr; }
.filter-actions { margin-top: 14px; }
label { display: grid; gap: 6px; font-size: 14px; color: var(--muted); }
select {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px;
  background: white;
  color: var(--ink);
}
.case-list { display: grid; gap: 18px; }
.case-card__header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.case-card h3 { margin: 0 0 8px; font-size: 22px; }
.case-card h4 { margin-bottom: 6px; }
.meta { color: var(--muted); margin: 0; }
.meta-filter {
  border: 0;
  padding: 0;
  background: none;
  color: var(--accent-2);
  cursor: pointer;
  font: inherit;
}
.meta-filter:hover, .meta-filter:focus { text-decoration: underline; }
.result {
  white-space: nowrap;
  border-radius: 999px;
  padding: 7px 10px;
  font-size: 13px;
  font-weight: 700;
  background: #eceff2;
}
button.result {
  border: 0;
  font-family: inherit;
  cursor: pointer;
}
button.result:hover, button.result:focus { outline: 2px solid rgba(41, 75, 99, .16); }
.result-satisfied { color: var(--good); background: #e7f3ed; }
.result-partially_satisfied { color: var(--mixed); background: #f5edd8; }
.result-rejected { color: var(--bad); background: #f8e7e7; }
.result-mixed { color: var(--accent-2); background: #e7edf2; }
.case-facts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 18px 0; }
.case-facts.stacked { grid-template-columns: 1fr; }
.case-facts div { background: #f6f1e8; border-radius: 16px; padding: 12px; }
dt { color: var(--muted); font-size: 12px; }
dd { margin: 2px 0 0; font-weight: 700; }
.case-links { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 18px; align-items: center; }
.case-primary-link { font-weight: 750; }
.source-link {
  display: inline-flex;
  align-items: center;
  color: var(--muted);
  font-size: 14px;
}
.source-link:hover, .source-link:focus { color: var(--accent-2); }
.story-content { font-size: 17px; }
.story-content h3, .story-content h4 { margin-top: 26px; }
.story-content p, .story-content li { max-width: 900px; }
.story-content details { border: 1px solid var(--line); border-radius: 16px; padding: 16px 18px; background: #fffaf0; }
.story-content summary { cursor: pointer; font-weight: 750; color: var(--accent-2); }
.timeline { list-style: none; padding: 0; display: grid; gap: 10px; }
.timeline li { display: grid; grid-template-columns: 130px 1fr; gap: 12px; border-bottom: 1px solid var(--line); padding-bottom: 10px; }
.timeline time { color: var(--accent); font-weight: 750; }
.amount-list { list-style: none; padding: 0; display: grid; gap: 10px; }
.amount-list li { display: grid; grid-template-columns: 1fr auto; gap: 4px 12px; background: #f6f1e8; border-radius: 14px; padding: 12px; }
.amount-list small { grid-column: 1 / -1; color: var(--muted); }
.legal-ref-list { display: grid; gap: 14px; }
.legal-ref { border: 1px solid var(--line); border-radius: 18px; padding: 18px; background: #fffaf0; }
.legal-ref h3 { margin-top: 0; color: var(--accent-2); }
.related-list { display: flex; flex-wrap: wrap; gap: 10px; }
.related, .button {
  display: inline-block;
  padding: 10px 14px;
  background: var(--accent-2);
  color: white;
  border-radius: 12px;
  border: 0;
  font: inherit;
  cursor: pointer;
}
.button.secondary { background: #efe8dc; color: var(--ink); }
.button.secondary:hover, .button.secondary:focus { background: #e2d6c3; }
.related a { color: white; }
.index-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.index-card h2 { margin-top: 0; }
[hidden] { display: none !important; }
@media (max-width: 900px) {
  .situation-layout, .grid.two, .index-grid, .filter-grid, .case-facts { grid-template-columns: 1fr; }
  .situation-content, .filter-sidebar { grid-column: auto; grid-row: auto; }
  .filter-sidebar { position: static; max-height: none; overflow: visible; margin-bottom: 18px; }
  .timeline li, .amount-list li { grid-template-columns: 1fr; }
  .site-header { display: block; }
  .hero { padding: 26px; }
  .case-card__header { display: block; }
  .result { display: inline-block; margin-top: 10px; }
}
"""
    (OUT_DIR / "assets").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "assets" / "prototype.css").write_text(css.strip() + "\n", encoding="utf-8")


def main() -> int:
    labels = load_enum_labels()
    _, by_cluster = load_cases()

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "praktika").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "dela").mkdir(parents=True, exist_ok=True)
    write_css()

    generated_case_pages = 0
    for page in PAGES:
        page.output_path.parent.mkdir(parents=True, exist_ok=True)
        page.output_path.write_text(render_situation_page(page, by_cluster[page.code], labels), encoding="utf-8")
        for row in by_cluster[page.code]:
            docid = row["docid"]
            case_path = OUT_DIR / "dela" / docid / "index.html"
            case_path.parent.mkdir(parents=True, exist_ok=True)
            case_path.write_text(render_case_detail_page(row, page, labels), encoding="utf-8")
            generated_case_pages += 1

    (OUT_DIR / "index.html").write_text(render_index(by_cluster), encoding="utf-8")

    print(f"Сгенерировано страниц-ситуаций: {len(PAGES)}")
    print(f"Сгенерировано страниц дел: {generated_case_pages}")
    print(f"Индекс: {(OUT_DIR / 'index.html').as_posix()}")
    for page in PAGES:
        print(f"- {page.route} -> {page.output_path.as_posix()} ({len(by_cluster[page.code])} дел)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
