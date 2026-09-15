#!/usr/bin/env python3
"""Verify the surviving commercial Tutorial easter-egg chain."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from script_binding_audit import (
    MISSION_ARCHIVES,
    SCRIPT_ARCHIVES,
    effective_entries,
    parse_bindings,
    scene_frame_names,
)


MISSION = "tutorial"
MISSION_FILES = (
    "missions/tutorial/scripts.dta",
    "missions/tutorial/scene2.bin",
    "missions/tutorial/actors.bin",
)
SCRIPT_FILES = (
    "scripts/tutorial/t_ee_button.scr",
    "scripts/tutorial/t_ee_activator1.scr",
    "scripts/tutorial/t_ee_target1.scr",
    "scripts/tutorial/t_ee_target2.scr",
    "scripts/tutorial/t_ee_target3.scr",
    "scripts/tutorial/t_ee_target4.scr",
    "scripts/tutorial/t_fw1.scr",
    "scripts/tutorial/t_fw2.scr",
    "scripts/tutorial/t_fw3.scr",
    "scripts/tutorial/t_fw4.scr",
    "scripts/tutorial/t_fw5.scr",
)
REQUIRED_BINDINGS = {
    "m_alar_1.cylinder01": "t_ee_button.scr",
    "t_dummy_ee_activator1": "t_ee_activator1.scr",
    "t_ee_target1": "t_ee_target1.scr",
    "t_ee_target2": "t_ee_target2.scr",
    "t_ee_target3": "t_ee_target3.scr",
    "t_ee_target4": "t_ee_target4.scr",
    "t_fw1": "t_fw1.scr",
    "t_fw2": "t_fw2.scr",
    "t_fw3": "t_fw3.scr",
    "t_fw4": "t_fw4.scr",
    "t_fw5": "t_fw5.scr",
}
REQUIRED_FRAMES = {
    "la_bedford_1",
    "t_dummy_ee_activator1",
    "t_ee_target1",
    "t_ee_target2",
    "t_ee_target3",
    "t_ee_target4",
}


def normalized_text(data: bytes) -> str:
    return data.decode("cp1252", errors="replace").replace("\r\n", "\n").lower()


def contains_all(text: str, fragments: tuple[str, ...]) -> bool:
    return all(fragment.lower() in text for fragment in fragments)


def audit(game: Path) -> dict[str, object]:
    mission_entries = effective_entries(
        game,
        MISSION_ARCHIVES,
        lambda name: name in MISSION_FILES,
    )
    script_entries = effective_entries(
        game,
        SCRIPT_ARCHIVES,
        lambda name: name in SCRIPT_FILES,
    )

    missing_files = sorted(
        set(MISSION_FILES).difference(mission_entries)
        | set(SCRIPT_FILES).difference(script_entries)
    )
    if missing_files:
        return {
            "game": str(game),
            "logic_complete": False,
            "missing_files": missing_files,
        }

    registry = mission_entries["missions/tutorial/scripts.dta"][1]
    bindings = {
        actor.lower(): script.lower()
        for actor, script in parse_bindings(registry)
    }
    missing_bindings = {
        actor: script
        for actor, script in REQUIRED_BINDINGS.items()
        if bindings.get(actor) != script
    }

    frames: set[str] = set()
    for path in (
        "missions/tutorial/scene2.bin",
        "missions/tutorial/actors.bin",
    ):
        frames.update(scene_frame_names(mission_entries[path][1]))
    missing_frames = sorted(REQUIRED_FRAMES.difference(frames))

    scripts = {
        path.rsplit("/", 1)[-1]: normalized_text(value[1])
        for path, value in script_entries.items()
    }
    checks = {
        "button_fuels_bedford_and_reveals_gold": contains_all(
            scripts["t_ee_button.scr"],
            (
                'frm_findframe(car, "la_bedford_1")',
                'frm_findframe(cihla, "item_cihla")',
                "car_setfuel(car, 1)",
                "frm_seton(cihla, true)",
            ),
        ),
        "activator_requires_item_245": contains_all(
            scripts["t_ee_activator1.scr"],
            ("onsignal(1)", "if(_isininventory(245))"),
        ),
        "activator_starts_first_target": contains_all(
            scripts["t_ee_activator1.scr"],
            ("frm_seton(target1, true)", "sendsignal(target1, 1)"),
        ),
        "activator_starts_five_fireworks": all(
            f"sendsignal(t_fw{index}, 1)" in scripts["t_ee_activator1.scr"]
            for index in range(1, 6)
        ),
        "four_target_chain_survives": (
            all(
                contains_all(
                    scripts[f"t_ee_target{index}.scr"],
                    (
                        "onsignal(1)",
                        "ondeath()",
                        f"frm_seton(t{index + 1}, true)",
                        f"sendsignal(t{index + 1}, 1)",
                    ),
                )
                for index in range(1, 4)
            )
            and contains_all(
                scripts["t_ee_target4.scr"],
                ("onsignal(1)", "ondeath()"),
            )
        ),
    }

    weather_bound = any(
        script in {"t_ee_weather.scr", "t_ee_light.scr"}
        for script in bindings.values()
    )
    logic_complete = (
        not missing_bindings
        and not missing_frames
        and all(checks.values())
        and not weather_bound
    )
    return {
        "game": str(game),
        "logic_complete": logic_complete,
        "active_mission_sources": {
            path: mission_entries[path][0] for path in MISSION_FILES
        },
        "active_script_sources": {
            path: script_entries[path][0] for path in SCRIPT_FILES
        },
        "registry_sha256": hashlib.sha256(registry).hexdigest(),
        "required_bindings": len(REQUIRED_BINDINGS),
        "missing_bindings": missing_bindings,
        "required_frames": len(REQUIRED_FRAMES),
        "missing_frames": missing_frames,
        "checks": checks,
        "weather_or_light_bound_to_secret": weather_bound,
        "historical_result": "4 targets + 5 fireworks",
        "remaining_blocker": "physical vehicle-climbing access under 1.12",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(args.game.resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "Tutorial easter egg: "
            + ("logic complete" if result["logic_complete"] else "incomplete")
        )
        print("Result: " + str(result.get("historical_result", "unknown")))
        print("Blocker: " + str(result.get("remaining_blocker", "unknown")))
    return 0 if result["logic_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
