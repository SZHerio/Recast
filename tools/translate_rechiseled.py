#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Перевод названий блоков Rechiseled.

Мод даёт 3656 строк, и переводить их по одной бессмысленно: за ними стоит 640
уникальных основ вида «Acacia Plank Beams», каждая из которых встречается ещё в
виде плиты, ступеней и бесшовного варианта.

Поэтому работа разделена надвое. Основы переводит человек и складывает в
словарь `authoring/lang/rechiseled_base.json`. Формы приставляет этот скрипт по
русским правилам: плита и ступени требуют родительного падежа, поэтому в
словаре у каждой основы две формы — именительная и родительная.

    "Acacia Plank Beams": ["Акациевые доски с балками", "акациевых досок с балками"]

Из этой пары получаются все четыре строки:

    Акациевые доски с балками
    Плита из акациевых досок с балками
    Ступени из акациевых досок с балками
    Акациевые доски с балками — бесшовный вариант

Непереведённые основы скрипт не выдумывает: он пропускает их и сообщает,
сколько осталось. Строка, которой нет в русском файле, показывается игроку
по-английски — это честнее машинного перевода.

Запуск:
    python tools/translate_rechiseled.py
"""

from __future__ import annotations

import glob
import io
import json
import pathlib
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
DICTIONARY = ROOT / "authoring" / "lang" / "rechiseled_base.json"
OUTPUT = (
    ROOT
    / "config"
    / "paxi"
    / "resourcepacks"
    / "IndustrialFrontier-Core"
    / "assets"
    / "rechiseled"
    / "lang"
    / "ru_ru.json"
)

# Строки интерфейса самого мода — их мало, они переведены здесь же.
INTERFACE = {
    "rechiseled.item_group": "Резьба по блокам",
    "rechiseled.tooltip.connecting": "Бесшовный",
    "rechiseled.chiseling.preview.mode_0": "Показ: один блок",
    "rechiseled.chiseling.preview.mode_1": "Показ: три в ряд",
    "rechiseled.chiseling.preview.mode_2": "Показ: три на три",
    "rechiseled.chiseling.connecting": "Связанные текстуры: %s",
    "rechiseled.chiseling.connecting.on": "включены",
    "rechiseled.chiseling.connecting.off": "выключены",
    "rechiseled.chiseling.chisel_all": "Обработать всё",
    "rechiseled.chiseling.chisel_all.shift": "%s — для всех форм",
    "rechiseled.chiseling.chisel_all.items": "%s предметов",
    "rechiseled.chiseling.select_block": "Выбрать: %s",
    "rechiseled.chiseling.preview": "Предпросмотр блока",
    "rechiseled.chiseling.select_shape": "Форма: %s",
    "rechiseled.chiseling.filter": "Отбор",
    "rechiseled.chiseling.filter.clear": "Правый клик — сбросить",
    "rechiseled.chiseling.filter.show_blocks": "показывать блоки",
    "rechiseled.chiseling.filter.show_stairs": "показывать ступени",
    "rechiseled.chiseling.filter.show_slabs": "показывать плиты",
    "rechiseled.chiseling.filter.show_non_connecting": "показывать несоединяемые",
    "rechiseled.chiseling.scrollbar": "Полоса прокрутки",
    "rechiseled.chiseling.entry.recipe": "Рецепт: %s",
    "rechiseled.chiseling.entry.owner": "Дополнение: %s",
    "rechiseled.recipe_category.title": "Резьба",
    "rechiseled.recipe_category.conversion_value": "Курс обмена: %s",
    "rechiseled.chiseling.shape.block": "Блок",
    "rechiseled.chiseling.shape.stairs": "Ступени",
    "rechiseled.chiseling.shape.slab": "Плита",
    "rechiseled.item.chisel": "Резец",
}


def english_names() -> dict[str, str]:
    jars = glob.glob(str(ROOT / "mods" / "rechiseled-*.jar"))
    if not jars:
        raise SystemExit("Мод Rechiseled не найден в mods.")
    archive = zipfile.ZipFile(jars[0])
    name = [item for item in archive.namelist() if item.endswith("lang/en_us.json")][0]
    return json.loads(archive.read(name).decode("utf-8-sig"))


def split_name(value: str) -> tuple[str, str, bool]:
    """Название → основа, форма и признак бесшовности."""
    connecting = value.startswith("Connecting ")
    if connecting:
        value = value[len("Connecting ") :]
    for suffix, form in ((" Slab", "slab"), (" Stairs", "stairs")):
        if value.endswith(suffix):
            return value[: -len(suffix)], form, connecting
    return value, "block", connecting


def load_dictionary() -> dict[str, list[str]]:
    if not DICTIONARY.exists():
        return {}
    with io.open(DICTIONARY, encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    source = english_names()
    dictionary = load_dictionary()

    bases: dict[str, None] = {}
    translated: dict[str, str] = dict(INTERFACE)
    missing: dict[str, None] = {}

    for key, value in source.items():
        # Названия приходят двумя наборами: block.rechiseled.* для мира и
        # rechiseled.block.* для окна резца. Текст в них одинаковый, поэтому
        # оба переводятся одним словарём.
        if not (key.startswith("block.rechiseled.") or key.startswith("rechiseled.block.")):
            continue
        base, form, connecting = split_name(str(value))
        bases[base] = None

        pair = dictionary.get(base)
        if not pair or len(pair) != 2 or not all(pair):
            missing[base] = None
            continue

        # Часть основ приходит из словаря со строчной буквы — они там записаны
        # так, чтобы годиться и в середину названия. В самостоятельном имени
        # блока первая буква обязана быть заглавной.
        nominative = pair[0]
        nominative = nominative[0].upper() + nominative[1:] if nominative else nominative
        # Форма приписывается в скобках, а не оборотом «плита из…».
        # Названия здесь и так содержат «из»: «балки из багровых досок».
        # Второе «из» подряд по-русски не читается — «плита из балок из
        # багровых досок», — поэтому форма выносится в скобку.
        if form == "slab":
            name = f"{nominative} (плита)"
        elif form == "stairs":
            name = f"{nominative} (ступени)"
        else:
            name = nominative
        if connecting:
            name = f"{name} — бесшовный вариант"
        translated[key] = name

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUTPUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps({k: translated[k] for k in sorted(translated)}, ensure_ascii=False, indent=2) + "\n"
    )

    # Заготовка словаря: непереведённые основы выписываются пустыми парами,
    # чтобы их было видно и можно было заполнять частями.
    if missing:
        draft = dict(dictionary)
        for base in missing:
            draft.setdefault(base, ["", ""])
        DICTIONARY.parent.mkdir(parents=True, exist_ok=True)
        io.open(DICTIONARY, "w", encoding="utf-8", newline="\n").write(
            json.dumps({k: draft[k] for k in sorted(draft)}, ensure_ascii=False, indent=2) + "\n"
        )

    done = len(bases) - len(missing)
    print(f"основ всего: {len(bases)}   переведено: {done}   осталось: {len(missing)}")
    print(f"строк записано в ru_ru.json: {len(translated)} из {len(source)}")
    print(f"словарь: {DICTIONARY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
