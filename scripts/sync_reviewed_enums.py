# -*- coding: utf-8 -*-
"""Скрипт для синхронизации reviewed-разметки enum из CSV с structure_*.json."""
import csv
import json
from pathlib import Path

CSV_PATH = Path("data/review/phase1-2-enum-suggestions.reviewed.csv")
STRUCTURED_DIR = Path("data/structured")

def main():
    if not CSV_PATH.exists():
        print(f"[ERR] Файл {CSV_PATH.as_posix()} не найден")
        return 1

    updated_count = 0
    updated_docids = []

    with open(CSV_PATH, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            docid = row.get("docid")
            if not docid:
                continue

            docid = docid.strip()
            json_path = STRUCTURED_DIR / f"structure_{docid}.json"
            if not json_path.exists():
                print(f"[WARN] JSON файл для {docid} не найден: {json_path.as_posix()}")
                continue

            try:
                with open(json_path, mode="r", encoding="utf-8") as jf:
                    data = json.load(jf)
            except Exception as e:
                print(f"[ERR] Ошибка чтения {json_path.as_posix()}: {e}")
                continue

            # Инициализация/проверка разделов
            if "taxonomy" not in data:
                data["taxonomy"] = {}
            if "claims_and_result" not in data:
                data["claims_and_result"] = {}
            if "outcome" not in data["claims_and_result"]:
                data["claims_and_result"]["outcome"] = {}
            if "publication" not in data:
                data["publication"] = {}

            # Извлечение данных из CSV
            dispute_type_code = row.get("final_dispute_type_code", "").strip()
            claim_type_codes_raw = row.get("final_claim_type_codes", "").strip()
            claim_type_codes = [c.strip() for c in claim_type_codes_raw.split(";") if c.strip()]
            result_type = row.get("final_result_type", "").strip()
            platform_norm = row.get("final_platform_norm", "").strip()
            object_type_norm = row.get("final_object_type_norm", "").strip()
            index_policy = row.get("final_index_policy", "").strip()
            main_site_fit_raw = row.get("final_main_site_fit", "").strip().lower()
            main_site_fit = (main_site_fit_raw == "true")

            # Специальная логика исключения для qNPGP4ky266p
            if docid == "qNPGP4ky266p":
                dispute_type_code = "non_consumer_hold"
                claim_type_codes = ["hold"]
                result_type = "hold"
                index_policy = "hold"
                main_site_fit = False

            # Вносим или обновляем поля в JSON
            data["taxonomy"]["dispute_type_code"] = dispute_type_code
            data["taxonomy"]["claim_type_codes"] = claim_type_codes
            data["claims_and_result"]["outcome"]["result_type"] = result_type
            data["publication"]["index_policy"] = index_policy
            data["publication"]["main_site_fit"] = main_site_fit

            # Синхронизация платформы и типа объекта, если они есть
            if "platform_or_company" in data["taxonomy"]:
                data["taxonomy"]["platform_or_company"] = platform_norm
            if "object_type" in data["taxonomy"]:
                data["taxonomy"]["object_type"] = object_type_norm

            try:
                with open(json_path, mode="w", encoding="utf-8") as jf:
                    json.dump(data, jf, ensure_ascii=False, indent=2)
                updated_count += 1
                updated_docids.append(docid)
                print(f"[OK] Обновлен {json_path.name}")
            except Exception as e:
                print(f"[ERR] Ошибка записи в {json_path.as_posix()}: {e}")

    print("\n=== РЕЗУЛЬТАТЫ СИНХРОНИЗАЦИИ ===")
    print(f"Успешно обновлено JSON файлов: {updated_count}")
    print(f"Список docid: {', '.join(updated_docids)}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
