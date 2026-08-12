#!/usr/bin/env python3
"""Prepare the approved Recast v3 lockup and mark from the archived study.

The accepted ImageGen sheet has a stable near-black background and contains
both a horizontal lockup and a small mark study.  This script performs only a
deterministic matte extraction; it does not redraw or reinterpret the logo.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parent.parent
APPROVED_SHEET = (
    ROOT
    / "docs"
    / "visual_previews"
    / "main_menu_concepts"
    / "logo_minecraft_recast_semibold_study.png"
)
LOCKUP_OUTPUT = ROOT / "brand_source" / "title_lockup_orbital_foundry_v3.png"
MARK_OUTPUT = ROOT / "brand_source" / "orbital_foundry_mark_v3.png"

# Coordinates are locked to the accepted 1692x929 sheet.  The lockup crop ends
# before the separate small-mark study; the mark crop excludes all word art.
LOCKUP_CROP = (170, 110, 1580, 655)
MARK_CROP = (170, 110, 750, 660)

# The approved sheet also contains a separate small mark below the lockup, and
# the large mark crop grazes the first letter of the adjacent wordmark.  These
# exclusion rectangles are crop-local and remove only those study fragments.
LOCKUP_EXCLUSIONS = ((530, 510, 1410, 545),)
MARK_EXCLUSIONS = ((460, 190, 580, 550),)

# Robust median of the four empty borders in the accepted sheet.
BACKGROUND_RGB = np.array((1.55, 2.71, 4.89), dtype=np.float32)
TRANSPARENT_DISTANCE = 5.0
OPAQUE_DISTANCE = 18.0


def extract(
    source: Image.Image,
    box: tuple[int, int, int, int],
    exclusions: tuple[tuple[int, int, int, int], ...] = (),
) -> Image.Image:
    pixels = np.asarray(source.crop(box).convert("RGB"), dtype=np.float32)
    distance = np.sqrt(np.square(pixels - BACKGROUND_RGB).sum(axis=2))
    alpha = np.clip(
        (distance - TRANSPARENT_DISTANCE)
        / (OPAQUE_DISTANCE - TRANSPARENT_DISTANCE),
        0.0,
        1.0,
    )
    # Smoothstep retains antialiasing without leaving a dark rectangular halo.
    alpha = alpha * alpha * (3.0 - 2.0 * alpha)
    for left, top, right, bottom in exclusions:
        alpha[top:bottom, left:right] = 0.0
    rgba = np.dstack((pixels.astype(np.uint8), (alpha * 255.0).astype(np.uint8)))
    result = Image.fromarray(rgba, "RGBA")
    alpha_box = result.getchannel("A").getbbox()
    if alpha_box is None:
        raise SystemExit("Approved logo extraction produced an empty alpha mask")
    return result.crop(alpha_box)


def save(image: Image.Image, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)
    print(f"{path.relative_to(ROOT).as_posix()}: {image.width}x{image.height} {image.mode}")


def main() -> int:
    if not APPROVED_SHEET.is_file():
        raise SystemExit(f"Missing approved logo sheet: {APPROVED_SHEET}")
    source = Image.open(APPROVED_SHEET).convert("RGB")
    if source.size != (1692, 929):
        raise SystemExit(f"Unexpected approved-sheet size: {source.size}; expected (1692, 929)")

    save(extract(source, LOCKUP_CROP, LOCKUP_EXCLUSIONS), LOCKUP_OUTPUT)
    save(extract(source, MARK_CROP, MARK_EXCLUSIONS), MARK_OUTPUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
