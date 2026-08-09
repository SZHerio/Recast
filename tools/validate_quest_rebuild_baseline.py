#!/usr/bin/env python3
"""Static QR0/QR2 validation; never starts Minecraft or mutates pack data."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # A focused local fallback keeps the audit offline-capable.
    Draft202012Validator = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs/registries/quest_rebuild_baseline.json"
COVERAGE_PATH = ROOT / "docs/registries/quest_content_coverage.json"
BASELINE_SCHEMA_PATH = ROOT / "authoring/schemas/quest_rebuild_baseline.schema.json"
COVERAGE_SCHEMA_PATH = ROOT / "authoring/schemas/quest_content_coverage.schema.json"
HISTORICAL_AUTHORING_DIR = ROOT / "authoring/quests"
ACTIVE_SOURCE_DIR = ROOT / "authoring/questbook_v2"
ACTIVE_SOURCE_SCHEMA = ROOT / "authoring/schemas/quest_source_v2.schema.json"
ACTIVE_BUILD_DIR = ROOT / "build/questbook_v2"
CHAPTER_DIR = ROOT / "config/ftbquests/quests/chapters"
CHAPTER_GROUPS_PATH = ROOT / "config/ftbquests/quests/chapter_groups.snbt"
MODS_DIR = ROOT / "mods"
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME|LOREM)\b|ЗАГЛУШК", re.IGNORECASE)
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
ENCODING_CORRUPTION_RE = re.compile(r"\?{3,}")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def schema_errors(instance: Any, schema: Any, label: str) -> list[str]:
    if Draft202012Validator is None:
        errors: list[str] = []
        validate_schema_subset(instance, schema, schema, label, errors)
        return errors

    errors: list[str] = []
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{label} schema {location}: {error.message}")
    return errors


def validate_schema_subset(
    instance: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    location: str,
    errors: list[str],
) -> None:
    """Validate the JSON-Schema keywords used by the two local QR schemas.

    The project validator prefers jsonschema when installed. This fallback is
    intentionally limited to the checked-in schemas and avoids a network or
    package-install requirement for static pack audits.
    """
    if "$ref" in schema:
        reference = schema["$ref"]
        if not reference.startswith("#/"):
            errors.append(f"{location}: unsupported non-local schema reference {reference}")
            return
        target: Any = root_schema
        for part in reference[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        validate_schema_subset(instance, target, root_schema, location, errors)
        return

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{location}: expected constant {schema['const']!r}, got {instance!r}")
        return
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{location}: value {instance!r} is outside enum")
        return

    declared_types = schema.get("type")
    if declared_types is not None:
        allowed = declared_types if isinstance(declared_types, list) else [declared_types]

        def matches(kind: str) -> bool:
            return {
                "object": isinstance(instance, dict),
                "array": isinstance(instance, list),
                "string": isinstance(instance, str),
                "integer": isinstance(instance, int) and not isinstance(instance, bool),
                "number": isinstance(instance, (int, float)) and not isinstance(instance, bool),
                "boolean": isinstance(instance, bool),
                "null": instance is None,
            }.get(kind, False)

        if not any(matches(kind) for kind in allowed):
            errors.append(f"{location}: expected type {allowed}, got {type(instance).__name__}")
            return

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{location}: string is shorter than minLength")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{location}: string does not match {schema['pattern']}")

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{location}: array is shorter than minItems")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{location}: array is longer than maxItems")
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in instance]
            if len(canonical) != len(set(canonical)):
                errors.append(f"{location}: array items are not unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(instance):
                validate_schema_subset(item, item_schema, root_schema, f"{location}/{index}", errors)

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{location}: missing required property {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    errors.append(f"{location}: unexpected property {key}")
        for key, child_schema in properties.items():
            if key in instance:
                validate_schema_subset(instance[key], child_schema, root_schema, f"{location}/{key}", errors)

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{location}: number is below minimum")


def parse_compiled_chapter(path: Path) -> dict[str, dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    quests: dict[str, dict[str, Any]] = {}
    for match in re.finditer(r"^\t\t\{\r?\n(.*?)^\t\t\}", text, re.MULTILINE | re.DOTALL):
        body = match.group(1)
        id_match = re.search(r'^\t\t\tid: "(3[0-9A-F]{15})"', body, re.MULTILINE)
        if not id_match:
            continue
        engine_id = id_match.group(1)
        task_types = re.findall(r'^\t\t\t\t\ttype: "([a-z0-9_:-]+)"', body, re.MULTILINE)
        proof_ids = re.findall(r'^\t\t\t\t\tid: "(4[0-9A-F]{15})"', body, re.MULTILINE)
        dependencies: list[str] = []
        for dependency_block in re.finditer(r"dependencies: \[(.*?)\]", body, re.DOTALL):
            dependencies.extend(re.findall(r'"(3[0-9A-F]{15})"', dependency_block.group(1)))
        tag_match = re.search(r"^\t\t\ttags: \[(.*?)\]", body, re.MULTILINE)
        tags = re.findall(r'"([^"]+)"', tag_match.group(1)) if tag_match else []
        quests[engine_id] = {
            "task_types": task_types,
            "proof_ids": proof_ids,
            "dependencies": list(dict.fromkeys(dependencies)),
            "tags": tags,
            "optional": bool(re.search(r"^\t\t\toptional: true$", body, re.MULTILINE)),
            "dependency_mode": (
                "ANY_OF"
                if re.search(r'^\t\t\tdependency_requirement: "one_completed"$', body, re.MULTILINE)
                else "ALL_OF"
            ),
        }
    return quests


def compiled_chapter_engine_id(path: Path) -> str | None:
    match = re.search(r'^\tid: "(2[0-9A-F]{15})"$', path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def historical_authoring_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chapters: list[dict[str, Any]] = []
    quests: list[dict[str, Any]] = []
    for path in sorted(HISTORICAL_AUTHORING_DIR.glob("*.json")):
        source = load_json(path)
        chapter_file = path.stem
        chapter_optional = bool(source.get("optional", False))
        chapter = {
            "chapter_file": chapter_file,
            "chapter_alias": source["chapter_alias"],
            "engine_id": str(source["engine_id"]),
            "authoring_optional": chapter_optional,
            "quest_count": len(source["quests"]),
        }
        chapters.append(chapter)
        for quest in source["quests"]:
            quests.append(
                {
                    "chapter_file": chapter_file,
                    "chapter_alias": source["chapter_alias"],
                    "alias": quest["alias"],
                    "engine_id": str(quest["engine_id"]),
                    "purpose_ru": quest["purpose"],
                    "authoring_task_kind": quest.get("task_kind") or None,
                }
            )
    return chapters, quests


def require_ru_text(value: str, label: str, errors: list[str]) -> None:
    if not CYRILLIC_RE.search(value):
        errors.append(f"{label}: Russian-primary field has no Cyrillic text")
    if PLACEHOLDER_RE.search(value):
        errors.append(f"{label}: placeholder marker is forbidden")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def dependency_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        state[node] = 1
        stack.append(node)
        for dependency in graph.get(node, []):
            if dependency not in graph:
                continue
            if state.get(dependency, 0) == 0:
                found = visit(dependency)
                if found:
                    return found
            elif state.get(dependency) == 1:
                start = stack.index(dependency)
                return stack[start:] + [dependency]
        stack.pop()
        state[node] = 2
        return None

    for node in graph:
        if state.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return None


def validate_baseline(data: dict[str, Any]) -> list[str]:
    """Validate the immutable QR0 migration inventory, never active runtime."""
    errors: list[str] = []
    source_chapters, source_quests = historical_authoring_inventory()
    registry_chapters = data["chapters"]
    registry_quests = data["quests"]
    expected_counts = data["expected_counts"]

    expected_snapshot = {
        "active_jars": 133,
        "snapshot_kind": "HISTORICAL_PRE_QR2_DELTA",
    }
    if data["content_snapshot"] != expected_snapshot:
        errors.append("QR0 content snapshot must remain the historical 133-JAR pre-QR2 baseline")

    frozen_hash = canonical_sha256({"chapters": registry_chapters, "quests": registry_quests})
    if frozen_hash != data["historical_inventory_sha256"]:
        errors.append(
            "QR0 historical inventory hash differs: "
            f"expected={data['historical_inventory_sha256']} actual={frozen_hash}"
        )

    expected_chapters = expected_counts["chapters"]
    expected_quests = expected_counts["quests"]
    if len(source_chapters) != expected_chapters or len(registry_chapters) != expected_chapters:
        errors.append(
            "historical chapter count differs: "
            f"expected={expected_chapters} source={len(source_chapters)} registry={len(registry_chapters)}"
        )
    if len(source_quests) != expected_quests or len(registry_quests) != expected_quests:
        errors.append(
            "historical quest count differs: "
            f"expected={expected_quests} source={len(source_quests)} registry={len(registry_quests)}"
        )

    for key in ("chapter_file", "chapter_alias", "engine_id"):
        values = [row[key] for row in registry_chapters]
        if len(values) != len(set(values)):
            errors.append(f"duplicate historical chapter {key}")
    for key in ("alias", "engine_id"):
        values = [row[key] for row in registry_quests]
        if len(values) != len(set(values)):
            errors.append(f"duplicate historical quest {key}")

    source_chapter_map = {row["chapter_file"]: row for row in source_chapters}
    registry_chapter_map = {row["chapter_file"]: row for row in registry_chapters}
    if set(source_chapter_map) != set(registry_chapter_map):
        errors.append("historical chapter file set differs from authoring/quests")
    for chapter_file, source in source_chapter_map.items():
        registry = registry_chapter_map.get(chapter_file)
        if registry and registry != source:
            errors.append(f"{chapter_file}: historical chapter metadata differs from authoring source")

    source_quest_map = {row["engine_id"]: row for row in source_quests}
    registry_quest_map = {row["engine_id"]: row for row in registry_quests}
    if set(source_quest_map) != set(registry_quest_map):
        errors.append("historical quest engine-id set differs from authoring/quests")

    all_engine_ids = set(registry_quest_map)
    alias_by_engine = {row["engine_id"]: row["alias"] for row in registry_quests}
    historical_graph: dict[str, list[str]] = {}
    for engine_id, row in registry_quest_map.items():
        source = source_quest_map.get(engine_id)
        if source:
            for key in ("chapter_file", "chapter_alias", "alias", "purpose_ru", "authoring_task_kind"):
                if row[key] != source[key]:
                    errors.append(f"{row['alias']}: historical {key} differs from authoring source")
        expected_aliases = [
            alias_by_engine[item]
            for item in row["dependency_engine_ids"]
            if item in alias_by_engine
        ]
        if expected_aliases != row["dependency_aliases"]:
            errors.append(f"{row['alias']}: historical dependency aliases do not match dependency ids")
        unresolved = set(row["dependency_engine_ids"]) - all_engine_ids
        if unresolved:
            errors.append(f"{row['alias']}: unresolved historical dependencies {sorted(unresolved)}")
        if row["engine_id"] in row["dependency_engine_ids"]:
            errors.append(f"{row['alias']}: historical self dependency")
        historical_graph[engine_id] = row["dependency_engine_ids"]
        if row["required"] == row["optional"]:
            errors.append(f"{row['alias']}: required and optional must be logical opposites")
        if row["mainline"] and not row["required"]:
            errors.append(f"{row['alias']}: mainline quest must be required")
        require_ru_text(row["purpose_ru"], f"{row['alias']}.purpose_ru", errors)
        ru = row["ru_copy"]
        if (
            ru["primary_language"] != "ru_ru"
            or not ru["human_authoring_required"]
            or not ru["machine_translation_forbidden"]
            or not ru["placeholders_forbidden"]
        ):
            errors.append(f"{row['alias']}: invalid Russian-primary authoring policy")
        marks = ru["editorial_checks"]
        if ru["ru_ready"] != all(marks.values()):
            errors.append(f"{row['alias']}: RU_READY must equal all four editorial checks")
        if ru["ru_ready"] and ru["status"] != "APPROVED_HUMAN_COPY":
            errors.append(f"{row['alias']}: RU-ready copy must have APPROVED_HUMAN_COPY status")

    cycle = dependency_cycle(historical_graph)
    if cycle:
        errors.append(f"historical dependency cycle: {' -> '.join(cycle)}")
    return errors


def validate_active_runtime(contract: dict[str, Any]) -> list[str]:
    """Validate promoted V2 source -> staged build -> active FTB Quests runtime."""
    errors: list[str] = []
    expected = contract["expected_counts"]

    required_paths = [
        ACTIVE_SOURCE_DIR,
        ACTIVE_SOURCE_SCHEMA,
        ACTIVE_BUILD_DIR,
        ROOT / contract["build_manifest"],
        ROOT / contract["validation_report"],
        ROOT / contract["graph_report"],
        ROOT / contract["semantic_audit_report"],
        CHAPTER_DIR,
        CHAPTER_GROUPS_PATH,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required_paths if not path.exists()]
    if missing:
        return [f"active V2 contract paths are missing: {missing}"]

    try:
        from validate_questbook_v2 import VERIFIED_ADAPTERS, load_project, validate_project
    except ImportError as exc:
        return [f"cannot load active V2 validator: {exc}"]

    project, source_issues = load_project(ROOT, ACTIVE_SOURCE_DIR, ACTIVE_SOURCE_SCHEMA)
    semantic_issues, report = validate_project(project, release=True)
    for issue in source_issues + semantic_issues:
        if issue.level == "ERROR":
            errors.append(f"active V2 {issue.code} {issue.path}: {issue.message}")

    actual_counts = {
        "chapters": int(report.get("counts", {}).get("chapters", -1)),
        "quests": int(report.get("counts", {}).get("quests", -1)),
        "proofs": int(report.get("counts", {}).get("proofs", -1)),
        "dependency_edges": sum(len(items) for items in report.get("dependencies", {}).values()),
    }
    if actual_counts != expected:
        errors.append(f"active V2 source counts differ: expected={expected} actual={actual_counts}")

    manifest_path = ROOT / contract["build_manifest"]
    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != 2 or manifest.get("compiler_version") != 2:
        errors.append("active V2 manifest must use schema/compiler version 2")
    if manifest.get("status") != "STAGED":
        errors.append(f"active V2 manifest status must be STAGED, got {manifest.get('status')!r}")

    source_files = sorted(path for path in ACTIVE_SOURCE_DIR.rglob("*.json") if path.is_file())
    actual_source_keys = {path.relative_to(ROOT).as_posix() for path in source_files}
    manifest_source_hashes = manifest.get("source_hashes", {})
    if set(manifest_source_hashes) != actual_source_keys:
        errors.append(
            "active V2 manifest source set differs: "
            f"missing={sorted(actual_source_keys - set(manifest_source_hashes))} "
            f"extra={sorted(set(manifest_source_hashes) - actual_source_keys)}"
        )
    for relative, expected_hash in manifest_source_hashes.items():
        path = ROOT / relative
        if path.is_file() and sha256_file(path) != expected_hash:
            errors.append(f"active V2 source hash differs: {relative}")

    manifest_files = manifest.get("files", {})
    supplemental_build_keys = {
        (ROOT / contract["semantic_audit_report"]).relative_to(ACTIVE_BUILD_DIR).as_posix(),
    }
    actual_build_keys = {
        path.relative_to(ACTIVE_BUILD_DIR).as_posix()
        for path in ACTIVE_BUILD_DIR.rglob("*")
        if path.is_file()
        and path.name != "manifest.json"
        and path.relative_to(ACTIVE_BUILD_DIR).as_posix() not in supplemental_build_keys
    }
    if set(manifest_files) != actual_build_keys:
        errors.append(
            "active V2 build manifest file set differs: "
            f"missing={sorted(actual_build_keys - set(manifest_files))} "
            f"extra={sorted(set(manifest_files) - actual_build_keys)}"
        )
    for relative, expected_hash in manifest_files.items():
        path = ACTIVE_BUILD_DIR / relative
        if path.is_file() and sha256_file(path) != expected_hash:
            errors.append(f"active V2 build hash differs: {relative}")

    validation = load_json(ROOT / contract["validation_report"])
    validation_counts = validation.get("counts", {})
    for key in ("chapters", "quests", "proofs"):
        if validation_counts.get(key) != expected[key]:
            errors.append(
                f"active V2 validation report {key} expected {expected[key]}, "
                f"got {validation_counts.get(key)}"
            )
    if validation.get("errors"):
        errors.append("active V2 validation report contains release errors")
    if validation.get("status") not in {"OK", "WARN"}:
        errors.append(f"active V2 validation report status is {validation.get('status')!r}")

    graph_report = load_json(ROOT / contract["graph_report"])
    if len(graph_report.get("edges", [])) != expected["dependency_edges"]:
        errors.append(
            "active V2 graph edge count differs: "
            f"expected={expected['dependency_edges']} actual={len(graph_report.get('edges', []))}"
        )

    semantic_audit = load_json(ROOT / contract["semantic_audit_report"])
    semantic_summary = semantic_audit.get("summary", {})
    if semantic_audit.get("status") != "PASS_STATIC_RUNTIME_SYNC" or semantic_audit.get("errors"):
        errors.append("active V2 semantic audit must be PASS_STATIC_RUNTIME_SYNC with zero errors")
    for key in ("chapters", "quests", "proofs", "dependency_edges"):
        if semantic_summary.get(key) != expected[key]:
            errors.append(
                f"active V2 semantic audit {key} expected {expected[key]}, "
                f"got {semantic_summary.get(key)}"
            )

    chapter_manifest = {
        relative: digest
        for relative, digest in manifest_files.items()
        if relative.startswith("chapters/") and relative.endswith(".snbt")
    }
    runtime_files = sorted(CHAPTER_DIR.glob("*.snbt"))
    runtime_keys = {f"chapters/{path.name}" for path in runtime_files}
    if len(chapter_manifest) != expected["chapters"] or len(runtime_files) != expected["chapters"]:
        errors.append(
            "active runtime chapter count differs: "
            f"expected={expected['chapters']} manifest={len(chapter_manifest)} runtime={len(runtime_files)}"
        )
    if set(chapter_manifest) != runtime_keys:
        errors.append(
            "active runtime chapter set differs from staged manifest: "
            f"missing={sorted(set(chapter_manifest) - runtime_keys)} "
            f"extra={sorted(runtime_keys - set(chapter_manifest))}"
        )
    for relative, expected_hash in chapter_manifest.items():
        runtime_path = CHAPTER_DIR / Path(relative).name
        if runtime_path.is_file() and sha256_file(runtime_path) != expected_hash:
            errors.append(f"active runtime chapter hash differs from staged build: {runtime_path.name}")
    group_hash = manifest_files.get("chapter_groups.snbt")
    if group_hash is None or sha256_file(CHAPTER_GROUPS_PATH) != group_hash:
        errors.append("active runtime chapter_groups.snbt differs from staged build")

    compiled: dict[str, dict[str, Any]] = {}
    compiled_chapter_ids: dict[str, str | None] = {}
    for path in runtime_files:
        compiled_chapter_ids[path.stem] = compiled_chapter_engine_id(path)
        for engine_id, quest in parse_compiled_chapter(path).items():
            if engine_id in compiled:
                errors.append(f"duplicate active runtime quest engine id {engine_id}")
            compiled[engine_id] = quest

    report_chapters = report.get("chapters", {})
    expected_chapter_ids = {
        chapter["filename"]: chapter["engine_id"]
        for chapter in report_chapters.values()
    }
    if compiled_chapter_ids != expected_chapter_ids:
        errors.append("active runtime chapter engine IDs differ from V2 source")

    source_quests = report.get("quests", {})
    alias_to_id = {alias: quest["engine_id"] for alias, quest in source_quests.items()}
    source_ids = set(alias_to_id.values())
    if set(compiled) != source_ids:
        errors.append(
            "active runtime quest engine-id set differs from V2 source: "
            f"missing={sorted(source_ids - set(compiled))} extra={sorted(set(compiled) - source_ids)}"
        )
    if len(compiled) != expected["quests"]:
        errors.append(f"active runtime quest count expected {expected['quests']}, got {len(compiled)}")

    for alias, source in source_quests.items():
        engine_id = source["engine_id"]
        actual = compiled.get(engine_id)
        if actual is None:
            continue
        expected_dependencies = [alias_to_id[item] for item in report["dependencies"][alias]]
        if actual["dependencies"] != expected_dependencies:
            errors.append(f"{alias}: active runtime dependencies differ from V2 source")
        if actual["dependency_mode"] != report["dependency_modes"][alias]:
            errors.append(f"{alias}: active runtime dependency mode differs from V2 source")
        if actual["tags"] != source.get("tags", []):
            errors.append(f"{alias}: active runtime tags differ from V2 source")
        if actual["optional"] != (source["requirement"] == "optional"):
            errors.append(f"{alias}: active runtime optionality differs from V2 source")
        expected_proof_ids = [proof["engine_id"] for proof in source["proofs"]]
        if actual["proof_ids"] != expected_proof_ids:
            errors.append(f"{alias}: active runtime proof IDs differ from V2 source")
        expected_task_types = [VERIFIED_ADAPTERS[proof["type"]]["runtime_type"] for proof in source["proofs"]]
        if actual["task_types"] != expected_task_types:
            errors.append(f"{alias}: active runtime proof types differ from V2 source")

    return errors


def validate_coverage(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = data["jars"]
    actual_jars = sorted(path.name for path in MODS_DIR.glob("*.jar"))
    registry_jars = [row["jar"] for row in rows]
    if len(actual_jars) != 133 or len(registry_jars) != 133:
        errors.append(f"JAR count must be 133/133 after JER quarantine, got source={len(actual_jars)} registry={len(registry_jars)}")
    if len(registry_jars) != len(set(registry_jars)):
        errors.append("duplicate JAR filename in coverage registry")
    if set(actual_jars) != set(registry_jars):
        errors.append(
            "coverage JAR set differs from mods directory: "
            f"missing={sorted(set(actual_jars) - set(registry_jars))}, "
            f"extra={sorted(set(registry_jars) - set(actual_jars))}"
        )

    expected = {
        "CONTENT_GAMEPLAY": 80,
        "AUTHORING_RUNTIME": 19,
        "LIBRARY_DEPENDENCY": 26,
        "CLIENT_OPTIMIZATION": 8,
    }
    counts = Counter(row["category"] for row in rows)
    if counts != Counter(expected):
        errors.append(f"category counts differ: expected={expected}, actual={dict(counts)}")

    expected_delta = {
        "baseline_active_jars": 133,
        "current_active_jars": 133,
        "post_baseline_additions": ["ftb-essentials-forge-2001.2.4.jar"],
        "post_baseline_removals": ["JustEnoughResources-1.20.1-1.4.0.247.jar"],
    }
    if data["inventory_delta"] != expected_delta:
        errors.append("QR2 inventory delta must record the FTB Essentials addition and JER quarantine")
    post_baseline = [
        row["jar"]
        for row in rows
        if row.get("snapshot_status", "QR0_BASELINE") == "POST_BASELINE_ADDITION"
    ]
    if post_baseline != ["ftb-essentials-forge-2001.2.4.jar"]:
        errors.append(
            "exactly FTB Essentials must be marked as the QR2 post-baseline addition"
        )
    removals = data["inventory_delta"]["post_baseline_removals"]
    if set(removals) & set(registry_jars):
        errors.append("quarantined JARs must not remain in the active coverage registry")
    if len(rows) - len(post_baseline) + len(removals) != 133:
        errors.append("QR2 delta must reconstruct the 133-JAR QR0 baseline")

    compiled_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(CHAPTER_DIR.glob("*.snbt")))
    for row in rows:
        expected_refs = sum(compiled_text.count(f"{modid}:") for modid in row["modids"])
        if row["current_quest_ref_count"] != expected_refs:
            errors.append(f"{row['jar']}: current_quest_ref_count expected {expected_refs}")
        contract = row["coverage_contract"]
        require_ru_text(contract["summary_ru"], f"{row['jar']}.summary_ru", errors)
        require_ru_text(contract["verification_ru"], f"{row['jar']}.verification_ru", errors)
        require_ru_text(contract["integration_ru"], f"{row['jar']}.integration_ru", errors)
        for index, topic in enumerate(contract["minimum_topics_ru"]):
            require_ru_text(topic, f"{row['jar']}.minimum_topics_ru[{index}]", errors)

        ru = row["ru_copy_coverage"]
        if (
            ru["primary_language"] != "ru_ru"
            or not ru["machine_translation_forbidden"]
            or not ru["placeholders_forbidden"]
        ):
            errors.append(f"{row['jar']}: invalid Russian-primary coverage policy")
        marks = ru["editorial_checks"]
        if ru["ru_ready"] != all(marks.values()):
            errors.append(f"{row['jar']}: RU_READY must equal all four editorial checks")
        if ru["ru_ready"] and ru["status"] != "APPROVED_HUMAN_COPY":
            errors.append(f"{row['jar']}: RU-ready coverage must have APPROVED_HUMAN_COPY status")

        if row["category"] == "CONTENT_GAMEPLAY":
            if row["role"] == "INSTRUMENTAL_NO_QUEST":
                errors.append(f"{row['jar']}: content JAR cannot be instrumental-only")
            if not row["home_chapter"] or not row["epochs"]:
                errors.append(f"{row['jar']}: content JAR requires home chapter and epoch coverage")
            if not contract["minimum_topics_ru"]:
                errors.append(f"{row['jar']}: content JAR requires minimum tutorial topics")
            if not ru["human_authoring_required"] or ru["status"] == "NOT_APPLICABLE":
                errors.append(f"{row['jar']}: content JAR requires human-authored Russian copy")
            if not ru["minimum_scope"]:
                errors.append(f"{row['jar']}: content JAR requires non-empty Russian copy scope")
        else:
            if row["role"] != "INSTRUMENTAL_NO_QUEST":
                errors.append(f"{row['jar']}: infrastructure JAR must be instrumental-only")
            if row["home_chapter"] is not None or row["epochs"]:
                errors.append(f"{row['jar']}: infrastructure JAR must not own a quest chapter/epoch")
            if row["status"] != "NO_QUEST_REQUIRED":
                errors.append(f"{row['jar']}: infrastructure JAR must have NO_QUEST_REQUIRED status")
            if ru["status"] != "NOT_APPLICABLE" or ru["human_authoring_required"]:
                errors.append(f"{row['jar']}: infrastructure JAR RU status must be NOT_APPLICABLE")

    return errors


def main() -> int:
    required_paths = [BASELINE_PATH, COVERAGE_PATH, BASELINE_SCHEMA_PATH, COVERAGE_SCHEMA_PATH]
    missing = [str(path.relative_to(ROOT)) for path in required_paths if not path.is_file()]
    if missing:
        print("ERROR: missing required files:", ", ".join(missing))
        return 1

    corrupted = [
        str(path.relative_to(ROOT))
        for path in required_paths
        if ENCODING_CORRUPTION_RE.search(path.read_text(encoding="utf-8"))
    ]
    if corrupted:
        print("ERROR: possible encoding corruption ('???'):", ", ".join(corrupted))
        return 1

    baseline = load_json(BASELINE_PATH)
    coverage = load_json(COVERAGE_PATH)
    baseline_schema = load_json(BASELINE_SCHEMA_PATH)
    coverage_schema = load_json(COVERAGE_SCHEMA_PATH)

    errors = []
    errors.extend(schema_errors(baseline, baseline_schema, "quest_rebuild_baseline"))
    errors.extend(schema_errors(coverage, coverage_schema, "quest_content_coverage"))
    if not errors:
        errors.extend(validate_baseline(baseline))
        errors.extend(validate_active_runtime(baseline["active_runtime_contract"]))
        errors.extend(validate_coverage(coverage))

    if errors:
        print(f"FAILED: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("OK: schemas valid")
    print("OK: frozen QR0 migration inventory = 24 chapters / 214 quests (hash locked)")
    print("OK: active V2 source/build/runtime sync = 27 chapters / 501 quests / 822 proofs / 668 edges")
    print("OK: active JAR coverage = 133/133 (80 content, 19 authoring, 26 libraries, 8 client)")
    print("OK: QR0 historical snapshot = 133 JARs; QR2 delta = +FTB Essentials, -JER quarantine")
    print("OK: Russian-primary human-authoring policy is present for every quest and content JAR")
    return 0


if __name__ == "__main__":
    sys.exit(main())
