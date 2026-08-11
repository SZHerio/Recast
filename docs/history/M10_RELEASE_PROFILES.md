# M10: релизные профили Recast

Build ID: `IF-M10-0001`

Статус: `STATIC_UNTESTED`

Платформа: Minecraft `1.20.1`, Forge `47.4.22`

Этот документ задаёт четыре разные среды. Они не являются четырьмя вариантами
баланса: это четыре способа обращаться с одними и теми же файлами. Игровой
При проектировании самих профилей контент и переводы не менялись; последующая
волна `IF-RU-0001` добавлена в те же разрешённые runtime-корни и отдельный
отчёт. Minecraft и Forge не запускались.

Машиночитаемый контракт находится в
[`registries/release_files.json`](registries/release_files.json).

## 1. Неподвижные правила

1. Публичный архив строится из чистого зафиксированного worktree, а не из
   живого CurseForge-instance.
2. В `overrides` никогда не попадают сторонние JAR. Их получает CurseForge по
   паре `projectID/fileID` из `manifest.json`.
3. Миры, резервные копии, логи, crash-report, скриншоты, кэши, временные файлы,
   имена, UUID, точки карты и launcher metadata не являются частью сборки.
4. Разрешённый корень не означает «взять из него всё». Для релиза выбираются
   только Git-tracked файлы плюс явно перечисленные обязательные файлы.
5. Любое неизвестное происхождение, лишний JAR или несовпадение manifest
   останавливает экспорт. Неоднозначная лицензия принудительно оставляет файл
   manifest-only и запрещает прямое вложение; предположение не считается
   разрешением.
6. Архив не получает статус `RELEASE` до пользовательского запуска по
   протоколам M8.5/M9/M10. Статическая проверка не заменяет загрузку клиента,
   мира и multiplayer.

## 2. Профили

| Профиль | Для чего | Что входит | Что принципиально не входит |
|---|---|---|---|
| `dev` | Авторинг и статический анализ | `authoring`, `assets`, `brand_source`, `config`, `defaultconfigs`, `docs`, `kubejs`, `threat_director`, `tools`, реестры и launcher-снимок | Миры, логи, кэши и любые файлы владельца; этот профиль не публикуется |
| `owner-test` | Чистая установка для ручной проверки владельцем | Установка по manifest, затем ровно release-overrides; после теста отдельно собираются лог и требуемые скриншоты | Авторский live-instance, старые настройки, реальные миры и случайные локальные JAR |
| `release` | Публичное runtime-содержимое | Только утверждённые `config`, `defaultconfigs`, `kubejs`, README, иконка, четыре документа и два файла атрибуции шрифта | Исходники, генераторы, дизайн-файлы, JAR, сохранения и диагностика |
| `curseforge-export` | ZIP, который принимает CurseForge | В корне `manifest.json`; всё авторское runtime-содержимое — под `overrides/` | `minecraftinstance.json`, `mods`, `options.txt`, прямые JAR и локальные каталоги модов |

`owner-test` всегда создаётся как новый instance. Это предотвращает ложный
успех, когда игра незаметно использует старый конфиг, распакованный TaCZ-пак,
оставшийся resource pack или JAR, которого нет в manifest.

## 3. Публичная раскладка

Целевая структура staging-каталога:

```text
Recast-IF-M10-0001/
├── manifest.json
└── overrides/
    ├── README.md
    ├── pack_icon.png
    ├── config/
    ├── defaultconfigs/
    ├── kubejs/
    └── docs/
        ├── KNOWN_ISSUES.md
        ├── RU_LOCALIZATION_REPORT.md
        ├── M10_RELEASE_PROFILES.md
        ├── MIGRATION_NOTES_IF-M10-0001.md
        ├── THIRD_PARTY_NOTICES.md
        ├── licenses/
        │   └── CCCyrillic-MIT.txt
        └── registries/
            └── cc_terminal_font.json
```

Папка `overrides` сейчас отсутствует в рабочем instance и должна быть создана
только в отдельном staging-каталоге экспортёром. Нельзя переименовывать текущие
`config`, `defaultconfigs` или `kubejs` на месте: они являются рабочей копией.

### Разрешённые runtime-корни

- `config/` — закреплённые общие настройки, compiled FTB Quests, Paxi datapack
  и resource pack, FancyMenu и Drippy;
- `defaultconfigs/` — defaults, которые копируются в новые миры;
- `kubejs/` — рецепты, gates, Ponder, NPC presets и авторская логика;
- `README.md`, `pack_icon.png`, пять документов для игрока и два файла
  атрибуции терминального шрифта.

`docs` не берётся целиком. Исследовательские аудиты, планы, схемы авторинга и
внутренние generated-отчёты нужны разработчику, но не клиенту.

### Запрещённые данные

В экспорт не допускаются:

- `saves`, `backups`, `logs`, `crash-reports`, `screenshots`, `tmp`;
- `usercache.json`, `usernamecache.json`, `.curseclient`, `servers.dat`;
- `options.txt` и пользовательские `resourcepacks`/`shaderpacks`;
- `minecraftinstance.json`, потому что он содержит абсолютные локальные пути и
  launcher-state;
- `fancymenu_data`, `config/fancymenu/user_variables.db`, `gtceu`, `xaero`,
  локальные waypoints;
- распакованный `tacz/`: стандартный gunpack разворачивается самим модом;
- `kubejs/exported`: это диагностические census-файлы, а не runtime-вход;
- `assets`, `brand_source`, `authoring`, `tools`, `.git` и IDE/agent metadata;
- любой `mods/*.jar`, даже если лицензия кажется свободной.

## 4. CurseForge packaging

Перед сборкой ZIP выполняется такое соответствие:

```text
локальный JAR
  -> точный projectID/fileID
  -> запись manifest.json
  -> запись происхождения и hash
  -> разрешённое CurseForge-распространение
```

Файловый URL сам по себе не заменяет `projectID/fileID`. Совпавший file ID при
ошибочном project ID тоже не считается корректной записью.

Базовый аудит `IF-M9-0001` видел 133 JAR, 132 CurseForge-артефакта/metadata и
одно owner-исключение; старый `manifest.json` содержал 131 запись. M10 исправил
доказуемые дефекты этого baseline:

1. Tom's Simple Storage `378609/6418133` добавлен в manifest и source registry.
2. Project ID BlockUI исправлен `528052 -> 522992`, Domum Ornamentum
   `446069 -> 527361`, Create: Central Kitchen `628194 -> 820977`; file ID и
   локальные SHA-256 при этом не менялись.
3. Build ID manifest и source registry поднят до `IF-M10-0001`.

Открыт один source gate и действуют два fail-closed ограничения поставки:

1. CC: Tweaked `1.120.0` зарегистрирован как non-CurseForge owner exception.
   Для публичного CurseForge-only профиля это блокер: нужен разрешённый
   CurseForge-вариант совместимой пары либо отдельное решение, не маскирующее
   JAR внутри overrides.
2. CurseForge metadata помечает Easy NPC bundle
   `559312/8500463` как `allowModDistribution=false`. Он остаётся штатной
   manifest-ссылкой, а его JAR запрещён внутри overrides.
3. Неоднозначные и ограничительные license declaration не дают права класть
   JAR в архив. Текущий manifest-only профиль уже запрещает это; любой будущий
   server-pack с бинарниками потребует отдельной ручной проверки.

Новый lock-аудит строится в `generated/IF-M10-0001`; отчёт
`generated/IF-M9-0001` остаётся только историческим baseline.

## 5. Сборка staging-пакета

1. Зафиксировать build ID `IF-M10-0001` во всех релизных реестрах.
2. Убедиться, что worktree не содержит неучтённых runtime-файлов.
3. Создать новый пустой staging-каталог вне live-instance.
4. Положить в его корень новый `manifest.json`.
5. Скопировать в `overrides` только allowlist из машинного реестра.
6. Отвергнуть staging, если совпал хотя бы один `forbidden_glob`.
7. Сверить число manifest-записей с числом разрешённых сторонних файлов.
8. Построить новый source/hash/dependency audit для M10.
9. Проверить ZIP-лист до загрузки: отсутствие JAR, миров, логов и
   `minecraftinstance.json` является отдельным gate.
10. Установить ZIP в новый CurseForge-instance и передать владельцу на тест.

ZIP создаётся только после шага 9; проверка уже созданного архива не должна
быть единственным барьером против утечки личных данных.

## 6. Owner-test и возврат результатов

Владелец устанавливает экспорт как новую сборку и проверяет:

- чистую установку всех manifest-файлов;
- запуск клиента и отсутствие dependency-error;
- главное меню и загрузочные экраны;
- создание одноразового мира и загрузку копии существующего мира;
- FTB Quests, Paxi, KubeJS reload/startup, рецепты и эпохальные gates;
- одиночную игру и multiplayer-команду;
- отсутствие персональных миров, серверов, waypoints и настроек в новом
  instance.

Возвращаются `latest.log`, требуемые скриншоты и заполненный тестовый протокол.
Эти файлы остаются test-artifacts и не переносятся в следующий экспорт.

## 7. Release gate

Профиль меняется с `STATIC_UNTESTED` на релизный только когда одновременно:

- manifest, установленный модлист, project/file registry и хэши согласованы;
- owner exception CC: Tweaked устранён или получило совместимое с публичной
  политикой решение;
- license inventory соответствует lock, а direct-JAR distribution отсутствует;
- M10-валидатор не находит forbidden-файлов;
- миграция копии существующего мира и чистая установка пройдены владельцем;
- Known Issues соответствует фактической сборке;
- обязательные M10 runtime и multiplayer gates закрыты;
- отдельный поток локализации закрыл свой релизный gate.

До этого `IF-M10-0001` — имя рабочего среза, а не обещание готового релиза.
