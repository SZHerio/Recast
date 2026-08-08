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


def _validate_migrations(project: Project, quests: dict[str, dict[str, Any]], issues: list[Issue]) -> dict[str, Any]:
    old_registry_path = project.root / "docs/registries/stable_ids.json"
    old_ids: dict[str, str] = {}
    if old_registry_path.is_file():
        try:
            registry = json.loads(old_registry_path.read_text(encoding="utf-8-sig"))
            old_ids = {str(k): str(v) for k, v in registry.get("ids", {}).items() if str(k).startswith("if.quest.")}
        except (OSError, json.JSONDecodeError):
            issues.append(Issue("WARN", "QV2-MIGRATION-OLD-REGISTRY", str(old_registry_path), "Could not read the old stable registry."))

    mapped_old_aliases: set[str] = set()
    mappings: list[dict[str, Any]] = []
    seen_migration_ids: set[str] = set()
    for document in project.migrations:
        migration_id = document.get("migration_id")
        path = project.migration_files.get(str(migration_id), "migrations")
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
            for required_field in ("old_engine_id", "new_alias", "new_engine_id", "policy", "reason", "evidence"):
                if required_field not in mapping:
                    issues.append(Issue("ERROR", "QV2-MIGRATION-MAPPING-FIELD", where, f"Mapping is missing {required_field}."))
            if policy not in {"carry", "review", "reset"}:
                issues.append(Issue("ERROR", "QV2-MIGRATION-POLICY", where, f"Unknown policy {policy!r}."))
            new_alias = mapping.get("new_alias")
            new_id = mapping.get("new_engine_id")
            if new_alias not in quests:
                issues.append(Issue("ERROR", "QV2-MIGRATION-TARGET", where, f"Unknown v2 quest {new_alias!r}."))
            elif new_id != quests[new_alias].get("engine_id"):
                issues.append(Issue("ERROR", "QV2-MIGRATION-TARGET-ID", where, "new_engine_id does not match the v2 source."))
            old_alias = mapping.get("old_alias")
            old_id = mapping.get("old_engine_id")
            if isinstance(old_alias, str):
                mapped_old_aliases.add(old_alias)
                if old_alias in old_ids and old_id != old_ids[old_alias]:
                    issues.append(Issue("ERROR", "QV2-MIGRATION-SOURCE-ID", where, "old_engine_id does not match docs/registries/stable_ids.json."))
            evidence = mapping.get("evidence")
            reason = mapping.get("reason")
            if not isinstance(reason, str) or len(reason.strip()) < 12 or not isinstance(evidence, list) or not evidence:
                issues.append(Issue("ERROR", "QV2-MIGRATION-EVIDENCE", where, "Every mapping needs a reason and non-empty evidence."))
            if policy == "carry" and old_id != new_id:
                issues.append(Issue("ERROR", "QV2-MIGRATION-CARRY-ID", where, "carry requires the same engine ID; no runtime progress converter exists."))
            mappings.append(mapping)

    reused_old_ids = {quest.get("engine_id") for quest in quests.values()} & set(old_ids.values())
    mapped_carry_ids = {item.get("new_engine_id") for item in mappings if item.get("policy") == "carry"}
    for reused in sorted(reused_old_ids - mapped_carry_ids):
        issues.append(Issue("ERROR", "QV2-ID-REUSE-UNDECLARED", "migrations", f"Old engine ID {reused} is reused without a carry mapping."))
    return {
        "migration_documents": len(project.migrations),
        "mappings": mappings,
        "old_quest_alias_count": len(old_ids),
        "mapped_old_aliases": sorted(mapped_old_aliases),
        "unmapped_old_aliases": sorted(set(old_ids) - mapped_old_aliases),
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
    for alias, quest in quests.items():
        for ref in quest.get("content_refs", []):
            kind = ref.get("kind")
            value = str(ref.get("id", "")).lstrip("#")
            modid = ""
            if kind == "mod":
                modid = value.split(":", 1)[0]
            elif kind in resource_kinds and ":" in value:
                modid = value.split(":", 1)[0]
            if modid:
                by_modid[modid].add(alias)

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

    # Commissioning is the sole authoritative join and epoch boundary.
    memo: dict[str, set[str]] = {}
    commissioning_by_epoch: dict[str, str] = {}
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
            if quest.get("epoch") == next_epoch and not any(quests.get(dep, {}).get("epoch") == next_epoch for dep in dependencies.get(alias, []))
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
        seen_proofs.update(re.findall(r'^\t\t\t\tid: "(4[0-9A-F]{15})"$', text, re.M))
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
