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
import hashlib
import json
from datetime import date
from pathlib import Path

DEFAULT_QUEUE_PATH = Path("data/inbox/_queue.json")
DEFAULT_RAW_ACTS = Path("data/raw_acts")


def load_queue(queue_path: Path) -> dict:
    if not queue_path.exists():
        return {"queue": []}
    return json.loads(queue_path.read_text(encoding="utf-8"))


def save_queue(q: dict, queue_path: Path) -> None:
    q["_last_updated"] = date.today().isoformat()
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(
        json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def known_docids(q: dict) -> set[str]:
    return {item["docid"] for item in q.get("queue", [])}


def docid_from_filename(name: str) -> str:
    # act_<docid>.txt -> <docid>
    return name[len("act_"):-len(".txt")] if name.startswith("act_") else name


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_metadata_for(act_file: Path, docid: str) -> dict:
    meta_path = act_file.with_suffix(".meta.json")
    if meta_path.exists():
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        metadata = {
            "docid": docid,
            "source_url": f"https://sudact.ru/regular/doc/{docid}/",
            "source_domain": "sudact.ru",
            "source_title": None,
            "source_passage": None,
            "raw_act_path": act_file.as_posix(),
            "raw_text_sha256": sha256_file(act_file) if act_file.exists() else "",
            "source_type": "court_act",
        }
    return {
        "source_url": metadata.get("source_url"),
        "source_domain": metadata.get("source_domain"),
        "source_title": metadata.get("source_title"),
        "source_passage": metadata.get("source_passage"),
        "raw_text_sha256": metadata.get("raw_text_sha256"),
        "source_meta_path": meta_path.as_posix() if meta_path.exists() else None,
    }


def register_all(queue_path: Path, raw_dir: Path) -> int:
    q = load_queue(queue_path)
    known = known_docids(q)
    added = 0
    for act_file in sorted(raw_dir.glob("act_*.txt")):
        docid = docid_from_filename(act_file.name)
        if docid in known:
            continue
        q.setdefault("queue", []).append({
            "docid": docid,
            "act_path": act_file.as_posix(),
            **source_metadata_for(act_file, docid),
            "case_number": "",
            "vertical": "",
            "status": "pending",
            "processed_by": None,
            "processed_at": None,
            "notes": "",
        })
        added += 1
    if added:
        save_queue(q, queue_path)
    return added


def show_status(queue_path: Path) -> None:
    q = load_queue(queue_path)
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
    ap.add_argument(
        "--queue",
        default=str(DEFAULT_QUEUE_PATH),
        help="Путь к JSON-очереди. По умолчанию data/inbox/_queue.json.",
    )
    ap.add_argument(
        "--raw-dir",
        default=str(DEFAULT_RAW_ACTS),
        help="Каталог с act_<docid>.txt. По умолчанию data/raw_acts.",
    )
    args = ap.parse_args()
    queue_path = Path(args.queue)
    raw_dir = Path(args.raw_dir)

    if args.status:
        show_status(queue_path)
        return 0

    if args.docid:
        # Регистрация одного
        q = load_queue(queue_path)
        if args.docid in known_docids(q):
            print(f"Акт {args.docid} уже в очереди")
            return 0
        act_file = raw_dir / f"act_{args.docid}.txt"
        q.setdefault("queue", []).append({
            "docid": args.docid,
            "act_path": act_file.as_posix(),
            **source_metadata_for(act_file, args.docid),
            "case_number": "", "vertical": "",
            "status": "pending",
            "processed_by": None, "processed_at": None, "notes": "",
        })
        save_queue(q, queue_path)
        print(f"Добавлен акт {args.docid}")
        return 0

    added = register_all(queue_path, raw_dir)
    print(f"Зарегистрировано новых актов: {added}")
    show_status(queue_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
