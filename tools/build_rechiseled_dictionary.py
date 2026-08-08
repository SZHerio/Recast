#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка словаря основ Rechiseled из русских составляющих.

Шестьсот сорок названий собраны примерно из сотни слов: материал, узор и
несколько определений вроде «мелкий», «диагональный», «полированный». Здесь
переведены именно эти слова — руками, по-русски и с учётом падежей, — а
названия из них собираются по правилам.

Почему так, а не построчно. Построчный перевод шестисот названий неизбежно
разъезжается: в одном месте «плитка», в другом «плитки», в третьем
«черепица». Словарь составляющих гарантирует, что одно и то же слово везде
переведено одинаково, а падежи расставлены по одному правилу.

Материалы и узоры хранятся с двумя формами: именительной для блока и
родительной для «плита из…» и «ступени из…». Определения согласуются с родом
узора, поэтому у каждого узора род указан явно.

Что не собирается правилами — перечислено в SPECIAL и переведено вручную.

Запуск:
    python tools/build_rechiseled_dictionary.py
    python tools/translate_rechiseled.py
"""

from __future__ import annotations

import io
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DICTIONARY = ROOT / "authoring" / "lang" / "rechiseled_base.json"

# Материалы: именительный падеж множественного или единственного числа и
# родительный. Порядок слов в русском обратный английскому, поэтому материал
# почти всегда идёт после узора: «плитка из дуба», а не «дубовая плитка».
MATERIALS = {
    "Acacia Plank": ("акация", "акациевых досок"),
    "Acacia Planks": ("акация", "акациевых досок"),
    "Amethyst": ("аметист", "аметиста"),
    "Andesite": ("андезит", "андезита"),
    "Bamboo Plank": ("бамбук", "бамбуковых досок"),
    "Bamboo Planks": ("бамбук", "бамбуковых досок"),
    "Basalt": ("базальт", "базальта"),
    "Birch Plank": ("берёза", "берёзовых досок"),
    "Birch Planks": ("берёза", "берёзовых досок"),
    "Blackstone": ("чёрный камень", "чёрного камня"),
    "Blue Ice": ("синий лёд", "синего льда"),
    "Bone": ("кость", "кости"),
    "Cherry Plank": ("вишня", "вишнёвых досок"),
    "Cherry Planks": ("вишня", "вишнёвых досок"),
    "Coal": ("уголь", "угля"),
    "Cobbled Deepslate": ("булыжник из глубинного сланца", "булыжника из глубинного сланца"),
    "Cobblestone": ("булыжник", "булыжника"),
    "Copper": ("медь", "меди"),
    "Crimson Plank": ("багровые доски", "багровых досок"),
    "Crimson Planks": ("багровые доски", "багровых досок"),
    "Dark Oak Plank": ("тёмный дуб", "досок тёмного дуба"),
    "Dark Oak Planks": ("тёмный дуб", "досок тёмного дуба"),
    "Dark Prismarine": ("тёмный призмарин", "тёмного призмарина"),
    "Deepslate": ("глубинный сланец", "глубинного сланца"),
    "Diamond": ("алмаз", "алмаза"),
    "Diorite": ("диорит", "диорита"),
    "Dirt": ("земля", "земли"),
    "Emerald": ("изумруд", "изумруда"),
    "End Stone": ("камень Края", "камня Края"),
    "Exposed Copper": ("потемневшая медь", "потемневшей меди"),
    "Glowstone": ("светокамень", "светокамня"),
    "Gold": ("золото", "золота"),
    "Granite": ("гранит", "гранита"),
    "Ice": ("лёд", "льда"),
    "Iron": ("железо", "железа"),
    "Jungle Plank": ("тропическое дерево", "досок тропического дерева"),
    "Jungle Planks": ("тропическое дерево", "досок тропического дерева"),
    "Lapis Lazuli": ("лазурит", "лазурита"),
    "Mangrove Plank": ("мангровое дерево", "мангровых досок"),
    "Mangrove Planks": ("мангровое дерево", "мангровых досок"),
    "Mud": ("грязь", "грязи"),
    "Netherite": ("незерит", "незерита"),
    "Nether Brick": ("незеритовый кирпич", "незерского кирпича"),
    "Oak Plank": ("дуб", "дубовых досок"),
    "Oak Planks": ("дуб", "дубовых досок"),
    "Obsidian": ("обсидиан", "обсидиана"),
    "Oxidized Copper": ("окислившаяся медь", "окислившейся меди"),
    "Prismarine": ("призмарин", "призмарина"),
    "Purpur": ("пурпур", "пурпура"),
    "Quartz": ("кварц", "кварца"),
    "Red Nether Brick": ("красный незерский кирпич", "красного незерского кирпича"),
    "Red Sandstone": ("красный песчаник", "красного песчаника"),
    "Redstone": ("редстоун", "редстоуна"),
    "Sandstone": ("песчаник", "песчаника"),
    "Spruce Plank": ("ель", "еловых досок"),
    "Spruce Planks": ("ель", "еловых досок"),
    "Stone": ("камень", "камня"),
    "Terracotta": ("терракота", "терракоты"),
    "Tuff": ("туф", "туфа"),
    "Warped Plank": ("искажённые доски", "искажённых досок"),
    "Warped Planks": ("искажённые доски", "искажённых досок"),
    "Weathered Copper": ("выветрившаяся медь", "выветрившейся меди"),
    "Coal Block": ("угольный блок", "угольного блока"),
    "Copper Block": ("медный блок", "медного блока"),
    "Iron Block": ("железный блок", "железного блока"),
    "Gold Block": ("золотой блок", "золотого блока"),
    "Emerald Block": ("изумрудный блок", "изумрудного блока"),
    "Diamond Block": ("алмазный блок", "алмазного блока"),
    "Lapis Lazuli Block": ("лазуритовый блок", "лазуритового блока"),
    "Redstone Block": ("редстоуновый блок", "редстоунового блока"),
    "Netherite Block": ("незеритовый блок", "незеритового блока"),
    "Quartz Block": ("кварцевый блок", "кварцевого блока"),
    "Bone Block": ("костяной блок", "костяного блока"),
    "Purpur Block": ("пурпурный блок", "пурпурного блока"),
    "Nether Bricks": ("незерский кирпич", "незерского кирпича"),
    "Mossy Cobblestone": ("замшелый булыжник", "замшелого булыжника"),
    "Dark Prismarine": ("тёмный призмарин", "тёмного призмарина"),
    "Prismarine Brick": ("призмариновый кирпич", "призмаринового кирпича"),
}

# Узоры: название, родительная форма и род — род нужен, чтобы согласовать
# определения вроде «мелкий» и «диагональный».
PATTERNS = {
    "Beams": ("балки", "балок", "pl"),
    "Blobs": ("капли", "капель", "pl"),
    "Brick Pattern": ("кирпичный узор", "кирпичного узора", "m"),
    "Brick Paving": ("кирпичная мостовая", "кирпичной мостовой", "f"),
    "Bricks": ("кирпич", "кирпича", "m"),
    "Bundled": ("вязанка", "вязанки", "f"),
    "Circles": ("круги", "кругов", "pl"),
    "Clovers": ("клевер", "клевера", "m"),
    "Clumps": ("комья", "комьев", "pl"),
    "Crate": ("ящик", "ящика", "m"),
    "Crosses": ("кресты", "крестов", "pl"),
    "Cubes": ("кубики", "кубиков", "pl"),
    "Flooring": ("настил", "настила", "m"),
    "Mosaic": ("мозаика", "мозаики", "f"),
    "Pattern": ("узор", "узора", "m"),
    "Paving": ("мостовая", "мостовой", "f"),
    "Pillar": ("колонна", "колонны", "f"),
    "Scales": ("чешуя", "чешуи", "f"),
    "Squares": ("квадраты", "квадратов", "pl"),
    "Stripes": ("полосы", "полос", "pl"),
    "Tiles": ("плитка", "плитки", "f"),
    "Weave": ("плетение", "плетения", "n"),
    "Ovals": ("овалы", "овалов", "pl"),
    "Lines": ("линии", "линий", "pl"),
    "Gears": ("шестерни", "шестерён", "pl"),
    "Pipes": ("трубы", "труб", "pl"),
    "Shafts": ("валы", "валов", "pl"),
    "Rhombuses": ("ромбы", "ромбов", "pl"),
    "Grid": ("решётка", "решётки", "f"),
    "Mesh": ("сетка", "сетки", "f"),
    "Rows": ("ряды", "рядов", "pl"),
    "Fabric": ("ткань", "ткани", "f"),
    "Plating": ("обшивка", "обшивки", "f"),
    "Bars": ("прутья", "прутьев", "pl"),
    "Cone": ("конус", "конуса", "m"),
    "Ribs": ("рёбра", "рёбер", "pl"),
    "Skull": ("череп", "черепа", "m"),
    "Chunks": ("комья", "комьев", "pl"),
    "Grooves": ("борозды", "борозд", "pl"),
    "Soil": ("почва", "почвы", "f"),
    "Sheets": ("листы", "листов", "pl"),
    "Ribbons": ("ленты", "лент", "pl"),
}

# Определения. Для каждого рода своя форма.
MODIFIERS = {
    "Small": {"m": "мелкий", "f": "мелкая", "n": "мелкое", "pl": "мелкие"},
    "Large": {"m": "крупный", "f": "крупная", "n": "крупное", "pl": "крупные"},
    "Diagonal": {"m": "диагональный", "f": "диагональная", "n": "диагональное", "pl": "диагональные"},
    "Rotated": {"m": "повёрнутый", "f": "повёрнутая", "n": "повёрнутое", "pl": "повёрнутые"},
    "Bordered": {"m": "обрамлённый", "f": "обрамлённая", "n": "обрамлённое", "pl": "обрамлённые"},
    "Dotted": {"m": "точечный", "f": "точечная", "n": "точечное", "pl": "точечные"},
    "Wavy": {"m": "волнистый", "f": "волнистая", "n": "волнистое", "pl": "волнистые"},
    "Woven": {"m": "плетёный", "f": "плетёная", "n": "плетёное", "pl": "плетёные"},
    "Patterned": {"m": "узорчатый", "f": "узорчатая", "n": "узорчатое", "pl": "узорчатые"},
    "Decorated": {"m": "украшенный", "f": "украшенная", "n": "украшенное", "pl": "украшенные"},
    "Dented": {"m": "чеканный", "f": "чеканная", "n": "чеканное", "pl": "чеканные"},
    "Edged": {"m": "гранёный", "f": "гранёная", "n": "гранёное", "pl": "гранёные"},
    "Crushed": {"m": "дроблёный", "f": "дроблёная", "n": "дроблёное", "pl": "дроблёные"},
    "Compacted": {"m": "утрамбованный", "f": "утрамбованная", "n": "утрамбованное", "pl": "утрамбованные"},
}

# Родительные формы определений — для «плита из мелкой плитки».
MODIFIERS_GENITIVE = {
    "Small": {"m": "мелкого", "f": "мелкой", "n": "мелкого", "pl": "мелких"},
    "Large": {"m": "крупного", "f": "крупной", "n": "крупного", "pl": "крупных"},
    "Diagonal": {"m": "диагонального", "f": "диагональной", "n": "диагонального", "pl": "диагональных"},
    "Rotated": {"m": "повёрнутого", "f": "повёрнутой", "n": "повёрнутого", "pl": "повёрнутых"},
    "Bordered": {"m": "обрамлённого", "f": "обрамлённой", "n": "обрамлённого", "pl": "обрамлённых"},
    "Dotted": {"m": "точечного", "f": "точечной", "n": "точечного", "pl": "точечных"},
    "Wavy": {"m": "волнистого", "f": "волнистой", "n": "волнистого", "pl": "волнистых"},
    "Woven": {"m": "плетёного", "f": "плетёной", "n": "плетёного", "pl": "плетёных"},
    "Patterned": {"m": "узорчатого", "f": "узорчатой", "n": "узорчатого", "pl": "узорчатых"},
    "Decorated": {"m": "украшенного", "f": "украшенной", "n": "украшенного", "pl": "украшенных"},
    "Dented": {"m": "чеканного", "f": "чеканной", "n": "чеканного", "pl": "чеканных"},
    "Edged": {"m": "гранёного", "f": "гранёной", "n": "гранёного", "pl": "гранёных"},
    "Crushed": {"m": "дроблёного", "f": "дроблёной", "n": "дроблёного", "pl": "дроблёных"},
    "Compacted": {"m": "утрамбованного", "f": "утрамбованной", "n": "утрамбованного", "pl": "утрамбованных"},
}

# Обработка материала как определения: «Polished», «Smooth», «Cut» и подобные
# в английском стоят перед материалом и описывают именно его.
MATERIAL_STATES = {
    "Polished": ("полированный", "полированного"),
    "Smooth": ("гладкий", "гладкого"),
    "Cut": ("резной", "резного"),
    "Shiny": ("блестящий", "блестящего"),
    "Chiseled": ("точёный", "точёного"),
    "Cracked": ("потрескавшийся", "потрескавшегося"),
    "Compressed": ("прессованный", "прессованного"),
    "Carved": ("резной", "резного"),
    "Cobbled": ("колотый", "колотого"),
    "Dark": ("тёмный", "тёмного"),
    "Red": ("красный", "красного"),
}

# Названия, которые правилами не собираются.
SPECIAL = {
    "Amethyst Jewel Block": ("аметистовая друза", "аметистовой друзы"),
    "Bone Block": ("костяной блок", "костяного блока"),
    "Block of Coal": ("угольный блок", "угольного блока"),
    "Block of Copper": ("медный блок", "медного блока"),
    "Block of Diamond": ("алмазный блок", "алмазного блока"),
    "Block of Emerald": ("изумрудный блок", "изумрудного блока"),
    "Block of Gold": ("золотой блок", "золотого блока"),
    "Block of Iron": ("железный блок", "железного блока"),
    "Block of Lapis Lazuli": ("лазуритовый блок", "лазуритового блока"),
    "Block of Netherite": ("незеритовый блок", "незеритового блока"),
    "Block of Redstone": ("редстоуновый блок", "редстоунового блока"),
    "Block of Amethyst": ("аметистовый блок", "аметистового блока"),
}



# Материал как самостоятельное название: «обрамлённый базальт», «точечные
# акациевые доски». Здесь материал стоит в именительном падеже, и указан род,
# чтобы согласовать определение.
MATERIAL_NOMINATIVE = {
    "Acacia Planks": ("акациевые доски", "акациевых досок", "pl"),
    "Bamboo Planks": ("бамбуковые доски", "бамбуковых досок", "pl"),
    "Birch Planks": ("берёзовые доски", "берёзовых досок", "pl"),
    "Cherry Planks": ("вишнёвые доски", "вишнёвых досок", "pl"),
    "Crimson Planks": ("багровые доски", "багровых досок", "pl"),
    "Dark Oak Planks": ("доски тёмного дуба", "досок тёмного дуба", "pl"),
    "Jungle Planks": ("доски тропического дерева", "досок тропического дерева", "pl"),
    "Mangrove Planks": ("мангровые доски", "мангровых досок", "pl"),
    "Oak Planks": ("дубовые доски", "дубовых досок", "pl"),
    "Spruce Planks": ("еловые доски", "еловых досок", "pl"),
    "Warped Planks": ("искажённые доски", "искажённых досок", "pl"),
    "Basalt": ("базальт", "базальта", "m"),
    "Blue Ice": ("синий лёд", "синего льда", "m"),
    "Bone Block": ("костяной блок", "костяного блока", "m"),
    "Cobblestone": ("булыжник", "булыжника", "m"),
    "Deepslate": ("глубинный сланец", "глубинного сланца", "m"),
    "Dirt": ("земля", "земли", "f"),
    "End Stone": ("камень Края", "камня Края", "m"),
    "Ice": ("лёд", "льда", "m"),
    "Netherrack": ("незерак", "незерака", "m"),
    "Obsidian": ("обсидиан", "обсидиана", "m"),
    "Prismarine": ("призмарин", "призмарина", "m"),
    "Purpur": ("пурпур", "пурпура", "m"),
    "Quartz": ("кварц", "кварца", "m"),
    "Sandstone": ("песчаник", "песчаника", "m"),
    "Stone": ("камень", "камня", "m"),
    "Terracotta": ("терракота", "терракоты", "f"),
    "Tuff": ("туф", "туфа", "m"),
    "Granite": ("гранит", "гранита", "m"),
    "Diorite": ("диорит", "диорита", "m"),
    "Andesite": ("андезит", "андезита", "m"),
    "Blackstone": ("чёрный камень", "чёрного камня", "m"),
    "Mud": ("грязь", "грязи", "f"),
    "Amethyst": ("аметист", "аметиста", "m"),
    "Glowstone": ("светокамень", "светокамня", "m"),
    "Nether Bricks": ("незерский кирпич", "незерского кирпича", "m"),
    "Red Nether Bricks": ("красный незерский кирпич", "красного незерского кирпича", "m"),
    "Bricks": ("кирпич", "кирпича", "m"),
    "Sand": ("песок", "песка", "m"),
    "Red Sand": ("красный песок", "красного песка", "m"),
    "Gravel": ("гравий", "гравия", "m"),
    "Snow": ("снег", "снега", "m"),
    "Clay": ("глина", "глины", "f"),
}

# Определения, встречающиеся только здесь.
EXTRA_MODIFIERS = {
    "Inverted": {"m": "перевёрнутый", "f": "перевёрнутая", "n": "перевёрнутое", "pl": "перевёрнутые"},
    "Jagged": {"m": "зубчатый", "f": "зубчатая", "n": "зубчатое", "pl": "зубчатые"},
    "Glossy": {"m": "глянцевый", "f": "глянцевая", "n": "глянцевое", "pl": "глянцевые"},
    "Framed": {"m": "окаймлённый", "f": "окаймлённая", "n": "окаймлённое", "pl": "окаймлённые"},
    "Indented": {"m": "вдавленный", "f": "вдавленная", "n": "вдавленное", "pl": "вдавленные"},
    "Meteoric": {"m": "метеоритный", "f": "метеоритная", "n": "метеоритное", "pl": "метеоритные"},
    "Muddy": {"m": "грязный", "f": "грязная", "n": "грязное", "pl": "грязные"},
    "Dark": {"m": "тёмный", "f": "тёмная", "n": "тёмное", "pl": "тёмные"},
    "Shiny": {"m": "блестящий", "f": "блестящая", "n": "блестящее", "pl": "блестящие"},
    "Compacted": {"m": "утрамбованный", "f": "утрамбованная", "n": "утрамбованное", "pl": "утрамбованные"},
    "Crushed": {"m": "дроблёный", "f": "дроблёная", "n": "дроблёное", "pl": "дроблёные"},
    "Decorated": {"m": "украшенный", "f": "украшенная", "n": "украшенное", "pl": "украшенные"},
    "Edged": {"m": "гранёный", "f": "гранёная", "n": "гранёное", "pl": "гранёные"},
    "Bordered": {"m": "обрамлённый", "f": "обрамлённая", "n": "обрамлённое", "pl": "обрамлённые"},
    "Mossy": {"m": "замшелый", "f": "замшелая", "n": "замшелое", "pl": "замшелые"},
    "Chiseled": {"m": "точёный", "f": "точёная", "n": "точёное", "pl": "точёные"},
    "Polished": {"m": "полированный", "f": "полированная", "n": "полированное", "pl": "полированные"},
    "Smooth": {"m": "гладкий", "f": "гладкая", "n": "гладкое", "pl": "гладкие"},
    "Cracked": {"m": "потрескавшийся", "f": "потрескавшаяся", "n": "потрескавшееся", "pl": "потрескавшиеся"},
    "Cut": {"m": "резной", "f": "резная", "n": "резное", "pl": "резные"},
}
EXTRA_MODIFIERS_GENITIVE = {
    "Inverted": {"m": "перевёрнутого", "f": "перевёрнутой", "n": "перевёрнутого", "pl": "перевёрнутых"},
    "Jagged": {"m": "зубчатого", "f": "зубчатой", "n": "зубчатого", "pl": "зубчатых"},
    "Glossy": {"m": "глянцевого", "f": "глянцевой", "n": "глянцевого", "pl": "глянцевых"},
    "Framed": {"m": "окаймлённого", "f": "окаймлённой", "n": "окаймлённого", "pl": "окаймлённых"},
    "Indented": {"m": "вдавленного", "f": "вдавленной", "n": "вдавленного", "pl": "вдавленных"},
    "Meteoric": {"m": "метеоритного", "f": "метеоритной", "n": "метеоритного", "pl": "метеоритных"},
    "Muddy": {"m": "грязного", "f": "грязной", "n": "грязного", "pl": "грязных"},
    "Dark": {"m": "тёмного", "f": "тёмной", "n": "тёмного", "pl": "тёмных"},
    "Shiny": {"m": "блестящего", "f": "блестящей", "n": "блестящего", "pl": "блестящих"},
    "Compacted": {"m": "утрамбованного", "f": "утрамбованной", "n": "утрамбованного", "pl": "утрамбованных"},
    "Crushed": {"m": "дроблёного", "f": "дроблёной", "n": "дроблёного", "pl": "дроблёных"},
    "Decorated": {"m": "украшенного", "f": "украшенной", "n": "украшенного", "pl": "украшенных"},
    "Edged": {"m": "гранёного", "f": "гранёной", "n": "гранёного", "pl": "гранёных"},
    "Bordered": {"m": "обрамлённого", "f": "обрамлённой", "n": "обрамлённого", "pl": "обрамлённых"},
    "Mossy": {"m": "замшелого", "f": "замшелой", "n": "замшелого", "pl": "замшелых"},
    "Chiseled": {"m": "точёного", "f": "точёной", "n": "точёного", "pl": "точёных"},
    "Polished": {"m": "полированного", "f": "полированной", "n": "полированного", "pl": "полированных"},
    "Smooth": {"m": "гладкого", "f": "гладкой", "n": "гладкого", "pl": "гладких"},
    "Cracked": {"m": "потрескавшегося", "f": "потрескавшейся", "n": "потрескавшегося", "pl": "потрескавшихся"},
    "Cut": {"m": "резного", "f": "резной", "n": "резного", "pl": "резных"},
}


def compose_plain(name: str) -> tuple[str, str] | None:
    """Название вида «определения + материал», без узора.

    «Bordered Basalt» — обрамлённый базальт. «Dotted Acacia Planks» — точечные
    акациевые доски. Определения согласуются с родом материала.
    """
    words = name.split()
    for length in range(3, 0, -1):
        if length > len(words):
            continue
        candidate = " ".join(words[-length:])
        if candidate not in MATERIAL_NOMINATIVE:
            continue
        material_nom, material_gen, gender = MATERIAL_NOMINATIVE[candidate]
        prefix = words[: len(words) - length]
        nominative_parts, genitive_parts = [], []
        for word in prefix:
            table = MODIFIERS if word in MODIFIERS else EXTRA_MODIFIERS
            table_gen = MODIFIERS_GENITIVE if word in MODIFIERS else EXTRA_MODIFIERS_GENITIVE
            if word not in table:
                return None
            nominative_parts.append(table[word][gender])
            genitive_parts.append(table_gen[word][gender])
        if not prefix:
            return (material_nom[0].upper() + material_nom[1:], material_gen)
        head = " ".join(nominative_parts)
        tail = " ".join(genitive_parts)
        return (
            f"{head[0].upper()}{head[1:]} {material_nom}",
            f"{tail} {material_gen}",
        )
    return None


def compose(name: str) -> tuple[str, str] | None:
    """Русское название по английскому: именительная и родительная формы."""
    if name in SPECIAL:
        return SPECIAL[name]

    words = name.split()

    # «Copper Bars Block» — прутья из медного блока. Слово Block в конце
    # относится к материалу: медный блок, а не «блок прутьев».
    if words[-1] == "Block" and len(words) >= 3:
        material_key = f"{words[-3]} Block" if len(words) >= 3 else ""
        pattern_key = words[-2]
        if material_key in MATERIALS and pattern_key in PATTERNS:
            prefix_words = words[: len(words) - 3]
            material_gen = MATERIALS[material_key][1]
            pattern_nom, pattern_gen, gender = PATTERNS[pattern_key]
            modifier_nom = modifier_gen = ""
            ok = True
            for word in prefix_words:
                table = MODIFIERS if word in MODIFIERS else EXTRA_MODIFIERS
                table_gen = MODIFIERS_GENITIVE if word in MODIFIERS else EXTRA_MODIFIERS_GENITIVE
                if word not in table:
                    ok = False
                    break
                modifier_nom = table[word][gender]
                modifier_gen = table_gen[word][gender]
            if ok:
                head_nom = f"{modifier_nom} {pattern_nom}".strip() if modifier_nom else pattern_nom
                head_gen = f"{modifier_gen} {pattern_gen}".strip() if modifier_gen else pattern_gen
                return (
                    f"{head_nom[0].upper()}{head_nom[1:]} из {material_gen}",
                    f"{head_gen} из {material_gen}",
                )

    # Сначала пробуем «определения + материал» без узора.
    plain = compose_plain(name)
    if plain:
        return plain

    # «Cut Block of Amethyst» и подобные.
    if "of" in words:
        index = words.index("of")
        head = " ".join(words[:index])
        material = " ".join(words[index + 1 :])
        base = SPECIAL.get(f"Block of {material}")
        if not base:
            return None
        state = head.replace("Block", "").strip()
        if not state:
            return base
        if state in MODIFIERS or state in EXTRA_MODIFIERS:
            table = MODIFIERS if state in MODIFIERS else EXTRA_MODIFIERS
            table_gen = MODIFIERS_GENITIVE if state in MODIFIERS else EXTRA_MODIFIERS_GENITIVE
            full = f"{table[state]['m']} {base[0]}"
            return (f"{full[0].upper()}{full[1:]}", f"{table_gen[state]['m']} {base[1]}")
        if state not in MATERIAL_STATES:
            return None
        nominative, genitive = MATERIAL_STATES[state]
        full = f"{nominative} {base[0]}"
        return (f"{full[0].upper()}{full[1:]}", f"{genitive} {base[1]}")

    # Ищем самое длинное совпадение материала в начале либо в середине.
    for length in range(3, 0, -1):
        for start in range(len(words) - length + 1):
            candidate = " ".join(words[start : start + length])
            if candidate not in MATERIALS:
                continue
            pattern_words = words[start + length :]
            prefix_words = words[:start]
            if not pattern_words:
                continue
            pattern_key = " ".join(pattern_words)
            if pattern_key not in PATTERNS:
                continue

            material_nom, material_gen = MATERIALS[candidate]
            pattern_nom, pattern_gen, gender = PATTERNS[pattern_key]

            # Определения перед материалом бывают двух видов: состояние
            # материала («полированный камень») и свойство узора («мелкая
            # плитка»). Первое проверяется по своему словарю.
            state_nom = state_gen = ""
            modifier_nom = modifier_gen = ""
            for word in prefix_words:
                if word in MATERIAL_STATES:
                    state_nom, state_gen = MATERIAL_STATES[word]
                elif word in MODIFIERS:
                    modifier_nom = MODIFIERS[word][gender]
                    modifier_gen = MODIFIERS_GENITIVE[word][gender]
                else:
                    return None

            # Состояние материала тоже стоит в родительном: «из гладкого камня».
            material_full_nom = f"{state_gen} {material_gen}".strip() if state_gen else material_gen
            head_nom = f"{modifier_nom} {pattern_nom}".strip() if modifier_nom else pattern_nom
            head_gen = f"{modifier_gen} {pattern_gen}".strip() if modifier_gen else pattern_gen

            return (
                f"{head_nom[0].upper()}{head_nom[1:]} из {material_full_nom}",
                f"{head_gen} из {material_full_nom}",
            )
    return None


def main() -> int:
    with io.open(DICTIONARY, encoding="utf-8") as handle:
        dictionary = json.load(handle)

    filled = 0
    for name in list(dictionary):
        if dictionary[name] and all(dictionary[name]):
            continue
        result = compose(name)
        if result:
            dictionary[name] = list(result)
            filled += 1

    io.open(DICTIONARY, "w", encoding="utf-8", newline="\n").write(
        json.dumps({k: dictionary[k] for k in sorted(dictionary)}, ensure_ascii=False, indent=2) + "\n"
    )

    remaining = [k for k, v in dictionary.items() if not v or not all(v)]
    print(f"собрано правилами: {filled}   осталось вручную: {len(remaining)}")
    for name in remaining[:25]:
        print(f"    {name}")
    if len(remaining) > 25:
        print(f"    … и ещё {len(remaining) - 25}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
