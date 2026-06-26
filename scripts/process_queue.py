# -*- coding: utf-8 -*-
"""Опциональная автоматическая обработка очереди актов через DeepSeek API.

Основной масштабируемый путь для больших партий — Antigravity по контракту
data/inbox/_TASK.md. Этот скрипт оставлен как DeepSeek-вариант и при запуске
должен создавать полный комплект: user_story, practice и structure JSON.
"""
import os
import json
import time
import sys
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

# Подгружаем окружение
scripts_dir = Path(__file__).parent
load_dotenv(scripts_dir / ".env")
KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro").strip()

if not KEY:
    print("Ошибка: DEEPSEEK_API_KEY не задан в .env")
    sys.exit(1)

# Импортируем верификатор цитат
sys.path.append(str(scripts_dir))
try:
    import verify_citations
except ImportError as e:
    print(f"Не удалось импортировать verify_citations: {e}")
    verify_citations = None

QUEUE_PATH = Path("data/inbox/_queue.json")
RAW_ACTS_DIR = Path("data/raw_acts")
STRUCTURED_DIR = Path("data/structured")

def call_deepseek(prompt_template: str, act_text: str, max_tokens: int = 3000) -> str:
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json"
    }
    full_prompt = f"{prompt_template}\n\n{act_text}"
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    
    # Делаем до 3 попыток с экспоненциальным бэкоффом при ошибках сервера
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=90)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            elif r.status_code == 429:
                print(f"Превышен лимит запросов (429). Ожидание {10 * (attempt + 1)} сек...")
                time.sleep(10 * (attempt + 1))
            else:
                print(f"HTTP {r.status_code}: {r.text[:500]}")
                time.sleep(5)
        except Exception as e:
            print(f"Исключение при запросе: {e}")
            time.sleep(5)
    raise RuntimeError("Не удалось получить ответ от DeepSeek API после 3 попыток")

def clean_response(text: str) -> str:
    return text.strip()

def source_metadata_for_item(item: dict, act_path: Path) -> dict:
    meta_path = act_path.with_suffix(".meta.json")
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    docid = item["docid"]
    return {
        "docid": docid,
        "source_url": item.get("source_url") or f"https://sudact.ru/regular/doc/{docid}/",
        "source_domain": item.get("source_domain") or "sudact.ru",
        "source_title": item.get("source_title"),
        "source_passage": item.get("source_passage"),
        "raw_act_path": item.get("act_path") or act_path.as_posix(),
        "raw_text_sha256": item.get("raw_text_sha256") or "",
        "source_type": "court_act",
    }


def json_input(metadata: dict, act_text: str) -> str:
    return (
        "Технические метаданные источника:\n"
        + json.dumps(metadata, ensure_ascii=False, indent=2)
        + "\n\nТекст судебного акта:\n"
        + act_text
    )


def process_item(item: dict, prompt_user_story: str, prompt_practice: str,
                 prompt_extract: str) -> bool:
    docid = item["docid"]
    act_path = Path(item["act_path"])
    if not act_path.exists():
        # Попробуем относительный путь от корня проекта
        act_path = Path(".") / item["act_path"]
        if not act_path.exists():
            print(f"Файл акта не найден: {item['act_path']}")
            return False
            
    print(f"\n--- Обработка акта {docid} ---")
    act_text = act_path.read_text(encoding="utf-8")
    metadata = source_metadata_for_item(item, act_path)
    
    # 1. Генерация user_story
    print(f"[{docid}] Генерация user_story...")
    try:
        user_story_content = call_deepseek(prompt_user_story, act_text, max_tokens=2500)
        user_story_content = clean_response(user_story_content)
    except Exception as e:
        print(f"Ошибка при генерации user_story для {docid}: {e}")
        return False
        
    # 2. Генерация practice
    print(f"[{docid}] Генерация practice...")
    try:
        practice_content = call_deepseek(prompt_practice, act_text, max_tokens=3000)
        practice_content = clean_response(practice_content)
    except Exception as e:
        print(f"Ошибка при генерации practice для {docid}: {e}")
        return False

    # 3. Генерация structure JSON
    print(f"[{docid}] Генерация structure JSON...")
    try:
        structure_content = call_deepseek(
            prompt_extract,
            json_input(metadata, act_text),
            max_tokens=5000,
        )
        structure_content = clean_response(structure_content)
        parsed_structure = json.loads(structure_content)
        structure_content = json.dumps(parsed_structure, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при генерации structure JSON для {docid}: {e}")
        return False

    # Запись результатов
    STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)
    user_story_file = STRUCTURED_DIR / f"user_story_{docid}.md"
    practice_file = STRUCTURED_DIR / f"practice_{docid}.md"
    structure_file = STRUCTURED_DIR / f"structure_{docid}.json"
    
    user_story_file.write_text(user_story_content, encoding="utf-8")
    practice_file.write_text(practice_content, encoding="utf-8")
    structure_file.write_text(structure_content, encoding="utf-8")
    print(f"Сохранено: {user_story_file.name}, {practice_file.name}, {structure_file.name}")
    
    # Верификация цитат
    if verify_citations:
        try:
            citations = verify_citations.extract_citations(practice_content)
            if citations:
                results = verify_citations.verify(act_text, citations)
                bad = sum(1 for v in results.values() if v is False)
                partial = sum(1 for v in results.values() if v == "partial")
                print(f"Верификация: всего ссылок: {len(citations)} | ОК: {len(citations) - bad - partial} | Частично: {partial} | Галлюцинации: {bad}")
                if bad:
                    print(f"⚠️ ВНИМАНИЕ: Обнаружено {bad} подозрений на галлюцинации:")
                    for cit, v in results.items():
                        if v is False:
                            print(f"  - {cit}")
            else:
                print("Правовых ссылок в анализе не найдено.")
        except Exception as e:
            print(f"Ошибка при верификации ссылок: {e}")
            
    return True

def main():
    if not QUEUE_PATH.exists():
        print(f"Очередь не найдена: {QUEUE_PATH}")
        return 1
        
    # Чтение промптов
    prompt_user_story = (scripts_dir / "prompt_user_story.txt").read_text(encoding="utf-8")
    prompt_practice = (scripts_dir / "prompt_practice_analysis.txt").read_text(encoding="utf-8")
    prompt_extract = (scripts_dir / "prompt_extract.txt").read_text(encoding="utf-8")
    
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    queue = data.get("queue", [])
    # Сортируем или берем только те, у которых статус pending
    pending_items = [item for item in queue if item.get("status") == "pending"]
    
    print(f"Найдено {len(pending_items)} pending-актов для обработки.")
    
    success_count = 0
    for idx, item in enumerate(pending_items, 1):
        docid = item["docid"]
        print(f"\n[{idx}/{len(pending_items)}] Акт {docid}")
        
        success = process_item(item, prompt_user_story, prompt_practice, prompt_extract)
        if success:
            # Обновляем статус в памяти
            item["status"] = "done"
            item["processed_by"] = "DeepSeek API"
            item["processed_at"] = datetime.now().isoformat()
            
            # Сохраняем очередь после каждого успешного шага
            with open(QUEUE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            success_count += 1
            # Пауза перед следующим актом
            time.sleep(2)
        else:
            print(f"Пропуск акта {docid} из-за ошибки.")
            time.sleep(5)
            
    print(f"\nОбработка завершена. Успешно обработано актов: {success_count} из {len(pending_items)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
