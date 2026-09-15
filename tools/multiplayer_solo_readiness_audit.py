#!/usr/bin/env python3
"""Prove whether multiplayer maps have become real single-player missions.

Static assets are necessary but never sufficient.  A conversion is only
reported as validated when it also has an explicit runtime record covering
menu launch, player spawn, objectives and mission completion.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from dta_archive import DtaArchive
from menu_gui_audit import catalogue
from objective_audit import split_comments
from script_binding_audit import (
    ASSIGN_RE,
    INCLUDE_RE,
    MISSION_ARCHIVES,
    SCRIPT_ARCHIVES,
    normalize_script_name,
    parse_bindings,
)


CATALOGUE_ARCHIVES = ("others.DTA", "Patch.dta", "SabreSquadron.dta")
MAPLIST_ARCHIVES = ("others.DTA", "Patch.dta", "SabreSquadron.dta")
CATALOGUE_RE = re.compile(r"^gamedata/gamedata\d+\.gdt$", re.I)
OBJECTIVE_RE = re.compile(r"\bSetObjectiveStatus\s*\(", re.I)
CORE_MINIMUM_SIZES = {
    "map.4ds": 100,
    "tree.klz": 1000,
    "scene.4ds": 1000,
    "loader.4ds": 100,
}
CORE_FILES = tuple(CORE_MINIMUM_SIZES)
MISSION_FILES = ("actors.bin", "scene2.bin", "check2.bin")
PROTOTYPES = ("afrika5_mp", "normandy3_mp_zone")
RUNTIME_CHECKS = ("menu_launch", "player_spawn", "objectives", "completion")


def normalized(value: str) -> str:
    return value.replace("\\", "/").strip("/").casefold()


def effective_archive_entries(
    game: Path, archives: tuple[str, ...], predicate, load_data=lambda _name: True
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for archive_name in archives:
        path = game / archive_name
        if not path.is_file():
            continue
        with DtaArchive(path) as archive:
            for entry in archive.entries:
                name = normalized(entry.name)
                if predicate(name):
                    result[name] = {
                        "source": archive_name,
                        "size": entry.size,
                        "data": archive.read(entry) if load_data(name) else None,
                    }
    return result


def overlay_loose_files(
    game: Path, root_name: str, suffixes: tuple[str, ...], result,
    load_data=lambda _name: True,
) -> None:
    root = game / root_name
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if not path.is_file() or not path.name.casefold().endswith(suffixes):
            continue
        relative = normalized(path.relative_to(game).as_posix())
        result[relative] = {
            "source": "loose",
            "size": path.stat().st_size,
            "data": path.read_bytes() if load_data(relative) else None,
        }


def parse_maplist(data: bytes, source: str) -> dict[str, dict[str, object]]:
    text = data.decode("cp1252", errors="replace")
    result: dict[str, dict[str, object]] = {}
    for style_match in re.finditer(
        r'<GAMESTYLE\s+type="([^"]+)"[\s\S]*?</GAMESTYLE>', text, re.I
    ):
        style = style_match.group(1).casefold()
        for map_match in re.finditer(
            r'<MAP\b[\s\S]*?</MAP>', style_match.group(0), re.I
        ):
            block = map_match.group(0)
            directory = re.search(r'\bdir\s*=\s*"([^"]+)"', block, re.I)
            if not directory:
                continue
            name = re.search(r'\bname\s*=\s*"([^"]*)"', block, re.I)
            key = normalized(directory.group(1))
            row = result.setdefault(key, {
                "directory": directory.group(1),
                "names": [],
                "styles": [],
                "declared_objectives": 0,
                "sources": [],
            })
            if name and name.group(1) not in row["names"]:
                row["names"].append(name.group(1))
            if style not in row["styles"]:
                row["styles"].append(style)
            row["declared_objectives"] = max(
                int(row["declared_objectives"]),
                len(re.findall(r"<OBJECTIVE\b", block, re.I)),
            )
            if source not in row["sources"]:
                row["sources"].append(source)
    return result


def effective_commercial_maplist(game: Path) -> tuple[bytes, str]:
    data = None
    source = None
    for archive_name in MAPLIST_ARCHIVES:
        path = game / archive_name
        if not path.is_file():
            continue
        with DtaArchive(path) as archive:
            for entry in archive.entries:
                if normalized(entry.name) == "gamedata/mpmaplist.txt":
                    data = archive.read(entry)
                    source = archive_name
    if data is None or source is None:
        raise ValueError("Commercial multiplayer catalogue not found")
    return data, source


def singleplayer_catalogues(game: Path) -> tuple[dict[str, dict], list[dict]]:
    entries = effective_archive_entries(
        game, CATALOGUE_ARCHIVES, lambda name: bool(CATALOGUE_RE.match(name))
    )
    decoded = [
        catalogue(item["data"], f"{item['source']}:{name}")
        for name, item in sorted(entries.items())
    ]
    loose_root = game / "GameData"
    if loose_root.is_dir():
        for path in sorted(loose_root.glob("Gamedata*.gdt")):
            decoded.append(catalogue(path.read_bytes(), str(path)))

    missions: dict[str, dict] = {}
    for cat in decoded:
        for campaign in cat["campaigns"]:
            for mission in campaign["missions"]:
                if mission["directory"]:
                    missions[normalized(mission["directory"])] = {
                        "source": cat["source"],
                        "objective_count": len(mission["objectives"]),
                    }
        for mission in cat["unassigned_missions"]:
            if mission["directory"]:
                missions[normalized(mission["directory"])] = {
                    "source": cat["source"],
                    "objective_count": len(mission["objectives"]),
                }
    return missions, decoded


def mission_assets(game: Path) -> dict[str, dict[str, dict[str, object]]]:
    entries = effective_archive_entries(
        game,
        MISSION_ARCHIVES,
        lambda name: name.startswith("missions/") and name.count("/") == 2,
        lambda name: name.endswith(("/scripts.dta", "/mpscripts.dta")),
    )
    overlay_loose_files(
        game, "Missions", ("",), entries,
        lambda name: name.endswith(("/scripts.dta", "/mpscripts.dta")),
    )
    result: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    for name, item in entries.items():
        parts = name.split("/")
        if len(parts) == 3:
            result[parts[1]][parts[2]] = item
    return dict(result)


def mission_scripts(game: Path) -> dict[str, dict[str, dict[str, object]]]:
    entries = effective_archive_entries(
        game,
        SCRIPT_ARCHIVES,
        lambda name: name.startswith("scripts/") and name.endswith(".scr"),
    )
    overlay_loose_files(game, "Scripts", (".scr",), entries)
    result: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    for name, item in entries.items():
        parts = name.split("/")
        if len(parts) == 3:
            result[parts[1]][parts[2]] = item
    return dict(result)


def used_scripts(assets: dict, scripts: dict) -> dict[str, object]:
    bindings = []
    registries = []
    malformed = []
    for registry_name in ("scripts.dta", "mpscripts.dta"):
        item = assets.get(registry_name)
        if not item:
            continue
        registries.append(registry_name)
        try:
            bindings.extend(parse_bindings(item["data"]))
        except ValueError as error:
            malformed.append(f"{registry_name}: {error}")

    roots = {
        normalize_script_name(script)
        for _, script in bindings if script.strip()
    }
    used = set(roots)
    pending = list(roots)
    missing = set()
    while pending:
        current = pending.pop()
        item = scripts.get(current)
        if item is None:
            missing.add(current)
            continue
        text = item["data"].decode("cp1252", errors="replace")
        for dependency in INCLUDE_RE.findall(text) + ASSIGN_RE.findall(text):
            target = normalize_script_name(dependency)
            if target and target not in used:
                used.add(target)
                pending.append(target)

    objective_scripts = []
    for name in sorted(used & set(scripts)):
        active, _ = split_comments(
            scripts[name]["data"].decode("cp1252", errors="replace")
        )
        if OBJECTIVE_RE.search(active):
            objective_scripts.append(name)
    return {
        "registries": registries,
        "malformed_registries": malformed,
        "binding_count": len(bindings),
        "root_script_count": len(roots),
        "available_root_script_count": len(roots & set(scripts)),
        "used_script_count": len(used),
        "missing_bound_scripts": sorted(missing & roots),
        "missing_dependencies": sorted(missing - roots),
        "missing_scripts": sorted(missing),
        "objective_scripts": objective_scripts,
    }


def runtime_results(path: Path | None) -> dict[str, dict[str, object]]:
    if path is None or not path.is_file():
        return {}
    decoded = json.loads(path.read_text(encoding="utf-8"))
    if decoded.get("schema_version") != 1:
        raise ValueError("Unsupported runtime-results schema")
    result = {}
    for row in decoded.get("missions", []):
        directory = normalized(str(row.get("directory", "")))
        if directory:
            result[directory] = row
    return result


def runtime_passed(row: dict[str, object] | None) -> bool:
    return bool(row) and all(row.get(check) is True for check in RUNTIME_CHECKS)


def assess(
    directory: str,
    map_row: dict | None,
    solo: dict[str, dict],
    assets_by_mission: dict,
    scripts_by_mission: dict,
    runtime_by_mission: dict,
) -> dict[str, object]:
    assets = assets_by_mission.get(directory, {})
    scripts = scripts_by_mission.get(directory, {})
    controller = used_scripts(assets, scripts)
    sizes = {name: int(item["size"]) for name, item in assets.items()}
    core_sizes = {name: sizes.get(name, 0) for name in CORE_FILES}
    complete_core = all(
        core_sizes[name] >= minimum
        for name, minimum in CORE_MINIMUM_SIZES.items()
    )
    mission_files = {
        name: sizes.get(name, 0) > 6 for name in MISSION_FILES
    }
    controller_ok = bool(
        controller["registries"]
        and controller["binding_count"]
        and not controller["malformed_registries"]
        and controller["available_root_script_count"]
    )
    objective_logic = bool(controller["objective_scripts"])
    static_ready = bool(
        complete_core
        and all(mission_files.values())
        and controller_ok
        and objective_logic
    )
    runtime = runtime_by_mission.get(directory)
    validation = runtime_passed(runtime)
    solo_entry = solo.get(directory)
    validated = bool(solo_entry and static_ready and validation)
    blockers = []
    if not solo_entry:
        blockers.append("not_in_singleplayer_catalogue")
    if not complete_core:
        blockers.append("incomplete_geometry")
    if not all(mission_files.values()):
        blockers.append("missing_singleplayer_mission_data")
    if not controller_ok:
        blockers.append("missing_or_broken_controller")
    if not objective_logic:
        blockers.append("no_bound_objective_logic")
    if not validation:
        blockers.append("runtime_validation_incomplete")
    return {
        "directory": directory,
        "map_names": map_row["names"] if map_row else [],
        "multiplayer_styles": map_row["styles"] if map_row else [],
        "multiplayer_objectives": map_row["declared_objectives"] if map_row else 0,
        "singleplayer_catalogued": bool(solo_entry),
        "singleplayer_catalogue": solo_entry,
        "complete_core": complete_core,
        "core_sizes": core_sizes,
        "mission_files": mission_files,
        "controller": controller,
        "static_ready": static_ready,
        "runtime": runtime,
        "runtime_passed": validation,
        "validated_singleplayer": validated,
        "blockers": blockers,
    }


def build(game: Path, runtime_path: Path | None) -> dict[str, object]:
    commercial_data, commercial_source = effective_commercial_maplist(game)
    commercial = parse_maplist(commercial_data, commercial_source)
    installed_path = game / "mpmaplist.txt"
    installed = (
        parse_maplist(installed_path.read_bytes(), "loose mpmaplist.txt")
        if installed_path.is_file() else commercial
    )
    solo, catalogues = singleplayer_catalogues(game)
    assets = mission_assets(game)
    scripts = mission_scripts(game)
    runtime = runtime_results(runtime_path)

    original_solo = {
        directory: assess(directory, None, solo, assets, scripts, runtime)
        for directory in sorted(solo)
        if solo[directory]["source"].lower().endswith(
            ("gamedata00.gdt", "gamedata01.gdt")
        )
    }
    multiplayer = {
        directory: assess(
            directory, installed.get(directory) or commercial.get(directory),
            solo, assets, scripts, runtime,
        )
        for directory in sorted(set(installed) | set(commercial) | set(PROTOTYPES))
    }
    for directory, row in multiplayer.items():
        row["commercial_multiplayer"] = directory in commercial
        row["installed_multiplayer"] = directory in installed
        row["official_prototype"] = directory in PROTOTYPES
    validated = [
        row for row in multiplayer.values() if row["validated_singleplayer"]
    ]
    static_candidates = [
        row for row in multiplayer.values() if row["static_ready"]
    ]
    commercial_static_candidates = [
        row for row in static_candidates if row["commercial_multiplayer"]
    ]
    community_static_candidates = [
        row for row in static_candidates if not row["commercial_multiplayer"]
    ]
    prototypes = {
        name: multiplayer[name] for name in PROTOTYPES if name in multiplayer
    }
    return {
        "game": str(game),
        "scope": {
            "commercial_singleplayer_missions": len(original_solo),
            "commercial_multiplayer_directories": len(commercial),
            "installed_multiplayer_directories": len(installed),
            "catalogues_read": len(catalogues),
            "static_multiplayer_to_solo_candidates": len(static_candidates),
            "commercial_static_candidates": len(commercial_static_candidates),
            "community_static_candidates": len(community_static_candidates),
            "validated_multiplayer_to_solo_conversions": len(validated),
        },
        "baseline": {
            "static_ready": sum(
                1 for row in original_solo.values() if row["static_ready"]
            ),
            "missions": original_solo,
        },
        "prototypes": prototypes,
        "multiplayer": multiplayer,
        "validated_conversions": [row["directory"] for row in validated],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--runtime-results", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument(
        "--require-proven", action="store_true",
        help="fail if an MP map is claimed as solo without every proof",
    )
    parser.add_argument(
        "--require-baseline", action="store_true",
        help="fail unless all 33 commercial solo missions pass the static gate",
    )
    arguments = parser.parse_args()
    report = build(arguments.game, arguments.runtime_results)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    prototype_summary = {
        name: {
            "static_ready": row["static_ready"],
            "singleplayer_catalogued": row["singleplayer_catalogued"],
            "validated_singleplayer": row["validated_singleplayer"],
            "blockers": row["blockers"],
        }
        for name, row in report["prototypes"].items()
    }
    print(json.dumps({
        "scope": report["scope"],
        "baseline_static_ready": report["baseline"]["static_ready"],
        "prototypes": prototype_summary,
        "validated_conversions": report["validated_conversions"],
    }, ensure_ascii=False))
    if arguments.require_proven:
        unproven_catalogued = [
            row for row in report["multiplayer"].values()
            if row["singleplayer_catalogued"]
            and not row["validated_singleplayer"]
        ]
        if unproven_catalogued:
            return 1
    if arguments.require_baseline and (
        report["scope"]["commercial_singleplayer_missions"] != 33
        or report["baseline"]["static_ready"] != 33
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
