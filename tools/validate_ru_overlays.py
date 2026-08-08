"""Validate the Russian resource/data-pack overlays shipped with the instance.

The checks are intentionally source-backed: translated Patchouli pages and
ComputerCraft help are compared with the exact files in the installed mod JARs.
Only the Python standard library is required.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import pathlib
import re
import sys
import zipfile
from collections.abc import Iterator
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
RESOURCE_PACK = ROOT / "config/paxi/resourcepacks/IndustrialFrontier-Core"
DATA_PACK = ROOT / "config/paxi/datapacks/IndustrialFrontier-Data"
PNC_TARGET = (
    RESOURCE_PACK
    / "assets/pneumaticcraft/patchouli_books/book/ru_ru"
)
CC_ROM_TARGET = DATA_PACK / "data/computercraft/lua/rom"
CC_HELP_AUTHORING = ROOT / "authoring/computercraft/help"
CC_TERM_FONT = (
    RESOURCE_PACK / "assets/computercraft/textures/gui/term_font.png"
)
BASELINE = ROOT / "tmp/codex_ru_audit_20260808/non_lang_findings.csv"

PNC_SOURCE_PREFIX = (
    "assets/pneumaticcraft/patchouli_books/book/en_us/"
)
CC_ROM_SOURCE_PREFIX = "data/computercraft/lua/rom/"
CC_TERM_FONT_SHA256 = (
    "db4c4a8ab49265f6e8e456f495800ea148b133b18a3242aabca30b98ab7f784f"
)
CC_UNSAFE_GLYPH_BYTES = frozenset(range(0x80, 0xA0)) | {
    0xA3, 0xA5, 0xBC, 0xBD, 0xBE,
}
VISIBLE_PATCHOULI_KEYS = {
    "name", "text", "title", "description", "link_text", "header",
}
PNC_WEAPON_PAGES = {
    "entries/tools/minigun.json",
    "entries/tools/minigun_ammo.json",
    "entries/tools/micromissiles.json",
    "entries/tools/vortex_cannon.json",
}

PATCHOULI_TOKEN = re.compile(r"\$\([^)]*\)|/\$")
PRINTF_TOKEN = re.compile(
    # A literal percentage followed by prose ("20% of") is not printf. The
    # rarely used printf space flag is deliberately excluded to avoid treating
    # ordinary manual text as a format token.
    r"(?<!\d)%(?:\d+\$)?[-+#0]*(?:\d+|\*)?(?:\.\d+|\.\*)?"
    r"(?:hh|h|ll|l|L|z|j|t)?[diuoxXfFeEgGaAcspq%]"
)
BRACE_TOKEN = re.compile(r"\{\d+\}")
LANG_PATH = re.compile(r"^assets/([^/]+)/lang/(en_us|ru_ru)\.json$", re.IGNORECASE)
LANG_PRINTF_TOKEN = re.compile(
    r"%%|%(?:\d+\$)?[-+#0]*(?:\d+|\*)?(?:\.\d+|\.\*)?"
    r"(?:hh|h|ll|l|L|z|j|t)?[diuoxXfFeEgGaAcspq]"
)
CC_DECIMAL_ESCAPE = re.compile(r"\\(\d{1,3})")
CYRILLIC = re.compile(r"[А-Яа-яЁё]")
CC_HELP_RUNTIME_TRANSLATION = str.maketrans({"—": "-"})

KNOWN_STRAGGLER_GUARDS: dict[pathlib.Path, tuple[str, ...]] = {
    CC_HELP_AUTHORING / "hello.txt": ("Привет, мир!",),
    CC_HELP_AUTHORING / "type.txt": ("файл", "каталог", "Путь не найден"),
    CC_HELP_AUTHORING / "label.txt": ("Мой компьютер", "Мои программы"),
    CC_HELP_AUTHORING / "commandsapi.txt": ("Привет, мир!",),
    CC_HELP_AUTHORING / "exec.txt": ("Привет, мир!",),
    CC_HELP_AUTHORING / "changelog.md": (
        "Возможно, ComputerCraft установлен неправильно",
        "Не удалось",
        "«Запустить»",
        "«Включить»/«Выключить»",
        "Сенсорная черепаха",
    ),
    PNC_TARGET / "entries/machines/drone_interface.json": (
        "-- ждём завершения, как выше",
    ),
}


class Audit:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats: dict[str, int] = {}

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def count(self, name: str, amount: int = 1) -> None:
        self.stats[name] = self.stats.get(name, 0) + amount


def one_jar(pattern: str) -> pathlib.Path:
    matches = sorted((ROOT / "mods").glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one JAR matching {pattern!r}, found {len(matches)}")
    return matches[0]


def read_utf8(path: pathlib.Path, audit: Audit) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        audit.error(f"Cannot read {path.relative_to(ROOT)}: {exc}")
        return None
    if raw.startswith(b"\xef\xbb\xbf"):
        audit.error(f"UTF-8 BOM is not allowed: {path.relative_to(ROOT)}")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        audit.error(f"Invalid UTF-8 in {path.relative_to(ROOT)}: {exc}")
        return None


def read_cp1251(path: pathlib.Path, audit: Audit) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        audit.error(f"Cannot read {path.relative_to(ROOT)}: {exc}")
        return None
    try:
        return raw.decode("cp1251")
    except UnicodeDecodeError as exc:
        audit.error(f"Invalid Windows-1251 in {path.relative_to(ROOT)}: {exc}")
        return None


def load_json(path: pathlib.Path, audit: Audit) -> Any | None:
    text = read_utf8(path, audit)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        audit.error(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")
        return None


def iter_json_files() -> Iterator[pathlib.Path]:
    roots = [
        ROOT / "authoring/lang",
        ROOT / "authoring/fragments",
        RESOURCE_PACK,
        DATA_PACK,
    ]
    for base in roots:
        if base.exists():
            yield from base.rglob("*.json")


def normalized_patchouli_tokens(value: str) -> list[str]:
    result: list[str] = []
    for token in PATCHOULI_TOKEN.findall(value):
        # Tooltip prose is visible and should be translated. The surrounding
        # token remains mandatory, while its payload may differ by locale.
        if token.startswith("$(t:"):
            result.append("$(t:*)")
        else:
            result.append(token)
    return result


def validate_patchouli_value(
    source: str,
    target: str,
    location: str,
    audit: Audit,
) -> None:
    source_tokens = normalized_patchouli_tokens(source)
    target_tokens = normalized_patchouli_tokens(target)
    if source_tokens != target_tokens:
        audit.error(f"Patchouli token mismatch at {location}")
    if source.count("$(") != len(PATCHOULI_TOKEN.findall(source)) - source.count("/$"):
        audit.error(f"Malformed Patchouli token in source at {location}")
    if target.count("$(") != len(PATCHOULI_TOKEN.findall(target)) - target.count("/$"):
        audit.error(f"Malformed Patchouli token in translation at {location}")
    if PRINTF_TOKEN.findall(source) != PRINTF_TOKEN.findall(target):
        audit.error(f"printf token mismatch at {location}")
    if BRACE_TOKEN.findall(source) != BRACE_TOKEN.findall(target):
        audit.error(f"numbered placeholder mismatch at {location}")


def compare_json_shape(
    source: Any,
    target: Any,
    location: str,
    audit: Audit,
    key: str | None = None,
) -> None:
    if type(source) is not type(target):
        audit.error(f"JSON type mismatch at {location}")
        return
    if isinstance(source, dict):
        if list(source) != list(target):
            audit.error(f"JSON key/order mismatch at {location}")
            return
        for child_key in source:
            compare_json_shape(
                source[child_key],
                target[child_key],
                f"{location}.{child_key}",
                audit,
                child_key,
            )
        return
    if isinstance(source, list):
        if len(source) != len(target):
            audit.error(f"JSON list length mismatch at {location}")
            return
        for index, (source_item, target_item) in enumerate(zip(source, target)):
            compare_json_shape(
                source_item,
                target_item,
                f"{location}[{index}]",
                audit,
                key,
            )
        return
    if isinstance(source, str):
        if key in VISIBLE_PATCHOULI_KEYS:
            validate_patchouli_value(source, target, location, audit)
        elif source != target:
            audit.error(f"Technical Patchouli value changed at {location}")
        return
    if source != target:
        audit.error(f"Technical JSON value changed at {location}")


def validate_all_json(audit: Audit) -> None:
    seen: set[pathlib.Path] = set()
    for path in iter_json_files():
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if load_json(path, audit) is not None:
            audit.count("json_files")


def validate_pneumaticcraft(audit: Audit) -> None:
    jar = one_jar("pneumaticcraft-repressurized-6.0.23+mc1.20.1.jar")
    with zipfile.ZipFile(jar) as archive:
        source_entries = sorted(
            name
            for name in archive.namelist()
            if name.startswith(PNC_SOURCE_PREFIX) and name.endswith(".json")
        )
        source_relatives = {
            name.removeprefix(PNC_SOURCE_PREFIX) for name in source_entries
        }
        target_relatives = {
            path.relative_to(PNC_TARGET).as_posix()
            for path in PNC_TARGET.rglob("*.json")
        }
        missing = sorted(source_relatives - target_relatives)
        extra = sorted(target_relatives - source_relatives)
        for relative in missing:
            audit.error(f"Missing PneumaticCraft page: {relative}")
        for relative in extra:
            audit.error(f"Unexpected PneumaticCraft page: {relative}")

        for source_name in source_entries:
            relative = source_name.removeprefix(PNC_SOURCE_PREFIX)
            target_path = PNC_TARGET / pathlib.PurePosixPath(relative)
            if not target_path.exists():
                continue
            try:
                source = json.loads(archive.read(source_name).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                audit.error(f"Invalid source page {relative}: {exc}")
                continue
            target = load_json(target_path, audit)
            if target is None:
                continue
            compare_json_shape(source, target, relative, audit)
            if relative in PNC_WEAPON_PAGES:
                if source.get("name") != target.get("name"):
                    audit.error(f"Weapon name was translated in {relative}")
            audit.count("pnc_pages")

    # Terminology rejected during editorial review must not reappear.
    forbidden = {
        "гаджет передачи": "передающий модуль",
        "тепловая рамка сущности": "тепловая рамка",
        "термопневматический завод": "термопневматическая перерабатывающая установка",
    }
    for path in PNC_TARGET.rglob("*.json"):
        text = path.read_text(encoding="utf-8").lower()
        for bad, preferred in forbidden.items():
            if bad in text:
                audit.error(
                    f"Rejected term {bad!r} in {path.relative_to(PNC_TARGET)}; "
                    f"use {preferred!r}"
                )


def validate_non_lang_baseline(audit: Audit) -> None:
    if not BASELINE.exists():
        audit.warning("Non-language baseline is absent; coverage check skipped")
        return
    with BASELINE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if (
            row["corpus"] == "PneumaticCraft Patchouli"
            and row["status"] == "literal_english_metadata"
        ):
            # The values are localization keys, not visible English text.
            audit.count("non_lang_allowed_metadata")
            continue
        try:
            internal = row["source_path"].split("!/", 1)[1]
        except IndexError:
            audit.error(f"Bad baseline source path: {row['source_path']}")
            continue
        if row["status"] == "missing_ru_file":
            internal = internal.replace("/en_us/", "/ru_ru/")
        if internal.startswith("assets/"):
            target = RESOURCE_PACK / pathlib.PurePosixPath(internal)
        elif internal.startswith("data/"):
            target = DATA_PACK / pathlib.PurePosixPath(internal)
        else:
            audit.error(f"Unsupported baseline path: {internal}")
            continue
        if target.exists():
            audit.count("non_lang_covered")
        else:
            audit.error(
                f"Missing non-language override for {row['corpus']}: "
                f"{target.relative_to(ROOT)}"
            )
    audit.stats["non_lang_baseline_rows"] = len(rows)


def validate_cc_help(audit: Audit) -> None:
    jar = one_jar("cc-tweaked-1.20.1-forge-1.120.0.jar")
    prefix = CC_ROM_SOURCE_PREFIX + "help/"
    with zipfile.ZipFile(jar) as archive:
        entries = sorted(
            name for name in archive.namelist()
            if name.startswith(prefix) and not name.endswith("/")
        )
        source_relatives = {name.removeprefix(prefix) for name in entries}
        target_root = CC_ROM_TARGET / "help"
        target_relatives = {
            path.relative_to(target_root).as_posix()
            for path in target_root.rglob("*") if path.is_file()
        }
        expected_target = source_relatives | {"lc_money.txt"}
        authoring_relatives = {
            path.relative_to(CC_HELP_AUTHORING).as_posix()
            for path in CC_HELP_AUTHORING.rglob("*") if path.is_file()
        }
        for relative in sorted(expected_target - target_relatives):
            audit.error(f"Missing ComputerCraft help file: {relative}")
        for relative in sorted(target_relatives - expected_target):
            audit.error(f"Unexpected ComputerCraft help file: {relative}")
        for relative in sorted(expected_target - authoring_relatives):
            audit.error(f"Missing UTF-8 ComputerCraft help authoring file: {relative}")
        for relative in sorted(authoring_relatives - expected_target):
            audit.error(f"Unexpected UTF-8 ComputerCraft help authoring file: {relative}")
        for source_name in entries:
            relative = source_name.removeprefix(prefix)
            target = target_root / pathlib.PurePosixPath(relative)
            authoring = CC_HELP_AUTHORING / pathlib.PurePosixPath(relative)
            if not target.exists() or not authoring.exists():
                continue
            source_text = archive.read(source_name).decode("utf-8")
            target_text = read_cp1251(target, audit)
            authoring_text = read_utf8(authoring, audit)
            if (
                target_text is not None
                and authoring_text is not None
                and target_text != authoring_text.translate(CC_HELP_RUNTIME_TRANSLATION)
            ):
                audit.error(f"Stale Windows-1251 help output: {relative}")
            if (
                authoring_text is not None
                and len(source_text.splitlines()) != len(authoring_text.splitlines())
            ):
                audit.error(f"Help line structure changed: {relative}")
            audit.count("cc_native_help")

    lc_target = CC_ROM_TARGET / "help/lc_money.txt"
    lc_jar = one_jar("lightmanscurrency-1.20.1-2.3.0.5.jar")
    lc_source = CC_ROM_SOURCE_PREFIX + "help/lc_money.txt"
    lc_authoring = CC_HELP_AUTHORING / "lc_money.txt"
    if lc_target.exists() and lc_authoring.exists():
        with zipfile.ZipFile(lc_jar) as archive:
            source_text = archive.read(lc_source).decode("utf-8")
        target_text = read_cp1251(lc_target, audit)
        authoring_text = read_utf8(lc_authoring, audit)
        if (
            target_text is not None
            and authoring_text is not None
            and target_text != authoring_text.translate(CC_HELP_RUNTIME_TRANSLATION)
        ):
            audit.error("Stale Windows-1251 help output: lc_money.txt")
        if (
            authoring_text is not None
            and len(source_text.splitlines()) != len(authoring_text.splitlines())
        ):
            audit.error("Help line structure changed: lc_money.txt")
        audit.count("cc_addon_help")


def validate_cc_runtime(audit: Audit) -> None:
    if not CC_TERM_FONT.is_file():
        audit.error(f"Missing ComputerCraft terminal font: {CC_TERM_FONT.relative_to(ROOT)}")
    else:
        actual_hash = hashlib.sha256(CC_TERM_FONT.read_bytes()).hexdigest()
        if actual_hash != CC_TERM_FONT_SHA256:
            audit.error(
                f"Unexpected ComputerCraft terminal font SHA-256: {actual_hash}"
            )
        audit.count("cc_terminal_fonts")

    for path in sorted((CC_ROM_TARGET / "help").rglob("*")):
        if not path.is_file():
            continue
        reserved = sorted({
            byte for byte in path.read_bytes() if byte in CC_UNSAFE_GLYPH_BYTES
        })
        if reserved:
            rendered = ", ".join(f"0x{byte:02X}" for byte in reserved)
            audit.error(
                f"ComputerCraft help uses reserved semigraphics bytes "
                f"({rendered}): {path.relative_to(ROOT)}"
            )

    lua_files = sorted(CC_ROM_TARGET.rglob("*.lua"))
    if len(lua_files) != 84:
        audit.error(f"Expected 84 ComputerCraft Lua overlays, found {len(lua_files)}")
    high_byte_escapes = 0
    for path in lua_files:
        text = read_utf8(path, audit)
        if text is None:
            continue
        if CYRILLIC.search(text):
            audit.error(
                f"Raw Cyrillic remains in ComputerCraft Lua runtime: "
                f"{path.relative_to(ROOT)}"
            )
        for match in CC_DECIMAL_ESCAPE.finditer(text):
            value = int(match.group(1))
            if value > 255:
                audit.error(
                    f"ComputerCraft Lua byte escape exceeds 255 at "
                    f"{path.relative_to(ROOT)}: {match.group()}"
                )
            elif value in CC_UNSAFE_GLYPH_BYTES:
                audit.error(
                    f"ComputerCraft Lua uses reserved semigraphics byte "
                    f"0x{value:02X}: {path.relative_to(ROOT)}"
                )
            elif value >= 128:
                high_byte_escapes += 1
    if high_byte_escapes < 1000:
        audit.error(
            f"Too few Windows-1251 Lua byte escapes: {high_byte_escapes}"
        )
    audit.stats["cc_lua_overlays"] = len(lua_files)
    audit.stats["cc_lua_high_byte_escapes"] = high_byte_escapes


def validate_routing(audit: Audit) -> None:
    wrong_resource_data = [
        path for path in (RESOURCE_PACK / "data").rglob("*")
        if path.is_file()
    ] if (RESOURCE_PACK / "data").exists() else []
    wrong_datapack_assets = [
        path for path in (DATA_PACK / "assets").rglob("*")
        if path.is_file()
    ] if (DATA_PACK / "assets").exists() else []
    for path in wrong_resource_data:
        audit.error(f"SERVER_DATA file is in resource pack: {path.relative_to(ROOT)}")
    for path in wrong_datapack_assets:
        audit.error(f"CLIENT_RESOURCES file is in data pack: {path.relative_to(ROOT)}")
    audit.stats["routing_errors"] = len(wrong_resource_data) + len(wrong_datapack_assets)


def iter_archive_lang(
    archive: zipfile.ZipFile,
    archive_label: str,
    audit: Audit,
    depth: int = 0,
) -> Iterator[tuple[str, str, dict[str, str], str]]:
    """Yield language dictionaries from a JAR and its bundled JarJar files."""
    for name in sorted(archive.namelist()):
        match = LANG_PATH.match(name)
        if match:
            label = f"{archive_label}!{name}"
            try:
                parsed = json.loads(archive.read(name).decode("utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                audit.count("archive_lang_parse_errors")
                audit.warning(f"Invalid upstream language JSON {label}: {exc}")
                continue
            if not isinstance(parsed, dict):
                audit.error(f"Upstream language file is not an object: {label}")
                continue
            values = {str(key): str(value) for key, value in parsed.items()}
            yield match.group(1).lower(), match.group(2).lower(), values, label
        elif depth < 2 and name.lower().endswith(".jar"):
            try:
                nested_bytes = archive.read(name)
                with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
                    yield from iter_archive_lang(
                        nested,
                        f"{archive_label}!{name}",
                        audit,
                        depth + 1,
                    )
            except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                audit.warning(f"Cannot inspect nested JAR {archive_label}!{name}: {exc}")


def lang_format_signature(
    value: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], int]:
    """Return a signature which permits safe reordering of indexed arguments."""
    implicit: list[str] = []
    indexed: list[str] = []
    literal_percents = 0
    for match in LANG_PRINTF_TOKEN.finditer(value):
        token = match.group()
        if token == "%%":
            literal_percents += 1
        elif re.match(r"%\d+\$", token):
            indexed.append(token)
        else:
            # Unindexed arguments are positional by occurrence, so their order
            # must remain unchanged.
            implicit.append(token)
    braces = sorted(match.group() for match in BRACE_TOKEN.finditer(value))
    return tuple(implicit), tuple(sorted(indexed)), tuple(braces), literal_percents


def validate_effective_lang_placeholders(audit: Audit) -> None:
    english: dict[str, dict[str, str]] = {}
    russian: dict[str, dict[str, str]] = {}
    for jar in sorted((ROOT / "mods").glob("*.jar")):
        try:
            with zipfile.ZipFile(jar) as archive:
                sources = iter_archive_lang(archive, jar.name, audit)
                for namespace, locale, values, _ in sources:
                    destination = english if locale == "en_us" else russian
                    destination.setdefault(namespace, {}).update(values)
        except (OSError, zipfile.BadZipFile) as exc:
            audit.error(f"Cannot inspect mod JAR {jar.name}: {exc}")

    # Paxi is loaded after mod resources, so its values are the effective ones.
    assets = RESOURCE_PACK / "assets"
    if assets.exists():
        for path in sorted(assets.glob("*/lang/ru_ru.json")):
            parsed = load_json(path, audit)
            if not isinstance(parsed, dict):
                continue
            namespace = path.parts[-3].lower()
            russian.setdefault(namespace, {}).update(
                {str(key): str(value) for key, value in parsed.items()}
            )

    mismatches = 0
    compared = 0
    for namespace, en_values in english.items():
        ru_values = russian.get(namespace, {})
        for key, en_value in en_values.items():
            if key not in ru_values:
                continue
            compared += 1
            en_signature = lang_format_signature(en_value)
            ru_signature = lang_format_signature(ru_values[key])
            if en_signature != ru_signature:
                mismatches += 1
                audit.error(
                    f"Language placeholder mismatch {namespace}:{key}: "
                    f"{en_signature!r} != {ru_signature!r}"
                )
    audit.stats["effective_lang_values_checked"] = compared
    audit.stats["effective_lang_placeholder_mismatches"] = mismatches
    audit.stats["effective_lang_namespaces"] = len(english)


def validate_known_straggler_regressions(audit: Audit) -> None:
    """Keep independently found non-lang English leftovers from returning."""
    checked = 0
    for path, required_fragments in KNOWN_STRAGGLER_GUARDS.items():
        text = read_utf8(path, audit)
        if text is None:
            continue
        for fragment in required_fragments:
            checked += 1
            if fragment not in text:
                audit.error(
                    f"Expected Russian residual fix is missing in "
                    f"{path.relative_to(ROOT)}: {fragment!r}"
                )

    xaero_profiles = sorted((ROOT / "config/xaero").glob("*/profiles/default.cfg"))
    xaero_profiles += sorted(
        (ROOT / "config/xaero").glob("*/server_profiles/default.cfg")
    )
    if len(xaero_profiles) != 6:
        audit.error(
            f"Expected 6 Xaero default profile files, found {len(xaero_profiles)}"
        )
    for path in xaero_profiles:
        text = read_utf8(path, audit)
        if text is None:
            continue
        checked += 1
        if not re.search(r"(?m)^profile_name\s*=\s*По умолчанию\s*$", text):
            audit.error(
                f"Xaero profile display name is not Russian: {path.relative_to(ROOT)}"
            )
    audit.stats["known_straggler_guards"] = checked


def main() -> int:
    audit = Audit()
    try:
        validate_all_json(audit)
        validate_pneumaticcraft(audit)
        validate_non_lang_baseline(audit)
        validate_cc_help(audit)
        validate_cc_runtime(audit)
        validate_routing(audit)
        validate_effective_lang_placeholders(audit)
        validate_known_straggler_regressions(audit)
    except Exception as exc:  # Keep one readable failure instead of a traceback wall.
        audit.error(f"Validator failed: {type(exc).__name__}: {exc}")

    print("Russian overlay validation")
    for name in sorted(audit.stats):
        print(f"  {name}: {audit.stats[name]}")
    if audit.warnings:
        print(f"Warnings: {len(audit.warnings)}")
        for message in audit.warnings:
            print(f"  WARN: {message}")
    if audit.errors:
        print(f"Errors: {len(audit.errors)}")
        for message in audit.errors[:100]:
            print(f"  ERROR: {message}")
        if len(audit.errors) > 100:
            print(f"  ... and {len(audit.errors) - 100} more")
        return 1
    print("Errors: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
