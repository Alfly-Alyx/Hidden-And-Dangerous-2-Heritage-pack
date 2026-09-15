#!/usr/bin/env python3
"""Inventory commercial H&D2 mission directories and multiplayer declarations."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from dta_archive import DtaArchive

MISSION_ARCHIVES = ("missions.dta", "Patch.dta", "SabreSquadron.dta")
MAPLIST_ARCHIVES = ("others.DTA", "Patch.dta", "SabreSquadron.dta")
CORE = ("map.4ds", "tree.klz", "scene.4ds", "loader.4ds")
INTERESTING = re.compile(r"(_mp|_obj|_zone|castle|england|london|proto|test)", re.I)


def norm(value: str) -> str:
    return value.replace("\\", "/").lower()


def effective_entries(game: Path):
    result = {}
    for archive_name in MISSION_ARCHIVES:
        with DtaArchive(game / archive_name) as archive:
            for entry in archive.entries:
                name = norm(entry.name)
                if name.startswith("missions/"):
                    result[name] = {"archive": archive_name, "size": entry.size, "name": entry.name}
    return result


def commercial_maplist(game: Path):
    selected = None
    source = None
    for archive_name in MAPLIST_ARCHIVES:
        with DtaArchive(game / archive_name) as archive:
            for entry in archive.entries:
                if norm(entry.name) == "gamedata/mpmaplist.txt":
                    selected = archive.read(entry)
                    source = archive_name
    if selected is None:
        raise ValueError("Commercial multiplayer map list not found")
    return selected.decode("cp1252", errors="replace"), source


def audit(game: Path):
    entries = effective_entries(game)
    grouped = defaultdict(dict)
    for name, item in entries.items():
        parts = name.split("/")
        if len(parts) < 3:
            continue
        tail = "/".join(parts[2:])
        if "/" not in tail:
            grouped[parts[1]][tail] = item
    maplist, maplist_source = commercial_maplist(game)
    listed_dirs = {match.group(1).lower() for match in re.finditer(r'\bdir\s*=\s*"([^"]+)"', maplist, re.I)}
    rows = []
    for directory, files in sorted(grouped.items()):
        sizes = {name: item["size"] for name, item in files.items()}
        complete_core = all(sizes.get(name, 0) > 1000 for name in CORE)
        rows.append({
            "directory": directory,
            "listed_multiplayer": directory in listed_dirs,
            "interesting_name": bool(INTERESTING.search(directory)),
            "direct_file_count": len(files),
            "complete_core": complete_core,
            "has_volumes": sizes.get("volumy.bin", 0) > 1000,
            "has_registry": sizes.get("scripts.dta", 0) > 6 or sizes.get("mpscripts.dta", 0) > 6,
            "has_actors": sizes.get("actors.bin", 0) > 6,
            "core_sizes": {name: sizes.get(name) for name in CORE + ("volumy.bin",)},
            "files": sorted(sizes),
        })
    return {"game": str(game), "maplist_source": maplist_source,
            "commercial_multiplayer_directories": len(listed_dirs),
            "mission_directories": len(rows), "directories": rows}


def markdown(report):
    candidates = [row for row in report["directories"] if row["interesting_name"] and not row["listed_multiplayer"]]
    lines = ["# Inventaire des cartes et variantes multijoueurs", "",
        "Inventaire dérivé des archives commerciales. Une variante non déclarée ne devient jouable qu'après validation de sa géométrie, de ses collisions, de ses points d'apparition et de son mode de jeu.", "",
        "## Couverture", "", f"- {report['mission_directories']} dossiers de mission ;",
        f"- {report['commercial_multiplayer_directories']} dossiers déclarés dans la liste multijoueur commerciale ;",
        f"- {len(candidates)} dossiers non déclarés dont le nom suggère une variante, un objectif ou un prototype.", "",
        "## Dossiers à examiner", "",
        "| Dossier | Coeur géométrique complet | Volumes | Registre | Acteurs | Fichiers directs |",
        "|---|---|---|---|---|---:|"]
    for row in candidates:
        yes = lambda value: "oui" if value else "non"
        lines.append(f"| {row['directory']} | {yes(row['complete_core'])} | {yes(row['has_volumes'])} | {yes(row['has_registry'])} | {yes(row['has_actors'])} | {row['direct_file_count']} |")
    lines += ["", "Les dossiers de scripts seuls sont conservés pour la phase finale de reconstruction ; ils ne sont pas ajoutés comme cartes vides ou cassées.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.game)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(markdown(report), encoding="utf-8")
    interesting = [row for row in report["directories"] if row["interesting_name"] and not row["listed_multiplayer"]]
    print(json.dumps({"mission_directories": report["mission_directories"], "commercial_multiplayer_directories": report["commercial_multiplayer_directories"], "unlisted_interesting": len(interesting)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())