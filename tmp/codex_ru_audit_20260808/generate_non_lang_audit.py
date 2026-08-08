from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODS = ROOT / "mods"
CSV_PATH = HERE / "non_lang_findings.csv"
JSON_PATH = HERE / "non_lang_summary.json"

WORD_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
LATIN_RE = re.compile(r"[A-Za-z]")
VISIBLE_FIELDS = {
    "name",
    "title",
    "subtitle",
    "description",
    "text",
    "landing_text",
    "tooltip",
    "content",
}


def find_jar(pattern: str) -> Path:
    matches = sorted(MODS.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one JAR for {pattern!r}, found {len(matches)}")
    return matches[0]


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def visible_strings(value: object, field: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.extend(visible_strings(child, str(key)))
    elif isinstance(value, list):
        for child in value:
            found.extend(visible_strings(child, field))
    elif isinstance(value, str) and field.lower() in VISIBLE_FIELDS and LATIN_RE.search(value):
        text = compact(value)
        if text:
            found.append(text)
    return found


def add_row(
    rows: list[dict[str, object]],
    *,
    corpus: str,
    status: str,
    source_path: str,
    peer_path: str = "",
    english_text: str = "",
    note: str = "",
) -> None:
    rows.append(
        {
            "corpus": corpus,
            "status": status,
            "source_path": source_path,
            "peer_path": peer_path,
            "english_text": english_text,
            "word_count": len(WORD_RE.findall(english_text)),
            "note": note,
        }
    )


rows: list[dict[str, object]] = []
parse_errors: list[dict[str, str]] = []

patchouli_specs = [
    (
        "Advanced Peripherals Patchouli",
        find_jar("AdvancedPeripherals-*.jar"),
        "assets/advancedperipherals/patchouli_books/manual/en_us/",
        "assets/advancedperipherals/patchouli_books/manual/ru_ru/",
        "data/advancedperipherals/patchouli_books/manual/book.json",
    ),
    (
        "Lightman's Currency Patchouli",
        find_jar("lightmanscurrency-*.jar"),
        "assets/lightmanscurrency/patchouli_books/trader_guide/en_us/",
        "assets/lightmanscurrency/patchouli_books/trader_guide/ru_ru/",
        "data/lightmanscurrency/patchouli_books/trader_guide/book.json",
    ),
    (
        "Little Logistics Patchouli",
        find_jar("littlelogistics-*.jar"),
        "assets/littlelogistics/patchouli_books/guide/en_us/",
        "assets/littlelogistics/patchouli_books/guide/ru_ru/",
        "data/littlelogistics/patchouli_books/guide/book.json",
    ),
    (
        "PneumaticCraft Patchouli",
        find_jar("pneumaticcraft-repressurized-*.jar"),
        "assets/pneumaticcraft/patchouli_books/book/en_us/",
        "assets/pneumaticcraft/patchouli_books/book/ru_ru/",
        "data/pneumaticcraft/patchouli_books/book/book.json",
    ),
]

for corpus, jar_path, en_prefix, ru_prefix, metadata_path in patchouli_specs:
    with zipfile.ZipFile(jar_path) as archive:
        names = set(archive.namelist())
        for source in sorted(
            name for name in names if name.startswith(en_prefix) and name.endswith(".json")
        ):
            peer = ru_prefix + source[len(en_prefix) :]
            if peer in names:
                continue
            try:
                payload = json.loads(decode(archive.read(source)))
                text = "\n".join(visible_strings(payload))
            except Exception as exc:  # keep the file visible even if malformed
                text = decode(archive.read(source))
                parse_errors.append(
                    {"source": f"mods/{jar_path.name}!/{source}", "error": str(exc)}
                )
            add_row(
                rows,
                corpus=corpus,
                status="missing_ru_file",
                source_path=f"mods/{jar_path.name}!/{source}",
                peer_path=f"mods/{jar_path.name}!/{peer}",
                english_text=text,
                note="Player-visible Patchouli category, entry, or template; translate as a whole in context.",
            )

        if metadata_path in names:
            try:
                payload = json.loads(decode(archive.read(metadata_path)))
                literal = "\n".join(visible_strings(payload))
            except Exception as exc:
                literal = ""
                parse_errors.append(
                    {"source": f"mods/{jar_path.name}!/{metadata_path}", "error": str(exc)}
                )
            if literal:
                add_row(
                    rows,
                    corpus=corpus,
                    status="literal_english_metadata",
                    source_path=f"mods/{jar_path.name}!/{metadata_path}",
                    english_text=literal,
                    note="Literal book metadata is not selected through an en_us/ru_ru peer path.",
                )


ie_jar = find_jar("ImmersiveEngineering-*.jar")
ie_en_prefix = "assets/immersiveengineering/manual/en_us/"
ie_ru_prefix = "assets/immersiveengineering/manual/ru_ru/"
with zipfile.ZipFile(ie_jar) as archive:
    names = set(archive.namelist())
    for source in sorted(
        name for name in names if name.startswith(ie_en_prefix) and name.endswith(".txt")
    ):
        peer = ie_ru_prefix + source[len(ie_en_prefix) :]
        if peer in names:
            continue
        add_row(
            rows,
            corpus="Immersive Engineering manual",
            status="missing_ru_file",
            source_path=f"mods/{ie_jar.name}!/{source}",
            peer_path=f"mods/{ie_jar.name}!/{peer}",
            english_text=decode(archive.read(source)),
            note="Missing Russian manual page; preserve the manual markup while translating.",
        )


nc_jar = find_jar("NuclearCraft-*.jar")
nc_residue = [
    (
        "assets/nuclearcraft/patchouli_books/nuclearcraft/ru_ru/templates/items/material.json",
        "Symbol; Atomic Number; Formula",
    ),
    (
        "assets/nuclearcraft/patchouli_books/nuclearcraft/ru_ru/templates/items/ore.json",
        "Symbol; Atomic Number",
    ),
    (
        "assets/nuclearcraft/patchouli_books/nuclearcraft/ru_ru/templates/particle.json",
        "registry name",
    ),
]
for source, text in nc_residue:
    add_row(
        rows,
        corpus="NuclearCraft Patchouli residue",
        status="english_in_ru",
        source_path=f"mods/{nc_jar.name}!/{source}",
        english_text=text,
        note="Confirmed visible English label inside an otherwise paired Russian book.",
    )


ip_jar = find_jar("ImmersivePetroleum-*.jar")
ip_residue = [
    ("assets/immersivepetroleum/manual/ru_ru/derrick.txt", "redstone"),
    ("assets/immersivepetroleum/manual/ru_ru/fluids.txt", "crude oil; at a slow rate"),
    (
        "assets/immersivepetroleum/manual/ru_ru/lubricant.txt",
        "can be actively lubricated to increase their speed by 25%",
    ),
]
for source, text in ip_residue:
    add_row(
        rows,
        corpus="Immersive Petroleum manual residue",
        status="english_in_ru",
        source_path=f"mods/{ip_jar.name}!/{source}",
        english_text=text,
        note="Confirmed English fragment inside an existing Russian manual page.",
    )

for source, text, note in [
    (
        "assets/immersiveengineering/manual/ru_ru/minerals.txt",
        "Oresome",
        "Confirmed English subtitle in the Russian page.",
    ),
    (
        "assets/immersiveengineering/manual/ru_ru/buzzsaw.txt",
        "config;b;... / of;using>",
        "Broken manual markup, likely visible as garbage; inspect while translating.",
    ),
]:
    add_row(
        rows,
        corpus="Immersive Engineering manual residue",
        status="english_or_broken_markup_in_ru",
        source_path=f"mods/{ie_jar.name}!/{source}",
        english_text=text,
        note=note,
    )


help_specs = [
    ("ComputerCraft ROM help", find_jar("cc-tweaked-*.jar")),
    ("Lightman's Currency ComputerCraft help", find_jar("lightmanscurrency-*.jar")),
]
help_pattern = re.compile(r"^data/computercraft/lua/rom/help/[^/]+$")
for corpus, jar_path in help_specs:
    with zipfile.ZipFile(jar_path) as archive:
        for source in sorted(name for name in archive.namelist() if help_pattern.match(name)):
            add_row(
                rows,
                corpus=corpus,
                status="missing_ru_corpus",
                source_path=f"mods/{jar_path.name}!/{source}",
                english_text=decode(archive.read(source)),
                note="Hard-coded ROM help outside lang JSON; no Russian peer corpus was found.",
            )


rows.sort(key=lambda row: (str(row["corpus"]), str(row["source_path"]), str(row["status"])))
with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "corpus",
            "status",
            "source_path",
            "peer_path",
            "english_text",
            "word_count",
            "note",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

by_corpus: dict[str, dict[str, int]] = {}
for corpus in sorted({str(row["corpus"]) for row in rows}):
    corpus_rows = [row for row in rows if row["corpus"] == corpus]
    by_corpus[corpus] = {
        "rows": len(corpus_rows),
        "ascii_word_tokens": sum(int(row["word_count"]) for row in corpus_rows),
    }

summary = {
    "schema_version": 1,
    "root": ROOT.as_posix(),
    "rows": len(rows),
    "status_counts": dict(Counter(str(row["status"]) for row in rows)),
    "corpora": by_corpus,
    "parse_errors": parse_errors,
    "verified_covered_guides": {
        "ae2_guideme": {"english_pages": 119, "russian_pages": 119, "source": "Paxi"},
        "nuclearcraft_guideme": {"english_pages": 52, "russian_pages": 52, "source": "mod JAR"},
    },
    "notes": [
        "The CSV retains whole visible fragments so future human translation has sentence and page context.",
        "Mod and weapon names occurring inside prose are context markers and must remain unchanged during translation.",
        "No generated Russian translations are included.",
    ],
}
JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps({"csv": CSV_PATH.name, "json": JSON_PATH.name, **summary}, ensure_ascii=False, indent=2))
