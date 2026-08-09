#!/usr/bin/env python3
"""Read-only audit of a user-supplied Minecraft launch log.

The script never starts Minecraft.  It separates pack-owned regressions from
known third-party noise so a visually successful launch cannot hide a broken
questbook, KubeJS script or resource overlay.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path


PACK_BLOCKERS: dict[str, re.Pattern[str]] = {
    "invalid_quest_icon": re.compile(r"Invalid icon item stack", re.IGNORECASE),
    "kubejs_script_error": re.compile(
        r"(?:Loaded \d+/\d+ KubeJS .* with [1-9]\d* errors|"
        r"\[CHAT\] KubeJS errors found \[[1-9]\d*\])",
        re.IGNORECASE,
    ),
    "rhino_redeclaration": re.compile(r"(?:already been declared|redeclaration)", re.IGNORECASE),
    "resource_json_error": re.compile(
        r"(?:JsonParseException|MalformedJsonException|Couldn't parse .*\.json)",
        re.IGNORECASE,
    ),
    "datapack_reload_failure": re.compile(
        r"(?:Failed to reload data packs|Failed to load datapacks|Errors in currently selected datapacks)",
        re.IGNORECASE,
    ),
    "owned_missing_resource": re.compile(
        r"(?:Failed to load model|Missing textures in model) "
        r"(?:hbm_ntm_rebirth|car|supplementaries|farmersdelight|brewinandchewin):",
        re.IGNORECASE,
    ),
    "jer_plugin_failure": re.compile(
        r"Caught an error from mod plugin:.*jeresources", re.IGNORECASE
    ),
}

KNOWN_EXTERNAL: dict[str, re.Pattern[str]] = {
    "f11_zero_sized_glfw_transition": re.compile(r"Invalid window size 0x0", re.IGNORECASE),
    "lightmans_currency_model_baker": re.compile(
        r"(?:SimpleUnbakedGeometry|VariantModelBakery)", re.IGNORECASE
    ),
    "gcyr_zero_eut_recipe": re.compile(r"EUt can't be explicitly set to 0, id: gcyr:"),
    "pneumaticcraft_jei_without_world": re.compile(
        r"PneumaticCraftRecipeType\[pneumaticcraft:fuel_quality\].*no world",
        re.IGNORECASE,
    ),
    "third_party_invalid_pack_path": re.compile(r"Invalid path in pack:", re.IGNORECASE),
}

EVIDENCE: dict[str, re.Pattern[str]] = {
    "client_reached_title_or_world": re.compile(
        r"(?:OpenAL initialized|Preparing level|Joining World|Loaded \d+ advancements)",
        re.IGNORECASE,
    ),
    "world_saved_cleanly": re.compile(
        r"(?:Saving chunks for level|ThreadedAnvilChunkStorage.*All dimensions are saved)",
        re.IGNORECASE,
    ),
    "server_stopped_cleanly": re.compile(r"Stopping server", re.IGNORECASE),
}


def read_log(path: Path) -> list[str]:
    if path.suffix.lower() == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            return handle.readlines()
    return path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)


def scan(lines: list[str], patterns: dict[str, re.Pattern[str]]) -> tuple[Counter[str], dict[str, str]]:
    counts: Counter[str] = Counter()
    first: dict[str, str] = {}
    for line in lines:
        for key, pattern in patterns.items():
            if pattern.search(line):
                counts[key] += 1
                first.setdefault(key, line.strip())
    return counts, first


def main() -> int:
    parser = argparse.ArgumentParser(description="Статический аудит пользовательского launch-лога")
    parser.add_argument("log", type=Path, help="latest.log либо архив .log.gz")
    parser.add_argument("--json", dest="json_path", type=Path, help="необязательный JSON-отчёт")
    args = parser.parse_args()

    if not args.log.is_file():
        parser.error(f"Файл не найден: {args.log}")

    lines = read_log(args.log)
    blockers, blocker_first = scan(lines, PACK_BLOCKERS)
    external, external_first = scan(lines, KNOWN_EXTERNAL)
    evidence, evidence_first = scan(lines, EVIDENCE)
    report = {
        "schema_version": 1,
        "log": str(args.log.resolve()),
        "line_count": len(lines),
        "minecraft_launched_by_script": False,
        "pack_blockers": dict(blockers),
        "known_external_signatures": dict(external),
        "lifecycle_evidence": dict(evidence),
        "first_match": {
            "pack_blockers": blocker_first,
            "known_external_signatures": external_first,
            "lifecycle_evidence": evidence_first,
        },
        "status": "FAIL" if blockers else "PASS",
    }

    print(f"[LAUNCH-AUDIT] log={args.log} lines={len(lines)}")
    for key in PACK_BLOCKERS:
        print(f"[LAUNCH-AUDIT][{'FAIL' if blockers[key] else 'PASS'}] {key}={blockers[key]}")
    for key in KNOWN_EXTERNAL:
        if external[key]:
            print(f"[LAUNCH-AUDIT][EXTERNAL] {key}={external[key]}")
    for key in EVIDENCE:
        print(f"[LAUNCH-AUDIT][EVIDENCE] {key}={evidence[key]}")
    print(f"[LAUNCH-AUDIT][SUMMARY] status={report['status']} game_started_by_tool=false")

    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
