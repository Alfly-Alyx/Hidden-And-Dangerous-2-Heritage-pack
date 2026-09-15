#!/usr/bin/env python3
"""Audit Africa 4 key placements and both commercial easter-egg trigger owners."""
from __future__ import annotations

import argparse
import json
import math
import re
import struct
from pathlib import Path

from script_binding_audit import (
    MISSION_ARCHIVES,
    SCRIPT_ARCHIVES,
    effective_entries,
    parse_bindings,
)
from scene_frame_position_audit import audit as scene_audit


ITEMS_PATH = "missions/africa4/items.dat"
REGISTRY_PATH = "missions/africa4/scripts.dta"
SCRIPT_PATH = "scripts/africa4/af3b_ee_activator.scr"
KEY_IDS = (240, 241, 242)
EXPECTED_OWNERS = {"w_mg42lie_00", "dummy_ee_activator"}
RECORD_SIZE = 61


def placed_item_records(data: bytes, item_id: int) -> list[dict[str, object]]:
    """Recognize the fixed-size world-placement records in items.dat.

    The same item identifiers also occur in inventory declarations. Placement
    records are distinguished by their enabled word, unit scale, normalized
    rotation and 17-byte zero tail.
    """
    needle = struct.pack("<I", item_id)
    result = []
    offset = data.find(needle)
    while offset >= 0:
        if offset + RECORD_SIZE <= len(data):
            instance_id, enabled = struct.unpack_from("<II", data, offset + 4)
            position = struct.unpack_from("<3f", data, offset + 12)
            scale = struct.unpack_from("<f", data, offset + 24)[0]
            rotation = struct.unpack_from("<4f", data, offset + 28)
            zero_tail = data[offset + 44:offset + RECORD_SIZE]
            rotation_length = math.sqrt(sum(value * value for value in rotation))
            if (
                enabled == 1
                and abs(scale - 1.0) < 1e-5
                and all(math.isfinite(value) for value in position + rotation)
                and abs(rotation_length - 1.0) < 1e-3
                and zero_tail == bytes(17)
            ):
                result.append({
                    "item_id": item_id,
                    "instance_id": instance_id,
                    "world_position": [
                        round(value, 6) for value in position
                    ],
                    "rotation": [
                        round(value, 6) for value in rotation
                    ],
                    "record_offset": offset,
                })
        offset = data.find(needle, offset + 1)
    return result


def audit(game: Path) -> dict[str, object]:
    mission_entries = effective_entries(
        game,
        MISSION_ARCHIVES,
        lambda name: name in {ITEMS_PATH, REGISTRY_PATH},
    )
    script_entries = effective_entries(
        game,
        SCRIPT_ARCHIVES,
        lambda name: name == SCRIPT_PATH,
    )
    missing = sorted(
        {ITEMS_PATH, REGISTRY_PATH}.difference(mission_entries)
        | {SCRIPT_PATH}.difference(script_entries)
    )
    if missing:
        return {
            "game": str(game),
            "ok": False,
            "errors": ["Missing commercial entries: " + ", ".join(missing)],
        }

    items_source, items_data = mission_entries[ITEMS_PATH]
    registry_source, registry_data = mission_entries[REGISTRY_PATH]
    script_source, script_data = script_entries[SCRIPT_PATH]

    errors = []
    keys = []
    for item_id in KEY_IDS:
        records = placed_item_records(items_data, item_id)
        if len(records) != 1:
            errors.append(
                f"item {item_id}: expected one placement, found {len(records)}"
            )
        keys.extend(records)

    owners = sorted({
        actor
        for actor, script in parse_bindings(registry_data)
        if script.casefold() == "af3b_ee_activator.scr"
    }, key=str.casefold)
    if {owner.casefold() for owner in owners} != EXPECTED_OWNERS:
        errors.append(
            "unexpected AF3b_ee_activator.scr owners: " + ", ".join(owners)
        )

    positions = scene_audit(
        game,
        "africa4",
        owners,
        [],
        0,
    )
    if not positions["ok"]:
        errors.extend(positions["errors"])
    trigger_positions = []
    for frame in positions["matches"]:
        trigger_positions.append({
            "name": frame["name"],
            "world_position": frame["position"],
            "blob": frame["blob"],
            "archive": positions["sources"][frame["blob"]],
        })

    script_text = script_data.decode("cp1252", errors="replace")
    proximity_checks = {
        str(item_id): bool(re.search(
            rf"_ItemInRange\s*\(\s*{item_id}\s*,\s*3\s*\)",
            script_text,
            re.IGNORECASE,
        ))
        for item_id in KEY_IDS
    }
    disabled_by_patch = bool(re.search(
        r"Whenever\s+iir[\s\S]*?\{\s*goto\s+END\s*;",
        script_text,
        re.IGNORECASE,
    ))
    if not all(proximity_checks.values()):
        errors.append("one or more three-metre key checks are missing")
    if not disabled_by_patch:
        errors.append("effective commercial script is not the 1.12-disabled form")

    return {
        "game": str(game),
        "ok": not errors,
        "errors": errors,
        "sources": {
            ITEMS_PATH: items_source,
            REGISTRY_PATH: registry_source,
            SCRIPT_PATH: script_source,
        },
        "keys": keys,
        "proximity_radius_metres": 3,
        "proximity_checks": proximity_checks,
        "trigger_owners": owners,
        "trigger_positions": trigger_positions,
        "disabled_by_patch_1_12": disabled_by_patch,
        "static_conclusion": (
            "The original three-key branch is complete but its shared script "
            "is bound to two distinct owners."
        ),
        "runtime_validation_required": (
            "Test each owner separately after restoration before publishing "
            "a definitive player-facing drop point."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.game.resolve())
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
