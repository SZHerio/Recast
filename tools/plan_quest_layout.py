"""План слияния глав в эпохи и раскладки заданий по сетке.

Скрипт ничего не меняет: он только считает, как будет выглядеть книга после
переработки, и пишет план в build/quest_layout_plan.json. Применение плана —
отдельная операция, которую нельзя обрывать на середине.

Раскладка повторяет приём Nomifactory: задания стоят по клеткам, столбец задаёт
глубину цепочки, строка — параллельные ветки одной глубины. Связи получаются
короткими, а ветвление и схождение видно без подписей.

Размер узла задан ролью: рубеж эпохи крупнее шага к нему.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKELETON = ROOT / "build" / "quest_skeleton.json"
OUT = ROOT / "build" / "quest_layout_plan.json"

EPOCH_ORDER = {"ONBOARDING": -1, **{f"P{i}": i for i in range(10)}}
SIZE = {"commissioning": 1.6, "integration": 1.3, "automation": 1.3, "operation": 1.15}
DEFAULT_SIZE = 1.0
STEP_X = 2.0   # шаг между столбцами
STEP_Y = 1.5   # шаг между строками


def main() -> int:
    if not SKELETON.exists():
        print("нет скелета: сначала tools/export_quest_skeleton.py")
        return 1

    data = json.loads(SKELETON.read_text(encoding="utf-8"))
    quests: dict[str, dict] = {}
    for chapter in data["chapters"]:
        for quest in chapter["quests"]:
            quests[quest["alias"]] = quest

    # Эпоха задания: своя, а для системных и справочных — эпоха самой поздней
    # предпосылки, потому что именно она решает, когда игрок сюда попадёт.
    resolved: dict[str, str] = {}

    def epoch_of(alias: str, seen: set[str] | None = None) -> str:
        if alias in resolved:
            return resolved[alias]
        quest = quests[alias]
        own = quest["epoch"]
        if own in EPOCH_ORDER:
            resolved[alias] = own
            return own
        seen = seen or set()
        if alias in seen:
            return "P0"
        seen.add(alias)
        best = -1
        for parent in quest["after"]:
            if parent in quests:
                best = max(best, EPOCH_ORDER.get(epoch_of(parent, seen), -1))
        value = f"P{best}" if best >= 0 else "P0"
        resolved[alias] = value
        return value

    for alias in quests:
        epoch_of(alias)

    groups: dict[str, list[str]] = collections.defaultdict(list)
    for alias in quests:
        groups[resolved[alias]].append(alias)

    # Глубина цепочки внутри эпохи: столько шагов от входа в эпоху.
    plan = []
    for epoch in sorted(groups, key=lambda e: EPOCH_ORDER.get(e, 99)):
        members = set(groups[epoch])
        depth: dict[str, int] = {}

        def depth_of(alias: str, seen: set[str] | None = None) -> int:
            if alias in depth:
                return depth[alias]
            seen = seen or set()
            if alias in seen:
                return 0
            seen.add(alias)
            parents = [p for p in quests[alias]["after"] if p in members]
            value = 0 if not parents else 1 + max(depth_of(p, seen) for p in parents)
            depth[alias] = value
            return value

        for alias in members:
            depth_of(alias)

        columns: dict[int, list[str]] = collections.defaultdict(list)
        for alias in sorted(members, key=lambda a: (depth[a], a)):
            columns[depth[alias]].append(alias)

        placed = []
        for column, aliases in sorted(columns.items()):
            offset = (len(aliases) - 1) / 2.0
            for row, alias in enumerate(aliases):
                quest = quests[alias]
                placed.append({
                    "alias": alias,
                    "title_ru": quest["title_ru"],
                    "role": quest["role"],
                    "x": round(column * STEP_X, 2),
                    "y": round((row - offset) * STEP_Y, 2),
                    "size": SIZE.get(quest["role"], DEFAULT_SIZE),
                    "after": quest["after"],
                })

        plan.append({
            "epoch": epoch,
            "quests": len(placed),
            "columns": len(columns),
            "widest_column": max(len(v) for v in columns.values()),
            "layout": placed,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "schema_version": 1,
        "note": "План раскладки. Источник книги не изменялся.",
        "grid": {"step_x": STEP_X, "step_y": STEP_Y},
        "epochs": plan,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{'эпоха':12} {'заданий':>8} {'столбцов':>9} {'широчайший':>11}")
    for row in plan:
        print(f"  {row['epoch']:10} {row['quests']:8} {row['columns']:9} {row['widest_column']:11}")
    print(f"\nплан: {OUT}")
    print("Источник книги не изменялся, Minecraft не запускался.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
