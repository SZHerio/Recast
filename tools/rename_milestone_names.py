"""Снятие следов волн разработки M0–M11 с имён файлов и ссылок.

Версия полная, и хроника разработки в названиях ей не нужна. Операция
неразрывна: переименование без одновременной правки ссылок ломает сборку —
валидаторы ищут схемы по маскам, реестры ссылаются друг на друга путями,
трассировки перечисляют файлы поимённо, KubeJS грузит скрипты по названиям.

Поэтому скрипт делает всё за один проход: строит карту, переименовывает,
переписывает ссылки и сообщает о столкновениях. Без --apply не пишет ничего.

Порядок загрузки KubeJS зависит от имени файла, поэтому в его каталогах
числовой префикс сохраняется — меняется только буква волны.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Работаем только в авторских каталогах. Чужие ресурсы трогать нельзя: в TaCZ,
# например, лежат звуки винтовки M95, и они не имеют отношения к волнам работ.
WORK_DIRS = ("authoring", "docs", "kubejs", "tools", "config/paxi")
# Архив этапов переименованию не подлежит: имя волны и есть его содержание.
SKIP_DIRS = {".git", "build", "logs", "saves", "mods", "backups", "crash-reports",
             "disabled_mods", "downloads", "resourcepacks", "shaderpacks", ".uv-cache",
             "libraries", "tmp", "local", "history"}
SKIP_PARTS = {"probe", "__pycache__", "exported"}
TEXT_SUFFIXES = {".py", ".ps1", ".js", ".json", ".jsonc", ".md", ".snbt", ".txt", ".toml", ".yaml", ".yml"}

# m85 -> 85, m8.5 -> 85: волна теряет букву, порядок остаётся.
STAGE_RE = re.compile(r"^m(\d{1,2})(?:[._](\d))?_", re.I)


def walkable(path: pathlib.Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    if not any(relative.startswith(folder + "/") for folder in WORK_DIRS):
        return False
    parts = set(p.lower() for p in path.relative_to(ROOT).parts)
    return not (parts & SKIP_DIRS) and not (parts & SKIP_PARTS)


def new_name(name: str, keep_order: bool) -> str | None:
    match = STAGE_RE.match(name)
    if not match:
        return None
    rest = name[match.end():]
    if keep_order:
        # KubeJS грузит по алфавиту: сохраняем двузначный порядок.
        major = int(match.group(1))
        minor = match.group(2) or ""
        return f"{major:02d}{minor}_{rest}"
    return rest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    mapping: dict[pathlib.Path, pathlib.Path] = {}
    collisions: list[tuple[str, str]] = []

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or not walkable(path):
            continue
        keep_order = "kubejs" in {p.lower() for p in path.relative_to(ROOT).parts}
        renamed = new_name(path.name, keep_order)
        if not renamed or renamed == path.name:
            continue
        target = path.with_name(renamed)
        if target.exists() or target in mapping.values():
            # Столкновение: несколько волн дали файлы с одинаковым смыслом
            # (m2_trace, m3_trace…). Номер сохраняем как порядковый, буква волны
            # уходит — так остаётся и различимость, и чистота имени.
            match = STAGE_RE.match(path.name)
            ordered = f"{int(match.group(1)):02d}_{renamed}"
            target = path.with_name(ordered)
            if target.exists() or target in mapping.values():
                collisions.append((str(path.relative_to(ROOT)), ordered))
                continue
        mapping[path] = target

    print(f"файлов под переименование: {len(mapping)}")
    print(f"столкновений имён: {len(collisions)}")
    for source, renamed in collisions[:15]:
        print(f"    {source} -> {renamed}")

    by_dir = collections.Counter(str(p.parent.relative_to(ROOT)) for p in mapping)
    print("\nпо каталогам:")
    for folder, count in by_dir.most_common(12):
        print(f"    {folder or '.':46} {count}")

    print("\nпримеры:")
    for source, target in list(mapping.items())[:10]:
        print(f"    {source.name:44} -> {target.name}")

    if not args.apply:
        print("\nПРОБНЫЙ ПРОГОН: ничего не изменено")
        return 0

    renames = {source.name: target.name for source, target in mapping.items()}

    # 1. Переименование.
    for source, target in mapping.items():
        source.rename(target)

    # 2. Правка ссылок во всех текстовых файлах профиля.
    touched = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or not walkable(path) or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for old, new in renames.items():
            if old in text:
                text = text.replace(old, new)
        # Маски вида 02_*.schema.json тоже теряют букву волны.
        text = re.sub(r"\bm(\d{1,2})_\*", lambda m: f"{int(m.group(1)):02d}_*", text)
        if text != original:
            path.write_text(text, encoding="utf-8")
            touched += 1

    print(f"\nпереименовано файлов: {len(mapping)}")
    print(f"поправлено файлов со ссылками: {touched}")
    print("Minecraft не запускался.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
