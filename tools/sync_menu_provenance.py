#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synchronize M9 provenance records after the Recast v2 menu build.

This is a mechanical registry updater.  It never launches Minecraft and it
does not inspect or modify localization files.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "docs" / "registries" / "m9_asset_provenance.json"


def file_metadata(relative_path: str) -> dict[str, object]:
    path = ROOT / pathlib.PurePosixPath(relative_path)
    payload = path.read_bytes()
    result: dict[str, object] = {
        "sha256": hashlib.sha256(payload).hexdigest().upper(),
        "bytes": len(payload),
    }
    if path.suffix.lower() == ".png":
        with Image.open(path) as image:
            result["width"], result["height"] = image.size
    return result


def source_record(
    source_id: str,
    path: str,
    created_at: str,
    summary_ru: str,
    summary_en: str,
    output_asset_ids: list[str],
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "path": path,
        "kind": "PNG",
        "origin_type": "PROJECT_AI_GENERATED",
        "license_id": "PROJECT-ORIGINAL",
        **file_metadata(path),
        "created_at": created_at,
        "generator_provider": "OpenAI ImageGen built-in tool",
        "model_disclosure": "The exact model identifier was not exposed by the built-in image-generation tool.",
        "prompt_record_status": "RECONSTRUCTED_SUMMARY_ONLY",
        "prompt_summary_ru": summary_ru,
        "prompt_summary_en": summary_en,
        "rights_basis": "Original artwork generated specifically for Recast; no third-party raster source is present in the accepted source chain.",
        "output_asset_ids": output_asset_ids,
    }


SOURCE_RECORDS = {
    "industrial_frontier:source/brand/mark": source_record(
        "industrial_frontier:source/brand/mark",
        "brand_source/orbital_foundry_icon_v2.png",
        "2026-08-08T16:18:00+03:00",
        "Знак «Орбитальная литейная»: шестигранная стальная рама, единый силуэт реактора и ракеты, орбитальная дуга и один расплавленный оранжевый шов; рассчитан на чтение от 16 пикселей.",
        "Orbital Foundry emblem: a steel hexagonal frame, unified reactor-and-rocket silhouette, one orbital arc and one molten-orange seam, designed to read from 16 pixels.",
        [
            "industrial_frontier:asset/gui/icon_16",
            "industrial_frontier:asset/gui/icon_32",
            "industrial_frontier:asset/gui/icon_64",
            "industrial_frontier:asset/gui/icon_128",
            "industrial_frontier:asset/gui/icon_256",
            "industrial_frontier:asset/gui/mark",
        ],
    ),
    "industrial_frontier:source/brand/menu_background": source_record(
        "industrial_frontier:source/brand/menu_background",
        "brand_source/menu_parallax_base_v2.png",
        "2026-08-08T16:12:00+03:00",
        "Дальний план меню: обитаемый промышленный город, химический комплекс, логистика и космодром в одной blue-hour панораме с тёмной безопасной зоной слева.",
        "Menu far plane: a living industrial city, chemical complex, logistics network and spaceport in one blue-hour panorama with a calm dark UI-safe zone on the left.",
        [
            "industrial_frontier:asset/gui/background",
            "industrial_frontier:asset/gui/menu/base",
        ],
    ),
    "industrial_frontier:source/brand/menu_mid": source_record(
        "industrial_frontier:source/brand/menu_mid",
        "brand_source/menu_parallax_mid_v2.png",
        "2026-08-08T16:15:00+03:00",
        "Прозрачный средний план: трубопроводная эстакада, химическая сервисная ферма, грузовая линия и сигнальные башни для умеренного параллакса.",
        "Transparent mid plane: pipe rack, chemical-service gantry, freight line and signal towers for moderate cursor parallax.",
        ["industrial_frontier:asset/gui/menu/mid"],
    ),
    "industrial_frontier:source/brand/menu_near": source_record(
        "industrial_frontier:source/brand/menu_near",
        "brand_source/menu_parallax_near_v2.png",
        "2026-08-08T16:17:00+03:00",
        "Прозрачная передняя рама: ограждение, трубы, край стальной фермы и один янтарный светильник для сильного, но безопасного параллакса.",
        "Transparent near frame: railing, pipes, a cropped steel truss and one amber service lamp for strong but safe cursor parallax.",
        ["industrial_frontier:asset/gui/menu/near"],
    ),
    "industrial_frontier:source/brand/title_lockup": source_record(
        "industrial_frontier:source/brand/title_lockup",
        "brand_source/title_lockup_v2.png",
        "2026-08-08T16:20:00+03:00",
        "Собственный двухстрочный игровой логотип MINECRAFT / RECAST из холодной стали с единым литейным швом и без сторонней графики.",
        "Original two-line MINECRAFT / RECAST game-title lockup in cold steel with one casting seam and no third-party artwork.",
        ["industrial_frontier:asset/gui/logo"],
    ),
}


ASSET_SPECS: dict[str, dict[str, object]] = {
    "config/paxi/resourcepacks/IndustrialFrontier-Core/assets/industrial_frontier/textures/gui/background.png": {
        "asset_id": "industrial_frontier:asset/gui/background",
        "resource_location": "industrial_frontier:textures/gui/background.png",
        "source_type": "PROJECT_GENERATED",
        "source_artwork_id": "industrial_frontier:source/brand/menu_background",
        "source_note": "16:9 service-screen delivery frame built by tools/build_menu_visuals.py from the accepted v2 far-plane artwork.",
    },
    "config/paxi/resourcepacks/IndustrialFrontier-Core/assets/industrial_frontier/textures/gui/menu/base.png": {
        "asset_id": "industrial_frontier:asset/gui/menu/base",
        "resource_location": "industrial_frontier:textures/gui/menu/base.png",
        "source_type": "PROJECT_GENERATED",
        "source_artwork_id": "industrial_frontier:source/brand/menu_background",
        "source_note": "Overscan 16:9 title-menu base built by tools/build_menu_visuals.py.",
    },
    "config/paxi/resourcepacks/IndustrialFrontier-Core/assets/industrial_frontier/textures/gui/menu/mid.png": {
        "asset_id": "industrial_frontier:asset/gui/menu/mid",
        "resource_location": "industrial_frontier:textures/gui/menu/mid.png",
        "source_type": "PROJECT_GENERATED",
        "source_artwork_id": "industrial_frontier:source/brand/menu_mid",
        "source_note": "Alpha-preserving 16:9 midground layer built by tools/build_menu_visuals.py.",
    },
    "config/paxi/resourcepacks/IndustrialFrontier-Core/assets/industrial_frontier/textures/gui/menu/near.png": {
        "asset_id": "industrial_frontier:asset/gui/menu/near",
        "resource_location": "industrial_frontier:textures/gui/menu/near.png",
        "source_type": "PROJECT_GENERATED",
        "source_artwork_id": "industrial_frontier:source/brand/menu_near",
        "source_note": "Alpha-preserving 16:9 foreground frame built by tools/build_menu_visuals.py.",
    },
    "config/paxi/resourcepacks/IndustrialFrontier-Core/assets/industrial_frontier/textures/gui/logo.png": {
        "asset_id": "industrial_frontier:asset/gui/logo",
        "resource_location": "industrial_frontier:textures/gui/logo.png",
        "source_type": "PROJECT_GENERATED",
        "source_artwork_id": "industrial_frontier:source/brand/title_lockup",
        "source_note": "Alpha-trimmed and fitted to the 3:1 runtime canvas by tools/build_menu_visuals.py.",
    },
}

for size in (16, 32, 64, 128, 256):
    icon_spec = {
        "asset_id": f"industrial_frontier:asset/gui/icon_{size}",
        "resource_location": f"industrial_frontier:textures/gui/icon_{size}.png",
        "source_type": "PROJECT_GENERATED",
    }
    if size <= 32:
        icon_spec["source_note"] = (
            "Dedicated Recast micro-mark drawn directly on a 16px grid by tools/build_menu_visuals.py; "
            "the 32px delivery uses nearest-neighbour scaling and is not a downsampled illustration."
        )
    else:
        icon_spec["source_artwork_id"] = "industrial_frontier:source/brand/mark"
        icon_spec["source_note"] = (
            "Size-specific orbital-foundry icon built from the accepted source artwork by tools/build_menu_visuals.py."
        )
    ASSET_SPECS[f"config/paxi/resourcepacks/IndustrialFrontier-Core/assets/industrial_frontier/textures/gui/icon_{size}.png"] = icon_spec

ASSET_SPECS["config/paxi/resourcepacks/IndustrialFrontier-Core/assets/industrial_frontier/textures/gui/mark.png"] = {
    "asset_id": "industrial_frontier:asset/gui/mark",
    "resource_location": "industrial_frontier:textures/gui/mark.png",
    "source_type": "PROJECT_GENERATED",
    "source_artwork_id": "industrial_frontier:source/brand/mark",
    "source_note": "512px canonical orbital-foundry mark built by tools/build_menu_visuals.py.",
}

DERIVED = {
    "config/fancymenu/assets/background.png": ("industrial_frontier:asset/fancymenu/background", "industrial_frontier:asset/gui/background"),
    "config/fancymenu/assets/menu/base.png": ("industrial_frontier:asset/fancymenu/menu/base", "industrial_frontier:asset/gui/menu/base"),
    "config/fancymenu/assets/menu/mid.png": ("industrial_frontier:asset/fancymenu/menu/mid", "industrial_frontier:asset/gui/menu/mid"),
    "config/fancymenu/assets/menu/near.png": ("industrial_frontier:asset/fancymenu/menu/near", "industrial_frontier:asset/gui/menu/near"),
    "config/fancymenu/assets/logo.png": ("industrial_frontier:asset/fancymenu/logo", "industrial_frontier:asset/gui/logo"),
    "config/fancymenu/assets/mark.png": ("industrial_frontier:asset/fancymenu/mark", "industrial_frontier:asset/gui/mark"),
    "config/fancymenu/assets/icon_16.png": ("industrial_frontier:asset/fancymenu/icon_16", "industrial_frontier:asset/gui/icon_16"),
    "config/fancymenu/assets/icon_32.png": ("industrial_frontier:asset/fancymenu/icon_32", "industrial_frontier:asset/gui/icon_32"),
    "pack_icon.png": ("industrial_frontier:asset/package/pack_icon", "industrial_frontier:asset/gui/icon_256"),
}

for path, (asset_id, derived_from) in DERIVED.items():
    ASSET_SPECS[path] = {
        "asset_id": asset_id,
        "source_type": "DERIVED_PROJECT_ASSET",
        "derived_from": derived_from,
        "source_note": "Byte-identical delivery copy of the canonical Recast v2 resource-pack asset.",
    }

for state in ("normal", "hover", "inactive"):
    ASSET_SPECS[f"config/fancymenu/assets/ui/button_{state}.png"] = {
        "asset_id": f"industrial_frontier:asset/fancymenu/ui/button_{state}",
        "source_type": "PROJECT_GENERATED",
        "source_note": "Chamfered nine-slice button state rendered by tools/build_menu_visuals.py.",
    }
    ASSET_SPECS[f"config/fancymenu/assets/ui/icon_button_{state}.png"] = {
        "asset_id": f"industrial_frontier:asset/fancymenu/ui/icon_button_{state}",
        "source_type": "PROJECT_GENERATED",
        "source_note": "Compact language/accessibility button state rendered by tools/build_menu_visuals.py.",
    }

ASSET_SPECS["config/fancymenu/assets/ui/panel.png"] = {
    "asset_id": "industrial_frontier:asset/fancymenu/ui/panel",
    "source_type": "PROJECT_GENERATED",
    "source_note": "Chamfered translucent control panel rendered by tools/build_menu_visuals.py for 12px nine-slicing.",
}


def asset_record(path: str, spec: dict[str, object]) -> dict[str, object]:
    record: dict[str, object] = {
        "asset_id": spec["asset_id"],
        "path": path,
    }
    if "resource_location" in spec:
        record["resource_location"] = spec["resource_location"]
    record.update(
        {
            "kind": "PNG",
            "source_type": spec["source_type"],
            "license_id": "PROJECT-ORIGINAL",
            **file_metadata(path),
        }
    )
    if "derived_from" in spec:
        record["derived_from"] = spec["derived_from"]
    if "source_artwork_id" in spec:
        record["source_artwork_id"] = spec["source_artwork_id"]
    record["source_note"] = spec["source_note"]
    return record


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))
    old_sources = {entry["source_id"]: entry for entry in registry["source_artwork"]}
    for source_id, record in SOURCE_RECORDS.items():
        old_sources[source_id] = record
    registry["source_artwork"] = list(old_sources.values())

    old_assets = {entry["path"]: entry for entry in registry["assets"]}
    for path, spec in ASSET_SPECS.items():
        old_assets[path] = asset_record(path, spec)
    registry["assets"] = sorted(old_assets.values(), key=lambda entry: entry["path"])
    registry["generator"]["method"] = (
        "Deterministic Pillow rendering for symbols and UI states; accepted ImageGen artwork is reframed and alpha-preserved by "
        "tools/build_menu_visuals.py; 16/32px window icons are direct pixel-grid micro-marks; FancyMenu delivery copies are "
        "byte-identical to canonical resource-pack assets."
    )

    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"source_artwork={len(registry['source_artwork'])} assets={len(registry['assets'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
