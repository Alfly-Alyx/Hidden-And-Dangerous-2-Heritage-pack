#!/usr/bin/env python3
"""Verify a static H&D2 custom-menu test candidate without launching the game."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ORIGINAL_EXECUTABLE_SHA256 = (
    "1EEBDE4710F800F712A05B1ECEE2BA862C144F478DF89B58E54C912E857EE78C"
)
EXPECTED_CATEGORIES = [
    "multiplayer-adaptation",
    "user-mission",
    "free-exploration",
]
EXPECTED_TECHNICAL_SLOTS = ["Brest", "Libye1", "Sicily1"]
REQUIRED_TEXT_IDS = {20402, 20410, 20411, 20412, 20420, 20421, 20422}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def text_table_state(test_game: Path) -> dict[str, object]:
    rows = []
    for path in sorted(
        (test_game / "Text").glob("*/TEXTY_DD.txt"),
        key=lambda item: str(item).casefold(),
    ):
        data = path.read_bytes()
        found = {
            int(value)
            for value in re.findall(
                rb"(?m)^\s*(20402|20410|20411|20412|20420|20421|20422)\s+\"",
                data,
            )
        }
        rows.append({
            "language": path.parent.name,
            "path": str(path),
            "ids": sorted(found),
            "complete": found == REQUIRED_TEXT_IDS,
        })
    return {
        "count": len(rows),
        "all_complete": len(rows) == 8 and all(row["complete"] for row in rows),
        "tables": rows,
    }


def audit(original_game: Path, test_game: Path) -> dict[str, object]:
    errors: list[str] = []
    report_path = test_game / "STATIC_MENU_PATCH.json"
    managed_path = test_game / "STATIC_MENU_MANAGED_FILES.json"
    add_error(errors, report_path.is_file(), "STATIC_MENU_PATCH.json absent")
    add_error(errors, managed_path.is_file(), "manifeste des fichiers gérés absent")
    if errors:
        return {"ok": False, "errors": errors}

    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
        managed = json.loads(managed_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        return {"ok": False, "errors": [str(error)]}

    active_executable = test_game / "HD2_SabreSquadron.exe"
    original_executable = original_game / "HD2_SabreSquadron.exe"
    backup_executable = test_game / "HD2_SabreSquadron.original.exe"
    menu_path = test_game / "Models" / "singleplayer.4ds"
    catalogues = {
        name: test_game / "GameData" / name
        for name in (
            "Gamedata02.gdt",
            "Gamedata03.gdt",
            "Gamedata04.gdt",
            "Gamedata05.gdt",
        )
    }
    required_files = {
        "active executable": active_executable,
        "original executable": original_executable,
        "backup executable": backup_executable,
        "menu": menu_path,
        "restore script": test_game / "RestaurerMenuTest.ps1",
        "launch shortcut": test_game / "Lancer Hidden and Dangerous 2.lnk",
        **{name: path for name, path in catalogues.items()},
    }
    missing = [label for label, path in required_files.items() if not path.is_file()]
    if missing:
        errors.append("fichiers absents : " + ", ".join(missing))

    add_error(
        errors,
        str(Path(report.get("target", "")).resolve()).casefold()
        == str(test_game.resolve()).casefold(),
        "le rapport vise un autre dossier de test",
    )
    add_error(
        errors,
        report.get("catalogue_sections") == EXPECTED_CATEGORIES,
        "les trois catégories attendues ne sont pas déclarées dans l'ordre",
    )
    add_error(
        errors,
        report.get("custom_action") == "OPEN_GROUPED_CUSTOM_MISSION_BROWSER",
        "l'action du bouton custom est inattendue",
    )
    add_error(
        errors,
        report.get("custom_list_scope")
        == "GAMEDATA02_CATEGORIES_AND_GAMEDATA03_TO_05_DETAILS",
        "la portée des quatre catalogues custom est inattendue",
    )
    add_error(
        errors,
        report.get("native_single_mission_scope") == "OFFICIAL_CATALOGUES",
        "les catalogues solo officiels ne sont plus explicitement isolés",
    )
    add_error(
        errors,
        report.get("text_tables") == 8,
        "le rapport ne déclare pas huit tables de langue",
    )
    add_error(
        errors,
        report.get("original_sha256") == ORIGINAL_EXECUTABLE_SHA256,
        "l'empreinte commerciale déclarée est inattendue",
    )
    if report.get("mission_library") is None:
        add_error(
            errors,
            report.get("technical_slots") == EXPECTED_TECHNICAL_SLOTS,
            "les trois emplacements techniques de validation sont inattendus",
        )

    hashes: dict[str, str | None] = {}
    if not missing:
        hashes = {
            label: sha256(path)
            for label, path in required_files.items()
            if path.suffix.casefold() != ".lnk"
        }
        add_error(
            errors,
            hashes["original executable"] == ORIGINAL_EXECUTABLE_SHA256,
            "l'exécutable du jeu original a changé",
        )
        add_error(
            errors,
            hashes["backup executable"] == ORIGINAL_EXECUTABLE_SHA256,
            "la sauvegarde commerciale de la copie de test a changé",
        )
        add_error(
            errors,
            hashes["active executable"] == report.get("sha256"),
            "l'exécutable de test ne correspond plus au rapport",
        )
        add_error(
            errors,
            hashes["menu"] == report.get("menu_sha256"),
            "le menu de test ne correspond plus au rapport",
        )
        expected_catalogues = report.get("catalogue_sha256", {})
        for name in catalogues:
            add_error(
                errors,
                hashes[name] == expected_catalogues.get(name),
                f"{name} ne correspond plus au rapport",
            )

    text_tables = text_table_state(test_game)
    add_error(
        errors,
        text_tables["all_complete"],
        "les sept libellés custom ne sont pas présents dans les huit langues",
    )
    add_error(
        errors,
        managed.get("format") == 1 and isinstance(managed.get("files"), list),
        "le manifeste des fichiers gérés est invalide",
    )
    return {
        "ok": not errors,
        "static_candidate_ready": not errors,
        "visual_runtime_validated": False,
        "errors": errors,
        "original_game": str(original_game),
        "test_game": str(test_game),
        "categories": report.get("catalogue_sections"),
        "custom_packages": report.get("custom_packages"),
        "hashes": hashes,
        "text_tables": text_tables,
        "note": (
            "A green result proves file integrity and routing metadata only. "
            "The three screens must still be opened and checked in the game."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_game", type=Path)
    parser.add_argument("test_game", type=Path)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.original_game.resolve(), arguments.test_game.resolve())
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    print(encoded)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(encoded + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
