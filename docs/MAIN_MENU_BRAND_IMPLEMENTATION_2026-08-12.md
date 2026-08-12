# Внедрение бренда главного меню — 12 августа 2026 года

Build-контракт: `IF-M10-MENU-0002`

Статус: `IMPLEMENTED_STATIC_UNTESTED`

## 1. Результат для игрока

В главное меню внедрён утверждённый логотип `MINECRAFT / RECAST`: литейная
печь, заводской корпус и пусковая башня собраны в один знак, а траектория
заканчивается орбитальной звездой. Логотип связывает три основные темы сборки —
фабрики, города и космическую программу — и сохраняет строгую стальную палитру
с одним янтарным акцентом расплава.

Этот же горизонтальный логотип автоматически используется тремя активными
экранами загрузки FancyMenu. Из эмблемы подготовлен отдельный квадратный знак
для иконки окна, панели задач и обложки сборки.

Тёмный фон, существующая левая панель, строгие кнопки и их состояния
`normal / hover / inactive` в этой работе не заменялись. Итоговый статический
кадр находится в
[`visual_previews/recast_title_strict.png`](visual_previews/recast_title_strict.png).

## 2. Принятое художественное решение

Неизменяемым одобренным листом выбран
[`logo_minecraft_recast_semibold_study.png`](visual_previews/main_menu_concepts/logo_minecraft_recast_semibold_study.png)
с SHA-256
`BCEBE2D66BC712FF40A9351D7BB16BC3B68AC90FC841C752C1887173D0E00D57`.

Лист создан встроенным ImageGen по утверждённому направлению: `MINECRAFT` над
`RECAST`, полужирная инженерная надпись, единый знак литейного производства и
выхода на орбиту, холодная сталь и приглушённый янтарный свет на почти чёрном
фоне. Финальная подготовка не перерисовывает композицию: она только отделяет
фон, удаляет вспомогательную эмблему из листа и формирует прозрачные мастера.

## 3. Канонические исходники и runtime-ресурсы

| Роль | Путь | Формат |
|---|---|---|
| горизонтальный мастер | `brand_source/title_lockup_orbital_foundry_v3.png` | 1380×524 RGBA |
| квадратный мастер | `brand_source/orbital_foundry_mark_v3.png` | 547×524 RGBA |
| активный логотип FancyMenu | `config/fancymenu/assets/logo.png` | 1536×512 RGBA |
| активный знак FancyMenu | `config/fancymenu/assets/mark.png` | 512×512 RGBA |
| оконные иконки | `config/fancymenu/assets/icon_16.png`, `icon_32.png` | 16×16 и 32×32 RGBA |
| каноническая pack-ветка | `config/paxi/resourcepacks/IndustrialFrontier-Core/assets/industrial_frontier/textures/gui/` | logo, mark, 16/32/64/128/256 |
| обложка экземпляра | `pack_icon.png` | 256×256 RGBA |

`config/fancymenu/assets/logo.png` читается главным меню и всеми тремя
загрузочными layout-файлами. Копии `logo`, `mark`, `icon_16` и `icon_32` в
FancyMenu побайтно совпадают с одноимёнными каноническими ресурсами Paxi;
`pack_icon.png` побайтно совпадает с канонической иконкой 256×256.

## 4. Воспроизводимая пересборка

```powershell
python tools/prepare_approved_logo.py
python tools/build_menu_visuals.py --brand-only
python tools/sync_menu_provenance.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/validate_menu_visuals.ps1
```

- `prepare_approved_logo.py` детерминированно извлекает прозрачные мастера из
  утверждённого листа;
- `build_menu_visuals.py --brand-only` обновляет только logo/mark/icon в Paxi,
  FancyMenu и корневой `pack_icon.png`, не затрагивая фон и кнопки;
- `sync_menu_provenance.py` записывает актуальные SHA-256 и происхождение в
  `docs/registries/asset_provenance.json`;
- `validate_menu_visuals.ps1` проверяет размеры, режимы PNG, layout-контракты и
  соответствие provenance без запуска Minecraft.

## 5. Фактически выполненная проверка

Статическая приёмка завершилась так:

```text
[MENU][SUMMARY] errors=0 warnings=0 passes=8 layers=3 game_launched=false translations_touched=false
```

Дополнительно подтверждено:

- повторная подготовка и brand-only сборка сохранили **14 из 14** SHA-256;
- пять пар FancyMenu/Paxi и `pack_icon.png`/`icon_256.png` побайтно совпадают;
- у всех проверенных PNG есть полноценный alpha-канал с диапазоном `0…255`;
- три изменённые JSON-реестра читаются без ошибок;
- `git diff --check` не обнаружил ошибок пробелов или конфликтных маркеров;
- итоговый логотип и квадратный знак визуально проверены в исходном размере и
  в статической композиции меню.

Minecraft и FancyMenu в клиенте не запускались. Статический preview не
доказывает поведение реального layout.

## 6. Что ещё должен проверить владелец

После полного перезапуска клиента необходимо проверить:

1. главное меню при GUI scale 2, 3 и 4;
2. отсутствие обрезки `MINECRAFT / RECAST` и читаемость эмблемы;
3. три случайных экрана загрузки;
4. иконку окна и панели задач после полного перезапуска;
5. состояния кнопок, F11 и разные пропорции окна.

До этой проверки статус остаётся `IMPLEMENTED_STATIC_UNTESTED`.

Полный `validate_m9_visuals.ps1` на текущем снимке проекта не зелёный:
он показывает 16 ошибок вне цепочки пикселей логотипа — одну общую ошибку
паритета RU/EN, девять несоответствий ссылок загрузочных текстов и шесть
несоответствий квестовых иконок P4–P9. Эти ошибки не скрыты и не объявлены
закрытыми данным отчётом.
