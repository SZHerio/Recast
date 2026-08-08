"""Build the 8-bit Russian CC:Tweaked runtime from UTF-8 authoring text.

CC:Tweaked terminals render one byte per glyph.  The bundled font atlas uses
Windows-1251, so Russian Lua literals are emitted as decimal byte escapes and
help pages are emitted as raw Windows-1251 bytes.  Human-editable help remains
UTF-8 under authoring/computercraft/help.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
ROM = (
    ROOT
    / "config/paxi/datapacks/IndustrialFrontier-Data"
    / "data/computercraft/lua/rom"
)
RUNTIME_HELP = ROM / "help"
AUTHORING_HELP = ROOT / "authoring/computercraft/help"
FONT = (
    ROOT
    / "config/paxi/resourcepacks/IndustrialFrontier-Core"
    / "assets/computercraft/textures/gui/term_font.png"
)

EXPECTED_LUA_FILES = 84
EXPECTED_HELP_FILES = 100
EXPECTED_FONT_SHA256 = (
    "db4c4a8ab49265f6e8e456f495800ea148b133b18a3242aabca30b98ab7f784f"
)
LONG_OPEN = re.compile(r"\[(=*)\[")
HIGH_DECIMAL_ESCAPE = re.compile(r"\\(\d{3})")
UNSAFE_GLYPH_BYTES = frozenset(range(0x80, 0xA0)) | {
    # These Windows-1251 letters are not replaced by CCCyrillic 1.0.0 and
    # still contain the original Latin-1 fraction/currency glyphs.
    0xA3,
    0xA5,
    0xBC,
    0xBD,
    0xBE,
}
TERMINAL_FALLBACKS = {
    # CC:Tweaked keeps semigraphics in 0x80-0x9F.  In particular, the
    # Windows-1251 em-dash byte 0x97 is a block glyph in this atlas.
    "—": "-",
}


def relative(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_utf8(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"UTF-8 BOM is not allowed: {relative(path)}")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Invalid UTF-8: {relative(path)}: {exc}") from exc


def can_encode_cp1251(character: str) -> bool:
    try:
        character.encode("cp1251")
    except UnicodeEncodeError:
        return False
    return True


def cp1251_escape(character: str, path: pathlib.Path, line: int) -> str:
    if character in TERMINAL_FALLBACKS:
        return TERMINAL_FALLBACKS[character]
    try:
        encoded = character.encode("cp1251")
    except UnicodeEncodeError as exc:
        raise ValueError(
            f"Character {character!r} is not available in Windows-1251 at "
            f"{relative(path)}:{line}"
        ) from exc
    if len(encoded) != 1:
        raise ValueError(
            f"Character {character!r} did not encode to one terminal byte at "
            f"{relative(path)}:{line}"
        )
    if encoded[0] in UNSAFE_GLYPH_BYTES:
        raise ValueError(
            f"Character {character!r} maps to reserved ComputerCraft glyph "
            f"0x{encoded[0]:02X} at {relative(path)}:{line}"
        )
    return f"\\{encoded[0]:03d}"


def encode_help_text(text: str, path: pathlib.Path) -> bytes:
    output = bytearray()
    line = 1
    for character in text:
        fallback = TERMINAL_FALLBACKS.get(character)
        if fallback is not None:
            output.extend(fallback.encode("ascii"))
        else:
            try:
                encoded = character.encode("cp1251")
            except UnicodeEncodeError as exc:
                raise ValueError(
                    f"Help character {character!r} is unavailable in "
                    f"Windows-1251 at {relative(path)}:{line}"
                ) from exc
            if any(byte in UNSAFE_GLYPH_BYTES for byte in encoded):
                raise ValueError(
                    f"Help character {character!r} maps to a reserved "
                    f"ComputerCraft glyph at {relative(path)}:{line}"
                )
            output.extend(encoded)
        line += character == "\n"
    return bytes(output)


def long_delimiter(text: str, offset: int) -> tuple[str, int] | None:
    match = LONG_OPEN.match(text, offset)
    if not match:
        return None
    equals = match.group(1)
    return "]" + equals + "]", match.end()


def ensure_ascii(segment: str, path: pathlib.Path, line: int, context: str) -> None:
    for character in segment:
        if ord(character) > 127:
            raise ValueError(
                f"Non-ASCII {character!r} outside a quoted Lua literal "
                f"({context}) at {relative(path)}:{line}"
            )
        line += character == "\n"


def encode_lua(text: str, path: pathlib.Path) -> tuple[str, int]:
    """Encode non-ASCII characters in short quoted Lua strings only."""
    output: list[str] = []
    index = 0
    line = 1
    encoded_characters = 0

    while index < len(text):
        character = text[index]

        if text.startswith("--", index):
            opening = long_delimiter(text, index + 2)
            if opening:
                closing, content_start = opening
                content_end = text.find(closing, content_start)
                if content_end < 0:
                    raise ValueError(
                        f"Unterminated long Lua comment at {relative(path)}:{line}"
                    )
                end = content_end + len(closing)
            else:
                newline = text.find("\n", index)
                end = len(text) if newline < 0 else newline
            segment = text[index:end]
            # Documentation comments are copied byte-for-byte from upstream.
            # Their occasional typographic Unicode is ignored by Lua and does
            # not reach the terminal, so it does not need terminal encoding.
            output.append(segment)
            line += segment.count("\n")
            index = end
            continue

        opening = long_delimiter(text, index)
        if opening:
            closing, content_start = opening
            content_end = text.find(closing, content_start)
            if content_end < 0:
                raise ValueError(
                    f"Unterminated long Lua string at {relative(path)}:{line}"
                )
            end = content_end + len(closing)
            segment = text[index:end]
            ensure_ascii(segment, path, line, "long string")
            output.append(segment)
            line += segment.count("\n")
            index = end
            continue

        if character in {'"', "'"}:
            quote = character
            output.append(character)
            index += 1
            while index < len(text):
                character = text[index]
                if character == quote:
                    output.append(character)
                    index += 1
                    break
                if character == "\\":
                    output.append(character)
                    index += 1
                    if index >= len(text):
                        raise ValueError(
                            f"Dangling Lua escape at {relative(path)}:{line}"
                        )
                    escaped = text[index]
                    if ord(escaped) > 127:
                        raise ValueError(
                            f"Non-ASCII escaped character {escaped!r} at "
                            f"{relative(path)}:{line}"
                        )
                    output.append(escaped)
                    line += escaped == "\n"
                    index += 1
                    continue
                if character in "\r\n":
                    raise ValueError(
                        f"Unescaped newline in Lua string at {relative(path)}:{line}"
                    )
                if ord(character) > 127:
                    output.append(cp1251_escape(character, path, line))
                    encoded_characters += 1
                else:
                    output.append(character)
                index += 1
            else:
                raise ValueError(
                    f"Unterminated quoted Lua string at {relative(path)}:{line}"
                )
            continue

        if ord(character) > 127:
            raise ValueError(
                f"Non-ASCII {character!r} outside a Lua string at "
                f"{relative(path)}:{line}"
            )
        output.append(character)
        line += character == "\n"
        index += 1

    return "".join(output), encoded_characters


def validate_font() -> None:
    if not FONT.is_file():
        raise ValueError(f"Missing ComputerCraft font atlas: {relative(FONT)}")
    actual = hashlib.sha256(FONT.read_bytes()).hexdigest()
    if actual != EXPECTED_FONT_SHA256:
        raise ValueError(
            f"Unexpected ComputerCraft font SHA-256: {actual}; "
            f"expected {EXPECTED_FONT_SHA256}"
        )


def authoring_help_files() -> list[pathlib.Path]:
    files = sorted(path for path in AUTHORING_HELP.rglob("*") if path.is_file())
    if len(files) != EXPECTED_HELP_FILES:
        raise ValueError(
            f"Expected {EXPECTED_HELP_FILES} UTF-8 help files, found {len(files)}"
        )
    return files


def build_help() -> tuple[int, int]:
    files = authoring_help_files()
    characters = 0
    prepared: list[tuple[pathlib.Path, str]] = []
    problems: list[str] = []
    for source in files:
        text = read_utf8(source)
        prepared.append((source, text))
        unsupported = sorted(
            {
                character
                for character in text
                if not can_encode_cp1251(character)
            }
        )
        if unsupported:
            rendered = ", ".join(
                f"{character!r} (U+{ord(character):04X})"
                for character in unsupported
            )
            problems.append(
                f"{relative(source)}: {rendered}"
            )
    if problems:
        raise ValueError(
            "Help contains characters unavailable in Windows-1251:\n  "
            + "\n  ".join(problems)
        )
    for source, text in prepared:
        encoded = encode_help_text(text, source)
        destination = RUNTIME_HELP / source.relative_to(AUTHORING_HELP)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encoded)
        characters += sum(ord(character) > 127 for character in text)
    return len(files), characters


def build_lua() -> tuple[int, int, int]:
    files = sorted(ROM.rglob("*.lua"))
    if len(files) != EXPECTED_LUA_FILES:
        raise ValueError(f"Expected {EXPECTED_LUA_FILES} Lua overlays, found {len(files)}")
    changed = 0
    characters = 0
    for path in files:
        text = read_utf8(path)
        encoded, count = encode_lua(text, path)
        if encoded != text:
            path.write_text(encoded, encoding="utf-8", newline="")
            changed += 1
        characters += count
    return len(files), changed, characters


def check_runtime() -> tuple[int, int, int]:
    validate_font()
    help_files = authoring_help_files()
    runtime_help = sorted(path for path in RUNTIME_HELP.rglob("*") if path.is_file())
    if {path.relative_to(AUTHORING_HELP) for path in help_files} != {
        path.relative_to(RUNTIME_HELP) for path in runtime_help
    }:
        raise ValueError("Authoring and runtime ComputerCraft help file sets differ")
    for source in help_files:
        text = read_utf8(source)
        expected = encode_help_text(text, source)
        target = RUNTIME_HELP / source.relative_to(AUTHORING_HELP)
        if target.read_bytes() != expected:
            raise ValueError(f"Stale Windows-1251 help output: {relative(target)}")

    lua_files = sorted(ROM.rglob("*.lua"))
    if len(lua_files) != EXPECTED_LUA_FILES:
        raise ValueError(f"Expected {EXPECTED_LUA_FILES} Lua overlays, found {len(lua_files)}")
    high_escapes = 0
    for path in lua_files:
        text = read_utf8(path)
        encoded, remaining = encode_lua(text, path)
        if encoded != text or remaining:
            raise ValueError(
                f"Lua runtime still contains unencoded terminal text: {relative(path)}"
            )
        for match in HIGH_DECIMAL_ESCAPE.finditer(text):
            value = int(match.group(1))
            if value > 255:
                raise ValueError(
                    f"Lua byte escape exceeds 255 at {relative(path)}: {match.group()}"
                )
            if value in UNSAFE_GLYPH_BYTES:
                raise ValueError(
                    f"Lua uses reserved ComputerCraft glyph byte 0x{value:02X} "
                    f"at {relative(path)}"
                )
            high_escapes += value >= 128
    if high_escapes == 0:
        raise ValueError("No Windows-1251 byte escapes found in Russian Lua overlays")
    return len(lua_files), len(runtime_help), high_escapes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="validate generated runtime without writing"
    )
    args = parser.parse_args()
    try:
        if args.check:
            lua_count, help_count, escapes = check_runtime()
            print(
                f"Validated {lua_count} terminal-safe Lua overlays, {help_count} "
                f"Windows-1251 help files and {escapes} high-byte Lua escapes."
            )
            return 0
        validate_font()
        lua_count, changed_lua, lua_characters = build_lua()
        help_count, help_characters = build_help()
        print(
            f"Built CC:Tweaked Windows-1251 runtime: {lua_count} Lua overlays "
            f"({changed_lua} rewritten, {lua_characters} characters escaped), "
            f"{help_count} help files ({help_characters} non-ASCII characters)."
        )
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
