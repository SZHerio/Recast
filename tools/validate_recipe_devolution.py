"""Страж линии передачи рецептов машинам.

Проверяет docs/registries/recipe_devolution.json против книги заданий:

1. снятый рецепт не относится к предмету, который книга требует раньше эпохи
   снятия — иначе игрок упрётся в стену;
2. каждая заявленная стадия ссылается на существующий скрипт;
3. каждое снятие, объявленное в реестре, действительно присутствует в скрипте;
4. исключения bootstrap имеют причину и механизм.

Minecraft не запускается: читаются только файлы профиля.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "docs" / "registries" / "recipe_devolution.json"
SOURCE = ROOT / "authoring" / "questbook_v2"

EPOCH_ORDER = {"ONBOARDING": -1, **{f"P{i}": i for i in range(10)}}
LATE = 99  # SYSTEMS и REFERENCE не привязаны к эпохе прохождения


def epoch_rank(name: str) -> int:
    return EPOCH_ORDER.get(name, LATE)


def first_demand() -> dict[str, str]:
    """Эпоха, в которой книга впервые требует предмет или тег."""
    first: dict[str, str] = {}
    for path in sorted(SOURCE.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for quest in document.get("quests", []):
            epoch = quest["epoch"]
            for proof in quest.get("proofs", []):
                ids = []
                if "item" in proof:
                    ids.append(proof["item"]["id"])
                if "item_tag" in proof:
                    ids.append("#" + proof["item_tag"]["id"])
                for item in ids:
                    if item not in first or epoch_rank(epoch) < epoch_rank(first[item]):
                        first[item] = epoch
    return first


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    demand = first_demand()

    for exception in registry.get("bootstrap_exceptions", []):
        if not exception.get("reason_ru") or not exception.get("mechanism"):
            errors.append(f"Исключение {exception.get('id')} без причины или механизма.")

    implemented = 0
    planned = 0
    for stage in registry.get("stages", []):
        epoch = stage["epoch"]
        status = stage["status"]
        if status == "PLANNED":
            planned += 1
            continue
        implemented += 1

        script = stage.get("script")
        if not script:
            errors.append(f"{epoch}: стадия реализована, но скрипт не указан.")
            continue
        script_path = ROOT / script
        if not script_path.exists():
            errors.append(f"{epoch}: скрипт не найден: {script}")
            continue
        body = script_path.read_text(encoding="utf-8")

        for removal in stage.get("removals", []):
            output = removal["output"]
            if f"'{output}'" not in body and f'"{output}"' not in body:
                errors.append(f"{epoch}: снятие {output} объявлено в реестре, но отсутствует в скрипте.")

            demanded = demand.get(output)
            if demanded is None:
                continue
            if epoch_rank(demanded) < epoch_rank(epoch):
                errors.append(
                    f"{epoch}: книга требует {output} уже в {demanded} — снятие раньше владельца оставит игрока без пути."
                )
            elif epoch_rank(demanded) == epoch_rank(epoch):
                warnings.append(
                    f"{epoch}: книга требует {output} в той же эпохе; путь через машину обязан открываться раньше квеста."
                )

    # Владелец операции назначается один раз: результат не может принадлежать
    # двум стадиям, иначе поздняя машина обесценит раннюю фабрику.
    seen_owner: dict[str, str] = {}
    for stage in registry.get("stages", []):
        for removal in stage.get("removals", []):
            output = removal["output"]
            if output in seen_owner:
                errors.append(
                    f"{stage['epoch']}: у {output} уже есть владелец из {seen_owner[output]} — "
                    "второй рецепт того же результата обесценивает раннюю линию."
                )
            else:
                seen_owner[output] = stage["epoch"]

    # Снятия в скриптах, не объявленные в реестре: линия должна быть полной.
    declared = {
        removal["output"]
        for stage in registry.get("stages", [])
        for removal in stage.get("removals", [])
    }
    for stage in registry.get("stages", []):
        script = stage.get("script")
        if not script or not (ROOT / script).exists():
            continue
        body = (ROOT / script).read_text(encoding="utf-8")
        for found in re.findall(r"output:\s*'([a-z0-9_.:-]+)'", body):
            if found not in declared and not found.startswith("create:"):
                warnings.append(f"{stage['epoch']}: снятие {found} есть в скрипте, но не объявлено в реестре.")

    for line in warnings:
        print(f"WARN  {line}")
    for line in errors:
        print(f"ERROR {line}")
    print(
        f"recipe devolution: стадий реализовано {implemented}, запланировано {planned}; "
        f"ошибок {len(errors)}, предупреждений {len(warnings)}"
    )
    print("Minecraft не запускался; изменялись только файлы профиля.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
