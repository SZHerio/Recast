#!/usr/bin/env python3
"""Static validator for the isolated Quest Source v2 authoring contour.

The validator reads only JSON/SNBT files.  It never imports Minecraft classes,
starts Forge, edits runtime quests, or touches the shared language pack.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict, deque
from typing import Any, Iterable


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = pathlib.Path("authoring/questbook_v2")
DEFAULT_SCHEMA = pathlib.Path("authoring/schemas/quest_source_v2.schema.json")
DEFAULT_BUILD = pathlib.Path("build/questbook_v2")

EPOCHS = [f"P{i}" for i in range(10)]
EPOCH_INDEX = {epoch: index for index, epoch in enumerate(EPOCHS)}
REVIEW_MARKS = [
    "RU_PRIMARY_DRAFTED",
    "RU_TECH_CHECKED",
    "RU_STYLE_REVIEWED",
    "RU_FLOW_REVIEWED",
]
REVIEW_STATES = REVIEW_MARKS + ["RU_READY"]
PLACEHOLDER_RE = re.compile(
    r"(?:\bTODO\b|\bTBD\b|\bFIXME\b|PLACEHOLDER|LOREM\s+IPSUM|"
    r"ЗАГЛУШК|ДОПИСАТЬ|НАПИСАТЬ\s+ПОЗЖЕ|ПЕРЕВЕСТИ|МАШИНН(?:ЫЙ|ОГО)\s+ПЕРЕВОД|"
    r"N/?A|\?{3,}|<{2,}|>{2,}|\{\{.+?\}\})",
    re.IGNORECASE,
)
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
RESOURCE_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
INTERNAL_JARGON_RE = re.compile(
    r"(?:\bproof(?:s)?\b|\bruntime(?:[- ]?gate)?\b|\bengine[_ -]?id\b|"
    r"\bquest\s*source\b|\btask[- ]?adapter\b|\bcommissioning\b|"
    r"\b(?:алиас|рантайм|гейт|валидатор|адаптер\s+задач|движковый\s+id)\b|"
    r"объективн(?:ая|ое|ую)\s+(?:предметн(?:ая|ое|ую)\s+)?проверк)",
    re.IGNORECASE,
)
RAW_RESOURCE_IN_PLAYER_RE = re.compile(r"(?<![/\w])[a-z0-9_.-]+:[a-z0-9_./-]+(?![\w/])")
RAW_SNAKE_IN_PLAYER_RE = re.compile(r"(?<![/\w])[a-z][a-z0-9]*(?:_[a-z0-9]+){1,}(?![\w/])")
MOJIBAKE_RE = re.compile(r"(?:Рџ|РЎ|РЃ|СЂР|С‚Р|РЅР|вЂ|в„–)")

# Every emitted adapter is backed by the installed class' writeData bytecode or
# by an existing compiled chapter.  This table is also written to reports by the
# compiler so a mod upgrade cannot be mistaken for proven compatibility.
VERIFIED_ADAPTERS: dict[str, dict[str, Any]] = {
    "item": {
        "runtime_type": "item",
        "evidence": [
            "config/ftbquests/quests/chapters/00_start_here.snbt",
            "mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.ItemTask#writeData",
        ],
    },
    "checkmark": {
        "runtime_type": "checkmark",
        "evidence": ["config/ftbquests/quests/chapters/00_start_here.snbt"],
    },
    "dimension": {
        "runtime_type": "dimension",
        "evidence": [
            "config/ftbquests/quests/chapters/00_start_here.snbt",
            "mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.DimensionTask#writeData",
        ],
    },
    "fluid": {
        "runtime_type": "fluid",
        "evidence": ["mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.FluidTask#writeData"],
    },
    "energy": {
        "runtime_type": "forge_energy",
        "evidence": [
            "mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.EnergyTask#writeData",
            "mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.forge.FTBQuestsForge#forge_energy",
        ],
    },
    "structure": {
        "runtime_type": "structure",
        "evidence": ["mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.StructureTask#writeData"],
    },
    "location": {
        "runtime_type": "location",
        "evidence": ["mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.LocationTask#writeData"],
    },
    "biome": {
        "runtime_type": "biome",
        "evidence": ["mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.BiomeTask#writeData"],
    },
    "kill": {
        "runtime_type": "kill",
        "evidence": ["mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.KillTask#writeData"],
    },
    "stage": {
        "runtime_type": "gamestage",
        "evidence": ["mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.StageTask#writeData"],
    },
    "observation": {
        "runtime_type": "observation",
        "evidence": [
            "mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.ObservationTask#writeData",
            "mods/ftb-quests-forge-2001.4.22.jar!dev.ftb.mods.ftbquests.quest.task.ObservationTask$ObserveType",
        ],
    },
    "place": {
        "runtime_type": "questsadditions:place",
        "evidence": [
            "mods/questsadditions-1.4.7.jar!questsadditions.tasks.BlockInteractionTask#writeData",
            "mods/questsadditions-1.4.7.jar!questsadditions.tasks.PlaceTask#writeData",
            "mods/questsadditions-1.4.7.jar!questsadditions.tasks.TasksRegistry#PLACE",
        ],
    },
    "use": {
        "runtime_type": "questsadditions:use",
        "evidence": [
            "mods/questsadditions-1.4.7.jar!questsadditions.tasks.BlockInteractionTask#writeData",
            "mods/questsadditions-1.4.7.jar!questsadditions.tasks.UseTask#writeData",
            "mods/questsadditions-1.4.7.jar!questsadditions.tasks.TasksRegistry#USE",
        ],
    },
}


@dataclasses.dataclass(frozen=True)
class Issue:
    level: str
    code: str
    path: str
    message: str


@dataclasses.dataclass
class Project:
    root: pathlib.Path
    source_dir: pathlib.Path
    schema: dict[str, Any]
    chapters: list[dict[str, Any]]
    chapter_files: dict[str, str]
    migrations: list[dict[str, Any]]
    migration_files: dict[str, str]


def _json_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local schema references are supported: {ref}")
    node: Any = root_schema
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        node = node[token]
    if not isinstance(node, dict):
        raise ValueError(f"Schema reference does not resolve to an object: {ref}")
    return node


def _schema_issues(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
) -> list[str]:
    """Evaluate the JSON-Schema keywords used by quest_source_v2.schema.json."""
    if "$ref" in schema:
        return _schema_issues(value, _resolve_ref(root_schema, schema["$ref"]), root_schema, path)

    errors: list[str] = []
    expected = schema.get("type")
    if expected is not None:
        allowed = [expected] if isinstance(expected, str) else list(expected)
        if not any(_json_type(value, item) for item in allowed):
            return [f"{path}: expected {' or '.join(allowed)}, got {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']!r}")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: string is shorter than {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: string is longer than {schema['maxLength']}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: {value!r} does not match /{schema['pattern']}/")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: value {value} is below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: value {value} is above {schema['maximum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: value {value} must be greater than {schema['exclusiveMinimum']}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: array has fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: array has more than {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{path}: array items are not unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_schema_issues(item, item_schema, root_schema, f"{path}[{index}]"))

    if isinstance(value, dict):
        for required in schema.get("required", []):
            if required not in value:
                errors.append(f"{path}: missing required property {required!r}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                errors.extend(_schema_issues(item, properties[key], root_schema, f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property {key!r}")

    for sub in schema.get("allOf", []):
        errors.extend(_schema_issues(value, sub, root_schema, path))
    if "oneOf" in schema:
        matches = sum(not _schema_issues(value, sub, root_schema, path) for sub in schema["oneOf"])
        if matches != 1:
            errors.append(f"{path}: expected exactly one oneOf branch, matched {matches}")
    if "anyOf" in schema:
        matches = sum(not _schema_issues(value, sub, root_schema, path) for sub in schema["anyOf"])
        if matches == 0:
            errors.append(f"{path}: expected at least one anyOf branch to match")
    if "not" in schema and not _schema_issues(value, schema["not"], root_schema, path):
        errors.append(f"{path}: value matches a forbidden schema")
    if "if" in schema:
        condition_matches = not _schema_issues(value, schema["if"], root_schema, path)
        selected = schema.get("then") if condition_matches else schema.get("else")
        if isinstance(selected, dict):
            errors.extend(_schema_issues(value, selected, root_schema, path))
    return errors


def _read_json(path: pathlib.Path, issues: list[Issue]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(Issue("ERROR", "QV2-JSON", str(path), str(exc)))
        return None
    if not isinstance(value, dict):
        issues.append(Issue("ERROR", "QV2-JSON-ROOT", str(path), "JSON root must be an object."))
        return None
    return value


def load_project(
    root: pathlib.Path = ROOT,
    source: pathlib.Path = DEFAULT_SOURCE,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
) -> tuple[Project, list[Issue]]:
    root = root.resolve()
    source_dir = source if source.is_absolute() else root / source
    schema_file = schema_path if schema_path.is_absolute() else root / schema_path
    issues: list[Issue] = []
    schema = _read_json(schema_file, issues) or {}
    chapters: list[dict[str, Any]] = []
    chapter_files: dict[str, str] = {}
    migrations: list[dict[str, Any]] = []
    migration_files: dict[str, str] = {}

    if not source_dir.is_dir():
        issues.append(Issue("ERROR", "QV2-SOURCE-MISSING", str(source_dir), "Quest Source v2 directory does not exist."))
        return Project(root, source_dir, schema, chapters, chapter_files, migrations, migration_files), issues

    for path in sorted(source_dir.rglob("*.json"), key=lambda item: item.as_posix().lower()):
        relative = path.relative_to(source_dir).as_posix()
        value = _read_json(path, issues)
        if value is None:
            continue
        if "migrations" in path.relative_to(source_dir).parts or value.get("source_kind") == "quest_migration":
            migrations.append(value)
            migration_files[str(value.get("migration_id", relative))] = relative
            continue
        schema_errors = _schema_issues(value, schema, schema, "$") if schema else ["schema could not be loaded"]
        for message in schema_errors:
            issues.append(Issue("ERROR", "QV2-SCHEMA", relative, message))
        chapters.append(value)
        chapter_alias = str(value.get("chapter", {}).get("alias", relative))
        chapter_files[chapter_alias] = relative

    if not chapters:
        issues.append(Issue("ERROR", "QV2-NO-CHAPTERS", str(source_dir), "No quest_chapter JSON sources were found."))
    return Project(root, source_dir, schema, chapters, chapter_files, migrations, migration_files), issues


def _flatten_ru_text(quest: dict[str, Any]) -> list[tuple[str, str]]:
    text = quest.get("text_ru", {})
    result: list[tuple[str, str]] = []
    for key in ("title_ru", "lead_ru", "purpose_ru", "success_ru", "next_ru", "task_text_ru", "optional_note_ru"):
        value = text.get(key)
        if isinstance(value, str):
            result.append((key, value))
    for key in ("steps_ru", "diagnostics_ru"):
        for index, value in enumerate(text.get(key, []) if isinstance(text.get(key), list) else []):
            if isinstance(value, str):
                result.append((f"{key}[{index}]", value))
    for pindex, proof in enumerate(quest.get("proofs", [])):
        proof_text = proof.get("text_ru", {})
        for key in ("objective", "help"):
            value = proof_text.get(key)
            if isinstance(value, str):
                result.append((f"proofs[{pindex}].text_ru.{key}", value))
    return result


def _ancestors(alias: str, dependencies: dict[str, list[str]], memo: dict[str, set[str]]) -> set[str]:
    if alias in memo:
        return memo[alias]
    result: set[str] = set()
    for dep in dependencies.get(alias, []):
        result.add(dep)
        result.update(_ancestors(dep, dependencies, memo))
    memo[alias] = result
    return result


def _pack_item_tag_members(root: pathlib.Path, tag_id: str, seen: set[str] | None = None) -> set[str] | None:
    """Resolve author-owned item tags used as static migration evidence."""
    seen = set() if seen is None else seen
    if tag_id in seen or ":" not in tag_id:
        return None
    seen.add(tag_id)
    namespace, path = tag_id.split(":", 1)
    candidates = sorted(
        (root / "config/paxi/datapacks").glob(f"*/data/{namespace}/tags/items/{path}.json")
    )
    candidates += sorted((root / "kubejs/data").glob(f"{namespace}/tags/items/{path}.json"))
    if not candidates:
        return None
    members: set[str] = set()
    for candidate in candidates:
        try:
            document = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None
        if document.get("replace") is True:
            members.clear()
        for raw_value in document.get("values", []):
            value = raw_value.get("id") if isinstance(raw_value, dict) else raw_value
            if not isinstance(value, str):
                continue
            if value.startswith("#"):
                nested = _pack_item_tag_members(root, value[1:], seen)
                if nested is None:
                    return None
                members.update(nested)
            else:
                members.add(value)
    return members


def _old_task_implies_v2(
    root: pathlib.Path,
    task: dict[str, Any],
    quest: dict[str, Any],
) -> tuple[bool, str]:
    proofs = quest.get("proofs", []) if isinstance(quest.get("proofs"), list) else []
    if len(proofs) != 1 or proofs[0].get("status") != "verified":
        return False, "the successor must have exactly one verified proof"
    proof = proofs[0]
    predicate = task.get("predicate", {})
    old_type = task.get("type")
    if old_type != proof.get("type"):
        return False, f"QR0 type {old_type!r} does not imply v2 type {proof.get('type')!r}"
    if old_type == "checkmark":
        return True, "same manually reviewed checkmark contract"
    if old_type == "dimension":
        same = predicate.get("dimension") == proof.get("dimension")
        return same, "same dimension" if same else "dimension target changed"
    if old_type != "item" or not isinstance(predicate.get("selector"), dict):
        return False, "unsupported or incomplete frozen QR0 predicate"

    old_selector = predicate["selector"]
    if isinstance(proof.get("item"), dict):
        new_selector = {"kind": "item", "id": proof["item"].get("id")}
        new_count = int(proof["item"].get("count", 1))
        new_payload = proof["item"]
    elif isinstance(proof.get("item_tag"), dict):
        new_selector = {"kind": "item_tag", "id": proof["item_tag"].get("id")}
        new_count = int(proof["item_tag"].get("count", 1))
        new_payload = proof["item_tag"]
    else:
        return False, "v2 item proof has no supported item or item-tag selector"
    if int(predicate.get("count", 0)) < new_count:
        return False, f"QR0 count {predicate.get('count')} is below v2 count {new_count}"
    if old_selector == new_selector:
        selector_implies = True
    elif old_selector.get("kind") == "item" and new_selector.get("kind") == "item_tag":
        members = _pack_item_tag_members(root, str(new_selector.get("id", "")))
        selector_implies = members is not None and old_selector.get("id") in members
    else:
        selector_implies = False
    if not selector_implies:
        return False, f"QR0 selector {old_selector!r} does not imply v2 selector {new_selector!r}"
    for flag in ("only_from_crafting", "match_nbt", "weak_nbt_match"):
        if bool(new_payload.get(flag, False)) and not bool(predicate.get(flag, False)):
            return False, f"v2 strengthens the {flag} predicate"
    return True, "the frozen QR0 item predicate statically implies the v2 proof"


def _validate_migrations(project: Project, quests: dict[str, dict[str, Any]], issues: list[Issue]) -> dict[str, Any]:
    baseline_path = project.root / "docs/registries/quest_rebuild_baseline.json"
    stable_path = project.root / "docs/registries/stable_ids.json"
    retired_path = project.root / "docs/registries/retired_ids.json"
    retired_schema_path = project.root / "authoring/schemas/retired_ids.schema.json"
    proof_contracts_path = project.root / "docs/registries/quest_qr0_proof_contracts.json"
    proof_contracts_schema_path = project.root / "authoring/schemas/quest_qr0_proof_contracts.schema.json"
    migration_schema_path = project.root / "authoring/schemas/quest_migration.schema.json"

    baseline = _read_json(baseline_path, issues) or {}
    stable = _read_json(stable_path, issues) or {}
    retired_registry = _read_json(retired_path, issues) or {}
    retired_schema = _read_json(retired_schema_path, issues) or {}
    proof_contracts_registry = _read_json(proof_contracts_path, issues) or {}
    proof_contracts_schema = _read_json(proof_contracts_schema_path, issues) or {}
    migration_schema = _read_json(migration_schema_path, issues) or {}

    baseline_rows = baseline.get("quests", []) if isinstance(baseline.get("quests"), list) else []
    old_by_id = {
        str(row.get("engine_id")): row
        for row in baseline_rows
        if isinstance(row, dict) and isinstance(row.get("engine_id"), str)
    }
    old_by_alias = {
        str(row.get("alias")): row
        for row in baseline_rows
        if isinstance(row, dict) and isinstance(row.get("alias"), str)
    }
    if len(old_by_id) != len(baseline_rows) or len(old_by_alias) != len(baseline_rows):
        issues.append(Issue(
            "ERROR",
            "QV2-MIGRATION-BASELINE-IDENTITY",
            str(baseline_path),
            "QR0 baseline quest aliases and engine IDs must both be unique.",
        ))

    if proof_contracts_schema:
        for message in _schema_issues(
            proof_contracts_registry,
            proof_contracts_schema,
            proof_contracts_schema,
            "$",
        ):
            issues.append(Issue("ERROR", "QV2-MIGRATION-PROOF-SCHEMA", str(proof_contracts_path), message))
    proof_contract_rows = (
        proof_contracts_registry.get("quests", [])
        if isinstance(proof_contracts_registry.get("quests"), list)
        else []
    )
    proof_contract_by_old_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(proof_contract_rows):
        where = f"{proof_contracts_path}:quests[{index}]"
        if not isinstance(row, dict) or not isinstance(row.get("quest_engine_id"), str):
            issues.append(Issue("ERROR", "QV2-MIGRATION-PROOF-ENTRY", where, "Proof contract needs a quest_engine_id."))
            continue
        old_id = str(row["quest_engine_id"])
        if old_id in proof_contract_by_old_id:
            issues.append(Issue("ERROR", "QV2-MIGRATION-PROOF-DUPLICATE", where, f"Duplicate proof contract for {old_id}."))
        proof_contract_by_old_id[old_id] = row
        baseline_row = old_by_id.get(old_id)
        task = row.get("task", {}) if isinstance(row.get("task"), dict) else {}
        if baseline_row is None:
            issues.append(Issue("ERROR", "QV2-MIGRATION-PROOF-SOURCE", where, f"Proof contract {old_id} is absent from QR0."))
        else:
            if row.get("old_alias") != baseline_row.get("alias") or task.get("type") != baseline_row.get("task_type"):
                issues.append(Issue(
                    "ERROR",
                    "QV2-MIGRATION-PROOF-SOURCE",
                    where,
                    "Frozen proof alias or type differs from the QR0 baseline.",
                ))
            if task.get("engine_id") != "4" + old_id[1:]:
                issues.append(Issue(
                    "ERROR",
                    "QV2-MIGRATION-PROOF-TASK-ID",
                    where,
                    f"Frozen QR0 task ID must be {'4' + old_id[1:]}.",
                ))
    for old_id in sorted(set(old_by_id) - set(proof_contract_by_old_id)):
        issues.append(Issue(
            "ERROR",
            "QV2-MIGRATION-PROOF-MISSING",
            str(proof_contracts_path),
            f"QR0 quest {old_id} has no frozen executable proof contract.",
        ))

    stable_alias_by_id = {
        str(engine_id): str(alias)
        for alias, engine_id in stable.get("ids", {}).items()
        if isinstance(alias, str) and alias.startswith("if.quest.")
    } if isinstance(stable.get("ids"), dict) else {}
    stable_all_ids = {
        str(engine_id)
        for engine_id in stable.get("ids", {}).values()
    } if isinstance(stable.get("ids"), dict) else set()

    if retired_schema:
        for message in _schema_issues(retired_registry, retired_schema, retired_schema, "$"):
            issues.append(Issue("ERROR", "QV2-RETIRED-SCHEMA", str(retired_path), message))
    retired_rows = retired_registry.get("retired", []) if isinstance(retired_registry.get("retired"), list) else []
    retired_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(retired_rows):
        where = f"{retired_path}:retired[{index}]"
        if not isinstance(item, dict) or not isinstance(item.get("engine_id"), str):
            issues.append(Issue("ERROR", "QV2-RETIRED-ENTRY", where, "Retired entry needs an engine_id."))
            continue
        engine_id = str(item["engine_id"])
        if engine_id in retired_by_id:
            issues.append(Issue("ERROR", "QV2-RETIRED-DUPLICATE", where, f"Retired ID {engine_id} is duplicated."))
        retired_by_id[engine_id] = item

    current_ids: set[str] = set()
    current_proof_ids: set[str] = set()
    for document in project.chapters:
        chapter = document.get("chapter", {})
        current_ids.update(
            str(value)
            for value in (chapter.get("engine_id"), chapter.get("group", {}).get("engine_id"))
            if isinstance(value, str)
        )
        for quest in document.get("quests", []):
            if isinstance(quest.get("engine_id"), str):
                current_ids.add(str(quest["engine_id"]))
            for proof in quest.get("proofs", []):
                if isinstance(proof.get("engine_id"), str):
                    proof_id = str(proof["engine_id"])
                    current_ids.add(proof_id)
                    current_proof_ids.add(proof_id)
    for engine_id in sorted(current_ids & set(retired_by_id)):
        issues.append(Issue(
            "ERROR",
            "QV2-RETIRED-ID-REUSED",
            str(retired_path),
            f"Retired engine ID {engine_id} is still used by Quest Source v2.",
        ))
    for engine_id in sorted(stable_all_ids - current_ids - set(retired_by_id)):
        issues.append(Issue(
            "ERROR",
            "QV2-RETIRED-ID-MISSING",
            str(retired_path),
            f"Historical engine ID {engine_id} is inactive in v2 but has no retirement tombstone.",
        ))

    mapped_old_aliases: set[str] = set()
    mapped_old_ids: Counter[str] = Counter()
    mappings: list[dict[str, Any]] = []
    mapping_locations: list[str] = []
    seen_migration_ids: set[str] = set()
    target_rows: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for document in project.migrations:
        migration_id = document.get("migration_id")
        path = project.migration_files.get(str(migration_id), "migrations")
        if migration_schema:
            for message in _schema_issues(document, migration_schema, migration_schema, "$"):
                issues.append(Issue("ERROR", "QV2-MIGRATION-JSON-SCHEMA", path, message))
        for required_field in ("schema_version", "migration_id", "from_book", "to_book", "mappings"):
            if required_field not in document:
                issues.append(Issue("ERROR", "QV2-MIGRATION-FIELD", path, f"Migration is missing {required_field}."))
        if not isinstance(migration_id, str) or not migration_id:
            issues.append(Issue("ERROR", "QV2-MIGRATION-ID", path, "Migration needs a non-empty migration_id."))
            continue
        if migration_id in seen_migration_ids:
            issues.append(Issue("ERROR", "QV2-MIGRATION-DUPLICATE", path, f"Duplicate migration_id {migration_id}."))
        seen_migration_ids.add(migration_id)
        if document.get("schema_version") != 2:
            issues.append(Issue("ERROR", "QV2-MIGRATION-SCHEMA", path, "Migration schema_version must be 2."))
        raw_mappings = document.get("mappings", [])
        if not isinstance(raw_mappings, list):
            issues.append(Issue("ERROR", "QV2-MIGRATION-MAPPINGS", path, "mappings must be an array."))
            raw_mappings = []
        for index, mapping in enumerate(raw_mappings):
            where = f"{path}:mappings[{index}]"
            if not isinstance(mapping, dict):
                issues.append(Issue("ERROR", "QV2-MIGRATION-MAPPING", where, "Mapping must be an object."))
                continue
            policy = mapping.get("policy")
            for required_field in ("old_alias", "old_engine_id", "new_alias", "new_engine_id", "policy", "reason", "evidence"):
                if required_field not in mapping:
                    issues.append(Issue("ERROR", "QV2-MIGRATION-MAPPING-FIELD", where, f"Mapping is missing {required_field}."))
            if policy not in {"carry", "review", "reset"}:
                issues.append(Issue("ERROR", "QV2-MIGRATION-POLICY", where, f"Unknown policy {policy!r}."))

            new_alias = mapping.get("new_alias")
            new_id = mapping.get("new_engine_id")
            target = quests.get(str(new_alias)) if isinstance(new_alias, str) else None
            if target is None:
                issues.append(Issue("ERROR", "QV2-MIGRATION-TARGET", where, f"Unknown v2 quest {new_alias!r}."))
            elif new_id != target.get("engine_id"):
                issues.append(Issue("ERROR", "QV2-MIGRATION-TARGET-ID", where, "new_engine_id does not match the v2 source."))

            old_alias = mapping.get("old_alias")
            old_id = mapping.get("old_engine_id")
            old = old_by_id.get(str(old_id)) if isinstance(old_id, str) else None
            if isinstance(old_id, str):
                mapped_old_ids[old_id] += 1
            if isinstance(old_alias, str):
                mapped_old_aliases.add(old_alias)
            if old is None:
                issues.append(Issue(
                    "ERROR",
                    "QV2-MIGRATION-SOURCE-ID",
                    where,
                    f"old_engine_id {old_id!r} is absent from the frozen QR0 baseline.",
                ))
            else:
                expected_alias = str(old.get("alias"))
                if old_alias != expected_alias:
                    issues.append(Issue(
                        "ERROR",
                        "QV2-MIGRATION-SOURCE-ALIAS",
                        where,
                        f"QR0 engine ID {old_id} belongs to {expected_alias}, not {old_alias!r}.",
                    ))
                runtime_alias = stable_alias_by_id.get(str(old_id))
                documented_runtime_alias = mapping.get("old_runtime_alias")
                if runtime_alias and runtime_alias != expected_alias:
                    if documented_runtime_alias != runtime_alias:
                        issues.append(Issue(
                            "ERROR",
                            "QV2-MIGRATION-SOURCE-DRIFT",
                            where,
                            f"QR0 authoring/runtime alias drift must be documented as old_runtime_alias={runtime_alias!r}.",
                        ))
                elif documented_runtime_alias not in {None, expected_alias}:
                    issues.append(Issue(
                        "ERROR",
                        "QV2-MIGRATION-SOURCE-DRIFT",
                        where,
                        "old_runtime_alias is present but does not describe a QR0 alias drift.",
                    ))

            evidence = mapping.get("evidence")
            reason = mapping.get("reason")
            if not isinstance(reason, str) or len(reason.strip()) < 12 or not isinstance(evidence, list) or not evidence:
                issues.append(Issue("ERROR", "QV2-MIGRATION-EVIDENCE", where, "Every mapping needs a reason and non-empty evidence."))

            if policy == "carry" and old_id != new_id:
                issues.append(Issue("ERROR", "QV2-MIGRATION-CARRY-ID", where, "carry requires the same quest engine ID; no runtime progress converter exists."))
            if policy == "carry" and old is not None and target is not None:
                contract_row = proof_contract_by_old_id.get(str(old_id), {})
                old_task = contract_row.get("task", {}) if isinstance(contract_row.get("task"), dict) else {}
                old_type = old_task.get("type", old.get("task_type"))
                new_proofs = target.get("proofs", []) if isinstance(target.get("proofs"), list) else []
                safe, detail = _old_task_implies_v2(project.root, old_task, target)
                if not safe:
                    issues.append(Issue(
                        "ERROR",
                        "QV2-MIGRATION-CARRY-PROOF-CONTRACT",
                        where,
                        f"QR0 completion does not imply every v2 proof: {detail}.",
                    ))
                old_task_id = str(old_task.get("engine_id", "4" + str(old_id)[1:]))
                if len(new_proofs) == 1 and new_proofs[0].get("engine_id") != old_task_id:
                    issues.append(Issue(
                        "ERROR",
                        "QV2-MIGRATION-CARRY-TASK-ID",
                        where,
                        f"carry must preserve the QR0 task ID {old_task_id} for partial progress.",
                    ))
                if old_type == "checkmark" and target.get("role") == "commissioning":
                    issues.append(Issue(
                        "ERROR",
                        "QV2-MIGRATION-CHECKMARK-COMMISSIONING",
                        where,
                        "A QR0 checkmark cannot carry into a v2 commissioning gate.",
                    ))

            if policy in {"review", "reset"} and old is not None and target is not None:
                contract_row = proof_contract_by_old_id.get(str(old_id), {})
                old_task = contract_row.get("task", {}) if isinstance(contract_row.get("task"), dict) else {}
                old_task_id = str(old_task.get("engine_id", "4" + str(old_id)[1:]))
                if old_id == target.get("engine_id"):
                    issues.append(Issue(
                        "ERROR",
                        "QV2-MIGRATION-REVIEW-ID-REUSED",
                        where,
                        "review/reset must use a new quest engine ID so old completion cannot close the successor.",
                    ))
                if old_task_id in {proof.get("engine_id") for proof in target.get("proofs", [])}:
                    issues.append(Issue(
                        "ERROR",
                        "QV2-MIGRATION-REVIEW-TASK-ID-REUSED",
                        where,
                        f"review/reset successor reuses the QR0 task ID {old_task_id}.",
                    ))
                retired_quest = retired_by_id.get(str(old_id))
                if not retired_quest or retired_quest.get("kind") != "quest":
                    issues.append(Issue(
                        "ERROR",
                        "QV2-MIGRATION-RETIRED-QUEST-MISSING",
                        where,
                        f"review/reset QR0 quest ID {old_id} is missing from retired_ids.json.",
                    ))
                else:
                    for key, expected in (
                        ("old_alias", old.get("alias")),
                        ("successor_alias", new_alias),
                        ("migration_policy", policy),
                    ):
                        if retired_quest.get(key) != expected:
                            issues.append(Issue(
                                "ERROR",
                                "QV2-MIGRATION-RETIRED-QUEST-MISMATCH",
                                where,
                                f"Retired quest {old_id} has {key}={retired_quest.get(key)!r}, expected {expected!r}.",
                            ))
                retired_task = retired_by_id.get(old_task_id)
                if not retired_task or retired_task.get("kind") != "task" or retired_task.get("parent_old_engine_id") != old_id:
                    issues.append(Issue(
                        "ERROR",
                        "QV2-MIGRATION-RETIRED-TASK-MISSING",
                        where,
                        f"QR0 task ID {old_task_id} must be retired with its review/reset quest.",
                    ))

            mappings.append(mapping)
            mapping_locations.append(where)
            if isinstance(new_alias, str):
                target_rows[new_alias].append((where, mapping))

    for old_id, count in sorted(mapped_old_ids.items()):
        if count > 1:
            issues.append(Issue(
                "ERROR",
                "QV2-MIGRATION-SOURCE-DUPLICATE",
                "migrations",
                f"QR0 quest ID {old_id} is mapped {count} times; every old quest needs exactly one policy.",
            ))
    for old_id in sorted(set(old_by_id) - set(mapped_old_ids)):
        issues.append(Issue(
            "ERROR",
            "QV2-MIGRATION-SOURCE-UNMAPPED",
            "migrations",
            f"QR0 quest {old_by_id[old_id].get('alias')} ({old_id}) has no migration policy.",
        ))

    for new_alias, rows in sorted(target_rows.items()):
        if len(rows) > 1 and any(mapping.get("policy") == "carry" for _, mapping in rows):
            locations = [where for where, _mapping in rows]
            issues.append(Issue(
                "ERROR",
                "QV2-MIGRATION-MERGE-CARRY",
                ", ".join(locations),
                f"Merged successor {new_alias} cannot carry one predecessor; all predecessors must use review/reset.",
            ))

    reused_old_quest_ids = {quest.get("engine_id") for quest in quests.values()} & set(old_by_id)
    mapped_carry_ids = {item.get("new_engine_id") for item in mappings if item.get("policy") == "carry"}
    for reused in sorted(reused_old_quest_ids - mapped_carry_ids):
        issues.append(Issue("ERROR", "QV2-ID-REUSE-UNDECLARED", "migrations", f"Old quest engine ID {reused} is reused without a carry mapping."))
    for engine_id in sorted((current_proof_ids & stable_all_ids) - {
        "4" + str(item.get("old_engine_id"))[1:]
        for item in mappings
        if item.get("policy") == "carry" and isinstance(item.get("old_engine_id"), str)
    }):
        issues.append(Issue(
            "ERROR",
            "QV2-TASK-ID-REUSE-UNDECLARED",
            "migrations",
            f"Old task engine ID {engine_id} is reused outside a carry mapping.",
        ))

    return {
        "migration_documents": len(project.migrations),
        "mappings": mappings,
        "old_quest_alias_count": len(old_by_alias),
        "mapped_old_aliases": sorted(mapped_old_aliases),
        "unmapped_old_aliases": sorted(set(old_by_alias) - mapped_old_aliases),
        "policy_counts": dict(sorted(Counter(str(item.get("policy")) for item in mappings).items())),
        "retired_id_count": len(retired_by_id),
        "retired_quest_count": sum(item.get("kind") == "quest" for item in retired_by_id.values()),
        "retired_task_count": sum(item.get("kind") == "task" for item in retired_by_id.values()),
        "frozen_qr0_proof_contract_count": len(proof_contract_by_old_id),
    }


def _validate_content_mod_coverage(
    project: Project,
    quests: dict[str, dict[str, Any]],
    release: bool,
    issues: list[Issue],
) -> list[dict[str, Any]]:
    """Match every gameplay JAR contract to explicit Quest Source v2 references."""
    registry_path = project.root / "docs/registries/quest_content_coverage.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(Issue(
            "ERROR" if release else "WARN",
            "QV2-CONTENT-COVERAGE-REGISTRY",
            str(registry_path),
            f"Could not read the QR2 content coverage registry: {exc}.",
        ))
        return []

    resource_kinds = {
        "item", "item_tag", "block", "block_tag", "fluid", "fluid_tag",
        "entity", "biome", "structure", "dimension", "recipe",
    }
    by_modid: dict[str, set[str]] = defaultdict(set)
    declared_mod_refs: dict[str, set[str]] = defaultdict(set)
    for alias, quest in quests.items():
        for ref in quest.get("content_refs", []):
            kind = ref.get("kind")
            value = str(ref.get("id", "")).lstrip("#")
            modid = ""
            if kind == "mod":
                modid = value.split(":", 1)[0]
                if modid:
                    declared_mod_refs[modid].add(alias)
            elif kind in resource_kinds and ":" in value:
                modid = value.split(":", 1)[0]
            if modid:
                by_modid[modid].add(alias)

    known_modids = {
        str(modid)
        for jar in registry.get("jars", [])
        for modid in jar.get("modids", [])
        if str(modid)
    }
    for modid in sorted(set(declared_mod_refs) - known_modids):
        issues.append(Issue(
            "ERROR",
            "QV2-CONTENT-MOD-UNKNOWN",
            f"content_ref:mod:{modid}",
            f"Explicit mod reference is absent from the active QR2 registry; quests={sorted(declared_mod_refs[modid])}.",
        ))

    results: list[dict[str, Any]] = []
    for jar in registry.get("jars", []):
        if jar.get("category") != "CONTENT_GAMEPLAY":
            continue
        modids = sorted({str(item) for item in jar.get("modids", []) if str(item)})
        matched = sorted({alias for modid in modids for alias in by_modid.get(modid, set())})
        required_matches = sorted(alias for alias in matched if quests[alias].get("requirement") == "required")
        role = str(jar.get("role", ""))
        path = f"content:{jar.get('jar', jar.get('name', 'unknown'))}"
        if not matched:
            issues.append(Issue(
                "ERROR" if release else "WARN",
                "QV2-CONTENT-MOD-UNCOVERED",
                path,
                f"Gameplay mod IDs {modids} have no explicit quest content_ref.",
            ))
        if role in {"MANDATORY_BACKBONE", "MANDATORY_INTEGRATION"} and not required_matches:
            issues.append(Issue(
                "ERROR" if release else "WARN",
                "QV2-CONTENT-MOD-NOT-REQUIRED",
                path,
                f"{role} needs at least one required quest reference; matches={matched}.",
            ))
        results.append({
            "jar": jar.get("jar"),
            "name": jar.get("name"),
            "modids": modids,
            "category": jar.get("category"),
            "role": role,
            "home_chapter": jar.get("home_chapter"),
            "quest_refs": matched,
            "required_quest_refs": required_matches,
            "covered": bool(matched),
            "required_contract_satisfied": role not in {"MANDATORY_BACKBONE", "MANDATORY_INTEGRATION"} or bool(required_matches),
        })
    return results


def validate_project(project: Project, *, release: bool = False) -> tuple[list[Issue], dict[str, Any]]:
    issues: list[Issue] = []
    groups: dict[str, dict[str, Any]] = {}
    chapters: dict[str, dict[str, Any]] = {}
    quests: dict[str, dict[str, Any]] = {}
    proofs: dict[str, dict[str, Any]] = {}
    id_owner: dict[str, str] = {}
    alias_owner: dict[str, str] = {}
    dependencies: dict[str, list[str]] = {}
    dependency_modes: dict[str, str] = {}
    chapter_for_quest: dict[str, str] = {}
    order_owners: dict[int, list[str]] = defaultdict(list)
    layout_owners: dict[tuple[str, float, float], list[str]] = defaultdict(list)

    def register(alias: Any, engine_id: Any, kind: str, path: str) -> None:
        if not isinstance(alias, str) or not isinstance(engine_id, str):
            return
        if alias in alias_owner:
            issues.append(Issue("ERROR", "QV2-ALIAS-DUPLICATE", path, f"Alias {alias} already belongs to {alias_owner[alias]}."))
        else:
            alias_owner[alias] = path
        if engine_id in id_owner:
            issues.append(Issue("ERROR", "QV2-ID-DUPLICATE", path, f"Engine ID {engine_id} already belongs to {id_owner[engine_id]}."))
        else:
            id_owner[engine_id] = f"{kind}:{alias}"

    for document in project.chapters:
        chapter = document.get("chapter", {})
        chapter_alias = chapter.get("alias")
        path = project.chapter_files.get(str(chapter_alias), "unknown")
        if not isinstance(chapter_alias, str):
            continue
        if chapter_alias in chapters:
            issues.append(Issue("ERROR", "QV2-CHAPTER-DUPLICATE", path, f"Duplicate chapter alias {chapter_alias}."))
        chapters[chapter_alias] = chapter
        register(chapter_alias, chapter.get("engine_id"), "chapter", path)
        order_owners[chapter.get("order", 0)].append(chapter_alias)

        group = chapter.get("group", {})
        group_alias = group.get("alias")
        if isinstance(group_alias, str):
            previous = groups.get(group_alias)
            if previous is not None and previous != group:
                issues.append(Issue("ERROR", "QV2-GROUP-DRIFT", path, f"Group {group_alias} is declared differently across chapters."))
            elif previous is None:
                groups[group_alias] = group
                register(group_alias, group.get("engine_id"), "group", path)

        for qindex, quest in enumerate(document.get("quests", [])):
            alias = quest.get("alias")
            qpath = f"{path}:quests[{qindex}]"
            if not isinstance(alias, str):
                continue
            if alias in quests:
                issues.append(Issue("ERROR", "QV2-QUEST-DUPLICATE", qpath, f"Duplicate quest alias {alias}."))
            quests[alias] = quest
            chapter_for_quest[alias] = chapter_alias
            register(alias, quest.get("engine_id"), "quest", qpath)
            if quest.get("epoch") != chapter.get("epoch"):
                issues.append(Issue("ERROR", "QV2-EPOCH-CHAPTER", qpath, f"Quest epoch {quest.get('epoch')} differs from chapter epoch {chapter.get('epoch')}."))
            layout = quest.get("layout", {})
            if isinstance(layout.get("x"), (int, float)) and isinstance(layout.get("y"), (int, float)):
                layout_owners[(chapter_alias, float(layout["x"]), float(layout["y"]))].append(alias)
            dependency = quest.get("dependency", {})
            edges = dependency.get("edges", []) if isinstance(dependency, dict) else []
            dependencies[alias] = [edge.get("quest") for edge in edges if isinstance(edge, dict) and isinstance(edge.get("quest"), str)]
            dependency_modes[alias] = str(dependency.get("mode", "ALL_OF"))

            for pindex, proof in enumerate(quest.get("proofs", [])):
                proof_alias = proof.get("alias")
                ppath = f"{qpath}:proofs[{pindex}]"
                if isinstance(proof_alias, str):
                    if proof_alias in proofs:
                        issues.append(Issue("ERROR", "QV2-PROOF-DUPLICATE", ppath, f"Duplicate proof alias {proof_alias}."))
                    proofs[proof_alias] = proof
                    register(proof_alias, proof.get("engine_id"), "proof", ppath)

    for order, owners in order_owners.items():
        if len(owners) > 1:
            issues.append(Issue("WARN", "QV2-CHAPTER-ORDER", "chapters", f"Chapter order {order} is shared by {owners}."))
    for (_, x, y), owners in layout_owners.items():
        if len(owners) > 1:
            issues.append(Issue("WARN", "QV2-LAYOUT-OVERLAP", chapter_for_quest.get(owners[0], "chapter"), f"Quests overlap at ({x}, {y}): {owners}."))

    # Dependency integrity, optionality, edge evidence and cross-epoch gates.
    for alias, deps in dependencies.items():
        quest = quests[alias]
        path = f"quest:{alias}"
        if len(deps) != len(set(deps)):
            issues.append(Issue("ERROR", "QV2-EDGE-DUPLICATE", path, "The same dependency appears more than once."))
        if dependency_modes[alias] == "ANY_OF" and len(deps) < 2:
            issues.append(Issue("ERROR", "QV2-ANY-OF-SMALL", path, "ANY_OF needs at least two dependency edges."))
        for dep in deps:
            if dep == alias:
                issues.append(Issue("ERROR", "QV2-SELF-EDGE", path, "Quest depends on itself."))
                continue
            if dep not in quests:
                issues.append(Issue("ERROR", "QV2-EDGE-MISSING", path, f"Dependency {dep} does not exist."))
                continue
            if quest.get("requirement") == "required" and dependency_modes[alias] == "ALL_OF" and quests[dep].get("requirement") == "optional":
                issues.append(Issue("ERROR", "QV2-OPTIONAL-BECOMES-REQUIRED", path, f"Optional quest {dep} is an ALL_OF gate for a required quest."))
            source_epoch, target_epoch = quests[dep].get("epoch"), quest.get("epoch")
            if source_epoch in EPOCH_INDEX and target_epoch in EPOCH_INDEX:
                source_index, target_index = EPOCH_INDEX[source_epoch], EPOCH_INDEX[target_epoch]
                if source_index > target_index:
                    issues.append(Issue("ERROR", "QV2-EDGE-BACKWARDS", path, f"Future epoch {source_epoch} gates {target_epoch}."))
                elif source_index < target_index and not (
                    source_index + 1 == target_index and quests[dep].get("role") == "commissioning"
                ):
                    issues.append(Issue("ERROR", "QV2-CROSS-EPOCH-GATE", path, f"Only the immediately previous commissioning may cross into {target_epoch}; got {dep}."))
            elif target_epoch == "P0" and source_epoch not in {"P0", "ONBOARDING"}:
                issues.append(Issue("ERROR", "QV2-P0-GATE", path, f"P0 may only be gated by onboarding or P0; got {source_epoch}."))

    # DAG and reachability.
    indegree = {alias: 0 for alias in quests}
    children: dict[str, list[str]] = defaultdict(list)
    for alias, deps in dependencies.items():
        for dep in deps:
            if dep in quests:
                indegree[alias] += 1
                children[dep].append(alias)
    queue = deque(sorted(alias for alias, degree in indegree.items() if degree == 0))
    topological: list[str] = []
    while queue:
        alias = queue.popleft()
        topological.append(alias)
        for child in sorted(children.get(alias, [])):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(topological) != len(quests):
        cyclic = sorted(alias for alias, degree in indegree.items() if degree > 0)
        issues.append(Issue("ERROR", "QV2-CYCLE", "graph", f"Dependency graph is cyclic: {cyclic}."))
    roots = sorted(alias for alias, deps in dependencies.items() if not deps)
    reachable: set[str] = set()
    walk = deque(roots)
    while walk:
        alias = walk.popleft()
        if alias in reachable:
            continue
        reachable.add(alias)
        walk.extend(children.get(alias, []))
    for alias in sorted(set(quests) - reachable):
        issues.append(Issue("ERROR", "QV2-UNREACHABLE", f"quest:{alias}", "Quest is not reachable from a graph root."))

    # A structural ancestor is not necessarily mandatory: an ANY_OF node can
    # bypass every dependency that is not common to all alternatives.  Build a
    # second closure with the runtime completion semantics so commissioning
    # cannot appear to cover a required branch merely because it is somewhere
    # in the transitive graph.
    mandatory_dependencies: dict[str, set[str]] = {}
    if len(topological) == len(quests):
        for alias in topological:
            paths = [
                {dep, *mandatory_dependencies.get(dep, set())}
                for dep in dependencies.get(alias, [])
                if dep in quests
            ]
            if not paths:
                mandatory_dependencies[alias] = set()
            elif dependency_modes.get(alias) == "ANY_OF":
                mandatory_dependencies[alias] = set.intersection(*paths)
            else:
                mandatory_dependencies[alias] = set().union(*paths)

    # Early-game causal contracts are deliberately explicit.  Generic graph
    # validity is not enough here: the legacy runtime once asked for four
    # chests before the player had reached the crafting table and accepted
    # only vanilla raw iron even though several early GTCEu minerals produce
    # the same metal.  Keep those player-visible regressions impossible even
    # when aliases, layouts, or surrounding tutorial quests are edited later.
    p0_crafting = "if.quest.v2.p0.crafting_table"
    p0_planks = "if.quest.v2.p0.planks"
    p0_camp = "if.quest.v2.p0.camp_kit"
    p0_iron_source = "if.quest.v2.p0.iron_source"
    p0_iron_product = "if.quest.v2.p0.iron_product"

    def item_selectors(alias: str) -> list[tuple[str, str]]:
        selectors: list[tuple[str, str]] = []
        for proof in quests.get(alias, {}).get("proofs", []):
            if proof.get("type") != "item":
                continue
            if isinstance(proof.get("item"), dict):
                selectors.append(("item", str(proof["item"].get("id", ""))))
            if isinstance(proof.get("item_tag"), dict):
                selectors.append(("item_tag", str(proof["item_tag"].get("id", ""))))
        return selectors

    if p0_crafting in quests:
        if p0_planks not in dependencies.get(p0_crafting, []):
            issues.append(Issue(
                "ERROR",
                "QV2-P0-WORKBENCH-ORDER",
                p0_crafting,
                "The crafting-table quest must directly follow the accepted-planks quest.",
            ))
        chest_ancestors = sorted(
            ancestor
            for ancestor in mandatory_dependencies.get(p0_crafting, set())
            if ("item", "minecraft:chest") in item_selectors(ancestor)
        )
        if chest_ancestors:
            issues.append(Issue(
                "ERROR",
                "QV2-P0-CHEST-BEFORE-WORKBENCH",
                p0_crafting,
                f"Chest acquisition must not gate the first crafting table: {chest_ancestors}.",
            ))

    if p0_camp in quests and p0_crafting not in mandatory_dependencies.get(p0_camp, set()):
        issues.append(Issue(
            "ERROR",
            "QV2-P0-CAMP-BEFORE-WORKBENCH",
            p0_camp,
            "The camp kit must come after the crafting table has been obtained and opened.",
        ))

    for alias in sorted(quests):
        if ("item", "minecraft:chest") not in item_selectors(alias):
            continue
        if alias != p0_crafting and p0_crafting in quests and p0_crafting not in mandatory_dependencies.get(alias, set()):
            issues.append(Issue(
                "ERROR",
                "QV2-CHEST-REQUIRES-WORKBENCH",
                alias,
                "A chest-acquisition quest must have the first crafting table as a mandatory ancestor.",
            ))

    expected_p0_selectors = {
        p0_iron_source: ("item_tag", "industrial_frontier:quest_sources/early_iron"),
        p0_iron_product: ("item_tag", "industrial_frontier:materials/iron_ingots"),
    }
    for alias, expected_selector in expected_p0_selectors.items():
        if alias not in quests:
            continue
        selectors = item_selectors(alias)
        if selectors != [expected_selector]:
            issues.append(Issue(
                "ERROR",
                "QV2-P0-IRON-ACCEPTANCE",
                alias,
                f"Expected the capability selector {expected_selector}, got {selectors}; exact raw iron is forbidden.",
            ))

    expected_proof_selectors = {
        "if.task.v2.p0.iron_consumer.pickaxe": (
            "item_tag",
            "industrial_frontier:quest_components/iron_pickaxes",
        ),
        "if.task.v2.p5.bulk_processing.item": (
            "item_tag",
            "industrial_frontier:quest_sources/purified_iron_bearing_ores",
        ),
        "if.task.v2.p5.contracts.cargo": (
            "item_tag",
            "industrial_frontier:quest_sources/purified_iron_bearing_ores",
        ),
        "if.task.v2.p5.ae2_patterns.provider": (
            "item_tag",
            "ae2:pattern_provider",
        ),
        "if.task.v2.p5.last_mile.item": (
            "item_tag",
            "create:toolboxes",
        ),
        "if.task.v2.p6.materials.lead": (
            "item_tag",
            "industrial_frontier:materials/lead_plates",
        ),
        "if.task.v2.p6.enrichment.u235": (
            "item_tag",
            "nuclearcraft:isotopes/uranium/235",
        ),
        "if.task.v2.p6.enrichment.u238": (
            "item_tag",
            "nuclearcraft:isotopes/uranium/238",
        ),
        "if.task.v2.p6.fuel_form.item": (
            "item_tag",
            "nuclearcraft:reactor_fuel/uranium/leu-235",
        ),
        "if.task.v2.p6.spent_fuel.item": (
            "item_tag",
            "nuclearcraft:depleted_reactor_fuel/uranium/leu-235",
        ),
        "if.task.v2.p6.reprocessing.u238": (
            "item_tag",
            "nuclearcraft:isotopes/uranium/238",
        ),
        "if.task.v2.p6.reprocessing.pu239": (
            "item_tag",
            "nuclearcraft:isotopes/plutonium/239",
        ),
        "if.task.v2.p8.fusion_material.copernicium": (
            "item_tag",
            "nuclearcraft:isotopes/copernicium/291",
        ),
        "if.task.v2.p8.commissioning.copernicium": (
            "item_tag",
            "nuclearcraft:isotopes/copernicium/291",
        ),
        "if.task.v2.control.hardwired_interlocks.bus": (
            "item_tag",
            "projectred_transmission:bundled_wire",
        ),
        "if.task.v2.oil.respirator.item": (
            "item_tag",
            "industrial_frontier:safety/respirators",
        ),
    }
    for proof_alias, expected_selector in expected_proof_selectors.items():
        proof = proofs.get(proof_alias)
        if proof is None:
            continue
        if isinstance(proof.get("item"), dict):
            actual_selector = ("item", str(proof["item"].get("id", "")))
        elif isinstance(proof.get("item_tag"), dict):
            actual_selector = ("item_tag", str(proof["item_tag"].get("id", "")))
        else:
            actual_selector = (str(proof.get("type", "")), "")
        if actual_selector != expected_selector:
            issues.append(Issue(
                "ERROR",
                "QV2-CAPABILITY-SELECTOR-REGRESSION",
                proof_alias,
                f"Expected capability selector {expected_selector}, got {actual_selector}.",
            ))

    # These optional PneumaticCraft/IC2 bridge blocks have language and
    # Patchouli assets in the PNC archive but are not registered with the
    # installed integration set.  FTB Quests therefore cannot deserialize them
    # as item stacks.  Keep them out of icons, proof selectors, and content refs.
    known_unregistered_item_ids = {
        "ad_astra:tier_1_rocket",
        "pneumaticcraft:electric_compressor",
        "pneumaticcraft:pneumatic_generator",
    }

    def registry_ids(value: object) -> set[str]:
        found: set[str] = set()
        if isinstance(value, dict):
            for nested in value.values():
                found.update(registry_ids(nested))
        elif isinstance(value, list):
            for nested in value:
                found.update(registry_ids(nested))
        elif isinstance(value, str) and value in known_unregistered_item_ids:
            found.add(value)
        return found

    for alias, quest in quests.items():
        invalid_ids = sorted(registry_ids(quest))
        if invalid_ids:
            issues.append(Issue(
                "ERROR",
                "QV2-UNREGISTERED-ITEM-ID",
                alias,
                f"Quest source references item IDs not registered by the installed integration set: {invalid_ids}.",
            ))

    # Every pack-owned tag used by an item task must exist as real datapack
    # content.  A friendly 'one of these materials' sentence is meaningless if
    # the emitted FTB filter points at a missing or empty tag.
    for proof_alias, proof in proofs.items():
        if proof.get("type") == "fluid" and isinstance(proof.get("fluid"), dict):
            objective = str(proof.get("text_ru", {}).get("objective", ""))
            stated_amounts = {
                int(value.replace(" ", "").replace("\u00a0", "").replace("\u202f", ""))
                for value in re.findall(r"([0-9][0-9 \u00a0\u202f]*)\s*мБ\b", objective, re.IGNORECASE)
            }
            actual_amount = proof["fluid"].get("amount")
            if stated_amounts and actual_amount not in stated_amounts:
                issues.append(Issue(
                    "ERROR",
                    "QV2-PROOF-FLUID-AMOUNT",
                    proof_alias,
                    f"Russian objective states {sorted(stated_amounts)} mB, but executable selector requires {actual_amount} mB.",
                ))
        payload = proof.get("item_tag")
        if proof.get("type") != "item" or not isinstance(payload, dict):
            continue
        tag_id = str(payload.get("id", ""))
        if ":" not in tag_id:
            continue
        namespace, name = tag_id.split(":", 1)
        if namespace not in {"industrial_frontier", "forge"}:
            continue
        tag_path = (
            project.root
            / "config"
            / "paxi"
            / "datapacks"
            / "IndustrialFrontier-Data"
            / "data"
            / namespace
            / "tags"
            / "items"
            / f"{name}.json"
        )
        if not tag_path.is_file():
            issues.append(Issue(
                "ERROR",
                "QV2-ITEM-TAG-MISSING",
                proof_alias,
                f"Pack-owned item tag does not exist: {tag_path.relative_to(project.root).as_posix()}.",
            ))
            continue
        try:
            tag_document = json.loads(tag_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(Issue("ERROR", "QV2-ITEM-TAG-INVALID", proof_alias, f"Cannot read item tag: {exc}."))
            continue
        if not isinstance(tag_document, dict) or not isinstance(tag_document.get("values"), list) or not tag_document["values"]:
            issues.append(Issue(
                "ERROR",
                "QV2-ITEM-TAG-EMPTY",
                proof_alias,
                f"Pack-owned item tag {tag_id} must contain at least one accepted value.",
            ))

    early_iron_exact_ids = {
        "minecraft:raw_iron",
        "gtceu:raw_yellow_limonite",
        "gtceu:raw_magnetite",
        "gtceu:raw_basaltic_mineral_sand",
        "gtceu:raw_granitic_mineral_sand",
        "gtceu:raw_pyrite",
        "gtceu:raw_goethite",
        "gtceu:raw_hematite",
    }
    for alias, quest in quests.items():
        if quest.get("epoch") != "P0":
            continue
        forbidden = sorted(
            selector
            for kind, selector in item_selectors(alias)
            if kind == "item" and selector in early_iron_exact_ids
        )
        if forbidden:
            issues.append(Issue(
                "ERROR",
                "QV2-P0-EXACT-IRON-FORBIDDEN",
                alias,
                f"P0 must accept the proven early-iron source set, not exact mineral IDs: {forbidden}.",
            ))

    exact_choice_claim = re.compile(
        r"(?:из\s+списка\s+задачи|любой\s+подходящ(?:ий|ая|ее)\s+"
        r"(?:минерал|руда|слиток|пластина|доска|бревно|брёвно))",
        re.IGNORECASE,
    )
    for alias, quest in quests.items():
        for proof in quest.get("proofs", []):
            if proof.get("type") != "item" or not isinstance(proof.get("item"), dict):
                continue
            proof_copy = " ".join(str(value) for value in proof.get("text_ru", {}).values())
            if exact_choice_claim.search(proof_copy):
                issues.append(Issue(
                    "ERROR",
                    "QV2-EXACT-ITEM-CHOICE-LIE",
                    str(proof.get("alias", alias)),
                    "The Russian task promises a choice among equivalent materials, but the proof accepts one exact item ID.",
                ))

    # A campaign may contain its own required sequence while remaining wholly
    # optional to the technological backbone.  Keep that distinction explicit:
    # no quest from an optional campaign may become a mandatory ancestor of an
    # epoch commissioning.  City-labelled nodes outside that chapter are also
    # rejected on the backbone so a future rename cannot silently restore the
    # old city gate.
    optional_campaign_chapters = {
        alias
        for alias, chapter in chapters.items()
        if "optional_campaign" in chapter.get("tags", [])
    }
    optional_campaign_quests = {
        alias
        for alias, chapter_alias in chapter_for_quest.items()
        if chapter_alias in optional_campaign_chapters
    }

    def has_city_gate_marker(alias: str) -> bool:
        tags = {str(tag).lower() for tag in quests[alias].get("tags", [])}
        if bool(tags & {"city", "settlement", "minecolonies"}) or any(
            tag.startswith("city_") for tag in tags
        ):
            return True
        quest = quests[alias]
        structural_values = [
            str(quest.get("icon", "")),
            str(quest.get("grind", {}).get("budget_ref", "")),
        ]
        for ref in quest.get("content_refs", []):
            structural_values.append(str(ref.get("id", "")))
            structural_values.extend(str(value) for value in ref.get("evidence", []))
        return any(
            re.search(r"(?:city_demand|municipal|minecolonies|(?:^|[/_.-])city(?:[/_.-]|$))", value, re.IGNORECASE)
            for value in structural_values
        )

    # Commissioning is the sole authoritative join and epoch boundary.
    memo: dict[str, set[str]] = {}
    commissioning_by_epoch: dict[str, str] = {}
    reported_optional_campaign_gates: set[str] = set()
    reported_city_gates: set[str] = set()
    for epoch in EPOCHS:
        epoch_quests = [alias for alias, quest in quests.items() if quest.get("epoch") == epoch]
        if not epoch_quests:
            if release:
                issues.append(Issue("ERROR", "QV2-EPOCH-MISSING", epoch, "Release requires a complete P0-P9 quest graph."))
            continue
        commissioning = [alias for alias in epoch_quests if quests[alias].get("role") == "commissioning"]
        if len(commissioning) != 1:
            issues.append(Issue("ERROR", "QV2-COMMISSIONING-COUNT", epoch, f"Expected exactly one commissioning quest, found {commissioning}."))
            continue
        commission_alias = commissioning[0]
        commissioning_by_epoch[epoch] = commission_alias
        commission = quests[commission_alias]
        expected_tag = f"if_commissioning_{epoch.lower()}"
        owners = [alias for alias, quest in quests.items() if expected_tag in quest.get("tags", [])]
        if owners != [commission_alias]:
            issues.append(Issue("ERROR", "QV2-COMMISSIONING-TAG", epoch, f"Tag {expected_tag} must exist only on {commission_alias}; owners={owners}."))
        if dependency_modes.get(commission_alias) != "ALL_OF":
            issues.append(Issue("ERROR", "QV2-COMMISSIONING-MODE", commission_alias, "Commissioning must join branches with ALL_OF."))
        config = commission.get("commissioning", {})
        expected_next = f"P{EPOCH_INDEX[epoch] + 1}" if epoch != "P9" else "COMPLETE"
        if config.get("epoch") != epoch or config.get("advances_to") != expected_next:
            issues.append(Issue("ERROR", "QV2-COMMISSIONING-TRANSITION", commission_alias, f"Expected {epoch} -> {expected_next}."))
        ancestors = _ancestors(commission_alias, dependencies, memo) if len(topological) == len(quests) else set()
        mandatory = mandatory_dependencies.get(commission_alias, set())
        optional_campaign_gates = sorted(
            (mandatory & optional_campaign_quests) - reported_optional_campaign_gates
        )
        if optional_campaign_gates:
            issues.append(Issue(
                "ERROR",
                "QV2-OPTIONAL-CAMPAIGN-GATE",
                commission_alias,
                f"Optional-campaign quests must not gate epoch commissioning: {optional_campaign_gates}.",
            ))
            reported_optional_campaign_gates.update(optional_campaign_gates)
        city_gates = sorted(
            alias
            for alias in mandatory - reported_city_gates
            if has_city_gate_marker(alias)
        )
        if city_gates:
            issues.append(Issue(
                "ERROR",
                "QV2-CITY-GATES-MAINLINE",
                commission_alias,
                f"City-labelled quests or structural city contracts are mandatory ancestors of the technical backbone: {city_gates}.",
            ))
            reported_city_gates.update(city_gates)
        required = {alias for alias in epoch_quests if quests[alias].get("requirement") == "required" and alias != commission_alias}
        for missing in sorted(required - mandatory):
            detail = "not an ancestor" if missing not in ancestors else "avoidable through an ANY_OF path"
            issues.append(Issue("ERROR", "QV2-COMMISSIONING-BYPASS", commission_alias, f"Required quest {missing} is {detail} before commissioning."))
        for branch_end in config.get("required_branch_ends", []):
            if branch_end not in quests:
                issues.append(Issue("ERROR", "QV2-COMMISSIONING-BRANCH", commission_alias, f"Unknown branch end {branch_end}."))
            elif branch_end not in ancestors:
                issues.append(Issue("ERROR", "QV2-COMMISSIONING-BRANCH", commission_alias, f"Branch end {branch_end} does not lead to commissioning."))

    for epoch, commission_alias in commissioning_by_epoch.items():
        if epoch == "P9":
            continue
        next_epoch = f"P{EPOCH_INDEX[epoch] + 1}"
        if next_epoch not in commissioning_by_epoch and not any(q.get("epoch") == next_epoch for q in quests.values()):
            continue  # A deliberately partial QR source tree.
        entries = [
            alias for alias, quest in quests.items()
            if quest.get("epoch") == next_epoch
            and not any(
                quests.get(dep, {}).get("epoch") == next_epoch
                for dep in _ancestors(alias, dependencies, memo)
            )
        ]
        for entry in entries:
            if commission_alias not in dependencies.get(entry, []):
                issues.append(Issue("ERROR", "QV2-NEXT-EPOCH-ENTRY", entry, f"Entry to {next_epoch} must directly depend on {commission_alias}."))

    # Russian-first editorial checks and proof/verb truth.
    title_counter: Counter[str] = Counter()
    sentence_starts_by_chapter: dict[str, list[tuple[str, str]]] = defaultdict(list)
    blocked: list[dict[str, Any]] = []
    checkmark_allowed_roles = {"onboarding", "knowledge", "recovery"}
    for alias, quest in quests.items():
        path = f"quest:{alias}"
        role = quest.get("role")
        requirement = quest.get("requirement")
        text = quest.get("text_ru", {})
        review = quest.get("editorial_review", {})
        state = review.get("state")
        title = str(text.get("title_ru", "")).strip()
        title_counter[title.casefold()] += 1
        lead = str(text.get("lead_ru", "")).strip()
        if lead:
            start = " ".join(re.findall(r"[А-Яа-яЁёA-Za-z0-9-]+", lead)[:3]).casefold()
            sentence_starts_by_chapter[chapter_for_quest.get(alias, "")].append((alias, start))

        ru_fields = _flatten_ru_text(quest)
        for field, value in ru_fields:
            normalized = value.strip()
            if PLACEHOLDER_RE.search(normalized):
                issues.append(Issue("ERROR", "QV2-RU-PLACEHOLDER", f"{path}.{field}", "Placeholder or machine-translation marker is forbidden."))
            if not CYRILLIC_RE.search(normalized):
                issues.append(Issue("ERROR", "QV2-RU-NOT-RUSSIAN", f"{path}.{field}", "Russian-first field contains no Cyrillic text."))
            if normalized != value:
                issues.append(Issue("ERROR", "QV2-RU-WHITESPACE", f"{path}.{field}", "Leading/trailing whitespace is forbidden."))
            if re.search(r"\.{3,}|!{2,}|\?{2,}", normalized):
                issues.append(Issue("WARN", "QV2-RU-PUNCTUATION", f"{path}.{field}", "Avoid expressive punctuation in instructional text."))
            words = re.findall(r"[А-Яа-яЁёA-Za-z0-9-]+", normalized)
            if len(words) >= 8 and sum(word.isupper() and len(word) > 2 for word in words) / len(words) > 0.25:
                issues.append(Issue("WARN", "QV2-RU-CAPS", f"{path}.{field}", "Too much uppercase text for the calm mentor voice."))
            cyrillic_words = sum(bool(re.search(r"[А-Яа-яЁё]", word)) for word in words)
            latin_words = sum(bool(re.search(r"[A-Za-z]", word)) and not re.search(r"[А-Яа-яЁё]", word) for word in words)
            if len(words) >= 8 and latin_words > cyrillic_words:
                issues.append(Issue(
                    "ERROR" if state == "RU_READY" else "WARN",
                    "QV2-RU-LATIN-DOMINANT",
                    f"{path}.{field}",
                    "Russian-primary copy contains more Latin-script words than Cyrillic words.",
                ))
            for sentence in re.split(r"(?<=[.!?])\s+", normalized):
                count = len(re.findall(r"[А-Яа-яЁёA-Za-z0-9-]+", sentence))
                if count > 40:
                    issues.append(Issue("WARN", "QV2-RU-LONG-SENTENCE", f"{path}.{field}", f"Sentence has {count} words; target is at most 25."))
            if re.search(r"\b(?:в рамках|данн(?:ый|ая|ое)|осуществ(?:ить|ляется)|посредством|с целью выполнения|игрок должен)\b", normalized, re.I):
                issues.append(Issue("WARN", "QV2-RU-BUREAUCRATIC", f"{path}.{field}", "Possible bureaucratic or player-detached wording."))
            if INTERNAL_JARGON_RE.search(normalized):
                issues.append(Issue(
                    "ERROR" if state == "RU_READY" else "WARN",
                    "QV2-RU-INTERNAL-JARGON",
                    f"{path}.{field}",
                    "Player-facing Russian text contains implementation language; explain the action in world terms instead.",
                ))
            if RAW_RESOURCE_IN_PLAYER_RE.search(normalized):
                issues.append(Issue(
                    "ERROR" if state == "RU_READY" else "WARN",
                    "QV2-RU-RAW-RESOURCE-ID",
                    f"{path}.{field}",
                    "Player-facing Russian text contains a raw registry ID; use the natural Russian name and keep the ID only in proof/content_refs.",
                ))
            if RAW_SNAKE_IN_PLAYER_RE.search(normalized):
                issues.append(Issue(
                    "ERROR" if state == "RU_READY" else "WARN",
                    "QV2-RU-RAW-SNAKE-ID",
                    f"{path}.{field}",
                    "Player-facing Russian text contains a raw snake_case identifier; replace it with a natural Russian name.",
                ))
            if MOJIBAKE_RE.search(normalized):
                issues.append(Issue(
                    "ERROR",
                    "QV2-RU-MOJIBAKE",
                    f"{path}.{field}",
                    "Player-facing Russian text contains likely broken UTF-8/Windows-1251 decoding.",
                ))

        authorship = quest.get("authorship", {})
        if authorship.get("primary_language") != "ru" or authorship.get("origin") != "human_authored" or authorship.get("machine_translation") is not False:
            issues.append(Issue("ERROR", "QV2-RU-AUTHORSHIP", path, "Quest must declare Russian human-authored primary text and no machine translation."))
        marks = review.get("marks", [])
        if state not in REVIEW_STATES:
            issues.append(Issue("ERROR", "QV2-RU-STATE", path, f"Unknown editorial state {state!r}."))
        else:
            required_mark_count = 4 if state in {"RU_FLOW_REVIEWED", "RU_READY"} else REVIEW_MARKS.index(state) + 1
            missing_marks = REVIEW_MARKS[:required_mark_count]
            missing_marks = [mark for mark in missing_marks if mark not in marks]
            if missing_marks:
                issues.append(Issue("ERROR", "QV2-RU-MARKS", path, f"State {state} lacks prerequisite marks {missing_marks}."))
            if state == "RU_READY" and set(marks) != set(REVIEW_MARKS):
                issues.append(Issue("ERROR", "QV2-RU-READY", path, "RU_READY requires all four editorial marks and no invented fifth mark."))
            if state != "RU_READY":
                level = "ERROR" if release else "WARN"
                issues.append(Issue(level, "QV2-RU-NOT-READY", path, f"Editorial state is honestly {state}; staging compilation requires RU_READY."))

        if requirement == "optional" and not str(text.get("optional_note_ru", "")).strip():
            issues.append(Issue("ERROR", "QV2-OPTIONAL-NOTE", path, "Optional quest needs optional_note_ru."))
        if role not in {"onboarding", "knowledge", "recovery"}:
            if not text.get("steps_ru"):
                issues.append(Issue("ERROR" if release else "WARN", "QV2-RU-STEPS", path, "A content quest needs concrete steps_ru."))
            if not text.get("diagnostics_ru"):
                issues.append(Issue("ERROR" if release else "WARN", "QV2-RU-DIAGNOSTICS", path, "A content quest needs likely-failure diagnostics_ru."))

        proof_types = {str(proof.get("type")) for proof in quest.get("proofs", [])}
        if requirement == "required" and role not in checkmark_allowed_roles and proof_types == {"checkmark"}:
            issues.append(Issue("ERROR", "QV2-CHECKMARK-LIE", path, f"Role {role} cannot be proven only by self-certification."))
        for proof in quest.get("proofs", []):
            ptype = proof.get("type")
            if ptype not in VERIFIED_ADAPTERS:
                issues.append(Issue("ERROR", "QV2-ADAPTER-UNKNOWN", path, f"No locally proven adapter for {ptype!r}."))
            if proof.get("status") == "blocked":
                blocked.append({
                    "quest": alias,
                    "proof": proof.get("alias"),
                    "type": ptype,
                    "blocker": proof.get("blocker"),
                })
                issues.append(Issue("ERROR" if release else "WARN", "QV2-PROOF-BLOCKED", path, f"Proof {proof.get('alias')} is explicitly blocked; no SNBT will be invented."))
            if ptype == "use":
                payload = proof.get("use", {})
                if payload.get("check_item") is True and not payload.get("item"):
                    issues.append(Issue("ERROR", "QV2-USE-ITEM", path, "Use proof with check_item=true needs an exact item payload."))
            if ptype == "place":
                payload = proof.get("place", {})
                if payload.get("require_replace") and not payload.get("replaced_block"):
                    issues.append(Issue("ERROR", "QV2-PLACE-REPLACE", path, "Place proof with require_replace=true needs replaced_block."))

        task_text = str(text.get("task_text_ru", ""))
        verb_rules = [
            (r"\b(?:поставьте|разместите|возведите|установите)\b", {"place", "structure", "observation", "use"}, "placement/structure"),
            (r"\b(?:запустите|включите|запустите в работу)\b", {"use", "observation", "stage", "energy", "fluid"}, "operation"),
            (r"\b(?:посетите|доберитесь|войдите|найдите биом)\b", {"dimension", "location", "biome", "structure"}, "visit"),
            (r"\b(?:убейте|уничтожьте)\b", {"kill"}, "kill"),
            (r"\b(?:получите|добудьте|изготовьте|переплавьте)\b", {"item", "fluid"}, "acquisition/output"),
        ]
        for pattern, accepted, label in verb_rules:
            if re.search(pattern, task_text, re.I) and proof_types.isdisjoint(accepted):
                issues.append(Issue("ERROR" if state == "RU_READY" else "WARN", "QV2-TEXT-PROOF-MISMATCH", path, f"task_text_ru promises {label}, but proof types are {sorted(proof_types)}."))

        refs = quest.get("content_refs", [])
        if not refs and role not in {"onboarding", "knowledge", "recovery"}:
            issues.append(Issue("ERROR", "QV2-CONTENT-REFS", path, "A content quest needs at least one explicit content_ref."))
        for ref in refs:
            kind, value = ref.get("kind"), str(ref.get("id", ""))
            if kind == "mod":
                bare_mod = re.fullmatch(r"[a-z0-9_.-]+", value)
                qualified_mod = re.fullmatch(r"([a-z0-9_.-]+):\1", value)
                if not bare_mod and not qualified_mod:
                    issues.append(Issue("ERROR", "QV2-CONTENT-ID", path, f"content_ref mod:{value!r} must be a bare mod ID or modid:modid."))
            if kind in {"item", "item_tag", "block", "block_tag", "fluid", "fluid_tag", "entity", "biome", "structure", "dimension", "recipe"} and not RESOURCE_RE.match(value):
                issues.append(Issue("ERROR", "QV2-CONTENT-ID", path, f"content_ref {kind}:{value!r} must be a resource location."))
            for evidence in ref.get("evidence", []):
                if isinstance(evidence, str) and (evidence.startswith("http://") or evidence.startswith("https://") or "!" in evidence):
                    continue
                if isinstance(evidence, str) and ("/" in evidence or "\\" in evidence):
                    evidence_path = evidence.split("#", 1)[0]
                    candidate = project.root / pathlib.Path(evidence_path.replace("\\", "/"))
                    if not candidate.exists():
                        issues.append(Issue("WARN", "QV2-EVIDENCE-MISSING", path, f"Evidence path does not exist: {evidence}."))

        grind = quest.get("grind", {})
        if grind.get("class") == "REWORK" and state == "RU_READY":
            issues.append(Issue("ERROR", "QV2-GRIND-REWORK-READY", path, "A REWORK grind contract cannot be RU_READY."))
        expected_runs = grind.get("expected_runs")
        grind_copy = " ".join([
            str(grind.get("rationale_ru", "")),
            *(value for _, value in _flatten_ru_text(quest)),
        ])
        probabilistic_gate = bool(re.search(
            r"вероятност|шанс(?:ом|а|е)?\s+(?:в\s+)?\d|\d+\s*(?:%|процент)",
            grind_copy,
            re.IGNORECASE,
        ))
        if (
            requirement == "required"
            and isinstance(expected_runs, int)
            and expected_runs > 8
            and probabilistic_gate
        ):
            issues.append(Issue(
                "ERROR",
                "QV2-GRIND-RNG-GATE",
                path,
                f"Required probabilistic result expects {expected_runs} runs without a proven deterministic alternative or pity path.",
            ))
        elif isinstance(expected_runs, int) and expected_runs > 8 and not grind.get("automation_before_bulk"):
            issues.append(Issue(
                "ERROR",
                "QV2-GRIND-RUNS-BEFORE-AUTOMATION",
                path,
                f"Expected run count {expected_runs} exceeds the hard limit before automation.",
            ))
        item_counts: list[int] = []
        for proof in quest.get("proofs", []):
            if proof.get("type") == "item":
                payload = proof.get("item") or proof.get("item_tag") or {}
                if isinstance(payload.get("count", 1), int):
                    item_counts.append(payload.get("count", 1))
        if item_counts and max(item_counts) > 16 and not grind.get("automation_before_bulk"):
            issues.append(Issue("ERROR", "QV2-GRIND-BULK-BEFORE-AUTOMATION", path, f"Item proof count {max(item_counts)} is bulk, but automation_before_bulk is false."))
        if grind.get("class") == "TEACHING":
            training_batch = grind.get("training_batch")
            if not isinstance(training_batch, int) or training_batch < 1 or training_batch > 8:
                issues.append(Issue("ERROR", "QV2-GRIND-TEACHING-BATCH", path, "Teaching batches must stay between 1 and 8."))
            elif training_batch > 3 and not str(grind.get("rationale_ru", "")).strip():
                issues.append(Issue("ERROR", "QV2-GRIND-TEACHING-RATIONALE", path, "A teaching batch above 3 needs an immediate-construction rationale."))
            elif training_batch > 3:
                issues.append(Issue("WARN", "QV2-GRIND-TEACHING-BATCH", path, "Teaching batch exceeds the normal 1-3 range; keep it only when the next construction consumes it."))

        fields_used = {
            field for section in quest.get("teaching_sections", [])
            for field in section.get("source_fields", []) if isinstance(section, dict)
        }
        for field in ("text_ru.purpose_ru", "text_ru.success_ru", "text_ru.next_ru", "text_ru.task_text_ru"):
            if field not in fields_used:
                issues.append(Issue("ERROR" if release else "WARN", "QV2-TEACHING-COVERAGE", path, f"teaching_sections do not classify {field}."))

    for title, count in sorted(title_counter.items()):
        if title and count > 1:
            issues.append(Issue("WARN", "QV2-RU-TITLE-DUPLICATE", "editorial", f"Quest title {title!r} is repeated {count} times."))
    for chapter_alias, starts in sentence_starts_by_chapter.items():
        for index in range(len(starts) - 2):
            window = starts[index:index + 3]
            if window[0][1] and len({entry[1] for entry in window}) == 1:
                issues.append(Issue("WARN", "QV2-RU-REPEATED-OPENING", chapter_alias, f"Three adjacent quests start alike: {[entry[0] for entry in window]}."))

    # Oversized dependency lines obscure the quest graph at large GUI scales.
    # Keep this release invariant next to the semantic graph checks so a theme
    # edit cannot silently reintroduce the 1.5D regression seen in-game.
    theme_path = (
        project.root
        / "config"
        / "paxi"
        / "resourcepacks"
        / "IndustrialFrontier-Core"
        / "assets"
        / "ftbquests"
        / "ftb_quests_theme.txt"
    )
    if not theme_path.is_file():
        issues.append(Issue("ERROR", "QV2-THEME-DEPENDENCY-LINE", str(theme_path), "FTB Quests theme file is missing."))
    else:
        theme_text = theme_path.read_text(encoding="utf-8-sig")
        match = re.search(
            r"(?m)^\s*dependency_line_thickness\s*:\s*([0-9]+(?:\.[0-9]+)?)(?:[dDfF])?\s*$",
            theme_text,
        )
        if match is None:
            issues.append(Issue("ERROR", "QV2-THEME-DEPENDENCY-LINE", str(theme_path), "dependency_line_thickness is missing or malformed."))
        else:
            thickness = float(match.group(1))
            if not 0.12 <= thickness <= 0.25:
                issues.append(Issue(
                    "ERROR",
                    "QV2-THEME-DEPENDENCY-LINE",
                    str(theme_path),
                    f"dependency_line_thickness={thickness:g} is outside the safe 0.12-0.25 range.",
                ))

    migration_report = _validate_migrations(project, quests, issues)
    mod_coverage = _validate_content_mod_coverage(project, quests, release, issues)
    coverage: dict[str, dict[str, Any]] = {}
    for alias, quest in quests.items():
        for ref in quest.get("content_refs", []):
            key = f"{ref.get('kind')}:{ref.get('id')}"
            entry = coverage.setdefault(key, {"kind": ref.get("kind"), "id": ref.get("id"), "quests": [], "epochs": [], "roles": []})
            entry["quests"].append(alias)
            entry["epochs"].append(quest.get("epoch"))
            entry["roles"].append(quest.get("role"))
    for entry in coverage.values():
        for key in ("quests", "epochs", "roles"):
            entry[key] = sorted(set(entry[key]))

    report = {
        "schema_version": 2,
        "source_dir": project.source_dir.relative_to(project.root).as_posix() if project.source_dir.is_relative_to(project.root) else str(project.source_dir),
        "counts": {
            "groups": len(groups),
            "chapters": len(chapters),
            "quests": len(quests),
            "proofs": len(proofs),
            "required_quests": sum(q.get("requirement") == "required" for q in quests.values()),
            "optional_quests": sum(q.get("requirement") == "optional" for q in quests.values()),
            "blocked_proofs": len(blocked),
        },
        "groups": groups,
        "chapters": chapters,
        "quests": quests,
        "proofs": proofs,
        "chapter_for_quest": chapter_for_quest,
        "dependencies": dependencies,
        "dependency_modes": dependency_modes,
        "mandatory_dependencies": {
            alias: sorted(mandatory_dependencies.get(alias, set()))
            for alias in sorted(quests)
        },
        "roots": roots,
        "topological_order": topological,
        "commissioning_by_epoch": commissioning_by_epoch,
        "optional_campaign_chapters": sorted(optional_campaign_chapters),
        "optional_campaign_quests": sorted(optional_campaign_quests),
        "blocked_proofs": blocked,
        "coverage": [coverage[key] for key in sorted(coverage)],
        "mod_coverage": mod_coverage,
        "migration": migration_report,
        "verified_adapters": VERIFIED_ADAPTERS,
    }
    return issues, report


def validate_staging(project: Project, report: dict[str, Any], build_dir: pathlib.Path) -> list[Issue]:
    """Independent, conservative parity check over generated SNBT text."""
    issues: list[Issue] = []
    chapter_dir = build_dir / "chapters"
    if not chapter_dir.is_dir():
        return [Issue("ERROR", "QV2-STAGING-MISSING", str(chapter_dir), "Compiled chapter directory is missing.")]
    expected_chapters = report["chapters"]
    expected_quests = report["quests"]
    expected_proofs = report["proofs"]
    seen_chapters: set[str] = set()
    seen_quests: set[str] = set()
    seen_proofs: set[str] = set()
    for path in sorted(chapter_dir.glob("*.snbt")):
        text = path.read_text(encoding="utf-8")
        chapter_ids = re.findall(r'^\tid: "([0-9A-F]{16})"$', text, re.M)
        if len(chapter_ids) != 1:
            issues.append(Issue("ERROR", "QV2-PARITY-CHAPTER-ID", str(path), f"Expected one chapter ID, found {chapter_ids}."))
        else:
            seen_chapters.add(chapter_ids[0])
        seen_quests.update(re.findall(r'^\t\t\tid: "(3[0-9A-F]{15})"$', text, re.M))
        # The compiler renders each proof as a compound inside ``tasks``:
        # quest(3 tabs) -> proof compound(4) -> proof fields(5).
        # Four tabs matched the opening compound level and therefore saw zero
        # IDs while every generated task was actually present.
        seen_proofs.update(re.findall(r'^\t{5}id: "(4[0-9A-F]{15})"$', text, re.M))
        # Cheap delimiter/string validation independent from the renderer.
        stack: list[str] = []
        in_string = False
        escaped = False
        for index, character in enumerate(text):
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
            elif character in "[{":
                stack.append(character)
            elif character in "]}":
                expected = "[" if character == "]" else "{"
                if not stack or stack.pop() != expected:
                    issues.append(Issue("ERROR", "QV2-SNBT-DELIMITER", str(path), f"Mismatched delimiter at character {index}."))
                    break
        if in_string or stack:
            issues.append(Issue("ERROR", "QV2-SNBT-UNCLOSED", str(path), "SNBT has an unterminated string or delimiter."))

    expected_chapter_ids = {chapter.get("engine_id") for chapter in expected_chapters.values()}
    expected_quest_ids = {quest.get("engine_id") for quest in expected_quests.values()}
    expected_proof_ids = {proof.get("engine_id") for proof in expected_proofs.values()}
    for label, expected, seen in (
        ("chapter", expected_chapter_ids, seen_chapters),
        ("quest", expected_quest_ids, seen_quests),
        ("proof", expected_proof_ids, seen_proofs),
    ):
        if expected != seen:
            issues.append(Issue("ERROR", "QV2-SEMANTIC-PARITY", str(build_dir), f"{label} IDs differ: missing={sorted(expected-seen)}, extra={sorted(seen-expected)}."))
    return issues


def _resolve(root: pathlib.Path, value: str, default: pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(value) if value else default
    return path if path.is_absolute() else root / path


def _safe_report_path(root: pathlib.Path, value: str) -> pathlib.Path:
    path = _resolve(root, value, pathlib.Path(value)).resolve()
    report_root = (root / DEFAULT_BUILD).resolve()
    try:
        path.relative_to(report_root)
    except ValueError as exc:
        raise ValueError(f"Validation reports must stay inside {report_root}; got {path}") from exc
    if path == report_root:
        raise ValueError("A validation report must name a file inside the staging directory.")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Quest Source v2 without launching Minecraft.")
    parser.add_argument("--root", default=str(ROOT), help="Instance root (default: repository containing this tool).")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Quest Source v2 directory, relative to root by default.")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="JSON schema path, relative to root by default.")
    parser.add_argument("--build", default="", help="Optional staging directory to check semantic parity.")
    parser.add_argument("--release", action="store_true", help="Treat blocked proofs and unfinished RU editorial states as errors.")
    parser.add_argument("--json-report", default="", help="Optional path for a machine-readable validation report.")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    source = _resolve(root, args.source, DEFAULT_SOURCE)
    schema = _resolve(root, args.schema, DEFAULT_SCHEMA)
    project, issues = load_project(root, source, schema)
    semantic_issues, report = validate_project(project, release=args.release)
    issues.extend(semantic_issues)
    if args.build:
        issues.extend(validate_staging(project, report, _resolve(root, args.build, DEFAULT_BUILD)))

    errors = [issue for issue in issues if issue.level == "ERROR"]
    warnings = [issue for issue in issues if issue.level == "WARN"]
    output = {
        "schema_version": 2,
        "status": "ERROR" if errors else "WARN" if warnings else "OK",
        "errors": [dataclasses.asdict(issue) for issue in errors],
        "warnings": [dataclasses.asdict(issue) for issue in warnings],
        "summary": report.get("counts", {}),
    }
    if args.json_report:
        try:
            report_path = _safe_report_path(root, args.json_report)
        except ValueError as exc:
            parser.error(str(exc))
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    print(f"Quest Source v2: {len(errors)} error(s), {len(warnings)} warning(s)")
    for issue in issues:
        print(f"{issue.level} [{issue.code}] {issue.path}: {issue.message}")
    print("Minecraft was not launched. Runtime quests and shared lang files were not modified.")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
