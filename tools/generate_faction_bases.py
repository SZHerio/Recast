#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка опорных точек шести фракций для генерации мира.

До этого фракции существовали только в разговоре: их можно было увидеть, если
позвать посланника командой, и больше нигде. Здесь у них появляется место на
карте.

Собственных построек сборка не рисует — это потребовало бы запуска игры, чтобы
сохранить шаблон. Вместо этого берутся готовые наборы построек установленных
модов, и каждой фракции назначается тот, который отвечает её ремеслу: караванам
— стоянка, Меридиану — выработка с лагерем, Гелиосу — башня наблюдения. Мир при
этом не переписывается: базы садятся на рельеф теми же средствами, что и
остальные структуры, и в чужую генерацию не вмешиваются.

Расстояние выбрано так, чтобы база фракции была событием, а не декорацией:
одна опорная точка примерно на сорок восемь чанков.

Запуск:
    python tools/generate_faction_bases.py
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATAPACK = ROOT / "config" / "paxi" / "datapacks" / "IndustrialFrontier-Data" / "data" / "industrial_frontier"

# Порядок совпадает с IF_FACTION_LIST модуля фракций.
#
# start_pool — готовый набор построек установленного мода. Соответствие между
# фракцией и набором не случайное: оно повторяет то, чем фракция занимается по
# досье.
FACTION_BASES = [
    {
        "id": "zemlemer",
        "start_pool": "mvs:houses/house/start_pool",
        "size": 4,
        "comment": "Жилой узел общины: дом, двор, запас.",
    },
    {
        "id": "meridian",
        "start_pool": "mvs:other_decoration/mine_with_campsite/start_pool",
        "size": 5,
        "comment": "Выработка с лагерем: добыча и охрана при ней.",
    },
    {
        "id": "free_caravans",
        "start_pool": "mvs:other_decoration/campsite/start_pool",
        "size": 3,
        "comment": "Караванная стоянка на маршруте.",
    },
    {
        "id": "helios",
        "start_pool": "mvs:houses/diorite_tower/start_pool",
        "size": 4,
        "comment": "Башня наблюдения: смотрит дальше, чем подходит.",
    },
    {
        "id": "ash_root",
        "start_pool": "mvs:ruins/log_ruin/start_pool",
        "size": 3,
        "comment": "Лесное убежище на месте старой постройки.",
    },
    {
        "id": "scar",
        "start_pool": "mvs:other/small_pillager_tower/start_pool",
        "size": 3,
        "comment": "Башня артели: высоко, тесно и с обзором на дорогу.",
    },
]

# Соль выбрана один раз и меняться не должна: от неё зависит, где именно в уже
# созданном мире стоят базы.
PLACEMENT_SALT = 748213906
SPACING = 48
SEPARATION = 20


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    written = 0

    for base in FACTION_BASES:
        # Тип структуры взят у moogs_structures: он умеет сажать набор на
        # рельеф и отказываться от воды, чего простой jigsaw не делает.
        write_json(
            DATAPACK / "worldgen" / "structure" / f"base_{base['id']}.json",
            {
                "type": "moogs_structures:moogs_structures_generic_jigsaw_structure",
                "start_pool": base["start_pool"],
                "size": base["size"],
                "biomes": "#mvs:is_overworld",
                "cannot_spawn_in_liquid": True,
                "project_start_to_heightmap": "WORLD_SURFACE_WG",
                "terrain_height_radius_check": 2,
                "allowed_terrain_height_range": 3,
                "step": "surface_structures",
                "terrain_adaptation": "beard_thin",
                "start_height": {"absolute": 0},
                "spawn_overrides": {},
            },
        )
        written += 1

    # Один общий набор размещения: какая именно фракция окажется в точке,
    # решает жребий с равными долями. Так ни одна не занимает карту целиком.
    write_json(
        DATAPACK / "worldgen" / "structure_set" / "faction_bases.json",
        {
            "structures": [
                {"structure": f"industrial_frontier:base_{base['id']}", "weight": 1} for base in FACTION_BASES
            ],
            "placement": {
                "type": "moogs_structures:advanced_random_spread",
                "salt": PLACEMENT_SALT,
                "spacing": SPACING,
                "separation": SEPARATION,
            },
        },
    )
    written += 1

    # Тег нужен, чтобы модуль фракций мог спросить у мира «где ближайшая база»,
    # не перечисляя все шесть по именам.
    write_json(
        DATAPACK / "tags" / "worldgen" / "structure" / "faction_base.json",
        {"values": [f"industrial_frontier:base_{base['id']}" for base in FACTION_BASES]},
    )
    written += 1

    # Проверки присутствия. Модуль фракций спрашивает ими один вопрос: стоит ли
    # игрок прямо сейчас на базе такой-то фракции. Без этого база осталась бы
    # набором блоков, потому что узнать о приходе игрока больше неоткуда.
    for base in FACTION_BASES:
        write_json(
            DATAPACK / "predicates" / f"in_base_{base['id']}.json",
            {
                "condition": "minecraft:location_check",
                "predicate": {"structure": f"industrial_frontier:base_{base['id']}"},
            },
        )
        written += 1

    print(f"готово: {written} файлов генерации мира")
    return 0


if __name__ == "__main__":
    sys.exit(main())
