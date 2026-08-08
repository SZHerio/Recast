"""Build the Russian ComputerCraft syntax-diagnostic override.

Lua keywords and token/type names intentionally remain unchanged so that every
hint still refers to the exact text the player must type.
"""

from __future__ import annotations

import pathlib
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
JAR = next((ROOT / "mods").glob("cc-tweaked-1.20.1-forge-*.jar"))
RELATIVE = "modules/main/cc/internal/syntax/errors.lua"
SOURCE = "data/computercraft/lua/rom/" + RELATIVE
TARGET = (
    ROOT
    / "config/paxi/datapacks/IndustrialFrontier-Data/data/computercraft/lua/rom"
    / RELATIVE
)

# These are complete Lua string literals, not loose prose, which prevents
# changes to source comments or identifiers with similar words.
REPLACEMENTS = [
    ('"This string is not finished. Are you missing a closing quote ("',
     '"Строка не завершена. Возможно, пропущена закрывающая кавычка ("'),
    ('"String started here."', '"Строка начинается здесь."'),
    ('"Expected a closing quote here."', '"Здесь ожидалась закрывающая кавычка."'),
    ('"This string is not finished."', '"Строка не завершена."'),
    ('"An escape sequence was started here, but with nothing following it."',
     '"Здесь начинается экранирующая последовательность, но после неё ничего нет."'),
    ('"This string was never finished."', '"Строка так и не была завершена."'),
    ('"String was started here."', '"Строка началась здесь."'),
    ('"We expected a closing delimiter ("',
     '"Далее ожидался закрывающий разделитель ("'),
    ('") somewhere after this string was started."', '")."'),
    ('"Incorrect start of a long string."', '"Неверное начало длинной строки."'),
    ('"Tip: If you wanted to start a long string here, add an extra "',
     '"Подсказка: чтобы начать здесь длинную строку, добавьте ещё одну "'),
    ('code("[") .. " here."', 'code("[") .. "."'),
    ('" cannot be nested inside another "', '" нельзя вкладывать в другую конструкцию "'),
    ('"This isn\'t a valid number."', '"Это недопустимое число."'),
    ('"Numbers must be in one of the following formats: "',
     '"Число нужно записать в одном из следующих форматов: "'),
    ('"This comment was never finished."', '"Комментарий так и не был завершён."'),
    ('"Comment was started here."', '"Комментарий начался здесь."'),
    ('") somewhere after this comment was started."', '")."'),
    ('"Unexpected character."', '"Недопустимый символ."'),
    ('"Tip: Replace this with "', '"Подсказка: замените этот символ на "'),
    ('" to check if both values are true."',
     '" для проверки истинности обоих значений."'),
    ('" to check if either value is true."',
     '" для проверки истинности хотя бы одного значения."'),
    ('" to check if two values are not equal."',
     '" для проверки неравенства двух значений."'),
    ('" to negate a boolean."', '" для отрицания логического значения."'),
    ('"This character isn\'t usable in Lua code."',
     '"Этот символ нельзя использовать в коде Lua."'),
    ('"Unexpected "', '"Неожиданный токен "'),
    ('". Expected an expression."', '". Ожидалось выражение."'),
    ('". Expected a variable name."', '". Ожидалось имя переменной."'),
    ('" in expression."', '" в выражении."'),
    ('" to check if two values are equal."',
     '" для проверки равенства двух значений."'),
    ('"Tip: Wrap the preceding expression in "',
     '"Подсказка: заключите предыдущее выражение в "'),
    ('" to use it as a table key."',
     '" — тогда его можно будет использовать как ключ таблицы."'),
    ('" in table."', '" в таблице."'),
    ('"Are you missing a comma here?"', '"Возможно, здесь пропущена запятая?"'),
    ('" in function call."', '" при вызове функции."'),
    ('"Tip: Try removing this "', '"Подсказка: попробуйте убрать "'),
    ('". Expected a statement."', '". Ожидалась инструкция."'),
    ('". Expected "', '". Ожидался токен "'),
    ('"Cannot use "', '"Нельзя использовать "'),
    ('" with a table key."', '" с ключом таблицы."'),
    ('" appears here."', '" находится здесь."'),
    ('"Tip: "', '"Подсказка: "'),
    ('"Try removing this "', '"попробуйте убрать "'),
    ('" keyword."', '"."'),
    ('" after name."', '" после имени."'),
    ('"Did you mean to assign this or call it as a function?"',
     '"Вы хотели присвоить этому значение или вызвать как функцию?"'),
    ('"Did you mean to assign this?"', '"Вы хотели присвоить этому значение?"'),
    ('"Expected something before the end of the line."',
     '"Перед концом строки ожидалось выражение."'),
    ('"Tip: Use "', '"Подсказка: используйте "'),
    ('" to call with no arguments."', '" для вызова без аргументов."'),
    ('"Expected "', '"Ожидался токен "'),
    ('" and "', '" и "'),
    ('" after if condition."', '" после условия if."'),
    ('"If statement started here."', '"Условие if начинается здесь."'),
    ('" before here."', '" перед этим местом."'),
    ('" or another statement."', '" или другая инструкция."'),
    ('"Block started here."', '"Блок начинается здесь."'),
    ('"Expected end of block here."', '"Здесь ожидался конец блока."'),
    ('"Your program contains more "', '"В программе больше "'),
    ('"s than needed. Check "', '", чем нужно. Проверьте, что "'),
    ('"each block ("', '"каждый блок ("'),
    ('", ...) only has one "', '", ...) закрыт ровно одним "'),
    ('"Label was started here."', '"Метка начинается здесь."'),
    ('"Tip: Try adding "', '"Подсказка: попробуйте добавить "'),
    ('code("::") .. " here."', 'code("::") .. " здесь."'),
    ('". Are you missing a closing bracket?"',
     '". Возможно, пропущена закрывающая скобка?"'),
    ('"Brackets were opened here."', '"Скобки открыты здесь."'),
    ('" here."', '" здесь."'),
    ('" to start function arguments."', '" перед аргументами функции."'),
]

with zipfile.ZipFile(JAR) as archive:
    translated = archive.read(SOURCE).decode("utf-8")

for old, new in REPLACEMENTS:
    if old not in translated:
        raise RuntimeError(f"Missing source text: {old!r}")
    translated = translated.replace(old, new)

TARGET.parent.mkdir(parents=True, exist_ok=True)
TARGET.write_text(translated, encoding="utf-8", newline="\n")
print(f"{RELATIVE}: {len(REPLACEMENTS)} replacement rules")
