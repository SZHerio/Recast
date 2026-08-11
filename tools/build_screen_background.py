#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тайл фона ванильных экранов: тёмный бетон вместо земли.

Экраны настроек и выбора мира рисуют `textures/gui/options_background.png`
плиткой с объявленным размером 32x32 и умножают цвет на 0.25 — то же самое, что
делает ваниль со своей землёй (134,96,67 на диске превращаются в (34,24,17) на
экране). Поэтому плитку приходится рисовать вчетверо светлее нужного результата.

Плитка повторяется по ширине экрана шесть десятков раз, и любой заметный рисунок
превратился бы в сетку. Отсюда выбор: ровный тон и очень мелкое зерно с
размахом в единицы уровней. На экране это читается как бетон, а не как узор.
"""
from __future__ import annotations

import pathlib
import sys

import numpy
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = (
    ROOT
    / "config/paxi/resourcepacks/IndustrialFrontier-Core/assets/minecraft/textures/gui/options_background.png"
)

TILE = 32
# Затемнение, которое накладывает игра.
GAME_TINT = 0.25
# Каким бетон должен выглядеть уже на экране.
ON_SCREEN = (27, 29, 32)
# Размах зерна на экране, в уровнях яркости.
GRAIN_ON_SCREEN = 2.6
SEED = 20260811


def main() -> int:
    generator = numpy.random.default_rng(SEED)

    base = numpy.array(ON_SCREEN, dtype=numpy.float64) / GAME_TINT
    grain = generator.normal(0.0, GRAIN_ON_SCREEN / GAME_TINT, size=(TILE, TILE, 1))
    # Редкие тёмные крупинки: бетон не бывает идеально ровным.
    speckle = (generator.random((TILE, TILE, 1)) > 0.94) * (-14.0 / GAME_TINT)

    pixels = numpy.clip(base + grain + speckle, 0.0, 255.0).round().astype(numpy.uint8)
    image = Image.fromarray(pixels, mode="RGB")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    image.save(TARGET, format="PNG", optimize=True)

    preview = numpy.clip(pixels.astype(numpy.float64) * GAME_TINT, 0, 255).astype(numpy.uint8)
    print(f"записано: {TARGET.relative_to(ROOT).as_posix()}  {TILE}x{TILE} RGB")
    print(f"на диске  средний цвет: {tuple(int(v) for v in pixels.reshape(-1, 3).mean(axis=0).round())}")
    print(f"на экране средний цвет: {tuple(int(v) for v in preview.reshape(-1, 3).mean(axis=0).round())}")
    print("Minecraft не запускался.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
