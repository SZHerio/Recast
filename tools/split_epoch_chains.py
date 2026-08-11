"""Разрыв длинных ниток внутри эпох на параллельные линии.

После слияния глав стало видно, что несколько эпох выстроены в один ряд: в P6
сорок пять шагов подряд, хотя внутри четыре независимые линии — химия, топливный
цикл, тепловой контур и переработка отходов. Их сцепили последовательно, и книга
превратилась в нитку вместо ромба.

Правило разрыва одно и оно смысловое: **сбор сырья не зависит от переработки
соседней линии.** Задание с ролью acquisition получает предпосылкой вход в
эпоху, а не хвост предыдущей цепочки. Линии расходятся от входа и сходятся в
приёмке — та самая форма, что у Nomifactory.

Связи, ведущие к машинам и переработке, не трогаются: там зависимость настоящая.

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
SPLIT_ROLES = {"acquisition"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    total = 0
    report = []

    for path in sorted(SRC.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        quests = document.get("quests", [])
        if not quests:
            continue
        index = {quest["alias"]: quest for quest in quests}

        # Вход в эпоху — задание без предпосылок внутри главы, самое левое.
        entries = [
            quest for quest in quests
            if not [
                edge for edge in quest.get("dependency", {}).get("edges", [])
                if edge["quest"] in index
            ]
        ]
        if not entries:
            continue
        entry = min(entries, key=lambda q: (q["layout"]["x"], q["alias"]))

        changed = 0
        for quest in quests:
            if quest["role"] not in SPLIT_ROLES or quest["alias"] == entry["alias"]:
                continue
            edges = quest.get("dependency", {}).get("edges", [])
            local = [edge for edge in edges if edge["quest"] in index]
            if len(local) != 1 or local[0]["quest"] == entry["alias"]:
                continue
            parent = index[local[0]["quest"]]
            # Сырьё, которое добывают машиной, остаётся привязанным к ней.
            if parent["role"] == "machine":
                continue
            local[0]["quest"] = entry["alias"]
            local[0]["reason"] = (
                "Сбор сырья начинается сразу после входа в эпоху: он не зависит "
                "от переработки соседней линии."
            )
            changed += 1

        if changed:
            total += changed
            report.append((path.stem, changed))
            if args.apply:
                path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"связей переставлено: {total}")
    for stem, changed in report:
        print(f"    {stem:16} {changed}")
    if not args.apply:
        print("\nПРОБНЫЙ ПРОГОН: файлы не изменены")
    return 0


if __name__ == "__main__":
    sys.exit(main())
