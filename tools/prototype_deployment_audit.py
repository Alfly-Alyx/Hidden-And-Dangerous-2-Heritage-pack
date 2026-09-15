#!/usr/bin/env python3
"""Audit the two official prototype completion plans and loose deployment.

The archive plan is verified independently from the installer.  The installed
state is reported separately because an older pack can have a valid map-list
entry while still exposing only the incomplete commercial placeholder files.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from dta_archive import DtaArchive
from tree_klz import audit_bytes

AFRICA_FILES = (
    "map.4ds", "tree.klz", "scene.4ds", "items.dat", "check2.bin",
    "scene2.bin", "loader.4ds", "actors.bin", "sounds.bin", "volumy.bin",
    "vertanim.bin", "car_table.dat", "mpscripts.dta",
)
NORMANDY_FILES = (
    "map.4ds", "tree.klz", "scene.4ds", "items.dat", "check2.bin",
    "scene2.bin", "loader.4ds", "actors.bin", "sounds.bin", "volumy.bin",
    "effects.bin", "watercam.set", "car_table.dat", "meshplayer.bin",
)
NORMANDY_COMPLEMENTS = (
    "map.4ds", "tree.klz", "scene.4ds", "loader.4ds", "volumy.bin",
)
AFRICA_SCRIPTS = tuple(
    f"af5_mp_cisterna{number}.scr" for number in range(1, 8)
)
EXPECTED_BINDINGS = {
    "normandy3_mp_zone": (
        "teamplay", "PROTOTYPE - Normandy3 Zone (exploration libre)"
    ),
    "afrika5_mp": (
        "deathmatch", "PROTOTYPE - Africa5 (exploration libre)"
    ),
}


def normalized(value: str) -> str:
    return value.replace("\\", "/").casefold()


def direct_entries(archive: DtaArchive, prefix: str):
    prefix = normalized(prefix).rstrip("/") + "/"
    result = {}
    for entry in archive.entries:
        name = normalized(entry.name)
        if not name.startswith(prefix):
            continue
        tail = name[len(prefix):]
        if tail and "/" not in tail:
            result[tail] = {"size": entry.size, "source": entry.name}
    return result


def archive_plan(game: Path):
    errors: list[str] = []
    with DtaArchive(game / "missions.dta") as archive:
        africa_source = direct_entries(archive, "Missions/Africa5_MP")
        africa_own = direct_entries(archive, "Missions/AFRIKA5_MP")
        normandy_source = direct_entries(archive, "Missions/NORMANDY3_MP")
        normandy_own = direct_entries(archive, "Missions/NORMANDY3_MP_ZONE")
    with DtaArchive(game / "Scripts.dta") as archive:
        africa_scripts = direct_entries(archive, "Scripts/AFRICA5_MP")

    africa_missing = sorted(set(africa_source) - set(africa_own))
    africa_complete = set(africa_own) | {
        name for name in africa_missing if name in africa_source
    }
    normandy_complements = []
    for name in NORMANDY_COMPLEMENTS:
        own = normandy_own.get(name)
        if own is None or own["size"] <= 19:
            normandy_complements.append(name)
    normandy_complete = set(normandy_own) | set(normandy_complements)

    if set(africa_source) != set(AFRICA_FILES):
        errors.append("Africa5_MP commercial ne contient pas exactement les 13 bases attendues")
    if len(africa_own) != 7 or len(africa_missing) != 6:
        errors.append("AFRIKA5_MP n'est plus le vestige attendu de 7 fichiers + 6 bases")
    if africa_complete != set(AFRICA_FILES):
        errors.append("le plan Africa5 ne produit pas les 13 fichiers autonomes")
    if set(africa_scripts) != set(AFRICA_SCRIPTS):
        errors.append("les sept scripts de citernes Africa5 ne sont pas tous récupérables")
    if set(normandy_source) != set(NORMANDY_FILES):
        errors.append("NORMANDY3_MP commercial ne contient pas exactement les 14 bases attendues")
    if len(normandy_own) != 13 or normandy_complements != list(NORMANDY_COMPLEMENTS):
        errors.append("Normandy3 Zone n'exige pas exactement les cinq compléments attendus")
    if normandy_complete != set(NORMANDY_FILES):
        errors.append("le plan Normandy3 Zone ne produit pas les 14 fichiers autonomes")

    return {
        "ok": not errors,
        "errors": errors,
        "africa": {
            "source_files": len(africa_source),
            "own_files": len(africa_own),
            "copied_bases": africa_missing,
            "completed_files": len(africa_complete),
            "recoverable_scripts": len(africa_scripts),
        },
        "normandy": {
            "source_files": len(normandy_source),
            "own_files": len(normandy_own),
            "copied_bases": normandy_complements,
            "completed_files": len(normandy_complete),
        },
    }


def loose_files(folder: Path):
    if not folder.is_dir():
        return {}
    return {
        child.name.casefold(): child.stat().st_size
        for child in folder.iterdir() if child.is_file()
    }


def map_bindings(path: Path):
    if not path.is_file():
        return {}
    text = path.read_text(encoding="cp1252", errors="replace")
    result = {}
    for section in re.finditer(
        r'<GAMESTYLE\s+type="([^"]+)"[\s\S]*?</GAMESTYLE>', text, re.I
    ):
        style = section.group(1).casefold()
        for item in re.finditer(
            r'<MAP\s+name="([^"]*)"\s+dir="([^"]+)"[\s\S]*?</MAP>',
            section.group(0), re.I,
        ):
            result[item.group(2).casefold()] = {
                "style": style,
                "name": item.group(1),
            }
    return result


def tree_status(path: Path):
    if not path.is_file():
        return {"valid": False, "error": "absent"}
    try:
        audit = audit_bytes(path.read_bytes(), str(path))
        return {
            "valid": True,
            "records": audit.records,
            "warning_flags": audit.warning_flags,
            "failure_flags": audit.failure_flags,
            "both_flags": audit.both_flags,
            "boundary_labels": audit.boundary_labels,
            "clean": not (
                audit.warning_flags or audit.failure_flags or audit.both_flags
                or audit.boundary_labels
            ),
        }
    except (OSError, ValueError) as exc:
        return {"valid": False, "error": str(exc)}


def installed_state(game: Path):
    missions = game / "Missions"
    scripts = game / "Scripts"
    africa = loose_files(missions / "AFRIKA5_MP")
    normandy = loose_files(missions / "NORMANDY3_MP_ZONE")
    africa_scripts = loose_files(scripts / "AFRIKA5_MP")
    bindings = map_bindings(game / "mpmaplist.txt")

    africa_missing = sorted(set(AFRICA_FILES) - set(africa))
    normandy_missing = sorted(set(NORMANDY_FILES) - set(normandy))
    script_missing = sorted(set(AFRICA_SCRIPTS) - set(africa_scripts))
    normandy_base_sizes_ok = all((
        normandy.get("map.4ds", 0) > 1000,
        normandy.get("tree.klz", 0) > 1_000_000,
        normandy.get("scene.4ds", 0) > 1_000_000,
        normandy.get("loader.4ds", 0) > 1000,
        normandy.get("volumy.bin", 0) > 100_000,
    ))
    tree_reports = {
        "africa": tree_status(missions / "AFRIKA5_MP" / "tree.klz"),
        "normandy": tree_status(missions / "NORMANDY3_MP_ZONE" / "tree.klz"),
    }

    binding_reports = {}
    bindings_ok = True
    for directory, (expected_style, expected_name) in EXPECTED_BINDINGS.items():
        actual = bindings.get(directory)
        ok = bool(
            actual and actual["style"] == expected_style
            and actual["name"].casefold() == expected_name.casefold()
        )
        bindings_ok &= ok
        binding_reports[directory] = {
            "expected_style": expected_style,
            "expected_name": expected_name,
            "actual": actual,
            "ok": ok,
        }

    africa_ready = not africa_missing and not script_missing
    normandy_ready = not normandy_missing and normandy_base_sizes_ok
    exploration_clean = all(
        report.get("valid") and report.get("clean")
        for report in tree_reports.values()
    )
    return {
        "ready": africa_ready and normandy_ready and bindings_ok and exploration_clean,
        "africa": {
            "files_present": len(set(AFRICA_FILES) & set(africa)),
            "files_expected": len(AFRICA_FILES),
            "missing": africa_missing,
            "scripts_present": len(set(AFRICA_SCRIPTS) & set(africa_scripts)),
            "scripts_expected": len(AFRICA_SCRIPTS),
            "scripts_missing": script_missing,
            "ready": africa_ready,
        },
        "normandy": {
            "files_present": len(set(NORMANDY_FILES) & set(normandy)),
            "files_expected": len(NORMANDY_FILES),
            "missing": normandy_missing,
            "base_sizes_ok": normandy_base_sizes_ok,
            "ready": normandy_ready,
        },
        "bindings": binding_reports,
        "exploration_clean": exploration_clean,
        "trees": tree_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument(
        "--require-installed", action="store_true",
        help="fail unless both loose prototype folders are complete and clean",
    )
    args = parser.parse_args()

    report = {
        "game": str(args.game),
        "archive_plan": archive_plan(args.game),
        "installed": installed_state(args.game),
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({
        "archive_plan_ok": report["archive_plan"]["ok"],
        "installed_ready": report["installed"]["ready"],
        "africa_installed": (
            f"{report['installed']['africa']['files_present']}/"
            f"{report['installed']['africa']['files_expected']}"
        ),
        "normandy_installed": (
            f"{report['installed']['normandy']['files_present']}/"
            f"{report['installed']['normandy']['files_expected']}"
        ),
        "exploration_clean": report["installed"]["exploration_clean"],
    }, ensure_ascii=False))
    if not report["archive_plan"]["ok"]:
        return 1
    if args.require_installed and not report["installed"]["ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
