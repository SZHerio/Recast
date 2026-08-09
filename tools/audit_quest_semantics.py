#!/usr/bin/env python3
"""Write a complete static semantic audit for Quest Source v2.

The report contains one row for every quest, dependency edge, and proof.  It
does not start Minecraft and never writes to ``config/ftbquests/quests``.
Runtime is read only to make a stale deployed book visible before promotion.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
import sys
from typing import Any

from validate_questbook_v2 import (
    DEFAULT_SCHEMA,
    DEFAULT_SOURCE,
    EPOCH_INDEX,
    ROOT,
    load_project,
    validate_project,
    validate_staging,
)


DEFAULT_BUILD = pathlib.Path("build/questbook_v2")
DEFAULT_RUNTIME = pathlib.Path("config/ftbquests/quests")
DEFAULT_OUT = DEFAULT_BUILD / "reports/quest_semantic_audit_full.json"

NBT_FAMILY_IDS = {
    "tacz:ammo",
    "domum_ornamentum:plain",
    "immersiveengineering:coresample",
}
KNOWN_UNREGISTERED_ITEM_IDS = {
    "ad_astra:tier_1_rocket",
    "pneumaticcraft:electric_compressor",
    "pneumaticcraft:pneumatic_generator",
}
OPTIONAL_EXAMPLE_QUESTS = {
    "if.quest.v2.p0.food_crop",
    "if.quest.v2.p0.food_hunt",
    "if.quest.v2.p0.food_root",
}
MATERIAL_FORM_RE = re.compile(
    r"(?:^|_)(?:raw|purified|crushed|ingot|plate|dust|gem|ore|stone|wax|bitumen|petcoke)(?:_|$)"
)
CHOICE_CLAIM_RE = re.compile(
    r"(?:из\s+списка\s+задачи|любой\s+подходящ(?:ий|ая|ее)\s+"
    r"(?:минерал|руда|слиток|пластина|доска|бревно|брёвно))",
    re.IGNORECASE,
)


def resolve(root: pathlib.Path, value: str, default: pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(value) if value else default
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def read_snbt_ids(directory: pathlib.Path) -> dict[str, Any]:
    chapter_dir = directory / "chapters"
    files = sorted(chapter_dir.glob("*.snbt")) if chapter_dir.is_dir() else []
    chapters: set[str] = set()
    quests: set[str] = set()
    proofs: set[str] = set()
    filenames: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        filenames.append(path.name)
        chapters.update(re.findall(r'^\tid: "(2[0-9A-F]{15})"$', text, re.MULTILINE))
        quests.update(re.findall(r'^\t+id: "(3[0-9A-F]{15})"$', text, re.MULTILINE))
        proofs.update(re.findall(r'^\t+id: "(4[0-9A-F]{15})"$', text, re.MULTILINE))
    return {
        "directory": directory.as_posix(),
        "chapter_files": len(files),
        "chapter_ids": len(chapters),
        "quest_ids": len(quests),
        "proof_ids": len(proofs),
        "filenames": filenames,
        "chapter_id_set": chapters,
        "quest_id_set": quests,
        "proof_id_set": proofs,
    }


def exact_decision(quest: dict[str, Any], item_id: str) -> tuple[str, str]:
    alias = str(quest.get("alias", ""))
    role = str(quest.get("role", ""))
    requirement = str(quest.get("requirement", ""))
    if alias in OPTIONAL_EXAMPLE_QUESTS:
        return (
            "EXACT_OPTIONAL_EXAMPLE",
            "Точный продукт относится только к необязательному учебному маршруту; обязательный пищевой узел принимает общий набор рационов напрямую.",
        )
    if item_id in NBT_FAMILY_IDS:
        return (
            "EXACT_SHARED_REGISTRY_FAMILY",
            "Один реестровый ID представляет варианты предмета; задача не включает точное NBT-сопоставление и принимает семейство внутри этого ID.",
        )
    item_path = item_id.split(":", 1)[-1]
    if role in {"machine", "operation", "automation", "diagnostics", "commissioning"}:
        return (
            "EXACT_MACHINE_OR_CONTROL_ARTIFACT",
            "Проверяется названная машина, прибор или контрольный образец, а не взаимозаменяемая материальная категория.",
        )
    if MATERIAL_FORM_RE.search(item_path):
        return (
            "EXACT_CANONICAL_PROCESS_OUTPUT",
            "Проверяется конкретный названный продукт технологического процесса; текст не обещает выбор эквивалентных форм или минералов.",
        )
    if requirement == "optional":
        return (
            "EXACT_OPTIONAL_SPECIALISATION",
            "Необязательная специализация проверяет один явно названный предмет и не блокирует техническую магистраль.",
        )
    return (
        "EXACT_NAMED_ITEM",
        "Условие и русский текст называют один конкретный предмет; равнозначный набор игроку не обещан.",
    )


def selector_for(proof: dict[str, Any]) -> tuple[str, str | None, int | None]:
    if proof.get("type") != "item":
        return str(proof.get("type", "unknown")), None, None
    if isinstance(proof.get("item_tag"), dict):
        payload = proof["item_tag"]
        return "item_tag", str(payload.get("id", "")), int(payload.get("count", 1))
    payload = proof.get("item", {})
    return "item", str(payload.get("id", "")), int(payload.get("count", 1))


def edge_class(source: dict[str, Any], target: dict[str, Any]) -> str:
    source_epoch = str(source.get("epoch", ""))
    target_epoch = str(target.get("epoch", ""))
    if source_epoch == target_epoch:
        return "SAME_EPOCH_CAUSAL_STEP"
    if source_epoch == "ONBOARDING" and target_epoch == "P0":
        return "ONBOARDING_TO_P0_HANDOFF"
    if source.get("role") == "commissioning" and source_epoch in EPOCH_INDEX and target_epoch in EPOCH_INDEX:
        return "COMMISSIONING_EPOCH_HANDOFF"
    if target_epoch in {"SYSTEMS", "REFERENCE"}:
        return "OPTIONAL_OR_REFERENCE_UNLOCK"
    return "CROSS_CAMPAIGN_CAUSAL_LINK"


def serialise_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in snapshot.items() if not key.endswith("_set")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit every Quest Source v2 quest, proof, and dependency edge.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--build", default=str(DEFAULT_BUILD))
    parser.add_argument("--runtime", default=str(DEFAULT_RUNTIME))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--require-runtime-sync", action="store_true")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    source = resolve(root, args.source, DEFAULT_SOURCE)
    schema = resolve(root, args.schema, DEFAULT_SCHEMA)
    build = resolve(root, args.build, DEFAULT_BUILD)
    runtime = resolve(root, args.runtime, DEFAULT_RUNTIME)
    out = resolve(root, args.out, DEFAULT_OUT)

    project, load_issues = load_project(root, source, schema)
    semantic_issues, graph = validate_project(project, release=True)
    staging_issues = validate_staging(project, graph, build)
    all_issues = [*load_issues, *semantic_issues, *staging_issues]
    errors = [dataclasses.asdict(issue) for issue in all_issues if issue.level == "ERROR"]
    warnings = [dataclasses.asdict(issue) for issue in all_issues if issue.level == "WARN"]

    topological_index = {alias: index for index, alias in enumerate(graph.get("topological_order", []))}
    commissioning = graph.get("commissioning_by_epoch", {})
    mandatory = graph.get("mandatory_dependencies", {})
    quest_rows: list[dict[str, Any]] = []
    proof_rows: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    choice_conflicts: list[str] = []

    for alias, quest in sorted(graph.get("quests", {}).items()):
        epoch = str(quest.get("epoch", ""))
        required_before_commissioning = False
        commission_alias = commissioning.get(epoch)
        if quest.get("requirement") == "required" and commission_alias and alias != commission_alias:
            required_before_commissioning = alias in mandatory.get(commission_alias, [])
        quest_rows.append({
            "alias": alias,
            "chapter": graph.get("chapter_for_quest", {}).get(alias),
            "epoch": epoch,
            "requirement": quest.get("requirement"),
            "role": quest.get("role"),
            "dependency_mode": graph.get("dependency_modes", {}).get(alias),
            "dependency_count": len(graph.get("dependencies", {}).get(alias, [])),
            "proof_count": len(quest.get("proofs", [])),
            "topological_index": topological_index.get(alias),
            "required_before_epoch_commissioning": required_before_commissioning,
            "status": "PASS_STATIC",
        })

        for proof in quest.get("proofs", []):
            selector_kind, selector_id, count = selector_for(proof)
            if selector_kind == "item":
                decision, reason_ru = exact_decision(quest, str(selector_id))
                selector_verdict = "EXACT_ITEM_JUSTIFIED"
                proof_copy = " ".join(str(value) for value in proof.get("text_ru", {}).values())
                if CHOICE_CLAIM_RE.search(proof_copy):
                    choice_conflicts.append(str(proof.get("alias")))
                    decision = "ERROR_EXACT_ITEM_PROMISES_EQUIVALENCE"
                    selector_verdict = "MUST_USE_TAG_OR_ONE_OF"
                    reason_ru = "Текст обещает выбор, но исполняемая задача принимает один реестровый ID."
            elif selector_kind == "item_tag":
                decision = "TAG_REQUIRED_EQUIVALENCE"
                selector_verdict = "TAG_OR_ONE_OF_IMPLEMENTED"
                reason_ru = "Исполняемая задача принимает проверенный набор равнозначных предметов через pack-owned или подтверждённый общий тег."
            else:
                decision = "NON_ITEM_EXECUTABLE_PROOF"
                selector_verdict = "NOT_AN_ITEM_SELECTOR"
                reason_ru = "Условие проверяет действие, состояние мира, жидкость, энергию или этап и не использует предметную эквивалентность."
            proof_rows.append({
                "quest": alias,
                "proof": proof.get("alias"),
                "type": proof.get("type"),
                "selector_kind": selector_kind,
                "selector_id": selector_id,
                "count": count,
                "decision": decision,
                "selector_verdict": selector_verdict,
                "reason_ru": reason_ru,
                "objective_ru": proof.get("text_ru", {}).get("objective"),
                "status": "PASS_STATIC" if not decision.startswith("ERROR_") else "ERROR",
            })

        for edge in quest.get("dependency", {}).get("edges", []):
            source_alias = str(edge.get("quest", ""))
            source_quest = graph.get("quests", {}).get(source_alias, {})
            causal_ok = (
                source_alias in graph.get("quests", {})
                and topological_index.get(source_alias, -1) < topological_index.get(alias, -1)
                and bool(str(edge.get("reason", "")).strip())
                and bool(edge.get("evidence"))
            )
            edge_rows.append({
                "source": source_alias,
                "target": alias,
                "mode_at_target": quest.get("dependency", {}).get("mode"),
                "source_epoch": source_quest.get("epoch"),
                "target_epoch": quest.get("epoch"),
                "source_role": source_quest.get("role"),
                "target_role": quest.get("role"),
                "causal_class": edge_class(source_quest, quest),
                "causal_verdict": "CAUSAL_AND_REACHABLE" if causal_ok else "INVALID_EDGE",
                "reason_ru": edge.get("reason"),
                "evidence": edge.get("evidence"),
                "topological_order_valid": topological_index.get(source_alias, -1) < topological_index.get(alias, -1),
                "status": "PASS_STATIC" if causal_ok else "ERROR",
            })

    staging_snapshot = read_snbt_ids(build)
    runtime_snapshot = read_snbt_ids(runtime)
    source_quest_ids = {str(quest.get("engine_id")) for quest in graph.get("quests", {}).values()}
    source_proof_ids = {str(proof.get("engine_id")) for proof in graph.get("proofs", {}).values()}
    source_chapter_ids = {str(chapter.get("engine_id")) for chapter in graph.get("chapters", {}).values()}
    runtime_sync = (
        runtime_snapshot["chapter_id_set"] == source_chapter_ids
        and runtime_snapshot["quest_id_set"] == source_quest_ids
        and runtime_snapshot["proof_id_set"] == source_proof_ids
    )
    staging_sync = (
        staging_snapshot["chapter_id_set"] == source_chapter_ids
        and staging_snapshot["quest_id_set"] == source_quest_ids
        and staging_snapshot["proof_id_set"] == source_proof_ids
    )

    if choice_conflicts:
        errors.append({
            "level": "ERROR",
            "code": "QSA-EXACT-CHOICE-CONFLICT",
            "path": "proofs",
            "message": f"Exact-item tasks promise an equivalence choice: {sorted(choice_conflicts)}",
        })
    bad_edges = [row for row in edge_rows if row["status"] != "PASS_STATIC"]
    if bad_edges:
        errors.append({
            "level": "ERROR",
            "code": "QSA-EDGE-CAUSALITY",
            "path": "edges",
            "message": f"{len(bad_edges)} dependency edges failed existence/order/reason/evidence checks.",
        })

    unregistered_item_refs: list[dict[str, str]] = []
    for alias, quest in graph.get("quests", {}).items():
        candidates = [str(quest.get("icon", ""))]
        candidates.extend(
            str(ref.get("id", ""))
            for ref in quest.get("content_refs", [])
            if ref.get("kind") in {"item", "block"}
        )
        for proof in quest.get("proofs", []):
            if isinstance(proof.get("item"), dict):
                candidates.append(str(proof["item"].get("id", "")))
        for item_id in sorted(KNOWN_UNREGISTERED_ITEM_IDS.intersection(candidates)):
            unregistered_item_refs.append({"quest": alias, "item_id": item_id})
    if unregistered_item_refs:
        errors.append({
            "level": "ERROR",
            "code": "QSA-UNREGISTERED-ITEM-ID",
            "path": "quests",
            "message": f"Quest source contains known unregistered item references: {unregistered_item_refs}",
        })
    if not staging_sync:
        errors.append({
            "level": "ERROR",
            "code": "QSA-STAGING-DRIFT",
            "path": build.as_posix(),
            "message": "Staging IDs differ from Quest Source v2.",
        })

    decision_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    for row in proof_rows:
        decision_counts[row["decision"]] = decision_counts.get(row["decision"], 0) + 1
        type_counts[str(row["type"])] = type_counts.get(str(row["type"]), 0) + 1

    result = {
        "schema_version": 1,
        "status": "ERROR" if errors else "PASS_STATIC_RUNTIME_SYNC" if runtime_sync else "PASS_STATIC_RUNTIME_STALE",
        "scope_ru": "Полный статический проход всех квестов, доказательств и рёбер Quest Source v2 без запуска Minecraft.",
        "summary": {
            "chapters": len(graph.get("chapters", {})),
            "quests": len(quest_rows),
            "proofs": len(proof_rows),
            "dependency_edges": len(edge_rows),
            "exact_item_proofs": sum(row["selector_kind"] == "item" for row in proof_rows),
            "tag_item_proofs": sum(row["selector_kind"] == "item_tag" for row in proof_rows),
            "non_item_proofs": sum(row["selector_kind"] not in {"item", "item_tag"} for row in proof_rows),
            "choice_claim_conflicts": len(choice_conflicts),
            "failed_edges": len(bad_edges),
            "known_unregistered_item_refs": len(unregistered_item_refs),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "proof_type_counts": dict(sorted(type_counts.items())),
        "proof_decision_counts": dict(sorted(decision_counts.items())),
        "selector_verdict_counts": dict(sorted(
            (verdict, sum(row["selector_verdict"] == verdict for row in proof_rows))
            for verdict in {row["selector_verdict"] for row in proof_rows}
        )),
        "known_unregistered_item_refs": unregistered_item_refs,
        "runtime_comparison": {
            "source": {
                "chapters": len(source_chapter_ids),
                "quests": len(source_quest_ids),
                "proofs": len(source_proof_ids),
            },
            "staging": serialise_snapshot(staging_snapshot),
            "runtime": serialise_snapshot(runtime_snapshot),
            "staging_matches_source_ids": staging_sync,
            "runtime_matches_source_ids": runtime_sync,
            "runtime_missing_source_chapter_ids": sorted(source_chapter_ids - runtime_snapshot["chapter_id_set"]),
            "runtime_missing_source_quest_ids": sorted(source_quest_ids - runtime_snapshot["quest_id_set"]),
            "runtime_missing_source_proof_ids": sorted(source_proof_ids - runtime_snapshot["proof_id_set"]),
            "runtime_only_historical_chapter_ids": sorted(runtime_snapshot["chapter_id_set"] - source_chapter_ids),
            "runtime_only_historical_quest_ids": sorted(runtime_snapshot["quest_id_set"] - source_quest_ids),
            "runtime_only_historical_proof_ids": sorted(runtime_snapshot["proof_id_set"] - source_proof_ids),
        },
        "errors": errors,
        "warnings": warnings,
        "quests": quest_rows,
        "dependency_edges": edge_rows,
        "proofs": proof_rows,
    }

    try:
        out.relative_to(build)
    except ValueError:
        parser.error(f"--out must stay inside staging build directory: {build}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    print(
        f"quest semantic audit: {result['status']} | "
        f"quests={len(quest_rows)} proofs={len(proof_rows)} edges={len(edge_rows)} "
        f"exact={result['summary']['exact_item_proofs']} tags={result['summary']['tag_item_proofs']}"
    )
    print(f"report: {out}")
    print("Minecraft was not launched. Runtime quests were read only and were not modified.")
    if errors:
        return 2
    if args.require_runtime_sync and not runtime_sync:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
