#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный перевод строк мода по словарю.

Каждый мод переводится одинаково: берётся его английский файл языка, к нему
прикладывается словарь `authoring/lang/<namespace>.json`, результат кладётся в
оверлей ресурспака сборки.

Словарь — обычная пара «английский ключ: русская строка». Пишется руками, по
частям; чего в словаре нет, то не переводится и остаётся английским, а счётчик
показывает остаток. Выдуманных строк инструмент не создаёт.

Ключи, которых нет в самом моде, отбрасываются с предупреждением: перевод,
которого мод не спрашивал, — такой же дефект, как отсутствующий, и аудит его
ловит.

Редкое исключение — видимый legacy-ключ, который upstream оставил только в
ru_ru. Такие записи кладутся в явно названный фрагмент
`authoring/fragments/<namespace>_ru_only.json`; обычные фрагменты по-прежнему
обязаны совпадать с en_us.

Запуск:
    python tools/translate_mod.py <namespace> [маска jar]
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
PACK = ROOT / "config" / "paxi" / "resourcepacks" / "IndustrialFrontier-Core" / "assets"
FRAGMENTS = ROOT / "authoring" / "fragments"


def english(namespace: str, mask: str | None) -> dict[str, str]:
    pattern = mask or f"*{namespace}*"
    for path in glob.glob(str(ROOT / "mods" / f"{pattern}.jar")):
        archive = zipfile.ZipFile(path)
        target = f"assets/{namespace}/lang/en_us.json"
        if target in archive.namelist():
            return json.loads(archive.read(target).decode("utf-8-sig"))
    raise SystemExit(f"Не найден английский файл языка для {namespace}")


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("Укажите namespace мода.")
    namespace = sys.argv[1]
    mask = sys.argv[2] if len(sys.argv) > 2 else None

    source = english(namespace, mask)
    dictionary_path = ROOT / "authoring" / "lang" / f"{namespace}.json"
    dictionary = {}
    if dictionary_path.exists():
        with io.open(dictionary_path, encoding="utf-8") as handle:
            dictionary = json.load(handle)

    fragment_paths = sorted(FRAGMENTS.glob(f"{namespace}_*.json"))
    # Некоторые моды содержат видимые legacy-ключи только в своём ru_ru,
    # хотя en_us их не объявляет. Фрагмент *_ru_only.json фиксирует такой
    # намеренный оверлей явно, не ослабляя проверку обычных словарей.
    ru_only_keys: set[str] = set()
    for fragment_path in fragment_paths:
        with io.open(fragment_path, encoding="utf-8") as handle:
            fragment = json.load(handle)
        if fragment_path.stem.endswith("_ru_only"):
            ru_only_keys.update(fragment)
        for key, value in fragment.items():
            if key in dictionary and dictionary[key] != value:
                raise SystemExit(
                    f"Конфликт перевода {key}: {dictionary_path.name} и {fragment_path.name}"
                )
            dictionary[key] = value

    translated = {}
    invented = []
    for key, value in dictionary.items():
        if key not in source and key not in ru_only_keys:
            invented.append(key)
            continue
        if value:
            translated[key] = value

    output = PACK / namespace / "lang" / "ru_ru.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    io.open(output, "w", encoding="utf-8", newline="\n").write(
        json.dumps({k: translated[k] for k in sorted(translated)}, ensure_ascii=False, indent=2) + "\n"
    )

    missing = [k for k in source if k not in translated]
    source_translated = sum(key in source for key in translated)
    active_ru_only = sum(key in translated for key in ru_only_keys)
    print(f"{namespace}: переведено {source_translated} из {len(source)}, осталось {len(missing)}")
    if active_ru_only:
        print(f"  дополнительно ru-only legacy-ключей: {active_ru_only}")
    if fragment_paths:
        print(f"  подключено фрагментов: {len(fragment_paths)}")
    if invented:
        print(f"  ВНИМАНИЕ: в словаре {len(invented)} ключей, которых нет в моде — они отброшены")
        for key in invented[:5]:
            print(f"    {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
