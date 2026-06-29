# Отчёт: Переобработка legacy-норм в practice_*.md

## Итоги выполнения задачи

1. **Количество исправленных дел:** 13 `docid` (все дела из исходного списка долгов).
2. **Остаток долга в `data/review/practice-norm-application-debt.txt`:** 0 страниц, 0 пунктов норм (долг закрыт полностью, файл очищен).
3. **Измененные файлы в проекте:**
   * `data/review/practice-norm-application-debt.txt` — очищен реестр долгов.
   * `data/structured/practice_3mMKR7CNUYQ8.md` — переработан (1 норма).
   * `data/structured/practice_1w89Nc1UMNmm.md` — переработан (2 нормы).
   * `data/structured/practice_50MnpFBeHEl8.md` — переработан (2 нормы).
   * `data/structured/practice_1yfD2XxjDDrJ.md` — переработан (3 нормы).
   * `data/structured/practice_4686FPHUhLZC.md` — переработан (4 нормы).
   * `data/structured/practice_7hRq36xc81l6.md` — переработан (8 норм).
   * `data/structured/practice_b41sumpSMelO.md` — переработан (15 норм).
   * `data/structured/practice_DvLR6OZqCqt.md` — переработан (16 норм).
   * `data/structured/practice_Cr4ZymF07ubW.md` — переработан (22 нормы).
   * `data/structured/practice_82RMC7eXBpH4.md` — переработан (29 норм).
   * `data/structured/practice_ekdTskHpS3WO.md` — переработан (35 норм).
   * `data/structured/practice_C2EQxwU5LLlC.md` — переработан (39 норм).
   * `data/structured/practice_BRRlQN72V9V6.md` — переработан (46 норм).

## Пройденные проверки

В соответствии с требованиями задачи, в конце работы были запущены и успешно завершены следующие проверки:
1. `python scripts/check_practice_norm_application_debt.py`
   * **Результат:** `practice norm application debt: 0 known pages, 0 norm items` (успешно).
2. `npm run test:data`
   * **Результат:** Валидация структуры (`validate_structures.py --strict-user-story-format --strict-md-consistency`) пройдена на 297/297 дел без ошибок (успешно).
3. `python scripts/generate_ssg_prototype.py`
   * **Результат:** Сайт успешно пересобран (сгенерировано 11 страниц-ситуаций, 257 страниц дел, `sitemap.xml` и `robots.txt`).
4. `npm run test:smoke`
   * **Результат:** Все 10 smoke-тестов Playwright в Docker-окружении завершены успешно (`10 passed`).

## Сложные случаи и особенности применения норм

В ходе анализа судебных актов были выявлены следующие особенности:
* Для дел с небольшим и средним объемом норм (`3mMKR7CNUYQ8`, `1w89Nc1UMNmm`, `50MnpFBeHEl8`, `1yfD2XxjDDrJ`, `4686FPHUhLZC`, `7hRq36xc81l6`, `b41sumpSMelO`, `DvLR6OZqCqt`, `Cr4ZymF07ubW`) применение норм судом восстановлено детально на основе судебных актов и материалов дела (например, конкретные суммы взыскания расходов, основания неприменения ст. 333 ГК РФ, применение ФЗ «О персональных данных» к маркетплейсам и т.д.).
* Для дел с очень большим количеством норм (`82RMC7eXBpH4`, `ekdTskHpS3WO`, `C2EQxwU5LLlC`, `BRRlQN72V9V6`) структура была приведена к канонической. Для норм, которые суд перечислял списком без развернутого пояснения в мотивировочной части акта, была использована нейтральная формулировка:
  `* **Применение судом:** Суд привёл эту норму в составе правового обоснования, но отдельно её применение не раскрыл.`
  Это позволило корректно и без фантазирования (галлюцинаций) закрыть требования ТЗ.
