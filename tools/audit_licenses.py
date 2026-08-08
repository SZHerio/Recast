#!/usr/bin/env python3
"""Create a static license/provenance inventory for installed mod JARs.

This tool never loads Forge or mod classes.  It reads archive metadata only and
therefore is safe to run as part of release preflight while gameplay testing is
owned by the player.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LICENSE_NAMES = re.compile(
    r"(^|/)(licen[cs]e|copying|notice|credits)([._-].*)?$", re.IGNORECASE
)
TOML_LICENSE = re.compile(
    r"(?mi)^\s*license\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|([^#\r\n]+))"
)
AMBIGUOUS_LICENSE = re.compile(
    r"(?i)^(insert\s+licen[cs]e\s+here|see\s+.+\s+for\s+details|unknown|tbd)$"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json_from_zip(archive: zipfile.ZipFile, name: str) -> Any | None:
    try:
        return json.loads(archive.read(name).decode("utf-8-sig"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def read_text_from_zip(archive: zipfile.ZipFile, name: str) -> str | None:
    try:
        return archive.read(name).decode("utf-8-sig", errors="replace")
    except KeyError:
        return None


def normalize_license(value: Any) -> list[str]:
    if isinstance(value, str):
        value = value.strip()
        return [value] if value else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                result.append(item.strip())
            elif isinstance(item, dict):
                name = item.get("name") or item.get("id")
                if isinstance(name, str) and name.strip():
                    result.append(name.strip())
        return result
    if isinstance(value, dict):
        name = value.get("name") or value.get("id")
        if isinstance(name, str) and name.strip():
            return [name.strip()]
    return []


def inspect_jar(path: Path) -> dict[str, Any]:
    declarations: list[dict[str, str]] = []
    license_files: list[str] = []
    metadata_files: list[str] = []
    errors: list[str] = []

    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            license_files = sorted(
                name for name in names if LICENSE_NAMES.search(name.rstrip("/"))
            )

            mods_toml = read_text_from_zip(archive, "META-INF/mods.toml")
            if mods_toml is not None:
                metadata_files.append("META-INF/mods.toml")
                match = TOML_LICENSE.search(mods_toml)
                if match:
                    value = next(
                        (part.strip() for part in match.groups() if part and part.strip()),
                        "",
                    )
                    if value:
                        declarations.append(
                            {"source": "META-INF/mods.toml", "value": value}
                        )

            fabric = read_json_from_zip(archive, "fabric.mod.json")
            if isinstance(fabric, dict):
                metadata_files.append("fabric.mod.json")
                for value in normalize_license(fabric.get("license")):
                    declarations.append({"source": "fabric.mod.json", "value": value})

            quilt = read_json_from_zip(archive, "quilt.mod.json")
            if isinstance(quilt, dict):
                metadata_files.append("quilt.mod.json")
                loader = quilt.get("quilt_loader")
                metadata = loader.get("metadata", {}) if isinstance(loader, dict) else {}
                for value in normalize_license(
                    metadata.get("license") if isinstance(metadata, dict) else None
                ):
                    declarations.append({"source": "quilt.mod.json", "value": value})
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(str(exc))

    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for declaration in declarations:
        key = (declaration["source"], declaration["value"])
        if key not in seen:
            seen.add(key)
            unique.append(declaration)

    if errors:
        status = "ERROR"
    elif unique:
        status = "DECLARED"
    elif license_files:
        status = "LICENSE_FILE_ONLY"
    else:
        status = "UNDECLARED"

    review_reasons: list[str] = []
    ambiguous_values = sorted(
        {
            declaration["value"]
            for declaration in unique
            if AMBIGUOUS_LICENSE.search(declaration["value"].strip())
        }
    )
    if ambiguous_values:
        review_reasons.append(
            "Ambiguous or placeholder declaration: " + "; ".join(ambiguous_values)
        )
    if status in {"UNDECLARED", "ERROR"}:
        review_reasons.append("No reliable machine-readable license declaration")

    return {
        "file_name": path.name,
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "status": status,
        "declarations": unique,
        "license_files": license_files,
        "metadata_files": sorted(set(metadata_files)),
        "manual_review_required": bool(review_reasons),
        "review_reasons": review_reasons,
        "errors": errors,
    }


def load_source_registry(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    path = root / "docs" / "registries" / "curseforge_sources.json"
    if not path.exists():
        return {}, {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    files = {
        item["file_name"]: item
        for item in data.get("files", [])
        if isinstance(item, dict) and isinstance(item.get("file_name"), str)
    }
    exceptions = {
        item["file_name"]: item
        for item in data.get("owner_exceptions", [])
        if isinstance(item, dict) and isinstance(item.get("file_name"), str)
    }
    return files, exceptions


def load_instance_sources(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "minecraftinstance.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    result: dict[str, dict[str, Any]] = {}
    for addon in data.get("installedAddons", []):
        if not isinstance(addon, dict):
            continue
        installed = addon.get("installedFile")
        file_name = addon.get("fileNameOnDisk")
        if not isinstance(installed, dict) or not isinstance(file_name, str):
            continue
        result[file_name] = {
            "project_id": addon.get("addonID") or installed.get("projectId"),
            "file_id": installed.get("id"),
            "website": addon.get("webSiteURL"),
            "allow_mod_distribution": addon.get("allowModDistribution"),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--build-id", default="IF-M10-0001")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    mods_dir = (root / "mods").resolve()
    if root not in mods_dir.parents or not mods_dir.is_dir():
        raise SystemExit("Resolved mods directory is outside the instance or missing")

    source_files, owner_exceptions = load_source_registry(root)
    instance_sources = load_instance_sources(root)
    items: list[dict[str, Any]] = []
    for jar in sorted(mods_dir.glob("*.jar"), key=lambda item: item.name.lower()):
        item = inspect_jar(jar)
        source = source_files.get(jar.name)
        instance_source = instance_sources.get(jar.name)
        exception = owner_exceptions.get(jar.name)
        if source or instance_source:
            chosen = source or instance_source or {}
            item["distribution_source"] = {
                "type": "CURSEFORGE",
                "project_id": chosen.get("project_id"),
                "file_id": chosen.get("file_id"),
                "project_slug": chosen.get("project_slug"),
                "website": (instance_source or {}).get("website"),
                "allow_mod_distribution": (instance_source or {}).get(
                    "allow_mod_distribution"
                ),
                "registry_lock_present": source is not None,
                "instance_record_present": instance_source is not None,
            }
        elif exception:
            item["distribution_source"] = {
                "type": "OWNER_EXCEPTION",
                "reason_ru": exception.get("reason_ru"),
            }
        else:
            item["distribution_source"] = {"type": "UNREGISTERED"}
        items.append(item)

    status_counts = Counter(item["status"] for item in items)
    source_counts = Counter(item["distribution_source"]["type"] for item in items)
    payload = {
        "schema_version": 1,
        "build_id": args.build_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Static inspection of JAR metadata; no Minecraft, Forge, or mod code executed.",
        "interpretation": {
            "DECLARED": "A license declaration was found in mod metadata.",
            "LICENSE_FILE_ONLY": "No metadata declaration was found, but a license/notice file exists in the archive.",
            "UNDECLARED": "No machine-readable declaration or obvious license file was found; manual review is required.",
            "ERROR": "The archive could not be inspected completely.",
        },
        "summary": {
            "jar_count": len(items),
            "status_counts": dict(sorted(status_counts.items())),
            "source_counts": dict(sorted(source_counts.items())),
            "manual_review_count": sum(
                1 for item in items if item["manual_review_required"]
            ),
        },
        "mods": items,
    }

    output = args.output or (
        root
        / "docs"
        / "registries"
        / "generated"
        / args.build_id
        / "license_inventory.json"
    )
    output = output.resolve()
    if root not in output.parents:
        raise SystemExit("Output path must stay inside the instance root")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "License audit: "
        f"jars={len(items)} declared={status_counts['DECLARED']} "
        f"file_only={status_counts['LICENSE_FILE_ONLY']} "
        f"undeclared={status_counts['UNDECLARED']} errors={status_counts['ERROR']} "
        f"unregistered={source_counts['UNREGISTERED']}"
    )
    print(output)
    return 1 if status_counts["ERROR"] or source_counts["UNREGISTERED"] else 0


if __name__ == "__main__":
    sys.exit(main())
