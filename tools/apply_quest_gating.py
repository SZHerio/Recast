#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Постепенное раскрытие книги заданий.

Проблема, которую это решает. Восемнадцать глав и сто семьдесят девять заданий
были видны игроку с первой минуты: на старте, ещё не добыв камня, он видел
главу про ядерный реактор и оба финала. Книга такого размера не ведёт, а
пугает — и главное, не даёт понять, что делать прямо сейчас.

Как решается. Главы связываются в цепочку: следующая появляется в книге только
тогда, когда закончена предыдущая. Внутри главы, наоборот, видно всё — игрок
должен понимать объём эпохи и планировать, а не идти вслепую от задания к
заданию.

Технически это две настройки FTB Quests, обе подтверждены разбором
ftb-quests-forge-2001.4.22:

  * `hide_quest_until_deps_visible` на главе — задание скрыто, пока скрыто то,
    от которого оно зависит; так прячется вся глава разом;
  * `hide_until_deps_complete` на первом задании главы — оно появляется только
    после завершения предыдущей главы.

Скрипт можно запускать сколько угодно раз: он проверяет, не сделана ли работа.

Запуск:
    python tools/apply_quest_gating.py
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "config" / "ftbquests" / "quests" / "chapters"
DATA_FILE = ROOT / "config" / "ftbquests" / "quests" / "data.snbt"

# Что от чего открывается.
#
# Основная линия идёт по эпохам. Необязательные главы привязаны к той эпохе, в
# которой они впервые становятся нужны: дипломатия — когда мир начинает
# отвечать, паспорта материалов — когда материалов становится больше одного,
# мастерство — когда завод уже построен и начал вести себя странно.
#
# Две главы не гейтятся никогда: «Начало» и «Справка». Первая — вход, вторая
# нужна ровно тогда, когда что-то непонятно, то есть в любой момент.
CHAPTER_CHAIN = {
    "10_p0_expedition": "00_start_here",
    "11_p1_mechanised": "10_p0_expedition",
    "12_p2_steam_metallurgy": "11_p1_mechanised",
    "13_p3_electrification": "12_p2_steam_metallurgy",
    "14_p4_chemical_city": "13_p3_electrification",
    "15_p5_regional_logistics": "14_p4_chemical_city",
    "16_p6_nuclear": "15_p5_regional_logistics",
    "17_p7_strategic_space": "16_p6_nuclear",
    "18_p8_orbital_network": "17_p7_strategic_space",
    "19_p9_finale": "18_p8_orbital_network",
    # Главы про механики открываются в ту эпоху, когда механика становится
    # нужной: хранение и оборона — когда появилась сталь и мир начал отвечать,
    # поселение — когда есть чем кормить, мастерские и нефть — когда есть чем
    # питать, фракции в деле — сразу после разговора о дипломатии.
    "20_storage_order": "12_p2_steam_metallurgy",
    "21_defence_gear": "12_p2_steam_metallurgy",
    "22_settlement": "13_p3_electrification",
    "23_pressure_silicon": "14_p4_chemical_city",
    "24_oil_line": "15_p5_regional_logistics",
    "25_factions_live": "45_diplomacy_security",
    "71_academy_of_elements": "10_p0_expedition",
    "70_material_passports": "11_p1_mechanised",
    "45_diplomacy_security": "12_p2_steam_metallurgy",
    "73_marathon_choices": "13_p3_electrification",
    "46_operations_and_defence": "15_p5_regional_logistics",
    "72_mastery_distributed_factory": "18_p8_orbital_network",
}

NEVER_GATED = {"00_start_here", "90_help"}


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: pathlib.Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def quest_ids(text: str) -> list[str]:
    """Идентификаторы заданий главы в порядке появления."""
    return re.findall(r'^\t\t\tid: "(3\d{15})"', text, re.M)


def first_quest_id(text: str) -> str | None:
    """Задание, с которого глава начинается.

    Это то, у которого нет зависимостей внутри своей же главы. Зависимость на
    предыдущую главу не считается: её ставит этот же скрипт, и после первого
    запуска первое задание перестало бы находиться.
    """
    own = set(quest_ids(text))
    for block in re.findall(r"^\t\t\{\n(.*?)^\t\t\}", text, re.M | re.S):
        found = re.search(r'id: "(3\d{15})"', block)
        if not found:
            continue
        inner = set()
        for match in re.finditer(r"dependencies: \[(.*?)\]", block, re.S):
            inner.update(re.findall(r'"(3\d{15})"', match.group(1)))
        if not (inner & own):
            return found.group(1)
    return None


def last_quest_id(text: str) -> str | None:
    """Задание, которым глава заканчивается: от него никто не зависит."""
    ids = quest_ids(text)
    referenced = set(re.findall(r'"(3\d{15})"', text)) - set(ids)
    depended = set()
    for match in re.finditer(r"dependencies: \[(.*?)\]", text, re.S):
        depended.update(re.findall(r'"(3\d{15})"', match.group(1)))
    tail = [quest for quest in ids if quest not in depended]
    if not tail:
        return ids[-1] if ids else None
    return tail[-1]


def ensure_chapter_flag(text: str) -> tuple[str, bool]:
    """Глава прячет задание, пока скрыто то, от которого оно зависит."""
    if "hide_quest_until_deps_visible" in text:
        return text, False
    updated = text.replace(
        "\tdefault_hide_dependency_lines: false",
        "\tdefault_hide_dependency_lines: false\n\thide_quest_until_deps_visible: true",
        1,
    )
    return updated, updated != text


def ensure_first_quest_gate(text: str, quest_id: str, dependency_id: str) -> tuple[str, bool]:
    """Первое задание главы ждёт завершения предыдущей главы."""
    pattern = re.compile(r"(^\t\t\{\n)((?:(?!^\t\t\}).)*?id: \"" + quest_id + r"\".*?)(^\t\t\})", re.M | re.S)
    match = pattern.search(text)
    if not match:
        return text, False

    body = match.group(2)
    if dependency_id in body and "hide_until_deps_complete" in body:
        return text, False

    if "dependencies:" not in body:
        body = f'\t\t\tdependencies: ["{dependency_id}"]\n' + body
    if "hide_until_deps_complete" not in body:
        body = f"\t\t\thide_until_deps_complete: true\n" + body

    return text[: match.start()] + match.group(1) + body + match.group(3) + text[match.end() :], True


def main() -> int:
    changed = 0

    # Задания, недоступные из-за незакрытых зависимостей, не показываются.
    data_text = read(DATA_FILE)
    if "hide_excluded_quests: false" in data_text:
        write(DATA_FILE, data_text.replace("hide_excluded_quests: false", "hide_excluded_quests: true", 1))
        print("data.snbt: скрытие недоступных заданий включено")
        changed += 1

    tails: dict[str, str] = {}
    for path in sorted(CHAPTERS.glob("*.snbt")):
        tails[path.stem] = last_quest_id(read(path)) or ""

    for chapter_name, previous_name in CHAPTER_CHAIN.items():
        path = CHAPTERS / f"{chapter_name}.snbt"
        if not path.exists():
            print(f"ПРОПУЩЕНО: нет главы {chapter_name}")
            continue
        if chapter_name in NEVER_GATED:
            continue

        dependency_id = tails.get(previous_name)
        if not dependency_id:
            print(f"ОШИБКА: не найдено последнее задание главы {previous_name}")
            return 1

        text = read(path)
        head = first_quest_id(text)
        if not head:
            print(f"ОШИБКА: не найдено первое задание главы {chapter_name}")
            return 1

        text, flag_changed = ensure_chapter_flag(text)
        text, gate_changed = ensure_first_quest_gate(text, head, dependency_id)

        if flag_changed or gate_changed:
            write(path, text)
            changed += 1
            print(f"{chapter_name}: открывается после «{previous_name}»")

    print(f"готово: изменено файлов {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
