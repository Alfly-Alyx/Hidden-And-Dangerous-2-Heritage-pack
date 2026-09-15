#!/usr/bin/env python3
"""Verify the Burma 1 three-skull easter egg and report exact positions."""
from __future__ import annotations

import argparse
import json
import math
import re
import struct
from pathlib import Path

from dta_archive import DtaArchive
from objective_audit import blocks, direct, split_comments, walk
from script_binding_audit import parse_bindings


MISSION_ARCHIVES = ("missions.dta", "Patch.dta", "SabreSquadron.dta")
SCRIPT_ARCHIVES = ("Scripts.dta", "Patch.dta", "SabreSquadron.dta")
SCENE_PATH = "missions/burma1/scene2.bin"
REGISTRY_PATH = "missions/burma1/scripts.dta"
CONTROLLER_PATH = "scripts/burma1/bu1_ee.scr"
SKULL_SCRIPT_PATH = "scripts/burma1/bu1_lebka1.scr"
SKULLS = ("lebka", "lebka2", "lebka3")
EXPECTED_BINDINGS = {
    "bu1_ee": "bu1_ee.scr",
    "lebka": "bu1_lebka1.scr",
    "lebka2": "bu1_lebka1.scr",
    "lebka3": "bu1_lebka1.scr",
}


def normalized(value: str) -> str:
    return value.replace("\\", "/").casefold()


def effective(game: Path, archives: tuple[str, ...], wanted: set[str]):
    result = {}
    for archive_name in archives:
        path = game / archive_name
        if not path.is_file():
            continue
        with DtaArchive(path) as archive:
            for entry in archive.entries:
                name = normalized(entry.name)
                if name in wanted:
                    result[name] = {
                        "source": archive_name,
                        "entry": entry.name,
                        "data": archive.read(entry),
                    }
    return result


def scalar_name(node) -> str | None:
    names = direct(node, 0x10)
    if not names:
        return None
    return names[0].payload.rstrip(b"\0").decode(
        "cp1252", errors="replace"
    )


def positioned_frames(data: bytes) -> dict[str, list[dict[str, object]]]:
    root = blocks(data, 0, len(data))
    if root is None:
        raise ValueError("Invalid Burma 1 scene block structure")
    result: dict[str, list[dict[str, object]]] = {}
    for node in walk(root):
        name = scalar_name(node)
        positions = direct(node, 0x20)
        if not name or not positions or len(positions[0].payload) < 12:
            continue
        position = struct.unpack_from("<3f", positions[0].payload)
        if not all(math.isfinite(value) for value in position):
            continue
        result.setdefault(name.casefold(), []).append({
            "name": name,
            "position": [round(value, 6) for value in position],
            "record_kind": node.kind,
            "record_offset": node.start,
        })
    return result


def has_active(text: str, expression: str) -> bool:
    active, _ = split_comments(text)
    return bool(re.search(expression, active, re.I | re.S))


def audit(game: Path) -> dict[str, object]:
    errors = []
    mission = effective(
        game, MISSION_ARCHIVES, {SCENE_PATH, REGISTRY_PATH}
    )
    scripts = effective(
        game, SCRIPT_ARCHIVES, {CONTROLLER_PATH, SKULL_SCRIPT_PATH}
    )
    required = {
        SCENE_PATH: mission.get(SCENE_PATH),
        REGISTRY_PATH: mission.get(REGISTRY_PATH),
        CONTROLLER_PATH: scripts.get(CONTROLLER_PATH),
        SKULL_SCRIPT_PATH: scripts.get(SKULL_SCRIPT_PATH),
    }
    missing = sorted(name for name, item in required.items() if item is None)
    if missing:
        return {
            "game": str(game), "ok": False,
            "errors": ["Missing required entries: " + ", ".join(missing)],
        }

    scene = positioned_frames(mission[SCENE_PATH]["data"])
    positions = {}
    for skull in SKULLS:
        matches = scene.get(skull, [])
        if len(matches) != 1:
            errors.append(
                f"Expected one positioned scene frame {skull}, found {len(matches)}"
            )
        else:
            positions[skull] = matches[0]

    bindings = {
        actor.casefold(): script.replace("\\", "/").rsplit("/", 1)[-1].casefold()
        for actor, script in parse_bindings(mission[REGISTRY_PATH]["data"])
        if actor.casefold() in EXPECTED_BINDINGS
    }
    if bindings != EXPECTED_BINDINGS:
        errors.append(
            "Easter-egg registry bindings differ from the expected four actors"
        )

    controller = scripts[CONTROLLER_PATH]["data"].decode(
        "cp1252", errors="replace"
    )
    skull_script = scripts[SKULL_SCRIPT_PATH]["data"].decode(
        "cp1252", errors="replace"
    )
    contracts = {
        "enemy_count_arms_activation": has_active(
            controller,
            r"Whenever\s+enemy\s*\(\s*_GetCountOfCarnageEnemies\s*\(\s*\)\s*==\s*0\s*\)"
            r"[\s\S]{0,120}?activate\s*=\s*1",
        ),
        "three_skulls_required": has_active(
            controller,
            r"OnSignal\s*\(\s*1\s*\)[\s\S]{0,160}?skulls\s*=\s*skulls\s*\+\s*1"
            r"[\s\S]{0,100}?skulls\s*==\s*3",
        ),
        "activation_guarded": has_active(
            controller,
            r"Label\s+start\s*:[\s\S]{0,100}?If\s*\(\s*activate\s*==\s*1\s*\)",
        ),
        "three_figures_signalled": all(
            has_active(controller, rf"SendSignal\s*\(\s*{name}\s*,\s*1\s*\)")
            for name in ("n01", "n02", "n03")
        ),
        "skull_death_signals_controller": has_active(
            skull_script,
            r"OnDeath\s*\(\s*\)[\s\S]{0,100}?SendSignal\s*\(\s*ee\s*,\s*1\s*\)",
        ),
    }
    for name, passed in contracts.items():
        if not passed:
            errors.append("Script contract failed: " + name)

    return {
        "game": str(game),
        "ok": not errors,
        "errors": errors,
        "sources": {
            name: item["source"] for name, item in required.items()
        },
        "bindings": bindings,
        "contracts": contracts,
        "positions": positions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.game)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({
        "ok": report["ok"],
        "errors": report["errors"],
        "positions": report.get("positions", {}),
    }, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
