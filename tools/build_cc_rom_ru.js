"use strict";

// Build the Russian CC:Tweaked ROM overlay directly from the pinned mod JAR.
// Only string literals listed below may change. Lua code and comments are
// verified byte-for-byte by the lexer before any file is written.

const fs = require("fs");
const path = require("path");
const zlib = require("zlib");
const crypto = require("crypto");

const INSTANCE = path.resolve(__dirname, "..");
const JAR = path.join(INSTANCE, "mods", "cc-tweaked-1.20.1-forge-1.120.0.jar");
const ROM_PREFIX = "data/computercraft/lua/rom/";
const OUTPUT = path.join(
  INSTANCE,
  "config", "paxi", "datapacks", "IndustrialFrontier-Data",
  "data", "computercraft", "lua", "rom",
);
const EXPECTED_JAR_SHA256 = "f3cde5a1aa20ca6ace802fed8250920d73c000e32a392f887b02315dfc678e90";
const EXPECTED_LUA_FILES = 102;

// The source text is raw Lua string content (without delimiters). The target
// text is raw too, so Lua escapes such as \n and formatting tokens stay explicit.
// Every rule has an expected occurrence count and is tied to the pinned JAR.
const T = (file, from, to, count = 1) => ({ file, from, to, count });
const P = (file, line, column, from, to) => ({ file, line, column, from, to, count: 1 });
const CODE_PATCHES = [
  // These expressions are used only for displayed creature names. Use the
  // translated canonical key while retaining every English input alias.
  { file: "programs/fun/adventure.lua", from: "tItem.aliases[1]", to: "sItem", count: 4 },
  { file: "programs/fun/adventure.lua", from: "items[sMonster].aliases[1]", to: "sMonster", count: 3 },
];
const TRANSLATIONS = [
  // APIs (ten other API files come from companion maps and are audited below).
  T("apis/settings.lua", "Unknown type %q. Expected one of %s.", "Неизвестный тип %q. Ожидался один из типов: %s."),
  T("apis/term.lua", "Redirect object is missing method ", "У объекта перенаправления нет метода "),
  T("apis/term.lua", "term is not a recommended redirect target, try term.current() instead", "Не рекомендуется перенаправлять вывод в term; используйте term.current()"),
  T("apis/textutils.lua", " (string expected, got ", " (ожидался тип string, получено "),
  T("apis/textutils.lua", "',' or ']'", "',' или ']'"),
  T("apis/textutils.lua", "',' or '}'", "',' или '}'"),
  T("apis/textutils.lua", "Cannot serialize table with recursive entries", "Нельзя сериализовать таблицу с рекурсивными ссылками", 2),
  T("apis/textutils.lua", "Cannot serialize table with repeated entries", "Нельзя сериализовать таблицу с повторяющимися ссылками", 2),
  T("apis/textutils.lua", "Cannot serialize type ", "Нельзя сериализовать тип ", 2),
  T("apis/textutils.lua", "Expected object key", "Ожидался ключ объекта"),
  T("apis/textutils.lua", "Malformed JSON at position %d: %s", "Ошибка JSON в позиции %d: %s"),
  T("apis/textutils.lua", "Malformed JSON at position %d: Unexpected trailing character %q.", "Ошибка JSON в позиции %d: неожиданный лишний символ %q."),
  T("apis/textutils.lua", "Malformed number %q.", "Недопустимое число %q."),
  T("apis/textutils.lua", "Malformed unicode escape %q.", "Недопустимая Unicode-последовательность %q."),
  T("apis/textutils.lua", "Press any key to continue", "Нажмите любую клавишу, чтобы продолжить"),
  T("apis/textutils.lua", "Rate must be positive", "Скорость должна быть положительной"),
  T("apis/textutils.lua", "Unescaped whitespace %q.", "Неэкранированный пробельный символ %q."),
  T("apis/textutils.lua", "Unexpected %s, expected %s.", "Неожиданное значение %s; ожидалось %s."),
  T("apis/textutils.lua", "Unexpected character %q.", "Неожиданный символ %q."),
  T("apis/textutils.lua", "Unexpected end of input, expected '\\\"'.", "Неожиданный конец ввода: ожидалась '\\\"'."),
  T("apis/textutils.lua", "Unexpected end of input, expected '}'.", "Неожиданный конец ввода: ожидалась '}'."),
  T("apis/textutils.lua", "Unexpected end of input, expected escape sequence.", "Неожиданный конец ввода: ожидалась escape-последовательность."),
  T("apis/textutils.lua", "Unexpected end of input.", "Неожиданный конец ввода."),
  T("apis/textutils.lua", "Unknown escape character %q.", "Неизвестный escape-символ %q."),
  T("apis/textutils.lua", "attempt to mutate textutils.", "попытка изменить textutils."),
  T("apis/textutils.lua", "bad argument #", "неверный аргумент №"),
  T("apis/textutils.lua", "end of input", "конец ввода"),
  T("apis/textutils.lua", "object key", "ключ объекта"),
  T("apis/turtle/turtle.lua", "Cannot load turtle API on computer", "Нельзя загрузить API turtle на обычном компьютере"),
  T("apis/window.lua", "Arguments must be the same length", "Аргументы должны иметь одинаковую длину"),
  T("apis/window.lua", "Colour out of range", "Цвет вне допустимого диапазона"),
  T("apis/window.lua", "Line is out of range.", "Строка вне допустимого диапазона."),
  T("apis/window.lua", "term is not a recommended window parent, try term.current() instead", "Не рекомендуется использовать term как родительский объект окна; используйте term.current()"),

  // Modules (syntax diagnostics come from a companion map and are audited below).
  T("modules/main/cc/audio/dfpwm.lua", "Amplitude at position %d was %d, but should be between -128 and 127", "Амплитуда в позиции %d равна %d, но должна находиться между -128 и 127"),
  T("modules/main/cc/base64.lua", "alt_chars must be exactly two characters", "alt_chars должен содержать ровно два символа", 2),
  T("modules/main/cc/base64.lua", "input is not valid base64", "входные данные не являются допустимым base64"),
  T("modules/main/cc/expect.lua", " or ", " или "),
  T("modules/main/cc/expect.lua", "bad argument #%d (%s expected, got %s)", "неверный аргумент №%d (ожидался тип %s, получен %s)"),
  T("modules/main/cc/expect.lua", "bad argument #%d to '%s' (%s expected, got %s)", "неверный аргумент №%d функции '%s' (ожидался тип %s, получен %s)"),
  T("modules/main/cc/expect.lua", "bad field '%s' (%s expected, got %s)", "неверное поле '%s' (ожидался тип %s, получен %s)"),
  T("modules/main/cc/expect.lua", "field '%s' missing from table", "в таблице отсутствует поле '%s'"),
  T("modules/main/cc/expect.lua", "min must be less than or equal to max)", "min должен быть меньше или равен max"),
  T("modules/main/cc/expect.lua", "number outside of range (expected %s to be within %s and %s)", "число вне диапазона (значение %s должно находиться между %s и %s)"),
  T("modules/main/cc/internal/edit_runner.lua", "Press any key to continue.", "Нажмите любую клавишу, чтобы продолжить."),
  T("modules/main/cc/internal/error_hints.lua", " or ", " или "),
  T("modules/main/cc/internal/error_hints.lua", "Did you mean: ", "Возможно, вы имели в виду: "),
  T("modules/main/cc/internal/error_printer.lua", "Line ", "Строка "),
  T("modules/main/cc/internal/error_printer.lua", "Message is empty", "Пустое сообщение"),
  T("modules/main/cc/internal/error_printer.lua", "Unknown doc ", "Неизвестный тип документа: "),
  T("modules/main/cc/internal/import.lua", "). File may be corrupted", "). Файл может быть повреждён"),
  T("modules/main/cc/internal/import.lua", " is already a directory.", " уже является каталогом."),
  T("modules/main/cc/internal/import.lua", "Failed to write file (", "Не удалось записать файл ("),
  T("modules/main/cc/internal/import.lua", "Overwrite? (yes/no) ", "Перезаписать? (yes/no) "),
  T("modules/main/cc/internal/import.lua", "The following files will be overwritten:", "Следующие файлы будут перезаписаны:"),
  T("modules/main/cc/internal/import.lua", "Transferring ", "Перенос файла "),
  T("modules/main/cc/pretty.lua", "Unknown doc ", "Неизвестный тип документа: ", 4),
  T("modules/main/cc/pretty.lua", "depth must be a positive number", "depth должен быть положительным числом"),
  T("modules/main/cc/require.lua", "' not found:", "' не найден:"),
  T("modules/main/cc/require.lua", "loop or previous error loading module '", "цикл или предыдущая ошибка при загрузке модуля '"),
  T("modules/main/cc/require.lua", "module '", "модуль '"),
  T("modules/main/cc/require.lua", "no field package.preload['", "нет поля package.preload['"),
  T("modules/main/cc/require.lua", "no file '", "нет файла '"),
  T("modules/main/cc/shell/completion.lua", "Bad table entry #1 at argument #%d (function expected, got %s)", "Неверная запись таблицы №1 в аргументе №%d (ожидался тип function, получен %s)"),
  T("modules/main/cc/shell/completion.lua", "Unexpected 'many' field on argument #%d (should only occur on the last argument)", "Неожиданное поле 'many' у аргумента №%d (оно допустимо только у последнего аргумента)"),
  T("modules/main/cc/strings.lua", "separator is empty", "separator не должен быть пустым"),

  // programs
  T("programs/about.lua", " on ", " на платформе "),
  T("programs/advanced/bg.lua", "Requires multishell", "Требуется multishell"),
  T("programs/advanced/fg.lua", "Requires multishell", "Требуется multishell"),
  T("programs/advanced/multishell.lua", "Press any key to continue", "Нажмите любую клавишу, чтобы продолжить"),
  T("programs/alias.lua", "Usage: ", "Использование: "),
  T("programs/cd.lua", "Not a directory", "Это не каталог"),
  T("programs/cd.lua", "Usage: ", "Использование: "),
  T("programs/clear.lua", "Usages:", "Варианты использования:"),
  T("programs/copy.lua", "Cannot overwrite file multiple times", "Несколько файлов нельзя скопировать в один файл"),
  T("programs/copy.lua", "Destination exists", "Путь назначения уже существует"),
  T("programs/copy.lua", "Destination is read-only", "Путь назначения доступен только для чтения"),
  T("programs/copy.lua", "No matching files", "Подходящие файлы не найдены"),
  T("programs/copy.lua", "Not enough space", "Недостаточно места"),
  T("programs/copy.lua", "Usage: ", "Использование: "),
  T("programs/delete.lua", ": No matching files", ": подходящие файлы не найдены"),
  T("programs/delete.lua", "Cannot delete mount /", "Нельзя удалить точку монтирования /"),
  T("programs/delete.lua", "Cannot delete read-only file /", "Нельзя удалить файл только для чтения /"),
  T("programs/delete.lua", "To delete its contents run rm /", "Чтобы удалить её содержимое, выполните rm /"),
  T("programs/delete.lua", "Usage: ", "Использование: "),
  T("programs/drive.lua", "B remaining)", " Б свободно)"),
  T("programs/drive.lua", "KB remaining)", " КБ свободно)"),
  T("programs/drive.lua", "MB remaining)", " МБ свободно)"),
  T("programs/drive.lua", "No such path", "Путь не найден"),
  T("programs/edit.lua", " (page ", " (страница ", 2),
  T("programs/edit.lua", " Pages", ""),
  T("programs/edit.lua", "Access denied", "Доступ запрещён"),
  T("programs/edit.lua", "Cannot edit a directory.", "Нельзя редактировать каталог."),
  T("programs/edit.lua", "Disk is low on space", "На диске мало места"),
  T("programs/edit.lua", "Error saving to ", "Не удалось сохранить в ", 3),
  T("programs/edit.lua", "Error saving: ", "Ошибка сохранения: "),
  T("programs/edit.lua", "Error starting Task", "Не удалось запустить задачу"),
  T("programs/edit.lua", "Exit", "Выйти"),
  T("programs/edit.lua", "Failed to open ", "Не удалось открыть "),
  T("programs/edit.lua", "File is read only", "Файл доступен только для чтения"),
  T("programs/edit.lua", "Ln ", "Стр. ", 2),
  T("programs/edit.lua", "No printer attached", "Принтер не подключён"),
  T("programs/edit.lua", "Press Ctrl for menu", "Нажмите Ctrl, чтобы открыть меню"),
  T("programs/edit.lua", "Press Ctrl or click here to access menu", "Нажмите Ctrl или щёлкните здесь, чтобы открыть меню"),
  T("programs/edit.lua", "Press Ctrl to access menu", "Нажмите Ctrl, чтобы открыть меню"),
  T("programs/edit.lua", "Print", "Печать"),
  T("programs/edit.lua", "Printed ", "Напечатано страниц: "),
  T("programs/edit.lua", "Printed 1 Page", "Напечатана 1 страница"),
  T("programs/edit.lua", "Printer out of ink", "В принтере закончились чернила"),
  T("programs/edit.lua", "Printer out of ink, please refill", "В принтере закончились чернила — заправьте его"),
  T("programs/edit.lua", "Printer out of paper", "В принтере закончилась бумага"),
  T("programs/edit.lua", "Printer out of paper, please refill", "В принтере закончилась бумага — добавьте её"),
  T("programs/edit.lua", "Printer output tray full, please empty", "Выходной лоток принтера заполнен — освободите его", 2),
  T("programs/edit.lua", "Run", "Запустить"),
  T("programs/edit.lua", "Save", "Сохранить"),
  T("programs/edit.lua", "Saved to ", "Сохранено в "),
  T("programs/edit.lua", "Usage: ", "Использование: "),
  T("programs/eject.lua", " drive", " ничего нет"),
  T("programs/eject.lua", "Nothing in ", "В приводе "),
  T("programs/eject.lua", "Usage: ", "Использование: "),
  T("programs/fun/advanced/paint.lua", "Access denied", "Доступ запрещён"),
  T("programs/fun/advanced/paint.lua", "Cannot edit a directory.", "Нельзя редактировать каталог."),
  T("programs/fun/advanced/paint.lua", "Error saving to ", "Не удалось сохранить в ", 2),
  T("programs/fun/advanced/paint.lua", "Exit", "Выйти"),
  T("programs/fun/advanced/paint.lua", "Press Ctrl or click here to access menu", "Нажмите Ctrl или щёлкните здесь, чтобы открыть меню"),
  T("programs/fun/advanced/paint.lua", "Requires an Advanced Computer", "Требуется улучшенный компьютер"),
  T("programs/fun/advanced/paint.lua", "Save", "Сохранить"),
  T("programs/fun/advanced/paint.lua", "Saved to ", "Сохранено в "),
  T("programs/fun/advanced/paint.lua", "Usage: ", "Использование: "),
  T("programs/fun/advanced/redirection.lua", "  Check out the full game:  ", "  Полная версия игры:  ", 2),
  T("programs/fun/advanced/redirection.lua", "  Click to Begin  ", "  Щёлкните, чтобы начать  "),
  T("programs/fun/advanced/redirection.lua", "  ComputerCraft Edition  ", "  Версия для ComputerCraft  ", 3),
  T("programs/fun/advanced/redirection.lua", "  Thank you for  ", "  Спасибо за  "),
  T("programs/fun/advanced/redirection.lua", "  Thank you for playing Redirection  ", "  Спасибо за игру в Redirection  "),
  T("programs/fun/advanced/redirection.lua", "  playing Redirection  ", "  игру в Redirection  "),
  T("programs/fun/advanced/redirection.lua", "Check out the full version of Redirection:", "Полная версия Redirection:"),
  T("programs/fun/advanced/redirection.lua", "Exit Color Out", "Недопустимый цвет выхода"),
  T("programs/fun/advanced/redirection.lua", "Here X", "Нет клетки: X"),
  T("programs/fun/advanced/redirection.lua", "Level ", "Уровень "),
  T("programs/fun/advanced/redirection.lua", "Level Not Exists : ", "Уровень не найден: "),
  T("programs/fun/advanced/redirection.lua", "Start Color Out", "Недопустимый цвет старта"),
  T("programs/fun/adventure.lua", " and ", " и "),
  T("programs/fun/adventure.lua", ", which you pick up.", "; вы подбираете добычу."),
  T("programs/fun/adventure.lua", "), you feel a swelling sense of pride.", "), вас переполняет гордость."),
  T("programs/fun/adventure.lua", " appears.", "."),
  T("programs/fun/adventure.lua", " bursts into flame and dies.", " вспыхивает и погибает."),
  T("programs/fun/adventure.lua", " dies.", "» погибает."),
  T("programs/fun/adventure.lua", " dropped ", "» оставляет после себя: ", 2),
  T("programs/fun/adventure.lua", " here.", ".", 4),
  T("programs/fun/adventure.lua", " is injured by your blow.", "» ранено вашим ударом."),
  T("programs/fun/adventure.lua", " is not a good building material.", " не подходит для строительства."),
  T("programs/fun/adventure.lua", " is not strong enough to break this ore.", " — прочности этого инструмента недостаточно для этой руды."),
  T("programs/fun/adventure.lua", " using ", "; инструмент: ", 2),
  T("programs/fun/adventure.lua", " with ", "; инструмент: "),
  T("programs/fun/adventure.lua", " with what?", "?"),
  T("programs/fun/adventure.lua", "(life is peaceful there)", "(там живётся без забот)"),
  T("programs/fun/adventure.lua", "(lots of open air)", "(и вокруг простор)"),
  T("programs/fun/adventure.lua", "(sun in winter time)", "(зимой сияет солнце)"),
  T("programs/fun/adventure.lua", "(this and more we'll do)", "(и многое ещё)"),
  T("programs/fun/adventure.lua", "(this is what we'll do)", "(вот что мы сделаем)"),
  T("programs/fun/adventure.lua", "(to begin life anew)", "(начать жизнь с нуля)"),
  T("programs/fun/adventure.lua", "(we will do just fine)", "(у нас всё будет хорошо)"),
  T("programs/fun/adventure.lua", "(where the skies are blue)", "(под голубыми небесами)"),
  T("programs/fun/adventure.lua", "a chicken", "курица", 2),
  T("programs/fun/adventure.lua", "a cow", "корова", 2),
  T("programs/fun/adventure.lua", "a crafting table", "верстак", 2),
  T("programs/fun/adventure.lua", "a creeper", "крипер", 3),
  T("programs/fun/adventure.lua", "a diamond pickaxe", "алмазная кирка", 2),
  T("programs/fun/adventure.lua", "a diamond shovel", "алмазная лопата", 2),
  T("programs/fun/adventure.lua", "a furnace", "печь", 2),
  T("programs/fun/adventure.lua", "a cave entrance", "вход в пещеру", 7),
  T("programs/fun/adventure.lua", "a pig", "свинья", 2),
  T("programs/fun/adventure.lua", "a river", "река", 3),
  T("programs/fun/adventure.lua", "a sheep", "овца", 2),
  T("programs/fun/adventure.lua", "a skeleton", "скелет", 2),
  T("programs/fun/adventure.lua", "a spider", "паук", 3),
  T("programs/fun/adventure.lua", "a stone pickaxe", "каменная кирка", 2),
  T("programs/fun/adventure.lua", "a stone shovel", "каменная лопата", 2),
  T("programs/fun/adventure.lua", "a torch", "факел", 12),
  T("programs/fun/adventure.lua", "a wooden pickaxe", "деревянная кирка", 2),
  T("programs/fun/adventure.lua", "a wooden shovel", "деревянная лопата", 2),
  T("programs/fun/adventure.lua", "a zombie", "зомби", 2),
  T("programs/fun/adventure.lua", "A creeper explodes.", "Крипер взрывается."),
  T("programs/fun/adventure.lua", "A perfect handle for torches or a pickaxe.", "Отличная рукоять для факелов или кирки."),
  T("programs/fun/adventure.lua", "A pretty good sword.", "Вполне хороший меч."),
  T("programs/fun/adventure.lua", "All he wants to do is eat your brains.", "Ему всего лишь хочется съесть ваш мозг."),
  T("programs/fun/adventure.lua", "Attack what?", "Кого атаковать?"),
  T("programs/fun/adventure.lua", "As you look at your creation (made from ", "Глядя на своё творение (материал: "),
  T("programs/fun/adventure.lua", "Best. Pickaxe. Ever.", "Лучшая. Кирка. На свете."),
  T("programs/fun/adventure.lua", "Best. Sword. Ever.", "Лучший. Меч. На свете."),
  T("programs/fun/adventure.lua", "Break what?", "Что сломать?"),
  T("programs/fun/adventure.lua", "Build what?", "Что построить?"),
  T("programs/fun/adventure.lua", "By creating a computer in a computer in a computer, you tear a hole in the spacetime continuum from which no mortal being can escape.", "Создав компьютер внутри компьютера внутри компьютера, вы разрываете пространство-время и попадаете в ловушку, из которой смертному не выбраться."),
  T("programs/fun/adventure.lua", "Craft what?", "Что создать?"),
  T("programs/fun/adventure.lua", "Crafted.", "Готово."),
  T("programs/fun/adventure.lua", "Delicious and nutritious.", "Вкусно и питательно."),
  T("programs/fun/adventure.lua", "Dig where?", "Где копать?"),
  T("programs/fun/adventure.lua", "Dozens of eyes stare back at you.", "На вас смотрят десятки глаз."),
  T("programs/fun/adventure.lua", "Don't be shy.", "Не стесняйтесь."),
  T("programs/fun/adventure.lua", "Drop what?", "Что выбросить?"),
  T("programs/fun/adventure.lua", "Dropped.", "Выброшено."),
  T("programs/fun/adventure.lua", "Eat what?", "Что съесть?"),
  T("programs/fun/adventure.lua", "Enunciate.", "Говорите разборчиво."),
  T("programs/fun/adventure.lua", "Finger licking good.", "Пальчики оближешь."),
  T("programs/fun/adventure.lua", "Fire, fire, burn so bright, won't you light my cave tonight?", "Гори, огонь, сияй ярче и освети сегодня мою пещеру."),
  T("programs/fun/adventure.lua", "Flimsy, but better than nothing.", "Хлипкий, но лучше, чем ничего."),
  T("programs/fun/adventure.lua", "From the shadows, ", "Из темноты появляется существо: "),
  T("programs/fun/adventure.lua", "Go where?", "Куда идти?"),
  T("programs/fun/adventure.lua", "Good for digging holes.", "Подходит для рытья ям.", 4),
  T("programs/fun/adventure.lua", "Huh?", "А?"),
  T("programs/fun/adventure.lua", "I don't understand that direction.", "Я не понимаю это направление.", 2),
  T("programs/fun/adventure.lua", "I don't understand you.", "Я вас не понимаю."),
  T("programs/fun/adventure.lua", "I don't understand.", "Я не понимаю."),
  T("programs/fun/adventure.lua", "I'll think about it.", "Я подумаю."),
  T("programs/fun/adventure.lua", "It is daytime.", "Сейчас день.", 8),
  T("programs/fun/adventure.lua", "It is night.", "Сейчас ночь.", 5),
  T("programs/fun/adventure.lua", "It is pitch dark.", "Здесь кромешная тьма."),
  T("programs/fun/adventure.lua", "It's a crafting table. I shouldn't tell you this, but these don't actually do anything in this game, you can craft tools whenever you like.", "Это верстак. По секрету: в этой игре он ничего не делает — инструменты можно создавать где угодно."),
  T("programs/fun/adventure.lua", "It's a furnace. Between you and me, these don't actually do anything in this game.", "Это печь. Между нами: в этой игре она ничего не делает."),
  T("programs/fun/adventure.lua", "Let me get back to you on that one.", "Вернёмся к этому позже."),
  T("programs/fun/adventure.lua", "Mine ", "Чем добыть "),
  T("programs/fun/adventure.lua", "Mine what?", "Что добыть?"),
  T("programs/fun/adventure.lua", "Nope.", "Нет."),
  T("programs/fun/adventure.lua", "Place what?", "Что поставить?"),
  T("programs/fun/adventure.lua", "Placed.", "Установлено."),
  T("programs/fun/adventure.lua", "Project your voice.", "Говорите громче."),
  T("programs/fun/adventure.lua", "Pull yourself together man.", "Соберитесь, дружище."),
  T("programs/fun/adventure.lua", "Say again?", "Повторите?"),
  T("programs/fun/adventure.lua", "Score: &e0", "Счёт: &e0", 3),
  T("programs/fun/adventure.lua", "Soft and good for building.", "Мягкая и хорошо подходит для строительства."),
  T("programs/fun/adventure.lua", "Sparkly, rare, and impossible to mine without an iron pickaxe.", "Сверкает, редко встречается, а без железной кирки её не добыть."),
  T("programs/fun/adventure.lua", "Speak clearly.", "Говорите яснее."),
  T("programs/fun/adventure.lua", "Speak up.", "Говорите громче."),
  T("programs/fun/adventure.lua", "Stone is useful for building things, and making stone pickaxes.", "Камень пригодится для строительства и изготовления каменных кирок."),
  T("programs/fun/adventure.lua", "Take what?", "Что взять?"),
  T("programs/fun/adventure.lua", "Taken.", "Взято."),
  T("programs/fun/adventure.lua", "That coal looks useful for building torches, if only you had a pickaxe to mine it.", "Из этого угля получатся факелы — была бы кирка, чтобы его добыть."),
  T("programs/fun/adventure.lua", "That doesn't make any sense.", "В этом нет никакого смысла."),
  T("programs/fun/adventure.lua", "That iron looks mighty strong, you'll need a stone pickaxe to mine it.", "Железо выглядит прочным; для его добычи понадобится каменная кирка."),
  T("programs/fun/adventure.lua", "That was delicious!", "Было очень вкусно!"),
  T("programs/fun/adventure.lua", "That's crazy talk.", "Что за безумие."),
  T("programs/fun/adventure.lua", "The cave lights up under the torchflame.", "Пламя факела освещает пещеру."),
  T("programs/fun/adventure.lua", "The cave plunges into darkness.", "Пещера погружается во тьму."),
  T("programs/fun/adventure.lua", "The chicken looks delicious.", "Курица выглядит аппетитно."),
  T("programs/fun/adventure.lua", "The cow stares at you blankly.", "Корова безучастно смотрит на вас."),
  T("programs/fun/adventure.lua", "The creeper explodes.", "Крипер взрывается."),
  T("programs/fun/adventure.lua", "The creeper needs a hug.", "Криперу явно не хватает объятий."),
  T("programs/fun/adventure.lua", "The entrance to the cave is dark, but it looks like you can climb down.", "Вход в пещеру тёмен, но, похоже, туда можно спуститься."),
  T("programs/fun/adventure.lua", "The head bone's connected to the neck bone, the neck bone's connected to the chest bone, the chest bone's connected to the arm bone, the arm bone's connected to the bow, and the bow is pointed at you.", "Кость головы соединена с шеей, шея — с грудной клеткой, та — с рукой, рука держит лук, а лук направлен на вас."),
  T("programs/fun/adventure.lua", "The night gets a little brighter.", "Ночь становится немного светлее."),
  T("programs/fun/adventure.lua", "The ore breaks, dropping ", "Руда раскалывается и оставляет "),
  T("programs/fun/adventure.lua", "The pig has a square nose.", "У свиньи квадратный пятачок."),
  T("programs/fun/adventure.lua", "The pickaxe looks good for breaking iron.", "Эта кирка подходит для добычи железа."),
  T("programs/fun/adventure.lua", "The pickaxe looks good for breaking stone and coal.", "Эта кирка подходит для добычи камня и угля."),
  T("programs/fun/adventure.lua", "The pickaxe looks strong enough to break diamond.", "Эта кирка достаточно прочна для добычи алмазов."),
  T("programs/fun/adventure.lua", "The river flows majestically towards the horizon. It doesn't do anything else.", "Река величественно течёт к горизонту. Больше она ничего не делает."),
  T("programs/fun/adventure.lua", "The sheep is fluffy.", "Овца пушистая."),
  T("programs/fun/adventure.lua", "The sun is rising.", "Солнце восходит."),
  T("programs/fun/adventure.lua", "The sun is setting.", "Солнце садится."),
  T("programs/fun/adventure.lua", "The tree breaks into blocks of wood, which you pick up.", "Дерево распадается на блоки древесины, и вы их подбираете."),
  T("programs/fun/adventure.lua", "The trees look easy to break.", "Похоже, эти деревья легко сломать."),
  T("programs/fun/adventure.lua", "These won't run out for a while.", "Их хватит надолго."),
  T("programs/fun/adventure.lua", "This sword can slay any enemy.", "Этим мечом можно сразить любого врага."),
  T("programs/fun/adventure.lua", "Time passes...", "Время идёт..."),
  T("programs/fun/adventure.lua", "Use your words.", "Скажите словами."),
  T("programs/fun/adventure.lua", "Very handsome.", "Очень даже ничего."),
  T("programs/fun/adventure.lua", "Welcome to adventure, the greatest text adventure game on CraftOS. ", "Добро пожаловать в adventure — величайшую текстовую игру на CraftOS. "),
  T("programs/fun/adventure.lua", "With the sun high in the sky, the ", "Под ярким солнцем "),
  T("programs/fun/adventure.lua", "What?", "Что?"),
  T("programs/fun/adventure.lua", "Why not build a mud hut?", "Почему бы не построить хижину из грязи?"),
  T("programs/fun/adventure.lua", "You are carrying ", "У вас с собой: "),
  T("programs/fun/adventure.lua", "You are injured.", "Вы ранены."),
  T("programs/fun/adventure.lua", "You are no longer injured.", "Вы больше не ранены."),
  T("programs/fun/adventure.lua", "You are standing ", "Вы стоите "),
  T("programs/fun/adventure.lua", "You are underground. ", "Вы под землёй. "),
  T("programs/fun/adventure.lua", "You can just see the sky through the opening.", "Сквозь отверстие едва видно небо."),
  T("programs/fun/adventure.lua", "You can travel ", "Можно пойти: "),
  T("programs/fun/adventure.lua", "You can't break ", "Нельзя разрушить объект: ", 2),
  T("programs/fun/adventure.lua", "You can't carry ", "Это нельзя унести: "),
  T("programs/fun/adventure.lua", "You can't do that.", "Так сделать нельзя."),
  T("programs/fun/adventure.lua", "You can't drop that.", "Это нельзя выбросить."),
  T("programs/fun/adventure.lua", "You can't eat ", "Этот предмет нельзя съесть: "),
  T("programs/fun/adventure.lua", "You can't go that way.", "Туда пройти нельзя."),
  T("programs/fun/adventure.lua", "You can't dig that way.", "В этом направлении копать нельзя."),
  T("programs/fun/adventure.lua", "You could easily craft these planks into sticks.", "Из этих досок легко сделать палки."),
  T("programs/fun/adventure.lua", "You could easily craft this wood into planks.", "Из этой древесины легко сделать доски."),
  T("programs/fun/adventure.lua", "You dig ", "Направление раскопок: ", 2),
  T("programs/fun/adventure.lua", "You don't have a ", "У вас нет "),
  T("programs/fun/adventure.lua", "You don't have any ", "У вас нет ", 2),
  T("programs/fun/adventure.lua", "You don't have any building materials.", "У вас нет строительных материалов."),
  T("programs/fun/adventure.lua", "You don't have the items you need to craft ", "Не хватает компонентов для рецепта: "),
  T("programs/fun/adventure.lua", "You don't have torches.", "У вас нет факелов."),
  T("programs/fun/adventure.lua", "You don't know how to make ", "Неизвестный рецепт: "),
  T("programs/fun/adventure.lua", "You don't see a ", "Здесь нет ", 2),
  T("programs/fun/adventure.lua", "You don't see any ", "Здесь нет "),
  T("programs/fun/adventure.lua", "You have died.", "Вы погибли.", 3),
  T("programs/fun/adventure.lua", "You hit bedrock.", "Вы упираетесь в коренную породу."),
  T("programs/fun/adventure.lua", "You need a different kind of tool to break this ore.", "Для этой руды нужен инструмент другого типа."),
  T("programs/fun/adventure.lua", "You need a tool to break this ore.", "Чтобы добыть эту руду, нужен инструмент."),
  T("programs/fun/adventure.lua", "You need to mine this ore.", "Эту руду нужно добыть киркой."),
  T("programs/fun/adventure.lua", "You need to use a pickaxe to dig through stone.", "Чтобы пробиться сквозь камень, нужна кирка."),
  T("programs/fun/adventure.lua", "You see nothing special about ", "Ничего примечательного в этом нет: "),
  T("programs/fun/adventure.lua", "Your construction is complete.", "Строительство завершено."),
  T("programs/fun/adventure.lua", "You're not carrying a ", "У вас нет ", 2),
  T("programs/fun/adventure.lua", " and collect some dirt and stone.", ". Добыто немного земли и камня."),
  T("programs/fun/adventure.lua", " and collect some stone.", ". Добыто немного камня."),
  T("programs/fun/adventure.lua", "be read back to you. The actions available to you are go, look, inspect, inventory, ", "а игра опишет результат. Доступные действия: go, look, inspect, inventory, "),
  T("programs/fun/adventure.lua", "in a desert", "в пустыне"),
  T("programs/fun/adventure.lua", "in a forest", "в лесу"),
  T("programs/fun/adventure.lua", "in a grassy plain", "на травянистой равнине"),
  T("programs/fun/adventure.lua", "in a mountain range", "среди гор"),
  T("programs/fun/adventure.lua", "in a pine forest", "в сосновом лесу"),
  T("programs/fun/adventure.lua", "in frozen tundra", "в промёрзшей тундре"),
  T("programs/fun/adventure.lua", "knee deep in a swamp", "по колено в болоте"),
  T("programs/fun/adventure.lua", "an exit to the surface", "выход на поверхность", 7),
  T("programs/fun/adventure.lua", "an iron pickaxe", "железная кирка", 2),
  T("programs/fun/adventure.lua", "an iron shovel", "железная лопата", 2),
  T("programs/fun/adventure.lua", "no tea", "нет чая", 3),
  T("programs/fun/adventure.lua", "nothing", "ничего"),
  T("programs/fun/adventure.lua", "some chicken", "курятина", 2),
  T("programs/fun/adventure.lua", "some coal", "уголь", 6),
  T("programs/fun/adventure.lua", "some diamond", "алмазы", 6),
  T("programs/fun/adventure.lua", "some dirt", "земля", 3),
  T("programs/fun/adventure.lua", "some iron", "железо", 6),
  T("programs/fun/adventure.lua", "some planks", "доски", 7),
  T("programs/fun/adventure.lua", "some pork", "свинина", 2),
  T("programs/fun/adventure.lua", "some sticks", "палки", 15),
  T("programs/fun/adventure.lua", "some stone", "камень", 13),
  T("programs/fun/adventure.lua", "some torches", "факелы", 5),
  T("programs/fun/adventure.lua", "some wood", "древесина", 4),
  T("programs/fun/adventure.lua", "some wool", "шерсть", 2),
  T("programs/fun/adventure.lua", "take, drop, place, punch, attack, mine, dig, craft, build, eat and exit.", "take, drop, place, punch, attack, mine, dig, craft, build, eat и exit."),
  T("programs/fun/adventure.lua", "There are trees here.", "Здесь растут деревья."),
  T("programs/fun/adventure.lua", "There is ", "Здесь есть "),
  T("programs/fun/adventure.lua", "To get around the world, type actions, and the adventure will ", "Вводите действия, чтобы перемещаться по миру, "),
  P("programs/fun/adventure.lua", 1025, 23, "The ", "Существо «"),
  P("programs/fun/adventure.lua", 1030, 35, "The ", "Существо «"),
  P("programs/fun/adventure.lua", 1040, 23, "The ", "Существо «"),
  P("programs/fun/adventure.lua", 1046, 31, "The ", "Существо «"),
  P("programs/fun/adventure.lua", 1278, 35, "A ", "Существо «"),
  P("programs/fun/adventure.lua", 1278, 55, " attacks you.", "» атакует вас."),
  P("programs/fun/adventure.lua", 1280, 35, "The ", "Существо «"),
  P("programs/fun/adventure.lua", 1280, 57, " attacks you.", "» атакует вас."),
  T("programs/fun/dj.lua", "No Music Disc in disk drive: ", "В дисководе нет музыкальной пластинки: "),
  T("programs/fun/dj.lua", "No Music Discs in attached disk drives", "В подключённых дисководах нет музыкальных пластинок"),
  T("programs/fun/dj.lua", "Playing ", "Сейчас играет: "),
  T("programs/fun/dj.lua", "Usages:", "Варианты использования:"),
  T("programs/fun/hello.lua", "Hello World!", "Привет, мир!"),
  T("programs/fun/worm.lua", " FINAL SCORE ", " ИТОГОВЫЙ СЧЁТ "),
  T("programs/fun/worm.lua", " PRESS ANY KEY ", " НАЖМИТЕ ЛЮБУЮ КЛАВИШУ "),
  T("programs/fun/worm.lua", " SELECT DIFFICULTY ", " ВЫБЕРИТЕ СЛОЖНОСТЬ "),
  T("programs/fun/worm.lua", "DIFFICULTY ", "СЛОЖНОСТЬ "),
  T("programs/fun/worm.lua", "EASY", "ЛЕГКО"),
  T("programs/fun/worm.lua", "HARD", "СЛОЖНО"),
  T("programs/fun/worm.lua", "MEDIUM", "СРЕДНЕ"),
  T("programs/fun/worm.lua", "SCORE ", "СЧЁТ "),
  T("programs/help.lua", "Help topics available:", "Доступные разделы справки:"),
  T("programs/help.lua", "Help: ", "Справка: "),
  T("programs/help.lua", "No help available", "Справка не найдена"),
  T("programs/help.lua", "Press Q to exit", "Нажмите Q, чтобы выйти"),
  T("programs/id.lua", "Has audio track \\\"", "Аудиозапись: \\\""),
  T("programs/id.lua", "Has untitled audio", "Есть аудиозапись без названия"),
  T("programs/id.lua", "Labelled \\\"", "Метка: \\\""),
  T("programs/id.lua", "No disk in drive ", "В приводе нет дискеты: "),
  T("programs/id.lua", "Non-disk data source", "Источник данных не является дискетой"),
  T("programs/id.lua", "The disk is #", "Номер дискеты: "),
  T("programs/id.lua", "This computer is labelled \\\"", "Метка этого компьютера: \\\""),
  T("programs/id.lua", "This is computer #", "Это компьютер №"),
  T("programs/import.lua", "Drop files to transfer them to this computer", "Перетащите файлы, чтобы перенести их на этот компьютер"),
  T("programs/import.lua", "No files to transfer", "Нет файлов для переноса"),
  T("programs/label.lua", " drive", " нет дискеты"),
  T("programs/label.lua", "Computer label is \\\"", "Метка компьютера: \\\""),
  T("programs/label.lua", "Computer label cleared", "Метка компьютера удалена"),
  T("programs/label.lua", "Computer label set to \\\"", "Метка компьютера установлена: \\\""),
  T("programs/label.lua", "Disk label is \\\"", "Метка дискеты: \\\""),
  T("programs/label.lua", "Disk label cleared", "Метка дискеты удалена"),
  T("programs/label.lua", "Disk label set to \\\"", "Метка дискеты установлена: \\\""),
  T("programs/label.lua", "No Computer label", "У компьютера нет метки"),
  T("programs/label.lua", "No Disk label", "У дискеты нет метки"),
  T("programs/label.lua", "No disk drive named ", "Дисковод не найден: "),
  T("programs/label.lua", "No disk in ", "В приводе "),
  T("programs/label.lua", "Usages:", "Варианты использования:"),
  T("programs/list.lua", "Not a directory", "Это не каталог"),
  T("programs/lua.lua", "Call exit() to exit.", "Для выхода вызовите exit().", 2),
  T("programs/lua.lua", "Interactive Lua prompt.", "Интерактивная консоль Lua."),
  T("programs/lua.lua", "This is an interactive Lua prompt.", "Это интерактивная консоль Lua."),
  T("programs/lua.lua", "To access local variables in later inputs, remove the local keyword.", "Чтобы обращаться к локальным переменным в следующих командах, уберите ключевое слово local."),
  T("programs/lua.lua", "To run a lua program, just type its name.", "Чтобы запустить программу Lua, введите её имя."),
  T("programs/mkdir.lua", ": Access denied", ": доступ запрещён"),
  T("programs/mkdir.lua", ": Destination exists", ": путь назначения уже существует"),
  T("programs/mkdir.lua", "Usage: ", "Использование: "),
  T("programs/monitor.lua", "Invalid scale: ", "Недопустимый масштаб: "),
  T("programs/monitor.lua", "No monitor named ", "Монитор не найден: ", 2),
  T("programs/monitor.lua", "No such program: ", "Программа не найдена: "),
  T("programs/monitor.lua", "Running ", "Запуск "),
  T("programs/monitor.lua", " on monitor ", " на мониторе "),
  T("programs/monitor.lua", "Usage:", "Использование:"),
  T("programs/motd.lua", "Happy new year!", "С Новым годом!"),
  T("programs/motd.lua", "Merry X-mas!", "С Рождеством!"),
  T("programs/motd.lua", "OOoooOOOoooo! Spooky!", "У-у-у-у! Страшно!"),
  T("programs/move.lua", "Cannot move mount /", "Нельзя переместить точку монтирования /"),
  T("programs/move.lua", "Cannot move read-only file /", "Нельзя переместить файл только для чтения /"),
  T("programs/move.lua", "Cannot overwrite file multiple times", "Несколько файлов нельзя переместить в один файл"),
  T("programs/move.lua", "Destination exists", "Путь назначения уже существует"),
  T("programs/move.lua", "Destination is read-only", "Путь назначения доступен только для чтения"),
  T("programs/move.lua", "No matching files", "Подходящие файлы не найдены"),
  T("programs/move.lua", "Usage: ", "Использование: "),
  T("programs/peripherals.lua", "Attached Peripherals:", "Подключённая периферия:"),
  T("programs/peripherals.lua", "None", "Нет"),
  T("programs/pocket/falling.lua", " Play from level: <", " Начать с уровня: <"),
  T("programs/pocket/falling.lua", " Play head-to-head game! ", " Играть вдвоём! "),
  T("programs/pocket/falling.lua", " Quit ", " Выйти "),
  T("programs/pocket/falling.lua", "Game Over!", "Игра окончена!"),
  T("programs/pocket/falling.lua", "Level", "Уровень"),
  T("programs/pocket/falling.lua", "Lines", "Линии"),
  T("programs/pocket/falling.lua", "Next", "Далее"),
  T("programs/pocket/falling.lua", "Paused", "Пауза"),
  T("programs/pocket/falling.lua", "Score", "Счёт"),
  T("programs/pocket/falling.lua", "Your screen is too small to play :(", "Экран слишком мал для игры :(") ,
  T("programs/pocket/unequip.lua", "Item unequipped", "Предмет снят"),
  T("programs/pocket/unequip.lua", "Requires a Pocket Computer", "Требуется карманный компьютер"),
  T("programs/reboot.lua", "Goodbye", "До свидания"),
  T("programs/rednet/chat.lua", " user connected.", " пользователь подключён."),
  T("programs/rednet/chat.lua", " users connected.", " — подключено пользователей."),
  T("programs/rednet/chat.lua", " has joined the chat", " подключается к чату"),
  T("programs/rednet/chat.lua", " has left the chat", " покидает чат"),
  T("programs/rednet/chat.lua", " has timed out", ": время ожидания истекло"),
  T("programs/rednet/chat.lua", " is now known as ", " — новое имя: "),
  T("programs/rednet/chat.lua", " on ", " на "),
  T("programs/rednet/chat.lua", "* Available commands:", "* Доступные команды:"),
  T("programs/rednet/chat.lua", "* Connected Users:", "* Подключённые пользователи:"),
  T("programs/rednet/chat.lua", "* Unrecognised command: /", "* Неизвестная команда: /"),
  T("programs/rednet/chat.lua", "* Usage: /me [words]", "* Использование: /me [words]"),
  T("programs/rednet/chat.lua", "* Usage: /nick [nickname]", "* Использование: /nick [nickname]"),
  T("programs/rednet/chat.lua", "0 users connected.", "Нет подключённых пользователей."),
  T("programs/rednet/chat.lua", "Disconnected.", "Соединение закрыто."),
  T("programs/rednet/chat.lua", "Failed.", "Не удалось."),
  T("programs/rednet/chat.lua", "Looking up ", "Поиск сервера "),
  T("programs/rednet/chat.lua", "No modems found.", "Модемы не найдены."),
  T("programs/rednet/chat.lua", "Server timeout.", "Сервер не отвечает."),
  T("programs/rednet/chat.lua", "Success.", "Готово."),
  T("programs/rednet/chat.lua", "Usages:", "Варианты использования:"),
  T("programs/redstone.lua", "Bundled inputs:", "Входящие пакетные сигналы:"),
  T("programs/redstone.lua", "No such color", "Неизвестный цвет"),
  T("programs/redstone.lua", "None.", "Нет."),
  T("programs/redstone.lua", "Redstone inputs: ", "Входящие сигналы редстоуна: "),
  T("programs/redstone.lua", "Usages:", "Варианты использования:"),
  T("programs/redstone.lua", "Value must be boolean", "Значение должно иметь тип boolean"),
  T("programs/redstone.lua", "Value must be boolean or 0-15", "Значение должно иметь тип boolean или быть числом от 0 до 15"),
  T("programs/rename.lua", "Can't rename mounts", "Нельзя переименовать точки монтирования"),
  T("programs/rename.lua", "Destination exists", "Путь назначения уже существует"),
  T("programs/rename.lua", "Destination is read-only", "Путь назначения доступен только для чтения"),
  T("programs/rename.lua", "No matching files", "Подходящие файлы не найдены"),
  T("programs/rename.lua", "Source is read-only", "Источник доступен только для чтения"),
  T("programs/rename.lua", "Usage: ", "Использование: "),
  T("programs/set.lua", " (default is ", " (по умолчанию: "),
  T("programs/set.lua", " is ", ": ", 2),
  T("programs/set.lua", " set to ", ": "),
  T("programs/set.lua", " unset", ": значение сброшено"),
  T("programs/set.lua", "%s is not a valid %s.", "%s не является допустимым значением типа %s."),
  T("programs/shell.lua", "Attempt to create global ", "Попытка создать глобальную переменную "),
  T("programs/shell.lua", "Cannot use the shell as a hashbang program", "Нельзя использовать shell как программу в hashbang"),
  T("programs/shell.lua", "Hashbang program not found: ", "Программа из hashbang не найдена: "),
  T("programs/shell.lua", "Hashbang recursion depth limit reached when loading file: ", "Превышена глубина рекурсии hashbang при загрузке файла: "),
  T("programs/shell.lua", "No such program", "Программа не найдена", 2),
  T("programs/shell.lua", "Not a directory", "Это не каталог"),
  T("programs/shutdown.lua", "Goodbye", "До свидания"),
  T("programs/time.lua", " on Day ", ", день "),
  T("programs/time.lua", "The time is ", "Сейчас "),
  T("programs/turtle/turn.lua", "No such direction: ", "Неизвестное направление: "),
  T("programs/turtle/turn.lua", "Requires a Turtle", "Требуется черепаха"),
  T("programs/turtle/turn.lua", "Try: left, right", "Допустимые значения: left, right"),
  T("programs/turtle/turn.lua", "Usage: ", "Использование: "),
  T("programs/turtle/unequip.lua", "Item unequipped", "Предмет снят"),
  T("programs/turtle/unequip.lua", "No space to unequip item", "Нет места для снятого предмета"),
  T("programs/turtle/unequip.lua", "Nothing to unequip", "Нечего снимать"),
  T("programs/turtle/unequip.lua", "Requires a Turtle", "Требуется черепаха"),
  T("programs/turtle/unequip.lua", "Usage: ", "Использование: "),
  T("programs/type.lua", "No such path", "Путь не найден"),
  T("programs/type.lua", "Usage: ", "Использование: "),
  T("programs/type.lua", "directory", "каталог"),
  T("programs/type.lua", "file", "файл"),
];

function readZip(buffer) {
  const eocdSignature = 0x06054b50;
  const min = Math.max(0, buffer.length - 0xffff - 22);
  let eocd = -1;
  for (let i = buffer.length - 22; i >= min; i--) {
    if (buffer.readUInt32LE(i) === eocdSignature) {
      eocd = i;
      break;
    }
  }
  if (eocd < 0) throw new Error("ZIP end-of-central-directory record not found");

  const entryCount = buffer.readUInt16LE(eocd + 10);
  let cursor = buffer.readUInt32LE(eocd + 16);
  const entries = new Map();

  for (let index = 0; index < entryCount; index++) {
    if (buffer.readUInt32LE(cursor) !== 0x02014b50) {
      throw new Error(`Invalid ZIP central directory at byte ${cursor}`);
    }
    const method = buffer.readUInt16LE(cursor + 10);
    const compressedSize = buffer.readUInt32LE(cursor + 20);
    const uncompressedSize = buffer.readUInt32LE(cursor + 24);
    const nameLength = buffer.readUInt16LE(cursor + 28);
    const extraLength = buffer.readUInt16LE(cursor + 30);
    const commentLength = buffer.readUInt16LE(cursor + 32);
    const localOffset = buffer.readUInt32LE(cursor + 42);
    const name = buffer.subarray(cursor + 46, cursor + 46 + nameLength).toString("utf8");

    if (buffer.readUInt32LE(localOffset) !== 0x04034b50) {
      throw new Error(`Invalid ZIP local header for ${name}`);
    }
    const localNameLength = buffer.readUInt16LE(localOffset + 26);
    const localExtraLength = buffer.readUInt16LE(localOffset + 28);
    const dataStart = localOffset + 30 + localNameLength + localExtraLength;
    const compressed = buffer.subarray(dataStart, dataStart + compressedSize);
    let data;
    if (method === 0) data = Buffer.from(compressed);
    else if (method === 8) data = zlib.inflateRawSync(compressed);
    else throw new Error(`Unsupported ZIP compression method ${method} for ${name}`);
    if (data.length !== uncompressedSize) {
      throw new Error(`Uncompressed size mismatch for ${name}`);
    }
    entries.set(name, data);
    cursor += 46 + nameLength + extraLength + commentLength;
  }
  return entries;
}

function longBracketAt(source, index) {
  if (source[index] !== "[") return null;
  let i = index + 1;
  while (source[i] === "=") i++;
  if (source[i] !== "[") return null;
  const equals = i - index - 1;
  return { openLength: equals + 2, close: "]" + "=".repeat(equals) + "]" };
}

function lexLua(source, file) {
  const tokens = [];
  let i = 0;
  let segmentStart = 0;
  let line = 1;
  let column = 1;

  function advance(text) {
    for (let j = 0; j < text.length; j++) {
      if (text[j] === "\n") {
        line++;
        column = 1;
      } else {
        column++;
      }
    }
  }

  function pushPlain(end) {
    if (end > segmentStart) {
      tokens.push({ type: "plain", raw: source.slice(segmentStart, end) });
    }
  }

  while (i < source.length) {
    const startLine = line;
    const startColumn = column;

    if (source[i] === "-" && source[i + 1] === "-") {
      pushPlain(i);
      const start = i;
      const long = longBracketAt(source, i + 2);
      if (long) {
        const contentStart = i + 2 + long.openLength;
        const closeAt = source.indexOf(long.close, contentStart);
        if (closeAt < 0) throw new Error(`${file}:${line}:${column}: unterminated long comment`);
        i = closeAt + long.close.length;
      } else {
        const newline = source.indexOf("\n", i + 2);
        i = newline < 0 ? source.length : newline;
      }
      const raw = source.slice(start, i);
      tokens.push({ type: "comment", raw, line: startLine, column: startColumn });
      advance(raw);
      segmentStart = i;
      continue;
    }

    if (source[i] === "\"" || source[i] === "'") {
      pushPlain(i);
      const start = i;
      const quote = source[i++];
      advance(quote);
      let closed = false;
      while (i < source.length) {
        if (source[i] === "\\") {
          const escaped = source.slice(i, Math.min(source.length, i + 2));
          i += escaped.length;
          advance(escaped);
        } else if (source[i] === quote) {
          i++;
          advance(quote);
          closed = true;
          break;
        } else {
          advance(source[i]);
          i++;
        }
      }
      if (!closed) throw new Error(`${file}:${startLine}:${startColumn}: unterminated quoted string`);
      const raw = source.slice(start, i);
      tokens.push({
        type: "string",
        kind: "quoted",
        quote,
        raw,
        content: raw.slice(1, -1),
        line: startLine,
        column: startColumn,
      });
      segmentStart = i;
      continue;
    }

    const long = longBracketAt(source, i);
    if (long) {
      pushPlain(i);
      const start = i;
      const contentStart = i + long.openLength;
      const closeAt = source.indexOf(long.close, contentStart);
      if (closeAt < 0) throw new Error(`${file}:${line}:${column}: unterminated long string`);
      i = closeAt + long.close.length;
      const raw = source.slice(start, i);
      tokens.push({
        type: "string",
        kind: "long",
        open: raw.slice(0, long.openLength),
        close: long.close,
        raw,
        content: source.slice(contentStart, closeAt),
        line: startLine,
        column: startColumn,
      });
      advance(raw);
      segmentStart = i;
      continue;
    }

    advance(source[i]);
    i++;
  }
  pushPlain(source.length);
  return tokens;
}

function renderTarget(token, rawContent) {
  if (token.kind === "quoted") return token.quote + rawContent + token.quote;
  return token.open + rawContent + token.close;
}

function nonStringSignature(tokens) {
  return tokens.filter((x) => x.type !== "string").map((x) => `${x.type}\0${x.raw}`);
}

function sameArray(a, b) {
  return a.length === b.length && a.every((value, index) => value === b[index]);
}

function applyCodePatches(file, source) {
  let output = source;
  for (const patch of CODE_PATCHES) {
    if (patch.file !== file) continue;
    const found = output.split(patch.from).length - 1;
    if (found !== patch.count) {
      throw new Error(`${file}: code patch ${JSON.stringify(patch.from)} expected ${patch.count}, found ${found}`);
    }
    output = output.split(patch.from).join(patch.to);
  }
  return output;
}

function containsAsciiWords(value) {
  return /[A-Za-z]{2,}/.test(value);
}

function walkLuaFiles(root) {
  if (!fs.existsSync(root)) return [];
  const result = [];
  const visit = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const full = path.join(directory, entry.name);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile() && entry.name.endsWith(".lua")) result.push(full);
    }
  };
  visit(root);
  return result.sort();
}

function percentTokens(value) {
  return value.match(/%(?:[-+ #0]*\d*(?:\.\d+)?[A-Za-z%]|.)/g) || [];
}

function escapeTokens(value) {
  return value.match(/\\(?:x[0-9A-Fa-f]{2}|u\{[0-9A-Fa-f]+\}|\d{1,3}|\r?\n|.)/g) || [];
}

// Russian terminal text is emitted as Windows-1251 decimal byte escapes.
// Ignore those generated display escapes when checking whether upstream Lua
// control escapes were preserved, and decode them for the residual-prose QA.
const CP1251_DECODER = new TextDecoder("windows-1251");

function structuralEscapeTokens(value) {
  return escapeTokens(value).filter((token) => {
    const match = /^\\(\d{3})$/.exec(token);
    return !match || Number(match[1]) < 128;
  });
}

function decodeTerminalEscapes(value) {
  return value.replace(/\\(\d{3})/g, (token, digits) => {
    const byte = Number(digits);
    if (byte < 128 || byte > 255) return token;
    return CP1251_DECODER.decode(Uint8Array.of(byte));
  });
}

function looksLikeResidualProse(value) {
  if (!containsAsciiWords(value)) return false;
  const words = value.match(/[A-Za-z]{2,}/g) || [];
  if (words.length < 2) return false;
  if (/^(?:https?:\/\/|www\.|\/?rom\/|\.?:\/rom\/)/.test(value)) return false;
  if (/^[A-Za-z0-9_.?*;:/\\-]+$/.test(value)) return false;
  if (/^[%\^$()[\]{}+*?.\\A-Za-z0-9_ :/|<>=!,'"-]+$/.test(value) && /[%\^$\[\]]/.test(value)) return false;
  return true;
}

function isAllowedResidualProse(file, token) {
  const value = token.content;
  // Mixed Russian/technical text is translated prose with preserved commands,
  // API names, settings, formats or types.
  if (/[\u0400-\u04ff]/.test(value)) return true;
  if (/<[^>]+>|\[[a-z][^\]]*\]/i.test(value)) return true; // CLI templates.
  if (/https?:\/\/|www\./.test(value)) return true;

  if (file === "programs/fun/adventure.lua") {
    // The first half contains item keys, aliases, recipes and command grammar.
    if (token.line <= 608) return true;
    // Later occurrences are references to those same stable item keys.
    if (/^(?:a|an|some|no) [a-z ]+$/.test(value)) return true;
  }
  if (file === "modules/main/cc/internal/syntax/init.lua"
      || file === "modules/main/cc/internal/syntax/lexer.lua"
      || file === "modules/main/cc/internal/syntax/parser.lua") return true;

  const exact = new Set([
    "apis/io.lua\0closed file",
    "apis/rednet.lua\0lookup response",
    "modules/main/cc/internal/syntax/errors.lua\0end of file",
    "modules/main/cc/internal/syntax/errors.lua\0No such token ",
    "modules/main/cc/internal/syntax/errors.lua\0local function",
    "programs/fun/advanced/redirection.lua\0nNum == nil",
    "programs/fun/speaker.lua\0help speaker",
    "programs/lua.lua\0return _echo(",
    "programs/motd.lua\0Ed Balls",
  ]);
  if (exact.has(`${file}\0${value}`)) return true;
  if (file === "programs/http/pastebin.lua" && /^api_[a-z_]+=/.test(value)) return true;
  if (file === "programs/rednet/chat.lua" && /^(?:ping|pong) to (?:client|server)$/.test(value)) return true;
  return false;
}

function auditOverlay(sources, printResiduals) {
  const overlayFiles = walkLuaFiles(OUTPUT);
  let changedStrings = 0;
  const effective = new Map(sources);

  for (const full of overlayFiles) {
    const relative = path.relative(OUTPUT, full).split(path.sep).join("/");
    const pristineSource = sources.get(relative);
    if (pristineSource === undefined) throw new Error(`Unexpected Lua overlay file: ${relative}`);
    const source = applyCodePatches(relative, pristineSource);
    const bytes = fs.readFileSync(full);
    if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
      throw new Error(`${relative}: UTF-8 BOM is not allowed`);
    }
    const output = bytes.toString("utf8");
    if (Buffer.from(output, "utf8").compare(bytes) !== 0) throw new Error(`${relative}: invalid UTF-8`);
    const sourceTokens = lexLua(source, relative);
    const outputTokens = lexLua(output, relative);
    if (!sameArray(nonStringSignature(sourceTokens), nonStringSignature(outputTokens))) {
      throw new Error(`${relative}: code or comments differ outside string literals`);
    }
    const sourceStrings = sourceTokens.filter((x) => x.type === "string");
    const outputStrings = outputTokens.filter((x) => x.type === "string");
    if (sourceStrings.length !== outputStrings.length) throw new Error(`${relative}: string-token count differs`);
    for (let i = 0; i < sourceStrings.length; i++) {
      if (sourceStrings[i].content === outputStrings[i].content) continue;
      changedStrings++;
      if (!sameArray(percentTokens(sourceStrings[i].content), percentTokens(outputStrings[i].content))) {
        throw new Error(`${relative}:${sourceStrings[i].line}: percent token mismatch`);
      }
      if (!sameArray(structuralEscapeTokens(sourceStrings[i].content), structuralEscapeTokens(outputStrings[i].content))) {
        throw new Error(`${relative}:${sourceStrings[i].line}: Lua escape mismatch`);
      }
    }
    effective.set(relative, output);
  }

  if (printResiduals) {
    for (const [file, content] of effective) {
      const tokens = lexLua(content, file)
        .filter((x) => x.type === "string")
        .map((x) => ({ ...x, content: decodeTerminalEscapes(x.content) }))
        .filter((x) => looksLikeResidualProse(x.content));
      if (!tokens.length) continue;
      console.log(`\n### ${file}`);
      for (const token of tokens) console.log(`${token.line}:${token.column}\t${JSON.stringify(token.content)}`);
    }
  } else {
    const unclassified = [];
    for (const [file, content] of effective) {
      for (const rawToken of lexLua(content, file)) {
        const token = rawToken.type === "string"
          ? { ...rawToken, content: decodeTerminalEscapes(rawToken.content) }
          : rawToken;
        if (token.type !== "string" || !looksLikeResidualProse(token.content)) continue;
        if (!isAllowedResidualProse(file, token)) {
          unclassified.push(`${file}:${token.line}:${token.column} ${JSON.stringify(token.content)}`);
        }
      }
    }
    if (unclassified.length) {
      throw new Error(`Unclassified residual English prose:\n${unclassified.join("\n")}`);
    }
    console.log(`Audited ${overlayFiles.length} Lua overlays against ${sources.size} JAR sources; ${changedStrings} string literals changed; no unclassified English prose remains.`);
  }
}

function main() {
  const jarBuffer = fs.readFileSync(JAR);
  const actualHash = crypto.createHash("sha256").update(jarBuffer).digest("hex");
  if (actualHash !== EXPECTED_JAR_SHA256) {
    throw new Error(`Unexpected CC:Tweaked JAR SHA-256: ${actualHash}`);
  }
  const zip = readZip(jarBuffer);
  const luaEntries = [...zip.keys()]
    .filter((name) => name.startsWith(ROM_PREFIX) && name.endsWith(".lua"))
    .sort();
  if (luaEntries.length !== EXPECTED_LUA_FILES) {
    throw new Error(`Expected ${EXPECTED_LUA_FILES} ROM Lua files, found ${luaEntries.length}`);
  }

  const sources = new Map(luaEntries.map((entry) => [
    entry.slice(ROM_PREFIX.length),
    zip.get(entry).toString("utf8"),
  ]));

  if (process.argv.includes("--audit") || process.argv.includes("--residual")) {
    auditOverlay(sources, process.argv.includes("--residual"));
    return;
  }

  if (process.argv.includes("--report")) {
    for (const [file, source] of sources) {
      const strings = lexLua(source, file).filter((token) => token.type === "string");
      const candidates = strings.filter((token) => containsAsciiWords(token.content));
      if (!candidates.length) continue;
      console.log(`\n### ${file}`);
      for (const token of candidates) {
        console.log(`${token.line}:${token.column}\t${JSON.stringify(token.content)}`);
      }
    }
    return;
  }

  const byKey = new Map();
  const byPosition = new Map();
  for (const item of TRANSLATIONS) {
    if (item.line !== undefined) {
      const key = `${item.file}:${item.line}:${item.column}`;
      if (byPosition.has(key)) throw new Error(`Duplicate positioned translation ${key}`);
      byPosition.set(key, item);
    } else {
      const key = `${item.file}\0${item.from}`;
      if (byKey.has(key)) throw new Error(`Duplicate translation rule for ${item.file}: ${JSON.stringify(item.from)}`);
      byKey.set(key, item);
    }
  }

  const changedFiles = [];
  const used = new Map();
  for (const [file, pristineSource] of sources) {
    const source = applyCodePatches(file, pristineSource);
    const sourceTokens = lexLua(source, file);
    let changed = false;
    const output = sourceTokens.map((token) => {
      if (token.type !== "string") return token.raw;
      const positionKey = `${file}:${token.line}:${token.column}`;
      let key = positionKey;
      let translation = byPosition.get(positionKey);
      if (!translation) {
        key = `${file}\0${token.content}`;
        translation = byKey.get(key);
      }
      if (!translation) return token.raw;
      if (token.content !== translation.from) {
        throw new Error(`${positionKey}: source mismatch; expected ${JSON.stringify(translation.from)}, got ${JSON.stringify(token.content)}`);
      }
      used.set(key, (used.get(key) || 0) + 1);
      changed = true;
      return renderTarget(token, translation.to);
    }).join("");
    if (!changed) continue;

    const outputTokens = lexLua(output, file);
    if (!sameArray(nonStringSignature(sourceTokens), nonStringSignature(outputTokens))) {
      throw new Error(`${file}: code or comments changed outside string literals`);
    }
    const sourceStrings = sourceTokens.filter((x) => x.type === "string");
    const outputStrings = outputTokens.filter((x) => x.type === "string");
    if (sourceStrings.length !== outputStrings.length) {
      throw new Error(`${file}: string-token count changed`);
    }

    const destination = path.join(OUTPUT, ...file.split("/"));
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.writeFileSync(destination, output, "utf8");
    changedFiles.push(file);
  }

  const badCounts = [];
  for (const [key, item] of [...byKey, ...byPosition]) {
    const actual = used.get(key) || 0;
    if (actual !== item.count) {
      badCounts.push(`${item.file}: ${JSON.stringify(item.from)} expected ${item.count}, found ${actual}`);
    }
  }
  if (badCounts.length) throw new Error(`Translation occurrence mismatches:\n${badCounts.join("\n")}`);
  console.log(`Validated ${luaEntries.length} source Lua files; wrote ${changedFiles.length} translated overlays.`);
  for (const file of changedFiles) console.log(file);
}

main();
