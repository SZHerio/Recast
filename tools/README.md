# Статические инструменты Recast

Эти сценарии читают файлы профиля и **не запускают Minecraft**. Они нужны Codex перед каждым тестовым билдом и после любого изменения JAR, квестов, переводов, datapack/resource pack или KubeJS.

## `audit_instance.ps1`

Проверяет текущий профиль и пересобирает снимок `docs/registries/generated/IF-M2-0001/`:

- список и SHA-256 всех активных JAR;
- CurseForge project/file ID и допустимый CurseForge CDN URL происхождения;
- SHA-256 файлов из exact-file registry, а для записей CurseForge App — опубликованный SHA-1/MD5 из манифеста;
- `mods.toml`, включая вложенные JarJar-зависимости;
- наличие и диапазоны обязательных зависимостей;
- покрытие `ru_ru` с учётом фактического приоритета Paxi overlay над переводом внутри JAR;
- пустые значения, повреждённый UTF-8, неизвестные overlay-ключи и несовпадения format-плейсхолдеров.
- Markdown-страницы GuideME и локализуемые `.txt`-страницы книжных систем вне `lang`;
- паритет путей, тегов, ссылок, resource ID, frontmatter, разметки и отсутствие длинных строк исходного английского текста в русских страницах.
- нормализованный паритет значимых чисел в GuideME-тексте; при несовпадении отчёт сохраняет обе сигнатуры для диагностики;
- зарегистрированные смысловые исправления upstream из `docs/registries/guideme_content_corrections.json`, чтобы намеренная коррекция не маскировала случайную потерю числа.

Запуск из корня профиля:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\audit_instance.ps1
```

Ненулевой код возврата означает блокирующую ошибку источника, хэша либо зависимости. Любой ненулевой счётчик локализации остаётся релизным блокером, даже если сам audit завершился успешно; `release_gate_met` должен быть `true` в `localization_baseline.json`, `guide_content_baseline.json` и `book_content_baseline.json` перед финальным выпуском. Ручные hardcoded-строки ведутся отдельно, поскольку resource pack не может их исправить.

## `lint_content.ps1`

Проверяет авторский слой без загрузки Forge:

- корректность JSON;
- уникальность и регистрацию стабильных FTB/ресурсных ID;
- паритет ключей авторских `ru_ru` и `en_us`;
- ссылки квестов на существующие ключи;
- метаданные Paxi и обязательный тег брёвен;
- обязательные и запрещённые M1-JAR;
- запрет worldgen Create;
- синтаксис JavaScript через Node.js;
- регистрацию ID рецептов и Ponder-сцен.
- существование файлов из `authoring/trace/trace.json` и фактические количества 14 квестов, 119 GuideME-страниц, 90 Alex’s Mobs-overrides и 2 Citadel-страниц.
- 12 M2-тегов допустимых входов, конфигурационные договоры GTCEu, каноническую латунь, закрытие выбранных обходов Create и ранних корней AE2.
- структуру русской главы «Академия материалов»: 10 необязательных учебных квестов без наград и скрытого изменения прогресса.
- существование файлов из `authoring/trace/02_trace.json` и запуск отдельной семантической проверки архитектуры M2.
- локальные Markdown-ссылки во всём корпусе `docs/`, `authoring/`, `threat_director/` и `tools/`.

Запуск с закреплённым Node.js Codex:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\lint_content.ps1 -NodePath "C:\Users\SZHerio\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
```

`Errors: 0` обязателен для передачи билда владельцу. `Warnings` разбираются по одному и не замалчиваются.

## `validate_m2_architecture.ps1`

Проверяет девять машиночитаемых реестров M2 без загрузки Forge:

- соответствие manifest, JSON Schema и фактических количеств;
- глобальную уникальность ID, разрешение ссылок, evidence и gates;
- полный ациклический граф P0–P9: 21 маршрут, 51 стадия, 106 производственных рёбер `CONSUMES/PRODUCES/EMITS_WASTE`, 5 ограниченных контуров возврата и 235 dependency-рёбер с полной достижимостью вершин;
- двустороннюю проекцию стадий в граф: ребро без объявившей его стадии и стадия без ребра одинаково блокируют билд;
- бюджет возврата: контур восстановления обязан иметь потери и подпитку, контур формы возвращает вещество `1:1`, суммарный возврат за проход не превышает массы прохода;
- отсутствие исполняемых ID у будущего контента со статусом `GATED_NOT_INSTALLED`;
- отсутствие материальной прибыли в конверсиях и опасных обратных энергетических путей;
- 161 типизированный material/chemistry/food/waste/equipment concept, позиционные mappings и 20/20 fallback-контрактов;
- строительные палитры, пищевые контракты, 40 боевых профилей, B0–B6 и матрицу шести фракций по P0–P9;
- 27 loadout-архетипов и 401 role binding: классы, бюджеты, обязанности, эпохи и артиллерийский gate;
- 21 critical component ↔ 21 grind-карточку, bootstrap/automation/mass-demand и обязательное объяснение выхода за зелёные пределы.

Запуск:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\validate_m2_architecture.ps1
```

Успешный результат — `Errors: 0`. Этот валидатор проверяет архитектурные договоры, но не доказывает загрузку рецептов, тегов, квестов или конфигураций в игре.

## `generate_chapter.py`

Собирает главу книги заданий из JSON-спецификации: SNBT, оба языка, авторский источник и записи в `stable_ids.json` создаются из одного источника, поэтому паритет ключей RU/EN не может разойтись вручную.

```bash
python tools/generate_chapter.py authoring/quests/specs/71_academy_of_elements.json
```

Спецификации лежат в `authoring/quests/specs/`. Обязательные поля: `key`, `file`, `chapter_id`, `group_id`, `icon`, `tag`, заголовки на двух языках и массив `quests`, где у каждого квеста есть `slug`, координаты, иконка и блоки `ru`/`en` с `title`, `subtitle`, `desc` и `task`.

ID выводятся из `chapter_id` по формату стабильных идентификаторов: тип `3` для квеста, `4` для задачи, `5` для награды. Повторный запуск перезаписывает главу целиком и идемпотентен.

## Quest Source v2: проверка и изолированная сборка

Новая книга хранится в `authoring/questbook_v2/`. Сначала запускается строгая статическая проверка:

```powershell
python tools/validate_questbook_v2.py --source authoring/questbook_v2 --release
```

Она проверяет schema, уникальность ID и alias, DAG, переходы P0–P9, доказательства задач, миграции, охват модов и четыре русских редакторских прохода. Дополнительные контракты `QV2-OPTIONAL-CAMPAIGN-GATE` и `QV2-CITY-GATES-MAINLINE` гарантируют, что добровольная городская кампания не станет условием перехода эпохи.

После нулевого числа ошибок источник компилируется только в staging:

```powershell
python tools/compile_questbook_v2.py --source authoring/questbook_v2 --out build/questbook_v2
python tools/validate_questbook_v2.py --source authoring/questbook_v2 --build build/questbook_v2 --release
python tools/audit_quest_semantics.py --source authoring/questbook_v2 --build build/questbook_v2
```

Компилятор и семантический аудит не изменяют рабочую папку FTB Quests и не запускают Minecraft. После явного решения о выпуске сначала проверяется пакет продвижения, затем он атомарно заменяет только `chapters/` и `chapter_groups.snbt`, сохраняет `data.snbt` и создаёт восстанавливаемую копию предыдущей книги в `backups/`:

```powershell
powershell -ExecutionPolicy Bypass -File tools/promote_questbook_v2.ps1 -CheckOnly
powershell -ExecutionPolicy Bypass -File tools/promote_questbook_v2.ps1
python tools/audit_quest_semantics.py --source authoring/questbook_v2 --build build/questbook_v2 --require-runtime-sync
```

### Безопасная миграция старого прогресса

Перед выпуском Quest Source v2 миграции проверяются не только по совпадению ID, но и по замороженному исполняемому условию QR0: типу задания, предмету или тегу, количеству и дополнительным ограничениям. Предварительный запуск ничего не записывает:

```powershell
python tools/repair_quest_migration_ids.py
```

Режим `--apply` предназначен для единственной механической ротации ID после проверки отчёта:

```powershell
python tools/repair_quest_migration_ids.py --apply
```

Он переводит небезопасные переносы в `review`, выдаёт новые ID изменившимся квестам и доказательствам, сохраняет точные контракты QR0 в `docs/registries/quest_qr0_proof_contracts.json` и ставит старые ID на вечный учёт в `docs/registries/retired_ids.json`. Повторное использование retired-ID блокирует основной валидатор. Ни один из этих сценариев не запускает Minecraft.

## Аудит пользовательского запуска

`audit_launch_log.py` читает переданный `latest.log` или `.log.gz`, но не запускает Minecraft. Ошибки квестовых иконок, KubeJS, JSON-ресурсов, datapack reload и pack-owned моделей считаются блокерами. Известные сигнатуры сторонних модов выводятся отдельной категорией `EXTERNAL`, поэтому они видны, но не маскируют результат собственных файлов сборки.

```powershell
python tools/audit_launch_log.py logs/latest.log
```

Для архивного пользовательского прогона:

```powershell
python tools/audit_launch_log.py logs/2026-08-09-1.log.gz
```

Код возврата `0` означает отсутствие известных pack-owned ошибок в конкретном логе. Он не заменяет визуальную проверку меню, F11, квестовых линий и фактическое выполнение задач.

## Граница проверки

Статика не доказывает, что Forge загрузился, Paxi применил packs, FTB Quests отрисовал граф, фильтр распознал предмет, Ponder проиграл сцену или worldgen создал правильные жилы. Эти пункты проверяет только владелец по `docs/BUILD_TEST_PROTOCOL.md` и текущему `docs/M2_BUILD_TEST_PROTOCOL.md`, после чего передаёт `latest.log`, runtime registry dump и результаты `OK/FAIL`.
