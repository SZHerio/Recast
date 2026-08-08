#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка пресетов посланников шести фракций для Easy NPC.

Пресет — это один файл, который описывает NPC целиком: внешность, имя,
принадлежность к фракции, поведение и весь разговор с кнопками. Писать такие
файлы руками нельзя: в них повторяется одна и та же структура шесть раз, а
любая опечатка в теге обнаруживается только в игре.

Формат подтверждён разбором easy_npc-forge-1.20.1-7.4.1.jar:
  * пресеты датапака лежат в data/<namespace>/preset/**.npc.snbt;
  * принадлежность к фракции — строковый тег FactionName;
  * кнопка разговора умеет выполнять команду и умеет иметь условия;
  * условие типа SCOREBOARD сравнивает значение табло с числом.

Последнее и делает переговоры настоящими. Репутация и эпоха уже зеркалятся на
табло ядром Threat Director, поэтому кнопка «предложить союз» просто не
появится, пока отношения не дозрели, — и это решает сервер, а не текст.

Запуск:
    python tools/generate_faction_npc.py
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "kubejs" / "data" / "industrial_frontier" / "preset"

# Порядок обязан совпадать с IF_FACTION_LIST в модуле фракций: по нему
# считаются номера зеркал табло if_rep_01 … if_rep_06.
FACTIONS = [
    {
        "id": "zemlemer",
        "ru": "Содружество Полисов «Землемер»",
        "envoy_ru": "Смотритель округа",
        "colour": "#55FF55",
        "variant": "PROFESSOR_01",
        "greeting": [
            "Вы с завода? Хорошо. Разговор будет про воду и дорогу, @initiator.",
            "Совет просил передать: с вами готовы говорить, @initiator.",
            "Если пришли не отбирать, то садитесь. Слушаю, @initiator.",
        ],
    },
    {
        "id": "meridian",
        "ru": "Индустриальный консорциум «Меридиан»",
        "envoy_ru": "Уполномоченный представитель",
        "colour": "#5555FF",
        "variant": "SECURITY_01",
        "greeting": [
            "Консорциум ведёт учёт. Представьтесь по существу, @initiator.",
            "У вас пятнадцать минут и один вопрос, @initiator.",
            "Контракт или отказ. Третьего мы не оформляем, @initiator.",
        ],
    },
    {
        "id": "free_caravans",
        "ru": "Лига Вольных Караванов",
        "envoy_ru": "Фактор Лиги",
        "colour": "#FFAA00",
        "variant": "JAYJASONBO",
        "greeting": [
            "О, живой человек с деньгами! Или без. Проверим, @initiator?",
            "Дорога длинная, разговор короткий. Что нужно, @initiator?",
            "Слово Лиги дороже расписки. Слушаю вас, @initiator.",
        ],
    },
    {
        "id": "helios",
        "ru": "Директорат «Гелиос»",
        "envoy_ru": "Наблюдатель Директората",
        "colour": "#55FFFF",
        "variant": "KNIGHT_02",
        "greeting": [
            "Ваш допуск ниже требуемого. Говорите коротко, @initiator.",
            "Директорат знает о вашем реакторе больше, чем вы думаете, @initiator.",
            "Мы наблюдаем. Иногда — разговариваем. Сегодня второе, @initiator.",
        ],
    },
    {
        "id": "ash_root",
        "ru": "Движение «Пепельный Корень»",
        "envoy_ru": "Голос Корня",
        "colour": "#00AA00",
        "variant": "STEVE",
        "greeting": [
            "Земля помнит, кто её травил. О вас она пока молчит, @initiator.",
            "Мы не против машин. Мы против мёртвой воды, @initiator.",
            "Говорите. Только не о прибыли, @initiator.",
        ],
    },
    {
        "id": "scar",
        "ru": "Вольная артель «Шрам»",
        "envoy_ru": "Переговорщик артели",
        "colour": "#FF5555",
        "variant": "KNIGHT_01",
        "greeting": [
            "Живой. Пока. Чего хотел, @initiator?",
            "У артели простое правило: платят — не трогаем. Ясно, @initiator?",
            "Слушаю. Быстро, @initiator.",
        ],
    },
]

# Типы договоров. Пороги обязаны совпадать с IF_TREATY_TYPES модуля фракций;
# сверку делает линтер.
TREATIES = [
    {"id": "truce", "ru": "Перемирие", "min_reputation": -75, "min_epoch": 0},
    {"id": "trade", "ru": "Торговый договор", "min_reputation": -10, "min_epoch": 1},
    {"id": "tribute", "ru": "Дань", "min_reputation": -75, "min_epoch": 2},
    {"id": "alliance", "ru": "Союз", "min_reputation": 41, "min_epoch": 3},
    {"id": "joint_defence", "ru": "Совместная оборона", "min_reputation": 41, "min_epoch": 5},
]


def snbt_string(value: str) -> str:
    """Строка SNBT в двойных кавычках."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def scoreboard_condition(objective: str, minimum: int) -> str:
    """Условие «значение табло не ниже числа»."""
    return (
        "{"
        f"Type:\"SCOREBOARD\",Name:{snbt_string(objective)},"
        f"Operation:\"GREATER_THAN_OR_EQUALS\",Value:{minimum}"
        "}"
    )


def command_action(command: str) -> str:
    return "{" + f"Cmd:{snbt_string(command)},Type:\"COMMAND\"" + "}"


def open_dialog_action(label: str) -> str:
    return "{" + f"Cmd:{snbt_string(label)},Type:\"OPEN_NAMED_DIALOG\"" + "}"


CLOSE_DIALOG_ACTION = '{Type:"CLOSE_DIALOG"}'


def build_dialog(faction: dict, index: int) -> str:
    """Разговор посланника: знакомство и переговоры о договоре."""
    reputation_objective = f"if_rep_0{index + 1}"
    faction_id = faction["id"]

    # Приветствие и три пути: узнать, договориться, уйти.
    greeting_texts = ",".join("{Text:" + snbt_string(line) + "}" for line in faction["greeting"])
    default_buttons = ",".join(
        [
            "{"
            + f"Label:\"about\",Name:{snbt_string('Кто вы и чего хотите?')},Actions:["
            + command_action(f"/execute as @initiator run if_threat faction {faction_id}")
            + ","
            + CLOSE_DIALOG_ACTION
            + "]}",
            "{"
            + f"Label:\"talks\",Name:{snbt_string('Поговорим о договоре.')},Actions:["
            + open_dialog_action("talks")
            + "]}",
            "{"
            + f"Label:\"leave\",Name:{snbt_string('Не сейчас.')},Actions:["
            + CLOSE_DIALOG_ACTION
            + "]}",
        ]
    )

    # Переговоры. Каждая кнопка появляется только при своей репутации и эпохе:
    # именно поэтому предложить союз врагу невозможно — не потому, что текст
    # запрещает, а потому, что кнопки нет.
    treaty_buttons = []
    for treaty in TREATIES:
        conditions = ",".join(
            [
                scoreboard_condition(reputation_objective, treaty["min_reputation"]),
                scoreboard_condition("if_epoch", treaty["min_epoch"]),
            ]
        )
        treaty_buttons.append(
            "{"
            + f"Label:{snbt_string('treaty_' + treaty['id'])},Name:{snbt_string(treaty['ru'])},"
            + "Actions:["
            + command_action(
                f"/execute as @initiator run if_threat treaty sign {faction_id} {treaty['id']}"
            )
            + ","
            + CLOSE_DIALOG_ACTION
            + "],"
            + f"Conditions:[{conditions}]"
            + "}"
        )
    treaty_buttons.append(
        "{"
        + f"Label:\"talks_back\",Name:{snbt_string('Вернуться к началу.')},Actions:["
        + open_dialog_action("default")
        + "]}"
    )

    dialogs = [
        "{"
        + f"Label:\"default\",Name:{snbt_string('Встреча')},Texts:[{greeting_texts}],"
        + f"Buttons:[{default_buttons}]"
        + "}",
        "{"
        + f"Label:\"talks\",Name:{snbt_string('Переговоры')},Texts:[{{Text:"
        + snbt_string(
            "Договор — это обязательство обеих сторон. Мы предлагаем только то, "
            "на что вы уже заслужили право."
        )
        + "}],"
        + f"Buttons:[{','.join(treaty_buttons)}]"
        + "}",
    ]

    return "DialogData:{DialogDataSet:[" + ",".join(dialogs) + '],Type:"STANDARD"}'


def build_preset(faction: dict, index: int) -> str:
    """Полный пресет посланника."""
    name_component = (
        '{"color":"' + faction["colour"] + '","text":"' + faction["envoy_ru"] + '"}'
    )

    metadata = ",".join(
        [
            'author:"Recast"',
            'category:"Faction"',
            f"description:{snbt_string('Посланник фракции: ' + faction['ru'])}",
            'entityTypeId:"easy_npc:humanoid"',
            f"name:{snbt_string(faction['envoy_ru'])}",
            f"variantType:{snbt_string(faction['variant'])}",
            'version:"1.0.0"',
        ]
    )

    # Поведение посланника: смотрит на собеседника, гуляет у своего дома и
    # никого не атакует первым. Драку начинает не он.
    objectives = ",".join(
        [
            '{Prio:9,Type:"LOOK_AT_PLAYER"}',
            '{Prio:10,Type:"LOOK_AT_RESET"}',
            '{Prio:5,SpeedModifier:0.5d,Type:"RANDOM_STROLL_AROUND_HOME"}',
            '{Prio:1,Type:"FLOAT"}',
            '{Prio:3,Type:"FACTION_HURT_BY_TARGET"}',
        ]
    )

    # Посланник смертен намеренно: убийство переговорщика обязано стоить
    # репутации, а бессмертный собеседник обесценил бы и угрозу, и выбор.
    entity_attributes = ",".join(
        [
            "CanBeHitByProjectile:1b",
            "CanBeLeashed:0b",
            "CanFloat:1b",
            "CanOpenDoor:1b",
            "CanPassDoor:1b",
            "IsAttackableByMonsters:1b",
            "IsAttackableByPlayers:1b",
            "IsInvulnerable:0b",
            "IsPushable:1b",
            "HealthRegeneration:0.5d",
        ]
    )

    data = ",".join(
        [
            "ActionData:{ActionPermissionLevel:4}",
            f"CustomName:'{name_component}'",
            "CustomNameVisible:1b",
            f"FactionName:{snbt_string(faction['id'])}",
            build_dialog(faction, index),
            f"ObjectiveData:{{HasObjectives:1b,ObjectiveDataSet:[{objectives}]}}",
            f"EntityAttribute:{{{entity_attributes}}}",
            "Health:20.0f",
            'Profession:"NONE"',
            "CanPickUpLoot:0b",
            "PersistenceRequired:1b",
        ]
    )

    return "{PresetMetadata:{" + metadata + "},data:{" + data + "}}\n"


# Три ступени снаряжения отрядов.
#
# Это та же боевая лестница, на которой держится вся сборка: отряд не может
# носить то, чего игрок ещё не научился делать. Правило проверялось при разборе
# лута структур, где незеритовое снаряжение понижали до алмазного, и здесь оно
# соблюдается по той же причине — иначе бой перестаёт быть разговором о технике
# и превращается в лотерею.
SQUAD_TIERS = [
    {
        "id": "early",
        "ru": "боец",
        "max_epoch": 2,
        "armour": ["leather_boots", "leather_leggings", "leather_chestplate", "leather_helmet"],
        "hand": ["stone_sword", "shield"],
        "health": 20.0,
    },
    {
        "id": "mid",
        "ru": "стрелок",
        "max_epoch": 5,
        "armour": ["iron_boots", "iron_leggings", "iron_chestplate", "iron_helmet"],
        "hand": ["iron_sword", "shield"],
        "health": 24.0,
    },
    {
        "id": "late",
        "ru": "оперативник",
        "max_epoch": 9,
        "armour": ["diamond_boots", "diamond_leggings", "diamond_chestplate", "diamond_helmet"],
        "hand": ["diamond_sword", "shield"],
        "health": 30.0,
    },
]


def build_squad_preset(faction: dict, tier: dict) -> str:
    """Боец фракции: снаряжение по ступени, поведение по доктрине."""
    name_component = (
        '{"color":"' + faction["colour"] + '","text":"' + faction["envoy_ru"].split()[0] + " " + tier["ru"] + '"}'
    )

    metadata = ",".join(
        [
            'author:"Recast"',
            'category:"Faction Squad"',
            f"description:{snbt_string('Отряд фракции: ' + faction['ru'])}",
            'entityTypeId:"easy_npc:humanoid"',
            f"name:{snbt_string(faction['envoy_ru'].split()[0] + ' ' + tier['ru'])}",
            f"variantType:{snbt_string(faction['variant'])}",
            'version:"1.0.0"',
        ]
    )

    armour = ",".join(
        "{" + f"Count:1b,id:\"minecraft:{piece}\"" + "}" for piece in tier["armour"]
    )
    hands = ",".join("{" + f"Count:1b,id:\"minecraft:{piece}\"" + "}" for piece in tier["hand"])

    # Отряд нападает на игрока и на враждебные фракции, но не на всё живое:
    # операция имеет цель, а не задачу вырезать округу.
    objectives = ",".join(
        [
            '{Prio:1,Type:"FLOAT"}',
            '{Prio:2,SpeedModifier:1.0d,Type:"MELEE_ATTACK"}',
            '{Prio:3,Type:"ATTACK_PLAYER"}',
            '{Prio:3,Type:"ATTACK_HOSTILE_FACTIONS"}',
            '{Prio:4,Type:"FACTION_HURT_BY_TARGET"}',
            '{Prio:8,Type:"LOOK_AT_PLAYER"}',
            '{Prio:9,SpeedModifier:0.7d,Type:"RANDOM_STROLL_AROUND_HOME"}',
        ]
    )

    entity_attributes = ",".join(
        [
            "CanBeHitByProjectile:1b",
            "CanFloat:1b",
            "CanOpenDoor:1b",
            "CanPassDoor:1b",
            "IsAttackableByMonsters:1b",
            "IsAttackableByPlayers:1b",
            "IsInvulnerable:0b",
            "IsPushable:1b",
        ]
    )

    data = ",".join(
        [
            "ActionData:{ActionPermissionLevel:4}",
            f"CustomName:'{name_component}'",
            "CustomNameVisible:1b",
            f"FactionName:{snbt_string(faction['id'])}",
            f"ArmorItems:[{armour}]",
            f"HandItems:[{hands}]",
            "ArmorDropChances:[0.0f,0.0f,0.0f,0.0f]",
            "HandDropChances:[0.0f,0.0f]",
            f"ObjectiveData:{{HasObjectives:1b,ObjectiveDataSet:[{objectives}]}}",
            f"EntityAttribute:{{{entity_attributes}}}",
            f"Health:{tier['health']}f",
            'Profession:"NONE"',
            "CanPickUpLoot:0b",
            "PersistenceRequired:0b",
        ]
    )

    return "{PresetMetadata:{" + metadata + "},data:{" + data + "}}\n"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for index, faction in enumerate(FACTIONS):
        target = OUTPUT_DIR / f"{faction['id']}_envoy.npc.snbt"
        target.write_text(build_preset(faction, index), encoding="utf-8")
        written += 1

        for tier in SQUAD_TIERS:
            squad_target = OUTPUT_DIR / f"{faction['id']}_squad_{tier['id']}.npc.snbt"
            squad_target.write_text(build_squad_preset(faction, tier), encoding="utf-8")
            written += 1

    print(f"готово: {written} пресетов ({len(FACTIONS)} посланников и {len(FACTIONS) * len(SQUAD_TIERS)} бойцов)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
