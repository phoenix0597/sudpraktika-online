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
    "mixed": "смешанный итог",
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
  }});
}});
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


def counter_list(items: Counter[str], labels: dict[str, str], max_items: int = 8) -> str:
    parts = []
    for code, count in items.most_common(max_items):
        label = labels.get(code, code)
        parts.append(f'<span class="chip">{escape(label)} <b>{count}</b></span>')
    return "\n".join(parts) if parts else '<span class="muted">Нет данных</span>'


def make_options(values: list[str]) -> str:
    options = ['<option value="">Все</option>']
    for value in sorted({v for v in values if v and v != "не указан"}):
        options.append(f'<option value="{escape(value)}">{escape(value)}</option>')
    if any(v == "не указан" or not v for v in values):
        options.append('<option value="не указан">Не указано</option>')
    return "\n".join(options)


def data_value(value: Any) -> str:
    value = slug_attr(value)
    return value if value else "не указан"


def render_filters(cases: list[dict[str, Any]]) -> str:
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
    <label>Результат<select data-filter="result">{make_options(results)}</select></label>
    <label>Компания<select data-filter="company">{make_options(companies)}</select></label>
    <label>Объект<select data-filter="object">{make_options(objects)}</select></label>
    <label>Требование<select data-filter="claims">{make_options(claim_codes)}</select></label>
    <label>Регион<select data-filter="region">{make_options(regions)}</select></label>
  </div>
  <p class="hint">Фильтры работают внутри страницы и не создают отдельные индексируемые URL.</p>
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

    factor_html = ""
    if key_factors:
        factor_html = "<ul>" + "".join(f"<li>{escape(short(f, 180))}</li>" for f in key_factors[:2]) + "</ul>"
    else:
        factor_html = '<p class="muted">Ключевые факторы не выделены.</p>'

    chips = " ".join(f'<span class="chip small">{escape(label)}</span>' for label in claim_labels[:6])
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
      <h3>{escape(short(summary.get('situation'), 120) or 'Судебное дело')}</h3>
      <p class="meta">{escape(court.get('region') or 'регион не указан')} · {escape(court.get('decision_date') or 'дата не указана')} · дело {escape(court.get('case_number') or docid)}</p>
    </div>
    <span class="result result-{escape(str(result))}">{escape(result_label)}</span>
  </div>
  <p>{escape(short(summary.get('situation'), 420))}</p>
  <dl class="case-facts">
    <div><dt>Объект</dt><dd>{escape(object_text)}</dd></div>
    <div><dt>Компания</dt><dd>{escape(company)}</dd></div>
    <div><dt>Присуждено</dt><dd>{escape(money(amounts.get('awarded_total')))}</dd></div>
  </dl>
  <div class="chips">{chips}</div>
  <h4>Что повлияло на исход</h4>
  {factor_html}
  <div class="case-links">
    <a href="{escape(source_url)}" target="_blank" rel="noopener">Первоисточник</a>
    <span class="muted">Страница дела — позже: {escape(docid)}</span>
  </div>
</article>
"""


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
  <a class="brand" href="../../index.html">ZPP Consult · прототип</a>
  <nav>{' '.join(page_link(p, p.slug, current_page=page) for p in PAGES)}</nav>
</header>
<main>
  <section class="hero">
    <p class="eyebrow">{escape(court_acts_label(len(cases)))} в выборке</p>
    <h1>{escape(page.h1)}</h1>
    <p class="lead">{escape(page.short_problem)}</p>
    <p class="disclosure">Практика собрана из судебных актов. Обработка данных выполнена алгоритмически; ссылки на первоисточники сохранены в карточках дел.</p>
  </section>

  <section class="grid two">
    <div class="panel">
      <h2>Краткое резюме практики</h2>
      <ul class="summary-list">
        <li>Дел в выборке: <b>{len(cases)}</b></li>
        <li>Присуждённые суммы: <b>{escape(awarded_summary)}</b></li>
        <li>Результаты: {counter_list(result_counts, labels['result_type'], 5)}</li>
      </ul>
      <p class="hint">Это не статистика по всей судебной практике, а сводка по текущей выборке актов проекта.</p>
    </div>
    <div class="panel">
      <h2>Что обычно требует потребитель</h2>
      <div class="chips">{counter_list(claim_counts, labels['claim_type_codes'], 10)}</div>
    </div>
  </section>

  <section class="grid two">
    <div class="panel">
      <h2>Типичные объекты</h2>
      <div class="chips">{counter_list(object_counts, {}, 10)}</div>
    </div>
    <div class="panel">
      <h2>Компании и платформы</h2>
      <div class="chips">{counter_list(company_counts, {}, 10)}</div>
    </div>
  </section>

  <section class="panel">
    <h2>Почему суд удовлетворяет или отказывает</h2>
    <ul>{''.join(f'<li>{escape(item)}</li>' for item in factor_items)}</ul>
  </section>

  {render_filters(cases)}

  <section>
    <h2>Дела в этом кластере</h2>
    <div class="case-list">{cards}</div>
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
</main>
<footer class="site-footer">
  <p>Прототип. Не является юридической консультацией. Материалы основаны на судебных актах и требуют редакционной проверки перед публикацией.</p>
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
  <a class="brand" href="index.html">ZPP Consult · прототип</a>
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
  <p>Прототип создан из JSON-структур проекта.</p>
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
.grid.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin: 18px 0; }
.panel, .case-card, .index-card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 24px;
  box-shadow: 0 10px 30px rgba(31, 41, 51, .04);
}
.summary-list { padding-left: 20px; }
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
.chip.small { font-size: 12px; padding: 5px 8px; }
.filters { margin: 24px 0; }
.filter-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
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
.result {
  white-space: nowrap;
  border-radius: 999px;
  padding: 7px 10px;
  font-size: 13px;
  font-weight: 700;
  background: #eceff2;
}
.result-satisfied { color: var(--good); background: #e7f3ed; }
.result-partially_satisfied { color: var(--mixed); background: #f5edd8; }
.result-rejected { color: var(--bad); background: #f8e7e7; }
.result-mixed { color: var(--accent-2); background: #e7edf2; }
.case-facts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 18px 0; }
.case-facts div { background: #f6f1e8; border-radius: 16px; padding: 12px; }
dt { color: var(--muted); font-size: 12px; }
dd { margin: 2px 0 0; font-weight: 700; }
.case-links { display: flex; gap: 14px; margin-top: 16px; }
.related-list { display: flex; flex-wrap: wrap; gap: 10px; }
.related, .button {
  display: inline-block;
  padding: 10px 14px;
  background: var(--accent-2);
  color: white;
  border-radius: 12px;
}
.related a { color: white; }
.index-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.index-card h2 { margin-top: 0; }
[hidden] { display: none !important; }
@media (max-width: 900px) {
  .grid.two, .index-grid, .filter-grid, .case-facts { grid-template-columns: 1fr; }
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
    write_css()

    for page in PAGES:
        page.output_path.parent.mkdir(parents=True, exist_ok=True)
        page.output_path.write_text(render_situation_page(page, by_cluster[page.code], labels), encoding="utf-8")

    (OUT_DIR / "index.html").write_text(render_index(by_cluster), encoding="utf-8")

    print(f"Сгенерировано страниц-ситуаций: {len(PAGES)}")
    print(f"Индекс: {(OUT_DIR / 'index.html').as_posix()}")
    for page in PAGES:
        print(f"- {page.route} -> {page.output_path.as_posix()} ({len(by_cluster[page.code])} дел)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
