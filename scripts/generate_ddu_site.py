# -*- coding: utf-8 -*-
"""Generate static pages for ddu-online.ru from the DDU structured corpus."""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha1
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(".")
SITE_CONFIG = ROOT / "sites/ddu/site.json"
CSS_SRC = ROOT / "site_prototype/assets/prototype.css"

DISPUTE_SLUGS = {
    "ddu_delay_penalty_art6": "prosrochka-peredachi-kvartiry",
    "ddu_pretension_claim_procedure": "pretenziya-i-isk-k-zastroyschiku",
    "ddu_termination_refund_art9": "rastorzhenie-ddu-vozvrat-deneg",
    "ddu_quality_defects_art7": "nedostatki-kvartiry",
    "ddu_acceptance_defects_art8": "priemka-kvartiry-s-nedostatkami",
    "ddu_area_price_difference_art5": "ploshchad-kvartiry-pereraschet",
    "ddu_contract_terms_validity_art4": "usloviya-ddu",
    "ddu_project_info_violation": "informatsiya-o-proekte",
    "ddu_assignment_rights_art11": "ustupka-prav-ddu",
    "ddu_escrow_dispute": "eskrou-ddu",
    "ddu_developer_bankruptcy": "bankrotstvo-zastroyschika",
}

RESULT_CSS = {
    "satisfied": "result-satisfied",
    "partially_satisfied": "result-partially_satisfied",
    "partial_satisfaction": "result-partially_satisfied",
    "rejected": "result-rejected",
    "mixed": "result-mixed",
}

AMOUNT_LABELS = {
    "penalty": "неустойка",
    "refund_paid": "возврат уплаченных денег",
    "refund": "возврат денег",
    "interest": "проценты",
    "damages": "убытки",
    "defect_cure": "устранение недостатков",
    "repair_expenses": "расходы на устранение недостатков",
    "price_reduction": "уменьшение цены",
    "contract_termination": "расторжение договора",
    "compel_transfer": "обязать передать объект",
    "area_recalculation": "перерасчёт цены из-за площади",
    "consumer_fine": "потребительский штраф 50%",
    "moral_damage": "компенсация морального вреда",
    "moral_damages": "компенсация морального вреда",
    "expenses": "судебные, экспертные и иные расходы",
    "information_disclosure": "информация по объекту",
    "escrow_refund": "возврат средств с эскроу",
    "bankruptcy_claim": "требование при банкротстве",
}


@dataclass(frozen=True)
class DduPage:
    code: str
    slug: str
    label: str
    description: str

    @property
    def route(self) -> str:
        return f"/praktika/{self.slug}/"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def public_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    clean = path.strip("/")
    if not clean:
        return base + "/"
    suffix = clean + ("/" if path.endswith("/") else "")
    return base + "/" + suffix


def css_version() -> str:
    if not CSS_SRC.exists():
        return "dev"
    return sha1(CSS_SRC.read_bytes()).hexdigest()[:10]


def inline_md(text: Any) -> str:
    value = escape(str(text or ""))
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"`(.+?)`", r"<code>\1</code>", value)
    return value


def markdown_to_html(text: str, *, skip_first_h1: bool = False) -> str:
    lines = text.splitlines()
    html: list[str] = []
    list_stack: list[int] = []
    first_h1_skipped = False

    def close_lists(to_level: int = 0) -> None:
        while len(list_stack) > to_level:
            html.append("</ul>")
            list_stack.pop()

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            close_lists()
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            close_lists()
            level = min(len(heading.group(1)) + 1, 4)
            if skip_first_h1 and not first_h1_skipped and len(heading.group(1)) == 1:
                first_h1_skipped = True
                continue
            html.append(f"<h{level}>{inline_md(heading.group(2))}</h{level}>")
            continue

        bullet = re.match(r"^(\s*)(?:[-*]|\d+\.)\s+(.+)$", raw)
        if bullet:
            indent = len(bullet.group(1).replace("\t", "    "))
            level = 1 if indent < 4 else 2
            while len(list_stack) < level:
                html.append("<ul>")
                list_stack.append(level)
            close_lists(level)
            html.append(f"<li>{inline_md(bullet.group(2).strip())}</li>")
            continue

        close_lists()
        html.append(f"<p>{inline_md(stripped)}</p>")

    close_lists()
    return "\n".join(html)


def human_count(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        word = one
    elif 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        word = few
    else:
        word = many
    return f"{n} {word}"


def money(value: Any) -> str:
    if value is None or value == "":
        return "сумма не выделена"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return escape(str(value))
    if amount.is_integer():
        return f"{int(amount):,}".replace(",", " ") + " ₽"
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",") + " ₽"


def first_sentence(text: str, limit: int = 260) -> str:
    value = re.sub(r"\s+", " ", text or "").strip()
    if not value:
        return ""
    match = re.search(r"(.+?[.!?])\s", value)
    if match and len(match.group(1)) <= limit:
        return match.group(1)
    if len(value) <= limit:
        return value
    return value[:limit].rsplit(" ", 1)[0] + "…"


def display_value(value: Any, fallback: str = "не указано") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def result_label(enum_labels: dict[str, str], result_type: str) -> str:
    return enum_labels.get(result_type) or {
        "partial_satisfaction": "требования удовлетворены частично",
        "partially_satisfied": "требования удовлетворены частично",
        "satisfied": "требования удовлетворены",
        "rejected": "в иске отказано",
        "mixed": "смешанный результат",
    }.get(result_type, result_type or "результат не выделен")


def case_title(data: dict[str, Any], page_label: str) -> str:
    taxonomy = data.get("taxonomy", {})
    obj = taxonomy.get("object_name") or taxonomy.get("object_type") or "ДДУ"
    title = f"{obj}: {page_label}"
    title = re.sub(r"\s+", " ", title).strip()
    return title[:1].upper() + title[1:]


def case_sort_key(data: dict[str, Any]) -> tuple[str, str]:
    court = data.get("court", {})
    return (str(court.get("decision_date") or ""), data.get("source", {}).get("docid", ""))


def load_site() -> tuple[dict[str, Any], dict[str, Any], dict[str, str], dict[str, str]]:
    config = read_json(SITE_CONFIG)
    enum_dict = read_json(Path(config["paths"]["enum_dictionary"]))
    fields = enum_dict.get("fields", {})

    dispute_specs = fields.get("taxonomy.dispute_type_code", {}).get("values", {})
    claim_labels = {
        code: spec.get("label", code) if isinstance(spec, dict) else str(spec)
        for code, spec in fields.get("taxonomy.claim_type_codes", {}).get("values", {}).items()
    }
    result_labels = {
        code: spec if isinstance(spec, str) else spec.get("label", code)
        for code, spec in fields.get("claims_and_result.outcome.result_type", {}).get("values", {}).items()
    }
    return config, dispute_specs, claim_labels, result_labels


def load_cases(structured_dir: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(structured_dir.glob("structure_*.json")):
        data = read_json(path)
        publication = data.get("publication", {})
        if publication.get("index_policy") != "index" or publication.get("main_site_fit") is not True:
            continue
        cases.append(data)
    return sorted(cases, key=case_sort_key, reverse=True)


def build_pages(cases: list[dict[str, Any]], dispute_specs: dict[str, Any]) -> list[DduPage]:
    counts = Counter(case.get("taxonomy", {}).get("dispute_type_code") for case in cases)
    pages: list[DduPage] = []
    for code, count in counts.most_common():
        spec = dispute_specs.get(code, {}) if isinstance(dispute_specs.get(code), dict) else {}
        label = spec.get("label", code)
        description = spec.get("description", "")
        slug = DISPUTE_SLUGS.get(code) or re.sub(r"[^a-z0-9]+", "-", code.lower()).strip("-")
        pages.append(DduPage(code, slug, label, description))
    return pages


def html_page(title: str, body: str, css_href: str, canonical: str, *, brand_href: str = "/") -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <link rel="canonical" href="{escape(canonical)}">
  <link rel="stylesheet" href="{escape(css_href)}?v={css_version()}">
</head>
<body>

<header class="site-header">
  <a class="brand" href="{escape(brand_href)}">DDU Online</a>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <p>Не является юридической консультацией. Материалы основаны на судебных актах и обработаны алгоритмом для систематизации и обобщения текущей судебной практики.</p>
</footer>

<script>
document.querySelectorAll('[data-filter]').forEach((select) => {{
  select.addEventListener('change', applyFilters);
}});
document.querySelectorAll('[data-reset-filters]').forEach((button) => {{
  button.addEventListener('click', () => {{
    document.querySelectorAll('[data-filter]').forEach((filter) => filter.value = '');
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
      return (card.dataset[field] || '').split('|').includes(filter.value);
    }});
    card.hidden = !visible;
  }});
  const counter = document.querySelector('[data-visible-count]');
  if (counter) counter.textContent = String(cards.filter((card) => !card.hidden).length);
}}
</script>
</body>
</html>
"""


def render_index(
    config: dict[str, Any],
    pages: list[DduPage],
    by_code: dict[str, list[dict[str, Any]]],
    base_url: str,
) -> str:
    total_cases = sum(len(items) for items in by_code.values())
    cards = []
    for page in pages:
        count = len(by_code[page.code])
        cards.append(
            f"""<article class="index-card">
  <p class="eyebrow">{escape(human_count(count, "судебный акт", "судебных акта", "судебных актов"))} в выборке</p>
  <h2><a href="praktika/{escape(page.slug)}/">{escape(page.label[:1].upper() + page.label[1:])}</a></h2>
  <p>{escape(page.description or "Подборка судебных актов по этой ситуации.")}</p>
  <a class="button" href="praktika/{escape(page.slug)}/">Открыть страницу</a>
</article>"""
        )
    body = f"""
  <section class="hero">
    <p class="eyebrow">Судебная практика по ДДУ</p>
    <h1>{escape(config.get("title", "Судебная практика по ДДУ"))}</h1>
    <p class="lead">Сервис систематизирует судебные акты по спорам дольщиков с застройщиками: жизненные истории, требования, результаты, применённые нормы и повторяющиеся выводы судов.</p>
    <p class="disclosure">Сейчас опубликована стартовая выборка: {escape(human_count(total_cases, "судебный акт", "судебных акта", "судебных актов"))}. Показатели являются сводкой по текущей базе проекта, а не статистикой всей судебной практики.</p>
  </section>
  <section class="index-grid">
    {"".join(cards)}
  </section>
"""
    return html_page(config.get("title", "Судебная практика по ДДУ"), body, "assets/prototype.css", public_url(base_url, "/"), brand_href="index.html")


def option_tags(values: list[str]) -> str:
    return "\n".join(f'<option value="{escape(value)}">{escape(value)}</option>' for value in values if value)


def render_case_card(data: dict[str, Any], page: DduPage, result_labels: dict[str, str], claim_labels: dict[str, str]) -> str:
    source = data.get("source", {})
    court = data.get("court", {})
    taxonomy = data.get("taxonomy", {})
    summary = data.get("case_summary", {})
    outcome = data.get("claims_and_result", {}).get("outcome", {})
    result_type = outcome.get("result_type", "")
    claims = [claim_labels.get(code, code) for code in taxonomy.get("claim_type_codes", []) if code != "hold"]
    region = display_value(court.get("region"), "")
    title = case_title(data, page.label)
    docid = source.get("docid", "")
    return f"""<article class="case-card" data-case-card data-region="{escape(region)}" data-result="{escape(result_type)}" data-claims="{escape('|'.join(claims))}">
  <div class="case-card__header">
    <div>
      <h3>{escape(title)}</h3>
      <p class="meta">{escape(region or "регион не указан")} · {escape(display_value(court.get("decision_date"), "дата не указана"))} · {escape(display_value(court.get("court_name"), "суд не указан"))}</p>
    </div>
    <span class="result {escape(RESULT_CSS.get(result_type, "result-mixed"))}">{escape(result_label(result_labels, result_type))}</span>
  </div>
  <p>{escape(first_sentence(summary.get("situation", "")))}</p>
  <div class="chips">{"".join(f'<span class="chip small">{escape(claim)}</span>' for claim in claims[:5])}</div>
  <div class="case-links">
    <a class="button" href="../../dela/{escape(docid)}/">Разобрать это дело</a>
    <a class="source-link" href="{escape(source.get("source_url", ""))}">Источник</a>
  </div>
</article>"""


def render_situation_page(
    page: DduPage,
    cases: list[dict[str, Any]],
    base_url: str,
    result_labels: dict[str, str],
    claim_labels: dict[str, str],
) -> str:
    regions = sorted({display_value(case.get("court", {}).get("region"), "") for case in cases if display_value(case.get("court", {}).get("region"), "")})
    results = sorted({case.get("claims_and_result", {}).get("outcome", {}).get("result_type", "") for case in cases if case.get("claims_and_result", {}).get("outcome", {}).get("result_type")})
    claims = sorted({
        claim_labels.get(code, code)
        for case in cases
        for code in case.get("taxonomy", {}).get("claim_type_codes", [])
        if code != "hold"
    })
    result_counts = Counter(case.get("claims_and_result", {}).get("outcome", {}).get("result_type", "") for case in cases)
    claim_counts = Counter(
        claim_labels.get(code, code)
        for case in cases
        for code in case.get("taxonomy", {}).get("claim_type_codes", [])
        if code != "hold"
    )
    cards = "\n".join(render_case_card(case, page, result_labels, claim_labels) for case in cases)
    summary = f"""
<section class="panel">
  <h2>Краткое резюме практики</h2>
  <p class="disclosure">Показатели являются сводкой по текущей выборке судебных актов.</p>
  <ul class="summary-list">
    <li>В выборке: {escape(human_count(len(cases), "судебный акт", "судебных акта", "судебных актов"))}.</li>
    <li>Результаты: {", ".join(escape(result_label(result_labels, key)) + " — " + str(count) for key, count in result_counts.items() if key) or "недостаточно данных"}.</li>
    <li>Частые требования: {", ".join(escape(name) + " — " + str(count) for name, count in claim_counts.most_common(5)) or "недостаточно данных"}.</li>
  </ul>
</section>"""
    filters = f"""
<aside class="filter-sidebar">
  <section class="panel filters">
    <h2>Фильтры по делам</h2>
    <div class="filter-grid">
      <label>Регион
        <select data-filter="region"><option value="">Все</option>{option_tags(regions)}</select>
      </label>
      <label>Результат
        <select data-filter="result"><option value="">Все</option>{"".join(f'<option value="{escape(value)}">{escape(result_label(result_labels, value))}</option>' for value in results)}</select>
      </label>
      <label>Требование
        <select data-filter="claims"><option value="">Все</option>{option_tags(claims)}</select>
      </label>
    </div>
    <div class="filter-actions"><button class="button" type="button" data-reset-filters>Сбросить фильтры</button></div>
    <p class="muted">Показано дел: <span data-visible-count>{len(cases)}</span></p>
  </section>
</aside>"""
    body = f"""
  <section class="hero">
    <p class="eyebrow">Ситуация по ДДУ</p>
    <h1>{escape(page.label[:1].upper() + page.label[1:])}</h1>
    <p class="lead">{escape(page.description or "Судебная практика по этой ситуации.")}</p>
  </section>
  <div class="situation-layout">
    <div class="situation-content">
      {summary}
      <section class="panel">
        <h2>Дела в этой выборке</h2>
        <div class="case-list" data-case-list>{cards}</div>
      </section>
    </div>
    {filters}
  </div>
"""
    return html_page(page.label[:1].upper() + page.label[1:], body, "../../assets/prototype.css", public_url(base_url, page.route), brand_href="../../index.html")


def render_amounts(items: list[dict[str, Any]], title: str) -> str:
    if not items:
        return ""
    lis = []
    for item in items:
        label = AMOUNT_LABELS.get(str(item.get("type")), str(item.get("type") or "требование"))
        lis.append(
            f"<li><span>{escape(label)}</span><strong>{money(item.get('amount'))}</strong><small>{escape(str(item.get('note') or ''))}</small></li>"
        )
    return f'<div class="amount-subpanel"><h3>{escape(title)}</h3><ul class="amount-list">{"".join(lis)}</ul></div>'


def render_timeline(timeline: Any) -> str:
    if not isinstance(timeline, list) or not timeline:
        return ""
    rows = []
    for item in timeline[:8]:
        if isinstance(item, dict):
            date = display_value(item.get("date"), "дата не указана")
            event = display_value(item.get("event"), "")
        else:
            raw = str(item)
            if ":" in raw:
                date, event = raw.split(":", 1)
            else:
                date, event = "событие", raw
        rows.append(f"<li><time>{escape(date.strip())}</time><span>{escape(event.strip())}</span></li>")
    return f'<section class="panel"><h2>Что произошло по датам</h2><ul class="timeline">{"".join(rows)}</ul></section>'


def render_case_page(
    data: dict[str, Any],
    page: DduPage,
    base_url: str,
    result_labels: dict[str, str],
) -> str:
    source = data.get("source", {})
    docid = source.get("docid", "")
    court = data.get("court", {})
    summary = data.get("case_summary", {})
    claims = data.get("claims_and_result", {})
    outcome = claims.get("outcome", {})
    amounts = claims.get("amounts", {})
    story_path = Path("data/ddu/structured") / f"user_story_{docid}.md"
    practice_path = Path("data/ddu/structured") / f"practice_{docid}.md"
    story_html = markdown_to_html(story_path.read_text(encoding="utf-8")) if story_path.exists() else ""
    practice_html = markdown_to_html(practice_path.read_text(encoding="utf-8"), skip_first_h1=True) if practice_path.exists() else ""
    title = case_title(data, page.label)
    result_type = outcome.get("result_type", "")
    timeline_html = render_timeline(summary.get("timeline"))
    claimed = render_amounts(amounts.get("items_claimed") or [], "Состав требований")
    awarded = render_amounts(amounts.get("items_awarded") or [], "Что присуждено")
    amount_block = ""
    if claimed or awarded:
        amount_block = f"""
<section class="panel">
  <h2>Что требовал дольщик</h2>
  <div class="amount-columns">{claimed}{awarded}</div>
</section>"""
    key_factors = summary.get("key_factors") or []
    takeaways = summary.get("practical_takeaways") or []
    factors_html = ""
    if key_factors or takeaways:
        factors_html = f"""
<section class="panel">
  <h2>Что важно учитывать</h2>
  <ul class="summary-list">{"".join(f'<li>{escape(str(item))}</li>' for item in key_factors[:8])}</ul>
  {('<h3>Практические выводы</h3><ul class="summary-list">' + ''.join(f'<li>{escape(str(item))}</li>' for item in takeaways[:8]) + '</ul>') if takeaways else ''}
</section>"""
    body = f"""
  <section class="hero case-hero">
    <p class="eyebrow">Разбор судебного дела · {escape(display_value(court.get("region"), "регион не указан"))} · {escape(display_value(court.get("decision_date"), "дата не указана"))}</p>
    <h1>{escape(title)}</h1>
    <p class="lead">{escape(first_sentence(summary.get("situation", "")))}</p>
    <p><span class="result {escape(RESULT_CSS.get(result_type, "result-mixed"))}">{escape(result_label(result_labels, result_type))}</span></p>
  </section>
  <section class="panel">
    <h2>История дела простым языком</h2>
    <div class="story-content">{story_html}</div>
  </section>
  <div class="grid two">{timeline_html}{amount_block}</div>
  <section class="panel">
    <h2>Что решил суд</h2>
    <p>{escape(outcome.get("short_reason") or "Итог дела выделен в структурированных данных.")}</p>
  </section>
  {factors_html}
  <section class="panel">
    <h2>Подробный правовой разбор</h2>
    <div class="story-content">{practice_html}</div>
  </section>
  <section class="panel">
    <h2>Источник</h2>
    <p><a class="button" href="{escape(source.get("source_url", ""))}">Открыть судебный акт</a></p>
  </section>
"""
    return html_page(title, body, "../../assets/prototype.css", public_url(base_url, f"/dela/{docid}/"), brand_href="../../index.html")


def render_sitemap(base_url: str, paths: list[str]) -> str:
    urls = "\n".join(f"  <url><loc>{escape(public_url(base_url, path))}</loc></url>" for path in paths)
    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        urls,
        "</urlset>",
        "",
    ])


def main() -> int:
    config, dispute_specs, claim_labels, result_labels = load_site()
    output = Path(config["paths"]["output"])
    structured_dir = Path(config["paths"]["structured"])
    base_url = str(config.get("public_url") or "https://ddu-online.ru").rstrip("/")

    cases = load_cases(structured_dir)
    pages = build_pages(cases, dispute_specs)
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    page_by_code = {page.code: page for page in pages}
    for case in cases:
        by_code[case.get("taxonomy", {}).get("dispute_type_code")].append(case)

    if output.exists():
        shutil.rmtree(output)
    (output / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(CSS_SRC, output / "assets/prototype.css")

    paths = ["/"]
    write_text(output / "index.html", render_index(config, pages, by_code, base_url))

    for page in pages:
        page_cases = by_code[page.code]
        write_text(output / "praktika" / page.slug / "index.html", render_situation_page(page, page_cases, base_url, result_labels, claim_labels))
        paths.append(page.route)
        for case in page_cases:
            docid = case.get("source", {}).get("docid", "")
            write_text(output / "dela" / docid / "index.html", render_case_page(case, page, base_url, result_labels))
            paths.append(f"/dela/{docid}/")

    write_text(output / "sitemap.xml", render_sitemap(base_url, paths))
    write_text(output / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {public_url(base_url, '/sitemap.xml')}\n")

    print(f"DDU pages generated: {output.as_posix()}")
    print(f"Cases: {len(cases)}")
    print(f"Situation pages: {len(pages)}")
    for page in pages:
        print(f"- {page.route} ({len(by_code[page.code])} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
