#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фирменные изображения сборки: логотип, знак и иконка.

Рисуется программно, чтобы всё это можно было пересобрать в любой момент и
чтобы каждый цвет был взят из палитры, а не подобран на глаз.

Идея знака. Recast — это переплавка: сборка берёт готовые домены и отливает их
заново, одним стандартом. Отсюда шестиугольник (форма, в которой человек делает
всё, что должно держаться: гайка, слиток, ячейка) с косым разрезом и горячей
полосой в разрезе. Холодный металл снаружи, расплав внутри.

Палитра описана в docs/BRAND_STYLE_GUIDE.md и повторена здесь ровно один раз.

Запуск:
    python tools/generate_brand.py
"""

from __future__ import annotations

import pathlib
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "config" / "paxi" / "resourcepacks" / "IndustrialFrontier-Core" / "assets" / "industrial_frontier" / "textures" / "gui"

# Палитра. Остывший металл, горячий металл и холодная сталь.
COLD_DEEP = (20, 24, 28, 255)
COLD_SURFACE = (30, 37, 43, 255)
STEEL = (74, 156, 199, 255)
MOLTEN = (232, 121, 43, 255)
MOLTEN_BRIGHT = (255, 176, 92, 255)
TEXT = (230, 233, 236, 255)
TEXT_MUTED = (152, 162, 172, 255)

FONT_DIR = ROOT / "assets" / "fonts"
FONT_TITLE = FONT_DIR / "Lato-Black.ttf"
FONT_BODY = FONT_DIR / "Lato-Bold.ttf"


def load_font(path: pathlib.Path, size: int) -> ImageFont.FreeTypeFont:
    if not path.exists():
        raise SystemExit(f"Шрифт не найден: {path}")
    return ImageFont.truetype(str(path), size)


def hexagon(center: tuple[float, float], radius: float) -> list[tuple[float, float]]:
    """Правильный шестиугольник вершиной вверх."""
    import math

    return [
        (
            center[0] + radius * math.sin(math.radians(60 * index)),
            center[1] - radius * math.cos(math.radians(60 * index)),
        )
        for index in range(6)
    ]


def draw_mark(size: int) -> Image.Image:
    """Знак сборки: шестиугольник с косым разрезом и расплавом внутри."""
    scale = 4
    canvas = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    side = size * scale
    center = (side / 2, side / 2)
    outer = side * 0.44
    inner = outer * 0.70

    # Холодный корпус.
    draw.polygon(hexagon(center, outer), fill=COLD_SURFACE, outline=STEEL, width=max(2, side // 90))

    # Разрез: горячая полоса поперёк, шириной в треть знака.
    band = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    band_draw = ImageDraw.Draw(band)
    band_height = side * 0.13
    band_draw.rectangle(
        [0, center[1] - band_height / 2, side, center[1] + band_height / 2],
        fill=MOLTEN,
    )
    band_draw.rectangle(
        [0, center[1] - band_height / 6, side, center[1] + band_height / 6],
        fill=MOLTEN_BRIGHT,
    )
    band = band.rotate(-22, resample=Image.BICUBIC, center=center)

    # Полоса видна только внутри знака.
    mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(mask).polygon(hexagon(center, inner), fill=255)
    canvas = Image.alpha_composite(canvas, Image.composite(band, Image.new("RGBA", canvas.size, (0, 0, 0, 0)), mask))

    # Внутренняя грань, чтобы расплав читался как разрез, а не как наклейка.
    ImageDraw.Draw(canvas).polygon(hexagon(center, inner), outline=(90, 104, 116, 255), width=max(1, side // 200))

    return canvas.resize((size, size), Image.LANCZOS)


def draw_logo(width: int = 1024, height: int = 384) -> Image.Image:
    """Языконезависимый логотип: знак и название без запечённой подписи."""
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    mark_size = int(height * 0.62)
    source_mark = ROOT / "brand_source" / "1.png"
    if source_mark.exists():
        mark = Image.open(source_mark).convert("RGBA").resize((mark_size, mark_size), Image.LANCZOS)
        # У исходника тёмная подложка с виньеткой. На прозрачном логотипе она
        # читается как чёрный квадрат, поэтому края растушёвываются радиально:
        # знак остаётся, рамка исчезает.
        fade = Image.new("L", mark.size, 0)
        ImageDraw.Draw(fade).ellipse(
            [-mark_size * 0.04, -mark_size * 0.04, mark_size * 1.04, mark_size * 1.04], fill=255
        )
        mark.putalpha(fade.filter(ImageFilter.GaussianBlur(mark_size * 0.06)))
    else:
        mark = draw_mark(mark_size)
    mark_x = int(width * 0.06)
    mark_y = (height - mark_size) // 2
    canvas.alpha_composite(mark, (mark_x, mark_y))

    draw = ImageDraw.Draw(canvas)
    title_font = load_font(FONT_TITLE, int(height * 0.42))
    text_x = mark_x + mark_size + int(width * 0.045)
    title = "RECAST"

    # Горячая тень под названием: свет снизу, как от расплава.
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((text_x, int(height * 0.20) + 6), title, font=title_font, fill=(232, 121, 43, 150))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))

    draw.text((text_x, int(height * 0.20)), title, font=title_font, fill=TEXT)

    title_box = draw.textbbox((text_x, int(height * 0.20)), title, font=title_font)
    line_y = title_box[3] + int(height * 0.045)
    draw.rectangle([text_x, line_y, title_box[2], line_y + max(2, height // 130)], fill=MOLTEN)

    return canvas


def draw_pack_icon(size: int = 256) -> Image.Image:
    """Иконка сборки: знак на тёмном поле."""
    canvas = Image.new("RGBA", (size, size), COLD_DEEP)
    draw = ImageDraw.Draw(canvas)

    # Едва заметная сетка — намёк на чертёж, не отвлекающий от знака.
    step = size // 8
    for offset in range(step, size, step):
        draw.line([(offset, 0), (offset, size)], fill=(255, 255, 255, 10))
        draw.line([(0, offset), (size, offset)], fill=(255, 255, 255, 10))

    mark = draw_mark(int(size * 0.74))
    canvas.alpha_composite(mark, ((size - mark.width) // 2, (size - mark.height) // 2))
    return canvas


def draw_background(width: int = 1920, height: int = 1080) -> Image.Image:
    """Фон меню и загрузки: тёмное поле с горячим горизонтом."""
    canvas = Image.new("RGBA", (width, height), COLD_DEEP)
    draw = ImageDraw.Draw(canvas)

    # Вертикальный градиент к чуть более светлому низу.
    for y in range(height):
        ratio = y / height
        shade = (
            int(COLD_DEEP[0] + (COLD_SURFACE[0] - COLD_DEEP[0]) * ratio),
            int(COLD_DEEP[1] + (COLD_SURFACE[1] - COLD_DEEP[1]) * ratio),
            int(COLD_DEEP[2] + (COLD_SURFACE[2] - COLD_DEEP[2]) * ratio),
            255,
        )
        draw.line([(0, y), (width, y)], fill=shade)

    # Горячая линия горизонта: единственное тёплое пятно кадра.
    horizon = int(height * 0.72)
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rectangle([0, horizon, width, horizon + max(3, height // 240)], fill=(232, 121, 43, 190))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(height // 45)))
    ImageDraw.Draw(canvas).rectangle([0, horizon, width, horizon + max(2, height // 400)], fill=MOLTEN)

    return canvas


def draw_panorama_face(index: int, size: int = 1024) -> Image.Image:
    """Одна грань панорамы главного меню.

    Панорама — это куб из шести картинок, который игра медленно вращает за
    меню. Грани 0–3 смотрят по сторонам, 4 — вверх, 5 — вниз, поэтому линия
    горизонта на боковых гранях обязана совпадать, иначе стык виден.

    Сюжет один на все стороны: остывшая равнина, над ней полоса зарева, на
    горизонте силуэты труб и градирен. Ни одного узнаваемого мода — только то,
    чем сборка занимается.
    """
    import random

    canvas = Image.new("RGB", (size, size), COLD_DEEP[:3])
    draw = ImageDraw.Draw(canvas)
    horizon = int(size * 0.56)

    # Небо: от глубокого холода к тёплому у горизонта.
    for y in range(horizon):
        ratio = (y / horizon) ** 2.2
        draw.line(
            [(0, y), (size, y)],
            fill=(
                int(COLD_DEEP[0] + (196 - COLD_DEEP[0]) * ratio * 0.42),
                int(COLD_DEEP[1] + (104 - COLD_DEEP[1]) * ratio * 0.42),
                int(COLD_DEEP[2] + (46 - COLD_DEEP[2]) * ratio * 0.42),
            ),
        )

    # Земля: ровное тёмное поле, чуть светлее к низу.
    for y in range(horizon, size):
        ratio = (y - horizon) / max(1, size - horizon)
        draw.line([(0, y), (size, y)], fill=(int(14 + 10 * ratio), int(16 + 11 * ratio), int(19 + 12 * ratio)))

    if index < 4:
        # Силуэты промышленности. Зерно жёстко привязано к номеру грани,
        # поэтому панорама одинакова при каждой пересборке.
        rng = random.Random(4700 + index)
        for _ in range(rng.randint(7, 11)):
            width = rng.randint(int(size * 0.03), int(size * 0.09))
            height = rng.randint(int(size * 0.05), int(size * 0.20))
            left = rng.randint(-width, size)
            top = horizon - height
            draw.rectangle([left, top, left + width, horizon], fill=(11, 13, 16))
            # Труба с огоньком наверху: единственный тёплый акцент вдали.
            if rng.random() < 0.45:
                stack_width = max(3, width // 5)
                stack_x = left + width // 2 - stack_width // 2
                stack_top = top - rng.randint(int(size * 0.04), int(size * 0.12))
                draw.rectangle([stack_x, stack_top, stack_x + stack_width, top], fill=(11, 13, 16))
                draw.rectangle(
                    [stack_x, stack_top, stack_x + stack_width, stack_top + max(2, stack_width // 2)],
                    fill=MOLTEN[:3],
                )

        # Полоса зарева над горизонтом.
        glow = Image.new("RGB", canvas.size, (0, 0, 0))
        ImageDraw.Draw(glow).rectangle([0, horizon - size // 90, size, horizon], fill=(150, 74, 30))
        canvas = Image.blend(canvas, glow.filter(ImageFilter.GaussianBlur(size // 30)), 0.5)
    elif index == 4:
        # Небо над головой: ровный холод без зарева.
        canvas = Image.new("RGB", (size, size), (13, 16, 19))
    else:
        canvas = Image.new("RGB", (size, size), (16, 18, 21))

    return canvas


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    panorama_dir = (
        ROOT
        / "config"
        / "paxi"
        / "resourcepacks"
        / "IndustrialFrontier-Core"
        / "assets"
        / "minecraft"
        / "textures"
        / "gui"
        / "title"
        / "background"
    )

    # Знак, фон, панорама и иконка рисуются художником и раскладываются
    # инструментом install_brand_assets.py. Этот генератор их больше не
    # трогает: иначе запуск затёр бы присланные изображения нарисованными
    # фигурами. Здесь остаётся только то, чего у художника быть не может —
    # типографика поверх готового знака.
    accepted_lockup = ROOT / "brand_source" / "title_lockup_v2.png"
    if accepted_lockup.exists():
        source = Image.open(accepted_lockup).convert("RGBA")
        alpha_box = source.getchannel("A").getbbox()
        if alpha_box:
            source = source.crop(alpha_box)
        source.thumbnail((1512, 488), Image.Resampling.LANCZOS)
        logo = Image.new("RGBA", (1536, 512), (0, 0, 0, 0))
        logo.alpha_composite(source, ((logo.width - source.width) // 2, (logo.height - source.height) // 2))
    else:
        logo = draw_logo()
    products = {OUTPUT / "logo.png": logo}

    for path, image in products.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        print(f"{path.relative_to(ROOT)}: {image.width}x{image.height}")

    print(f"готово: {len(products)} изображения")
    return 0


if __name__ == "__main__":
    sys.exit(main())
