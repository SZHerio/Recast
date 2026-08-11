# Recast authoring layer

Этот каталог хранит машиночитаемое намерение и трассировку. Исполняемые артефакты находятся в `kubejs/`, `config/ftbquests/quests/` и `config/paxi/`.

Источники истины:

- стабильные engine ID: `docs/registries/stable_ids.json`;
- рецепты и теги: KubeJS;
- quest graph: FTB Quests SNBT;
- статические ресурсы: Paxi;
- полные русские non-lang корпуса: Paxi + `docs/registries/non_lang_manual_backlog.json`;
- связь source → compiled → отчёт: `authoring/trace/trace.json`;
- M2-паспорта, доменные контракты, энергетика, worldgen, обходы и P0–P9: `authoring/registries/registry_manifest.json` → `docs/registries/02_*.json`;
- M2 player-facing source: `authoring/quests/70_material_passports.json` → `config/ftbquests/quests/chapters/70_material_passports.snbt`;
- M2 source → runtime → audit: `authoring/trace/02_trace.json`;
- будущее состояние мира: Threat Director;
- Easy NPC sandbox на M1 — только неисполняемый дизайн.

Любое изменение обязательной цепочки одновременно обновляет recipe/quest ID, русский текст, английский текст, grind-audit и пользовательскую карточку.

Для `IF-M1-0001` trace schema 2 дополнительно закрепляет фактические количества: 14 квестов, 119 GuideME-страниц, 90 редакторских Alex’s Mobs-overrides и 2 страницы Citadel. `tools/lint_content.ps1` проверяет существование всех перечисленных артефактов и эти счётчики без запуска Minecraft.

Для `IF-M2-0001` pack-теги являются только допустимыми входами; output рецепта всегда указывает точный ID владельца. Любое M2-решение со статусом `GATED_NOT_INSTALLED` запрещает runtime-ID и исполняемое утверждение до exact CurseForge-файла, статического аудита и пользовательского gate. Семантику реестров проверяет `tools/validate_m2_architecture.ps1`, а `tools/lint_content.ps1` контролирует связь реестров с квестами, тегами, KubeJS и конфигами.

## Quest Source v2: изолированный контур

`authoring/questbook_v2/**/*.json` — русский первичный источник будущего квестбука. Формат закреплён в `authoring/schemas/quest_source_v2.schema.json`; текущий runtime-квестбук не является выходом компилятора v2 и не изменяется им.

Рабочий цикл без запуска Minecraft:

```powershell
python tools/validate_questbook_v2.py --source authoring/questbook_v2
python tools/compile_questbook_v2.py --source authoring/questbook_v2 --reports-only
python tools/compile_questbook_v2.py --source authoring/questbook_v2
python tools/validate_questbook_v2.py --source authoring/questbook_v2 --release --build build/questbook_v2
```

Первый вызов допускает честные черновики и выдаёт предупреждения по незавершённой редактуре или заблокированным доказательствам. `--reports-only` строит реестры и отчёты даже для частичного дерева, но возвращает ненулевой код при ошибках. Обычная компиляция включает release-проверку: каждый квест обязан получить состояние `RU_READY` и ровно четыре отметки `RU_PRIMARY_DRAFTED`, `RU_TECH_CHECKED`, `RU_STYLE_REVIEWED`, `RU_FLOW_REVIEWED`; заблокированные task-адаптеры не превращаются в выдуманный SNBT.

Компилятор детерминированно пишет только в `build/questbook_v2` или его подкаталоги. По умолчанию авторитетный русский текст встраивается прямо в staging-SNBT; режим `--text-mode staging-lang` создаёт отдельный staging-файл `localization/ru_ru.json`. Общий `config/paxi`, `config/ftbquests/quests`, рецепты и игра не затрагиваются.

Staging содержит главы, `chapter_groups.snbt`, стабильный v2-реестр, граф, coverage, миграционный отчёт, перечень заблокированных доказательств, evidence task-адаптеров, translation handoff, semantic-parity report и `reports/russian_editorial_corpus.md` для сквозного чтения всего русского текста в порядке книги. Он намеренно не содержит глобальный `data.snbt` и не умеет продвигать себя в runtime. Перед ручным promotion нужны завершённые P0–P9, нулевой release-error, проверенная миграция старых ID, сохранённые теги `if_commissioning_p0` … `if_commissioning_p9`, независимый просмотр diff и пользовательский игровой smoke-тест.
