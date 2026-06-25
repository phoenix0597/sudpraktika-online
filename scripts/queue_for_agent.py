# -*- coding: utf-8 -*-
"""Наполнение очереди обработки для ИИ-агента (Antigravity/ZCode).

После сбора актов (find_cases.py + extract_act_text.py) этот скрипт регистрирует
новые акты в data/inbox/_queue.json со статусом pending. ИИ-агент (запущенный
вручную в Antigravity или автоматически) читает _TASK.md + _queue.json,
обрабатывает pending-акты, пишет результаты в data/structured/, ставит status: done.

Принцип «почтового ящика»: Python и агент общаются через файлы-контракты,
без жёсткой программной связки. Работает с любым агентом (Antigravity, ZCode, др.).

Использование:
  py scripts/queue_for_agent.py                    # регистрирует все акты из data/raw_acts/
  py scripts/queue_for_agent.py --docid yQ8qgPoesvWJ  # только один
  py scripts/queue_for_agent.py --status           # показать статус очереди
"""
import argparse
import json
from datetime import date
from pathlib import Path

QUEUE_PATH = Path("data/inbox/_queue.json")
RAW_ACTS = Path("data/raw_acts")


def load_queue() -> dict:
    if not QUEUE_PATH.exists():
        return {"queue": []}
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def save_queue(q: dict) -> None:
    q["_last_updated"] = date.today().isoformat()
    QUEUE_PATH.write_text(
        json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def known_docids(q: dict) -> set[str]:
    return {item["docid"] for item in q.get("queue", [])}


def docid_from_filename(name: str) -> str:
    # act_<docid>.txt -> <docid>
    return name[len("act_"):-len(".txt")] if name.startswith("act_") else name


def register_all() -> int:
    q = load_queue()
    known = known_docids(q)
    added = 0
    for act_file in sorted(RAW_ACTS.glob("act_*.txt")):
        docid = docid_from_filename(act_file.name)
        if docid in known:
            continue
        q.setdefault("queue", []).append({
            "docid": docid,
            "act_path": f"data/raw_acts/{act_file.name}",
            "case_number": "",
            "vertical": "",
            "status": "pending",
            "processed_by": None,
            "processed_at": None,
            "notes": "",
        })
        added += 1
    if added:
        save_queue(q)
    return added


def show_status() -> None:
    q = load_queue()
    items = q.get("queue", [])
    pending = [i for i in items if i["status"] == "pending"]
    done = [i for i in items if i["status"] == "done"]
    print(f"Всего в очереди: {len(items)}")
    print(f"  pending (ждут обработки): {len(pending)}")
    print(f"  done (обработаны): {len(done)}")
    if pending:
        print("\nОжидают обработки:")
        for i in pending:
            print(f"  [{i['docid']}] {i.get('case_number', '?')} ({i.get('vertical', '?')})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Наполнение очереди обработки для ИИ-агента")
    ap.add_argument("--docid", default="", help="Зарегистрировать только один акт по docid")
    ap.add_argument("--status", action="store_true", help="Показать статус очереди")
    args = ap.parse_args()

    if args.status:
        show_status()
        return 0

    if args.docid:
        # Регистрация одного
        q = load_queue()
        if args.docid in known_docids(q):
            print(f"Акт {args.docid} уже в очереди")
            return 0
        q.setdefault("queue", []).append({
            "docid": args.docid,
            "act_path": f"data/raw_acts/act_{args.docid}.txt",
            "case_number": "", "vertical": "",
            "status": "pending",
            "processed_by": None, "processed_at": None, "notes": "",
        })
        save_queue(q)
        print(f"Добавлен акт {args.docid}")
        return 0

    added = register_all()
    print(f"Зарегистрировано новых актов: {added}")
    show_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
