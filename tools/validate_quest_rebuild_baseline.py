#!/usr/bin/env python3
"""Static QR0/QR2 validation; never starts Minecraft or mutates pack data."""

from __future__ import annotations

import json
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
AUTHORING_DIR = ROOT / "authoring/quests"
CHAPTER_DIR = ROOT / "config/ftbquests/quests/chapters"
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
        task_types = re.findall(r'^\t\t\t\ttype: "([a-z0-9_:-]+)"', body, re.MULTILINE)
        dependencies: list[str] = []
        for dependency_block in re.finditer(r"dependencies: \[(.*?)\]", body, re.DOTALL):
            dependencies.extend(re.findall(r'"(3[0-9A-F]{15})"', dependency_block.group(1)))
        tag_match = re.search(r"^\t\t\ttags: \[(.*?)\]", body, re.MULTILINE)
        tags = re.findall(r'"([^"]+)"', tag_match.group(1)) if tag_match else []
        quests[engine_id] = {
            "task_types": task_types,
            "dependencies": list(dict.fromkeys(dependencies)),
            "tags": tags,
        }
    return quests


def authoring_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chapters: list[dict[str, Any]] = []
    quests: list[dict[str, Any]] = []
    for path in sorted(AUTHORING_DIR.glob("*.json")):
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


def validate_baseline(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_chapters, source_quests = authoring_inventory()
    registry_chapters = data["chapters"]
    registry_quests = data["quests"]

    expected_snapshot = {
        "active_jars": 133,
        "snapshot_kind": "HISTORICAL_PRE_QR2_DELTA",
    }
    if data["content_snapshot"] != expected_snapshot:
        errors.append(
            "QR0 content snapshot must remain the historical 133-JAR pre-QR2 baseline"
        )

    if len(source_chapters) != 24 or len(registry_chapters) != 24:
        errors.append(f"chapter count must be 24/24, got source={len(source_chapters)} registry={len(registry_chapters)}")
    if len(source_quests) != 214 or len(registry_quests) != 214:
        errors.append(f"quest count must be 214/214, got source={len(source_quests)} registry={len(registry_quests)}")

    for key in ("chapter_file", "chapter_alias", "engine_id"):
        values = [row[key] for row in registry_chapters]
        if len(values) != len(set(values)):
            errors.append(f"duplicate chapter {key}")
    for key in ("alias", "engine_id"):
        values = [row[key] for row in registry_quests]
        if len(values) != len(set(values)):
            errors.append(f"duplicate quest {key}")

    source_chapter_map = {row["chapter_file"]: row for row in source_chapters}
    registry_chapter_map = {row["chapter_file"]: row for row in registry_chapters}
    if set(source_chapter_map) != set(registry_chapter_map):
        errors.append("chapter file set differs from authoring/quests")
    for chapter_file, source in source_chapter_map.items():
        registry = registry_chapter_map.get(chapter_file)
        if registry and registry != source:
            errors.append(f"{chapter_file}: chapter metadata differs from authoring source")

    source_quest_map = {row["engine_id"]: row for row in source_quests}
    registry_quest_map = {row["engine_id"]: row for row in registry_quests}
    if set(source_quest_map) != set(registry_quest_map):
        errors.append("quest engine-id set differs from authoring/quests")

    compiled: dict[str, dict[str, Any]] = {}
    compiled_files = sorted(CHAPTER_DIR.glob("*.snbt"))
    if len(compiled_files) != 24:
        errors.append(f"compiled chapter count must be 24, got {len(compiled_files)}")
    for path in compiled_files:
        for engine_id, quest in parse_compiled_chapter(path).items():
            if engine_id in compiled:
                errors.append(f"duplicate compiled quest engine id {engine_id}")
            compiled[engine_id] = quest
    if len(compiled) != 214:
        errors.append(f"compiled quest count must be 214, got {len(compiled)}")

    all_engine_ids = set(registry_quest_map)
    alias_by_engine = {row["engine_id"]: row["alias"] for row in registry_quests}
    for engine_id, row in registry_quest_map.items():
        source = source_quest_map.get(engine_id)
        if source:
            for key in ("chapter_file", "chapter_alias", "alias", "purpose_ru", "authoring_task_kind"):
                if row[key] != source[key]:
                    errors.append(f"{row['alias']}: {key} differs from authoring source")
        actual = compiled.get(engine_id)
        if not actual:
            errors.append(f"{row['alias']}: missing from compiled chapters")
            continue
        if actual["task_types"] != [row["task_type"]]:
            errors.append(f"{row['alias']}: task type differs from compiled chapter")
        if actual["dependencies"] != row["dependency_engine_ids"]:
            errors.append(f"{row['alias']}: dependency ids differ from compiled chapter")
        expected_aliases = [alias_by_engine[item] for item in row["dependency_engine_ids"] if item in alias_by_engine]
        if expected_aliases != row["dependency_aliases"]:
            errors.append(f"{row['alias']}: dependency aliases do not match dependency ids")
        if actual["tags"] != row["tags"]:
            errors.append(f"{row['alias']}: tags differ from compiled chapter")
        unresolved = set(row["dependency_engine_ids"]) - all_engine_ids
        if unresolved:
            errors.append(f"{row['alias']}: unresolved dependencies {sorted(unresolved)}")
        if row["engine_id"] in row["dependency_engine_ids"]:
            errors.append(f"{row['alias']}: self dependency")
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

    return errors


def validate_coverage(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = data["jars"]
    actual_jars = sorted(path.name for path in MODS_DIR.glob("*.jar"))
    registry_jars = [row["jar"] for row in rows]
    if len(actual_jars) != 134 or len(registry_jars) != 134:
        errors.append(f"JAR count must be 134/134, got source={len(actual_jars)} registry={len(registry_jars)}")
    if len(registry_jars) != len(set(registry_jars)):
        errors.append("duplicate JAR filename in coverage registry")
    if set(actual_jars) != set(registry_jars):
        errors.append(
            "coverage JAR set differs from mods directory: "
            f"missing={sorted(set(actual_jars) - set(registry_jars))}, "
            f"extra={sorted(set(registry_jars) - set(actual_jars))}"
        )

    expected = {
        "CONTENT_GAMEPLAY": 81,
        "AUTHORING_RUNTIME": 19,
        "LIBRARY_DEPENDENCY": 26,
        "CLIENT_OPTIMIZATION": 8,
    }
    counts = Counter(row["category"] for row in rows)
    if counts != Counter(expected):
        errors.append(f"category counts differ: expected={expected}, actual={dict(counts)}")

    expected_delta = {
        "baseline_active_jars": 133,
        "current_active_jars": 134,
        "post_baseline_additions": ["ftb-essentials-forge-2001.2.4.jar"],
    }
    if data["inventory_delta"] != expected_delta:
        errors.append("QR2 inventory delta must record the 133->134 FTB Essentials addition")
    post_baseline = [
        row["jar"]
        for row in rows
        if row.get("snapshot_status", "QR0_BASELINE") == "POST_BASELINE_ADDITION"
    ]
    if post_baseline != ["ftb-essentials-forge-2001.2.4.jar"]:
        errors.append(
            "exactly FTB Essentials must be marked as the QR2 post-baseline addition"
        )
    if len(rows) - len(post_baseline) != 133:
        errors.append("QR2 must preserve 133 QR0-baseline JAR rows")

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
        errors.extend(validate_coverage(coverage))

    if errors:
        print(f"FAILED: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("OK: schemas valid")
    print("OK: chapters/quests = 24/214 and all dependencies resolve")
    print("OK: active JAR coverage = 134/134 (81 content, 19 authoring, 26 libraries, 8 client)")
    print("OK: QR0 historical snapshot = 133 JARs; QR2 delta = FTB Essentials (133->134)")
    print("OK: Russian-primary human-authoring policy is present for every quest and content JAR")
    return 0


if __name__ == "__main__":
    sys.exit(main())
