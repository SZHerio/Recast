#!/usr/bin/env python3
"""Validate representative structure tags without starting Minecraft."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


RU_RE = re.compile(r"[А-Яа-яЁё]")
ID_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")


def read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / "docs" / "registries" / "quest_world_structure_sets.json"
    registry = read_json(path)
    if not isinstance(registry, dict):
        return ["registry root must be an object"]
    if registry.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if registry.get("registry_id") != "industrial_frontier:quest/world_structure_sets":
        errors.append("registry_id is invalid")
    policy = registry.get("policy_ru")
    if not isinstance(policy, str) or len(policy.strip()) < 12 or not RU_RE.search(policy):
        errors.append("policy_ru must contain substantive Russian copy")

    sets = registry.get("sets")
    if not isinstance(sets, list) or not sets:
        return errors + ["sets must be a non-empty array"]
    seen_sets: set[str] = set()
    seen_tags: set[str] = set()
    opened_jars: dict[str, set[str]] = {}

    for index, entry in enumerate(sets):
        where = f"sets[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: expected object")
            continue
        set_id = entry.get("set_id")
        if not isinstance(set_id, str) or not set_id.startswith("industrial_frontier:quest_set/world/"):
            errors.append(f"{where}.set_id: invalid")
        elif set_id in seen_sets:
            errors.append(f"{where}.set_id: duplicate {set_id}")
        else:
            seen_sets.add(set_id)
        for field in ("title_ru", "capability_ru"):
            value = entry.get(field)
            if not isinstance(value, str) or len(value.strip()) < 12 or not RU_RE.search(value):
                errors.append(f"{where}.{field}: expected natural Russian copy")

        tag_id = entry.get("tag_id")
        if not isinstance(tag_id, str) or not ID_RE.fullmatch(tag_id):
            errors.append(f"{where}.tag_id: invalid")
        elif tag_id in seen_tags:
            errors.append(f"{where}.tag_id: duplicate owner {tag_id}")
        else:
            seen_tags.add(tag_id)
        tag_file = entry.get("tag_file")
        if not isinstance(tag_file, str):
            errors.append(f"{where}.tag_file: expected path")
            continue
        tag_path = root / tag_file
        if not tag_path.is_file():
            errors.append(f"{where}.tag_file: missing {tag_file}")
            continue

        values = entry.get("values")
        if not isinstance(values, list) or not values:
            errors.append(f"{where}.values: expected non-empty array")
            continue
        ids = [item.get("id") for item in values if isinstance(item, dict)]
        if len(ids) != len(values) or any(not isinstance(item, str) or not ID_RE.fullmatch(item) for item in ids):
            errors.append(f"{where}.values: every entry needs a valid id")
            continue
        if len(ids) != len(set(ids)):
            errors.append(f"{where}.values: duplicate structure id")
        tag = read_json(tag_path)
        actual = tag.get("values") if isinstance(tag, dict) else None
        if actual != ids:
            errors.append(f"{where}.values: registry and tag membership/order differ")

        for item_index, item in enumerate(values):
            jar_name = item.get("source_jar")
            if not isinstance(jar_name, str):
                errors.append(f"{where}.values[{item_index}].source_jar: expected filename")
                continue
            jar_path = root / "mods" / jar_name
            if not jar_path.is_file():
                errors.append(f"{where}.values[{item_index}]: missing mods/{jar_name}")
                continue
            if jar_name not in opened_jars:
                try:
                    with zipfile.ZipFile(jar_path) as archive:
                        opened_jars[jar_name] = set(archive.namelist())
                except (OSError, zipfile.BadZipFile) as exc:
                    errors.append(f"{where}.values[{item_index}]: cannot read {jar_name}: {exc}")
                    continue
            namespace, name = item["id"].split(":", 1)
            member = f"data/{namespace}/worldgen/structure/{name}.json"
            if member not in opened_jars.get(jar_name, set()):
                errors.append(f"{where}.values[{item_index}]: {member} not found in {jar_name}")
        if entry.get("runtime_gate") != "USER_STRUCTURE_TASK_MATCH_PENDING":
            errors.append(f"{where}.runtime_gate: invalid state")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate(root)
    if errors:
        print("quest world structure set validation: FAIL")
        for error in errors:
            print(f"- {error}")
        print("Minecraft was not started")
        return 1
    registry = read_json(root / "docs" / "registries" / "quest_world_structure_sets.json")
    print(f"quest world structure set validation: PASS ({len(registry['sets'])} sets)")
    print("runtime structure-task matching remains USER_PENDING; Minecraft was not started")
    return 0


if __name__ == "__main__":
    sys.exit(main())
