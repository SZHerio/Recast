from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JAR = next((ROOT / "mods").glob("cc-tweaked-1.20.1-forge-1.120.0.jar"))
PREFIX = "data/computercraft/lua/rom/"
OUTPUT = ROOT / "config/paxi/datapacks/IndustrialFrontier-Data/data/computercraft/lua/rom"


REPLACEMENTS: dict[str, dict[str, str]] = {
    "programs/gps.lua": {
        '"Usages:"': '"Варианты использования:"',
        '"GPS Hosts must be stationary"': '"Серверы GPS должны оставаться неподвижными"',
        '"No wireless modems found. 1 required."': '"Беспроводные модемы не найдены. Требуется один модем."',
        '"Position is "': '"Координаты: "',
        '"Run \\"gps host <x> <y> <z>\\" to set position manually"': '"Запустите \\"gps host <x> <y> <z>\\", чтобы задать координаты вручную"',
        '"Opening channel on modem "': '"Открываю канал на модеме "',
        '" GPS requests served"': '" — обработано запросов GPS"',
    },
    "programs/fun/speaker.lua": {
        '"Speaker %q does not exist"': '"Динамик %q не существует"',
        '"%q is not a speaker"': '"%q не является динамиком"',
        '"No speakers attached"': '"Динамики не подключены"',
        '"speaker cannot play %s files."': '"Программа speaker не воспроизводит файлы %s."',
        '"Run \'"': '"Введите \'"',
        '"\' for information on supported formats."': '"\', чтобы узнать о поддерживаемых форматах."',
        '"Usage: speaker play <file or url> [speaker]"': '"Использование: speaker play <file or url> [speaker]"',
        '"Downloading..."': '"Загрузка..."',
        '"Could not play audio:"': '"Не удалось воспроизвести аудио:"',
        '"Could not play audio: Unsupported WAV file"': '"Не удалось воспроизвести аудио: неподдерживаемый файл WAV"',
        '"Warning: Only 48 kHz mono WAV files are supported. This file may not play correctly."': '"Предупреждение: поддерживаются только монофонические файлы WAV с частотой 48 кГц. Этот файл может воспроизводиться неправильно."',
        '"Could not play audio: Invalid WAV file"': '"Не удалось воспроизвести аудио: повреждённый файл WAV"',
        '"Playing "': '"Воспроизводится "',
        '"Usage: speaker sound <sound> [volume] [pitch] [speaker]"': '"Использование: speaker sound <sound> [volume] [pitch] [speaker]"',
        '"Volume must be a number"': '"Громкость должна быть числом"',
        '"Volume must be between 0 and 3"': '"Громкость должна быть от 0 до 3"',
        '"Pitch must be a number"': '"Высота тона должна быть числом"',
        '"Pitch must be between 0 and 2"': '"Высота тона должна быть от 0 до 2"',
        '"Played sound %q on speaker %q with volume %s and pitch %s."': '"Звук %q воспроизведён через динамик %q с громкостью %s и высотой тона %s."',
        '"Could not play sound %q"': '"Не удалось воспроизвести звук %q"',
        '"Usage:"': '"Использование:"',
    },
    "programs/command/commands.lua": {
        '"Requires a Command Computer."': '"Требуется командный компьютер."',
        '"Available commands:"': '"Доступные команды:"',
    },
    "programs/command/exec.lua": {
        '"Requires a Command Computer."': '"Требуется командный компьютер."',
        '"Usage: "': '"Использование: "',
        '"Success"': '"Успешно"',
        '"Failed"': '"Ошибка"',
    },
    "programs/http/pastebin.lua": {
        '"Usages:"': '"Варианты использования:"',
        '"Pastebin requires the http API, but it is not enabled"': '"Для Pastebin требуется API http, но он отключён"',
        '"Set http.enabled to true in CC: Tweaked\'s server config"': '"Установите http.enabled = true в конфигурации сервера CC: Tweaked"',
        '"Invalid pastebin code.\\n"': '"Недопустимый код Pastebin.\\n"',
        '"The code is the ID at the end of the pastebin.com URL.\\n"': '"Код — это ID в конце URL-адреса pastebin.com.\\n"',
        '"Connecting to pastebin.com... "': '"Подключение к pastebin.com... "',
        '"Failed.\\n"': '"Ошибка.\\n"',
        '"Pastebin blocked the download due to spam protection. Please complete the captcha in a web browser: https://pastebin.com/"': '"Pastebin заблокировал загрузку из-за защиты от спама. Пройдите проверку CAPTCHA в браузере: https://pastebin.com/"',
        '"Success."': '"Готово."',
        '"No such file"': '"Файл не найден"',
        '"Uploaded as "': '"Загружено: "',
        '"Run \\"pastebin get "': '"Введите \\"pastebin get "',
        '"\\" to download anywhere"': '"\\", чтобы скачать файл на любом компьютере"',
        '"Failed."': '"Ошибка."',
        '"File already exists"': '"Файл уже существует"',
        '"Downloaded as "': '"Сохранено как "',
    },
    "programs/http/wget.lua": {
        '"Usage:"': '"Использование:"',
        '"wget requires the http API, but it is not enabled"': '"Для wget требуется API http, но он отключён"',
        '"Set http.enabled to true in CC: Tweaked\'s server config"': '"Установите http.enabled = true в конфигурации сервера CC: Tweaked"',
        '"Invalid URL."': '"Недопустимый URL-адрес."',
        '"Connecting to "': '"Подключение к "',
        '"Success."': '"Готово."',
        '"File already exists"': '"Файл уже существует"',
        '"Cannot save file: "': '"Не удалось сохранить файл: "',
        '"Downloaded as "': '"Сохранено как "',
    },
    "programs/rednet/repeat.lua": {
        '"No modems found."': '"Модемы не найдены."',
        '"1 modem found."': '"Найден 1 модем."',
        '" modems found."': '" — найдено модемов."',
        '"0 messages repeated."': '"Повторено сообщений: 0."',
        '" message repeated."': '" — сообщение повторено."',
        '" messages repeated."': '" — повторено сообщений."',
    },
    "programs/turtle/craft.lua": {
        '"Requires a Turtle"': '"Требуется черепаха"',
        '"Requires a Crafty Turtle"': '"Требуется черепаха с верстаком"',
        '"Usage: "': '"Использование: "',
        '" items crafted"': '" — создано предметов"',
        '"1 item crafted"': '"Создан 1 предмет"',
        '"No items crafted"': '"Ничего не создано"',
    },
    "programs/turtle/dance.lua": {
        '"Requires a Turtle"': '"Требуется черепаха"',
        '"Preparing to get down."': '"Готовлюсь зажигать."',
        '"Jamming to "': '"Танцую под "',
        '"Press any key to stop the groove"': '"Нажмите любую клавишу, чтобы остановить танец"',
    },
    "programs/turtle/equip.lua": {
        '"Requires a Turtle"': '"Требуется черепаха"',
        '"Usage: "': '"Использование: "',
        '"Nothing to equip"': '"Нечего устанавливать"',
        '"Items swapped"': '"Предметы поменяны местами"',
        '"Item equipped"': '"Предмет установлен"',
        '"Item not equippable"': '"Этот предмет нельзя установить"',
    },
    "programs/turtle/excavate.lua": {
        '"Requires a Turtle"': '"Требуется черепаха"',
        '"Usage: "': '"Использование: "',
        '"Excavate diameter must be positive"': '"Диаметр карьера должен быть положительным числом"',
        '"Unloading items..."': '"Выгружаю предметы..."',
        '"Returning to surface..."': '"Возвращаюсь на поверхность..."',
        '"Waiting for fuel"': '"Ожидаю топливо"',
        '"Resuming mining..."': '"Продолжаю добычу..."',
        '"Mined "': '"Добыто предметов: "',
        '" items."': '"."',
        '"No empty slots left."': '"Свободных ячеек не осталось."',
        '"Not enough Fuel"': '"Недостаточно топлива"',
        '"Descended "': '"Глубина: "',
        '" metres."': '" м."',
        '"Out of Fuel"': '"Топливо закончилось"',
        '"Excavating..."': '"Начинаю разработку карьера..."',
        '" items total."': '"."',
    },
    "programs/turtle/go.lua": {
        '"Requires a Turtle"': '"Требуется черепаха"',
        '"Usage: "': '"Использование: "',
        '"Out of fuel"': '"Топливо закончилось"',
        '"No such direction: "': '"Неизвестное направление: "',
        '"Try: forward, back, up, down"': '"Доступные варианты: forward, back, up, down"',
    },
    "programs/turtle/refuel.lua": {
        '"Requires a Turtle"': '"Требуется черепаха"',
        '"Usage: "': '"Использование: "',
        '"Invalid limit, expected a number or \\"all\\""': '"Недопустимый предел: укажите число или \\"all\\""',
        '"Fuel level is "': '"Уровень топлива: "',
        '"Fuel limit reached"': '"Достигнут предел запаса топлива"',
        '"Fuel level is unlimited"': '"Запас топлива не ограничен"',
    },
    "programs/turtle/tunnel.lua": {
        '"Requires a Turtle"': '"Требуется черепаха"',
        '"Usage: "': '"Использование: "',
        '"Tunnel length must be positive"': '"Длина туннеля должна быть положительным числом"',
        '"Mined "': '"Добыто предметов: "',
        '" items."': '"."',
        '"Add more fuel to continue."': '"Добавьте топливо, чтобы продолжить."',
        '"Resuming Tunnel."': '"Продолжаю прокладывать туннель."',
        '"Tunnelling..."': '"Прокладываю туннель..."',
        '"Aborting Tunnel."': '"Прокладка туннеля прервана."',
        '"Tunnel complete."': '"Туннель готов."',
        '" items total."': '"."',
    },
    "programs/pocket/equip.lua": {
        '"Requires a Pocket Computer"': '"Требуется карманный компьютер"',
        '"Item equipped"': '"Предмет установлен"',
    },
}


def main() -> None:
    written = []
    with zipfile.ZipFile(JAR) as archive:
        for relative, replacements in REPLACEMENTS.items():
            source = archive.read(PREFIX + relative).decode("utf-8-sig")
            translated = source
            for old, new in replacements.items():
                count = translated.count(old)
                if count == 0:
                    raise RuntimeError(f"{relative}: source literal not found: {old}")
                translated = translated.replace(old, new)
            if translated == source:
                raise RuntimeError(f"{relative}: no changes")
            target = OUTPUT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(translated, encoding="utf-8", newline="\n")
            written.append(relative)
    print(f"written={len(written)}")
    for relative in written:
        print(relative)


if __name__ == "__main__":
    main()
