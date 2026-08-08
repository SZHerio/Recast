#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Russian EMI tag labels bundled by NuclearCraft.

The source file contains only registry-tag display names.  Most labels repeat
NuclearCraft item/fluid names, so this generator reuses the mod's Russian
terminology and applies reviewed rules to isotopes, fuels, slurries and tag
form plurals.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import pathlib
import re
import zipfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "authoring" / "lang" / "emi.json"

ELEMENTS = {
    "Americium": "Америций",
    "Berkelium": "Берклий",
    "Beryllium": "Бериллий",
    "Boron": "Бор",
    "Caesium": "Цезий",
    "Calcium": "Кальций",
    "Californium": "Калифорний",
    "Cobalt": "Кобальт",
    "Copernicium": "Коперниций",
    "Curium": "Кюрий",
    "Europium": "Европий",
    "Lithium": "Литий",
    "Neptunium": "Нептуний",
    "Plutonium": "Плутоний",
    "Promethium": "Прометий",
    "Protactinium": "Протактиний",
    "Ruthenium": "Рутений",
    "Strontium": "Стронций",
    "Thorium": "Торий",
    "Uranium": "Уран",
}

FUEL_ADJECTIVES = {
    "Americium": "америциевое",
    "Berkelium": "берклиевое",
    "Californium": "калифорниевое",
    "Curium": "кюриевое",
    "Mixed": "смешанное",
    "Neptunium": "нептуниевое",
    "Plutonium": "плутониевое",
    "Thorium": "ториевое",
    "Uranium": "урановое",
    "Xenorium": "ксенориевое",
}

SLURRY_GENITIVE = {
    "Aluminum": "алюминия",
    "Boron": "бора",
    "Cobalt": "кобальта",
    "Copper": "меди",
    "Gold": "золота",
    "Iron": "железа",
    "Lead": "свинца",
    "Lithium": "лития",
    "Magnesium": "магния",
    "Nickel": "никеля",
    "Platinum": "платины",
    "Silver": "серебра",
    "Thorium": "тория",
    "Tin": "олова",
    "Uranium": "урана",
    "Zinc": "цинка",
}

BASE_NAMES = {
    "Aluminum": "Алюминий",
    "Americium": "Америций",
    "Baratol": "Баратол",
    "Berkelium": "Берклий",
    "Beryllium": "Бериллий",
    "Bismuth": "Висмут",
    "Boron": "Бор",
    "Bronze": "Бронза",
    "Carbon Manganese": "Углеродистый марганец",
    "Cobalt": "Кобальт",
    "Depleted Fuel Xenorium Xen-298": "Отработанное ксенориевое топливо XEN-298",
    "Electrum": "Электрум",
    "Extreme": "Экстрим",
    "Ferroboron": "Ферробор",
    "Fissile Fuel": "Делящееся топливо",
    "Fuel Xenorium Xen-298": "Ксенориевое топливо XEN-298",
    "Hafnium": "Гафний",
    "Hard Carbon": "Твёрдый углерод",
    "Hsla Steel": "Сталь HSLA",
    "Lead Platinum": "Свинцово-платиновый сплав",
    "Lithium": "Литий",
    "Lithium Manganese Dioxide": "Литий-марганцевый диоксид",
    "Magnesium": "Магний",
    "Magnesium Diboride": "Диборид магния",
    "Manganese": "Марганец",
    "Manganese Dioxide": "Диоксид марганца",
    "Manganese Oxide": "Оксид марганца",
    "Neptunium": "Нептуний",
    "Palladium": "Палладий",
    "Shibuichi": "Сибуити",
    "Sic Sic Cmc": "Керамический композит SiC–SiC",
    "Silicon Carbide": "Карбид кремния",
    "Silver": "Серебро",
    "Sodium": "Натрий",
    "Steel": "Сталь",
    "Thermoconducting": "Теплопроводящий материал",
    "Tin": "Олово",
    "Tin Silver": "Оловянно-серебряный сплав",
    "Tough Alloy": "Прочный сплав",
    "Zinc": "Цинк",
    "Zircaloy": "Циркалой",
    "Zirconium": "Цирконий",
    "Zirconium Molybdenum": "Цирконий-молибденовый сплав",
}

RAW_NAMES = {
    "Boron Raw": "Необработанный бор",
    "Cobalt Raw": "Необработанный кобальт",
    "Lead Raw": "Необработанный свинец",
    "Lithium Raw": "Необработанный литий",
    "Magnesium Raw": "Необработанный магний",
    "Platinum Raw": "Необработанная платина",
    "Silver Raw": "Необработанное серебро",
    "Thorium Raw": "Необработанный торий",
    "Tin Raw": "Необработанное олово",
    "Uranium Raw": "Необработанный уран",
    "Zinc Raw": "Необработанный цинк",
}

SPECIAL_FORMS = {
    "Neutronium Ingots": "Нейтрониевые слитки",
    "Tungsten Carbide Ingots": "Слитки карбида вольфрама",
}

FORM_OVERRIDES = {
    "Arsenic Dusts": "Пыль мышьяка",
    "Bscco Dusts": "Пыль BSCCO",
    "Charcoal Dusts": "Пыль древесного угля",
    "Coal Dusts": "Угольная пыль",
    "Cobalt Dusts": "Кобальтовая пыль",
    "Dimensional Blend Dusts": "Пыль межпространственной смеси",
    "Europium 155 Dusts": "Пыль европия-155",
    "Extreme Dusts": "Пыль экстрима",
    "Iodine Dusts": "Пыль йода",
    "Irradiated Borax Dusts": "Облучённая пыль боракса",
    "Lead Platinum Dusts": "Пыль свинцово-платинового сплава",
    "Lithium Manganese Dioxide Dusts": "Пыль литий-марганцевого диоксида",
    "Potassium Fluoride Dusts": "Пыль фторида калия",
    "Potassium Hydroxide Dusts": "Пыль гидроксида калия",
    "Potassium Iodide Dusts": "Пыль йодида калия",
    "Promethium 147 Dusts": "Пыль прометия-147",
    "Pyrolitic Carbon Dusts": "Пыль пиролитического углерода",
    "Ruthenium 106 Dusts": "Пыль рутения-106",
    "Shibuichi Dusts": "Пыль сибуити",
    "Sic Sic Cmc Dusts": "Пыль керамического композита SiC–SiC",
    "Silicon Carbide Dusts": "Пыль карбида кремния",
    "Strontium 90 Dusts": "Пыль стронция-90",
    "Sulfur Dusts": "Серная пыль",
    "Tbp Dusts": "Пыль TBP",
    "Tin Silver Dusts": "Пыль оловянно-серебряного сплава",
    "Zirconium Molybdenum Dusts": "Пыль цирконий-молибденового сплава",
    "Lead Platinum Ingots": "Слитки свинцово-платинового сплава",
    "Lithium Manganese Dioxide Ingots": "Слитки литий-марганцевого диоксида",
    "Potassium Ingots": "Слитки калия",
    "Pyrolitic Carbon Ingots": "Слитки пиролитического углерода",
    "Shibuichi Ingots": "Слитки сибуити",
    "Sic Sic Cmc Ingots": "Слитки керамического композита SiC–SiC",
    "Silicon Carbide Ingots": "Слитки карбида кремния",
    "Tin Silver Ingots": "Слитки оловянно-серебряного сплава",
    "Zirconium Molybdenum Ingots": "Слитки цирконий-молибденового сплава",
    "Lithium Manganese Dioxide Plates": "Пластины литий-марганцевого диоксида",
    "Sic Sic Cmc Plates": "Пластины керамического композита SiC–SiC",
}


def normalize_russian(value: str) -> str:
    value = value.replace("Флюорид", "Фторид").replace("флюорид", "фторид")
    value = value.replace("Облученная", "Облучённая").replace("облученная", "облучённая")
    value = value.replace("Измельченный", "Измельчённый").replace("Твердого", "Твёрдого")
    # Registry labels use sentence case; core translations occasionally use
    # English-style title capitalization.
    return re.sub(
        r"(?<!^)\b([А-ЯЁ])([а-яё]+)",
        lambda match: match.group(1).lower() + match.group(2),
        value,
    )


def fuel_name(material: str, rest: str, depleted: bool) -> str:
    parts = rest.split(" ")
    code = parts[0].upper()
    suffix = " ".join(parts[1:])
    adjective = FUEL_ADJECTIVES[material]
    result = f"{adjective.capitalize()} топливо {code}"
    if depleted:
        result = f"Отработанное {adjective} топливо {code}"
    if suffix:
        result += f" {suffix}"
    return result


def compact_fuel_name(key: str) -> str | None:
    depleted_marker = ".depleted_reactor_fuel."
    live_marker = ".reactor_fuel."
    if depleted_marker in key:
        token = key.split(depleted_marker, 1)[1]
        depleted = True
    elif live_marker in key:
        token = key.split(live_marker, 1)[1]
        depleted = False
    else:
        return None
    for material in sorted(FUEL_ADJECTIVES, key=len, reverse=True):
        prefix = material.lower()
        if token.startswith(prefix):
            rest = token[len(prefix):]
            return fuel_name(material, rest, depleted)
    raise ValueError(f"Unknown compact fuel tag: {key}")


def choose(counter: Counter[str]) -> str:
    # Prefer the community wording used by the greatest number of core keys.
    # Stable lexical ordering makes ties deterministic.
    return sorted(counter, key=lambda value: (-counter[value], value))[0]


def main() -> None:
    jar = next((ROOT / "mods").glob("NuclearCraft*.jar"))
    with zipfile.ZipFile(jar) as archive:
        emi_en = json.loads(archive.read("assets/emi/lang/en_us.json").decode("utf-8-sig"))
        nc_en = json.loads(archive.read("assets/nuclearcraft/lang/en_us.json").decode("utf-8-sig"))
        nc_ru = json.loads(archive.read("assets/nuclearcraft/lang/ru_ru.json").decode("utf-8-sig"))

    by_english: dict[str, Counter[str]] = defaultdict(Counter)
    for key, english in nc_en.items():
        russian = nc_ru.get(key)
        if russian and russian != english:
            by_english[str(english)][str(russian)] += 1

    singular_suffixes = {
        " Dusts": " Dust",
        " Ingots": " Ingot",
        " Nuggets": " Nugget",
        " Plates": " Plate",
    }

    translated: dict[str, str] = {}
    unresolved: list[tuple[str, str]] = []
    isotope_re = re.compile(
        r"^(Americium|Berkelium|Beryllium|Boron|Caesium|Calcium|Californium|"
        r"Cobalt|Copernicium|Curium|Europium|Lithium|Neptunium|Plutonium|"
        r"Promethium|Protactinium|Ruthenium|Strontium|Thorium|Uranium) "
        r"(\d+)(?: (Ni|Ox|Za))?$"
    )
    fuel_re = re.compile(
        r"^(Depleted )?Fuel (Americium|Berkelium|Californium|Curium|Mixed|"
        r"Neptunium|Plutonium|Thorium|Uranium|Xenorium) (.+)$"
    )

    for key, english in emi_en.items():
        compact = compact_fuel_name(key)
        if compact is not None:
            translated[key] = compact
            continue

        match = fuel_re.match(english)
        if match:
            translated[key] = fuel_name(match.group(2), match.group(3), bool(match.group(1)))
            continue

        match = isotope_re.match(english)
        if match:
            suffix = f" {match.group(3)}" if match.group(3) else ""
            translated[key] = f"{ELEMENTS[match.group(1)]}-{match.group(2)}{suffix}"
            continue

        if english.endswith(" Clean Slurry"):
            material = english[: -len(" Clean Slurry")]
            translated[key] = f"Очищенная суспензия {SLURRY_GENITIVE[material]}"
            continue
        if english.endswith(" Slurry"):
            material = english[: -len(" Slurry")]
            translated[key] = f"Суспензия {SLURRY_GENITIVE[material]}"
            continue

        if english in BASE_NAMES:
            translated[key] = BASE_NAMES[english]
            continue
        if english in RAW_NAMES:
            translated[key] = RAW_NAMES[english]
            continue
        if english in SPECIAL_FORMS:
            translated[key] = SPECIAL_FORMS[english]
            continue
        if english in FORM_OVERRIDES:
            translated[key] = FORM_OVERRIDES[english]
            continue
        if english in by_english:
            translated[key] = choose(by_english[english])
            continue

        for plural, singular in singular_suffixes.items():
            if english.endswith(plural):
                singular_name = english[: -len(plural)] + singular
                if singular_name in by_english:
                    translated[key] = choose(by_english[singular_name])
                    break
        else:
            unresolved.append((key, english))

    if unresolved:
        details = "\n".join(f"{key} = {value}" for key, value in unresolved[:20])
        raise SystemExit(f"Unresolved EMI labels ({len(unresolved)}):\n{details}")
    if len(translated) != len(emi_en):
        raise SystemExit(f"Expected {len(emi_en)} labels, generated {len(translated)}")

    translated = {key: normalize_russian(value) for key, value in translated.items()}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({key: translated[key] for key in sorted(translated)}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"emi: generated {len(translated)} reviewed tag labels")


if __name__ == "__main__":
    main()
