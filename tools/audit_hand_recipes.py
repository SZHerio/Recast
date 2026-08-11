"""Сплошной обход рецептов сборки.

Собирает ВСЕ ручные рецепты (верстак, печь, доменная печь, коптильня, костёр,
камнерез) ванили и всех установленных модов, и ВСЕ машинные рецепты всех модов.
Затем делит ручные рецепты на два класса:

  A. у результата уже есть машинный владелец — ручной рецепт можно снимать;
  B. машинного владельца нет — сначала нужен машинный рецепт, иначе предмет
     исчезнет из игры.

Класс B дополнительно разбивается по типу работы, чтобы операции передавались
группами, а не поштучно.

Minecraft не запускается: читаются только jar-файлы и профиль.
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODS = ROOT / "mods"
VANILLA_CANDIDATES = [
    pathlib.Path(r"C:\Users\SZHerio\curseforge\minecraft\Install\versions\1.20.1\1.20.1.jar"),
]

HAND_TYPES = {
    "minecraft:crafting_shaped": "верстак",
    "minecraft:crafting_shapeless": "верстак",
    "minecraft:smelting": "печь",
    "minecraft:blasting": "доменная печь",
    "minecraft:smoking": "коптильня",
    "minecraft:campfire_cooking": "костёр",
    "minecraft:stonecutting": "камнерез",
}


def ids(node) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [node[key] for key in ("item", "id") if isinstance(node.get(key), str)]
    if isinstance(node, list):
        out: list[str] = []
        for entry in node:
            out += ids(entry)
        return out
    return []


def results(recipe: dict) -> list[str]:
    found: list[str] = []
    for key in ("result", "results", "output"):
        if key in recipe:
            found += ids(recipe[key])
    return [i for i in found if ":" in i]


def classify(item: str) -> str:
    """Грубый класс работы по имени результата — для группировки передачи."""
    path = item.split(":", 1)[1]
    if re.search(r"_block$|^bricks$|_bricks$|_planks$|^hay_block$|_wool$", path):
        return "уплотнение и блоки"
    if re.search(r"_slab$|_stairs$|_wall$|_fence|_gate$|_door$|_trapdoor$", path):
        return "распил и формовка"
    if re.search(r"_dye$|^dye|_powder$|^sugar$|^bone_meal$|_dust$", path):
        return "помол и порошки"
    if re.search(r"_ingot$|_nugget$|_plate$|_rod$|_gear$|_wire$", path):
        return "металл и форма"
    if re.search(r"^cooked_|_stew$|^bread$|^cake$|_pie$|^cookie$", path):
        return "пища"
    if re.search(r"_helmet$|_chestplate$|_leggings$|_boots$|_sword$|_pickaxe$|_axe$|_shovel$|_hoe$", path):
        return "инструменты и броня"
    if re.search(r"torch|lantern|lamp|candle|campfire", path):
        return "свет"
    return "прочее"


def load_jars() -> list[pathlib.Path]:
    jars = sorted(MODS.glob("*.jar"))
    for candidate in VANILLA_CANDIDATES:
        if candidate.exists():
            jars.append(candidate)
    return jars


def main() -> int:
    hand: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    machine: dict[str, set[str]] = collections.defaultdict(set)

    for jar in load_jars():
        try:
            archive = zipfile.ZipFile(jar)
        except Exception:
            continue
        with archive:
            for name in archive.namelist():
                if "/recipes/" not in name or not name.endswith(".json"):
                    continue
                try:
                    recipe = json.loads(archive.read(name).decode("utf-8-sig"))
                except Exception:
                    continue
                kind = str(recipe.get("type", ""))
                out = results(recipe)
                if not out:
                    continue
                if kind in HAND_TYPES:
                    for item in out:
                        hand[item].append((HAND_TYPES[kind], jar.name))
                elif kind:
                    for item in out:
                        machine[item].add(kind)

    owned = {item: kinds for item, kinds in machine.items()}
    class_a = sorted(item for item in hand if item in owned)
    class_b = sorted(item for item in hand if item not in owned)

    print(f"ручных рецептов: {sum(len(v) for v in hand.values())} на {len(hand)} предметов")
    print(f"предметов с машинным рецептом: {len(machine)}")
    print()
    print(f"КЛАСС A — машина уже умеет, ручной рецепт можно снимать: {len(class_a)}")
    print(f"КЛАСС B — машинного владельца нет, сначала нужен рецепт: {len(class_b)}")
    print()
    print("КЛАСС B по типу работы:")
    grouped: dict[str, list[str]] = collections.defaultdict(list)
    for item in class_b:
        grouped[classify(item)].append(item)
    for group, items in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
        print(f"  {group:24} {len(items):5}")
        for sample in items[:4]:
            print(f"      {sample}")

    report = ROOT / "build" / "hand_recipe_audit.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({
        "schema_version": 1,
        "hand_recipe_items": len(hand),
        "class_a_machine_owner_exists": class_a,
        "class_b_needs_machine_recipe": {group: items for group, items in grouped.items()},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nполный список: {report}")
    print("Minecraft не запускался.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
