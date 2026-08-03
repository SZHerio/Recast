# M2: статический аудит веществ, форм и обходов

Build ID: `IF-M2-0001`  
Дата среза: **2 августа 2026 года**  
Платформа: **Minecraft 1.20.1, Forge 47.4.22**  
Установленный технический стек: **GTCEu Modern 7.5.3 + Create 6.0.8 + AE2 15.4.10**  
Метод: чтение конфигов, JSON-ресурсов и bytecode установленных JAR. Minecraft и GUI не запускались.

Этот отчёт фиксирует подтверждённую фактическую основу M2. Машиночитаемыми источниками истины являются реестры `docs/registries/m2_*.json`; документ объясняет принятые решения человеку.

## 1. Правило канона

Для каждого вещества разделяются четыре понятия:

1. **сущность материала** — железо, медь, вода или пар независимо от конкретного предмета;
2. **форма** — слиток, самородок, пластина, пыль, жидкость, газ или специализированное состояние;
3. **допустимый вход** — pack/Forge-тег, который рецепт может принять без потери физического смысла;
4. **канонический выход** — точный ID владельца процесса, а не случайный элемент общего тега.

Тег не назначает владельца и не создаёт бесплатную конверсию. Он только описывает допустимый вход. Специализированные формы не объединяются по совпадению элемента в названии.

## 2. Подтверждённые формы первого среза

Машиночитаемый слой шире этой сводной таблицы: `m2_substance_passports.json` содержит `14` паспортов установленного ядра и `33` концептуальные сущности последующих отраслей, а `m2_material_forms.json` — `41` точную подтверждённую форму. У всех `47` сущностей записаны источник, процессный маршрут, рецептурная политика, потребители, отходы, канонический выход, эпоха, автоматизация и русский термин. Будущие сущности не содержат выдуманных item/fluid ID.

| Сущность | Канонический стандарт | Допустимые/специализированные формы | Решение M2 |
|---|---|---|---|
| Железо | `minecraft:iron_ingot`, `minecraft:iron_nugget`, vanilla block/raw | `gtceu:iron_plate`, `gtceu:iron_dust`, `create:iron_sheet`, `create:crushed_raw_iron` | Обычные слитки/самородки/пластины принимаются pack-тегами; crushed raw не является каноническим выходом |
| Медь | `minecraft:copper_ingot`, vanilla block/raw | `gtceu:copper_nugget`, `create:copper_nugget`, `gtceu:copper_plate`, `create:copper_sheet` | Дубли форм допустимы только как стандартные входы; новый output всегда указывает владельца |
| Цинк | `gtceu:zinc_ingot` | GTCEu nugget/block/plate/foil/ring/wire; формы Create | GTCEu — владелец металлургического выхода; `gtceu:raw_zinc` не предполагается, потому что у GT Zinc нет ore property |
| Сталь | `gtceu:steel_ingot` | GTCEu nugget/block/plate и точные формы | Единственный активный владелец; самостоятельная оружейная сталь запрещена |
| Латунь | `gtceu:brass_ingot` | GTCEu plate и совместимые стандартные sheets | Состав закреплён как `Cu₃Zn`; несовместимая рецептура Create заменена |
| Золото | vanilla ingot/nugget/block/raw | `create:crushed_raw_gold`, plates | Raw-обход Create закрыт; обычные формы сохраняют vanilla alias GTCEu |
| Редстоун | `minecraft:redstone` | GTCEu рудные промежуточные формы | Основная пыль намеренно совпадает с vanilla; бонус из промывки Create закрыт вместе с raw-цепью |
| Глина | `minecraft:clay_ball`, `minecraft:clay` | `gtceu:clay_dust`, small dust, compressed/fireclay forms | Стандартная глина общая, технологические формы сохраняют роль GTCEu |
| Вода | `minecraft:water` | pack fluid-tag `industrial_frontier:materials/water` | Прямая связь подтверждена; питьевая/технологическая вода появятся отдельными состояниями в P4 |
| Пар | `gtceu:steam` | pack fluid-tag `industrial_frontier:materials/steam` | Выдуманный `forge:steam` не используется: общий Forge-тег статически не подтверждён |

Полный набор динамически создаваемых GTCEu-форм нельзя доказать архивным листингом без runtime-dump. Поэтому реестр отдельно указывает `exhaustive_for`, исключённую динамическую область и пользовательский gate; он не заявляет, что `41` запись равна всему GTCEu registry. Подтверждённые ванильные raw/storage-формы закреплены локальным неизменяемым снимком с SHA-256 источника в `authoring/m2/minecraft_1_20_1_core_forms_evidence.json`.

Для закрытия динамической части владелец выполняет штатные команды установленного KubeJS `/kubejs dump_registry minecraft:item` и `/kubejs dump_registry minecraft:fluid` по [`M2_BUILD_TEST_PROTOCOL.md`](M2_BUILD_TEST_PROTOCOL.md). Codex затем фильтрует фактические GTCEu/интеграционные ID и присваивает каждой релевантной форме статус `CANONICAL`, `ACCEPTED_INPUT`, `SPECIALIZED`, `DISABLED_DUPLICATE` либо `OUT_OF_SCOPE_WITH_REASON`. До получения вывода coverage честно остаётся `STATIC_TOUCHED_FORMS_COMPLETE_DYNAMIC_CENSUS_USER_GATE_PENDING`.

## 3. Генерация мира

Фактический baseline:

- `config/create-common.toml`: `disableWorldGen = true`;
- `config/gtceu.yaml`: `removeVanillaOreGen = true`;
- `config/gtceu.yaml`: `removeVanillaLargeOreVeins = true`.

Следовательно, GTCEu является владельцем основной установленной геологии. Это не даёт ему автоматического права на будущую нефть, планетарные минералы или реакторные месторождения: каждый новый домен проходит отдельный паспорт и config-gate.

Ресурсы Create для zinc worldgen остаются внутри JAR, но выключены конфигом. Старые чанки и ранее полученные предметы являются пользовательским runtime-риском и проверяются отдельно.

## 4. Закрытые обходы Create

### 4.1. Сырая руда

Stock-рецепты Create принимают общие `forge:raw_materials/*` и поэтому способны увидеть сырьё других доменов. Цепочка давала собственное дробление, бонусную промывку и прямой обжиг до слитка. Для iron/copper/zinc/gold промывка дополнительно создавала redstone, clay, gunpowder или quartz.

`kubejs/server_scripts/30_integrations/m2_process_ownership.js` точечно удаляет:

- top-level crushing руд и raw/raw-block для основных металлов и минералов;
- core washing `crushed_raw_{iron,copper,zinc,gold}`;
- core smelting/blasting crushed forms;
- прямые zinc smelting/blasting from ore/raw ore;
- dormant Immersive Engineering washing routes, чтобы будущая установка IE не открыла обход автоматически;
- `create:crushing/tuff` и `create:crushing/tuff_recycling`, выдававшие по `10%` gold/copper/zinc/iron nugget: второй рецепт принимал весь `#create:stone_types/tuff` и потому также являлся самостоятельным обходом.

Create не лишён роли переработки навсегда. В M3 будут добавлены курируемые маршруты `руда владельца → механический концентрат`, после чего точная очистка и металлургия продолжатся у назначенного домена. До паспорта выхода stock-мультипликация отключена.

### 4.2. Латунь

Vendor-рецепт `create:mixing/brass_ingot` задавал `1 Cu + 1 Zn → 2 Brass`, тогда как GTCEu определяет латунь как `3 Cu + 1 Zn`. Общий `forge:ingots/brass` делал эти две стехиометрии опасно взаимозаменяемыми.

M2 удаляет vendor-рецепт и добавляет:

```text
3 × #forge:ingots/copper
+ 1 × #forge:ingots/zinc
-- heated Create mixing -->
4 × gtceu:brass_ingot
```

Recipe ID: `industrial_frontier:m2/create/brass_from_copper_zinc`.

Create сохраняет наглядное массовое смешивание, GTCEu задаёт состав и канонический выход, а материальный баланс остаётся `4 → 4`.

### 4.3. Осознанно оставленные маршруты

До M3 не удаляются автоматически:

- `create:mixing/andesite_alloy` и zinc-вариант: необходим выбор раннего P1-контракта без циклической блокировки Create;
- pressing обычных iron/copper/gold/brass plates: это потенциально допустимая низкоточная роль Create, но реальные потребители и эпохи проверяются в P0–P3;
- уникальные `precision_mechanism` и `sturdy_sheet`: они принадлежат сборочному домену Create;
- M1 batch clay `4:1`: он сохраняет vanilla-стоимость и сокращает только интерфейсные действия.

Каждый пункт имеет статус `REVIEW_M3`, а не молчаливое вечное разрешение.

## 5. Закрытый ранний вход AE2

Проектный контракт открывает AE2 в P5, но vendor-рецепты позволяли начать домен на обычном iron/copper. При `nativeEUToFE: true` ранний Energy Acceptor также создавал прямой путь GT EU → AE network.

`kubejs/server_scripts/10_progression/m2_ae2_epoch_gate.js` удаляет семь корневых рецептов:

- Charger;
- Inscriber;
- Energy Acceptor;
- fluix crystal transformation;
- calculation, engineering и logic processors.

Это осознанная временная блокировка, а не готовая P5-прогрессия. Полные заменяющие рецепты, подробные задания и recovery-path создаются в M5 одновременно. Руководство GuideME остаётся доступной справкой.

## 6. Энергетический baseline

Подтверждено `config/gtceu.yaml`:

- `nativeEUToFE: true`;
- `enableFEConverters: false`;
- GT steam имеет ID `gtceu:steam`;
- Create SU не является FE/EU и не получает конвертер в M2.

Отдельно формализованы два неэлектрических носителя:

- **процессное тепло** — локальное условие конкретной машины/рецепта, а не универсальный кабель;
- **GTCEu-пар** — вещественный теплоноситель с расходом в mB, который не равен EU/FE/AE.

Разрешены только направленные физические мосты `тепло → пар` и `пар → механическая работа` с учётом воды, расхода и будущего конденсата; они не создают скрытый универсальный энергоконвертер.

Разрешён только нативный односторонний compatibility-output EU → FE; двусторонний блок-конвертер отключён. Фактическое направление, коэффициент и отсутствие обратного FE → EU цикла остаются пользовательским runtime-gate. Тепло, вода, пар и теплоносители являются предпочтительными физическими мостами будущих доменов.

## 7. Подтверждённый API авторства

GTCEu 7.5.3 регистрирует KubeJS recipe schemas для своих machine recipe types. Статически подтверждены, среди прочих: `macerator`, `compressor`, `mixer`, `ore_washer`, `forge_hammer`, `bender`, `alloy_smelter`, `autoclave`, `extractor`, `fluid_heater`, `fluid_solidifier`, `coke_oven`, `primitive_blast_furnace`, `electric_blast_furnace`.

Подтверждённые элементы DSL: `itemInputs`, `itemOutputs`, `inputFluids`, `outputFluids`, `notConsumable`, `circuit`, `chancedOutput`, `blastFurnaceTemp`, `duration` и двухаргументный `EUt(voltage, amperage)`. Одноаргументный `EUt(value)` не считается подтверждённым для этого exact JAR.

## 8. Статическая граница доказательства

Статика подтверждает наличие IDs/ресурсов, конфиги, синтаксис и архитектурное решение. Только тест владельца подтверждает:

- фактические runtime-теги динамических GT-форм;
- удаление рецептов в JEI после полной загрузки datapack/KubeJS;
- загрузку replacement brass recipe;
- направление и коэффициент EU → FE;
- отсутствие раннего AE2-маршрута через неизвестный аддон или лут;
- поведение старого мира и уже созданных предметов.

До пользовательского протокола M2 имеет статус `STATIC_COMPLETE / USER_GATE_PENDING`, а не `ACCEPTED`.

## 9. Официальные справочные источники

- [GTCEu Modern 1.20.1: Materials & Elements](https://gregtechceu.github.io/GregTech-Modern/1.20.1/Modpacks/Materials-and-Elements/) — модель материала и генерируемых форм;
- [GTCEu Modern 1.20.1: Material Properties](https://gregtechceu.github.io/GregTech-Modern/1.20.1/Modpacks/Materials-and-Elements/Material-Properties/) — свойства, определяющие формы и автогенерацию рецептов;
- [GTCEu Modern 1.20.1: Modifying Existing Materials](https://gregtechceu.github.io/GregTech-Modern/1.20.1/Modpacks/Materials-and-Elements/Modifying-Existing-Materials/) — безопасное изменение существующих материалов;
- [GTCEu Modern 1.20.1: Adding & Removing Recipes](https://gregtechceu.github.io/GregTech-Modern/1.20.1/Modpacks/Recipes/Adding-and-Removing-Recipes/) — официальный KubeJS-маршрут удаления и замены GTCEu-рецептов;
- [KubeJS Wiki: Create, ветка 1.19.2–1.20.1](https://kubejs.com/wiki/addons/create) — синтаксис mixing/pressing/crushing и тепловых условий;
- точные CurseForge-проекты, версии, file ID и dependency-gates химического стека закреплены в [`CURSEFORGE_CHEMISTRY_AUDIT.md`](CURSEFORGE_CHEMISTRY_AUDIT.md).

Внешняя документация объясняет API, но решения по канону и балансу приняты по exact JAR текущего профиля: документация более новой версии не используется как доказательство наличия ID в `7.5.3/6.0.8/15.4.10`.
