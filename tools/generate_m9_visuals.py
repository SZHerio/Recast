#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministically build the M9 interface and icon atlas.

This script never touches saves or launches Minecraft. It converts the accepted
M9 visual contract into small, reviewable PNG assets and copies the approved
hero artwork into FancyMenu's local asset directory.
"""

from __future__ import annotations

import math
import pathlib
import shutil
import sys
from collections.abc import Callable

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from build_menu_visuals import main as build_menu_visuals


ROOT = pathlib.Path(__file__).resolve().parent.parent
PACK = ROOT / "config" / "paxi" / "resourcepacks" / "IndustrialFrontier-Core" / "assets"
GUI = PACK / "industrial_frontier" / "textures" / "gui"
FM = ROOT / "config" / "fancymenu" / "assets"

DEEP = (20, 24, 28, 255)
SURFACE = (30, 37, 43, 255)
SURFACE_2 = (42, 51, 59, 255)
STEEL = (74, 156, 199, 255)
MOLTEN = (232, 121, 43, 255)
MOLTEN_BRIGHT = (255, 176, 92, 255)
TEXT = (230, 233, 236, 255)
MUTED = (152, 162, 172, 255)
SUCCESS = (118, 199, 122, 255)
WARNING = (225, 175, 79, 255)
DANGER = (229, 107, 84, 255)

EPOCHS = tuple(f"p{i}" for i in range(10))
PROCESS_PATHS = (
    "create/clay_form_service",
    "create/heated_brass",
    "geology/ore_sources",
    "gtceu/foundational_feedstocks",
    "gtceu/metallurgy",
    "gtceu/air_separation",
    "gtceu/chlor_alkali",
    "gtceu/nitrogen_chemistry",
    "gtceu/sulfuric_acid",
    "gtceu/hydrochloric_acid",
    "gtceu/water_treatment",
    "gtceu/petrochemical_products",
    "gtceu/electronic_silicon",
    "gtceu/uranium_preparation",
    "gtceu/rocket_materials",
    "gtceu/sewage_recovery",
    "ae2/digital_material_entry",
    "future/petroleum_primary",
    "future/civil_nuclear_cycle",
    "future/strategic_demand",
    "future/city_demand",
    "future/space_launch_and_colony",
)

FACTIONS = {
    "zemlemer": (118, 199, 122, 255),
    "meridian": (74, 156, 199, 255),
    "free_caravans": (225, 175, 79, 255),
    "helios": (114, 202, 232, 255),
    "ash_root": (135, 166, 107, 255),
    "scar": (229, 107, 84, 255),
}

REPUTATION = {
    "sworn_enemy": DANGER,
    "hostile": (207, 91, 75, 255),
    "distrust": WARNING,
    "neutral": MUTED,
    "respect": STEEL,
    "alliance": SUCCESS,
    "special": MOLTEN_BRIGHT,
}

TREATIES = ("truce", "trade", "tribute", "alliance", "joint_defence")
OPERATIONS = (
    "planned",
    "recon",
    "warned",
    "negotiation_window",
    "preparation",
    "active",
    "recovery",
    "cooldown",
    "closed",
)


def aa_canvas(size: tuple[int, int], scale: int = 4) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    image = Image.new("RGBA", (size[0] * scale, size[1] * scale), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image), scale


def downsample(image: Image.Image, size: tuple[int, int], sharpen: bool = True) -> Image.Image:
    result = image.resize(size, Image.Resampling.LANCZOS)
    if sharpen:
        result = result.filter(ImageFilter.UnsharpMask(radius=0.8, percent=115, threshold=2))
    return result


def save(path: pathlib.Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def frame(draw: ImageDraw.ImageDraw, size: int, scale: int, accent=STEEL) -> None:
    pad = 3 * scale
    radius = 7 * scale
    draw.rounded_rectangle(
        (pad, pad, size * scale - pad - 1, size * scale - pad - 1),
        radius=radius,
        fill=SURFACE,
        outline=accent,
        width=max(2, scale),
    )
    draw.line(
        (8 * scale, (size - 8) * scale, 24 * scale, (size - 8) * scale),
        fill=MOLTEN,
        width=2 * scale,
    )


def draw_epoch_icon(index: int, size: int = 64) -> Image.Image:
    image, draw, scale = aa_canvas((size, size))
    frame(draw, size, scale)
    c = size * scale // 2
    w = max(2, 2 * scale)
    steel = STEEL
    hot = MOLTEN_BRIGHT

    if index == 0:  # compass / expedition
        draw.ellipse((14 * scale, 14 * scale, 50 * scale, 50 * scale), outline=steel, width=w)
        draw.polygon(((c, 16 * scale), (38 * scale, 37 * scale), (c, c)), fill=hot)
        draw.polygon(((c, 48 * scale), (26 * scale, 27 * scale), (c, c)), fill=MUTED)
    elif index == 1:  # mechanical settlement
        draw.ellipse((19 * scale, 19 * scale, 45 * scale, 45 * scale), outline=steel, width=3 * scale)
        draw.ellipse((27 * scale, 27 * scale, 37 * scale, 37 * scale), fill=hot)
        for angle in range(0, 360, 45):
            x1 = c + math.cos(math.radians(angle)) * 14 * scale
            y1 = c + math.sin(math.radians(angle)) * 14 * scale
            x2 = c + math.cos(math.radians(angle)) * 20 * scale
            y2 = c + math.sin(math.radians(angle)) * 20 * scale
            draw.line((x1, y1, x2, y2), fill=steel, width=4 * scale)
    elif index == 2:  # industrial heat
        draw.rounded_rectangle((16 * scale, 20 * scale, 48 * scale, 50 * scale), radius=3 * scale, outline=steel, width=w)
        draw.rectangle((20 * scale, 15 * scale, 26 * scale, 22 * scale), fill=MUTED)
        draw.rectangle((38 * scale, 12 * scale, 44 * scale, 22 * scale), fill=MUTED)
        draw.polygon(((c, 45 * scale), (24 * scale, 36 * scale), (29 * scale, 25 * scale), (36 * scale, 33 * scale), (40 * scale, 26 * scale), (42 * scale, 39 * scale)), fill=hot)
    elif index == 3:  # electrified district
        draw.rectangle((14 * scale, 31 * scale, 24 * scale, 49 * scale), fill=MUTED)
        draw.rectangle((27 * scale, 23 * scale, 37 * scale, 49 * scale), fill=steel)
        draw.rectangle((40 * scale, 28 * scale, 50 * scale, 49 * scale), fill=MUTED)
        draw.polygon(((35 * scale, 11 * scale), (25 * scale, 30 * scale), (33 * scale, 29 * scale), (29 * scale, 43 * scale), (44 * scale, 23 * scale), (36 * scale, 24 * scale)), fill=hot)
    elif index == 4:  # chemical city
        draw.line((24 * scale, 14 * scale, 40 * scale, 14 * scale), fill=steel, width=w)
        draw.line((28 * scale, 14 * scale, 28 * scale, 28 * scale), fill=steel, width=w)
        draw.line((36 * scale, 14 * scale, 36 * scale, 28 * scale), fill=steel, width=w)
        draw.polygon(((28 * scale, 27 * scale), (17 * scale, 48 * scale), (47 * scale, 48 * scale), (36 * scale, 27 * scale)), outline=steel, fill=SURFACE_2)
        draw.polygon(((21 * scale, 43 * scale), (43 * scale, 43 * scale), (38 * scale, 34 * scale), (26 * scale, 37 * scale)), fill=hot)
    elif index == 5:  # regional logistics
        draw.line((12 * scale, 42 * scale, 52 * scale, 42 * scale), fill=steel, width=3 * scale)
        draw.line((17 * scale, 48 * scale, 47 * scale, 48 * scale), fill=MUTED, width=2 * scale)
        for x in range(18, 48, 8):
            draw.line((x * scale, 38 * scale, (x - 2) * scale, 51 * scale), fill=MUTED, width=scale)
        draw.rectangle((17 * scale, 20 * scale, 39 * scale, 36 * scale), outline=steel, width=w)
        draw.polygon(((39 * scale, 24 * scale), (50 * scale, 29 * scale), (39 * scale, 34 * scale)), fill=hot)
    elif index == 6:  # nuclear industry
        draw.ellipse((16 * scale, 27 * scale, 48 * scale, 37 * scale), outline=steel, width=w)
        draw.ellipse((27 * scale, 16 * scale, 37 * scale, 48 * scale), outline=steel, width=w)
        draw.ellipse((21 * scale, 19 * scale, 43 * scale, 45 * scale), outline=MUTED, width=scale)
        draw.ellipse((28 * scale, 28 * scale, 36 * scale, 36 * scale), fill=hot)
    elif index == 7:  # strategic aerospace
        draw.polygon(((c, 11 * scale), (42 * scale, 34 * scale), (38 * scale, 48 * scale), (c, 41 * scale), (26 * scale, 48 * scale), (22 * scale, 34 * scale)), outline=steel, fill=SURFACE_2)
        draw.ellipse((29 * scale, 22 * scale, 35 * scale, 28 * scale), fill=hot)
        draw.line((29 * scale, 43 * scale, 25 * scale, 53 * scale), fill=MOLTEN, width=w)
        draw.line((35 * scale, 43 * scale, 39 * scale, 53 * scale), fill=MOLTEN, width=w)
    elif index == 8:  # orbital network
        draw.ellipse((20 * scale, 20 * scale, 44 * scale, 44 * scale), outline=steel, width=w)
        draw.ellipse((8 * scale, 27 * scale, 56 * scale, 37 * scale), outline=MUTED, width=scale)
        draw.ellipse((44 * scale, 27 * scale, 50 * scale, 33 * scale), fill=hot)
        draw.line((c, 16 * scale, c, 48 * scale), fill=steel, width=scale)
    else:  # interplanetary civilization
        draw.ellipse((18 * scale, 20 * scale, 46 * scale, 48 * scale), fill=steel, outline=TEXT, width=scale)
        draw.arc((8 * scale, 26 * scale, 56 * scale, 44 * scale), 185, 355, fill=hot, width=3 * scale)
        draw.ellipse((48 * scale, 28 * scale, 54 * scale, 34 * scale), fill=hot)
        draw.line((13 * scale, 15 * scale, 18 * scale, 20 * scale), fill=MUTED, width=scale)
        draw.line((46 * scale, 13 * scale, 43 * scale, 19 * scale), fill=MUTED, width=scale)

    return downsample(image, (size, size))


def draw_process_icon(pathway: str, index: int, size: int = 64) -> Image.Image:
    image, draw, scale = aa_canvas((size, size))
    frame(draw, size, scale)
    w = max(2, 2 * scale)
    # Common process grammar: feed on the left, operation in the centre, product on the right.
    draw.ellipse((9 * scale, 28 * scale, 17 * scale, 36 * scale), fill=MUTED)
    draw.line((17 * scale, 32 * scale, 24 * scale, 32 * scale), fill=STEEL, width=w)
    draw.line((40 * scale, 32 * scale, 47 * scale, 32 * scale), fill=STEEL, width=w)
    draw.polygon(((47 * scale, 27 * scale), (55 * scale, 32 * scale), (47 * scale, 37 * scale)), fill=MOLTEN_BRIGHT)

    if "water" in pathway or "sewage" in pathway:
        draw.polygon(((32 * scale, 18 * scale), (23 * scale, 34 * scale), (32 * scale, 45 * scale), (41 * scale, 34 * scale)), fill=STEEL, outline=TEXT)
    elif "acid" in pathway or "alkali" in pathway or "nitrogen" in pathway or "petrochemical" in pathway:
        draw.line((27 * scale, 18 * scale, 37 * scale, 18 * scale), fill=TEXT, width=w)
        draw.polygon(((28 * scale, 18 * scale), (28 * scale, 28 * scale), (21 * scale, 43 * scale), (43 * scale, 43 * scale), (36 * scale, 28 * scale), (36 * scale, 18 * scale)), fill=SURFACE_2, outline=STEEL)
        draw.rectangle((25 * scale, 36 * scale, 39 * scale, 41 * scale), fill=MOLTEN)
    elif "nuclear" in pathway or "uranium" in pathway:
        draw.ellipse((25 * scale, 25 * scale, 39 * scale, 39 * scale), fill=MOLTEN_BRIGHT)
        for angle in (0, 120, 240):
            x = 32 * scale + math.cos(math.radians(angle)) * 12 * scale
            y = 32 * scale + math.sin(math.radians(angle)) * 12 * scale
            draw.ellipse((x - 4 * scale, y - 4 * scale, x + 4 * scale, y + 4 * scale), outline=STEEL, width=w)
    elif "rocket" in pathway or "space" in pathway:
        draw.polygon(((32 * scale, 15 * scale), (40 * scale, 36 * scale), (35 * scale, 45 * scale), (29 * scale, 45 * scale), (24 * scale, 36 * scale)), fill=SURFACE_2, outline=STEEL)
        draw.polygon(((29 * scale, 44 * scale), (32 * scale, 52 * scale), (35 * scale, 44 * scale)), fill=MOLTEN_BRIGHT)
    elif "silicon" in pathway or "digital" in pathway:
        draw.rectangle((22 * scale, 22 * scale, 42 * scale, 42 * scale), fill=SURFACE_2, outline=STEEL, width=w)
        for pos in range(24, 43, 6):
            draw.line((pos * scale, 17 * scale, pos * scale, 22 * scale), fill=MUTED, width=scale)
            draw.line((pos * scale, 42 * scale, pos * scale, 47 * scale), fill=MUTED, width=scale)
        draw.rectangle((28 * scale, 28 * scale, 36 * scale, 36 * scale), fill=MOLTEN_BRIGHT)
    elif "metallurgy" in pathway or "brass" in pathway or "clay" in pathway:
        draw.polygon(((20 * scale, 20 * scale), (44 * scale, 20 * scale), (39 * scale, 43 * scale), (25 * scale, 43 * scale)), fill=SURFACE_2, outline=STEEL)
        draw.polygon(((25 * scale, 32 * scale), (39 * scale, 32 * scale), (36 * scale, 40 * scale), (28 * scale, 40 * scale)), fill=MOLTEN_BRIGHT)
    elif "logistics" in pathway or "demand" in pathway or "city" in pathway:
        draw.rectangle((21 * scale, 23 * scale, 41 * scale, 41 * scale), outline=STEEL, width=w)
        draw.line((21 * scale, 29 * scale, 41 * scale, 29 * scale), fill=MUTED, width=scale)
        draw.line((27 * scale, 23 * scale, 27 * scale, 41 * scale), fill=MUTED, width=scale)
    elif "air" in pathway:
        for offset in (-7, 0, 7):
            draw.arc(((17 + offset) * scale, (22 + offset // 2) * scale, (47 + offset) * scale, (36 + offset // 2) * scale), 190, 350, fill=STEEL, width=w)
    else:
        draw.ellipse((22 * scale, 22 * scale, 42 * scale, 42 * scale), outline=STEEL, width=3 * scale)
        draw.ellipse((29 * scale, 29 * scale, 35 * scale, 35 * scale), fill=MOLTEN_BRIGHT)
        for angle in range(0, 360, 60):
            x1 = 32 * scale + math.cos(math.radians(angle)) * 10 * scale
            y1 = 32 * scale + math.sin(math.radians(angle)) * 10 * scale
            x2 = 32 * scale + math.cos(math.radians(angle)) * 15 * scale
            y2 = 32 * scale + math.sin(math.radians(angle)) * 15 * scale
            draw.line((x1, y1, x2, y2), fill=STEEL, width=2 * scale)

    # A small deterministic notch makes icons within the same family distinguishable.
    notch_x = (10 + (index * 7) % 40) * scale
    draw.rectangle((notch_x, 8 * scale, notch_x + 4 * scale, 11 * scale), fill=MOLTEN)
    return downsample(image, (size, size))


def draw_faction_emblem(faction: str, accent: tuple[int, int, int, int], size: int = 96) -> Image.Image:
    image, draw, scale = aa_canvas((size, size))
    pad = 8 * scale
    draw.polygon(
        (
            (48 * scale, pad),
            ((96 - 12) * scale, 28 * scale),
            ((96 - 12) * scale, 68 * scale),
            (48 * scale, (96 - 8) * scale),
            (12 * scale, 68 * scale),
            (12 * scale, 28 * scale),
        ),
        fill=SURFACE,
        outline=accent,
    )
    w = 3 * scale
    if faction == "zemlemer":
        for pos in (31, 48, 65):
            draw.line((pos * scale, 23 * scale, pos * scale, 64 * scale), fill=accent, width=scale)
        for pos in (31, 45, 59):
            draw.line((24 * scale, pos * scale, 72 * scale, pos * scale), fill=accent, width=scale)
        draw.arc((22 * scale, 48 * scale, 74 * scale, 76 * scale), 190, 350, fill=MOLTEN_BRIGHT, width=w)
    elif faction == "meridian":
        draw.line((48 * scale, 17 * scale, 48 * scale, 77 * scale), fill=accent, width=4 * scale)
        draw.line((30 * scale, 27 * scale, 66 * scale, 27 * scale), fill=MUTED, width=w)
        draw.line((30 * scale, 47 * scale, 66 * scale, 47 * scale), fill=MUTED, width=w)
        draw.line((30 * scale, 67 * scale, 66 * scale, 67 * scale), fill=MUTED, width=w)
        draw.rectangle((43 * scale, 38 * scale, 53 * scale, 56 * scale), fill=MOLTEN_BRIGHT)
    elif faction == "free_caravans":
        draw.ellipse((23 * scale, 23 * scale, 73 * scale, 73 * scale), outline=accent, width=w)
        draw.polygon(((48 * scale, 18 * scale), (56 * scale, 50 * scale), (48 * scale, 45 * scale), (40 * scale, 50 * scale)), fill=MOLTEN_BRIGHT)
        draw.line((29 * scale, 66 * scale, 67 * scale, 30 * scale), fill=accent, width=w)
        for x, y in ((29, 66), (48, 48), (67, 30)):
            draw.ellipse(((x - 3) * scale, (y - 3) * scale, (x + 3) * scale, (y + 3) * scale), fill=TEXT)
    elif faction == "helios":
        draw.ellipse((27 * scale, 27 * scale, 69 * scale, 69 * scale), outline=accent, width=4 * scale)
        draw.ellipse((39 * scale, 39 * scale, 57 * scale, 57 * scale), fill=MOLTEN_BRIGHT)
        for angle in range(0, 360, 45):
            x1 = 48 * scale + math.cos(math.radians(angle)) * 25 * scale
            y1 = 48 * scale + math.sin(math.radians(angle)) * 25 * scale
            x2 = 48 * scale + math.cos(math.radians(angle)) * 32 * scale
            y2 = 48 * scale + math.sin(math.radians(angle)) * 32 * scale
            draw.line((x1, y1, x2, y2), fill=accent, width=2 * scale)
    elif faction == "ash_root":
        draw.ellipse((24 * scale, 22 * scale, 72 * scale, 70 * scale), outline=MUTED, width=w)
        draw.line((48 * scale, 18 * scale, 48 * scale, 71 * scale), fill=accent, width=4 * scale)
        draw.line((48 * scale, 48 * scale, 30 * scale, 69 * scale), fill=accent, width=w)
        draw.line((48 * scale, 48 * scale, 66 * scale, 69 * scale), fill=accent, width=w)
        draw.line((48 * scale, 37 * scale, 61 * scale, 25 * scale), fill=MOLTEN_BRIGHT, width=2 * scale)
    else:  # scar
        draw.polygon(((25 * scale, 25 * scale), (71 * scale, 25 * scale), (68 * scale, 70 * scale), (28 * scale, 70 * scale)), fill=SURFACE_2, outline=accent)
        draw.line((30 * scale, 68 * scale, 65 * scale, 28 * scale), fill=MOLTEN_BRIGHT, width=5 * scale)
        draw.line((25 * scale, 46 * scale, 40 * scale, 46 * scale), fill=accent, width=w)
        draw.line((55 * scale, 51 * scale, 70 * scale, 51 * scale), fill=accent, width=w)
    return downsample(image, (size, size))


def draw_silhouette(faction: str, accent: tuple[int, int, int, int], size=(128, 192)) -> Image.Image:
    image, draw, scale = aa_canvas(size)
    # Ground marker and neutral human mass keep identity readable without relying on faction colour.
    draw.ellipse((24 * scale, 172 * scale, 104 * scale, 184 * scale), fill=(10, 12, 14, 190))
    helmet_top = {"helios": 18, "scar": 26, "free_caravans": 22}.get(faction, 24)
    draw.ellipse((43 * scale, helmet_top * scale, 85 * scale, (helmet_top + 43) * scale), fill=MUTED, outline=TEXT, width=scale)
    shoulder = 24 if faction in ("scar", "meridian") else 31
    draw.polygon(((shoulder * scale, 72 * scale), ((128 - shoulder) * scale, 72 * scale), (92 * scale, 142 * scale), (36 * scale, 142 * scale)), fill=SURFACE_2, outline=accent)
    draw.rectangle((43 * scale, 137 * scale, 59 * scale, 176 * scale), fill=SURFACE, outline=MUTED)
    draw.rectangle((69 * scale, 137 * scale, 85 * scale, 176 * scale), fill=SURFACE, outline=MUTED)
    if faction == "zemlemer":
        draw.rectangle((48 * scale, 34 * scale, 80 * scale, 41 * scale), fill=accent)
        draw.line((40 * scale, 85 * scale, 88 * scale, 121 * scale), fill=accent, width=2 * scale)
    elif faction == "meridian":
        draw.rectangle((28 * scale, 78 * scale, 100 * scale, 91 * scale), fill=accent)
        draw.rectangle((51 * scale, 47 * scale, 77 * scale, 62 * scale), fill=SURFACE)
    elif faction == "free_caravans":
        draw.line((36 * scale, 75 * scale, 86 * scale, 136 * scale), fill=accent, width=6 * scale)
        draw.rectangle((91 * scale, 79 * scale, 108 * scale, 126 * scale), fill=SURFACE, outline=accent)
    elif faction == "helios":
        draw.ellipse((47 * scale, 30 * scale, 81 * scale, 57 * scale), fill=(20, 31, 37, 255), outline=accent, width=2 * scale)
        draw.rectangle((53 * scale, 87 * scale, 75 * scale, 105 * scale), fill=accent)
    elif faction == "ash_root":
        draw.polygon(((43 * scale, 35 * scale), (84 * scale, 27 * scale), (78 * scale, 64 * scale), (48 * scale, 59 * scale)), fill=SURFACE, outline=accent)
        draw.line((31 * scale, 92 * scale, 93 * scale, 126 * scale), fill=accent, width=3 * scale)
    else:
        draw.polygon(((27 * scale, 73 * scale), (104 * scale, 68 * scale), (94 * scale, 139 * scale), (37 * scale, 143 * scale)), fill=SURFACE_2, outline=accent)
        draw.line((38 * scale, 132 * scale, 91 * scale, 75 * scale), fill=MOLTEN_BRIGHT, width=5 * scale)
    return downsample(image, size)


def draw_base_icon(level: int, accent: tuple[int, int, int, int], size=(96, 64)) -> Image.Image:
    image, draw, scale = aa_canvas(size)
    draw.rounded_rectangle((3 * scale, 3 * scale, 93 * scale, 61 * scale), radius=5 * scale, fill=DEEP, outline=accent, width=scale)
    ground = 52 * scale
    draw.line((8 * scale, ground, 88 * scale, ground), fill=MUTED, width=scale)
    material = (95 + level * 12, 92 + level * 12, 85 + level * 12, 255) if level < 3 else (70 + level * 6, 78 + level * 6, 84 + level * 7, 255)
    blocks = 1 + level
    span = 60
    bw = max(7, span // blocks)
    start = 48 - (blocks * bw) // 2
    for index in range(blocks):
        height = (14 + ((index * 7 + level * 5) % (15 + level * 2))) * scale
        left = (start + index * bw) * scale
        draw.rectangle((left, ground - height, left + (bw - 2) * scale, ground), fill=material, outline=SURFACE_2)
    if level <= 1:
        draw.line((11 * scale, ground, 11 * scale, (28 - level * 4) * scale), fill=accent, width=2 * scale)
        draw.line((85 * scale, ground, 85 * scale, (28 - level * 4) * scale), fill=accent, width=2 * scale)
    if level >= 2:
        draw.rectangle((9 * scale, (46 - level * 2) * scale, 16 * scale, ground), fill=SURFACE_2, outline=accent)
        draw.rectangle((80 * scale, (46 - level * 2) * scale, 87 * scale, ground), fill=SURFACE_2, outline=accent)
    if level >= 3:
        draw.line((12 * scale, (18 + level) * scale, 84 * scale, (18 + level) * scale), fill=accent, width=2 * scale)
    if level >= 4:
        draw.ellipse((42 * scale, 9 * scale, 54 * scale, 21 * scale), outline=MOLTEN_BRIGHT, width=2 * scale)
    if level >= 5:
        draw.arc((20 * scale, 1 * scale, 76 * scale, 45 * scale), 205, 335, fill=accent, width=2 * scale)
    if level >= 6:
        draw.line((48 * scale, 8 * scale, 48 * scale, 24 * scale), fill=MOLTEN_BRIGHT, width=2 * scale)
        draw.ellipse((45 * scale, 5 * scale, 51 * scale, 11 * scale), fill=MOLTEN_BRIGHT)
    return downsample(image, size)


def symbol_icon(kind: str, accent: tuple[int, int, int, int], size: int = 64) -> Image.Image:
    image, draw, scale = aa_canvas((size, size))
    frame(draw, size, scale, accent)
    w = 3 * scale
    if kind in ("sworn_enemy", "active"):
        draw.line((19 * scale, 19 * scale, 45 * scale, 45 * scale), fill=accent, width=w)
        draw.line((45 * scale, 19 * scale, 19 * scale, 45 * scale), fill=accent, width=w)
    elif kind in ("hostile", "warned"):
        draw.polygon(((32 * scale, 14 * scale), (51 * scale, 48 * scale), (13 * scale, 48 * scale)), outline=accent, fill=SURFACE_2)
        draw.line((32 * scale, 24 * scale, 32 * scale, 38 * scale), fill=TEXT, width=w)
        draw.ellipse((29 * scale, 41 * scale, 35 * scale, 47 * scale), fill=TEXT)
    elif kind in ("distrust", "recon"):
        draw.ellipse((14 * scale, 23 * scale, 50 * scale, 42 * scale), outline=accent, width=w)
        draw.ellipse((27 * scale, 26 * scale, 37 * scale, 39 * scale), fill=accent)
    elif kind in ("neutral", "cooldown"):
        draw.line((18 * scale, 32 * scale, 46 * scale, 32 * scale), fill=accent, width=4 * scale)
    elif kind in ("respect", "preparation"):
        draw.polygon(((16 * scale, 34 * scale), (27 * scale, 45 * scale), (49 * scale, 20 * scale)), outline=accent, fill=None)
        draw.line((16 * scale, 34 * scale, 27 * scale, 45 * scale, 49 * scale, 20 * scale), fill=accent, width=w)
    elif kind in ("alliance", "joint_defence"):
        draw.arc((14 * scale, 20 * scale, 38 * scale, 48 * scale), 210, 30, fill=accent, width=w)
        draw.arc((26 * scale, 20 * scale, 50 * scale, 48 * scale), 150, 330, fill=accent, width=w)
        draw.rectangle((25 * scale, 29 * scale, 39 * scale, 37 * scale), fill=accent)
    elif kind in ("special", "closed"):
        points = []
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            radius = 18 if i % 2 == 0 else 8
            points.append(((32 + math.cos(angle) * radius) * scale, (32 + math.sin(angle) * radius) * scale))
        draw.polygon(points, fill=accent, outline=TEXT)
    elif kind in ("planned", "truce"):
        draw.rectangle((17 * scale, 19 * scale, 47 * scale, 46 * scale), outline=accent, width=w)
        for y in (26, 33, 40):
            draw.line((23 * scale, y * scale, 41 * scale, y * scale), fill=MUTED, width=scale)
    elif kind in ("negotiation_window", "trade"):
        draw.line((16 * scale, 39 * scale, 29 * scale, 26 * scale, 37 * scale, 34 * scale, 48 * scale, 23 * scale), fill=accent, width=w)
        draw.polygon(((44 * scale, 18 * scale), (51 * scale, 20 * scale), (49 * scale, 27 * scale)), fill=MOLTEN_BRIGHT)
    elif kind in ("recovery", "tribute"):
        draw.arc((16 * scale, 16 * scale, 48 * scale, 48 * scale), 30, 310, fill=accent, width=w)
        draw.polygon(((42 * scale, 15 * scale), (51 * scale, 18 * scale), (47 * scale, 27 * scale)), fill=accent)
    else:
        draw.polygon(((32 * scale, 14 * scale), (48 * scale, 22 * scale), (45 * scale, 43 * scale), (32 * scale, 51 * scale), (19 * scale, 43 * scale), (16 * scale, 22 * scale)), outline=accent, fill=SURFACE_2)
        draw.line((24 * scale, 32 * scale, 40 * scale, 32 * scale), fill=MOLTEN_BRIGHT, width=w)
    return downsample(image, (size, size))


def button_texture(fill, border, highlight=None, size=(256, 20)) -> Image.Image:
    image, draw, scale = aa_canvas(size)
    draw.rounded_rectangle((scale, scale, size[0] * scale - scale - 1, size[1] * scale - scale - 1), radius=4 * scale, fill=fill, outline=border, width=scale)
    if highlight:
        draw.line((8 * scale, (size[1] - 3) * scale, (size[0] - 8) * scale, (size[1] - 3) * scale), fill=highlight, width=scale)
    return downsample(image, size, sharpen=False)


def panel_texture(size=(512, 512)) -> Image.Image:
    image, draw, scale = aa_canvas(size, scale=2)
    draw.rounded_rectangle((4 * scale, 4 * scale, (size[0] - 4) * scale, (size[1] - 4) * scale), radius=12 * scale, fill=(20, 24, 28, 232), outline=(74, 156, 199, 190), width=2 * scale)
    draw.line((24 * scale, 22 * scale, 160 * scale, 22 * scale), fill=MOLTEN, width=2 * scale)
    return downsample(image, size, sharpen=False)


def install_hero_assets() -> int:
    count = 0
    for name in ("logo.png", "background.png", "loading_frontier.png", "loading_works.png", "loading_launch.png", "mark.png", "icon_16.png", "icon_32.png"):
        source = GUI / name
        if not source.exists():
            raise FileNotFoundError(f"Missing approved M9 source asset: {source}")
        target = FM / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        count += 1
    return count


def main() -> int:
    products: dict[pathlib.Path, Image.Image] = {}

    for index, epoch in enumerate(EPOCHS):
        products[GUI / "icons" / "epochs" / f"{epoch}.png"] = draw_epoch_icon(index)

    for index, pathway in enumerate(PROCESS_PATHS):
        products[GUI / "icons" / "process" / f"{pathway}.png"] = draw_process_icon(pathway, index)

    for faction, accent in FACTIONS.items():
        faction_root = GUI / "factions" / faction
        products[faction_root / "emblem.png"] = draw_faction_emblem(faction, accent)
        products[faction_root / "silhouette.png"] = draw_silhouette(faction, accent)
        for level in range(7):
            products[faction_root / "bases" / f"b{level}.png"] = draw_base_icon(level, accent)

    for kind, accent in REPUTATION.items():
        products[GUI / "reputation" / f"{kind}.png"] = symbol_icon(kind, accent)

    for kind in TREATIES:
        products[GUI / "treaties" / f"{kind}.png"] = symbol_icon(kind, SUCCESS if kind in ("alliance", "joint_defence") else STEEL)

    operation_colors = {
        "planned": MUTED,
        "recon": (114, 202, 232, 255),
        "warned": WARNING,
        "negotiation_window": WARNING,
        "preparation": MOLTEN_BRIGHT,
        "active": DANGER,
        "recovery": STEEL,
        "cooldown": MUTED,
        "closed": SUCCESS,
    }
    for kind in OPERATIONS:
        products[GUI / "operations" / f"{kind}.png"] = symbol_icon(kind, operation_colors[kind])

    products[FM / "ui" / "button_normal.png"] = button_texture((30, 37, 43, 236), (74, 156, 199, 220))
    products[FM / "ui" / "button_hover.png"] = button_texture((38, 48, 56, 246), (255, 176, 92, 255), MOLTEN)
    products[FM / "ui" / "button_inactive.png"] = button_texture((25, 30, 34, 200), (82, 91, 98, 180))
    products[FM / "ui" / "panel.png"] = panel_texture()
    products[FM / "ui" / "loading_frame.png"] = button_texture((20, 24, 28, 230), (74, 156, 199, 255), MOLTEN, (1024, 18))

    for path, image in products.items():
        save(path, image)

    copied = install_hero_assets()
    menu_result = build_menu_visuals()
    if menu_result != 0:
        raise SystemExit("Recast v2 menu-visual build failed.")
    print(f"generated={len(products)} copied={copied} menu_v2=ready")
    for path in sorted(products, key=lambda item: str(item)):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
