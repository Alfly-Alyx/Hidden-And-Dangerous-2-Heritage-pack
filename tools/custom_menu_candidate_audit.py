#!/usr/bin/env python3
"""Verify an installed H&D2 three-list custom-mission GUI without launching it."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ORIGINAL_EXECUTABLE_SHA256 = (
    "1EEBDE4710F800F712A05B1ECEE2BA862C144F478DF89B58E54C912E857EE78C"
)
EXPECTED_CATEGORIES = (
    "multiplayer-adaptation",
    "user-mission",
    "free-exploration",
)
REQUIRED_RUNTIME_FILES = {
    "GameData/Gamedata02.gdt",
    "GameData/Gamedata03.gdt",
    "GameData/Gamedata04.gdt",
    "GameData/Gamedata05.gdt",
    "Models/singleplayer.4ds",
    "Models/single mission 2.4ds",
    "Scripts/HD2.CustomMenu.asi",
}
REQUIRED_TEXT_IDS = {20402, 20410, 20411, 20412, 20413, 20499}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def safe_target(root: Path, relative: str) -> Path | None:
    if not relative or Path(relative).is_absolute():
        return None
    target = (root / Path(*relative.replace("\\", "/").split("/"))).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    return target


def text_table_state(test_game: Path) -> dict[str, object]:
    rows = []
    pattern = rb"(?m)^\s*(20402|20410|20411|20412|20413|20499)\s+\""
    for path in sorted(
        (test_game / "Text").glob("*/TEXTY_DD.txt"),
        key=lambda item: str(item).casefold(),
    ):
        found = {int(value) for value in re.findall(pattern, path.read_bytes())}
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


def package_state(library: Path) -> dict[str, object]:
    packages = []
    payload_files = 0
    if library.is_dir():
        for manifest in sorted(library.glob("*/mission.json")):
            if manifest.parent.name.startswith("_"):
                continue
            try:
                document = json.loads(manifest.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            payload = manifest.parent / "payload"
            files = sum(1 for path in payload.rglob("*") if path.is_file())
            payload_files += files
            packages.append({
                "id": document.get("id"),
                "category": document.get("category"),
                "mission_directory": document.get("missionDirectory"),
                "payload_files": files,
            })
    return {"packages": len(packages), "payload_files": payload_files, "items": packages}


def audit(original_game: Path, test_game: Path) -> dict[str, object]:
    errors: list[str] = []
    report_path = test_game / "CUSTOM_MISSIONS_INSTALL.json"
    managed_path = test_game / "STATIC_MENU_MANAGED_FILES.json"
    add_error(errors, report_path.is_file(), "CUSTOM_MISSIONS_INSTALL.json absent")
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
    add_error(errors, active_executable.is_file(), "exécutable de test absent")
    add_error(errors, original_executable.is_file(), "exécutable original absent")
    if active_executable.is_file():
        add_error(
            errors,
            sha256(active_executable) == ORIGINAL_EXECUTABLE_SHA256,
            "l'exécutable de test n'est pas le client commercial 1.12 attendu",
        )
    if original_executable.is_file():
        add_error(
            errors,
            sha256(original_executable) == ORIGINAL_EXECUTABLE_SHA256,
            "l'exécutable original n'est pas le client commercial 1.12 attendu",
        )

    add_error(
        errors,
        report.get("status")
        == "CUSTOM_MISSIONS_INSTALLED_THREE_LIST_GUI_GAME_NOT_LAUNCHED",
        "état d'installation du menu inattendu",
    )
    runtime = report.get("runtime_sha256")
    add_error(errors, isinstance(runtime, dict), "empreintes du runtime absentes")
    runtime = runtime if isinstance(runtime, dict) else {}
    add_error(
        errors,
        REQUIRED_RUNTIME_FILES.issubset(runtime),
        "un catalogue, une scène de menu ou le module ASI manque au rapport",
    )

    verified_runtime = 0
    for relative, expected in runtime.items():
        target = safe_target(test_game, relative)
        if target is None:
            errors.append(f"chemin runtime interdit : {relative}")
        elif not target.is_file():
            errors.append(f"fichier runtime absent : {relative}")
        elif sha256(target) != str(expected).upper():
            errors.append(f"empreinte runtime différente : {relative}")
        else:
            verified_runtime += 1

    text_tables = text_table_state(test_game)
    add_error(
        errors,
        text_tables["all_complete"],
        "les six libellés du menu ne sont pas présents dans les huit langues",
    )

    files = managed.get("files") if isinstance(managed, dict) else None
    add_error(
        errors,
        managed.get("format") == 1 and isinstance(files, list),
        "le manifeste des fichiers gérés est invalide",
    )
    managed_hashes = {
        item.get("relative"): str(item.get("sha256", "")).upper()
        for item in (files or [])
        if isinstance(item, dict)
    }
    for relative, expected in runtime.items():
        add_error(
            errors,
            managed_hashes.get(relative) == str(expected).upper(),
            f"le runtime n'est pas suivi correctement : {relative}",
        )

    library_value = report.get("library")
    library = (
        Path(library_value)
        if isinstance(library_value, str)
        else test_game / "CustomMissions"
    )
    packages = package_state(library)
    add_error(
        errors,
        packages["packages"] == report.get("missions"),
        "le nombre de paquets ne correspond plus au rapport",
    )
    add_error(
        errors,
        packages["payload_files"] == report.get("payload_files"),
        "le nombre de fichiers de mission ne correspond plus au rapport",
    )
    categories = sorted({item["category"] for item in packages["items"]})
    unexpected = sorted(set(categories).difference(EXPECTED_CATEGORIES))
    add_error(
        errors,
        not unexpected,
        "catégories de paquet inattendues : " + ", ".join(unexpected),
    )

    return {
        "ok": not errors,
        "static_candidate_ready": not errors,
        "visual_runtime_validated": False,
        "errors": errors,
        "original_game": str(original_game),
        "test_game": str(test_game),
        "categories": categories,
        "custom_packages": packages,
        "runtime_files": len(runtime),
        "verified_runtime_files": verified_runtime,
        "text_tables": text_tables,
        "note": (
            "A green result proves installed-file integrity and routing metadata only. "
            "The button, three lists and Back routes still require an in-game visual check."
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
