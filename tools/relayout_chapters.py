#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Переразметка книги заданий: компактная сетка, единые формы, без наград.

Три вещи разом, потому что все три трогают одни и те же файлы.

**Сетка.** Задания стояли с шагом три клетки при размере иконки два — между
соседними шагами оставалась пустота, и глава из четырнадцати заданий
растягивалась на двадцать четыре клетки вправо. Игрок листал пустое поле, чтобы
увидеть следующий шаг. Здесь иконка полторы клетки при шаге две: вдвое плотнее
прежнего и при этом связи между заданиями не начинают доминировать в кадре.

**Форма.** Раньше формы стояли вперемешку. Теперь у них смысл: шестерёнка —
вход в главу, ромб — то, чем глава заканчивается, закруглённый квадрат — всё
остальное.

**Награды.** Решение владельца: системы наград у заданий нет. Все блоки наград
снимаются. Книга объясняет и ведёт, а не платит за прохождение.

Раскладка считается по связям: колонка — это глубина задания в цепочке, строка
— его место среди равных по глубине. Ветка, идущая параллельно, встаёт рядом, а
не в хвост.

Запуск:
    python tools/relayout_chapters.py
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "config" / "ftbquests" / "quests" / "chapters"

# Пропорция между иконкой и связью.
#
# Линии зависимостей FTB Quests рисует фиксированной толщиной: они не
# уменьшаются вместе с иконками. При иконке в одну клетку линии начинают
# доминировать в кадре и книга выглядит как схема проводки, а не как список
# заданий. Иконка полторы клетки при шаге две держит их на своём месте и всё
# ещё вдвое компактнее исходной разметки.
COLUMN_STEP = 2.0
ROW_STEP = 2.0
QUEST_SIZE = "1.5d"


def parse_quests(text: str) -> list[dict]:
    """Задания главы: идентификатор, зависимости и границы блока."""
    quests = []
    for match in re.finditer(r"^\t\t\{\n(.*?)^\t\t\}\n?", text, re.M | re.S):
        body = match.group(1)
        found = re.search(r'^\t\t\tid: "(3\d{15})"', body, re.M)
        if not found:
            continue
        deps = set()
        for block in re.finditer(r"dependencies: \[(.*?)\]", body, re.S):
            deps.update(re.findall(r'"(3\d{15})"', block.group(1)))
        quests.append(
            {
                "id": found.group(1),
                "deps": deps,
                "start": match.start(),
                "end": match.end(),
                "body": body,
            }
        )
    return quests


def assign_positions(quests: list[dict]) -> dict[str, tuple[float, float]]:
    """Колонка — глубина в цепочке, строка — место среди равных."""
    own = {quest["id"] for quest in quests}
    depth: dict[str, int] = {}

    # Глубина считается прогонами: задание опускается на уровень ниже самой
    # глубокой своей зависимости. Внешние зависимости (ворота главы) не в счёт —
    # они ведут в другую главу.
    for _ in range(len(quests) + 1):
        changed = False
        for quest in quests:
            inner = [d for d in quest["deps"] if d in own]
            level = 0 if not inner else max(depth.get(d, 0) for d in inner) + 1
            if depth.get(quest["id"]) != level:
                depth[quest["id"]] = level
                changed = True
        if not changed:
            break

    rows: dict[int, int] = {}
    positions: dict[str, tuple[float, float]] = {}
    for quest in quests:
        level = depth[quest["id"]]
        index = rows.get(level, 0)
        rows[level] = index + 1
        positions[quest["id"]] = (level * COLUMN_STEP, index * ROW_STEP)

    # Центрирование по вертикали: цепочка идёт по оси, ветки расходятся вверх и
    # вниз, а не уползают в одну сторону.
    for level, count in rows.items():
        shift = (count - 1) * ROW_STEP / 2
        for quest in quests:
            if depth[quest["id"]] == level:
                x, y = positions[quest["id"]]
                positions[quest["id"]] = (x, round(y - shift, 3))

    return positions


def rewrite_quest(body: str, position: tuple[float, float], shape: str) -> str:
    """Координаты, форма, размер — и ни одной награды."""
    body = re.sub(r"^\t\t\trewards: \[\{.*?^\t\t\t\}\]\n", "", body, flags=re.M | re.S)
    body = re.sub(r"^\t\t\trewards: \[ ?\]\n", "", body, flags=re.M)
    body = re.sub(r'^\t\t\tshape: "\w+"\n', "", body, flags=re.M)
    body = re.sub(r"^\t\t\tsize: [\d.]+d\n", "", body, flags=re.M)
    body = re.sub(r"^\t\t\tx: -?[\d.]+d?\n", "", body, flags=re.M)
    body = re.sub(r"^\t\t\ty: -?[\d.]+d?\n", "", body, flags=re.M)

    x, y = position
    tail = (
        f'\t\t\tshape: "{shape}"\n'
        f"\t\t\tsize: {QUEST_SIZE}\n"
        f"\t\t\tx: {x:g}d\n"
        f"\t\t\ty: {y:g}d\n"
    )
    return body + tail


def process(path: pathlib.Path) -> bool:
    text = path.read_text(encoding="utf-8")
    quests = parse_quests(text)
    if not quests:
        return False

    positions = assign_positions(quests)
    own = {quest["id"] for quest in quests}
    referenced = set()
    for quest in quests:
        referenced.update(d for d in quest["deps"] if d in own)

    pieces = []
    cursor = 0
    for quest in quests:
        inner = [d for d in quest["deps"] if d in own]
        if not inner:
            shape = "gear"
        elif quest["id"] not in referenced:
            shape = "diamond"
        else:
            shape = "rsquare"

        pieces.append(text[cursor : quest["start"]])
        pieces.append("\t\t{\n" + rewrite_quest(quest["body"], positions[quest["id"]], shape) + "\t\t}\n")
        cursor = quest["end"]
    pieces.append(text[cursor:])

    updated = "".join(pieces)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    changed = 0
    for path in sorted(CHAPTERS.glob("*.snbt")):
        quests = parse_quests(path.read_text(encoding="utf-8"))
        if process(path):
            changed += 1
            width = max(1, len({round(q, 3) for q, _ in assign_positions(quests).values()}))
            print(f"{path.stem}: {len(quests)} заданий, глубина {width}")
    print(f"готово: переразмечено глав {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
