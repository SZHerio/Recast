#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ветвление цепочек там, где в сборке есть настоящий выбор.

Каждая глава была прямой ниткой: одно задание, одна зависимость, и так до
конца. Но сборка устроена иначе. В пятой эпохе рельсы, вода и ME-сеть — это три
разных способа возить, а не три ступени одной лестницы. В шестой топливо,
реактор и защита идут параллельно: пока обогащается уран, реактор уже строится.

Прямая нитка врала об этом и заодно растягивала главу вширь. Здесь связи
приводятся к тому, как всё работает на самом деле: ветки расходятся после
общего вступления и сходятся в задании, которое их сравнивает.

Ветвления заданы явной таблицей, а не угаданы: у каждой строки есть причина,
записанная рядом.

Запуск:
    python tools/apply_quest_branches.py
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "config" / "ftbquests" / "quests" / "chapters"

# Глава -> задание -> от чего оно зависит внутри главы.
# Пустой список означает начало ветки: задание висит прямо на вступлении.
BRANCHES = {
    "13_p3_electrification": {
        # Редстоун-сигнал не требует генератора: это отдельный разговор,
        # который можно вести параллельно с электричеством.
        "signal": ["intro"],
        "generator": ["intro"],
        "cable": ["generator"],
        "line": ["cable"],
        "buffer": ["line"],
        "machine": ["line", "signal"],
        "bridge": ["machine"],
        "exit": ["bridge", "buffer"],
    },
    "15_p5_regional_logistics": {
        # Три способа возить расходятся сразу и сравниваются в «balance».
        "freight_rail": ["intro"],
        "water_route": ["intro"],
        "ae2_entry": ["intro"],
        "transit_line": ["freight_rail"],
        "last_mile": ["transit_line", "water_route"],
        "ae2_channels": ["ae2_entry"],
        "ae2_patterns": ["ae2_channels"],
        "ae2_autocraft": ["ae2_patterns"],
        "ae2_recovery": ["ae2_autocraft"],
        "balance": ["last_mile", "ae2_recovery"],
        "bulk_processing": ["balance"],
        "reserve": ["bulk_processing"],
        "contracts": ["reserve"],
    },
    "16_p6_nuclear": {
        # Топливная цепочка, реакторная линия и дозиметрия идут параллельно:
        # пока обогащается уран, реактор уже строится, а защита нужна раньше
        # обоих.
        "entry": ["intro"],
        "dosimetry": ["intro"],
        "materials": ["entry"],
        "alloys": ["materials"],
        "enrichment": ["entry"],
        "isotopes": ["enrichment"],
        "purification": ["isotopes"],
        "fuel": ["purification"],
        "reactor": ["alloys", "dosimetry"],
        "heat_loop": ["reactor"],
        "turbine": ["heat_loop"],
        "spent_fuel": ["fuel"],
        "city_plant": ["turbine", "spent_fuel"],
    },
}


def quest_slug_map(text: str, chapter_key: str) -> dict[str, str]:
    """Соответствие «имя задания -> идентификатор».

    Имя видно в языковых ключах описания, поэтому его не нужно угадывать.
    """
    mapping = {}
    for match in re.finditer(r"^\t\t\{\n(.*?)^\t\t\}", text, re.M | re.S):
        body = match.group(1)
        found = re.search(r'^\t\t\tid: "(3\d{15})"', body, re.M)
        slug = re.search(r"industrial_frontier\.quest\." + chapter_key + r"\.([a-z0-9_]+)\.", body)
        if found and slug:
            mapping[slug.group(1)] = found.group(1)
    return mapping


def chapter_key(name: str) -> str:
    """Ключ главы в языковых строках: 13_p3_electrification -> p3."""
    parts = name.split("_")
    return parts[1] if len(parts) > 1 else name


def set_dependencies(text: str, quest_id: str, dependency_ids: list[str], own_ids: set[str]) -> str:
    """Переписать связи задания, сохранив только ворота главы.

    Старые связи внутри главы обязаны исчезнуть: если оставить и их, и новые,
    цепочка замкнётся сама на себя и раскладка уедет в бесконечность.
    Сохраняется лишь ссылка на другую главу — это ворота, их ставит отдельный
    инструмент.
    """
    pattern = re.compile(r"(^\t\t\{\n)((?:(?!^\t\t\}).)*?id: \"" + quest_id + r"\".*?)(^\t\t\})", re.M | re.S)
    match = pattern.search(text)
    if not match:
        return text

    body = match.group(2)
    external = []
    for block in re.finditer(r"dependencies: \[(.*?)\]", body, re.S):
        external.extend(item for item in re.findall(r'"(3\d{15})"', block.group(1)) if item not in own_ids)

    body = re.sub(r"^\t\t\tdependencies: \[[^\]]*\]\n", "", body, flags=re.M | re.S)

    combined = list(dict.fromkeys(list(dependency_ids) + [e for e in external if e not in dependency_ids]))
    if combined:
        if len(combined) == 1:
            block = f'\t\t\tdependencies: ["{combined[0]}"]\n'
        else:
            inner = "".join(f'\t\t\t\t"{item}"\n' for item in combined)
            block = f"\t\t\tdependencies: [\n{inner}\t\t\t]\n"
        body = block + body

    return text[: match.start()] + match.group(1) + body + match.group(3) + text[match.end() :]


def main() -> int:
    changed = 0
    for chapter_name, plan in BRANCHES.items():
        path = CHAPTERS / f"{chapter_name}.snbt"
        if not path.exists():
            print(f"ПРОПУЩЕНО: нет главы {chapter_name}")
            continue

        text = path.read_text(encoding="utf-8")
        key = chapter_key(chapter_name)
        slugs = quest_slug_map(text, key)

        missing = [slug for slug in plan if slug not in slugs]
        if missing:
            print(f"ОШИБКА в {chapter_name}: не найдены задания {missing}")
            return 1

        own = set(slugs.values())
        for slug, deps in plan.items():
            quest_id = slugs[slug]
            dependency_ids = [slugs[d] for d in deps]
            # Внешние зависимости — это ворота главы, они остаются.
            text = set_dependencies(text, quest_id, dependency_ids, own)

        # Проверка: ни одно задание не должно зависеть само от себя.
        for slug, quest_id in slugs.items():
            if quest_id in [slugs[d] for d in plan.get(slug, [])]:
                print(f"ОШИБКА: {chapter_name}/{slug} зависит от себя")
                return 1

        path.write_text(text, encoding="utf-8", newline="\n")
        changed += 1
        widths = {}
        for slug, deps in plan.items():
            widths[len(deps)] = widths.get(len(deps), 0) + 1
        print(f"{chapter_name}: ветвление задано для {len(plan)} заданий")

    print(f"готово: изменено глав {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
