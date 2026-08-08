#!/usr/bin/env python3
"""Static P0-P9 progression and grind-budget audit.

The audit consumes the current M2 registry fields directly. It never starts
Minecraft, Forge, a server, or a launcher. A non-zero exit status means that
at least one blocker has no registry-backed explanation. Known GATED, EXPLAIN,
or REWORK decisions remain visible in the report but do not fail the command.

Examples:
    python tools/audit_progression.py
    python tools/audit_progression.py --json-report build/audit_progression.json
    python tools/audit_progression.py --json-report -
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
import zipfile
from collections import defaultdict, deque
from typing import Any, Iterable, Iterator


ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_DIR = ROOT / "docs" / "registries"
INPUT_FILES = {
    "progression_graph": REGISTRY_DIR / "m2_progression_graph.json",
    "substance_passports": REGISTRY_DIR / "m2_substance_passports.json",
    "grind_budget": REGISTRY_DIR / "m2_grind_budget.json",
}
EXPECTED_EPOCHS = set(range(10))
EPOCH_RE = re.compile(r"^industrial_frontier:epoch/p([0-9])$")
SUBSTANCE_PREFIX = "industrial_frontier:substance/"


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def input_metadata(path: pathlib.Path) -> dict[str, Any]:
    relative = str(path.relative_to(ROOT)).replace("\\", "/")
    if not path.is_file():
        return {"path": relative, "sha256": None, "bytes": None}
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": relative,
        "sha256": digest.hexdigest().upper(),
        "bytes": path.stat().st_size,
    }


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def as_record_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def epoch_from_ref(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    match = EPOCH_RE.fullmatch(value)
    return int(match.group(1)) if match else None


def walk_records(value: Any, path: str = "$") -> Iterator[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk_records(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_records(child, f"{path}[{index}]")


class Audit:
    def __init__(self) -> None:
        self.findings: list[dict[str, Any]] = []
        self.checks: dict[str, Any] = {}

    def add(
        self,
        severity: str,
        code: str,
        category: str,
        subject: str,
        message: str,
        *,
        explained: bool = False,
        evidence_refs: Iterable[str] | None = None,
    ) -> None:
        finding: dict[str, Any] = {
            "severity": severity,
            "code": code,
            "category": category,
            "subject": subject,
            "message": message,
            "explained": explained,
        }
        refs = sorted({ref for ref in (evidence_refs or []) if is_nonempty_string(ref)})
        if refs:
            finding["evidence_refs"] = refs
        self.findings.append(finding)

    def blocker(self, code: str, category: str, subject: str, message: str) -> None:
        self.add("BLOCKER", code, category, subject, message)

    def warning(
        self,
        code: str,
        category: str,
        subject: str,
        message: str,
        *,
        explained: bool = False,
        evidence_refs: Iterable[str] | None = None,
    ) -> None:
        self.add(
            "WARNING",
            code,
            category,
            subject,
            message,
            explained=explained,
            evidence_refs=evidence_refs,
        )

    def info(self, code: str, category: str, subject: str, message: str) -> None:
        self.add("INFO", code, category, subject, message)

    @property
    def blocker_count(self) -> int:
        return sum(item["severity"] == "BLOCKER" for item in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(item["severity"] == "WARNING" for item in self.findings)

    @property
    def info_count(self) -> int:
        return sum(item["severity"] == "INFO" for item in self.findings)


def duplicate_ids(
    audit: Audit,
    records: Iterable[dict[str, Any]],
    id_field: str,
    category: str,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        identifier = record.get(id_field)
        subject = str(identifier or f"{category}[{index}]")
        if not is_nonempty_string(identifier):
            audit.blocker("MISSING_ID", category, subject, f"Missing non-empty {id_field}.")
            continue
        if identifier in result:
            audit.blocker("DUPLICATE_ID", category, identifier, f"Duplicate {id_field}.")
            continue
        result[identifier] = record
    return result


def record_has_explanation(record: dict[str, Any]) -> bool:
    evidence = record.get("evidence_refs")
    gate = record.get("gate") or record.get("gate_refs")
    decision = record.get("decision_ru") or record.get("exit_contract")
    has_evidence = isinstance(evidence, list) and any(is_nonempty_string(item) for item in evidence)
    has_gate = is_nonempty_string(gate) or (
        isinstance(gate, list) and any(is_nonempty_string(item) for item in gate)
    )
    return has_evidence and has_gate and bool(decision)


def safe_root_path(reference: str) -> tuple[pathlib.Path | None, str | None]:
    base = reference.split("#", 1)[0].replace("\\", "/")
    archive_member: str | None = None
    if "!/" in base:
        base, archive_member = base.split("!/", 1)
    candidate = (ROOT / base).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None, archive_member
    return candidate, archive_member


def validate_physical_evidence(
    audit: Audit,
    reference: str,
    subject: str,
    *,
    code_prefix: str,
) -> bool:
    candidate, archive_member = safe_root_path(reference)
    if candidate is None:
        audit.blocker(
            f"{code_prefix}_OUTSIDE_ROOT",
            "evidence",
            subject,
            f"Evidence path escapes the instance root: {reference}",
        )
        return False
    if not candidate.exists():
        audit.blocker(
            f"{code_prefix}_PATH_MISSING",
            "evidence",
            subject,
            f"Evidence path does not exist: {reference}",
        )
        return False
    if archive_member is None:
        return True
    try:
        with zipfile.ZipFile(candidate) as archive:
            normalized = archive_member.strip("/")
            names = archive.namelist()
            if normalized in names or any(name.startswith(normalized + "/") for name in names):
                return True
    except (OSError, zipfile.BadZipFile) as exc:
        audit.blocker(
            f"{code_prefix}_ARCHIVE_INVALID",
            "evidence",
            subject,
            f"Cannot inspect evidence archive {candidate.relative_to(ROOT)}: {exc}",
        )
        return False
    audit.blocker(
        f"{code_prefix}_ARCHIVE_MEMBER_MISSING",
        "evidence",
        subject,
        f"Archive evidence member does not exist: {reference}",
    )
    return False


def audit_evidence(
    audit: Audit,
    documents: dict[str, dict[str, Any]],
) -> None:
    evidence_records: list[dict[str, Any]] = []
    gate_records: list[dict[str, Any]] = []
    for document in documents.values():
        evidence_records.extend(as_record_list(document.get("source_evidence")))
        gate_records.extend(as_record_list(document.get("gates")))

    evidence_by_id = duplicate_ids(audit, evidence_records, "evidence_id", "evidence_definition")
    gate_by_id = duplicate_ids(audit, gate_records, "gate_id", "gate_definition")
    physical_checks = 0
    physical_ok = 0

    for evidence_id, record in evidence_by_id.items():
        path = record.get("path")
        if not is_nonempty_string(path):
            audit.blocker(
                "EVIDENCE_DEFINITION_PATH_MISSING",
                "evidence",
                evidence_id,
                "Evidence definition has no physical path.",
            )
            continue
        physical_checks += 1
        if validate_physical_evidence(
            audit, path, evidence_id, code_prefix="EVIDENCE_DEFINITION"
        ):
            physical_ok += 1

    referenced_evidence: set[str] = set()
    referenced_gates: set[str] = set()
    direct_paths: set[str] = set()
    for document_name, document in documents.items():
        for record_path, record in walk_records(document):
            subject = f"{document_name}:{record_path}"
            evidence_refs = record.get("evidence_refs")
            if evidence_refs is not None and not isinstance(evidence_refs, list):
                audit.blocker(
                    "EVIDENCE_REFS_NOT_ARRAY",
                    "evidence",
                    subject,
                    "evidence_refs must be an array.",
                )
            for reference in evidence_refs if isinstance(evidence_refs, list) else []:
                if not is_nonempty_string(reference):
                    audit.blocker(
                        "EMPTY_EVIDENCE_REF", "evidence", subject, "Empty evidence reference."
                    )
                elif reference.startswith("industrial_frontier:evidence/"):
                    referenced_evidence.add(reference)
                    if reference not in evidence_by_id:
                        audit.blocker(
                            "UNRESOLVED_EVIDENCE_ID",
                            "evidence",
                            subject,
                            f"Unknown evidence ID: {reference}",
                        )
                elif reference.startswith("industrial_frontier:"):
                    audit.blocker(
                        "INVALID_EVIDENCE_ID",
                        "evidence",
                        subject,
                        f"Evidence ID has the wrong namespace/type: {reference}",
                    )
                else:
                    direct_paths.add(reference)

            gate_refs = record.get("gate_refs")
            if gate_refs is not None and not isinstance(gate_refs, list):
                audit.blocker(
                    "GATE_REFS_NOT_ARRAY", "evidence", subject, "gate_refs must be an array."
                )
            for reference in gate_refs if isinstance(gate_refs, list) else []:
                if not is_nonempty_string(reference):
                    audit.blocker("EMPTY_GATE_REF", "evidence", subject, "Empty gate reference.")
                else:
                    referenced_gates.add(reference)
                    if reference not in gate_by_id:
                        audit.blocker(
                            "UNRESOLVED_GATE_ID",
                            "evidence",
                            subject,
                            f"Unknown gate ID: {reference}",
                        )

    for reference in sorted(direct_paths):
        physical_checks += 1
        if validate_physical_evidence(
            audit, reference, reference, code_prefix="DIRECT_EVIDENCE"
        ):
            physical_ok += 1

    for gate_id, gate in gate_by_id.items():
        if gate.get("blocks_runtime_claim") and not gate.get("evidence_refs"):
            audit.blocker(
                "BLOCKING_GATE_WITHOUT_EVIDENCE",
                "evidence",
                gate_id,
                "A runtime-blocking gate must cite evidence.",
            )

    audit.checks["evidence"] = {
        "definitions": len(evidence_by_id),
        "referenced_definition_ids": len(referenced_evidence),
        "gate_definitions": len(gate_by_id),
        "referenced_gate_ids": len(referenced_gates),
        "physical_paths_checked": physical_checks,
        "physical_paths_valid": physical_ok,
    }


def audit_epochs(
    audit: Audit,
    graph: dict[str, Any],
    chain_by_id: dict[str, dict[str, Any]],
    component_by_id: dict[str, dict[str, Any]],
) -> None:
    nodes = as_record_list(graph.get("nodes"))
    node_by_id = duplicate_ids(audit, nodes, "node_id", "epoch_node")
    epoch_to_node: dict[int, dict[str, Any]] = {}
    for node_id, node in node_by_id.items():
        ref_epoch = epoch_from_ref(node_id)
        epoch = node.get("epoch")
        if not isinstance(epoch, int) or epoch not in EXPECTED_EPOCHS:
            audit.blocker("INVALID_NODE_EPOCH", "epoch", node_id, f"Invalid epoch value: {epoch!r}")
            continue
        if ref_epoch != epoch:
            audit.blocker(
                "NODE_ID_EPOCH_MISMATCH",
                "epoch",
                node_id,
                f"node_id encodes P{ref_epoch}, record says P{epoch}.",
            )
        if epoch in epoch_to_node:
            audit.blocker("DUPLICATE_EPOCH", "epoch", node_id, f"P{epoch} has two nodes.")
        epoch_to_node[epoch] = node

    missing_epochs = sorted(EXPECTED_EPOCHS - set(epoch_to_node))
    extra_epochs = sorted(set(epoch_to_node) - EXPECTED_EPOCHS)
    if missing_epochs:
        audit.blocker(
            "MISSING_EPOCHS", "epoch", "P0-P9", f"Missing epochs: {missing_epochs}"
        )
    if extra_epochs:
        audit.blocker("EXTRA_EPOCHS", "epoch", "P0-P9", f"Unexpected epochs: {extra_epochs}")

    for epoch, node in sorted(epoch_to_node.items()):
        subject = node.get("node_id", f"P{epoch}")
        for field, index in (
            ("grind_chain_refs", chain_by_id),
            ("critical_component_refs", component_by_id),
        ):
            refs = node.get(field)
            if not isinstance(refs, list) or not refs:
                audit.blocker(
                    "EMPTY_EPOCH_BINDING", "epoch", subject, f"{field} must be non-empty."
                )
                continue
            for reference in refs:
                target = index.get(reference)
                if target is None:
                    audit.blocker(
                        "UNRESOLVED_EPOCH_BINDING",
                        "epoch",
                        subject,
                        f"{field} references unknown ID: {reference}",
                    )
                elif target.get("epoch") != epoch:
                    audit.blocker(
                        "CROSS_EPOCH_BINDING",
                        "epoch",
                        subject,
                        f"{reference} belongs to P{target.get('epoch')}, not P{epoch}.",
                    )

    expected_pairs = {(epoch, epoch + 1) for epoch in range(9)}
    seen_pairs: set[tuple[int, int]] = set()
    adjacency: dict[int, set[int]] = defaultdict(set)
    for edge in as_record_list(graph.get("edges")):
        edge_id = str(edge.get("edge_id") or "epoch_edge")
        source = epoch_from_ref(edge.get("from"))
        target = epoch_from_ref(edge.get("to"))
        if source is None or target is None:
            audit.blocker(
                "INVALID_EPOCH_EDGE", "topology", edge_id, "Epoch edge endpoints are invalid."
            )
            continue
        pair = (source, target)
        if pair in seen_pairs:
            audit.blocker("DUPLICATE_EPOCH_EDGE", "topology", edge_id, f"Duplicate P{source}->P{target} edge.")
        seen_pairs.add(pair)
        adjacency[source].add(target)
        delta = target - source
        if delta > 1:
            audit.blocker(
                "EPOCH_JUMP", "topology", edge_id, f"Progression jumps from P{source} to P{target}."
            )
        elif delta <= 0:
            audit.blocker(
                "EPOCH_BACK_EDGE", "topology", edge_id, f"Progression goes from P{source} to P{target}."
            )

    for source, target in sorted(expected_pairs - seen_pairs):
        audit.blocker(
            "MISSING_SEQUENTIAL_EDGE",
            "topology",
            f"P{source}->P{target}",
            "Required sequential epoch edge is missing.",
        )

    reachable = {0}
    queue: deque[int] = deque([0])
    while queue:
        source = queue.popleft()
        for target in adjacency.get(source, set()):
            if target not in reachable:
                reachable.add(target)
                queue.append(target)
    unreachable_epochs = sorted(EXPECTED_EPOCHS - reachable)
    if unreachable_epochs:
        audit.blocker(
            "UNREACHABLE_EPOCHS",
            "topology",
            "P0-P9",
            f"Epochs unreachable from P0: {unreachable_epochs}",
        )

    audit.checks["epochs"] = {
        "expected": 10,
        "present": len(epoch_to_node),
        "covered": sorted(epoch_to_node),
        "sequential_edges_expected": 9,
        "sequential_edges_present": len(expected_pairs & seen_pairs),
        "reachable_from_p0": sorted(reachable),
        "jumps": sum(
            item["code"] == "EPOCH_JUMP" for item in audit.findings
        ),
    }


def metric_band(value: float, green: float, hard: float) -> str:
    if value <= green:
        return "GREEN"
    if value <= hard:
        return "EXPLAIN"
    return "HARD_EXCEEDED"


def audit_grind(
    audit: Audit,
    grind: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    limits = grind.get("limits")
    required_limits = {
        "training_batches_max",
        "manual_repeats_green_max",
        "manual_repeats_hard_max",
        "transfers_green_max",
        "transfers_hard_max",
        "passive_minutes_green_max",
        "passive_minutes_hard_max",
    }
    if not isinstance(limits, dict):
        audit.blocker("LIMITS_MISSING", "grind", "limits", "limits must be an object.")
        limits = {}
    for key in sorted(required_limits):
        if not isinstance(limits.get(key), (int, float)):
            audit.blocker("LIMIT_MISSING", "grind", key, "Required numeric limit is missing.")
    for green_key, hard_key in (
        ("manual_repeats_green_max", "manual_repeats_hard_max"),
        ("transfers_green_max", "transfers_hard_max"),
        ("passive_minutes_green_max", "passive_minutes_hard_max"),
    ):
        if isinstance(limits.get(green_key), (int, float)) and isinstance(
            limits.get(hard_key), (int, float)
        ) and limits[green_key] > limits[hard_key]:
            audit.blocker(
                "INVERTED_LIMITS",
                "grind",
                f"{green_key}/{hard_key}",
                "Green threshold is greater than the hard threshold.",
            )

    components = as_record_list(grind.get("critical_components"))
    chains = as_record_list(grind.get("chains"))
    component_by_id = duplicate_ids(audit, components, "component_id", "critical_component")
    chain_by_id = duplicate_ids(audit, chains, "chain_id", "grind_chain")

    bands = defaultdict(int)
    result_counts = defaultdict(int)
    epoch_counts = defaultdict(int)
    hard_exceedances = 0
    explained_exceedances = 0

    metric_specs = (
        ("repeated_manual_operations", "manual_repeats_green_max", "manual_repeats_hard_max"),
        ("manual_transfers", "transfers_green_max", "transfers_hard_max"),
        ("passive_minutes", "passive_minutes_green_max", "passive_minutes_hard_max"),
    )

    for chain_id, chain in chain_by_id.items():
        epoch = chain.get("epoch")
        if not isinstance(epoch, int) or epoch not in EXPECTED_EPOCHS:
            audit.blocker("INVALID_CHAIN_EPOCH", "grind", chain_id, f"Invalid epoch: {epoch!r}")
        else:
            epoch_counts[epoch] += 1

        result = str(chain.get("result") or "")
        result_counts[result or "MISSING"] += 1
        evidence_refs = chain.get("evidence_refs") if isinstance(chain.get("evidence_refs"), list) else []
        explained = record_has_explanation(chain)
        metric_results: dict[str, str] = {}

        training = chain.get("training_batches")
        training_max = limits.get("training_batches_max")
        if not isinstance(training, (int, float)):
            audit.blocker("INVALID_GRIND_METRIC", "grind", chain_id, "training_batches is not numeric.")
        elif isinstance(training_max, (int, float)) and training > training_max:
            hard_exceedances += 1
            if result in {"REWORK", "GATED"} and explained:
                explained_exceedances += 1
                audit.warning(
                    "EXPLAINED_TRAINING_EXCEEDANCE",
                    "grind",
                    chain_id,
                    f"training_batches={training} exceeds max={training_max}; registry marks {result}.",
                    explained=True,
                    evidence_refs=evidence_refs,
                )
            else:
                audit.blocker(
                    "UNEXPLAINED_TRAINING_EXCEEDANCE",
                    "grind",
                    chain_id,
                    f"training_batches={training} exceeds max={training_max}.",
                )

        for field, green_key, hard_key in metric_specs:
            value = chain.get(field)
            green = limits.get(green_key)
            hard = limits.get(hard_key)
            if not isinstance(value, (int, float)) or not isinstance(green, (int, float)) or not isinstance(hard, (int, float)):
                audit.blocker(
                    "INVALID_GRIND_METRIC", "grind", chain_id, f"{field} or its limits are not numeric."
                )
                continue
            band = metric_band(float(value), float(green), float(hard))
            metric_results[field] = band
            bands[band] += 1
            if band == "HARD_EXCEEDED":
                hard_exceedances += 1
                if result in {"REWORK", "GATED"} and explained:
                    explained_exceedances += 1
                    audit.warning(
                        "EXPLAINED_HARD_EXCEEDANCE",
                        "grind",
                        chain_id,
                        f"{field}={value} exceeds hard limit={hard}; registry marks {result}.",
                        explained=True,
                        evidence_refs=evidence_refs,
                    )
                else:
                    audit.blocker(
                        "UNEXPLAINED_HARD_EXCEEDANCE",
                        "grind",
                        chain_id,
                        f"{field}={value} exceeds hard limit={hard}.",
                    )

        worst = (
            "HARD_EXCEEDED"
            if "HARD_EXCEEDED" in metric_results.values()
            else "EXPLAIN"
            if "EXPLAIN" in metric_results.values()
            else "GREEN"
        )
        if result == "GREEN" and worst != "GREEN":
            audit.blocker(
                "GREEN_RESULT_EXCEEDS_GREEN_LIMIT",
                "grind",
                chain_id,
                f"result=GREEN but measured band is {worst}: {metric_results}",
            )
        elif result == "EXPLAIN" and not explained:
            audit.blocker(
                "EXPLAIN_RESULT_WITHOUT_EVIDENCE",
                "grind",
                chain_id,
                "result=EXPLAIN lacks decision, gate, or evidence.",
            )
        elif result == "EXPLAIN" and worst == "GREEN":
            audit.warning(
                "CONSERVATIVE_EXPLAIN_RESULT",
                "grind",
                chain_id,
                "result=EXPLAIN although all measured metrics are inside green limits; a non-numeric design risk is documented.",
                explained=True,
                evidence_refs=evidence_refs,
            )
        elif result == "REWORK" and not explained:
            audit.blocker(
                "REWORK_RESULT_WITHOUT_EVIDENCE",
                "grind",
                chain_id,
                "result=REWORK lacks decision, gate, or evidence.",
            )
        elif result == "GATED":
            if chain.get("status") != "GATED_NOT_INSTALLED" or not explained:
                audit.blocker(
                    "INVALID_GATED_RESULT",
                    "grind",
                    chain_id,
                    "result=GATED requires GATED_NOT_INSTALLED plus decision, gate, and evidence.",
                )
            else:
                audit.warning(
                    "EXPLAINED_GATED_CHAIN",
                    "grind",
                    chain_id,
                    "Chain is intentionally gated and is not an unexplained blocker.",
                    explained=True,
                    evidence_refs=evidence_refs,
                )
        elif result not in {"GREEN", "EXPLAIN", "REWORK", "GATED"}:
            audit.blocker("INVALID_GRIND_RESULT", "grind", chain_id, f"Unknown result: {result!r}")

        automation = chain.get("automation_epoch")
        mass_demand = chain.get("mass_demand_epoch")
        if mass_demand is not None and automation is None:
            audit.blocker(
                "MASS_DEMAND_WITHOUT_AUTOMATION",
                "grind",
                chain_id,
                "mass_demand_epoch is set while automation_epoch is null.",
            )
        elif isinstance(mass_demand, int) and isinstance(automation, int) and mass_demand < automation:
            audit.blocker(
                "MASS_DEMAND_BEFORE_AUTOMATION",
                "grind",
                chain_id,
                f"Mass demand P{mass_demand} precedes automation P{automation}.",
            )

        rng = chain.get("rng_percent")
        alternative = chain.get("deterministic_alternative_ru")
        if isinstance(rng, (int, float)) and rng < 100 and not is_nonempty_string(alternative):
            audit.blocker(
                "RNG_WITHOUT_DETERMINISTIC_ALTERNATIVE",
                "grind",
                chain_id,
                f"rng_percent={rng} but no deterministic alternative is documented.",
            )

        refs = chain.get("critical_component_refs")
        if not isinstance(refs, list) or not refs:
            audit.blocker(
                "CHAIN_WITHOUT_COMPONENT", "grind", chain_id, "critical_component_refs must be non-empty."
            )
        for reference in refs if isinstance(refs, list) else []:
            component = component_by_id.get(reference)
            if component is None:
                audit.blocker(
                    "UNRESOLVED_CHAIN_COMPONENT",
                    "grind",
                    chain_id,
                    f"Unknown critical component: {reference}",
                )
            elif component.get("budget_ref") != chain_id:
                audit.blocker(
                    "COMPONENT_BUDGET_MISMATCH",
                    "grind",
                    chain_id,
                    f"{reference} points to {component.get('budget_ref')!r}.",
                )

    for component_id, component in component_by_id.items():
        chain_id = component.get("budget_ref")
        chain = chain_by_id.get(chain_id)
        if chain is None:
            audit.blocker(
                "UNRESOLVED_COMPONENT_BUDGET",
                "grind",
                component_id,
                f"Unknown budget_ref: {chain_id!r}",
            )
        elif component_id not in chain.get("critical_component_refs", []):
            audit.blocker(
                "BUDGET_COMPONENT_BACKREF_MISSING",
                "grind",
                component_id,
                f"{chain_id} does not reference this component.",
            )
        elif (
            component.get("status") == "GATED_NOT_INSTALLED"
            and chain.get("status") == "ACTIVE_M2"
        ):
            audit.warning(
                "ACTIVE_BUDGET_FOR_GATED_COMPONENT",
                "grind",
                component_id,
                "The measurement card is active, but the runtime component remains gated by its typed dependencies.",
                explained=True,
                evidence_refs=component.get("evidence_refs", []),
            )
        if not component.get("required_refs"):
            audit.blocker(
                "COMPONENT_WITHOUT_REQUIREMENTS",
                "grind",
                component_id,
                "required_refs must be non-empty.",
            )

    missing_chain_epochs = sorted(EXPECTED_EPOCHS - set(epoch_counts))
    if missing_chain_epochs:
        audit.blocker(
            "GRIND_EPOCH_COVERAGE_GAP",
            "grind",
            "P0-P9",
            f"No grind chain for epochs: {missing_chain_epochs}",
        )

    audit.checks["grind"] = {
        "limits": limits,
        "chains": len(chain_by_id),
        "critical_components": len(component_by_id),
        "chains_per_epoch": {f"P{epoch}": epoch_counts[epoch] for epoch in range(10)},
        "result_counts": dict(sorted(result_counts.items())),
        "metric_band_counts": dict(sorted(bands.items())),
        "hard_exceedances": hard_exceedances,
        "explained_hard_exceedances": explained_exceedances,
    }
    return chain_by_id, component_by_id


def dependency_cycle(nodes: set[str], adjacency: dict[str, set[str]]) -> list[str]:
    indegree = {node: 0 for node in nodes}
    for source in nodes:
        for target in adjacency.get(source, set()):
            indegree[target] = indegree.get(target, 0) + 1
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        source = queue.popleft()
        visited += 1
        for target in adjacency.get(source, set()):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited == len(indegree):
        return []
    return sorted(node for node, degree in indegree.items() if degree > 0)


def is_substance_explained(record: dict[str, Any] | None) -> bool:
    if not record:
        return False
    gate_refs = record.get("gate_refs")
    evidence_refs = record.get("evidence_refs")
    route_documented = bool(
        record.get("exit_contract")
        or record.get("process_refs")
        or record.get("source_strategy_ru")
        or record.get("process_route_ru")
    )
    # ACTIVE_INSTALLED passports can still rely on an external/world source or
    # an installed vendor process that is not represented as a production edge.
    # That is a visible registry debt, but it is not *unexplained* when a route,
    # evidence and a gate are all present. The audit reports it as a warning.
    return (
        isinstance(gate_refs, list)
        and bool(gate_refs)
        and isinstance(evidence_refs, list)
        and bool(evidence_refs)
        and route_documented
    )


def audit_graph_and_substances(
    audit: Audit,
    graph: dict[str, Any],
    passports: dict[str, Any],
    component_by_id: dict[str, dict[str, Any]],
) -> None:
    substances = as_record_list(passports.get("passports")) + as_record_list(
        passports.get("planned_substances")
    )
    substance_by_id = duplicate_ids(audit, substances, "substance_id", "substance")

    dependency_edges = as_record_list(graph.get("dependency_edges"))
    production_edges = as_record_list(graph.get("production_edges"))
    recycle_edges = as_record_list(graph.get("bounded_recycle_edges"))
    dependency_by_id = duplicate_ids(audit, dependency_edges, "dependency_id", "dependency_edge")
    production_by_id = duplicate_ids(audit, production_edges, "production_edge_id", "production_edge")
    recycle_by_id = duplicate_ids(audit, recycle_edges, "recycle_edge_id", "recycle_edge")

    dependency_nodes: set[str] = set()
    dependency_adjacency: dict[str, set[str]] = defaultdict(set)
    component_edge_requirements: dict[str, set[str]] = defaultdict(set)
    for edge_id, edge in dependency_by_id.items():
        source = edge.get("from_ref")
        target = edge.get("to_ref")
        if not is_nonempty_string(source) or not is_nonempty_string(target):
            audit.blocker(
                "INVALID_DEPENDENCY_ENDPOINT",
                "topology",
                edge_id,
                "Dependency edge has an empty endpoint.",
            )
            continue
        dependency_nodes.update((source, target))
        dependency_adjacency[source].add(target)
        if edge.get("relation") == "COMPONENT_REQUIRES":
            component_edge_requirements[target].add(source)

    cycle_nodes = dependency_cycle(dependency_nodes, dependency_adjacency)
    if cycle_nodes:
        audit.blocker(
            "DEPENDENCY_CYCLE",
            "topology",
            "dependency_edges",
            f"Unbounded dependency cycle touches {len(cycle_nodes)} refs; sample: {cycle_nodes[:8]}",
        )

    for component_id, component in component_by_id.items():
        declared = set(component.get("required_refs") or [])
        bound = component_edge_requirements.get(component_id, set())
        for reference in sorted(declared - bound):
            audit.blocker(
                "COMPONENT_REQUIREMENT_EDGE_MISSING",
                "topology",
                component_id,
                f"No COMPONENT_REQUIRES edge for {reference}.",
            )
        for reference in sorted(bound - declared):
            audit.blocker(
                "UNDECLARED_COMPONENT_REQUIREMENT_EDGE",
                "topology",
                component_id,
                f"Graph requires {reference}, but the grind component does not declare it.",
            )

    produced: set[str] = set()
    consumed: set[str] = set()
    required: set[str] = set()
    stage_inputs: dict[str, dict[str | None, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))
    stage_outputs: dict[str, set[str]] = defaultdict(set)
    production_epoch_jumps = 0

    for edge_id, edge in production_by_id.items():
        relation = edge.get("relation")
        source = edge.get("from_ref")
        target = edge.get("to_ref")
        direction = edge.get("direction")
        earliest = edge.get("earliest_epoch")
        automation = edge.get("automation_epoch")
        status = edge.get("status")
        substance_ref: str | None = None

        if isinstance(earliest, int) and isinstance(automation, int) and automation < earliest:
            audit.blocker(
                "AUTOMATION_BEFORE_ROUTE",
                "topology",
                edge_id,
                f"automation_epoch=P{automation} precedes earliest_epoch=P{earliest}.",
            )

        if relation == "PROCESS_CONSUMES":
            if not (isinstance(source, str) and source.startswith(SUBSTANCE_PREFIX)) or direction != "SUBSTANCE_TO_STAGE":
                audit.blocker(
                    "INVALID_CONSUME_EDGE_DIRECTION",
                    "topology",
                    edge_id,
                    "PROCESS_CONSUMES must point substance -> stage.",
                )
                continue
            substance_ref = source
            consumed.add(source)
            if edge.get("optionality") == "REQUIRED":
                group = edge.get("input_group_ref")
                logic = edge.get("input_group_logic") or "ALL_OF"
                stage_inputs[str(target)][group].append((source, str(logic)))
        elif relation in {"PROCESS_PRODUCES", "PROCESS_EMITS_WASTE"}:
            if not (isinstance(target, str) and target.startswith(SUBSTANCE_PREFIX)) or direction != "STAGE_TO_SUBSTANCE":
                audit.blocker(
                    "INVALID_PRODUCE_EDGE_DIRECTION",
                    "topology",
                    edge_id,
                    f"{relation} must point stage -> substance.",
                )
                continue
            substance_ref = target
            produced.add(target)
            stage_outputs[str(source)].add(target)
        else:
            audit.blocker(
                "UNKNOWN_PRODUCTION_RELATION",
                "topology",
                edge_id,
                f"Unknown relation: {relation!r}",
            )
            continue

        substance = substance_by_id.get(substance_ref)
        if substance is None:
            audit.blocker(
                "UNKNOWN_PRODUCTION_SUBSTANCE",
                "topology",
                edge_id,
                f"Production edge references unknown substance: {substance_ref}",
            )
        elif isinstance(earliest, int) and isinstance(substance.get("first_epoch"), int) and substance["first_epoch"] > earliest:
            production_epoch_jumps += 1
            message = (
                f"Edge is available at P{earliest}, before passport first_epoch=P{substance['first_epoch']} "
                f"for {substance_ref}."
            )
            if status == "GATED_BINDING" and is_substance_explained(substance):
                audit.warning(
                    "EXPLAINED_PRODUCTION_EPOCH_MISMATCH",
                    "topology",
                    edge_id,
                    message,
                    explained=True,
                    evidence_refs=substance.get("evidence_refs", []),
                )
            else:
                audit.blocker("PRODUCTION_EPOCH_MISMATCH", "topology", edge_id, message)

    for recycle_id, edge in recycle_by_id.items():
        substance_ref = edge.get("substance_ref")
        if substance_ref not in substance_by_id:
            audit.blocker(
                "UNKNOWN_RECYCLE_SUBSTANCE",
                "topology",
                recycle_id,
                f"Unknown recycle substance: {substance_ref!r}",
            )
        return_ratio = edge.get("max_return_ratio")
        makeup_ratio = edge.get("minimum_makeup_ratio")
        if not isinstance(return_ratio, (int, float)) or not 0 < return_ratio <= 1:
            audit.blocker(
                "INVALID_RECYCLE_RETURN_RATIO", "topology", recycle_id, f"max_return_ratio={return_ratio!r}"
            )
        if not isinstance(makeup_ratio, (int, float)) or not 0 <= makeup_ratio <= 1:
            audit.blocker(
                "INVALID_RECYCLE_MAKEUP_RATIO", "topology", recycle_id, f"minimum_makeup_ratio={makeup_ratio!r}"
            )
        if isinstance(return_ratio, (int, float)) and isinstance(makeup_ratio, (int, float)) and return_ratio + makeup_ratio < 1:
            audit.warning(
                "RECYCLE_LOSS_NOT_FULLY_ACCOUNTED",
                "topology",
                recycle_id,
                f"return+makeup={return_ratio + makeup_ratio:.3f}; remaining loss must stay explicit in recipes.",
                explained=True,
                evidence_refs=edge.get("evidence_refs", []),
            )

    for node in as_record_list(graph.get("nodes")):
        node_epoch = node.get("epoch")
        for substance_ref in node.get("required_substance_refs") or []:
            required.add(substance_ref)
            substance = substance_by_id.get(substance_ref)
            if substance is None:
                audit.blocker(
                    "UNKNOWN_REQUIRED_SUBSTANCE",
                    "reachability",
                    str(node.get("node_id")),
                    f"Unknown required substance: {substance_ref}",
                )
                continue
            first_epoch = substance.get("first_epoch")
            if isinstance(node_epoch, int) and isinstance(first_epoch, int):
                delta = first_epoch - node_epoch
                if delta > 1:
                    audit.blocker(
                        "SUBSTANCE_EPOCH_JUMP",
                        "topology",
                        str(node.get("node_id")),
                        f"{substance_ref} starts at P{first_epoch}, more than one boundary after P{node_epoch}.",
                    )
                elif delta == 1:
                    audit.info(
                        "BOUNDARY_PROOF_SUBSTANCE",
                        "topology",
                        str(node.get("node_id")),
                        f"{substance_ref} is a P{first_epoch} boundary proof referenced by P{node_epoch}.",
                    )

    for component in component_by_id.values():
        for reference in component.get("required_refs") or []:
            if isinstance(reference, str) and reference.startswith(SUBSTANCE_PREFIX):
                required.add(reference)

    world_sources = {
        substance_id
        for substance_id, record in substance_by_id.items()
        if is_nonempty_string(record.get("world_origin_decision_ref"))
    }
    domain_used = {
        substance_id
        for substance_id, record in substance_by_id.items()
        if record.get("domain_consumers") or record.get("consumer_domain_refs")
    }
    used = consumed | required | domain_used

    missing_producers: list[str] = []
    explained_unreachable: list[str] = []
    for substance_ref in sorted((consumed | required) - produced - world_sources):
        record = substance_by_id.get(substance_ref)
        if is_substance_explained(record):
            explained_unreachable.append(substance_ref)
            audit.warning(
                "EXPLAINED_UNREACHABLE_SUBSTANCE",
                "reachability",
                substance_ref,
                "No production/world-source edge is declared; the passport route, evidence and gate explain the registry debt.",
                explained=True,
                evidence_refs=record.get("evidence_refs", []) if record else [],
            )
        else:
            missing_producers.append(substance_ref)
            audit.blocker(
                "UNEXPLAINED_UNREACHABLE_SUBSTANCE",
                "reachability",
                substance_ref,
                "Required/consumed substance has neither a production edge nor a world-origin decision.",
            )

    dead_ends: list[str] = []
    explained_dead_ends: list[str] = []
    for substance_ref in sorted(produced - used):
        record = substance_by_id.get(substance_ref)
        if is_substance_explained(record):
            explained_dead_ends.append(substance_ref)
            audit.warning(
                "EXPLAINED_DEAD_END_SUBSTANCE",
                "reachability",
                substance_ref,
                "Produced substance has no declared consumer yet; its passport route, evidence and gate explain the unfinished route.",
                explained=True,
                evidence_refs=record.get("evidence_refs", []) if record else [],
            )
        else:
            dead_ends.append(substance_ref)
            audit.blocker(
                "UNEXPLAINED_DEAD_END_SUBSTANCE",
                "reachability",
                substance_ref,
                "Produced substance has no production input, epoch requirement, component requirement, or domain consumer.",
            )

    # Fixed-point reachability respects ALL_OF and ONE_OF input groups.
    reachable_substances = set(world_sources)
    reachable_stages: set[str] = set()
    changed = True
    while changed:
        changed = False
        all_stages = set(stage_inputs) | set(stage_outputs)
        for stage in all_stages - reachable_stages:
            groups = stage_inputs.get(stage, {})
            group_results: list[bool] = []
            for entries in groups.values():
                logics = {logic for _, logic in entries}
                logic = "ONE_OF" if logics == {"ONE_OF"} else "ALL_OF"
                refs = [reference for reference, _ in entries]
                group_results.append(
                    any(reference in reachable_substances for reference in refs)
                    if logic == "ONE_OF"
                    else all(reference in reachable_substances for reference in refs)
                )
            if all(group_results):
                reachable_stages.add(stage)
                changed = True
                for output in stage_outputs.get(stage, set()):
                    if output not in reachable_substances:
                        reachable_substances.add(output)
        # A stage that became reachable above may add outputs even when it was
        # already known from a previous iteration.
        for stage in reachable_stages:
            for output in stage_outputs.get(stage, set()):
                if output not in reachable_substances:
                    reachable_substances.add(output)
                    changed = True

    path_unreachable = sorted(required - reachable_substances)
    unexplained_path_unreachable: list[str] = []
    explained_path_unreachable: list[str] = []
    for substance_ref in path_unreachable:
        record = substance_by_id.get(substance_ref)
        if is_substance_explained(record):
            explained_path_unreachable.append(substance_ref)
            # Already reported above when no producer exists; avoid duplicate noise.
            if substance_ref not in explained_unreachable:
                audit.warning(
                    "EXPLAINED_PATH_UNREACHABLE",
                    "reachability",
                    substance_ref,
                    "A declared route exists but its required input chain is gated.",
                    explained=True,
                    evidence_refs=record.get("evidence_refs", []) if record else [],
                )
        else:
            unexplained_path_unreachable.append(substance_ref)
            if substance_ref not in missing_producers:
                audit.blocker(
                    "UNEXPLAINED_PATH_UNREACHABLE",
                    "reachability",
                    substance_ref,
                    "Declared production route cannot be reached from any world-origin source.",
                )

    audit.checks["topology"] = {
        "dependency_edges": len(dependency_by_id),
        "production_edges": len(production_by_id),
        "bounded_recycle_edges": len(recycle_by_id),
        "dependency_cycle_refs": cycle_nodes,
        "production_epoch_mismatches": production_epoch_jumps,
    }
    audit.checks["reachability"] = {
        "substances": len(substance_by_id),
        "world_sources": len(world_sources),
        "produced": len(produced),
        "consumed": len(consumed),
        "required_by_epochs_or_components": len(required),
        "reachable_by_fixed_point": len(reachable_substances),
        "unexplained_missing_producer": missing_producers,
        "explained_missing_producer": explained_unreachable,
        "unexplained_dead_ends": dead_ends,
        "explained_dead_ends": explained_dead_ends,
        "unexplained_path_unreachable": unexplained_path_unreachable,
        "explained_path_unreachable": explained_path_unreachable,
    }


def build_report() -> tuple[Audit, dict[str, Any]]:
    audit = Audit()
    documents: dict[str, dict[str, Any]] = {}
    for name, path in INPUT_FILES.items():
        try:
            value = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            audit.blocker("INPUT_LOAD_FAILED", "input", name, f"Cannot read {path}: {exc}")
            value = {}
        if not isinstance(value, dict):
            audit.blocker("INPUT_NOT_OBJECT", "input", name, f"{path} must contain a JSON object.")
            value = {}
        documents[name] = value

    grind = documents["grind_budget"]
    graph = documents["progression_graph"]
    passports = documents["substance_passports"]

    chain_by_id, component_by_id = audit_grind(audit, grind)
    audit_epochs(audit, graph, chain_by_id, component_by_id)
    audit_graph_and_substances(audit, graph, passports, component_by_id)
    audit_evidence(audit, documents)

    audit.findings.sort(
        key=lambda item: (
            {"BLOCKER": 0, "WARNING": 1, "INFO": 2}.get(item["severity"], 9),
            item["category"],
            item["code"],
            item["subject"],
        )
    )
    report = {
        "audit_id": "industrial_frontier:m10/progression_grind_static_audit",
        "audit_version": 1,
        "generated_at_utc": utc_timestamp(),
        "scope": "Static registry audit only; Minecraft/Forge was not launched.",
        "inputs": {name: input_metadata(path) for name, path in INPUT_FILES.items()},
        "exit_policy": "Non-zero only when summary.unexplained_blockers > 0.",
        "summary": {
            "unexplained_blockers": audit.blocker_count,
            "warnings": audit.warning_count,
            "information": audit.info_count,
            "status": "FAIL_UNEXPLAINED_BLOCKERS" if audit.blocker_count else "PASS_STATIC",
            "minecraft_launched": False,
        },
        "checks": audit.checks,
        "findings": audit.findings,
    }
    return audit, report


def print_console(report: dict[str, Any]) -> None:
    summary = report["summary"]
    checks = report["checks"]
    epochs = checks.get("epochs", {})
    grind = checks.get("grind", {})
    reachability = checks.get("reachability", {})
    evidence = checks.get("evidence", {})
    print("=== Recast M10: static progression and grind audit ===")
    print(
        f"P0-P9: {epochs.get('present', 0)}/10 nodes; "
        f"sequential edges {epochs.get('sequential_edges_present', 0)}/9"
    )
    print(
        f"Grind: {grind.get('chains', 0)} chains, {grind.get('critical_components', 0)} components; "
        f"results {json.dumps(grind.get('result_counts', {}), ensure_ascii=False, sort_keys=True)}"
    )
    print(
        f"Reachability: produced={reachability.get('produced', 0)}, "
        f"consumed={reachability.get('consumed', 0)}, "
        f"unexplained_missing={len(reachability.get('unexplained_missing_producer', []))}, "
        f"unexplained_dead_ends={len(reachability.get('unexplained_dead_ends', []))}"
    )
    print(
        f"Evidence: {evidence.get('physical_paths_valid', 0)}/"
        f"{evidence.get('physical_paths_checked', 0)} physical paths valid"
    )
    print(
        f"Findings: blockers={summary['unexplained_blockers']} "
        f"warnings={summary['warnings']} info={summary['information']}"
    )
    visible_findings = [
        finding for finding in report["findings"] if finding["severity"] != "INFO"
    ]
    for finding in visible_findings[:20]:
        suffix = " [explained]" if finding.get("explained") else ""
        print(
            f"{finding['severity']}: {finding['code']} {finding['subject']}: "
            f"{finding['message']}{suffix}"
        )
    if len(visible_findings) > 20:
        print(
            f"... {len(visible_findings) - 20} additional warning/blocker records are available "
            "in the JSON report."
        )
    print("Minecraft/Forge was not launched.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-report",
        metavar="PATH",
        help="Write the complete machine-readable report to PATH; use '-' for stdout.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the human-readable summary (JSON output is unaffected).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    audit, report = build_report()

    if args.json_report == "-":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if not args.quiet:
            print_console(report)
        if args.json_report:
            output = pathlib.Path(args.json_report)
            if not output.is_absolute():
                output = pathlib.Path.cwd() / output
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            if not args.quiet:
                print(f"JSON report: {output}")

    return 1 if audit.blocker_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
