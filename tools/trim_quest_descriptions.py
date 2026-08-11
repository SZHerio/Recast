"""Чистка описаний по новому редакторскому стандарту.

Стандарт от 10 августа 2026 года: сначала условие, описание — только если
условия мало. Прежняя редакция требовала девять полей на каждое задание, отсюда
1 159 знаков в среднем и канцелярит.

Здесь делается механическая половина работы: с заданий, которые объясняются
условием, снимаются лишние поля. Остаются заголовок, короткая подводка и текст
условия. Написание новых описаний там, где они нужны, — ручная работа, её
скрипт не делает и не изображает.

Описание сохраняется, если задание подходит хотя бы под один признак стандарта:

- роль operation, integration, automation или commissioning — там объясняется,
  что считается работающим;
- многоблочная установка: в тексте есть слои, ориентация или сборка;
- опасность: радиация, давление, взрыв, кислота;
- развилка: задание предлагает выбор.

Без --apply ничего не пишется.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "authoring" / "questbook_v2"

KEEP_ROLES = {"operation", "integration", "automation", "commissioning", "diagnostics", "recovery"}
KEEP_WORDS = re.compile(
    r"многоблоч|слой|слоя|ориентац|собер[иё]те корпус|радиац|давлени|взрыв|кислот|"
    r"перегрев|облучен|выбор|альтернатив|либо",
    re.I,
)
DROP_FIELDS = ("purpose_ru", "steps_ru", "success_ru", "diagnostics_ru", "next_ru")


def keeps_description(quest: dict) -> bool:
    if quest.get("role") in KEEP_ROLES:
        return True
    text = json.dumps(quest.get("text_ru", {}), ensure_ascii=False)
    return bool(KEEP_WORDS.search(text))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    kept = trimmed = 0
    before = after = 0

    for path in sorted(SRC.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for quest in document.get("quests", []):
            text = quest.get("text_ru", {})
            before += len(json.dumps(text, ensure_ascii=False))
            if keeps_description(quest):
                kept += 1
                after += len(json.dumps(text, ensure_ascii=False))
                continue
            for field in DROP_FIELDS:
                if field in text:
                    text.pop(field)
                    changed = True
            trimmed += 1
            after += len(json.dumps(text, ensure_ascii=False))
        if changed and args.apply:
            path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total = kept + trimmed
    print(f"заданий всего: {total}")
    print(f"  описание сохраняется: {kept}")
    print(f"  объясняется условием, поля сняты: {trimmed}")
    print(f"\nобъём текста: было {before // 1000} тыс. знаков, станет {after // 1000} тыс.")
    print(f"средняя длина: было {before // total}, станет {after // total}")
    if not args.apply:
        print("\nПРОБНЫЙ ПРОГОН: файлы не изменены")
    return 0


if __name__ == "__main__":
    sys.exit(main())
