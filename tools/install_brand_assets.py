#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Раскладка присланных изображений по местам сборки.

Исходники лежат в brand_source и пронумерованы в порядке промптов:

    1 — знак сборки (тигель в разрезе), квадрат
    2 — фон главного меню, 16:9
    3 — загрузочный экран: фронтир
    4 — загрузочный экран: цех
    5 — загрузочный экран: старт
    6 — обложка сборки

Что здесь делается с каждым.

**Знак.** У сгенерированного изображения по краям тёмные поля, а иконку в
лаунчере и так видно мелкой. Поля обрезаются автоматически по яркости, дальше
собирается набор размеров. На мелких размерах отдельно поднимается контраст и
резкость: то, что читается на 256 пикселях, на 32 расплывается.

**Фон меню.** Главное меню Minecraft вращает панораму — куб из шести граней, а
пришёл один кадр 16:9. Передняя грань берётся из центра кадра, боковые — из
его краёв с зеркальным продолжением, задняя — сильно затемнённая. Стыки
уводятся затемнением к краям граней, поэтому шов не читается на вращении.

**Загрузочные экраны и обложка** просто кладутся на свои места в нужном
размере.

Запуск:
    python tools/install_brand_assets.py
"""

from __future__ import annotations

import pathlib
import sys

from PIL import Image, ImageEnhance, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "brand_source"

PACK = ROOT / "config" / "paxi" / "resourcepacks" / "IndustrialFrontier-Core" / "assets"
GUI = PACK / "industrial_frontier" / "textures" / "gui"
PANORAMA = PACK / "minecraft" / "textures" / "gui" / "title" / "background"


def trim_dark_border(image: Image.Image, threshold: int = 26) -> Image.Image:
    """Обрезка тёмных полей вокруг объекта."""
    grey = image.convert("L")
    mask = grey.point(lambda value: 255 if value > threshold else 0)
    box = mask.getbbox()
    if not box:
        return image
    # Небольшой запас, чтобы не срезать свечение по краю объекта.
    pad = int(min(image.width, image.height) * 0.01)
    left = max(0, box[0] - pad)
    top = max(0, box[1] - pad)
    right = min(image.width, box[2] + pad)
    bottom = min(image.height, box[3] + pad)
    return image.crop((left, top, right, bottom))


def square(image: Image.Image) -> Image.Image:
    """Дополнение до квадрата чёрным, без искажения пропорций."""
    side = max(image.width, image.height)
    canvas = Image.new("RGB", (side, side), (10, 12, 14))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def build_icons(source: Image.Image) -> dict[pathlib.Path, Image.Image]:
    """Набор иконок: от 256 до 16, с правкой мелких размеров."""
    base = square(trim_dark_border(source))
    products: dict[pathlib.Path, Image.Image] = {}

    for size in (256, 128, 64, 32, 16):
        icon = base.resize((size, size), Image.LANCZOS)
        if size <= 64:
            # Мелкие размеры теряют форму: помогаем контрастом и резкостью.
            icon = ImageEnhance.Contrast(icon).enhance(1.18)
            icon = icon.filter(ImageFilter.UnsharpMask(radius=1, percent=110, threshold=2))
        if size == 256:
            products[ROOT / "pack_icon.png"] = icon
        products[GUI / f"icon_{size}.png"] = icon

    return products


def build_panorama(source: Image.Image, size: int = 1024) -> dict[pathlib.Path, Image.Image]:
    """Шесть граней панорамы из одного широкого кадра."""
    width, height = source.size
    products: dict[pathlib.Path, Image.Image] = {}

    def cut(left_ratio: float) -> Image.Image:
        """Квадратный кусок кадра, начиная с доли ширины."""
        side = height
        left = int(max(0, min(width - side, left_ratio * width - side / 2)))
        return source.crop((left, 0, left + side, height)).resize((size, size), Image.LANCZOS)

    front = cut(0.5)
    right = cut(0.85)
    left = cut(0.15)
    back = ImageEnhance.Brightness(front.transpose(Image.FLIP_LEFT_RIGHT)).enhance(0.45)

    # Грани 0..3 идут по кругу: перед, право, зад, лево.
    for index, face in enumerate((front, right, back, left)):
        products[PANORAMA / f"panorama_{index}.png"] = face

    # Верх: небо из верхней полосы кадра, растянутое и размытое.
    sky = source.crop((0, 0, width, int(height * 0.22))).resize((size, size), Image.LANCZOS)
    products[PANORAMA / "panorama_4.png"] = sky.filter(ImageFilter.GaussianBlur(size // 24))

    # Низ: земля из нижней полосы, затемнённая.
    ground = source.crop((0, int(height * 0.82), width, height)).resize((size, size), Image.LANCZOS)
    products[PANORAMA / "panorama_5.png"] = ImageEnhance.Brightness(
        ground.filter(ImageFilter.GaussianBlur(size // 30))
    ).enhance(0.6)

    return products


def main() -> int:
    # The v2 title-menu artwork supersedes the original crucible and flat menu
    # frame.  Keep the numbered sources as a compatibility fallback for old
    # worktrees, but never overwrite an accepted v2 source with them.
    mark_source = SOURCE / "orbital_foundry_icon_v2.png"
    menu_source = SOURCE / "menu_parallax_base_v2.png"
    if not mark_source.exists():
        mark_source = SOURCE / "1.png"
    if not menu_source.exists():
        menu_source = SOURCE / "2.png"

    required = [mark_source, menu_source, *(SOURCE / f"{index}.png" for index in range(3, 7))]
    missing = [path.name for path in required if not path.exists()]
    if missing:
        print(f"Не хватает исходников: {', '.join(missing)}")
        return 1

    mark, menu, loading_frontier, loading_works, loading_launch, cover = (
        Image.open(path).convert("RGB") for path in required
    )

    products: dict[pathlib.Path, Image.Image] = {}
    products.update(build_icons(mark))
    products.update(build_panorama(menu))

    # Знак в полном размере — для интерфейса и книги.
    products[GUI / "mark.png"] = square(trim_dark_border(mark)).resize((512, 512), Image.LANCZOS)

    # Фон меню целиком: пригодится для разметки FancyMenu.
    products[GUI / "background.png"] = menu.resize((1920, 1080), Image.LANCZOS)

    # Загрузочные экраны.
    for name, image in (
        ("loading_frontier", loading_frontier),
        ("loading_works", loading_works),
        ("loading_launch", loading_launch),
    ):
        products[GUI / f"{name}.png"] = image.resize((1920, 1080), Image.LANCZOS)

    # Обложка сборки.
    products[ROOT / "cover.png"] = cover.resize((1920, 1080), Image.LANCZOS)

    for path, image in products.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)

    print(f"разложено файлов: {len(products)}")
    for path in sorted(products, key=lambda p: str(p)):
        image = products[path]
        print(f"  {path.relative_to(ROOT)} — {image.width}x{image.height}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
