#!/usr/bin/env python3
"""Deterministically compile Quest Source v2 into an isolated staging tree.

Default output is ``build/questbook_v2``. Player-facing text is localized by
default so FTB Quests never tries to sync the full Russian guidebook inside its
single 1 MiB login packet. The script deliberately does not write runtime files.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
from typing import Any

from validate_questbook_v2 import (
    DEFAULT_SCHEMA,
    DEFAULT_SOURCE,
    Issue,
    ROOT,
    VERIFIED_ADAPTERS,
    load_project,
    validate_project,
    validate_staging,
)


COMPILER_VERSION = 2
DEFAULT_OUTPUT = pathlib.Path("build/questbook_v2")
QUEST_SYNC_SNBT_BUDGET = 850_000
OBSERVATION_ORDINAL = {
    "BLOCK": 0,
    "BLOCK_TAG": 1,
    "BLOCK_STATE": 2,
    "BLOCK_ENTITY": 3,
    "BLOCK_ENTITY_TYPE": 4,
    "ENTITY_TYPE": 5,
    "ENTITY_TYPE_TAG": 6,
}


def _q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _num(value: int | float) -> str:
    numeric = float(value)
    if numeric.is_integer():
        return f"{int(numeric)}d"
    return f"{numeric:g}d"


def _key(alias: str, suffix: str) -> str:
    stem = alias[3:] if alias.startswith("if.") else alias
    return f"industrial_frontier.{stem}.{suffix}"


def _text(value: str, key: str, mode: str, localized: dict[str, str]) -> str:
    localized[key] = value
    return f"{{{key}}}" if mode == "staging-lang" else value


def _snbt_value(value: Any, indent: int = 0) -> list[str]:
    """Render the JSON-shaped subset used for item/fluid NBT."""
    prefix = "\t" * indent
    if isinstance(value, dict):
        lines = [prefix + "{"]
        for key in sorted(value):
            rendered_key = key if re.fullmatch(r"[A-Za-z0-9_.+-]+", key) else _q(key)
            rendered = _snbt_value(value[key], indent + 1)
            if len(rendered) == 1:
                lines.append("\t" * (indent + 1) + f"{rendered_key}: {rendered[0].lstrip()}")
            else:
                lines.append("\t" * (indent + 1) + f"{rendered_key}: {rendered[0].lstrip()}")
                lines.extend(rendered[1:])
        lines.append(prefix + "}")
        return lines
    if isinstance(value, list):
        return [prefix + "[" + ", ".join(_snbt_value(item, 0)[0].strip() for item in value) + "]"]
    if isinstance(value, bool):
        return [prefix + ("true" if value else "false")]
    if value is None:
        return [prefix + '""']
    if isinstance(value, (int, float)):
        return [prefix + str(value)]
    return [prefix + _q(str(value))]


def _append_compound(lines: list[str], indent: int, name: str, value: dict[str, Any]) -> None:
    rendered = _snbt_value(value, indent)
    lines.append("\t" * indent + f"{name}: " + rendered[0].lstrip())
    lines.extend(rendered[1:])


def _item_stack_lines(payload: dict[str, Any], indent: int) -> list[str]:
    lines = ["\t" * indent + "item: {", "\t" * (indent + 1) + "Count: 1", "\t" * (indent + 1) + f"id: {_q(payload['id'])}"]
    if payload.get("nbt"):
        _append_compound(lines, indent + 1, "tag", payload["nbt"])
    lines.append("\t" * indent + "}")
    return lines


def _render_proof(proof: dict[str, Any], mode: str, localized: dict[str, str]) -> list[str]:
    if proof.get("status") != "verified":
        raise ValueError(f"Refusing to compile blocked proof {proof.get('alias')}")
    proof_type = proof["type"]
    runtime_type = VERIFIED_ADAPTERS[proof_type]["runtime_type"]
    indent = 4
    lines = ["\t" * indent + "{"]
    body = indent + 1
    lines.append("\t" * body + f"id: {_q(proof['engine_id'])}")

    if proof_type == "item":
        if "item_tag" in proof:
            payload = proof["item_tag"]
            count = payload.get("count", 1)
            if count > 1:
                lines.append("\t" * body + f"count: {count}L")
            lines.extend([
                "\t" * body + "item: {",
                "\t" * (body + 1) + "Count: 1",
                "\t" * (body + 1) + 'id: "ftbfiltersystem:smart_filter"',
                "\t" * (body + 1) + "tag: {",
                "\t" * (body + 2) + _q("ftbfiltersystem:filter") + ": " + _q(f"ftbfiltersystem:item_tag({payload['id']})"),
                "\t" * (body + 1) + "}",
                "\t" * body + "}",
            ])
        else:
            payload = proof["item"]
            count = payload.get("count", 1)
            if count > 1:
                lines.append("\t" * body + f"count: {count}L")
            lines.extend(_item_stack_lines(payload, body))
            lines.append("\t" * body + "consume_items: false")
            if "only_from_crafting" in payload:
                lines.append("\t" * body + f"only_from_crafting: {str(payload['only_from_crafting']).lower()}")
            if "match_nbt" in payload:
                lines.append("\t" * body + f"match_nbt: {str(payload['match_nbt']).lower()}")
            if payload.get("weak_nbt_match"):
                lines.append("\t" * body + "weak_nbt_match: true")
    elif proof_type == "dimension":
        lines.append("\t" * body + f"dimension: {_q(proof['dimension'])}")
    elif proof_type == "fluid":
        payload = proof["fluid"]
        lines.append("\t" * body + f"fluid: {_q(payload['id'])}")
        lines.append("\t" * body + f"amount: {payload['amount']}L")
        if payload.get("nbt"):
            _append_compound(lines, body, "nbt", payload["nbt"])
    elif proof_type == "energy":
        payload = proof["energy"]
        lines.append("\t" * body + f"value: {payload['amount']}L")
        if payload.get("max_input"):
            lines.append("\t" * body + f"max_input: {payload['max_input']}L")
    elif proof_type == "structure":
        lines.append("\t" * body + f"structure: {_q(proof['structure'])}")
    elif proof_type == "location":
        payload = proof["location"]
        lines.append("\t" * body + f"dimension: {_q(payload['dimension'])}")
        lines.append("\t" * body + f"ignore_dimension: {str(payload.get('ignore_dimension', False)).lower()}")
        lines.append("\t" * body + "position: [I; " + ", ".join(str(item) for item in payload["position"]) + "]")
        lines.append("\t" * body + "size: [I; " + ", ".join(str(item) for item in payload["size"]) + "]")
    elif proof_type == "biome":
        lines.append("\t" * body + f"biome: {_q(proof['biome'])}")
    elif proof_type == "kill":
        payload = proof["kill"]
        lines.append("\t" * body + f"entity: {_q(payload['entity'])}")
        lines.append("\t" * body + f"value: {payload['count']}L")
    elif proof_type == "stage":
        lines.append("\t" * body + f"stage: {_q(proof['stage'])}")
    elif proof_type == "observation":
        payload = proof["observation"]
        lines.append("\t" * body + f"timer: {payload['timer']}L")
        lines.append("\t" * body + f"observe_type: {OBSERVATION_ORDINAL[payload['observe_type']]}")
        lines.append("\t" * body + f"to_observe: {_q(payload['target'])}")
    elif proof_type in {"place", "use"}:
        payload = proof[proof_type]
        is_tag = "block_tag" in payload
        lines.append("\t" * body + f"block_type: {1 if is_tag else 0}")
        lines.append("\t" * body + f"block: {_q(payload['block_tag'] if is_tag else payload['block'])}")
        lines.append("\t" * body + f"value: {payload['count']}L")
        if proof_type == "place":
            lines.append("\t" * body + f"replace: {str(payload.get('require_replace', False)).lower()}")
            # PlaceTask#readData constructs a ResourceLocation unconditionally;
            # its installed-class default is minecraft:air, so the field may
            # not be omitted even when replacement checking is disabled.
            lines.append("\t" * body + f"replaced: {_q(payload.get('replaced_block', 'minecraft:air'))}")
        else:
            lines.append("\t" * body + f"checkItem: {str(payload['check_item']).lower()}")
            lines.append("\t" * body + f"isItemInteraction: {str(payload['item_interaction']).lower()}")
            if payload.get("item"):
                lines.extend(_item_stack_lines(payload["item"], body))

    objective_key = _key(proof["alias"], "objective")
    objective = _text(proof["text_ru"]["objective"], objective_key, mode, localized)
    lines.append("\t" * body + f"title: {_q(objective)}")
    lines.append("\t" * body + f"type: {_q(runtime_type)}")
    lines.append("\t" * indent + "}")
    return lines


def _quest_description(quest: dict[str, Any]) -> list[tuple[str, str]]:
    text = quest["text_ru"]
    entries: list[tuple[str, str]] = [("purpose", text["purpose_ru"])]
    entries.extend((f"step.{index}", value) for index, value in enumerate(text["steps_ru"], 1))
    entries.append(("success", text["success_ru"]))
    entries.append(("task", text["task_text_ru"]))
    entries.extend((f"diagnostic.{index}", value) for index, value in enumerate(text["diagnostics_ru"], 1))
    for pindex, proof in enumerate(quest["proofs"], 1):
        help_text = proof.get("text_ru", {}).get("help")
        if help_text:
            entries.append((f"proof_help.{pindex}", help_text))
    entries.append(("next", text["next_ru"]))
    if text.get("optional_note_ru"):
        entries.append(("optional_note", text["optional_note_ru"]))
    return entries


def _render_chapter(document: dict[str, Any], mode: str, localized: dict[str, str]) -> str:
    chapter = document["chapter"]
    lines = [
        "{",
        "\tdefault_hide_dependency_lines: false",
        "\tdefault_quest_shape: \"square\"",
    ]
    if chapter.get("hide_until_reached", True):
        lines.append("\thide_quest_until_deps_visible: true")
    lines.extend([
        f"\tfilename: {_q(chapter['filename'])}",
        f"\tgroup: {_q(chapter['group']['engine_id'])}",
        f"\ticon: {_q(chapter['icon'])}",
        f"\tid: {_q(chapter['engine_id'])}",
        f"\torder_index: {chapter['order']}",
        "\tquest_links: [ ]",
        "\tquests: [",
    ])

    for quest in document["quests"]:
        base = _key(quest["alias"], "")[:-1]
        lines.append("\t\t{")
        deps = [edge["quest"] for edge in quest["dependency"]["edges"]]
        quest_ids = {item["alias"]: item["engine_id"] for doc in [document] for item in doc["quests"]}
        # Cross-chapter IDs are resolved by a temporary field injected by compile().
        quest_ids.update(document.get("_global_quest_ids", {}))
        if deps:
            if any(document.get("_quest_epochs", {}).get(dep) != quest["epoch"] for dep in deps):
                lines.append("\t\t\thide_until_deps_complete: true")
            if len(deps) == 1:
                lines.append(f"\t\t\tdependencies: [{_q(quest_ids[deps[0]])}]")
            else:
                lines.append("\t\t\tdependencies: [")
                lines.extend(f"\t\t\t\t{_q(quest_ids[dep])}" for dep in deps)
                lines.append("\t\t\t]")
            if quest["dependency"]["mode"] == "ANY_OF":
                lines.append('\t\t\tdependency_requirement: "one_completed"')

        lines.append("\t\t\tdescription: [")
        for suffix, value in _quest_description(quest):
            rendered = _text(value, f"{base}.{suffix}", mode, localized)
            lines.append(f"\t\t\t\t{_q(rendered)}")
        lines.append("\t\t\t]")
        lines.append(f"\t\t\ticon: {_q(quest['icon'])}")
        lines.append(f"\t\t\tid: {_q(quest['engine_id'])}")
        if quest["requirement"] == "optional":
            lines.append("\t\t\toptional: true")
        layout = quest["layout"]
        if layout.get("shape"):
            lines.append(f"\t\t\tshape: {_q(layout['shape'])}")
        if layout.get("size") is not None:
            lines.append(f"\t\t\tsize: {_num(layout['size'])}")
        lead = _text(quest["text_ru"]["lead_ru"], f"{base}.lead", mode, localized)
        lines.append(f"\t\t\tsubtitle: {_q(lead)}")
        tags = list(quest.get("tags", []))
        if tags:
            lines.append("\t\t\ttags: [" + ", ".join(_q(tag) for tag in tags) + "]")
        lines.append("\t\t\ttasks: [")
        for index, proof in enumerate(quest["proofs"]):
            proof_lines = _render_proof(proof, mode, localized)
            lines.extend(proof_lines)
        lines.append("\t\t\t]")
        title = _text(quest["text_ru"]["title_ru"], f"{base}.title", mode, localized)
        lines.append(f"\t\t\ttitle: {_q(title)}")
        lines.append(f"\t\t\tx: {_num(layout['x'])}")
        lines.append(f"\t\t\ty: {_num(layout['y'])}")
        lines.append("\t\t}")

    lines.append("\t]")
    chapter_base = _key(chapter["alias"], "")[:-1]
    subtitle_values = [chapter["text_ru"]["subtitle"], *chapter["text_ru"]["description"]]
    lines.append("\tsubtitle: [")
    for index, value in enumerate(subtitle_values):
        rendered = _text(value, f"{chapter_base}.subtitle.{index + 1}", mode, localized)
        lines.append(f"\t\t{_q(rendered)}")
    lines.append("\t]")
    chapter_title = _text(chapter["text_ru"]["title"], f"{chapter_base}.title", mode, localized)
    lines.append(f"\ttitle: {_q(chapter_title)}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _render_groups(groups: dict[str, dict[str, Any]], mode: str, localized: dict[str, str]) -> str:
    lines = ["{", "\tchapter_groups: ["]
    for alias, group in sorted(groups.items(), key=lambda item: (item[1]["engine_id"], item[0])):
        title = _text(group["title_ru"], _key(alias, "title"), mode, localized)
        lines.extend([
            "\t\t{",
            f"\t\t\tid: {_q(group['engine_id'])}",
            f"\t\t\ttitle: {_q(title)}",
            "\t\t}",
        ])
    lines.extend(["\t]", "}"])
    return "\n".join(lines) + "\n"


def _stable_registry(report: dict[str, Any]) -> dict[str, Any]:
    ids: dict[str, str] = {}
    for alias, group in report["groups"].items():
        ids[alias] = group["engine_id"]
    for alias, chapter in report["chapters"].items():
        ids[alias] = chapter["engine_id"]
    for alias, quest in report["quests"].items():
        ids[alias] = quest["engine_id"]
    for alias, proof in report["proofs"].items():
        ids[alias] = proof["engine_id"]
    return {
        "schema_version": 2,
        "registry": "quest_source_v2_staging",
        "ids": {alias: ids[alias] for alias in sorted(ids)},
    }


def _graph_report(report: dict[str, Any]) -> dict[str, Any]:
    nodes = []
    edges = []
    for alias in report["topological_order"]:
        quest = report["quests"][alias]
        nodes.append({
            "alias": alias,
            "engine_id": quest["engine_id"],
            "chapter": report["chapter_for_quest"][alias],
            "epoch": quest["epoch"],
            "role": quest["role"],
            "requirement": quest["requirement"],
        })
        edge_lookup = {edge["quest"]: edge for edge in quest["dependency"]["edges"]}
        for dep in report["dependencies"][alias]:
            edge = edge_lookup[dep]
            edges.append({
                "from": dep,
                "to": alias,
                "mode_at_target": report["dependency_modes"][alias],
                "reason": edge["reason"],
                "evidence": edge["evidence"],
            })
    return {
        "schema_version": 2,
        "roots": report["roots"],
        "commissioning_by_epoch": report["commissioning_by_epoch"],
        "mandatory_dependencies": report["mandatory_dependencies"],
        "nodes": nodes,
        "edges": edges,
    }


def _translation_handoff(report: dict[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for alias in report["topological_order"]:
        quest = report["quests"][alias]
        entries.append({
            "quest_alias": alias,
            "primary_language": "ru",
            "origin": quest["authorship"]["origin"],
            "editorial_state": quest["editorial_review"]["state"],
            "ru": quest["text_ru"],
            "future_en_us": {"status": "NOT_AUTHORED_SEPARATELY"},
        })
    return {"schema_version": 2, "policy": "RU_PRIMARY_EN_SEPARATELY_AUTHORED", "entries": entries}


def _russian_editorial_corpus(report: dict[str, Any]) -> str:
    """Render every player-facing Russian string in reading order for review."""
    lines = [
        "# Сквозная вычитка русского квестбука",
        "",
        "Этот файл собран автоматически из Quest Source v2. Он нужен для непрерывного чтения; правки вносятся в исходные JSON-файлы.",
        "",
    ]
    chapter_order = sorted(
        report["chapters"],
        key=lambda alias: (
            report["chapters"][alias]["order"],
            report["chapters"][alias]["filename"],
            alias,
        ),
    )
    for chapter_alias in chapter_order:
        chapter = report["chapters"][chapter_alias]
        chapter_text = chapter["text_ru"]
        lines.extend([
            f"## {chapter_text['title']}",
            "",
            f"_{chapter_text['subtitle']}_",
            "",
        ])
        for paragraph in chapter_text["description"]:
            lines.extend([paragraph, ""])

        aliases = [
            alias
            for alias in report["topological_order"]
            if report["chapter_for_quest"][alias] == chapter_alias
        ]
        for alias in aliases:
            quest = report["quests"][alias]
            text_ru = quest["text_ru"]
            lines.extend([
                f"### {text_ru['title_ru']}",
                "",
                f"<!-- {alias} | {quest['epoch']} | {quest['role']} | {quest['requirement']} -->",
                "",
                text_ru["lead_ru"],
                "",
                text_ru["purpose_ru"],
                "",
            ])
            if text_ru["steps_ru"]:
                lines.extend(["Что сделать:", ""])
                lines.extend(f"{index}. {step}" for index, step in enumerate(text_ru["steps_ru"], 1))
                lines.append("")
            lines.extend([f"Результат: {text_ru['success_ru']}", ""])
            if text_ru["diagnostics_ru"]:
                lines.extend(["Если не получилось:", ""])
                lines.extend(f"- {entry}" for entry in text_ru["diagnostics_ru"])
                lines.append("")
            lines.extend([
                f"Дальше: {text_ru['next_ru']}",
                "",
                f"Текст задачи: {text_ru['task_text_ru']}",
                "",
            ])
            if text_ru.get("optional_note_ru"):
                lines.extend([f"Необязательная ветвь: {text_ru['optional_note_ru']}", ""])
            lines.extend(["Задачи проверки:", ""])
            for proof in quest["proofs"]:
                proof_text = proof["text_ru"]
                suffix = f" — {proof_text['help']}" if proof_text.get("help") else ""
                lines.append(f"- {proof_text['objective']}{suffix}")
            lines.extend(["", "---", ""])
    return "\n".join(lines).rstrip() + "\n"


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _source_hashes(project_root: pathlib.Path, source_dir: pathlib.Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(source_dir.rglob("*.json"), key=lambda item: item.as_posix().lower()):
        relative = path.relative_to(project_root).as_posix() if path.is_relative_to(project_root) else str(path)
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _manifest(temp: pathlib.Path, root: pathlib.Path, source_dir: pathlib.Path, text_mode: str, status: str) -> dict[str, Any]:
    files: dict[str, str] = {}
    for path in sorted(temp.rglob("*"), key=lambda item: item.as_posix().lower()):
        if path.is_file() and path.name != "manifest.json":
            files[path.relative_to(temp).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "schema_version": 2,
        "compiler_version": COMPILER_VERSION,
        "status": status,
        "text_mode": text_mode,
        "runtime_written": False,
        "shared_lang_written": False,
        "source_hashes": _source_hashes(root, source_dir),
        "files": files,
    }


def _compound_blocks_by_id(text: str, compound_indent: int, id_indent: int) -> dict[str, str]:
    """Extract renderer-owned compounds without pretending to parse all SNBT."""
    lines = text.splitlines()
    opening = "\t" * compound_indent + "{"
    closing = "\t" * compound_indent + "}"
    id_pattern = re.compile(rf'^\t{{{id_indent}}}id: "([0-9A-F]{{16}})"$', re.M)
    blocks: dict[str, str] = {}
    index = 0
    while index < len(lines):
        if lines[index] != opening:
            index += 1
            continue
        end = index + 1
        while end < len(lines) and lines[end] != closing:
            end += 1
        if end >= len(lines):
            break
        block = "\n".join(lines[index:end + 1])
        match = id_pattern.search(block)
        if match:
            blocks[match.group(1)] = block
        index = end + 1
    return blocks


def _parity_projection(report: dict[str, Any], chapter_dir: pathlib.Path, mode: str) -> tuple[dict[str, Any], list[Issue]]:
    checks: list[dict[str, Any]] = []
    issues: list[Issue] = []
    for chapter_alias, chapter in sorted(report["chapters"].items(), key=lambda item: (item[1]["order"], item[1]["filename"])):
        path = chapter_dir / f"{chapter['filename']}.snbt"
        text = path.read_text(encoding="utf-8")
        quest_blocks = _compound_blocks_by_id(text, 2, 3)
        for alias, quest in report["quests"].items():
            if report["chapter_for_quest"][alias] != chapter_alias:
                continue
            block = quest_blocks.get(quest["engine_id"], "")
            id_present = bool(block)
            dep_ids = [report["quests"][dep]["engine_id"] for dep in report["dependencies"][alias]]
            dependencies_present = all(_q(dep) in block for dep in dep_ids)
            dependency_field_present = "\n\t\t\tdependencies:" in block
            dependency_shape_ok = dependency_field_present == bool(dep_ids)
            any_of_present = 'dependency_requirement: "one_completed"' in block
            dependency_mode_ok = any_of_present == (bool(dep_ids) and report["dependency_modes"][alias] == "ANY_OF")
            tags_present = all(_q(tag) in block for tag in quest.get("tags", []))
            optional_present = "\n\t\t\toptional: true" in block
            optionality_ok = optional_present == (quest["requirement"] == "optional")
            proof_blocks = _compound_blocks_by_id(block, 4, 5)
            proof_checks = []
            for proof in quest["proofs"]:
                runtime_type = VERIFIED_ADAPTERS[proof["type"]]["runtime_type"]
                proof_block = proof_blocks.get(proof["engine_id"], "")
                proof_checks.append({
                    "alias": proof["alias"],
                    "id_present": bool(proof_block),
                    "type_present": f"type: {_q(runtime_type)}" in proof_block,
                })
            ru_present = True
            if mode == "ru-inline":
                source_strings = [value for _, value in _quest_all_ru_strings(quest)]
                ru_present = all(_q(value) in block for value in source_strings)
            ok = (
                id_present
                and dependencies_present
                and dependency_shape_ok
                and dependency_mode_ok
                and tags_present
                and optionality_ok
                and ru_present
                and all(item["id_present"] and item["type_present"] for item in proof_checks)
            )
            check = {
                "quest": alias,
                "id_present": id_present,
                "dependency_ids_present": dependencies_present,
                "dependency_shape_ok": dependency_shape_ok,
                "dependency_mode_ok": dependency_mode_ok,
                "tags_present": tags_present,
                "optionality_ok": optionality_ok,
                "ru_primary_strings_present": ru_present,
                "proofs": proof_checks,
                "ok": ok,
            }
            checks.append(check)
            if not ok:
                issues.append(Issue("ERROR", "QV2-SEMANTIC-PARITY", str(path), f"Compiled projection differs for {alias}."))
    return {"schema_version": 2, "text_mode": mode, "checks": checks, "ok": all(item["ok"] for item in checks)}, issues


def _quest_all_ru_strings(quest: dict[str, Any]) -> list[tuple[str, str]]:
    text = quest["text_ru"]
    values: list[tuple[str, str]] = []
    for key in ("title_ru", "lead_ru", "purpose_ru", "success_ru", "next_ru", "task_text_ru", "optional_note_ru"):
        if text.get(key):
            values.append((key, text[key]))
    values.extend(("steps_ru", value) for value in text.get("steps_ru", []))
    values.extend(("diagnostics_ru", value) for value in text.get("diagnostics_ru", []))
    for proof in quest["proofs"]:
        values.append(("proof.objective", proof["text_ru"]["objective"]))
        if proof["text_ru"].get("help"):
            values.append(("proof.help", proof["text_ru"]["help"]))
    return values


def _safe_output(root: pathlib.Path, output: pathlib.Path) -> pathlib.Path:
    resolved = output.resolve()
    build_root = (root / DEFAULT_OUTPUT).resolve()
    try:
        resolved.relative_to(build_root)
    except ValueError as exc:
        raise ValueError(f"Staging output must stay inside {build_root}; got {resolved}") from exc
    return resolved


def _publish(temp: pathlib.Path, output: pathlib.Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    temp.replace(output)


def _print_issues(issues: list[Issue]) -> None:
    for issue in issues:
        print(f"{issue.level} [{issue.code}] {issue.path}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile Quest Source v2 to isolated staging SNBT.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--text-mode", choices=["ru-inline", "staging-lang"], default="staging-lang", help="Default stores Russian in staging localization so the FTB Quests login packet remains below 1 MiB.")
    parser.add_argument("--reports-only", action="store_true", help="Write reports but no SNBT; allows honest draft/blocked sources.")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    source = pathlib.Path(args.source)
    source = source if source.is_absolute() else root / source
    schema = pathlib.Path(args.schema)
    schema = schema if schema.is_absolute() else root / schema
    output_arg = pathlib.Path(args.out)
    try:
        output = _safe_output(root, output_arg if output_arg.is_absolute() else root / output_arg)
    except ValueError as exc:
        parser.error(str(exc))

    project, issues = load_project(root, source, schema)
    semantic_issues, report = validate_project(project, release=not args.reports_only)
    issues.extend(semantic_issues)
    errors = [issue for issue in issues if issue.level == "ERROR"]
    if errors and not args.reports_only:
        print(f"Compilation refused: {len(errors)} validation error(s).")
        _print_issues(issues)
        print("Minecraft was not launched. Runtime quests and shared lang files were not modified.")
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    temp = pathlib.Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        reports = temp / "reports"
        validation_json = {
            "schema_version": 2,
            "status": "ERROR" if errors else "WARN" if issues else "OK",
            "errors": [dataclasses.asdict(issue) for issue in issues if issue.level == "ERROR"],
            "warnings": [dataclasses.asdict(issue) for issue in issues if issue.level == "WARN"],
            "counts": report.get("counts", {}),
        }
        _write_json(reports / "validation.json", validation_json)
        _write_json(reports / "graph.json", _graph_report(report))
        _write_json(reports / "coverage.json", {
            "schema_version": 2,
            "entries": report["coverage"],
            "gameplay_mod_contracts": report["mod_coverage"],
        })
        _write_json(reports / "migration.json", report["migration"])
        _write_json(reports / "blocked_proofs.json", {"schema_version": 2, "blocked_proofs": report["blocked_proofs"]})
        _write_json(reports / "task_adapter_evidence.json", {"schema_version": 2, "adapters": report["verified_adapters"]})
        _write_json(reports / "translation_handoff.json", _translation_handoff(report))
        (reports / "russian_editorial_corpus.md").write_text(
            _russian_editorial_corpus(report), encoding="utf-8", newline="\n"
        )
        _write_json(temp / "registries" / "stable_ids_v2.json", _stable_registry(report))

        localized: dict[str, str] = {}
        parity_issues: list[Issue] = []
        if not args.reports_only:
            global_ids = {alias: quest["engine_id"] for alias, quest in report["quests"].items()}
            quest_epochs = {alias: quest["epoch"] for alias, quest in report["quests"].items()}
            chapter_dir = temp / "chapters"
            chapter_dir.mkdir(parents=True, exist_ok=True)
            documents = sorted(project.chapters, key=lambda doc: (doc["chapter"]["order"], doc["chapter"]["filename"], doc["chapter"]["alias"]))
            for document in documents:
                document = dict(document)
                document["_global_quest_ids"] = global_ids
                document["_quest_epochs"] = quest_epochs
                path = chapter_dir / f"{document['chapter']['filename']}.snbt"
                path.write_text(_render_chapter(document, args.text_mode, localized), encoding="utf-8", newline="\n")
            (temp / "chapter_groups.snbt").write_text(_render_groups(report["groups"], args.text_mode, localized), encoding="utf-8", newline="\n")
            if args.text_mode == "staging-lang":
                _write_json(temp / "localization" / "ru_ru.json", {key: localized[key] for key in sorted(localized)})

            sync_snbt_bytes = sum(path.stat().st_size for path in chapter_dir.glob("*.snbt")) + (temp / "chapter_groups.snbt").stat().st_size
            _write_json(reports / "network_budget.json", {
                "schema_version": 1,
                "minecraft_custom_payload_limit_bytes": 1_048_576,
                "maximum_staged_snbt_bytes": QUEST_SYNC_SNBT_BUDGET,
                "staged_snbt_bytes": sync_snbt_bytes,
                "status": "PASS" if sync_snbt_bytes <= QUEST_SYNC_SNBT_BUDGET else "FAIL",
            })
            if sync_snbt_bytes > QUEST_SYNC_SNBT_BUDGET:
                raise RuntimeError(
                    f"Quest sync staging is {sync_snbt_bytes} bytes; budget is {QUEST_SYNC_SNBT_BUDGET}. "
                    "Use staging-lang or split/remove non-player-facing payload data."
                )

            parity, compiler_parity_issues = _parity_projection(report, chapter_dir, args.text_mode)
            parity_issues.extend(compiler_parity_issues)
            parity_issues.extend(validate_staging(project, report, temp))
            _write_json(reports / "semantic_parity.json", parity)
            if parity_issues:
                _print_issues(parity_issues)
                raise RuntimeError(f"Generated staging failed semantic parity with {len(parity_issues)} issue(s).")
        else:
            _write_json(reports / "semantic_parity.json", {"schema_version": 2, "status": "NOT_COMPILED_REPORTS_ONLY"})

        status = "REPORTS_ONLY_BLOCKED" if args.reports_only and errors else "REPORTS_ONLY" if args.reports_only else "STAGED"
        _write_json(temp / "manifest.json", _manifest(temp, root, source, args.text_mode, status))
        _publish(temp, output)
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise

    print(f"Quest Source v2 {status}: {report['counts'].get('chapters', 0)} chapter(s), {report['counts'].get('quests', 0)} quest(s).")
    print(f"Output: {output}")
    print(f"Text mode: {args.text_mode}; authoritative Russian is {'inline SNBT' if args.text_mode == 'ru-inline' else 'isolated staging lang' }.")
    print("Minecraft was not launched. Runtime quests and shared lang files were not modified.")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
