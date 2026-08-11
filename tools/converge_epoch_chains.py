"""Сведение параллельных веток эпохи в её приёмку.

Разрыв длинных ниток развёл линии от входа в эпоху, но оставил их концы висеть.
Ромб состоит из двух половин: расхождение и схождение. Здесь делается вторая —
хвост каждой обязательной ветки магистрали становится предпосылкой приёмки.

Так приёмка эпохи снова означает то, что должна: игрок закрыл все линии, а не
дошёл по одной из них до конца.

Без --apply ничего не пишется.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "authoring" / "questbook_v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    total = 0
    report = []

    for path in sorted(SRC.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        quests = document.get("quests", [])
        index = {quest["alias"]: quest for quest in quests}
        commission = next((q for q in quests if q["role"] == "commissioning"), None)
        if not commission:
            continue

        children: dict[str, set[str]] = {alias: set() for alias in index}
        for quest in quests:
            for edge in quest.get("dependency", {}).get("edges", []):
                if edge["quest"] in children:
                    children[edge["quest"]].add(quest["alias"])

        edges = commission.setdefault("dependency", {"mode": "ALL_OF", "edges": []})["edges"]
        present = {edge["quest"] for edge in edges}

        # Предки приёмки: всё, до чего можно дойти вверх по связям.
        ancestors: set[str] = set()
        stack = [edge["quest"] for edge in edges if edge["quest"] in index]
        while stack:
            current = stack.pop()
            if current in ancestors:
                continue
            ancestors.add(current)
            for edge in index[current].get("dependency", {}).get("edges", []):
                if edge["quest"] in index:
                    stack.append(edge["quest"])

        added = 0
        for quest in quests:
            alias = quest["alias"]
            if alias == commission["alias"] or alias in present:
                continue
            if quest.get("requirement") != "required":
                continue
            if "mainline" not in (quest.get("tags") or []):
                continue
            # Ветка, которая уже ведёт к приёмке через потомков, не нуждается в
            # прямой связи: важно, что она не обходится, а не то, как именно.
            if alias in ancestors:
                continue
            edges.append({
                "quest": alias,
                "reason": "Ветка эпохи сходится в её приёмке: приёмка означает, что закрыты все линии, а не одна.",
                "evidence": ["tools/converge_epoch_chains.py"],
            })
            present.add(alias)
            added += 1

        if added:
            total += added
            report.append((path.stem, added))
            if args.apply:
                path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"веток сведено в приёмку: {total}")
    for stem, added in report:
        print(f"    {stem:16} {added}")
    if not args.apply:
        print("\nПРОБНЫЙ ПРОГОН: файлы не изменены")
    return 0


if __name__ == "__main__":
    sys.exit(main())
