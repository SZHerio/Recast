#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Recast title-menu image set without launching Minecraft.

The accepted AI artwork lives in ``brand_source``.  This script performs only
deterministic delivery work: 16:9 framing, alpha-preserving resize, size-specific
window icons, compact nine-slice UI textures and static composition previews.
"""

from __future__ import annotations

import pathlib
import sys
import time

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "brand_source"
PACK = ROOT / "config" / "paxi" / "resourcepacks" / "IndustrialFrontier-Core" / "assets"
GUI = PACK / "industrial_frontier" / "textures" / "gui"
FM = ROOT / "config" / "fancymenu" / "assets"
PREVIEW = ROOT / "docs" / "visual_previews"

BASE_SOURCE = SOURCE / "menu_parallax_base_v2.png"
MID_SOURCE = SOURCE / "menu_parallax_mid_v2.png"
NEAR_SOURCE = SOURCE / "menu_parallax_near_v2.png"
LOGO_SOURCE = SOURCE / "title_lockup_orbital_foundry_v3.png"
ICON_SOURCE = SOURCE / "orbital_foundry_mark_v3.png"

DEEP = (20, 24, 28, 255)
SURFACE = (30, 37, 43, 232)
SURFACE_HOVER = (38, 48, 56, 246)
STEEL = (74, 156, 199, 224)
STEEL_BRIGHT = (129, 196, 226, 255)
MOLTEN = (232, 121, 43, 255)
MOLTEN_BRIGHT = (255, 176, 92, 255)
TEXT = (230, 233, 236, 255)
MUTED = (112, 123, 132, 190)

# Строгий набор: заливки без цвета, выделение — белизной рамки.
BUTTON_NORMAL = (26, 30, 35, 236)
BUTTON_HOVER = (44, 50, 58, 247)
BUTTON_INACTIVE = (20, 23, 27, 206)
EDGE_NORMAL = (255, 255, 255, 42)
EDGE_HOVER = (255, 255, 255, 232)
EDGE_INACTIVE = (255, 255, 255, 18)
PANEL_FILL = (14, 17, 21, 232)
PANEL_EDGE = (255, 255, 255, 30)

RESAMPLE = Image.Resampling.LANCZOS
REFERENCE_SIZE = (854, 480)
BACKGROUND_PARALLAX = (0.025, 0.014)


def require_sources() -> None:
    missing = [path.relative_to(ROOT).as_posix() for path in (BASE_SOURCE, MID_SOURCE, NEAR_SOURCE, LOGO_SOURCE, ICON_SOURCE) if not path.is_file()]
    if missing:
        raise SystemExit("Missing accepted menu source artwork: " + ", ".join(missing))


def save(image: Image.Image, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.recast-build.tmp")
    image.save(temporary, format="PNG", optimize=True)
    for attempt in range(5):
        try:
            temporary.replace(path)
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(0.1)


def fit_16_9(image: Image.Image, size: tuple[int, int] = (2048, 1152)) -> Image.Image:
    return ImageOps.fit(image, size, method=RESAMPLE, centering=(0.5, 0.5))


def place_contain(image: Image.Image, size: tuple[int, int], padding: int = 0) -> Image.Image:
    target = Image.new("RGBA", size, (0, 0, 0, 0))
    usable = (max(1, size[0] - padding * 2), max(1, size[1] - padding * 2))
    fitted = ImageOps.contain(image, usable, method=RESAMPLE)
    target.alpha_composite(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return target


def crop_alpha(image: Image.Image, padding_ratio: float = 0.02) -> Image.Image:
    rgba = image.convert("RGBA")
    box = rgba.getchannel("A").getbbox()
    if not box:
        return rgba
    pad = max(2, round(max(rgba.size) * padding_ratio))
    return rgba.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(rgba.width, box[2] + pad), min(rgba.height, box[3] + pad)))


def aa_texture(size: tuple[int, int], painter, scale: int = 4) -> Image.Image:
    canvas = Image.new("RGBA", (size[0] * scale, size[1] * scale), (0, 0, 0, 0))
    painter(ImageDraw.Draw(canvas), scale)
    return canvas.resize(size, RESAMPLE)


def nine_slice_resize(
    image: Image.Image,
    size: tuple[int, int],
    source_border: tuple[int, int],
    destination_border: tuple[int, int],
) -> Image.Image:
    """Resize a nine-slice texture while preserving its corners and rails."""
    source = image.convert("RGBA")
    target = Image.new("RGBA", size, (0, 0, 0, 0))
    sx = (0, source_border[0], source.width - source_border[0], source.width)
    sy = (0, source_border[1], source.height - source_border[1], source.height)
    dx = (0, destination_border[0], size[0] - destination_border[0], size[0])
    dy = (0, destination_border[1], size[1] - destination_border[1], size[1])
    for row in range(3):
        for column in range(3):
            crop = source.crop((sx[column], sy[row], sx[column + 1], sy[row + 1]))
            cell_size = (dx[column + 1] - dx[column], dy[row + 1] - dy[row])
            if crop.size != cell_size:
                crop = crop.resize(cell_size, RESAMPLE)
            target.alpha_composite(crop, (dx[column], dy[row]))
    return target


def _flat_surface(state: str) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    """Заливка и рамка для строгого состояния кнопки."""
    if state == "hover":
        return BUTTON_HOVER, EDGE_HOVER
    if state == "inactive":
        return BUTTON_INACTIVE, EDGE_INACTIVE
    return BUTTON_NORMAL, EDGE_NORMAL


def button_texture(state: str, size: tuple[int, int] = (48, 24)) -> Image.Image:
    # Строгая кнопка ванильной формы: прямоугольник, сплошная тёмная заливка и
    # рамка в один пиксель. Выделение — белизна рамки, а не цвет: при наведении
    # она разгорается почти до белого. Скошенные углы, вертикальные засечки и
    # подчёркивания убраны — именно из-за них меню выглядело перегруженным.
    #
    # Координаты кратны множителю сглаживания, поэтому после уменьшения рамка
    # остаётся ровно в один пиксель и не размывается.
    def paint(draw: ImageDraw.ImageDraw, scale: int) -> None:
        fill, border = _flat_surface(state)
        draw.rectangle(
            [(0, 0), (size[0] * scale - 1, size[1] * scale - 1)],
            fill=fill,
            outline=border,
            width=scale,
        )

    return aa_texture(size, paint)


def icon_button_texture(state: str, size: tuple[int, int] = (24, 24)) -> Image.Image:
    def paint(draw: ImageDraw.ImageDraw, scale: int) -> None:
        fill, border = _flat_surface(state)
        draw.rectangle(
            [(0, 0), (size[0] * scale - 1, size[1] * scale - 1)],
            fill=fill,
            outline=border,
            width=scale,
        )

    return aa_texture(size, paint)


def panel_texture(size: tuple[int, int] = (96, 96)) -> Image.Image:
    # Панель держит текст на пёстром пейзаже и больше ничего не делает: ровная
    # тёмная подложка и тонкая рамка. Акцентные линии и скошенные углы сняты.
    def paint(draw: ImageDraw.ImageDraw, scale: int) -> None:
        draw.rectangle(
            [(0, 0), (size[0] * scale - 1, size[1] * scale - 1)],
            fill=PANEL_FILL,
            outline=PANEL_EDGE,
            width=scale,
        )

    return aa_texture(size, paint)


def processed_icon(source: Image.Image, size: int) -> Image.Image:
    # Keep the generated emblem's alpha and smooth vector-like edges at every
    # Windows-requested size. Nearest-neighbour pixel art looked jagged on
    # high-DPI taskbars and destroyed the steel/orbit silhouette.
    icon = ImageOps.fit(source.convert("RGBA"), (size, size), method=RESAMPLE)
    if size <= 64:
        icon = ImageEnhance.Contrast(icon).enhance(1.16)
        icon = icon.filter(ImageFilter.UnsharpMask(radius=max(0.5, size / 48), percent=125, threshold=2))
    return icon


def build_brand_products() -> tuple[dict[pathlib.Path, Image.Image], Image.Image]:
    """Build only the lockup, mark and icon delivery chain.

    This intentionally stays separate from the broad menu build so an approved
    identity update cannot rewrite the background, button or panel artwork.
    """
    logo = place_contain(crop_alpha(Image.open(LOGO_SOURCE)), (1536, 512), padding=12)
    icon_source = Image.open(ICON_SOURCE).convert("RGBA")
    products: dict[pathlib.Path, Image.Image] = {
        GUI / "logo.png": logo,
        GUI / "mark.png": processed_icon(icon_source, 512),
        FM / "logo.png": logo,
        FM / "mark.png": processed_icon(icon_source, 512),
    }

    for size in (256, 128, 64, 32, 16):
        icon = processed_icon(icon_source, size)
        products[GUI / f"icon_{size}.png"] = icon
        if size in (16, 32):
            products[FM / f"icon_{size}.png"] = icon
        if size == 256:
            products[ROOT / "pack_icon.png"] = icon

    return products, logo


def build_preview(
    base: Image.Image,
    mid: Image.Image,
    near: Image.Image,
    logo: Image.Image,
    panel: Image.Image,
    buttons: dict[str, Image.Image],
    compact: dict[str, Image.Image],
    *,
    size: tuple[int, int] = (1920, 1080),
    cursor: tuple[float, float] = (0.0, 0.0),
) -> Image.Image:
    width, height = size
    # FancyMenu's image-background parallax grows one always-present composite
    # before shifting it. Unlike separate image elements, this background
    # remains the screen background while F11 rebuilds the title screen.
    parallax_x, parallax_y = BACKGROUND_PARALLAX
    expanded_size = (
        round(width * (1.0 + parallax_x)),
        round(height * (1.0 + parallax_y)),
    )
    expanded = ImageOps.fit(base, expanded_size, method=RESAMPLE).convert("RGBA")
    offset_x = round(-cursor[0] * width * parallax_x / 2.0)
    offset_y = round(-cursor[1] * height * parallax_y / 2.0)
    origin = (
        (width - expanded.width) // 2 + offset_x,
        (height - expanded.height) // 2 + offset_y,
    )
    scene = Image.new("RGBA", size, DEEP)
    scene.alpha_composite(expanded, origin)

    scale_x, scale_y = width / REFERENCE_SIZE[0], height / REFERENCE_SIZE[1]
    # Mid/near source planes remain archived. Runtime movement belongs only to
    # the composite menu_background, so no decorative element can blink alone.

    panel_box = (round(16 * scale_x), round(16 * scale_y), round(294 * scale_x), round(400 * scale_y))
    panel_scaled = nine_slice_resize(
        panel,
        (panel_box[2], panel_box[3]),
        (12, 12),
        (round(12 * scale_x), round(12 * scale_y)),
    )
    scene.alpha_composite(panel_scaled, (panel_box[0], panel_box[1]))

    logo_scaled = logo.resize((round(258 * scale_x), round(86 * scale_y)), RESAMPLE)
    scene.alpha_composite(logo_scaled, (round(28 * scale_x), round(27 * scale_y)))

    font_path = ROOT / "assets" / "fonts" / "Lato-Bold.ttf"
    font_size = max(8, round(7.1 * scale_y))
    small_font_size = max(7, round(5.4 * scale_y))
    font = ImageFont.truetype(str(font_path), font_size) if font_path.is_file() else ImageFont.load_default()
    small_font = ImageFont.truetype(str(font_path), small_font_size) if font_path.is_file() else ImageFont.load_default()
    draw = ImageDraw.Draw(scene)
    draw.text((round(35 * scale_x), round(118 * scale_y)), "ИНДУСТРИЯ · ГОРОДА · КОСМОС", font=font, fill=TEXT)

    def draw_button(label: str, x: int, y: int, logical_width: int, state: str = "normal") -> None:
        position = (round(x * scale_x), round(y * scale_y))
        button_size = (round(logical_width * scale_x), round(24 * scale_y))
        background = nine_slice_resize(
            buttons[state],
            button_size,
            (6, 6),
            (round(6 * scale_x), round(6 * scale_y)),
        )
        scene.alpha_composite(background, position)
        box = draw.textbbox((0, 0), label, font=font)
        draw.text(
            (
                position[0] + (background.width - (box[2] - box[0])) // 2,
                position[1] + (background.height - (box[3] - box[1])) // 2 - box[1],
            ),
            label,
            font=font,
            fill=TEXT,
        )

    labels = ["ОДИНОЧНАЯ ИГРА", "СЕТЕВАЯ ИГРА", "МОДИФИКАЦИИ", "НАСТРОЙКИ", "ВЫЙТИ ИЗ ИГРЫ"]
    for index, label in enumerate(labels):
        draw_button(label, 34, 140 + index * 28, 226)

    draw_button("О СБОРКЕ", 34, 286, 109)
    draw_button("АВТОРЫ", 151, 286, 109)
    draw_button("ЧТО НОВОГО", 34, 314, 226)

    for x, glyph in ((34, "RU"), (62, "A")):
        position = (round(x * scale_x), round(346 * scale_y))
        compact_size = (round(24 * scale_x), round(24 * scale_y))
        background = nine_slice_resize(
            compact["normal"],
            compact_size,
            (6, 6),
            (round(6 * scale_x), round(6 * scale_y)),
        )
        scene.alpha_composite(background, position)
        box = draw.textbbox((0, 0), glyph, font=small_font)
        draw.text(
            (position[0] + (background.width - (box[2] - box[0])) // 2, position[1] + (background.height - (box[3] - box[1])) // 2 - box[1]),
            glyph,
            font=small_font,
            fill=TEXT,
        )

    draw.text((round(94 * scale_x), round(353 * scale_y)), "ЯЗЫК · ДОСТУПНОСТЬ", font=small_font, fill=(190, 205, 216, 255))
    draw.text((round(34 * scale_x), round(394 * scale_y)), "RECAST · FORGE 1.20.1", font=small_font, fill=(152, 162, 172, 255))
    return scene.convert("RGB")


def build_extremes_preview(
    base: Image.Image,
    mid: Image.Image,
    near: Image.Image,
    logo: Image.Image,
    panel: Image.Image,
    buttons: dict[str, Image.Image],
    compact: dict[str, Image.Image],
) -> Image.Image:
    sheet = Image.new("RGB", (1920, 1080), DEEP[:3])
    states = [((-1.0, -1.0), "КУРСОР · ЛЕВЫЙ ВЕРХ"), ((1.0, -1.0), "КУРСОР · ПРАВЫЙ ВЕРХ"), ((-1.0, 1.0), "КУРСОР · ЛЕВЫЙ НИЗ"), ((1.0, 1.0), "КУРСОР · ПРАВЫЙ НИЗ")]
    label_font_path = ROOT / "assets" / "fonts" / "Lato-Bold.ttf"
    label_font = ImageFont.truetype(str(label_font_path), 18) if label_font_path.is_file() else ImageFont.load_default()
    for index, (cursor, label) in enumerate(states):
        frame = build_preview(base, mid, near, logo, panel, buttons, compact, size=(960, 540), cursor=cursor)
        x, y = (index % 2) * 960, (index // 2) * 540
        sheet.paste(frame, (x, y))
        draw = ImageDraw.Draw(sheet)
        box = draw.textbbox((0, 0), label, font=label_font)
        label_x, label_y = x + 955 - (box[2] - box[0]), y + 8
        draw.rounded_rectangle((label_x - 10, label_y - 4, x + 958, label_y + 26), radius=5, fill=(10, 14, 18, 220))
        draw.text((label_x, label_y), label, font=label_font, fill=TEXT)
    return sheet


def build_button_states_preview(buttons: dict[str, Image.Image], compact: dict[str, Image.Image]) -> Image.Image:
    sheet = Image.new("RGB", (1280, 480), DEEP[:3])
    draw = ImageDraw.Draw(sheet)
    font_path = ROOT / "assets" / "fonts" / "Lato-Bold.ttf"
    title_font = ImageFont.truetype(str(font_path), 28) if font_path.is_file() else ImageFont.load_default()
    font = ImageFont.truetype(str(font_path), 22) if font_path.is_file() else ImageFont.load_default()
    small_font = ImageFont.truetype(str(font_path), 18) if font_path.is_file() else ImageFont.load_default()
    draw.text((48, 28), "RECAST · СОСТОЯНИЯ КНОПОК", font=title_font, fill=TEXT)
    draw.text((48, 68), "Nine-slice: углы и направляющие сохраняют геометрию", font=small_font, fill=(152, 162, 172))

    labels = {"normal": "ОБЫЧНОЕ", "hover": "НАВЕДЕНИЕ", "inactive": "НЕАКТИВНО"}
    for index, state in enumerate(("normal", "hover", "inactive")):
        y = 116 + index * 112
        large = nine_slice_resize(buttons[state], (678, 72), (6, 6), (18, 18))
        sheet.paste(large, (48, y), large)
        box = draw.textbbox((0, 0), labels[state], font=font)
        draw.text((48 + (678 - (box[2] - box[0])) // 2, y + (72 - (box[3] - box[1])) // 2 - box[1]), labels[state], font=font, fill=TEXT)

        compact_button = nine_slice_resize(compact[state], (72, 72), (6, 6), (18, 18))
        sheet.paste(compact_button, (790, y), compact_button)
        glyph = "A"
        glyph_box = draw.textbbox((0, 0), glyph, font=font)
        draw.text((790 + (72 - (glyph_box[2] - glyph_box[0])) // 2, y + (72 - (glyph_box[3] - glyph_box[1])) // 2 - glyph_box[1]), glyph, font=font, fill=TEXT)
        draw.text((888, y + 23), labels[state], font=small_font, fill=(190, 205, 216))
    return sheet


def build_loading_preview(logo: Image.Image, panel: Image.Image) -> Image.Image:
    """Render the compact Drippy layout against the real frontier frame."""
    background = Image.open(FM / "loading_frontier.png").convert("RGBA")
    scene = ImageOps.fit(background, (1920, 1080), method=RESAMPLE)
    scale_x, scale_y = 1920 / REFERENCE_SIZE[0], 1080 / REFERENCE_SIZE[1]

    logo_size = (round(260 * scale_x), round(87 * scale_y))
    logo_image = logo.resize(logo_size, RESAMPLE)
    scene.alpha_composite(logo_image, ((1920 - logo_size[0]) // 2, round(18 * scale_y)))

    panel_size = (round(520 * scale_x), round(96 * scale_y))
    panel_image = nine_slice_resize(panel, panel_size, (12, 12), (round(12 * scale_x), round(12 * scale_y)))
    panel_x = (1920 - panel_size[0]) // 2
    panel_y = 1080 - round(116 * scale_y)
    scene.alpha_composite(panel_image, (panel_x, panel_y))

    font_path = ROOT / "assets" / "fonts" / "Lato-Bold.ttf"
    title_font = ImageFont.truetype(str(font_path), 25) if font_path.is_file() else ImageFont.load_default()
    body_font = ImageFont.truetype(str(font_path), 19) if font_path.is_file() else ImageFont.load_default()
    small_font = ImageFont.truetype(str(font_path), 16) if font_path.is_file() else ImageFont.load_default()
    draw = ImageDraw.Draw(scene)
    text_x = panel_x + round(28 * scale_x)
    draw.text((text_x, 1080 - round(103 * scale_y)), "ФРОНТИР НАЧИНАЕТСЯ С НАДЁЖНОГО ЛАГЕРЯ", font=title_font, fill=TEXT)
    draw.text(
        (text_x, 1080 - round(82 * scale_y)),
        "Сначала обеспечьте воду, пищу, кров и карту района.\nМашины не исправят поселение без снабжения.",
        font=body_font,
        fill=TEXT,
        spacing=3,
    )

    frame = Image.open(FM / "ui" / "loading_frame.png").convert("RGBA")
    frame_size = (round(468 * scale_x), round(16 * scale_y))
    frame_image = frame.resize(frame_size, RESAMPLE)
    frame_x = (1920 - frame_size[0]) // 2
    frame_y = 1080 - round(46 * scale_y)
    scene.alpha_composite(frame_image, (frame_x, frame_y))
    bar_x = (1920 - round(452 * scale_x)) // 2
    bar_y = 1080 - round(42 * scale_y)
    bar_width = round(452 * scale_x * 0.68)
    draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + round(6 * scale_y)), fill=MOLTEN)
    draw.text((bar_x, 1080 - round(31 * scale_y)), "Собираем производственные цепочки", font=small_font, fill=TEXT)
    draw.text((bar_x + round(402 * scale_x), 1080 - round(31 * scale_y)), "68%", font=small_font, fill=TEXT)
    return scene.convert("RGB")


def main() -> int:
    require_sources()

    brand_only = "--brand-only" in sys.argv[1:]
    brand_products, logo = build_brand_products()
    if brand_only:
        for path, image in brand_products.items():
            save(image, path)
        print(f"brand_visuals={len(brand_products)}")
        for path in sorted(brand_products, key=lambda value: value.as_posix()):
            with Image.open(path) as image:
                print(f"  {path.relative_to(ROOT).as_posix()} {image.width}x{image.height} {image.mode}")
        return 0

    base = fit_16_9(Image.open(BASE_SOURCE).convert("RGB"))
    mid = fit_16_9(Image.open(MID_SOURCE).convert("RGBA"))
    near = fit_16_9(Image.open(NEAR_SOURCE).convert("RGBA"))

    products: dict[pathlib.Path, Image.Image] = {
        GUI / "menu" / "base.png": base,
        GUI / "menu" / "mid.png": mid,
        GUI / "menu" / "near.png": near,
        GUI / "background.png": base.resize((1920, 1080), RESAMPLE),
        FM / "menu" / "base.png": base,
        FM / "menu" / "mid.png": mid,
        FM / "menu" / "near.png": near,
        FM / "background.png": base.resize((1920, 1080), RESAMPLE),
    }
    products.update(brand_products)

    buttons = {state: button_texture(state) for state in ("normal", "hover", "inactive")}
    compact = {state: icon_button_texture(state) for state in ("normal", "hover", "inactive")}
    panel = panel_texture()
    for state, image in buttons.items():
        products[FM / "ui" / f"button_{state}.png"] = image
    for state, image in compact.items():
        products[FM / "ui" / f"icon_button_{state}.png"] = image
    products[FM / "ui" / "panel.png"] = panel

    for path, image in products.items():
        save(image, path)

    preview = build_preview(base, mid, near, logo, panel, buttons, compact)
    save(preview, PREVIEW / "recast_title_v2_center.png")
    extremes_preview = build_extremes_preview(base, mid, near, logo, panel, buttons, compact)
    save(extremes_preview, PREVIEW / "recast_title_v2_cursor_extremes.png")
    button_states_preview = build_button_states_preview(buttons, compact)
    save(button_states_preview, PREVIEW / "recast_title_v2_button_states.png")

    loading_preview = build_loading_preview(logo, panel)
    save(loading_preview, PREVIEW / "recast_loading_frontier_compact.png")

    print(f"menu_visuals={len(products)} previews=4")
    for path in sorted(products, key=lambda value: value.as_posix()):
        with Image.open(path) as image:
            print(f"  {path.relative_to(ROOT).as_posix()} {image.width}x{image.height} {image.mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
