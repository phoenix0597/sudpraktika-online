# -*- coding: utf-8 -*-
"""Синхронизация статусов в _queue.json на основе готовых файлов в data/structured/."""
import json
from datetime import datetime
from pathlib import Path

QUEUE_PATH = Path("data/inbox/_queue.json")
STRUCTURED_DIR = Path("data/structured")

def main():
    if not QUEUE_PATH.exists():
        print(f"Ошибка: Очередь не найдена по пути {QUEUE_PATH}")
        return 1

    with QUEUE_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    queue = data.get("queue", [])
    updated = 0

    for item in queue:
        docid = item["docid"]
        # Если статус уже done, не трогаем
        if item.get("status") == "done":
            continue

        txt_json = STRUCTURED_DIR / f"structure_{docid}.json"
        txt_story = STRUCTURED_DIR / f"user_story_{docid}.md"
        txt_practice = STRUCTURED_DIR / f"practice_{docid}.md"

        if txt_json.exists() and txt_story.exists() and txt_practice.exists():
            item["status"] = "done"
            item["processed_by"] = "Antigravity Subagent"
            # Используем время последнего изменения файла структуры
            mtime = txt_json.stat().st_mtime
            item["processed_at"] = datetime.fromtimestamp(mtime).astimezone().isoformat()
            updated += 1
            print(f"Обновлен статус для {docid}: done")

    if updated:
        with QUEUE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Обновлено статусов в очереди: {updated}")
    else:
        print("Нет новых завершенных дел для синхронизации.")

    return 0

if __name__ == "__main__":
    main()
