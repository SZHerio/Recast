"""Сверка книги заданий с фактическим содержимым запущенной игры.

Берёт все предметы и теги, которые книга требует от игрока, и ищет их в выгрузке
рецептов `kubejs/exported/recipe_index.json`. Если предмет не встречается ни во
входах, ни в выходах ни одного рецепта — задание на него, скорее всего, стало
невыполнимым: мод обновился, переименовал или убрал предмет.

Проверка приблизительная: предмет может существовать и не иметь ни одного
рецепта (например, добывается в мире). Поэтому результат — список кандидатов на
ручную проверку, а не приговор.

Minecraft не запускается.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "authoring" / "questbook_v2"
DUMP = ROOT / "kubejs" / "exported" / "recipe_index.json"


def main() -> int:
    if not DUMP.exists():
        print("нет выгрузки рецептов: зайдите в мир, файл создастся сам")
        return 1

    known: set[str] = set()
    for row in json.loads(DUMP.read_text(encoding="utf-8"))["rows"]:
        brace = row.find("{")
        if brace < 0:
            continue
        body = row[brace:]
        start = 0
        while True:
            start = body.find('"', start)
            if start < 0:
                break
            end = body.find('"', start + 1)
            if end < 0:
                break
            token = body[start + 1:end]
            if ":" in token and " " not in token:
                known.add(token)
            start = end + 1

    demanded: dict[str, list[str]] = collections.defaultdict(list)
    for path in sorted(SOURCE.glob("*.json")):
        for quest in json.loads(path.read_text(encoding="utf-8")).get("quests", []):
            for proof in quest.get("proofs", []):
                if "item" in proof:
                    demanded[proof["item"]["id"]].append(quest["alias"])
                if "item_tag" in proof:
                    demanded["#" + proof["item_tag"]["id"]].append(quest["alias"])

    items = {k: v for k, v in demanded.items() if not k.startswith("#")}
    tags = {k: v for k, v in demanded.items() if k.startswith("#")}
    missing = {k: v for k, v in items.items() if k not in known}

    print(f"книга требует предметов: {len(items)}, тегов: {len(tags)}")
    print(f"предметов найдено в игре: {len(items) - len(missing)}")
    print(f"НЕ НАЙДЕНО: {len(missing)}")
    by_mod = collections.Counter(k.split(":")[0] for k in missing)
    for mod, count in by_mod.most_common():
        print(f"\n  {mod} — {count}")
        for item in sorted(k for k in missing if k.startswith(mod + ":"))[:8]:
            print(f"    {item}   <- {missing[item][0]}")
    print("\nТеги проверяются отдельно: их содержимое собирается в игре.")
    print("Minecraft не запускался.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
