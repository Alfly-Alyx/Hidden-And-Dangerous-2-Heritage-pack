#!/usr/bin/env python3
"""Audit one commercial H&D2 mission before declaring its scripts closed."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from objective_audit import split_comments
from script_binding_audit import (
    MISSION_ARCHIVES,
    SCRIPT_ARCHIVES,
    effective_entries,
    normalize_script_name,
    parse_bindings,
)


INCLUDE_RE = re.compile(r'^\s*#include\s+"([^"]+\.scr)"', re.I | re.M)
ASSIGN_RE = re.compile(
    r'\bScriptAssign\s*\(\s*[^,\r\n]+\s*,\s*"([^"]+)"', re.I)
MOVE_RE = re.compile(
    r'\bHUMAN_(?:Move|Drive)\s*\(\s*"([^"]+)"', re.I)
FRAME_RE = re.compile(
    r'\bFRM_FindFrame\s*\(\s*[A-Za-z_]\w*\s*,\s*"([^"]+)"', re.I)
LABEL_RE = re.compile(r'\bLabel\s+([A-Za-z_]\w*)\s*:', re.I)
GOTO_RE = re.compile(r'\bgoto\s+([A-Za-z_]\w*)\s*;', re.I)


def normalized(value: str) -> str:
    return value.replace("\\", "/").lower()


def mission_entries(game: Path, mission: str):
    prefix = f"missions/{mission}/"
    return effective_entries(
        game,
        MISSION_ARCHIVES,
        lambda name: name.startswith(prefix)
        and name.endswith((
            "/scripts.dta", "/mpscripts.dta", "/check2.bin",
            "/scene2.bin", "/actors.bin", "/sounds.bin",
        )),
    )


def script_entries(game: Path, mission: str):
    prefix = f"scripts/{mission}/"
    return effective_entries(
        game,
        SCRIPT_ARCHIVES,
        lambda name: name.startswith(prefix) and name.endswith(".scr"),
    )


def transitive_scripts(
    roots: set[str], texts: dict[str, str]
) -> tuple[set[str], set[str]]:
    used = set(roots)
    missing = set()
    pending = list(roots)
    while pending:
        current = pending.pop()
        text = texts.get(current)
        if text is None:
            missing.add(current)
            continue
        dependencies = INCLUDE_RE.findall(text) + ASSIGN_RE.findall(text)
        for dependency in dependencies:
            target = normalize_script_name(dependency)
            if target and target not in used:
                used.add(target)
                pending.append(target)
    return used, missing


def blob_contains(blobs: list[bytes], value: str) -> bool:
    needle = value.encode("cp1252", errors="replace").lower()
    return any(needle in blob.lower() for blob in blobs)


def audit(game: Path, mission: str) -> dict[str, object]:
    mission = normalized(mission).strip("/")
    assets = mission_entries(game, mission)
    scripts = script_entries(game, mission)
    registries = [
        (name, data)
        for name, (_, data) in assets.items()
        if name.endswith(("/scripts.dta", "/mpscripts.dta"))
    ]
    bindings = []
    for _, data in registries:
        bindings.extend(parse_bindings(data))

    texts = {
        name.rsplit("/", 1)[-1]: data.decode("cp1252", errors="replace")
        for name, (_, data) in scripts.items()
    }
    roots = {normalize_script_name(script) for _, script in bindings}
    used, missing_scripts = transitive_scripts(roots, texts)
    available = set(texts)

    active_texts = {
        name: split_comments(texts[name])[0]
        for name in sorted(used & available)
    }
    movement_calls = []
    frame_calls = []
    missing_labels = []
    for script, text in active_texts.items():
        movement_calls.extend(
            {"script": script, "checkpoint": match.group(1)}
            for match in MOVE_RE.finditer(text)
        )
        frame_calls.extend(
            {"script": script, "frame": match.group(1)}
            for match in FRAME_RE.finditer(text)
        )
        labels = {match.group(1).lower() for match in LABEL_RE.finditer(text)}
        for target in GOTO_RE.findall(text):
            if target.lower() not in labels:
                missing_labels.append({"script": script, "label": target})

    checkpoint_blobs = [
        data for name, (_, data) in assets.items()
        if name.endswith("/check2.bin")
    ]
    scene_blobs = [
        data for name, (_, data) in assets.items()
        if name.endswith(("/scene2.bin", "/actors.bin", "/sounds.bin"))
    ]
    checkpoints = sorted({item["checkpoint"] for item in movement_calls},
                         key=str.lower)
    frames = sorted({item["frame"] for item in frame_calls}, key=str.lower)
    missing_checkpoints = [
        value for value in checkpoints
        if not blob_contains(checkpoint_blobs, value)
    ]
    missing_frames = [
        value for value in frames if not blob_contains(scene_blobs, value)
    ]

    return {
        "game": str(game),
        "mission": mission,
        "registry_count": len(registries),
        "binding_count": len(bindings),
        "direct_script_count": len(roots),
        "used_script_count": len(used),
        "available_script_count": len(available),
        "missing_scripts": sorted(missing_scripts),
        "unbound_scripts": sorted(available - used),
        "movement_call_count": len(movement_calls),
        "distinct_checkpoint_count": len(checkpoints),
        "missing_checkpoints": missing_checkpoints,
        "frame_call_count": len(frame_calls),
        "distinct_frame_count": len(frames),
        "missing_frames": missing_frames,
        "missing_labels": missing_labels,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("mission")
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.game, arguments.mission)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
