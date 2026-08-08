"""Rebuild and validate the complete Russian CC:Tweaked ROM overlay."""

from __future__ import annotations

import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def run(*command: str) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    python = sys.executable
    run("node", str(TOOLS / "build_cc_rom_ru.js"))
    run(python, str(TOOLS / "build_cc_extra_programs_ru.py"))
    run(python, str(TOOLS / "build_cc_api_ru.py"))
    run(python, str(TOOLS / "build_cc_syntax_ru.py"))
    run(python, str(TOOLS / "encode_cc_terminal_ru.py"))
    run("node", str(TOOLS / "build_cc_rom_ru.js"), "--audit")
    run(python, str(TOOLS / "encode_cc_terminal_ru.py"), "--check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
