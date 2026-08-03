# Recast authoring layer

Этот каталог хранит машиночитаемое намерение и трассировку. Исполняемые артефакты находятся в `kubejs/`, `config/ftbquests/quests/` и `config/paxi/`.

Источники истины:

- стабильные engine ID: `docs/registries/stable_ids.json`;
- рецепты и теги: KubeJS;
- quest graph: FTB Quests SNBT;
- статические ресурсы: Paxi;
- полные русские non-lang корпуса: Paxi + `docs/registries/non_lang_manual_backlog.json`;
- связь source → compiled → отчёт: `authoring/trace/m1_trace.json`;
- M2-паспорта, доменные контракты, энергетика, worldgen, обходы и P0–P9: `authoring/m2/registry_manifest.json` → `docs/registries/m2_*.json`;
- M2 player-facing source: `authoring/quests/70_material_passports.json` → `config/ftbquests/quests/chapters/70_material_passports.snbt`;
- M2 source → runtime → audit: `authoring/trace/m2_trace.json`;
- будущее состояние мира: Threat Director;
- Easy NPC sandbox на M1 — только неисполняемый дизайн.

Любое изменение обязательной цепочки одновременно обновляет recipe/quest ID, русский текст, английский текст, grind-audit и пользовательскую карточку.

Для `IF-M1-0001` trace schema 2 дополнительно закрепляет фактические количества: 14 квестов, 119 GuideME-страниц, 90 редакторских Alex’s Mobs-overrides и 2 страницы Citadel. `tools/lint_content.ps1` проверяет существование всех перечисленных артефактов и эти счётчики без запуска Minecraft.

Для `IF-M2-0001` pack-теги являются только допустимыми входами; output рецепта всегда указывает точный ID владельца. Любое M2-решение со статусом `GATED_NOT_INSTALLED` запрещает runtime-ID и исполняемое утверждение до exact CurseForge-файла, статического аудита и пользовательского gate. Семантику реестров проверяет `tools/validate_m2_architecture.ps1`, а `tools/lint_content.ps1` контролирует связь реестров с квестами, тегами, KubeJS и конфигами.
