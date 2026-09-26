#!/usr/bin/env python3
"""Audit script bindings stored in Hidden & Dangerous 2 mission registries."""
from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path

from dta_archive import DtaArchive

MISSION_ARCHIVES = ("missions.dta", "Patch.dta", "SabreSquadron.dta")
SCRIPT_ARCHIVES = ("Scripts.dta", "Patch.dta", "SabreSquadron.dta")
INCLUDE_RE = re.compile(r'^\s*#include\s+"([^"]+\.scr)"', re.IGNORECASE | re.MULTILINE)
ASSIGN_RE = re.compile(
    r'\bScriptAssign\s*\(\s*[^,\r\n]+\s*,\s*"([^"]+)"',
    re.IGNORECASE,
)


def normalize_script_name(value: str) -> str:
    """Return the mission-local filename used by the script archives."""
    name = value.replace("\\", "/").rsplit("/", 1)[-1].strip().lower()
    if name and not name.endswith(".scr"):
        name += ".scr"
    return name


def effective_entries(
    game: Path,
    archive_names: tuple[str, ...],
    wanted,
) -> dict[str, tuple[str, bytes]]:
    result: dict[str, tuple[str, bytes]] = {}
    for archive_name in archive_names:
        with DtaArchive(game / archive_name) as archive:
            for entry in archive.entries:
                normalized = entry.name.replace("\\", "/").lower()
                if wanted(normalized):
                    result[normalized] = (archive_name, archive.read(entry))
    return result


def overlay_loose_entries(
    game: Path,
    root_name: str,
    result: dict[str, tuple[str, bytes]],
    wanted,
) -> None:
    root = game / root_name
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(game).as_posix().lower()
        if wanted(relative):
            result[relative] = ("loose", path.read_bytes())


def registry_string(data: bytes, offset: int) -> tuple[str, int]:
    if offset + 6 > len(data):
        raise ValueError("Truncated mission script registry")
    marker, total = struct.unpack_from("<HI", data, offset)
    if marker != 1 or total < 7 or offset + total > len(data):
        raise ValueError(f"Invalid registry field at offset {offset}")
    raw = data[offset + 6:offset + total]
    if not raw.endswith(b"\x00"):
        raise ValueError(f"Unterminated registry field at offset {offset}")
    return raw[:-1].decode("cp1252"), offset + total


def parse_bindings(data: bytes) -> list[tuple[str, str]]:
    if len(data) < 6:
        raise ValueError("Mission script registry is too short")
    bindings: list[tuple[str, str]] = []
    offset = 6
    while offset < len(data):
        actor, offset = registry_string(data, offset)
        script, offset = registry_string(data, offset)
        bindings.append((actor, script))
    return bindings


def scene_frame_names(data: bytes) -> set[str]:
    """Read exact frame-like strings stored in 0x10 binary fields."""
    names = set()
    offset = 0
    marker = b"\x10\x00"
    while True:
        offset = data.find(marker, offset)
        if offset < 0:
            break
        if offset + 6 <= len(data):
            total = struct.unpack_from("<I", data, offset + 2)[0]
            if 7 <= total <= 4096 and offset + total <= len(data):
                raw = data[offset + 6:offset + total]
                if raw.endswith(b"\0") and b"\0" not in raw[:-1]:
                    value = raw[:-1].decode("cp1252", errors="replace")
                    if value and all(ord(character) >= 32 for character in value):
                        names.add(value.lower())
        offset += 2
    return names


def audit(game: Path, selected: set[str]) -> dict[str, object]:
    mission_prefixes = tuple(f"missions/{name}/" for name in selected)
    script_prefixes = tuple(f"scripts/{name}/" for name in selected)
    missions = effective_entries(
        game,
        MISSION_ARCHIVES,
        lambda name: (
            name.endswith("/scripts.dta") or name.endswith("/mpscripts.dta")
            or name.endswith("/scene2.bin") or name.endswith("/actors.bin")
            or name.endswith("/sounds.bin")
        ) and (not selected or name.startswith(mission_prefixes)),
    )
    overlay_loose_entries(
        game, "Missions", missions,
        lambda name: (
            name.endswith("/scripts.dta") or name.endswith("/mpscripts.dta")
            or name.endswith("/scene2.bin") or name.endswith("/actors.bin")
            or name.endswith("/sounds.bin")
        ) and (not selected or name.startswith(mission_prefixes)),
    )
    scripts = effective_entries(
        game,
        SCRIPT_ARCHIVES,
        lambda name: name.endswith(".scr")
        and (not selected or name.startswith(script_prefixes)),
    )
    overlay_loose_entries(
        game, "Scripts", scripts,
        lambda name: name.endswith(".scr")
        and (not selected or name.startswith(script_prefixes)),
    )
    registries = sorted(
        name for name in missions
        if name.startswith("missions/")
        and (name.endswith("/scripts.dta") or name.endswith("/mpscripts.dta"))
    )
    registries_by_mission: dict[str, list[str]] = {}
    for registry_path in registries:
        mission = registry_path.split("/")[1]
        registries_by_mission.setdefault(mission, []).append(registry_path)

    results = []
    for mission, mission_registries in sorted(registries_by_mission.items()):
        bindings: list[tuple[str, str]] = []
        binding_details = []
        registry_files = []
        for registry_path in mission_registries:
            archive_name, registry_data = missions[registry_path]
            current = parse_bindings(registry_data)
            bindings.extend(current)
            binding_details.extend({
                "registry": registry_path,
                "actor": actor,
                "script": script,
                "normalized_script": normalize_script_name(script),
            } for actor, script in current if script.strip())
            registry_files.append({
                "path": registry_path,
                "archive": archive_name,
                "binding_count": len(current),
            })
        attached = {
            normalize_script_name(script)
            for _, script in bindings
            if script.strip()
        }
        prefix = f"scripts/{mission}/"
        available = {
            name[len(prefix):]
            for name in scripts
            if name.startswith(prefix)
            and "/" not in name[len(prefix):]
            and name.endswith(".scr")
        }
        used = set(attached)
        changed = True
        while changed:
            changed = False
            for script_name in tuple(used):
                source = scripts.get(prefix + script_name)
                if source is None:
                    continue
                text = source[1].decode("cp1252", errors="replace")
                referenced = INCLUDE_RE.findall(text) + ASSIGN_RE.findall(text)
                for referenced_name in referenced:
                    normalized = normalize_script_name(referenced_name)
                    if normalized and normalized not in used:
                        used.add(normalized)
                        changed = True
        missing = sorted(attached - available)
        unbound = sorted(available - used)
        actor_names = set()
        for path in (
            f"missions/{mission}/scene2.bin",
            f"missions/{mission}/actors.bin",
            f"missions/{mission}/sounds.bin",
        ):
            if path in missions:
                actor_names.update(scene_frame_names(missions[path][1]))
        matching_actors = sorted(
            script for script in unbound
            if script.rsplit(".", 1)[0].lower() in actor_names
        )
        bound_by_actor: dict[str, set[str]] = {}
        for actor, script in bindings:
            bound_by_actor.setdefault(actor.lower(), set()).add(
                normalize_script_name(script)
            )
        free_matching_actors = []
        conflicting_matching_actors = []
        for script in matching_actors:
            actor = script.rsplit(".", 1)[0]
            current = sorted(bound_by_actor.get(actor.lower(), set()))
            if current:
                conflicting_matching_actors.append({
                    "script": script, "actor": actor,
                    "bound_scripts": current,
                })
            else:
                free_matching_actors.append(script)
        archives = sorted({item["archive"] for item in registry_files})
        results.append({
            "mission": mission,
            "registry_archive": ", ".join(archives),
            "registry_count": len(registry_files),
            "registry_files": registry_files,
            "binding_count": len(bindings),
            "attached_script_count": len(attached),
            "included_script_count": len(used - attached),
            "available_script_count": len(available),
            "missing_attached_scripts": missing,
            "missing_attached_bindings": [
                item for item in binding_details
                if item["normalized_script"] in missing
            ],
            "unbound_scripts": unbound,
            "unbound_scripts_with_matching_actor": matching_actors,
            "unbound_scripts_with_free_matching_actor": free_matching_actors,
            "unbound_scripts_with_conflicting_matching_actor": conflicting_matching_actors,
        })
    return {
        "game": str(game),
        "mission_count": len(results),
        "registry_count": len(registries),
        "missions": results,
    }
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--mission", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = audit(
        arguments.game,
        {value.replace("\\", "/").strip("/").lower() for value in arguments.mission},
    )
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded + "\n", encoding="utf-8")
    if arguments.json:
        print(encoded)
    else:
        for mission in result["missions"]:
            print(
                f"{mission['mission']}: {mission['binding_count']} bindings, "
                f"{mission['available_script_count']} scripts, "
                f"{len(mission['unbound_scripts'])} unbound"
            )
            for script in mission["unbound_scripts"]:
                print(f"  {script}")
            for script in mission["missing_attached_scripts"]:
                print(f"  MISSING {script}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
