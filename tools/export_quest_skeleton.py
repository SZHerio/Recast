"""Скелет книги: только условия, без единого описания.

Второй пункт плана переработки — собрать задания как чистые условия: что
скрафтить, что поставить, что собрать. Тексты появятся на четвёртом пункте и
только там, где без них непонятно.

Скрипт вынимает из действующего источника ровно эту часть: задание, его эпоху,
главу, обязательность, условия и связи. Ни одной строки описания в вывод не
попадает — это и есть заготовка для чистой переработки.

Minecraft не запускается, источник не изменяется.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "authoring" / "questbook_v2"
OUT = ROOT / "build" / "quest_skeleton.json"


def condition(proof: dict) -> dict:
    kind = proof.get("type")
    row: dict = {"type": kind}
    if "item" in proof:
        row["item"] = proof["item"]["id"]
        row["count"] = proof["item"].get("count", 1)
    elif "item_tag" in proof:
        row["tag"] = proof["item_tag"]["id"]
        row["count"] = proof["item_tag"].get("count", 1)
    elif kind in ("place", "use") and kind in proof:
        payload = proof[kind]
        row["block"] = payload.get("block") or payload.get("block_tag")
    elif kind == "fluid" and "fluid" in proof:
        row["fluid"] = proof["fluid"]["id"]
        row["amount"] = proof["fluid"]["amount"]
    elif kind == "structure":
        row["structure"] = proof.get("structure")
    elif kind == "dimension":
        row["dimension"] = proof.get("dimension")
    elif kind == "biome":
        row["biome"] = proof.get("biome")
    elif kind == "energy" and "energy" in proof:
        row["amount"] = proof["energy"]["amount"]
    return row


def main() -> int:
    chapters = []
    stats: collections.Counter[str] = collections.Counter()

    for path in sorted(SOURCE.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        chapter = document.get("chapter")
        if not chapter:
            continue
        quests = []
        for quest in document.get("quests", []):
            conditions = [condition(proof) for proof in quest.get("proofs", [])]
            for row in conditions:
                stats[str(row.get("type"))] += 1
            quests.append({
                "alias": quest["alias"],
                "epoch": quest["epoch"],
                "role": quest["role"],
                "requirement": quest["requirement"],
                "title_ru": quest["text_ru"]["title_ru"],
                "conditions": conditions,
                "after": [edge["quest"] for edge in quest.get("dependency", {}).get("edges", [])],
                "dependency_mode": quest.get("dependency", {}).get("mode"),
            })
        chapters.append({
            "file": path.name,
            "alias": chapter["alias"],
            "title_ru": chapter["text_ru"].get("title_ru") or chapter["text_ru"].get("title") or chapter["alias"],
            "epoch": chapter.get("epoch"),
            "quests": quests,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "schema_version": 1,
        "note": "Только условия и связи. Описания намеренно отсутствуют.",
        "chapters": chapters,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(len(c["quests"]) for c in chapters)
    print(f"глав: {len(chapters)}, заданий: {total}, условий: {sum(stats.values())}")
    print("условия по типам:")
    for kind, count in stats.most_common():
        print(f"  {kind:12} {count}")
    print(f"\nскелет: {OUT}")
    print("Minecraft не запускался, источник не изменялся.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
