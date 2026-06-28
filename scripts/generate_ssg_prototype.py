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
import os
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


def read_local_env(name: str) -> str | None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return None
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return None


def config_value(name: str, default: str) -> str:
    return os.environ.get(name) or read_local_env(name) or default


DEFAULT_PUBLIC_BASE_URL = "https://sudpraktika-online.ru"
PUBLIC_BASE_URL = config_value("SITE_PUBLIC_URL", DEFAULT_PUBLIC_BASE_URL).strip().rstrip("/")
PROTOTYPE_DISCLAIMER = (
    "Не является юридической консультацией. Материалы основаны на судебных актах "
    "и обработаны алгоритмом для систематизации и обобщения текущей судебной практики судов разных инстанций."
)


@dataclass(frozen=True)
class SituationPage:
    code: str
    slug: str
    h1: str
    short_problem: str
    page_type: str
    nav_label: str

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
        "Некачественный товар",
    ),
    SituationPage(
        "proper_quality_goods_exchange_art25",
        "vozvrat-obmen-kachestvennogo-tovara",
        "Возврат и обмен товара надлежащего качества: что решил суд",
        "Товар качественный, но не подошёл по форме, размеру, фасону, расцветке, комплектации или другим потребительским параметрам.",
        "long_tail",
        "Возврат качественного товара",
    ),
    SituationPage(
        "distance_sale_return_art26_1",
        "vozvrat-tovara-online",
        "Как вернуть товар, купленный онлайн",
        "Покупка была дистанционной: через сайт, маркетплейс или интернет-магазин, а потребитель хочет отказаться от товара и вернуть деньги.",
        "landing",
        "Возврат онлайн-покупки",
    ),
    SituationPage(
        "info_violation_art10_12",
        "nedostovernaya-informatsiya",
        "Неверная цена, продавец или информация о товаре: что решил суд",
        "Покупателю дали неполную или недостоверную информацию о цене, продавце, свойствах товара или условиях покупки.",
        "landing",
        "Недостоверная информация",
    ),
    SituationPage(
        "service_refusal_art32",
        "vozvrat-deneg-za-uslugu",
        "Как отказаться от услуги и вернуть деньги",
        "Потребитель хочет отказаться от услуги, курса, страховки, сертификата или сервиса и вернуть оплату.",
        "landing",
        "Возврат денег за услугу",
    ),
    SituationPage(
        "unfair_terms_imposed_services_art16",
        "navyazannye-uslugi-i-usloviya",
        "Навязанные услуги и недопустимые условия договора: практика судов",
        "Потребитель спорит с платными опциями, дополнительными услугами или условиями договора, которые ущемляют его права.",
        "landing",
        "Навязанные услуги",
    ),
    SituationPage(
        "prepaid_goods_delay_art23_1",
        "oplatili-tovar-ne-peredali",
        "Оплатили товар, но его не передали: что можно взыскать",
        "Заказ был оплачен заранее, но продавец задержал передачу, отменил заказ или не вернул предоплату.",
        "landing",
        "Оплатили, но товар не передали",
    ),
    SituationPage(
        "work_service_defect_art29",
        "nekachestvennaya-rabota-usluga",
        "Некачественные работы и услуги: права потребителя и возврат денег",
        "Потребитель заказал работы или услуги (ремонт, установка окон/дверей, изготовление мебели), но они выполнены некачественно или с дефектами.",
        "pillar",
        "Некачественные работы и услуги",
    ),
    SituationPage(
        "consumer_material_damage_art35",
        "povrezhdenie-veschi-potrebitelya",
        "Повреждение или утрата вещи потребителя при работах: практика по ст. 35 ЗоЗПП",
        "Потребитель передал вещь, материал или имущество исполнителю, а в ходе работ оно было повреждено, утрачено или испорчено.",
        "pillar",
        "Повреждение вещи при работах",
    ),
    SituationPage(
        "harm_from_defect_art14",
        "vred-ot-nedostatka",
        "Вред от недостатка товара, работы или услуги: когда взыскивают ущерб",
        "Недостаток товара, работы или услуги причинил вред имуществу, здоровью или иным охраняемым интересам потребителя.",
        "landing",
        "Вред от недостатка",
    ),
    SituationPage(
        "work_service_delay_art28",
        "prosrochka-rabot-uslug",
        "Нарушение сроков выполнения работ и услуг: расчет неустойки и права",
        "Исполнитель нарушил сроки начала или окончания работ/услуг (ремонт, монтаж, строительство).",
        "landing",
        "Просрочка работ и услуг",
    ),
]


RESULT_LABELS = {
    "satisfied": "удовлетворено",
    "partially_satisfied": "частично удовлетворено",
    "rejected": "отказано",
    "mixed": "смешанный результат",
    "hold": "не публиковать",
}


AMOUNT_ITEM_LABELS = {
    "contract_performance": "исполнение договора",
    "expert_expenses": "расходы на экспертизу",
    "fine": "штраф",
    "legal_expenses": "расходы на юридическую помощь",
    "loan_interest": "проценты по кредиту",
    "moral_damage": "компенсация морального вреда",
    "moral_damages": "компенсация морального вреда",
    "obligation_to_collect_item": "обязать забрать товар",
    "ongoing_penalty": "неустойка на будущее",
    "penalty": "неустойка",
    "penalty_fine": "потребительский штраф 50%",
    "penalty_under_contract_248": "неустойка по договору",
    "penalty_under_contract_249": "неустойка по договору",
    "postage_expenses": "почтовые расходы",
    "price_difference": "разница в цене",
    "refund": "возврат цены или предоплаты",
    "refund_under_contract_249": "возврат уплаченной суммы по договору",
    "return_of_premium": "возврат страховой премии",
}


RELATED = {
    "goods_defect_art18": [
        "proper_quality_goods_exchange_art25",
        "distance_sale_return_art26_1",
        "harm_from_defect_art14",
        "info_violation_art10_12",
    ],
    "proper_quality_goods_exchange_art25": [
        "goods_defect_art18",
        "distance_sale_return_art26_1",
        "info_violation_art10_12",
    ],
    "distance_sale_return_art26_1": [
        "proper_quality_goods_exchange_art25",
        "goods_defect_art18",
        "info_violation_art10_12",
        "prepaid_goods_delay_art23_1",
    ],
    "info_violation_art10_12": [
        "distance_sale_return_art26_1",
        "unfair_terms_imposed_services_art16",
        "service_refusal_art32",
        "goods_defect_art18",
    ],
    "service_refusal_art32": [
        "unfair_terms_imposed_services_art16",
        "info_violation_art10_12",
        "work_service_defect_art29",
    ],
    "unfair_terms_imposed_services_art16": [
        "service_refusal_art32",
        "info_violation_art10_12",
    ],
    "prepaid_goods_delay_art23_1": ["distance_sale_return_art26_1", "goods_defect_art18"],
    "work_service_defect_art29": [
        "consumer_material_damage_art35",
        "harm_from_defect_art14",
        "work_service_delay_art28",
    ],
    "consumer_material_damage_art35": [
        "work_service_defect_art29",
        "harm_from_defect_art14",
    ],
    "harm_from_defect_art14": [
        "goods_defect_art18",
        "work_service_defect_art29",
        "consumer_material_damage_art35",
    ],
    "work_service_delay_art28": ["work_service_defect_art29", "service_refusal_art32"],
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


def public_url(path: str) -> str | None:
    if not PUBLIC_BASE_URL:
        return None
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{PUBLIC_BASE_URL}{normalized}"


def canonical_link(path: str | None) -> str:
    if not path:
        return ""
    url = public_url(path)
    if not url:
        return ""
    return f'  <link rel="canonical" href="{escape(url)}">\n'


def html_page(title: str, body: str, stylesheet_href: str, canonical_path: str | None = None) -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
{canonical_link(canonical_path).rstrip()}
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


def case_route(docid: str) -> str:
    return f"/dela/{docid}/"


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
    if len(cleaned) > 140:
        return False
    if re.search(r"[.!?…]\s+\S", cleaned):
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
        subject = f"Разбор спора: {object_text}; оппонент — {company}."
    elif object_text:
        subject = f"Разбор спора: {object_text}."
    elif company:
        subject = f"Разбор спора с {company}."
    elif problem:
        subject = f"Разбор дела: {problem}."
    else:
        subject = "Разбор судебного дела из текущей выборки."

    result = f"Итог для потребителя: {result_label}." if result_label else ""
    reason = sentence_excerpt(outcome.get("short_reason"), max_sentences=1, limit=220)
    reason_text = f"Ключевой вопрос: {reason.rstrip(' .')}." if reason else ""
    return " ".join(part for part in [subject, result, reason_text] if part)


def inline_markdown(text: str) -> str:
    html = escape(text.strip())
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", html)
    return html


NOTE_LABELS = (
    "Значение в деле",
    "Применение судом",
    "Что означает в деле",
    "Как применена судом",
)

PRACTICE_SECTION_TITLES = (
    "Нормы, на которые сослался суд",
    "Логика решения",
    "Факторы, повлиявшие на исход",
)

LEGACY_APPLICATION_PATTERNS = (
    r"Суд\s+применил[а]?\b",
    r"Суд\s+использовал[а]?\b",
    r"Суд\s+руководствовался\b",
    r"Суд\s+уч[её]л\b",
    r"Суд\s+оценивал\b",
    r"Суд\s+сослался\b",
    r"Суд\s+указал\b",
    r"Применен[аы]?\s+судом\b",
    r"Применен[аы]?\b",
    r"Использован[аы]?\b",
)


def practice_numbered_heading(line: str) -> str | None:
    if not re.match(r"^\d+\.\s+", line.strip()):
        return None
    return normalize_practice_section_title(line)


def practice_heading_title(line: str) -> str | None:
    return normalize_practice_section_title(line)


def normalize_practice_section_title(text: str) -> str | None:
    title = text.strip()
    title = re.sub(r"^#{1,6}\s+", "", title).strip()
    title = re.sub(r"^\d+\.\s*", "", title).strip()
    title = title.rstrip(":").strip()
    title = re.sub(r"^\*\*(.+?)\*\*$", r"\1", title).strip()
    title = re.sub(r"^\*(.+?)\*$", r"\1", title).strip()
    title = title.replace("Fакторы", "Факторы")
    title = re.sub(r"\s+", " ", title)
    return title if title in PRACTICE_SECTION_TITLES else None


def semantic_note_markdown(raw_line: str) -> str | None:
    nested_bullet = re.match(r"^\s+[*-]\s+(.+)$", raw_line)
    has_indent = bool(re.match(r"^\s+", raw_line))
    candidate = nested_bullet.group(1).strip() if nested_bullet else raw_line.strip()
    probe = re.sub(r"^[*_]+", "", candidate).strip()
    probe = re.sub(r"^[*_]+", "", probe).strip()

    label_pattern = "|".join(re.escape(label) for label in NOTE_LABELS)
    if re.match(rf"^(?:{label_pattern}):", probe):
        return candidate
    if has_indent and re.match(r"^Пункт\s+\d+:", probe):
        return candidate
    return None


def nested_note_markdown(text: str) -> str:
    html = inline_markdown(text)
    html = re.sub(
        r"^<(?:strong|em)>((?:Значение в деле|Применение судом|Что означает в деле|Как применена судом|Пункт\s+\d+):)</(?:strong|em)>",
        r"<strong><em>\1</em></strong>",
        html,
    )
    html = re.sub(
        r"^((?:Значение в деле|Применение судом|Что означает в деле|Как применена судом|Пункт\s+\d+):)",
        r"<strong><em>\1</em></strong>",
        html,
    )
    return html


def split_legacy_application(text: str) -> tuple[str, str | None]:
    for pattern in LEGACY_APPLICATION_PATTERNS:
        match = re.search(rf"(.+?)\s+({pattern}.*)$", text, flags=re.IGNORECASE)
        if match:
            meaning = match.group(1).strip()
            application = match.group(2).strip()
            if meaning and application:
                return meaning, application
    return text.strip(), None


def render_legacy_norm_item(text: str) -> str | None:
    match = re.match(r"^\*\*(.+?)\*\*:\s*(.+)$", text.strip())
    if not match:
        return None

    norm = match.group(1).strip()
    details = match.group(2).strip()
    meaning, application = split_legacy_application(details)

    parts = [
        "<ul>",
        f"<li><strong>{escape(norm)}</strong></li>",
        "</ul>",
    ]
    if meaning:
        parts.append(f'<p class="md-note">{nested_note_markdown(f"Значение в деле: {meaning}")}</p>')
    if application:
        parts.append(f'<p class="md-note">{nested_note_markdown(f"Применение судом: {application}")}</p>')
    return "\n".join(parts)


def practice_section_list_type(section: str | None) -> str:
    return "ol" if section == "Логика решения" else "ul"


def practice_list_open_tag(list_type: str, section: str | None) -> str:
    if section == "Логика решения" and list_type == "ol":
        return '<ol class="practice-logic">'
    return f"<{list_type}>"


FACTOR_LEAD_DELIMITERS = (
    r"\s+\(",
    r"\s+от\s+\d{1,2}\.\d{1,2}\.\d{4}",
    r"\s+\d{1,2}\.\d{1,2}\.\d{4}",
    r"\s+в\s+течение\b",
    r"\s+по\s+ст\.?\s+\d",
)


def factor_lead_markdown(text: str) -> str:
    value = text.strip()
    if not value or value.lstrip().startswith("**") or re.match(r"^[^:<]{3,90}:\s+", value):
        return value

    cuts: list[int] = []
    for pattern in FACTOR_LEAD_DELIMITERS:
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            cuts.append(match.start())

    if not cuts:
        return value

    cut = min(cuts)
    lead = value[:cut].strip()
    tail = value[cut:].strip()
    words = re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", lead)
    if not tail or len(words) < 2 or len(words) > 10 or len(lead) > 90:
        return value

    return f"**{lead}:** {tail}"


def inline_practice_list_item(text: str, section: str | None) -> str:
    if section == "Факторы, повлиявшие на исход":
        text = factor_lead_markdown(text)
    html = inline_markdown(text)
    if section == "Факторы, повлиявшие на исход" and not html.lstrip().startswith("<strong>"):
        html = re.sub(r"^([^:<]{3,90}:)\s+", r"<strong>\1</strong> ", html)
    return html


def markdown_to_html(markdown: str) -> str:
    html: list[str] = []
    list_type: str | None = None
    current_practice_section: str | None = None

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

        numbered_heading = practice_numbered_heading(line)
        if numbered_heading:
            close_list()
            current_practice_section = numbered_heading
            html.append(f"<h4>{escape(numbered_heading)}</h4>")
            continue

        semantic_note = semantic_note_markdown(raw_line)
        if semantic_note:
            close_list()
            html.append(f'<p class="md-note">{nested_note_markdown(semantic_note)}</p>')
            continue

        nested_bullet = re.match(r"^\s+[*-]\s+(.+)$", raw_line)
        if nested_bullet:
            legacy_norm_html = (
                render_legacy_norm_item(nested_bullet.group(1))
                if current_practice_section == "Нормы, на которые сослался суд"
                else None
            )
            if legacy_norm_html:
                close_list()
                html.append(legacy_norm_html)
                continue

            target_list_type = practice_section_list_type(current_practice_section)
            if list_type != target_list_type:
                close_list()
                html.append(practice_list_open_tag(target_list_type, current_practice_section))
                list_type = target_list_type
            html.append(f"<li>{inline_practice_list_item(nested_bullet.group(1), current_practice_section)}</li>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            close_list()
            title = heading.group(2)
            practice_section = practice_heading_title(title)
            if practice_section:
                current_practice_section = practice_section
                html.append(f"<h4>{escape(practice_section)}</h4>")
            else:
                current_practice_section = None
                level = min(len(heading.group(1)) + 1, 4)
                html.append(f"<h{level}>{inline_markdown(title)}</h{level}>")
            continue

        bullet = re.match(r"^[*-]\s+(.+)$", line)
        if bullet:
            legacy_norm_html = (
                render_legacy_norm_item(bullet.group(1))
                if current_practice_section == "Нормы, на которые сослался суд"
                else None
            )
            if legacy_norm_html:
                close_list()
                html.append(legacy_norm_html)
                continue

            target_list_type = practice_section_list_type(current_practice_section)
            if list_type != target_list_type:
                close_list()
                html.append(practice_list_open_tag(target_list_type, current_practice_section))
                list_type = target_list_type
            html.append(f"<li>{inline_practice_list_item(bullet.group(1), current_practice_section)}</li>")
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", line)
        if ordered:
            if list_type != "ol":
                close_list()
                html.append(practice_list_open_tag("ol", current_practice_section))
                list_type = "ol"
            html.append(f"<li>{inline_practice_list_item(ordered.group(1), current_practice_section)}</li>")
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


def amount_item_label(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "денежное требование"
    if re.search(r"[А-Яа-яЁё]", text):
        return text
    return AMOUNT_ITEM_LABELS.get(text, "денежное требование")


def render_amount_items(items: Any, title: str) -> str:
    if not isinstance(items, list) or not items:
        return ""
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_type = amount_item_label(item.get("type"))
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
    title = uppercase_first_letter(title)
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
    return html_page(title, body, "../../assets/prototype.css", canonical_path=case_route(docid))


def top_counter_text(items: Counter[str], labels: dict[str, str] | None = None, max_items: int = 4) -> str:
    labels = labels or {}
    parts: list[str] = []
    for code, count in items.most_common(max_items):
        if not code:
            continue
        parts.append(f"{labels.get(code, code)} — {count}")
    return "; ".join(parts) if parts else "недостаточно данных"


def render_service_recommendations(
    cases: list[dict[str, Any]],
    labels: dict[str, dict[str, str]],
    result_counts: Counter[str],
    claim_counts: Counter[str],
    factor_items: list[str],
) -> str:
    region_counts: Counter[str] = Counter()
    court_counts: Counter[str] = Counter()

    for row in cases:
        data = row["_json"]
        court = data.get("court", {})
        if court.get("region"):
            region_counts[str(court["region"])] += 1
        if court.get("court_name"):
            court_counts[str(court["court_name"])] += 1

    factor_text = "; ".join(factor_items[:3]) if factor_items else "по текущей выборке повторяющиеся факторы пока не выделены"
    region_text = top_counter_text(region_counts, max_items=4)
    court_text = top_counter_text(court_counts, max_items=3)

    return f"""
      <section class="panel">
        <h2>Что показывает выборка и на что обратить внимание</h2>
        <p class="hint">Это алгоритмическое обобщение текущей подборки судебных актов, а не индивидуальная юридическая консультация.</p>
        <ul class="summary-list">
          <li><b>Требования.</b> В похожих делах чаще встречаются: {escape(top_counter_text(claim_counts, labels['claim_type_codes']))}.</li>
          <li><b>Исходы.</b> Распределение результатов в этой выборке: {escape(top_counter_text(result_counts, labels['result_type'], 3))}.</li>
          <li><b>Факторы.</b> Суд чаще обращает внимание на такие обстоятельства: {escape(factor_text)}.</li>
          <li><b>Регионы и суды.</b> Сейчас в выборке заметны регионы: {escape(region_text)}; суды: {escape(court_text)}. При расширении базы этот слой можно использовать для сравнения региональной и судебной практики.</li>
        </ul>
      </section>
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
  <a class="brand" href="../../index.html">{escape(SITE_BRAND)}</a>
  <nav>{' '.join(page_link(p, p.nav_label, current_page=page) for p in PAGES)}</nav>
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

{render_service_recommendations(cases, labels, result_counts, claim_counts, factor_items)}

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
    return html_page(page.h1, body, "../../assets/prototype.css", canonical_path=page.route)


def render_index(by_cluster: dict[str, list[dict[str, Any]]]) -> str:
    total_cases = sum(len(cases) for cases in by_cluster.values())
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
    <p class="eyebrow">Судебная практика</p>
    <h1>Первые страницы судебной практики по ЗоЗПП</h1>
    <p class="lead">Страницы-ситуации собраны из {escape(court_acts_label(total_cases))}: карточки дел, обобщающие показатели, фильтры, рекомендации по выборке и разборы конкретных историй.</p>
  </section>
  <section class="index-grid">
    {''.join(cards)}
  </section>
</main>
<footer class="site-footer">
  <p>{escape(PROTOTYPE_DISCLAIMER)}</p>
</footer>
"""
    return html_page("Судебная практика по защите прав потребителей", body, "assets/prototype.css", canonical_path="/")


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
  --content-block-padding: 38px;
  --content-block-padding-mobile: 26px;
  --card-padding: 24px;
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
  padding: var(--content-block-padding);
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
  padding: var(--card-padding);
  box-shadow: 0 10px 30px rgba(31, 41, 51, .04);
}
.panel { padding: var(--content-block-padding); }
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
.story-content p, .story-content li { max-width: none; }
.story-content .md-note { margin: 6px 0 10px 42px; padding-left: 14px; border-left: 3px solid #eadcc5; color: #3f3526; }
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
  :root { --content-block-padding: var(--content-block-padding-mobile); }
  .situation-layout, .grid.two, .index-grid, .filter-grid, .case-facts { grid-template-columns: 1fr; }
  .situation-content, .filter-sidebar { grid-column: auto; grid-row: auto; }
  .filter-sidebar { position: static; max-height: none; overflow: visible; margin-bottom: 18px; }
  .timeline li, .amount-list li { grid-template-columns: 1fr; }
  .site-header { display: block; }
  .case-card__header { display: block; }
  .result { display: inline-block; margin-top: 10px; }
}
"""
    (OUT_DIR / "assets").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "assets" / "prototype.css").write_text(css.strip() + "\n", encoding="utf-8")


def unique_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        result.append(path)
    return result


def write_seo_files(paths: list[str]) -> None:
    sitemap_urls = []
    for path in unique_paths(paths):
        url = public_url(path)
        if not url:
            continue
        sitemap_urls.append(f"  <url><loc>{escape(url)}</loc></url>")

    sitemap_xml = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            *sitemap_urls,
            "</urlset>",
            "",
        ]
    )
    (OUT_DIR / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")

    robots_lines = [
        "User-agent: *",
        "Allow: /",
    ]
    sitemap_url = public_url("/sitemap.xml")
    if sitemap_url:
        robots_lines.append(f"Sitemap: {sitemap_url}")
    (OUT_DIR / "robots.txt").write_text("\n".join(robots_lines) + "\n", encoding="utf-8")


def main() -> int:
    labels = load_enum_labels()
    _, by_cluster = load_cases()

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "praktika").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "dela").mkdir(parents=True, exist_ok=True)
    write_css()

    generated_case_pages = 0
    seo_paths = ["/"]
    for page in PAGES:
        page.output_path.parent.mkdir(parents=True, exist_ok=True)
        page.output_path.write_text(render_situation_page(page, by_cluster[page.code], labels), encoding="utf-8")
        seo_paths.append(page.route)
        for row in by_cluster[page.code]:
            docid = row["docid"]
            case_path = OUT_DIR / "dela" / docid / "index.html"
            case_path.parent.mkdir(parents=True, exist_ok=True)
            case_path.write_text(render_case_detail_page(row, page, labels), encoding="utf-8")
            seo_paths.append(case_route(docid))
            generated_case_pages += 1

    (OUT_DIR / "index.html").write_text(render_index(by_cluster), encoding="utf-8")
    write_seo_files(seo_paths)

    print(f"Сгенерировано страниц-ситуаций: {len(PAGES)}")
    print(f"Сгенерировано страниц дел: {generated_case_pages}")
    print(f"SEO: {(OUT_DIR / 'sitemap.xml').as_posix()}, {(OUT_DIR / 'robots.txt').as_posix()}")
    print(f"Индекс: {(OUT_DIR / 'index.html').as_posix()}")
    for page in PAGES:
        print(f"- {page.route} -> {page.output_path.as_posix()} ({len(by_cluster[page.code])} дел)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
