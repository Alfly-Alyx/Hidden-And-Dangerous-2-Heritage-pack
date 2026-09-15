#!/usr/bin/env python3
"""Build a curated audit of easter-egg world positions in commercial missions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scene_frame_position_audit import audit as scene_audit


MISSIONS = (
    {
        "id": "tutorial",
        "mission": "tutorial",
        "title": "Tutorial",
        "targets": {
            "M_ALAR_1": (
                "parent model of the bound button M_ALAR_1.Cylinder01"
            ),
            "la_Bedford_1": "vehicle used by the historical access route",
            "T_dummy_EE_Activator1": "gold-bar activation zone",
            "T_EE_Target1": "first hidden target",
            "T_EE_Target2": "second hidden target",
            "T_EE_Target3": "third hidden target",
            "T_EE_Target4": "fourth hidden target",
        },
        "note": (
            "The button is a model subframe and inherits the position of "
            "M_ALAR_1; the gold-bar item is revealed dynamically."
        ),
    },
    {
        "id": "alps1",
        "mission": "alps1",
        "title": "Alps 1 - Babes in the Wood",
        "targets": {
            "kwdet": "hidden two-metre gathering point for the four crewmen",
        },
    },
    {
        "id": "alps2",
        "mission": "alps2",
        "title": "Alps 2 - Estate Agent",
        "targets": {
            "eggdetect1": "first gold-bar zone",
            "eggdetect2": "second gold-bar zone",
            "eggdetect3": "third gold-bar zone",
            "egg": "effect controller",
            "kostej_": "first revealed skeleton",
            "kostej_2": "second revealed skeleton",
        },
    },
    {
        "id": "normandy1",
        "mission": "normandy",
        "title": "Normandy 1 - Lighthouse",
        "targets": {
            "N1_EE": "ten-bottle counter",
            "N48": "guard signalled after the tenth bottle",
            "bottle": "first bottle",
            "bottle2": "second bottle",
            "bottle3": "third bottle",
            "bottle4": "fourth bottle",
            "bottle5": "fifth bottle",
            "bottle6": "sixth bottle",
            "bottle7": "seventh bottle",
            "bottle8": "eighth bottle",
            "bottle9": "ninth bottle",
            "bottle10": "tenth bottle",
        },
    },
    {
        "id": "africa1",
        "mission": "africa1",
        "title": "Africa 1 - Spaghetti Airport",
        "targets": {
            "dummy_ee": "owner of AF1_ee.scr",
            "AF1_21": "officer required by the secret",
            "la_Jeepsas_01": "jeep required by the secret",
            "dummy_fire_portal": "hidden effect portal",
            "camera_ee": "hidden sequence camera",
        },
    },
    {
        "id": "africa4",
        "mission": "africa4",
        "title": "Africa 4 - seventh easter egg",
        "targets": {
            "w_mg42Lie_00": (
                "first owner bound to AF3b_ee_activator.scr"
            ),
            "dummy_ee_activator": (
                "second owner bound to AF3b_ee_activator.scr"
            ),
            "dummy_ee": "meteor-sequence controller",
            "meteor01": "meteor track object",
            "dummy_meteor_01": "meteor effect anchor",
        },
        "note": (
            "The commercial registry binds the same three-key proximity "
            "script to two owners. Runtime validation must identify whether "
            "both activation zones are live after the 1.12 override."
        ),
    },
)


def curated_frame(frame: dict[str, object], role: str, sources) -> dict[str, object]:
    result = {
        "name": frame["name"],
        "role": role,
        "world_position": frame["position"],
        "position_space": frame["position_space"],
        "blob": frame["blob"],
        "archive": sources[frame["blob"]],
    }
    if frame["local_position"] != frame["position"]:
        result["local_position"] = frame["local_position"]
    return result


def audit(game: Path) -> dict[str, object]:
    results = []
    errors = []
    for specification in MISSIONS:
        targets = specification["targets"]
        raw = scene_audit(
            game,
            specification["mission"],
            list(targets),
            [],
            0,
        )
        indexed = {
            frame["name"].casefold(): frame for frame in raw["matches"]
        }
        frames = []
        for expected, role in targets.items():
            frame = indexed.get(expected.casefold())
            if frame is None:
                errors.append(
                    f"{specification['id']}: missing frame {expected}"
                )
                continue
            if frame["position_space"] != "world":
                errors.append(
                    f"{specification['id']}: {expected} has no world position"
                )
            frames.append(curated_frame(frame, role, raw["sources"]))
        result = {
            "id": specification["id"],
            "mission": specification["mission"],
            "title": specification["title"],
            "frames": frames,
        }
        if "note" in specification:
            result["note"] = specification["note"]
        results.append(result)
        errors.extend(raw["errors"])
    return {
        "game": str(game),
        "ok": not errors,
        "coordinate_field": "0x2C world transform",
        "local_coordinate_field": "0x20 local transform",
        "mission_count": len(results),
        "frame_count": sum(len(item["frames"]) for item in results),
        "errors": errors,
        "missions": results,
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
