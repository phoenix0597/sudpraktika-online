# -*- coding: utf-8 -*-
"""Скрипт верификации всех файлов правового анализа против исходных актов (без проблем с кодировкой консоли)."""
import argparse
import sys
from pathlib import Path

# Принудительно настраиваем UTF-8 для вывода в консоль, если поддерживается
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

scripts_dir = Path(__file__).parent
sys.path.append(str(scripts_dir))

import verify_citations

def main():
    parser = argparse.ArgumentParser(
        description="Проверка markdown-файлов правового анализа против исходных актов."
    )
    parser.add_argument(
        "--structured-dir",
        default="data/structured",
        help="Каталог с practice_<docid>.md. По умолчанию data/structured.",
    )
    parser.add_argument(
        "--raw-dir",
        default="data/raw_acts",
        help="Каталог с act_<docid>.txt. По умолчанию data/raw_acts.",
    )
    args = parser.parse_args()
    structured_dir = Path(args.structured_dir)
    raw_dir = Path(args.raw_dir)
    
    practice_files = sorted(structured_dir.glob("practice_*.md"))
    print(f"Найдено файлов для проверки: {len(practice_files)}")
    
    total_ok = 0
    total_bad_files = 0
    
    for pf in practice_files:
        docid = pf.name[len("practice_"):-3]
        act_file = raw_dir / f"act_{docid}.txt"
        
        if not act_file.exists():
            print(f"[ERR] Файл акта для {docid} не найден по пути {act_file}")
            continue
            
        act_text = act_file.read_text(encoding="utf-8")
        analysis_text = pf.read_text(encoding="utf-8")
        
        citations = verify_citations.extract_citations(analysis_text)
        if not citations:
            total_ok += 1
            continue
            
        results = verify_citations.verify(act_text, citations)
        bad_citations = [cit for cit, v in results.items() if v is False]
        
        if bad_citations:
            total_bad_files += 1
            print(f"[ERR] Файл {pf.name} содержит {len(bad_citations)} подозрительных цитат:")
            for cit in bad_citations:
                print(f"   - {cit}")
        else:
            total_ok += 1
            
    print("\n=== ИТОГИ ВЕРИФИКАЦИИ ===")
    print(f"Всего проверено файлов правового анализа: {len(practice_files)}")
    print(f"  Успешно прошли проверку (0 галлюцинаций): {total_ok}")
    print(f"  Файлов с подозрительными ссылками: {total_bad_files}")
    
    if total_bad_files > 0:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
