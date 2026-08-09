#!/usr/bin/env python3
"""Repair Quest Source v2 migration identities without starting Minecraft.

The default mode is a read-only preview.  ``--apply`` performs the mechanical
JSON rewrite after every source, collision and QR0 coverage check has passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "authoring/questbook_v2"
MIGRATION_DIR = SOURCE_DIR / "migrations"
BASELINE_PATH = ROOT / "docs/registries/quest_rebuild_baseline.json"
STABLE_IDS_PATH = ROOT / "docs/registries/stable_ids.json"
RETIRED_IDS_PATH = ROOT / "docs/registries/retired_ids.json"
PROOF_CONTRACTS_PATH = ROOT / "docs/registries/quest_qr0_proof_contracts.json"
LEGACY_CHAPTER_DIR = ROOT / "config/ftbquests/quests/chapters"

# QR0 had one workshop chapter.  Quest Source v2 folds its lessons into the
# broader control-and-pressure chapter, so the old chapter ID has no active
# identity and must remain a permanent tombstone.
EXPLICIT_NON_QUEST_RETIREMENTS: dict[str, dict[str, str]] = {
    "2023000000000001": {
        "kind": "chapter",
        "successor_alias": "if.chapter.v2.control",
        "reason_ru": (
            "Старая глава мастерской объединена с главой управления и давления; "
            "её прежний ID больше не обозначает активную главу."
        ),
        "evidence": "authoring/questbook_v2/23_control_pressure.json",
    },
}

QUEST_BLOCK_RE = re.compile(r"^\t\t\{\r?\n(.*?)^\t\t\}", re.MULTILINE | re.DOTALL)
QUEST_ID_RE = re.compile(r'^\t\t\tid: "(3[0-9A-F]{15})"', re.MULTILINE)
TASK_ID_RE = re.compile(r'^\t+id: "(4[0-9A-F]{15})"', re.MULTILINE)
REWARD_ID_RE = re.compile(r'^\t+id: "(5[0-9A-F]{15})"', re.MULTILINE)
TASK_BLOCK_RE = re.compile(r"^\t\t\ttasks: \[\{\r?\n(.*?)^\t\t\t\}\]", re.MULTILINE | re.DOTALL)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def deterministic_id(prefix: str, semantic_alias: str, reserved: set[str]) -> str:
    for attempt in range(10_000):
        material = f"quest-source-v2-migration:{semantic_alias}:{attempt}".encode("utf-8")
        candidate = prefix + hashlib.sha256(material).hexdigest().upper()[:15]
        if candidate not in reserved:
            reserved.add(candidate)
            return candidate
    raise RuntimeError(f"Could not allocate a collision-free ID for {semantic_alias}")


def _boolean_field(body: str, name: str) -> bool:
    match = re.search(rf"^\s*{re.escape(name)}: (true|false)$", body, re.MULTILINE)
    return bool(match and match.group(1) == "true")


def _canonical_legacy_task(body: str, quest_id: str, source: str) -> dict[str, Any]:
    task_block_match = TASK_BLOCK_RE.search(body)
    if not task_block_match:
        raise RuntimeError(f"QR0 quest {quest_id} does not have one canonical task block")
    task_body = task_block_match.group(1)
    task_ids = TASK_ID_RE.findall(task_body)
    type_match = re.search(r'^\s*type: "([a-z0-9_:.-]+)"$', task_body, re.MULTILINE)
    if len(task_ids) != 1 or not type_match:
        raise RuntimeError(f"QR0 quest {quest_id} task identity is ambiguous")
    task_type = type_match.group(1)
    predicate: dict[str, Any] = {"kind": task_type}
    if task_type == "item":
        count_match = re.search(r"^\s*count: (\d+)L?$", task_body, re.MULTILINE)
        count = int(count_match.group(1)) if count_match else 1
        filter_match = re.search(r"ftbfiltersystem:item_tag\(([^)]+)\)", task_body)
        item_start = task_body.find("item: {")
        item_match = re.search(r'^\s*id: "([a-z0-9_.-]+:[a-z0-9_./-]+)"$', task_body[item_start:], re.MULTILINE) if item_start >= 0 else None
        if filter_match:
            selector = {"kind": "item_tag", "id": filter_match.group(1)}
        elif item_match:
            selector = {"kind": "item", "id": item_match.group(1)}
        else:
            raise RuntimeError(f"QR0 item task {task_ids[0]} has no supported selector")
        predicate.update({
            "selector": selector,
            "count": count,
            "only_from_crafting": _boolean_field(task_body, "only_from_crafting"),
            "match_nbt": _boolean_field(task_body, "match_nbt"),
            "weak_nbt_match": _boolean_field(task_body, "weak_nbt_match"),
        })
    elif task_type == "dimension":
        dimension_match = re.search(r'^\s*dimension: "([a-z0-9_.-]+:[a-z0-9_./-]+)"$', task_body, re.MULTILINE)
        if not dimension_match:
            raise RuntimeError(f"QR0 dimension task {task_ids[0]} has no dimension")
        predicate["dimension"] = dimension_match.group(1)
    elif task_type != "checkmark":
        raise RuntimeError(f"Unsupported QR0 task type {task_type!r} in {quest_id}")
    return {
        "engine_id": task_ids[0],
        "type": task_type,
        "predicate": predicate,
        "source": source,
        "source_fingerprint_sha256": hashlib.sha256(task_body.encode("utf-8")).hexdigest(),
    }


def legacy_children() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(LEGACY_CHAPTER_DIR.glob("*.snbt")):
        text = path.read_text(encoding="utf-8-sig")
        for match in QUEST_BLOCK_RE.finditer(text):
            body = match.group(1)
            quest_match = QUEST_ID_RE.search(body)
            if not quest_match:
                continue
            quest_id = quest_match.group(1)
            if quest_id in result:
                raise RuntimeError(f"Duplicate legacy quest ID {quest_id}")
            result[quest_id] = {
                "tasks": TASK_ID_RE.findall(body),
                "rewards": REWARD_ID_RE.findall(body),
                "chapter": [path.relative_to(ROOT).as_posix()],
                "task_contract": _canonical_legacy_task(
                    body,
                    quest_id,
                    path.relative_to(ROOT).as_posix(),
                ),
            }
    return result


def _pack_tag_members(tag_id: str, seen: set[str] | None = None) -> set[str] | None:
    seen = set() if seen is None else seen
    if tag_id in seen or ":" not in tag_id:
        return None
    seen.add(tag_id)
    namespace, path = tag_id.split(":", 1)
    candidates = sorted(
        (ROOT / "config/paxi/datapacks").glob(f"*/data/{namespace}/tags/items/{path}.json")
    )
    candidates += sorted((ROOT / "kubejs/data").glob(f"{namespace}/tags/items/{path}.json"))
    if not candidates:
        return None
    members: set[str] = set()
    for candidate in candidates:
        document = load_json(candidate)
        if document.get("replace") is True:
            members.clear()
        for raw_value in document.get("values", []):
            value = raw_value.get("id") if isinstance(raw_value, dict) else raw_value
            if not isinstance(value, str):
                continue
            if value.startswith("#"):
                nested = _pack_tag_members(value[1:], seen)
                if nested is None:
                    return None
                members.update(nested)
            else:
                members.add(value)
    return members


def _legacy_task_implies_current(task: dict[str, Any], quest: dict[str, Any]) -> tuple[bool, str]:
    proofs = quest.get("proofs", [])
    if len(proofs) != 1 or proofs[0].get("status") != "verified":
        return False, "the successor does not have exactly one verified proof"
    proof = proofs[0]
    predicate = task["predicate"]
    if task["type"] != proof.get("type"):
        return False, f"task type {task['type']} does not imply {proof.get('type')}"
    if task["type"] == "checkmark":
        return True, "same manually reviewed checkmark contract"
    if task["type"] == "dimension":
        same = predicate.get("dimension") == proof.get("dimension")
        return same, "same dimension" if same else "dimension changed"
    old_selector = predicate["selector"]
    if "item" in proof:
        new_selector = {"kind": "item", "id": proof["item"].get("id")}
        new_count = int(proof["item"].get("count", 1))
        new_payload = proof["item"]
    elif "item_tag" in proof:
        new_selector = {"kind": "item_tag", "id": proof["item_tag"].get("id")}
        new_count = int(proof["item_tag"].get("count", 1))
        new_payload = proof["item_tag"]
    else:
        return False, "current item proof has no supported selector"
    if int(predicate["count"]) < new_count:
        return False, f"old count {predicate['count']} is below new count {new_count}"
    if old_selector == new_selector:
        selector_implies = True
    elif old_selector["kind"] == "item" and new_selector["kind"] == "item_tag":
        members = _pack_tag_members(str(new_selector["id"]))
        selector_implies = members is not None and old_selector["id"] in members
    else:
        selector_implies = False
    if not selector_implies:
        return False, f"old selector {old_selector} does not imply {new_selector}"
    for flag in ("only_from_crafting", "match_nbt", "weak_nbt_match"):
        if bool(new_payload.get(flag, False)) and not bool(predicate.get(flag, False)):
            return False, f"new proof strengthens {flag}"
    return True, "old item predicate statically implies the successor"


def ordered_mapping(mapping: dict[str, Any], baseline_alias: str, runtime_alias: str | None) -> dict[str, Any]:
    ordered: dict[str, Any] = {"old_alias": baseline_alias}
    if runtime_alias and runtime_alias != baseline_alias:
        ordered["old_runtime_alias"] = runtime_alias
    for key in ("old_engine_id", "new_alias", "new_engine_id", "policy", "reason", "evidence"):
        ordered[key] = mapping[key]
    for key, value in mapping.items():
        if key not in ordered and key not in {"old_alias", "old_runtime_alias"}:
            ordered[key] = value
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the verified mechanical rewrite")
    args = parser.parse_args()

    baseline = load_json(BASELINE_PATH)
    baseline_by_id = {str(item["engine_id"]): item for item in baseline["quests"]}
    if len(baseline_by_id) != baseline["expected_counts"]["quests"]:
        raise RuntimeError("QR0 baseline quest IDs are incomplete or duplicated")

    stable = load_json(STABLE_IDS_PATH)
    stable_alias_by_id = {
        str(engine_id): str(alias)
        for alias, engine_id in stable.get("ids", {}).items()
        if str(alias).startswith("if.")
    }

    chapters: dict[Path, dict[str, Any]] = {}
    quest_owner: dict[str, tuple[Path, dict[str, Any]]] = {}
    all_current_ids: set[str] = set()
    for path in sorted(SOURCE_DIR.glob("*.json")):
        document = load_json(path)
        if document.get("source_kind") != "quest_chapter":
            continue
        chapters[path] = document
        chapter = document["chapter"]
        all_current_ids.add(str(chapter["engine_id"]))
        all_current_ids.add(str(chapter["group"]["engine_id"]))
        for quest in document["quests"]:
            alias = str(quest["alias"])
            if alias in quest_owner:
                raise RuntimeError(f"Duplicate current quest alias {alias}")
            quest_owner[alias] = (path, quest)
            all_current_ids.add(str(quest["engine_id"]))
            all_current_ids.update(str(proof["engine_id"]) for proof in quest["proofs"])

    migration_docs: dict[Path, dict[str, Any]] = {
        path: load_json(path) for path in sorted(MIGRATION_DIR.glob("*.json"))
    }
    rows: list[tuple[Path, int, dict[str, Any]]] = []
    by_target: dict[str, list[tuple[Path, int, dict[str, Any]]]] = defaultdict(list)
    old_id_counts: Counter[str] = Counter()
    for path, document in migration_docs.items():
        for index, mapping in enumerate(document.get("mappings", [])):
            old_id = str(mapping["old_engine_id"])
            target = str(mapping["new_alias"])
            if old_id not in baseline_by_id:
                raise RuntimeError(f"{path.name}[{index}] references unknown QR0 quest ID {old_id}")
            if target not in quest_owner:
                raise RuntimeError(f"{path.name}[{index}] references unknown v2 target {target}")
            rows.append((path, index, mapping))
            by_target[target].append((path, index, mapping))
            old_id_counts[old_id] += 1

    duplicate_old_ids = sorted(engine_id for engine_id, count in old_id_counts.items() if count != 1)
    missing_old_ids = sorted(set(baseline_by_id) - set(old_id_counts))
    if duplicate_old_ids or missing_old_ids:
        raise RuntimeError(
            f"Migration coverage is not bijective: duplicate={duplicate_old_ids}, missing={missing_old_ids}"
        )

    legacy = legacy_children()
    if set(legacy) != set(baseline_by_id):
        missing = sorted(set(baseline_by_id) - set(legacy))
        extra = sorted(set(legacy) - set(baseline_by_id))
        raise RuntimeError(f"Legacy runtime differs from QR0 baseline: missing={missing}, extra={extra}")
    for old_id, row in baseline_by_id.items():
        contract = legacy[old_id]["task_contract"]
        if contract["type"] != row["task_type"] or contract["engine_id"] != "4" + old_id[1:]:
            raise RuntimeError(f"QR0 executable contract differs from the frozen baseline at {old_id}")

    proof_contract_targets: set[str] = set()
    proof_contract_failures: dict[str, str] = {}
    for _path, _index, mapping in rows:
        if mapping.get("policy") != "carry":
            continue
        old_id = str(mapping["old_engine_id"])
        target = str(mapping["new_alias"])
        safe, detail = _legacy_task_implies_current(
            legacy[old_id]["task_contract"],
            quest_owner[target][1],
        )
        if not safe:
            proof_contract_targets.add(target)
            proof_contract_failures[target] = detail

    merge_carry_targets = {
        target
        for target, target_rows in by_target.items()
        if len(target_rows) > 1 and any(mapping.get("policy") == "carry" for _, _, mapping in target_rows)
    }
    rotate_targets = proof_contract_targets | merge_carry_targets

    reserved = set(all_current_ids)
    reserved.update(str(value) for value in stable.get("ids", {}).values())
    previous_retired = load_json(RETIRED_IDS_PATH) if RETIRED_IDS_PATH.is_file() else {"retired": []}
    reserved.update(str(item["engine_id"]) for item in previous_retired.get("retired", []))

    changed_chapters: set[Path] = set()
    old_target_ids: dict[str, str] = {}
    for target in sorted(rotate_targets):
        path, quest = quest_owner[target]
        old_target_ids[target] = str(quest["engine_id"])
        quest["engine_id"] = deterministic_id("3", target, reserved)
        for proof in quest["proofs"]:
            proof["engine_id"] = deterministic_id("4", str(proof["alias"]), reserved)
        changed_chapters.add(path)

    # Preserve partial progress for the remaining semantically identical,
    # single-proof carry mappings whenever the historical task ID is free.
    proof_owner: dict[str, tuple[str, dict[str, Any]]] = {}
    for alias, (_path, quest) in quest_owner.items():
        for proof in quest["proofs"]:
            proof_owner[str(proof["engine_id"])] = (alias, proof)
    aligned_proofs = 0
    for _path, _index, mapping in rows:
        target = str(mapping["new_alias"])
        if target in rotate_targets or mapping.get("policy") != "carry":
            continue
        quest_path, quest = quest_owner[target]
        old_tasks = legacy[str(mapping["old_engine_id"])]["tasks"]
        if len(old_tasks) != 1 or len(quest["proofs"]) != 1:
            continue
        proof = quest["proofs"][0]
        old_task_id = old_tasks[0]
        current_id = str(proof["engine_id"])
        if current_id == old_task_id:
            continue
        owner = proof_owner.get(old_task_id)
        if owner is not None and owner[1] is not proof:
            raise RuntimeError(f"Cannot preserve task ID {old_task_id}; it belongs to {owner[0]}")
        proof_owner.pop(current_id, None)
        proof["engine_id"] = old_task_id
        proof_owner[old_task_id] = (target, proof)
        changed_chapters.add(quest_path)
        aligned_proofs += 1

    converted_mappings = 0
    alias_drift_rows = 0
    for path, document in migration_docs.items():
        repaired: list[dict[str, Any]] = []
        for mapping in document["mappings"]:
            old_id = str(mapping["old_engine_id"])
            target = str(mapping["new_alias"])
            baseline_alias = str(baseline_by_id[old_id]["alias"])
            runtime_alias = stable_alias_by_id.get(old_id)
            if runtime_alias and runtime_alias != baseline_alias:
                alias_drift_rows += 1

            if target in rotate_targets:
                if mapping.get("policy") == "carry":
                    converted_mappings += 1
                mapping["policy"] = "review"
                role = quest_owner[target][1].get("role")
                if role == "commissioning":
                    mapping["reason"] = (
                        "Старая ручная отметка не доказывает ввод системы в эксплуатацию. "
                        "Новый допуск нужно пройти по исполняемым проверкам."
                    )
                elif target in merge_carry_targets:
                    mapping["reason"] = (
                        "Несколько старых квестов сведены в одну новую цель. Выполнение одного из них "
                        "не доказывает весь объединённый результат, поэтому цель проверяется заново."
                    )
                else:
                    mapping["reason"] = (
                        "В Quest Source v2 изменился способ проверки результата. Старое завершение не "
                        "переносится автоматически, чтобы новый этап не был засчитан без доказательства."
                    )
                evidence = list(mapping.get("evidence", []))
                for item in (
                    "docs/registries/quest_rebuild_baseline.json",
                    "docs/QUEST_SYSTEM_REBUILD_PLAN.md#12-миграция-и-совместимость-миров",
                ):
                    if item not in evidence:
                        evidence.append(item)
                mapping["evidence"] = evidence

            mapping["new_engine_id"] = str(quest_owner[target][1]["engine_id"])
            repaired.append(ordered_mapping(mapping, baseline_alias, runtime_alias))
        document["mappings"] = repaired

    retired: dict[str, dict[str, Any]] = {}
    for path, document in migration_docs.items():
        relative_migration = path.relative_to(ROOT).as_posix()
        for mapping in document["mappings"]:
            if mapping["policy"] not in {"review", "reset"}:
                continue
            old_id = str(mapping["old_engine_id"])
            old_alias = str(mapping["old_alias"])
            successor = str(mapping["new_alias"])
            common = {
                "retired_in": "industrial_frontier:quest_source_v2",
                "migration_policy": str(mapping["policy"]),
                "successor_alias": successor,
                "evidence": [
                    "docs/registries/quest_rebuild_baseline.json",
                    relative_migration,
                    *legacy[old_id]["chapter"],
                ],
            }
            retired[old_id] = {
                "engine_id": old_id,
                "kind": "quest",
                "old_alias": old_alias,
                **common,
                "reason_ru": str(mapping["reason"]),
            }
            for kind, child_ids in (("task", legacy[old_id]["tasks"]), ("reward", legacy[old_id]["rewards"])):
                for child_id in child_ids:
                    retired[child_id] = {
                        "engine_id": child_id,
                        "kind": kind,
                        "old_alias": stable_alias_by_id.get(child_id, f"legacy.{kind}.{child_id.lower()}"),
                        "parent_old_engine_id": old_id,
                        "parent_old_alias": old_alias,
                        **common,
                        "reason_ru": (
                            "Этот ID принадлежал старому доказательству или награде квеста, который "
                            "в Quest Source v2 требует повторной проверки."
                        ),
                    }

    current_ids_after: set[str] = set()
    for document in chapters.values():
        chapter = document["chapter"]
        current_ids_after.update((str(chapter["engine_id"]), str(chapter["group"]["engine_id"])))
        for quest in document["quests"]:
            current_ids_after.add(str(quest["engine_id"]))
            current_ids_after.update(str(proof["engine_id"]) for proof in quest["proofs"])

    inactive_stable_ids = {str(value) for value in stable.get("ids", {}).values()} - current_ids_after
    uncovered_stable_ids = inactive_stable_ids - set(retired)
    unknown_retirements = sorted(uncovered_stable_ids - set(EXPLICIT_NON_QUEST_RETIREMENTS))
    if unknown_retirements:
        raise RuntimeError(
            "Stable engine IDs disappeared without a migration or explicit retirement: "
            f"{unknown_retirements}"
        )
    for engine_id in sorted(uncovered_stable_ids):
        decision = EXPLICIT_NON_QUEST_RETIREMENTS[engine_id]
        retired[engine_id] = {
            "engine_id": engine_id,
            "kind": decision["kind"],
            "old_alias": stable_alias_by_id.get(engine_id, f"legacy.id.{engine_id.lower()}"),
            "retired_in": "industrial_frontier:quest_source_v2",
            "migration_policy": "retire",
            "successor_alias": decision["successor_alias"],
            "reason_ru": decision["reason_ru"],
            "evidence": [
                "docs/registries/stable_ids.json",
                decision["evidence"],
            ],
        }

    collision = sorted(current_ids_after & set(retired))
    if collision:
        raise RuntimeError(f"Retired IDs are still used by Quest Source v2: {collision}")
    if len(current_ids_after) != sum(
        2 + len(document["quests"]) + sum(len(quest["proofs"]) for quest in document["quests"])
        for document in chapters.values()
    ) - (len(chapters) - len({document["chapter"]["group"]["engine_id"] for document in chapters.values()})):
        # The explicit owner validator remains authoritative; this catches only
        # accidental collisions introduced by this repair before writing.
        counts: Counter[str] = Counter()
        for document in chapters.values():
            chapter = document["chapter"]
            counts[str(chapter["engine_id"])] += 1
            counts[str(chapter["group"]["engine_id"])] += 1
            for quest in document["quests"]:
                counts[str(quest["engine_id"])] += 1
                counts.update(str(proof["engine_id"]) for proof in quest["proofs"])
        duplicates = sorted(engine_id for engine_id, count in counts.items() if count > 1 and not engine_id.startswith("1"))
        if duplicates:
            raise RuntimeError(f"Repair introduced duplicate IDs: {duplicates}")

    retired_document = {
        "$schema": "../../authoring/schemas/retired_ids.schema.json",
        "schema_version": 2,
        "namespace": "industrial_frontier",
        "retired": sorted(retired.values(), key=lambda item: item["engine_id"]),
    }
    proof_contract_document = {
        "$schema": "../../authoring/schemas/quest_qr0_proof_contracts.schema.json",
        "schema_version": 1,
        "registry_id": "industrial_frontier:quest_qr0_proof_contracts",
        "generated_from": [
            "docs/registries/quest_rebuild_baseline.json",
            "config/ftbquests/quests/chapters",
        ],
        "quest_count": len(baseline_by_id),
        "quests": [
            {
                "old_alias": str(baseline_by_id[old_id]["alias"]),
                "quest_engine_id": old_id,
                "task": legacy[old_id]["task_contract"],
            }
            for old_id in sorted(baseline_by_id)
        ],
    }

    changed_migrations = sum(
        dump_json(document) != path.read_text(encoding="utf-8-sig")
        for path, document in migration_docs.items()
    )
    print(f"QR0 mappings: {len(rows)}")
    print(f"Unsafe proof-contract carry targets rotated: {len(proof_contract_targets)}")
    for target, detail in sorted(proof_contract_failures.items()):
        print(f"  - {target}: {detail}")
    print(f"Merged carry targets rotated: {len(merge_carry_targets)}")
    print(f"Carry mappings converted to review: {converted_mappings}")
    print(f"Safe carry proof IDs aligned: {aligned_proofs}")
    print(f"Documented QR0 alias drifts: {alias_drift_rows}")
    print(f"Changed chapter documents: {len(changed_chapters)}")
    print(f"Changed migration documents: {changed_migrations}")
    print(f"Retired IDs: {len(retired)}")
    print(f"Frozen QR0 proof contracts: {len(proof_contract_document['quests'])}")
    print(f"Mode: {'apply' if args.apply else 'preview'}")

    if not args.apply:
        return 0

    for path in sorted(changed_chapters):
        path.write_text(dump_json(chapters[path]), encoding="utf-8", newline="\n")
    for path, document in migration_docs.items():
        path.write_text(dump_json(document), encoding="utf-8", newline="\n")
    RETIRED_IDS_PATH.write_text(dump_json(retired_document), encoding="utf-8", newline="\n")
    PROOF_CONTRACTS_PATH.write_text(dump_json(proof_contract_document), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
