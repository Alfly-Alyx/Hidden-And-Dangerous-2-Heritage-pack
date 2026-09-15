#!/usr/bin/env python3
"""Create, check and integrate H&D2 custom mission packages."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from custom_mission_packages import CATEGORY_ORDER, load_library, package_summary, read_package


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_ORIGINAL = Path(r"D:\Games\Hidden and Dangerous 2")
DEFAULT_TEST = Path(r"D:\Games\Hidden and Dangerous 2 - Test Menu Personnalise")


def command_new(arguments) -> int:
    library = arguments.library.resolve()
    package = library / arguments.id
    if package.exists():
        raise FileExistsError(f"Le paquet existe déjà : {package}")
    mission = package / "payload" / "Missions" / arguments.mission_directory
    mission.mkdir(parents=True)
    document = {
        "$schema": "../../mission.schema.json",
        "format": 1,
        "id": arguments.id,
        "category": arguments.category,
        "missionDirectory": arguments.mission_directory,
        "title": {
            "default": arguments.title,
            "french": arguments.title,
        },
        "objectives": [],
    }
    (package / "mission.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Paquet créé : {package}")
    print(f"Copiez maintenant les fichiers de la mission dans : {mission}")
    print("Le paquet restera refusé tant que tree.klz sera absent.")
    return 0


def command_check(arguments) -> int:
    source = arguments.source.resolve()
    packages = [read_package(source)] if (source / "mission.json").is_file() else load_library(source)
    summary = package_summary(packages)
    if arguments.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Bibliothèque valide : {summary['packages']} mission(s), "
              f"{summary['payload_files']} fichier(s).")
        for mission in summary["missions"]:
            print(
                f"- {mission['id']} | {mission['category']} | "
                f"Missions/{mission['directory']}"
            )
    return 0


def command_integrate(arguments) -> int:
    library = arguments.library.resolve()
    # Fail early with a short creator-facing error before the longer PE rebuild.
    command_check(argparse.Namespace(source=library, json=False))
    command = [
        sys.executable,
        str(PROJECT / "tools" / "build_static_custom_menu.py"),
        str(arguments.original_game.resolve()),
        str(arguments.test_game.resolve()),
        "--mission-library",
        str(library),
    ]
    if arguments.dry_run:
        command.append("--dry-run")
    completed = subprocess.run(command, cwd=PROJECT, check=False)
    if completed.returncode:
        return completed.returncode
    print("Préparation terminée. Le jeu n'a pas été lancé.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("new", help="crée le squelette d'un paquet")
    create.add_argument("library", type=Path)
    create.add_argument("id")
    create.add_argument("mission_directory")
    create.add_argument("title")
    create.add_argument("--category", choices=CATEGORY_ORDER, default="original-creation")
    create.set_defaults(action=command_new)

    check = commands.add_parser("check", help="vérifie un paquet ou une bibliothèque")
    check.add_argument("source", type=Path)
    check.add_argument("--json", action="store_true")
    check.set_defaults(action=command_check)

    integrate = commands.add_parser("integrate", help="prépare la copie de test")
    integrate.add_argument("library", type=Path)
    integrate.add_argument("--original-game", type=Path, default=DEFAULT_ORIGINAL)
    integrate.add_argument("--test-game", type=Path, default=DEFAULT_TEST)
    integrate.add_argument("--dry-run", action="store_true")
    integrate.set_defaults(action=command_integrate)

    arguments = parser.parse_args()
    try:
        return arguments.action(arguments)
    except (FileNotFoundError, FileExistsError, ValueError) as error:
        print(f"ERREUR : {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
