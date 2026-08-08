#!/usr/bin/env python3
"""Static validation for pack-owned quest acceptance sets.

This tool never starts Minecraft. It checks registry structure, Russian-facing copy,
tag parity, duplicate membership and locally exported GTCEu item identifiers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


RU_RE = re.compile(r"[А-Яа-яЁё]")
ID_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")


def read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def flatten_gtceu_items(census: dict) -> set[str]:
    result: set[str] = set()
    for values in census.get("groups", {}).values():
        if isinstance(values, list):
            result.update(value for value in values if isinstance(value, str))
    return result


def tag_path(root: Path, implementation: str, tag_id: str) -> Path:
    namespace, name = tag_id.split(":", 1)
    kind = "items" if implementation == "ITEM_TAG" else "fluids"
    return (
        root
        / "config"
        / "paxi"
        / "datapacks"
        / "IndustrialFrontier-Data"
        / "data"
        / namespace
        / "tags"
        / kind
        / f"{name}.json"
    )


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    registry_path = root / "docs" / "registries" / "quest_acceptance_sets.json"
    census_path = root / "kubejs" / "exported" / "gtceu_item_census.json"
    registry = read_json(registry_path)
    if not isinstance(registry, dict):
        return ["registry root must be an object"]

    for field in ("policy_ru", "editorial_policy_ru"):
        value = registry.get(field)
        if not isinstance(value, str) or len(value.strip()) < 12 or not RU_RE.search(value):
            errors.append(f"{field}: expected substantive primary Russian copy")

    sets = registry.get("sets")
    if not isinstance(sets, list) or not sets:
        return errors + ["sets: expected a non-empty array"]

    gtceu_items = flatten_gtceu_items(read_json(census_path))
    seen_ids: set[str] = set()
    seen_tags: set[tuple[str, str]] = set()

    for index, entry in enumerate(sets):
        where = f"sets[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: expected object")
            continue
        set_id = entry.get("set_id")
        if not isinstance(set_id, str) or not set_id.startswith("industrial_frontier:quest_set/"):
            errors.append(f"{where}.set_id: invalid identifier")
        elif set_id in seen_ids:
            errors.append(f"{where}.set_id: duplicate {set_id}")
        else:
            seen_ids.add(set_id)

        for field in ("title_ru", "capability_ru"):
            value = entry.get(field)
            if not isinstance(value, str) or len(value.strip()) < 12 or not RU_RE.search(value):
                errors.append(f"{where}.{field}: expected natural primary Russian copy")

        if entry.get("copy_status") != "RU_PRIMARY_REVIEWED":
            errors.append(f"{where}.copy_status: must be RU_PRIMARY_REVIEWED")

        implementation = entry.get("implementation")
        tag_id = entry.get("tag_id")
        values = entry.get("values")
        if implementation not in {"ITEM_TAG", "FLUID_TAG", "ONE_OF_ITEMS"}:
            errors.append(f"{where}.implementation: unsupported value")
            continue
        if not isinstance(tag_id, str) or not ID_RE.fullmatch(tag_id):
            errors.append(f"{where}.tag_id: invalid resource identifier")
            continue
        if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values):
            errors.append(f"{where}.values: expected non-empty string array")
            continue
        if len(values) != len(set(values)):
            errors.append(f"{where}.values: duplicate entries")

        if implementation in {"ITEM_TAG", "FLUID_TAG"}:
            key = (implementation, tag_id)
            if key in seen_tags:
                errors.append(f"{where}.tag_id: duplicate ownership of {tag_id}")
            seen_tags.add(key)
            path = tag_path(root, implementation, tag_id)
            if not path.is_file():
                errors.append(f"{where}.tag_id: missing tag file {path.relative_to(root)}")
            else:
                tag = read_json(path)
                actual = tag.get("values") if isinstance(tag, dict) else None
                if actual != values:
                    errors.append(f"{where}.values: registry/tag order or membership mismatch")

        if implementation != "FLUID_TAG":
            for value in values:
                if value.startswith("gtceu:") and value not in gtceu_items:
                    errors.append(f"{where}.values: GTCEu census does not contain {value}")

        excluded = entry.get("excluded")
        if not isinstance(excluded, list):
            errors.append(f"{where}.excluded: expected array")
        else:
            for ex_index, exclusion in enumerate(excluded):
                if not isinstance(exclusion, dict):
                    errors.append(f"{where}.excluded[{ex_index}]: expected object")
                    continue
                reason = exclusion.get("reason_ru")
                if not isinstance(reason, str) or len(reason.strip()) < 12 or not RU_RE.search(reason):
                    errors.append(f"{where}.excluded[{ex_index}].reason_ru: expected Russian reason")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate(root)
    if errors:
        print("quest acceptance set validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    registry = read_json(root / "docs" / "registries" / "quest_acceptance_sets.json")
    print(f"quest acceptance set validation: PASS ({len(registry['sets'])} sets)")
    print("runtime task matching remains USER_PENDING; Minecraft was not started")
    return 0


if __name__ == "__main__":
    sys.exit(main())
