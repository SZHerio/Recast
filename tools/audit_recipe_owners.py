"""Лестница выхода: проверка, что старшая машина выгоднее младшей.

Правило сборки (docs/registries/recipe_devolution.json): одна операция живёт на
нескольких машинах, но выход обязан расти со ступенью. Нарушением считается
случай, когда младшая или более дешёвая машина даёт столько же или больше
старшей — это и есть обход технологии.

Инструмент обходит ВСЕ установленные моды, считает выход на единицу сырья для
каждого рецепта и сравнивает ступени. Оценка приблизительная: она считает
предметные входы и выходы и не видит энергию, время и жидкости, поэтому спорные
случаи выводятся для решения человеком, а не режутся молча.

Minecraft не запускается.
"""
from __future__ import annotations

import collections, json, pathlib, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "docs" / "registries" / "recipe_devolution.json"

# Ступень машины. 0 — ручная или почти бесплатная, 1 — ранняя механика,
# 2 — промышленная, 3 — поздняя и энергоёмкая.
TIERS = {
    "farmersdelight:cutting": 0,
    "refurbished_furniture:cutting_board_slicing": 0,
    "refurbished_furniture:freezer_solidifying": 0,
    "create:milling": 1,
    "create:crushing": 1,
    "create:pressing": 1,
    "create:splashing": 1,
    "create:compacting": 1,
    "create:mixing": 1,
    "create:cutting": 1,
    "create:mechanical_crafting": 1,
    "create:sequenced_assembly": 2,
    "immersiveengineering:crusher": 2,
    "immersiveengineering:shapeless_fluid": 2,
    "pneumaticcraft:pressure_chamber": 2,
    "pneumaticcraft:assembly_drill": 2,
    "nuclearcraft:manufactory": 3,
    "nuclearcraft:irradiator": 3,
    "hbm_ntm_rebirth:shredder": 3,
}


def ids(node):
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [node[k] for k in ("item", "id") if isinstance(node.get(k), str)]
    if isinstance(node, list):
        out = []
        for entry in node:
            out += ids(entry)
        return out
    return []


def count_of(node) -> int:
    if isinstance(node, dict):
        for key in ("count", "amount"):
            if isinstance(node.get(key), int):
                return node[key]
    return 1


def yield_of(recipe: dict, target: str) -> tuple[int, int]:
    """Сколько получаем и сколько кладём: грубая, но сопоставимая оценка."""
    produced = 0
    for key in ("result", "results", "output"):
        node = recipe.get(key)
        if node is None:
            continue
        entries = node if isinstance(node, list) else [node]
        for entry in entries:
            if target in ids(entry):
                produced += count_of(entry)
    raw = recipe.get("ingredients") or recipe.get("ingredient") or recipe.get("inputs") or []
    entries = raw if isinstance(raw, list) else [raw]
    consumed = sum(count_of(entry) for entry in entries) or 1
    return produced, consumed


def main() -> int:
    # Обход идёт по всем операциям сборки, а не только по уже затронутым линией.
    json.loads(REG.read_text(encoding="utf-8"))

    ladders: dict[str, list[tuple[int, str, float]]] = collections.defaultdict(list)
    for jar in sorted((ROOT / "mods").glob("*.jar")):
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
                if kind not in TIERS:
                    continue
                for item in set(ids(recipe.get("result") or recipe.get("results") or [])):
                    produced, consumed = yield_of(recipe, item)
                    if produced:
                        ladders[item].append((TIERS[kind], kind, produced / consumed))

    broken = []
    for item, rows in sorted(ladders.items()):
        best_by_tier: dict[int, float] = {}
        for tier, _, ratio in rows:
            best_by_tier[tier] = max(best_by_tier.get(tier, 0.0), ratio)
        tiers = sorted(best_by_tier)
        for lower, higher in zip(tiers, tiers[1:]):
            if best_by_tier[lower] >= best_by_tier[higher]:
                broken.append((item, lower, best_by_tier[lower], higher, best_by_tier[higher]))

    multi = sum(1 for rows in ladders.values() if len({tier for tier, _, _ in rows}) > 1)
    print(f"операций в сборке: {len(ladders)}; с несколькими ступенями: {multi}")
    print(f"\nСЛОМАННЫХ ЛЕСТНИЦ: {len(broken)}")
    by_gap = sorted(broken, key=lambda row: row[4] - row[2])
    for item, lower, low_ratio, higher, high_ratio in by_gap[:25]:
        print(f"  {item:36} ступень {lower}: {low_ratio:.2f}  →  ступень {higher}: {high_ratio:.2f}")
    report = ROOT / "build" / "yield_ladder_audit.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({
        "schema_version": 1,
        "operations": len(ladders),
        "multi_tier": multi,
        "broken": [
            {"item": item, "lower_tier": lower, "lower_yield": low, "higher_tier": higher, "higher_yield": high}
            for item, lower, low, higher, high in broken
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nполный список: {report}")
    print("\nОценка считает предметы и не видит энергию, время и жидкости:"
          " спорные случаи решает человек.")
    print("Minecraft не запускался.")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
