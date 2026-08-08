# Third-party notices и лицензионный индекс

Build ID: `IF-M10-0001`

Статус: `STATIC_UNTESTED / MANIFEST_ONLY_CONTROLLED`

Снимок модлиста: статический аудит `IF-M10-0001`, 133 JAR

Этот файл является индексом, а не копией чужих лицензий и не юридическим
заключением. Полные тексты лицензий намеренно не дублируются: перед выпуском
проверяется первичный источник каждого проекта и конкретного файла.

## 1. Где находится полный пофайловый индекс

| Источник | Что он доказывает | Ограничение |
|---|---|---|
| `manifest.json` | Что CurseForge должен установить по `projectID/fileID` | Сейчас 132 записи; не описывает non-CurseForge исключение |
| `minecraftinstance.json` | Имя, автор, URL, project/file metadata и distribution flags установленного addon | Локальный launcher-снимок с абсолютными путями; не публикуется |
| `docs/registries/curseforge_sources.json` | Exact URL и SHA-256 ручной волны и owner exceptions | Три project ID исправлены в M10 |
| `docs/registries/generated/IF-M10-0001/mod_manifest_lock.json` | 133 имени JAR, размеры, хэши и происхождение | Текущий M10 lock; один non-CurseForge owner exception |
| `docs/registries/generated/IF-M10-0001/license_inventory.json` | License declaration, hash и source-class каждого JAR | Не заменяет юридическое толкование первичного текста |
| `META-INF/mods.toml` внутри каждого JAR | Строка `license`, объявленная самим артефактом | Декларация может быть placeholder, ссылкой или неточным названием |
| Страница конкретного файла CurseForge | Публичный файл, автор и способ доставки | Не заменяет полный текст лицензии проекта |

Индекс читается совместно. Один источник не считается достаточным для
публичного распространения.

## 2. Результат локального статического чтения лицензий

Из всех 133 JAR удалось прочитать `META-INF/mods.toml`; 133 содержат непустую
строку `license`, ошибок чтения нет. Это означает только наличие декларации.

Крупнейшие дословные группы:

| Декларация в JAR | Файлов |
|---|---:|
| `All rights reserved` с разным регистром | 33 |
| `MIT` | 26 |
| `LGPLv3` | 16 |
| `GNU Lesser General Public License v3.0` | 5 |
| `GNU LGPLv3` | 5 |
| `GNU LESSER GENERAL PUBLIC LICENSE` | 3 |
| `MIT License` | 3 |
| остальные SPDX-варианты, ссылки и custom-лицензии | 42 |

Схожие названия здесь не нормализованы намеренно. Например, `LGPLv3`,
`LGPL-3.0-only` и `LGPL-3.0-or-later` имеют разные юридические значения.

### UNKNOWN до ручной проверки

Непустая, но неинформативная строка получает статус `UNKNOWN`:

| Проект | Файл | Декларация | Почему UNKNOWN |
|---|---|---|---|
| Create Deco | `createdeco-2.0.3-1.20.1-forge.jar` | `Insert License Here` | Placeholder не задаёт условий |
| Applied Energistics 2 | `appliedenergistics2-forge-15.4.10.jar` | `See GitHub repository for details` | Нужна проверка точной лицензии tag/release |
| GuideME | `guideme-20.1.15.jar` | `See GitHub repository for details` | Нужна проверка точной лицензии tag/release |

Эти записи не разрешают direct redistribution. Они не вкладываются в архив:
CurseForge-hosted файлы доставляет сама платформа по manifest. Поэтому три
неоднозначные строки не являются отдельным блокером именно manifest-only
профиля, но блокируют любой server-pack/зеркало с JAR и требуют первичной
ссылки, даты и решения перед таким способом распространения.

## 3. Fail-closed очередь

### All Rights Reserved

33 JAR объявляют `All rights reserved`. Это не означает запрет на установку
через CurseForge, но не даёт сборке права самостоятельно вкладывать JAR в ZIP.
Единственный допустимый по умолчанию маршрут — manifest-ссылка, которую
обрабатывает CurseForge. Перенос той же сборки на другой хост требует новой
проверки разрешений.

В группе находятся, среди прочих, FTB Quests/Library/Teams, Biomes O' Plenty,
Advanced Peripherals, Aquaculture, Epic Knights, Serene Seasons, Xaero's
Minimap/World Map, Rechiseled и несколько библиотек. Полный перечень даёт
`mod_manifest_lock.json` вместе со строкой license из соответствующего JAR.

### Custom и ограничительные декларации

Отдельной проверки требуют как минимум:

| Проект | Декларация JAR | Действие |
|---|---|---|
| FancyMenu, Drippy | `DSMSLv3.1` | Только manifest до подтверждения иных прав |
| TaCZ | `GPL3 / CC BY-NC-ND 4.0` | Разделить условия кода и assets/gunpack; не переупаковывать `tacz/` |
| Just Enough Resources | non-commercial custom license | Проверить допустимость конкретного способа публикации |
| Cristel Lib | `CC BY-NC-ND 4.0` | Не модифицировать и не вкладывать напрямую |
| Handcrafted | `Terrarium Licence` | Проверить первичный текст и условия modpack distribution |
| Supplementaries | `Supplementaries Team License v.1.4` | Проверить первичный текст и attribution |
| Immersive Engineering | `Blu's License of Common Sense` | Проверить первичный текст |
| Create Big Cannons | `MIT and CC BY-NC-SA` | Разделить код/assets и выполнить attribution/share-alike, если применимо |
| CC: Tweaked 1.120.0 | `ComputerCraft Public License` | Кроме лицензии, закрыть non-CurseForge source exception |

`CC BY-NC-*`, custom и non-commercial условия нельзя автоматически приравнять
к обычной open-source-лицензии на весь JAR. Проверяется, к каким частям проекта
относится декларация.

## 4. Текущая сверка источников и manifest

После исправлений M10 сопоставление локального набора с manifest даёт:

- все 132 CurseForge-JAR представлены текущими project/file-парами manifest;
- source registry исправлен для BlockUI на `522992/7541343`, Domum Ornamentum
  на `527361/8338110`, Create: Central Kitchen на `820977/8204836`;
- Tom's Simple Storage `378609/6418133` добавлен в manifest и source registry;
- CC: Tweaked `1.120.0` остаётся owner-registered non-CurseForge exception и
  не имеет допустимой по текущей политике пары CurseForge project/file;
- Easy NPC bundle `559312/8500463` в локальной metadata имеет
  `allowModDistribution=false`; поэтому он доставляется только manifest-ссылкой
  и никогда не вкладывается как JAR.

Таким образом, старое значение «unknown provenance = 0» не равно готовности
экспорта. Оно подтверждает известность происхождения, но не полноту manifest и
не лицензионное разрешение.

## 5. Правила для публичного пакета

1. Ни один сторонний JAR не входит в `overrides`.
2. Каждый CurseForge-мод представлен точной парой project/file в manifest.
3. Имя файла, URL, размер и хэш сверяются с новым M10 lock.
4. Запись `UNKNOWN`, placeholder или ссылка «see repository» навсегда остаётся
   manifest-only, пока не проверен первичный документ; напрямую такой JAR не
   публикуется.
5. `All Rights Reserved` и custom-лицензии доставляются только штатным
   manifest-механизмом, если страница проекта допускает modpack use.
6. Флаг `allowModDistribution=false` запрещает прямое вложение независимо от
   содержимого JAR metadata.
7. Файл, доступный на CurseForge, не считается автоматически разрешённым для
   GitHub, Google Drive, собственного CDN или server-pack с JAR.
8. При обновлении file ID лицензия проверяется заново: условия могут измениться
   между версиями.
9. Если автор удалил файл или запретил распространение, release не подменяет
   его зеркалом.
10. Результат фиксируется датой, первичной URL, проверяющим и одним из статусов
    `VERIFIED_MANIFEST_ONLY`, `VERIFIED_REDISTRIBUTABLE`, `UNKNOWN`, `REJECT`.

## 6. Не-JAR материалы

### Авторские ресурсы Recast

Происхождение M9-иллюстраций, иконок и производных хранится в
`docs/registries/m9_asset_provenance.json`. Они не были скопированы из других
модпаков. Source-artwork и generated-ассеты должны сохранять свои hashes и
provenance при любом новом экспорте.

### Шрифт Lato

Шрифт Lato использовался инструментами авторинга. Локальный указатель лицензии:
`assets/fonts/Lato-OFL-1.1.txt`. Перед публикацией исходного набора проверяется,
какие TTF реально входят в распространяемый архив. Растеризованные надписи и
сам font-файл рассматриваются отдельно; если TTF поставляется, выполняются
условия OFL и сохраняется требуемое уведомление.

### Терминальный шрифт CCCyrillic

Для вывода русской справки и сообщений в CC:Tweaked используется атлас
Windows-1251 из CCCyrillic 1.0.0 автора sashafiesta. Страница проекта объявляет
лицензию MIT. Точный источник, версия и контрольные суммы записаны в
`docs/registries/cc_terminal_font.json`, а текст уведомления сохранён в
`docs/licenses/CCCyrillic-MIT.txt`.

### Локализационные overlays и руководства

Переводы строк и Markdown-руководств являются производными от текста
соответствующего мода. Их нельзя автоматически объявить авторской лицензией
Recast. Для каждого namespace сохраняется ссылка на upstream и проверяется,
разрешает ли лицензия распространение перевода. Текущая локализационная волна
добавила русские словари, руководства и SERVER_DATA-перекрытия; перед публичным
выпуском их источники и условия распространения сверяются по финальному индексу.

### Minecraft и Forge

Minecraft assets/client и Forge installer не вкладываются в modpack ZIP. Их
получает launcher по собственным каналам и условиям. Наличие версии Minecraft
или Forge в manifest не является перераспространением их бинарников сборкой.

## 7. Шаблон записи ручной проверки

```text
Project:
Project ID / File ID:
Exact file:
SHA-256:
CurseForge project URL:
CurseForge file URL:
Primary licence URL:
Licence applies to: code / assets / both / unclear
Modpack distribution terms:
Attribution required:
Checked on:
Checked by:
Status: VERIFIED_MANIFEST_ONLY / VERIFIED_REDISTRIBUTABLE / UNKNOWN / REJECT
Notes:
```

## 8. Критерий статической лицензионной приёмки

Manifest-only контроль считается выполненным, когда:

- manifest описывает каждый из 132 разрешённых CurseForge JAR;
- исправленные project ID и добавленный Tom's Simple Storage подтверждены новым
  M10 lock-аудитом;
- ambiguous/custom/ARR записи отсутствуют в `overrides` и помечены
  `VERIFIED_MANIFEST_ONLY` либо `UNKNOWN_MANIFEST_ONLY`;
- ZIP-проверка подтверждает отсутствие JAR и распакованных чужих assets;
- индекс соответствует точному M10 lock, а не историческому IF-M9-0001.

Текущий inventory выполняет эту статическую защиту: все сторонние JAR
исключены из публичного архива. Direct redistribution остаётся закрытым до
ручной проверки первичных лицензий; это отдельный способ поставки, которого в
профиле M10 нет. Non-CurseForge CC:Tweaked остаётся source-policy blocker
независимо от своей лицензии.
