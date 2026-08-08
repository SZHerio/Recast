#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Перевод FramedBlocks.

Мод даёт блоки-хамелеоны: снаружи каркас, внутри — вид любого другого блока.
Отсюда и русское слово: «каркасный».

Двести три названия собраны из сорока существительных и трёх десятков
определений: «Framed Adjustable Double Slab» — каркасная регулируемая двойная
плита. Поэтому переведены составляющие, а названия собираются с согласованием
по роду главного слова.

Остальные сто сорок строк — подсказки, сообщения и настройки — живой текст и
переведены вручную.

Запуск:
    python tools/translate_framedblocks.py
"""

from __future__ import annotations

import glob
import io
import json
import pathlib
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = (
    ROOT
    / "config"
    / "paxi"
    / "resourcepacks"
    / "IndustrialFrontier-Core"
    / "assets"
    / "framedblocks"
    / "lang"
    / "ru_ru.json"
)

# Главные слова названий и их род.
NOUNS = {
    "Slab": ("плита", "f"),
    "Stairs": ("ступени", "pl"),
    "Block": ("блок", "m"),
    "Cube": ("куб", "m"),
    "Panel": ("панель", "f"),
    "Pane": ("стекло", "n"),
    "Door": ("дверь", "f"),
    "Trapdoor": ("люк", "m"),
    "Fence": ("забор", "m"),
    "Gate": ("калитка", "f"),
    "Wall": ("стена", "f"),
    "Post": ("столб", "m"),
    "Pillar": ("колонна", "f"),
    "Ladder": ("лестница", "f"),
    "Sign": ("табличка", "f"),
    "Torch": ("факел", "m"),
    "Lever": ("рычаг", "m"),
    "Button": ("кнопка", "f"),
    "Chest": ("сундук", "m"),
    "Bookshelf": ("книжная полка", "f"),
    "Bars": ("решётка", "f"),
    "Lattice": ("решётчатая панель", "f"),
    "Prism": ("призма", "f"),
    "Pyramid": ("пирамида", "f"),
    "Slope": ("скос", "m"),
    "Corner": ("угол", "m"),
    "Edge": ("ребро", "n"),
    "Segment": ("сегмент", "m"),
    "Strip": ("полоса", "f"),
    "Board": ("доска", "f"),
    "Frame": ("рама", "f"),
    "Window": ("окно", "n"),
    "Tube": ("труба", "f"),
    "Pot": ("горшок", "m"),
    "Plate": ("плита", "f"),
    "Rail": ("рельс", "m"),
    "Target": ("мишень", "f"),
    "Saw": ("пила", "f"),
    "Item": ("предмет", "m"),
    "Storage": ("хранилище", "n"),
}

# Определения в четырёх родовых формах.
ADJECTIVES = {
    "Adjustable": ("регулируемый", "регулируемая", "регулируемое", "регулируемые"),
    "Double": ("двойной", "двойная", "двойное", "двойные"),
    "Half": ("половинчатый", "половинчатая", "половинчатое", "половинчатые"),
    "Small": ("малый", "малая", "малое", "малые"),
    "Large": ("большой", "большая", "большое", "большие"),
    "Mini": ("мини", "мини", "мини", "мини"),
    "Thick": ("толстый", "толстая", "толстое", "толстые"),
    "Heavy": ("тяжёлый", "тяжёлая", "тяжёлое", "тяжёлые"),
    "Light": ("лёгкий", "лёгкая", "лёгкое", "лёгкие"),
    "Flat": ("плоский", "плоская", "плоское", "плоские"),
    "Elevated": ("приподнятый", "приподнятая", "приподнятое", "приподнятые"),
    "Inner": ("внутренний", "внутренняя", "внутреннее", "внутренние"),
    "Inverse": ("обратный", "обратная", "обратное", "обратные"),
    "Inverted": ("перевёрнутый", "перевёрнутая", "перевёрнутое", "перевёрнутые"),
    "Vertical": ("вертикальный", "вертикальная", "вертикальное", "вертикальные"),
    "Horizontal": ("горизонтальный", "горизонтальная", "горизонтальное", "горизонтальные"),
    "Centered": ("центрированный", "центрированная", "центрированное", "центрированные"),
    "Divided": ("разделённый", "разделённая", "разделённое", "разделённые"),
    "Sliced": ("рассечённый", "рассечённая", "рассечённое", "рассечённые"),
    "Stacked": ("составной", "составная", "составное", "составные"),
    "Compound": ("сборный", "сборная", "сборное", "сборные"),
    "Collapsible": ("складной", "складная", "складное", "складные"),
    "Extended": ("удлинённый", "удлинённая", "удлинённое", "удлинённые"),
    "Sloped": ("наклонный", "наклонная", "наклонное", "наклонные"),
    "Threeway": ("трёхсторонний", "трёхсторонняя", "трёхстороннее", "трёхсторонние"),
    "Fancy": ("узорный", "узорная", "узорное", "узорные"),
    "Checkered": ("клетчатый", "клетчатая", "клетчатое", "клетчатые"),
    "Chiseled": ("точёный", "точёная", "точёное", "точёные"),
    "Masonry": ("кладочный", "кладочная", "кладочное", "кладочные"),
    "Secret": ("потайной", "потайная", "потайное", "потайные"),
    "Bouncy": ("пружинящий", "пружинящая", "пружинящее", "пружинящие"),
    "Glowing": ("светящийся", "светящаяся", "светящееся", "светящиеся"),
    "Glow": ("светящийся", "светящаяся", "светящееся", "светящиеся"),
    "Powered": ("активируемый", "активируемая", "активируемое", "активируемые"),
    "Weighted": ("нажимной", "нажимная", "нажимное", "нажимные"),
    "Pressure": ("нажимной", "нажимная", "нажимное", "нажимные"),
    "One-Way": ("односторонний", "односторонняя", "одностороннее", "односторонние"),
    "Copycat": ("подражающий", "подражающая", "подражающее", "подражающие"),
    "Framing": ("каркасный", "каркасная", "каркасное", "каркасные"),
    "Hanging": ("подвесной", "подвесная", "подвесное", "подвесные"),
    "Floor": ("напольный", "напольная", "напольное", "напольные"),
    "Iron": ("железный", "железная", "железное", "железные"),
    "Stone": ("каменный", "каменная", "каменное", "каменные"),
    "Obsidian": ("обсидиановый", "обсидиановая", "обсидиановое", "обсидиановые"),
    "Soul": ("душевный", "душевная", "душевное", "душевные"),
    "Redstone": ("редстоуновый", "редстоуновая", "редстоуновое", "редстоуновые"),
    "Detector": ("нажимной", "нажимная", "нажимное", "нажимные"),
    "Activator": ("активирующий", "активирующая", "активирующее", "активирующие"),
    "Flower": ("цветочный", "цветочная", "цветочное", "цветочные"),
}

GENDER_INDEX = {"m": 0, "f": 1, "n": 2, "pl": 3}

# Существительные, которые в английском стоят определением: «Slope Panel» —
# панель со скосом, «Corner Pillar» — угловая колонна. По-русски они становятся
# прилагательными.
NOUN_AS_ADJECTIVE = {
    "Slope": ("скошенный", "скошенная", "скошенное", "скошенные"),
    "Corner": ("угловой", "угловая", "угловое", "угловые"),
    "Rail": ("рельсовый", "рельсовая", "рельсовое", "рельсовые"),
    "Cube": ("кубический", "кубическая", "кубическое", "кубические"),
    "Prism": ("призматический", "призматическая", "призматическое", "призматические"),
    "Pyramid": ("пирамидальный", "пирамидальная", "пирамидальное", "пирамидальные"),
    "Wall": ("настенный", "настенная", "настенное", "настенные"),
    "Panel": ("панельный", "панельная", "панельное", "панельные"),
    "Slab": ("плитный", "плитная", "плитное", "плитные"),
    "Stairs": ("ступенчатый", "ступенчатая", "ступенчатое", "ступенчатые"),
    "Door": ("дверной", "дверная", "дверное", "дверные"),
    "Torch": ("факельный", "факельная", "факельное", "факельные"),
    "Sign": ("табличный", "табличная", "табличное", "табличные"),
    "Window": ("оконный", "оконная", "оконное", "оконные"),
    "Frame": ("рамный", "рамная", "рамное", "рамные"),
    "Post": ("столбовой", "столбовая", "столбовое", "столбовые"),
    "Pillar": ("колонный", "колонная", "колонное", "колонные"),
    "Strip": ("полосовой", "полосовая", "полосовое", "полосовые"),
    "Edge": ("рёберный", "рёберная", "рёберное", "рёберные"),
    "Segment": ("сегментный", "сегментная", "сегментное", "сегментные"),
    "Plate": ("плитный", "плитная", "плитное", "плитные"),
    "Fence": ("заборный", "заборная", "заборное", "заборные"),
    "Gate": ("калиточный", "калиточная", "калиточное", "калиточные"),
    "Bars": ("решётчатый", "решётчатая", "решётчатое", "решётчатые"),
    "Pot": ("горшечный", "горшечная", "горшечное", "горшечные"),
    "Tube": ("трубный", "трубная", "трубное", "трубные"),
    "Board": ("дощатый", "дощатая", "дощатое", "дощатые"),
    "Item": ("предметный", "предметная", "предметное", "предметные"),
    "Storage": ("складской", "складская", "складское", "складские"),
    "Ladder": ("лестничный", "лестничная", "лестничное", "лестничные"),
    "Button": ("кнопочный", "кнопочная", "кнопочное", "кнопочные"),
    "Lever": ("рычажный", "рычажная", "рычажное", "рычажные"),
    "Chest": ("сундучный", "сундучная", "сундучное", "сундучные"),
    "Target": ("мишенный", "мишенная", "мишенное", "мишенные"),
    "Saw": ("пильный", "пильная", "пильное", "пильные"),
    "Lattice": ("решётчатый", "решётчатая", "решётчатое", "решётчатые"),
}

# Уточнения в скобках.
BRACKETS = {
    "(Slab)": "(плита)",
    "(Panel)": "(панель)",
    "(Vertical)": "(вертикальный)",
    "(Horizontal)": "(горизонтальный)",
}

# Живой текст: подсказки, сообщения и настройки.
MANUAL = {
    # Четыре названия, где слово Framed стоит не в начале либо отсутствует.
    "block.framedblocks.framed_large_button": "Большая каркасная кнопка",
    "block.framedblocks.framed_large_stone_button": "Большая каркасная каменная кнопка",
    "block.framedblocks.framing_saw": "Каркасная пила",
    "block.framedblocks.powered_framing_saw": "Каркасная пила с приводом",
}



# Живой текст мода: предметы, окна, сообщения и подсказки. Переведён вручную —
# здесь механика не помогает.
LIVE_TEXT = {
    "itemGroup.framed_blocks": "Каркасные блоки",
    "framedblocks.key.categories.framedblocks": "Каркасные блоки",
    "framedblocks.key.update_cull": "Обновить кэш отсечения",

    "item.framedblocks.framed_blueprint": "Каркасный чертёж",
    "item.framedblocks.framed_hammer": "Каркасный молоток",
    "item.framedblocks.framed_key": "Каркасный ключ",
    "item.framedblocks.framed_reinforcement": "Каркасное усиление",
    "item.framedblocks.framed_screwdriver": "Каркасная отвёртка",
    "item.framedblocks.framed_wrench": "Каркасный гаечный ключ",

    "title.framedblocks.framed_chest": "Каркасный сундук",
    "title.framedblocks.framed_secret_storage": "Каркасный тайник",
    "title.framedblocks.framing_saw": "Каркасная пила",
    "title.framedblocks.powered_framing_saw": "Каркасная пила с приводом",
    "title.framedblocks.powered_saw.target_block": "Результат:",
    "title.framedblocks.sign.edit": "Изменить табличку",

    "desc.framedblocks.blueprint_block": "Блок: %s",
    "desc.framedblocks.blueprint_camo": "Облик: %s",
    "desc.framedblocks.blueprint_cant_copy": "[Каркасный чертёж] Этот блок скопировать нельзя.",
    "desc.framedblocks.blueprint_cant_place_fluid_camo": "[Каркасный чертёж] Блоки с обликом жидкости копировать нельзя.",
    "desc.framedblocks.blueprint_false": "нет",
    "desc.framedblocks.blueprint_true": "да",
    "desc.framedblocks.blueprint_illuminated": "Светится: %s",
    "desc.framedblocks.blueprint_intangible": "Проницаемый: %s",
    "desc.framedblocks.blueprint_invalid": "Не подходит",
    "desc.framedblocks.blueprint_missing_materials": "[Каркасный чертёж] Не хватает материалов:",
    "desc.framedblocks.blueprint_none": "Нет",
    "desc.framedblocks.blueprint_reinforced": "Усилен: %s",
    "desc.framedblocks.slope_slab.place_upside_down": "Зажмите приседание, чтобы поставить вверх ногами",

    "msg.framedblocks.camo.blacklisted": "Этот блок нельзя использовать как облик.",
    "msg.framedblocks.camo.block_entity": "Блоки с содержимым внутрь каркасных не вставляются.",
    "msg.framedblocks.camo.non_solid": "Непрозрачные блоки без метки внутрь каркасных не вставляются.",
    "msg.framedblocks.frame_crafter.fail.incorrect_additive_0": "В первом слоте не та добавка",
    "msg.framedblocks.frame_crafter.fail.incorrect_additive_1": "Во втором слоте не та добавка",
    "msg.framedblocks.frame_crafter.fail.incorrect_additive_2": "В третьем слоте не та добавка",
    "msg.framedblocks.frame_crafter.fail.insufficient_additive_0": "В первом слоте добавки слишком мало",
    "msg.framedblocks.frame_crafter.fail.insufficient_additive_1": "Во втором слоте добавки слишком мало",
    "msg.framedblocks.frame_crafter.fail.insufficient_additive_2": "В третьем слоте добавки слишком мало",
    "msg.framedblocks.frame_crafter.fail.material_lcm": "Материала не хватает, чтобы получить целое число изделий",
    "msg.framedblocks.frame_crafter.fail.material_value": "Материала недостаточно",
    "msg.framedblocks.frame_crafter.fail.missing_additive_0": "В первом слоте нет добавки",
    "msg.framedblocks.frame_crafter.fail.missing_additive_1": "Во втором слоте нет добавки",
    "msg.framedblocks.frame_crafter.fail.missing_additive_2": "В третьем слоте нет добавки",
    "msg.framedblocks.frame_crafter.fail.output_size": "Результат не помещается в стопку",
    "msg.framedblocks.frame_crafter.fail.success": "Можно собрать",
    "msg.framedblocks.frame_crafter.fail.unexpected_additive_0": "В первом слоте лишняя добавка",
    "msg.framedblocks.frame_crafter.fail.unexpected_additive_1": "Во втором слоте лишняя добавка",
    "msg.framedblocks.frame_crafter.fail.unexpected_additive_2": "В третьем слоте лишняя добавка",
    "msg.framedblocks.framing_saw.transfer.invalid_recipe": "Рецепт не подходит",
    "msg.framedblocks.framing_saw.transfer.not_implemented": "Перенос не поддерживается, предметы не будут перемещены",
    "msg.framedblocks.lock_state": "Состояние блока теперь %s",
    "msg.framedblocks.lock_state.locked": "закреплено",
    "msg.framedblocks.lock_state.unlocked": "свободно",
    "msg.framedblocks.powered_saw.status": "Состояние: ",
    "msg.framedblocks.powered_saw.status.no_match": "Рецепт не совпадает",
    "msg.framedblocks.powered_saw.status.no_recipe": "Рецепта нет",
    "msg.framedblocks.powered_saw.status.ready": "Готово",
    "msg.framedblocks.prism_offset.switch": "Ударьте каркасным молотком, чтобы сместить призму",
    "msg.framedblocks.split_line.switch": "Ударьте каркасным гаечным ключом, чтобы повернуть линию разделения",

    "tooltip.framedblocks.camo_rotation.false": "Этот облик повернуть нельзя",
    "tooltip.framedblocks.camo_rotation.true": "Этот облик можно повернуть",
    "tooltip.framedblocks.frame_bg.set_camo": "Ударьте каркасным молотком, чтобы фоном стал облик",
    "tooltip.framedblocks.frame_bg.set_leather": "Ударьте каркасным молотком, чтобы фоном стала кожа",
    "tooltip.framedblocks.frame_bg.use_camo": "Каркасная рамка использует облик как фон",
    "tooltip.framedblocks.frame_bg.use_leather": "Каркасная рамка использует кожу как фон",
    "tooltip.framedblocks.framing_saw.have_item_none": "нет",
    "tooltip.framedblocks.framing_saw.have_x_but_need_y_item": "Есть %s, нужно %s",
    "tooltip.framedblocks.framing_saw.have_x_but_need_y_item_count": "Есть %s шт., нужно не меньше %s шт.",
    "tooltip.framedblocks.framing_saw.have_x_but_need_y_material_count": "Есть материала %s, нужно не меньше %s",
    "tooltip.framedblocks.framing_saw.have_x_but_need_y_tag": "Есть %s, нужно любое из %s",
    "tooltip.framedblocks.framing_saw.loose_additive": "Предмет собран с добавками — они будут потеряны",
    "tooltip.framedblocks.framing_saw.material": "Ценность материала: %s",
    "tooltip.framedblocks.framing_saw.output_count": "Выход: %s, максимум: %s",
    "tooltip.framedblocks.framing_saw.press_to_show": "Нажмите [%s], чтобы показать все варианты",
    "tooltip.framedblocks.is_waterloggable.false": "Блок не заполняется водой.",
    "tooltip.framedblocks.is_waterloggable.true": "Блок заполняется водой.",
    "tooltip.framedblocks.lock_state": "Состояние: %s",
    "tooltip.framedblocks.make_waterloggable.false": "Ударьте каркасным молотком, чтобы блок перестал заполняться водой",
    "tooltip.framedblocks.make_waterloggable.true": "Ударьте каркасным молотком, чтобы блок заполнялся водой",
    "tooltip.framedblocks.one_way_window.clear_face": "Ударьте каркасным ключом в приседе, чтобы убрать прозрачную сторону",
    "tooltip.framedblocks.one_way_window.curr_face": "Прозрачная сторона: %s",
    "tooltip.framedblocks.one_way_window.set_face": "Ударьте каркасным ключом, чтобы сделать прозрачной сторону: %s",
    "tooltip.framedblocks.one_way_window.dir.down": "вниз",
    "tooltip.framedblocks.one_way_window.dir.up": "вверх",
    "tooltip.framedblocks.one_way_window.dir.north": "на север",
    "tooltip.framedblocks.one_way_window.dir.south": "на юг",
    "tooltip.framedblocks.one_way_window.dir.east": "на восток",
    "tooltip.framedblocks.one_way_window.dir.west": "на запад",
    "tooltip.framedblocks.one_way_window.face.down": "низ",
    "tooltip.framedblocks.one_way_window.face.up": "верх",
    "tooltip.framedblocks.one_way_window.face.north": "север",
    "tooltip.framedblocks.one_way_window.face.south": "юг",
    "tooltip.framedblocks.one_way_window.face.east": "восток",
    "tooltip.framedblocks.one_way_window.face.west": "запад",
    "tooltip.framedblocks.one_way_window.face.none": "нет",
    "tooltip.framedblocks.one_way_window.face_abbr.down": "Н",
    "tooltip.framedblocks.one_way_window.face_abbr.up": "В",
    "tooltip.framedblocks.one_way_window.face_abbr.north": "С",
    "tooltip.framedblocks.one_way_window.face_abbr.south": "Ю",
    "tooltip.framedblocks.one_way_window.face_abbr.east": "В",
    "tooltip.framedblocks.one_way_window.face_abbr.west": "З",
    "tooltip.framedblocks.one_way_window.face_abbr.none": "—",
    "tooltip.framedblocks.powered_saw.energy": "%s / %s FE",
    "tooltip.framedblocks.powered_saw.status.no_recipe": "Рецепт не выбран: щёлкните по слоту результата любым каркасным блоком",
    "tooltip.framedblocks.prism_offset.false": "Текстура треугольника не смещена.",
    "tooltip.framedblocks.prism_offset.true": "Текстура треугольника смещена на полблока.",
    "tooltip.framedblocks.reinforce_state": "Блок %s.",
    "tooltip.framedblocks.reinforce_state.false": "не усилен",
    "tooltip.framedblocks.reinforce_state.true": "усилен",
    "tooltip.framedblocks.split_line.false": "Линия разделения идёт по крутой диагонали.",
    "tooltip.framedblocks.split_line.true": "Линия разделения идёт по пологой диагонали.",
    "tooltip.framedblocks.y_slope": "Блок использует %s грани для вертикальных скосов.",
    "tooltip.framedblocks.y_slope.horizontal": "горизонтальные",
    "tooltip.framedblocks.y_slope.vertical": "вертикальные",
    "tooltip.framedblocks.y_slope.toggle": "Ударьте каркасным ключом, чтобы переключить на %s грани",

    "config.framedblocks.client.altGhostRenderer": "Другой способ показа предпросмотра установки",
    "config.framedblocks.client.camoMessageVerbosity": "Подробность сообщений о запрещённом облике",
    "config.framedblocks.client.camoRotationMode": "Поворот облика: режим показа",
    "config.framedblocks.client.conTexMode": "Режим связанных текстур",
    "config.framedblocks.client.detailedCulling": "Подробное отсечение невидимых граней",
    "config.framedblocks.client.discreteUVSteps": "Дискретные шаги развёртки",
    "config.framedblocks.client.fancyHitboxes": "Точные области попадания",
    "config.framedblocks.client.forceAoOnGlowingBlocks": "Принудительное затенение на светящихся каркасных блоках",
    "config.framedblocks.client.itemFrameBackgroundMode": "Фон рамки: режим показа",
    "config.framedblocks.client.oneWayWindowMode": "Одностороннее окно: режим показа",
    "config.framedblocks.client.prismOffsetMode": "Смещение призмы: режим показа",
    "config.framedblocks.client.reinforcedMode": "Усиление: режим показа",
    "config.framedblocks.client.showAllRecipePermutationsInEmi": "Показывать все варианты рецептов каркасной пилы в EMI",
    "config.framedblocks.client.showButtonPlateTypeOverlay": "Показывать тип кнопки и нажимной плиты",
    "config.framedblocks.client.showGhostBlocks": "Показывать призрачные блоки",
    "config.framedblocks.client.showSpecialCubeTypeOverlay": "Показывать тип особого куба",
    "config.framedblocks.client.solidFrameMode": "Режим сплошного каркаса",
    "config.framedblocks.client.splitLineMode": "Линии разделения складных блоков: режим показа",
    "config.framedblocks.client.stateLockMode": "Закрепление состояния: режим показа",
    "config.framedblocks.client.toggleWaterlogMode": "Заполнение водой: режим показа",
    "config.framedblocks.client.toggleYSlopeMode": "Переключение вертикального скоса: режим показа",
    "config.framedblocks.common.fireproofBlocks": "Огнестойкие блоки",
    "config.framedblocks.server.allowBlockEntities": "Разрешить блоки с содержимым",
    "config.framedblocks.server.consumeCamoItem": "Расходовать предмет облика",
    "config.framedblocks.server.enableIntangibleFeature": "Включить проницаемость блоков",
    "config.framedblocks.server.glowstoneLightLevel": "Уровень света от светокамня",
    "config.framedblocks.server.intangibleMarkerItem": "Предмет-метка проницаемости",
    "config.framedblocks.server.oneWayWindowOwnable": "Одностороннее окно принадлежит владельцу",
    "config.jade.plugin_framedblocks.framed_item_frame": "Каркасная рамка",
}

def compose(value: str) -> str | None:
    """Русское название по английскому."""
    if not value.startswith("Framed "):
        return None
    words = value[len("Framed ") :].split()

    bracket = ""
    if words and words[-1] in BRACKETS:
        bracket = BRACKETS[words[-1]]
        words = words[:-1]
    if not words:
        return None

    noun_key = words[-1]
    if noun_key not in NOUNS:
        # Составные существительные: «Pressure Plate», «Fence Gate».
        if len(words) >= 2 and words[-1] in NOUNS:
            pass
        else:
            return None
    noun, gender = NOUNS[noun_key]
    index = GENDER_INDEX[gender]

    parts = []
    for word in words[:-1]:
        if word in ADJECTIVES:
            parts.append(ADJECTIVES[word][index])
        elif word in NOUN_AS_ADJECTIVE:
            parts.append(NOUN_AS_ADJECTIVE[word][index])
        else:
            return None

    base = ADJECTIVES["Framing"][index]
    name = " ".join([base] + parts + [noun])
    name = name[0].upper() + name[1:]
    return f"{name} {bracket}".strip()


def main() -> int:
    jars = glob.glob(str(ROOT / "mods" / "FramedBlocks*.jar"))
    if not jars:
        raise SystemExit("Мод FramedBlocks не найден.")
    archive = zipfile.ZipFile(jars[0])
    name = [item for item in archive.namelist() if item.endswith("lang/en_us.json")][0]
    source = json.loads(archive.read(name).decode("utf-8-sig"))

    translated = dict(MANUAL)
    translated.update(LIVE_TEXT)
    missing = []
    for key, value in source.items():
        if not key.startswith("block.framedblocks."):
            continue
        result = compose(str(value))
        if result:
            translated[key] = result
        else:
            missing.append((key, value))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUTPUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps({k: translated[k] for k in sorted(translated)}, ensure_ascii=False, indent=2) + "\n"
    )

    print(f"переведено блоков: {len(translated) - len(MANUAL)}   не собрано: {len(missing)}")
    for key, value in missing[:20]:
        print(f"    {value}")
    if len(missing) > 20:
        print(f"    … и ещё {len(missing) - 20}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
