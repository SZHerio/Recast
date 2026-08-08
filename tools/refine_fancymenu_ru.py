#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Исправляет смешанный русско-английский текст в локализации FancyMenu.

Правки здесь намеренно ограничены видимой прозой и названиями элементов
редактора. Имена мода, форматы, имена переменных и фрагменты кода остаются
неизменными, чтобы документация редактора не перестала соответствовать API.
"""

from __future__ import annotations

import json
import pathlib
import re
import zipfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
JAR = next((ROOT / "mods").glob("fancymenu_forge_*.jar"))
TARGET = ROOT / "authoring" / "fragments" / "fancymenu_mixed_ui.json"
MAIN = ROOT / "authoring" / "lang" / "fancymenu.json"


def replace_editor_terms(text: str) -> str:
    # Названия действий и элементов, которые игрок видит в самом редакторе.
    replacements = (
        ("часть элемента Ticker, который запущен в режиме Async", "частью элемента-таймера, запущенного асинхронно"),
        ("часть элемента Ticker, который работает в режиме Async", "частью элемента-таймера, работающего асинхронно"),
        ("элемента Ticker", "элемента-таймера"),
        ("элемента Audio", "аудиоэлемента"),
        ("элементом Audio", "аудиоэлементом"),
        ("элементы Audio", "аудиоэлементы"),
        ("элемент Audio", "аудиоэлемент"),
        ("Element Animator", "аниматор элементов"),
        ("EXECUTE LATER", "ВЫПОЛНИТЬ ПОЗЖЕ"),
        ("Execute Later", "Выполнить позже"),
        ("FM Variable", "переменная FancyMenu"),
        ("Copy Background Identifier", "Копировать идентификатор фона"),
        ("On ZIP Extracted via Action", "После распаковки ZIP действием"),
        ("Debug Overlay", "отладочный экран"),
        ("Open Screen or Custom GUI", "Открыть экран или пользовательский интерфейс"),
        ("Play Audio", "Воспроизвести звук"),
        ("AFMA Creator", "редактор AFMA"),
        ("Best Quality", "Лучшее качество"),
        ("Balanced", "Сбалансированный"),
        ("Smallest File", "Минимальный размер файла"),
        ("Shader Source", "Исходный код шейдера"),
        ("iMouse Position", "Положение iMouse"),
        ("Minecraft Text Components", "текстовые компоненты Minecraft"),
        ("Mimic Button", "Имитировать кнопку"),
        ("Advanced FancyMenu Animation", "Расширенная анимация FancyMenu"),
        ("Force GUI Scale", "Задать масштаб интерфейса"),
        ("Modpack Mode", "режим сборки"),
        ("Unix timestamp", "метка времени Unix"),
        ("Java Virtual Machine", "виртуальная машина Java"),
        ("Rect-Copy", "копирование прямоугольников"),
        ("IANA timezone IDs", "идентификаторы часовых поясов IANA"),
        ("IANA timezone", "часовой пояс IANA"),
        ("сообщения action bar", "сообщения в строке действий"),
        ("сообщение action bar", "сообщение в строке действий"),
        ("action bar", "строка действий"),
        ("Vanilla Minecraft", "ванильный Minecraft"),
        ("папке ASSETS FancyMenu", "папке ресурсов FancyMenu"),
        ("ASSETS FancyMenu", "ресурсы FancyMenu"),
    )
    for old, new in replacements:
        text = text.replace(old, new)

    # Термины шейдерного редактора. Имена GLSL-переменных и точки входа
    # main/mainImage не меняются.
    shader_replacements = (
        ("многошаговых/feedback-схем", "многопроходных схем с обратной связью"),
        ("многопроходных/feedback-схем", "многопроходных схем с обратной связью"),
        ("мультипроходных/feedback-схем", "многопроходных схем с обратной связью"),
        ("feedback-схем", "схем с обратной связью"),
        ("прямых fragment-шейдерах", "прямых фрагментных шейдерах"),
        ("прямых fragment shader", "прямых фрагментных шейдерах"),
        ("fragment-шейдерах", "фрагментных шейдерах"),
        ("fragment shader code", "код фрагментного шейдера"),
        ("fragment shader", "фрагментный шейдер"),
        ("fragment-шейдера", "фрагментного шейдера"),
        ("fragment-шейдер", "фрагментный шейдер"),
        ("fragment-код", "код фрагментного шейдера"),
        ("fragment code", "код фрагментного шейдера"),
        ("direct fragment-", "прямого фрагментного "),
        ("прямой fragment-", "прямой фрагментный "),
        ("прямых fragment ", "прямых фрагментных шейдерах "),
        ("fragment style", "фрагментный режим"),
        ("fragment-стиле", "фрагментном режиме"),
        ("fragment-стиль", "фрагментный режим"),
        ("uniform'а", "униформы"),
        ("uniform iChannel", "униформы iChannel"),
        ("runtime uniforms", "униформы времени выполнения"),
        ("input uniforms", "входные униформы"),
        ("resource location-источники", "источники по идентификатору ресурса"),
        ("resource location", "идентификатор ресурса"),
        ("fallback-текстуру", "резервную текстуру"),
        ("fallback-текстура", "резервная текстура"),
    )
    for old, new in shader_replacements:
        text = text.replace(old, new)

    # Грамматические формы названий проходов Shadertoy.
    text = text.replace("выходы Buffer A-D", "выходы буферов A–D")
    text = text.replace("выводы Buffer A-D", "выходы буферов A–D")
    text = text.replace("текстуры выхода Buffer A-D", "выходные текстуры буферов A–D")
    text = text.replace("текстуры вывода Buffer A-D", "выходные текстуры буферов A–D")
    text = text.replace("между Buffer A-D", "между буферами A–D")
    text = text.replace("источники Buffer A-D", "исходники буферов A–D")
    text = text.replace("поля источника Buffer A-D", "поля исходного кода буферов A–D")
    text = text.replace("поля Source для Buffer A-D", "поля исходного кода буферов A–D")
    text = text.replace("Buffer A-D", "буферы A–D")
    text = re.sub(r"Вход Buffer ([A-D]) (iChannel\d)", r"Вход \2 буфера \1", text)
    text = re.sub(r"Вход (iChannel\d) для Buffer ([A-D])", r"Вход \1 буфера \2", text)
    text = re.sub(r"проходе Buffer ([A-D])", r"проходе буфера \1", text)
    text = re.sub(r"прохода Buffer ([A-D])", r"прохода буфера \1", text)
    text = re.sub(r"проход Buffer ([A-D])", r"проход буфера \1", text)
    text = re.sub(r"для Buffer ([A-D])", r"для буфера \1", text)
    text = re.sub(r"Источник Buffer ([A-D])", r"Исходный код буфера \1", text)
    text = re.sub(r"\bBuffer ([A-D])\b", r"буфер \1", text)
    text = text.replace("проходе Image", "проходе изображения")
    text = text.replace("прохода Image", "прохода изображения")
    text = text.replace("для Image", "для изображения")
    text = text.replace("Источник Image", "Исходный код изображения")
    text = re.sub(r"Вход Image (iChannel\d)", r"Вход \1 изображения", text)
    text = text.replace("поля Source", "поля исходного кода")
    text = text.replace("внешние ресурс-каналы", "внешние каналы ресурсов")
    text = text.replace("внешние ресурсные каналы", "внешние каналы ресурсов")
    text = text.replace("многопроходных сетапов", "многопроходных схем")
    text = re.sub(
        r"Выбери, что будет сэмплировать (iChannel\d) в",
        r"Выбери, откуда \1 будет получать данные в",
        text,
    )
    text = re.sub(
        r"Выберите, что будет сэмплировать (iChannel\d) прохода",
        r"Выберите источник данных для \1 прохода",
        text,
    )
    text = text.replace("в Исходный код шейдера", "в поле «Исходный код шейдера»")
    text = text.replace("Исходный код фрагментный шейдер", "Исходный код фрагментного шейдера")
    text = text.replace(
        "обычный текстовый GLSL фрагментный шейдер",
        "обычный текстовый код фрагментного шейдера GLSL",
    )
    text = text.replace("кодом фрагментный шейдер", "кодом фрагментного шейдера")
    text = text.replace("прямой фрагментный стиль", "прямой фрагментный режим")
    text = text.replace("'Копировать идентификатор фона'", "«Копировать идентификатор фона»")
    text = text.replace(
        "'Открыть экран или пользовательский интерфейс'",
        "«Открыть экран или пользовательский интерфейс»",
    )

    # Девятисекционное масштабирование текстур.
    nine_slice = (
        ("Своя Nine-Slice подложка", "Своя девятисекционная подложка"),
        ("Нижняя граница Nine-Slice", "Нижняя граница девятисекционного"),
        ("Левая граница Nine-Slice", "Левая граница девятисекционного"),
        ("Правая граница Nine-Slice", "Правая граница девятисекционного"),
        ("Верхняя граница Nine-Slice", "Верхняя граница девятисекционного"),
        ("Nine-Slice текстура", "Девятисекционная текстура"),
        ("Nine-Slice фоны", "Девятисекционные фоны"),
        ("Nine-Slice фон", "Девятисекционный фон"),
        ("Nine-Slice бегунок", "Девятисекционный бегунок"),
        ("Границы Nine-Slice", "Границы девятисекционной разметки"),
        ("Фон с nine-slice", "Девятисекционный фон"),
        ("Полоса с nine-slice", "Девятисекционная полоса"),
        ("Пользовательский бегунок с nine-slice", "Пользовательский девятисекционный бегунок"),
        ("Границы бегунка по X в nine-slice", "Границы девятисекционного бегунка по X"),
        ("Границы бегунка по Y в nine-slice", "Границы девятисекционного бегунка по Y"),
        ("логикой nine-slicing", "логикой девятисекционного масштабирования"),
        ("Настройки nine-slicing", "Настройки девятисекционного масштабирования"),
        ("nine-slicing", "девятисекционное масштабирование"),
        ("Nine-Slice", "девятисекционная разметка"),
        ("nine-slice", "девятисекционная разметка"),
    )
    for old, new in nine_slice:
        text = text.replace(old, new)

    # Человекочитаемые примеры для преобразования регистра.
    examples = (
        ("alternating case", "чередующийся регистр"),
        ("aLtErNaTiNg CaSe", "чЕрЕдУюЩиЙ рЕгИсТр"),
        ("Title Case", "заглавные начала слов"),
        ("Toggle Case", "Смена Регистра"),
        ("tOGGLE cASE", "сМЕНА рЕГИСТРА"),
        ("HELLO WORLD", "ПРИВЕТ, МИР"),
        ("Hello World", "Привет, мир"),
        ("hello world", "привет, мир"),
        ("this is fancymenu", "это FancyMenu"),
        ("This is fancymenu", "Это FancyMenu"),
        ("Cool Name", "Любимый трек"),
        ("Another Name", "Другой трек"),
    )
    for old, new in examples:
        text = text.replace(old, new)
    if text == "Image":
        text = "Изображение"
    return text


def main() -> int:
    with zipfile.ZipFile(JAR) as archive:
        russian = json.loads(archive.read("assets/fancymenu/lang/ru_ru.json").decode("utf-8-sig"))

    overrides: dict[str, str] = {}
    for key, value in russian.items():
        if not isinstance(value, str):
            continue
        refined = replace_editor_terms(value)
        if refined != value:
            overrides[key] = refined

    overrides["fancymenu.elements.in_editor_display_name.desc"] = (
        "Отображаемое имя помогает поддерживать порядок в редакторе.\n"
        "Оно показывается в списке слоёв и в меню выбора элемента по ПКМ."
    )
    overrides["fancymenu.placeholders.title_case_text"] = "Текст с заглавными началами слов"
    overrides["fancymenu.placeholders.unix_time"] = "Текущее время в миллисекундах (метка времени Unix)"

    existing = json.loads(MAIN.read_text(encoding="utf-8")) if MAIN.exists() else {}
    for key in tuple(overrides):
        if key in existing:
            del overrides[key]

    # Наши замены не должны затронуть управляющие коды и подстановки.
    token_re = re.compile(r"%(?:\d+\$)?[a-zA-Z%]|§.|\$\([^)]*\)")
    for key, refined in overrides.items():
        before = russian[key]
        if token_re.findall(before) != token_re.findall(refined):
            raise SystemExit(f"Повреждены управляющие токены: {key}")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps(dict(sorted(overrides.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"FancyMenu: подготовлено {len(overrides)} редакторских исправлений -> {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
