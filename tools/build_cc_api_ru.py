"""Build Russian ComputerCraft ROM API overrides from the pristine mod archive.

Only player-facing runtime messages are changed. API names, type identifiers,
event names, example code, paths, URLs and documentation comments stay intact.
"""

from __future__ import annotations

import pathlib
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
JAR = next((ROOT / "mods").glob("cc-tweaked-1.20.1-forge-*.jar"))
SOURCE_PREFIX = "data/computercraft/lua/rom/"
TARGET = (
    ROOT
    / "config/paxi/datapacks/IndustrialFrontier-Data/data/computercraft/lua/rom"
)

REPLACEMENTS: dict[str, dict[str, str]] = {
    "apis/colors.lua": {
        'error("Colour out of range", 2)':
            'error("Цвет вне допустимого диапазона", 2)',
    },
    "apis/command/commands.lua": {
        'error("Cannot load command API on normal computer", 2)':
            'error("API команд недоступен на обычном компьютере", 2)',
        'error("Expected string, number, boolean or table", 3)':
            'error("Ожидались строка, число, логическое значение или таблица", 3)',
        'return ("command %q"):format': 'return ("команда %q"):format',
    },
    "apis/disk.lua": {
        'error("bad argument #1 (string expected, got " .. type(name) .. ")", 3)':
            'error("неверный аргумент #1 (нужна строка, получен тип " .. type(name) .. ")", 3)',
    },
    "apis/fs.lua": {
        'error("/" .. pattern .. ": Invalid Path", 2)':
            'error("/" .. pattern .. ": недопустимый путь", 2)',
    },
    "apis/gps.lua": {
        'print("No wireless modem attached")':
            'print("Беспроводной модем не подключён")',
        'print("Finding position...")': 'print("Определение координат...")',
        'print(tFix.nDistance .. " metres from " .. tostring(tFix.vPosition))':
            'print(tFix.nDistance .. " бл. до " .. tostring(tFix.vPosition))',
        'print("Ambiguous position")': 'print("Координаты неоднозначны")',
        'print("Could be " .. pos1.x .. "," .. pos1.y .. "," .. pos1.z .. " or " .. pos2.x .. "," .. pos2.y .. "," .. pos2.z)':
            'print("Возможны координаты " .. pos1.x .. "," .. pos1.y .. "," .. pos1.z .. " или " .. pos2.x .. "," .. pos2.y .. "," .. pos2.z)',
        'print("Position is " .. pos1.x .. "," .. pos1.y .. "," .. pos1.z)':
            'print("Координаты: " .. pos1.x .. "," .. pos1.y .. "," .. pos1.z)',
        'print("Could not determine position")':
            'print("Не удалось определить координаты")',
    },
    "apis/http/http.lua": {
        'error(("bad field \'%s\' (%s expected, got %s"):format(key, ty, valueTy), 4)':
            'error(("неверное поле «%s» (ожидался тип %s, получен тип %s)"):format(key, ty, valueTy), 4)',
        'error("Unsupported HTTP method", 3)':
            'error("Неподдерживаемый метод HTTP", 3)',
    },
    "apis/io.lua": {
        'return "file (closed)"': 'return "файл (закрыт)"',
        'return "file (" .. hash .. ")"': 'return "файл (" .. hash .. ")"',
        'error("bad argument #1 (FILE expected, got " .. type_of(self) .. ")", 2)':
            'error("неверный аргумент #1 (ожидался FILE, получен тип " .. type_of(self) .. ")", 2)',
        'error("attempt to use a closed file", 2)':
            'error("попытка обратиться к закрытому файлу", 2)',
        'return nil, "attempt to close standard stream"':
            'return nil, "нельзя закрыть стандартный поток"',
        'return nil, "file is not readable"':
            'return nil, "файл недоступен для чтения"',
        'error("file is already closed", 2)':
            'error("файл уже закрыт", 2)',
        'return nil, "Not opened for reading"':
            'return nil, "файл не открыт для чтения"',
        'error("bad argument #" .. i .. " (invalid format)", 2)':
            'error("неверный аргумент #" .. i .. " (недопустимый формат)", 2)',
        'error("bad argument #" .. i .. " (string expected, got " .. type_of(arg) .. ")", 2)':
            'error("неверный аргумент #" .. i .. " (нужна строка, получен тип " .. type_of(arg) .. ")", 2)',
        'return nil, "file is not seekable"':
            'return nil, "файл не поддерживает перемещение указателя"',
        'return nil, "file is not writable"':
            'return nil, "файл недоступен для записи"',
        'error("bad argument #1 (FILE expected, got " .. type_of(file) .. ")", 2)':
            'error("неверный аргумент #1 (ожидался FILE, получен тип " .. type_of(file) .. ")", 2)',
        'error("bad fileument #1 (FILE expected, got " .. type_of(file) .. ")", 2)':
            'error("неверный аргумент #1 (ожидался FILE, получен тип " .. type_of(file) .. ")", 2)',
    },
    "apis/parallel.lua": {
        'error("Cannot spawn new functions outside of waitForAll", 2)':
            'error("Нельзя запускать новые функции вне waitForAll", 2)',
    },
    "apis/peripheral.lua": {
        'error("bad argument #1 (table is not a peripheral)", 2)':
            'error("неверный аргумент #1 (таблица не является периферией)", 2)',
    },
    "apis/rednet.lua": {
        'error("No such modem: " .. modem, 2)':
            'error("Модем не найден: " .. modem, 2)',
        'error("Reserved hostname", 2)':
            'error("Это имя узла зарезервировано", 2)',
        'error("Hostname in use", 2)':
            'error("Имя узла уже используется", 2)',
        'error("rednet is already running", 2)':
            'error("rednet уже запущен", 2)',
    },
}


with zipfile.ZipFile(JAR) as archive:
    for relative, replacements in REPLACEMENTS.items():
        source = archive.read(SOURCE_PREFIX + relative).decode("utf-8")
        translated = source
        for old, new in replacements.items():
            count = translated.count(old)
            if count == 0:
                raise RuntimeError(f"Missing source text in {relative}: {old!r}")
            translated = translated.replace(old, new)
        destination = TARGET / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(translated, encoding="utf-8", newline="\n")
        print(f"{relative}: {len(replacements)} replacements")
