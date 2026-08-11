"""Слияние глав книги в эпохи и раскладка заданий по сетке.

Двадцать семь глав сходятся в двенадцать: знакомство, десять эпох и справка.
Тематические главы — склад, оборона, поселение, нефть, фракции, мир, академия —
растворяются в эпохах: каждое задание уходит туда, где его открывают
предпосылки, а не туда, где оно лежало по теме.

Раскладка повторяет приём Nomifactory: столбец задаёт глубину цепочки, строка —
параллельные ветки одной глубины. Связи получаются короткими, ветвление и
схождение видно без подписей. Размер узла задан ролью.

Без --apply ничего не пишется.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "authoring" / "questbook_v2"

EPOCH_ORDER = {"ONBOARDING": -1, **{f"P{i}": i for i in range(10)}}
# Главы, которые остаются собой: вход в игру и справка.
KEEP_AS_IS = {"90_help"}
ONBOARDING_TARGET = "00_onboarding"
EPOCH_FILE = {f"P{i}": f"{10 + i}_p{i}" for i in range(10)}

SIZE = {
    "commissioning": 1.8,
    "integration": 1.4,
    "automation": 1.4,
    "operation": 1.2,
    "machine": 1.1,
}
DEFAULT_SIZE = 1.0
STEP_X = 2.0
STEP_Y = 1.5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    documents: dict[str, dict] = {}
    for path in sorted(SRC.glob("*.json")):
        documents[path.stem] = json.loads(path.read_text(encoding="utf-8"))

    quests: dict[str, dict] = {}
    home: dict[str, str] = {}
    for stem, document in documents.items():
        for quest in document.get("quests", []):
            quests[quest["alias"]] = quest
            home[quest["alias"]] = stem

    # Эпоха задания: своя, а у системных и справочных — эпоха самой поздней
    # предпосылки. Именно она решает, когда игрок сюда попадёт.
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
        for edge in quest.get("dependency", {}).get("edges", []):
            parent = edge["quest"]
            if parent in quests:
                best = max(best, EPOCH_ORDER.get(epoch_of(parent, seen), -1))
        value = f"P{best}" if best >= 0 else "P0"
        resolved[alias] = value
        return value

    # Куда переезжает каждое задание.
    target: dict[str, str] = {}
    for alias in quests:
        if home[alias] in KEEP_AS_IS:
            target[alias] = home[alias]
            continue
        epoch = epoch_of(alias)
        # Задание переезжает вместе со своей эпохой: системные и справочные
        # получают ту, до которой их довели предпосылки. Валидатор требует
        # совпадения эпохи задания и главы, и это верно по смыслу.
        quests[alias]["epoch"] = epoch
        target[alias] = ONBOARDING_TARGET if epoch == "ONBOARDING" else EPOCH_FILE[epoch]

    buckets: dict[str, list[str]] = collections.defaultdict(list)
    for alias, stem in target.items():
        buckets[stem].append(alias)

    # Раскладка внутри главы.
    for stem, aliases in buckets.items():
        members = set(aliases)
        depth: dict[str, int] = {}

        def depth_of(alias: str, seen: set[str] | None = None) -> int:
            if alias in depth:
                return depth[alias]
            seen = seen or set()
            if alias in seen:
                return 0
            seen.add(alias)
            parents = [
                edge["quest"]
                for edge in quests[alias].get("dependency", {}).get("edges", [])
                if edge["quest"] in members
            ]
            value = 0 if not parents else 1 + max(depth_of(p, seen) for p in parents)
            depth[alias] = value
            return value

        for alias in members:
            depth_of(alias)

        columns: dict[int, list[str]] = collections.defaultdict(list)
        for alias in sorted(members, key=lambda a: (depth[a], a)):
            columns[depth[alias]].append(alias)

        for column, column_aliases in columns.items():
            offset = (len(column_aliases) - 1) / 2.0
            for row, alias in enumerate(column_aliases):
                quest = quests[alias]
                layout = dict(quest.get("layout", {}))
                layout["x"] = round(column * STEP_X, 2)
                layout["y"] = round((row - offset) * STEP_Y, 2)
                layout["size"] = SIZE.get(quest["role"], DEFAULT_SIZE)
                layout.setdefault("shape", "square")
                quest["layout"] = layout

    dissolved = sorted(set(documents) - set(buckets))
    print(f"глав было {len(documents)}, станет {len(buckets)}")
    print(f"растворяется: {len(dissolved)}")
    for stem in dissolved:
        print(f"    {stem}")
    print("\nсостав после слияния:")
    for stem in sorted(buckets, key=lambda s: documents[s]["chapter"]["order"] if s in documents else 999):
        print(f"    {stem:16} {len(buckets[stem]):4}")

    if not args.apply:
        print("\nПРОБНЫЙ ПРОГОН: файлы не изменены")
        return 0

    for stem, aliases in buckets.items():
        document = documents[stem]
        ordered = sorted(aliases, key=lambda a: (quests[a]["layout"]["x"], quests[a]["layout"]["y"]))
        document["quests"] = [quests[a] for a in ordered]
        (SRC / f"{stem}.json").write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    retired = SRC.parent / "questbook_v2_dissolved"
    retired.mkdir(exist_ok=True)
    for stem in dissolved:
        (SRC / f"{stem}.json").rename(retired / f"{stem}.json")

    print(f"\nприменено. Растворённые главы сохранены в {retired}")
    print("Minecraft не запускался.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
