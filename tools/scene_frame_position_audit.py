#!/usr/bin/env python3
"""Read exact positions of selected H&D2 mission frames from commercial data."""
from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

from dta_archive import DtaArchive
from objective_audit import blocks, direct, walk


MISSION_ARCHIVES = ("missions.dta", "Patch.dta", "SabreSquadron.dta")
POSITION_BLOBS = ("scene2.bin", "actors.bin", "sounds.bin")


def normalized(value: str) -> str:
    return value.replace("\\", "/").casefold()


def effective_blobs(game: Path, mission: str):
    wanted = {
        f"missions/{mission}/{filename}" for filename in POSITION_BLOBS
    }
    result = {}
    for archive_name in MISSION_ARCHIVES:
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
    loose_root = game / "Missions" / mission
    if loose_root.is_dir():
        for filename in POSITION_BLOBS:
            path = loose_root / filename
            if path.is_file():
                name = f"missions/{mission}/{filename}"
                result[name] = {
                    "source": "loose",
                    "entry": str(path),
                    "data": path.read_bytes(),
                }
    return result


def positioned_frames(data: bytes, source: str):
    root = blocks(data, 0, len(data))
    if root is None:
        raise ValueError(f"Invalid block structure: {source}")
    result = []
    for node in walk(root):
        names = direct(node, 0x10)
        local_positions = direct(node, 0x20)
        world_positions = direct(node, 0x2C)
        positions = world_positions or local_positions
        if not names or not positions or len(positions[0].payload) < 12:
            continue
        name = names[0].payload.rstrip(b"\0").decode(
            "cp1252", errors="replace"
        )
        position = struct.unpack_from("<3f", positions[0].payload)
        local_position = (
            struct.unpack_from("<3f", local_positions[0].payload)
            if local_positions and len(local_positions[0].payload) >= 12
            else position
        )
        if not name or not all(math.isfinite(value) for value in position):
            continue
        result.append({
            "name": name,
            "position": [round(value, 6) for value in position],
            "local_position": [
                round(value, 6) for value in local_position
            ],
            "position_space": "world" if world_positions else "local",
            "record_kind": node.kind,
            "record_offset": node.start,
            "blob": source,
        })
    return result


def distance(left, right) -> float:
    return math.sqrt(sum(
        (float(a) - float(b)) ** 2 for a, b in zip(left, right)
    ))


def audit(
    game: Path, mission: str, names: list[str], contains: list[str], nearest: int
):
    mission = normalized(mission).strip("/")
    blobs = effective_blobs(game, mission)
    frames = []
    sources = {}
    errors = []
    for path, item in sorted(blobs.items()):
        sources[path] = item["source"]
        try:
            frames.extend(positioned_frames(item["data"], path))
        except ValueError as error:
            errors.append(str(error))

    exact = {name.casefold() for name in names}
    fragments = [value.casefold() for value in contains]
    selected = [
        frame for frame in frames
        if frame["name"].casefold() in exact
        or any(fragment in frame["name"].casefold() for fragment in fragments)
    ]
    missing = sorted(
        name for name in names
        if not any(frame["name"].casefold() == name.casefold() for frame in frames)
    )
    if missing:
        errors.append("Missing requested frames: " + ", ".join(missing))

    if nearest > 0:
        for target in selected:
            candidates = sorted(
                (
                    (
                        distance(target["position"], other["position"]),
                        other,
                    )
                    for other in frames
                    if other is not target
                ),
                key=lambda item: (item[0], item[1]["name"].casefold()),
            )[:nearest]
            target["nearest"] = [
                {
                    "distance": round(separation, 3),
                    "name": other["name"],
                    "position": other["position"],
                    "blob": other["blob"],
                }
                for separation, other in candidates
            ]

    scene_positions = [
        frame["position"] for frame in frames
        if frame["blob"].endswith("/scene2.bin")
        and all(abs(float(value)) < 10000 for value in frame["position"])
    ]
    extent = None
    if scene_positions:
        extent = {
            "minimum": [
                min(float(position[axis]) for position in scene_positions)
                for axis in range(3)
            ],
            "maximum": [
                max(float(position[axis]) for position in scene_positions)
                for axis in range(3)
            ],
        }
    return {
        "game": str(game),
        "mission": mission,
        "ok": not errors,
        "errors": errors,
        "sources": sources,
        "positioned_frames_scanned": len(frames),
        "scene_extent": extent,
        "matches": selected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("mission")
    parser.add_argument("--name", action="append", default=[])
    parser.add_argument("--contains", action="append", default=[])
    parser.add_argument("--nearest", type=int, default=0)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    if not arguments.name and not arguments.contains:
        parser.error("at least one --name or --contains filter is required")
    if arguments.nearest < 0 or arguments.nearest > 50:
        parser.error("--nearest must be between 0 and 50")
    report = audit(
        arguments.game, arguments.mission, arguments.name,
        arguments.contains, arguments.nearest,
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
