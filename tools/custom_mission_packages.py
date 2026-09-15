#!/usr/bin/env python3
"""Read and validate creator-friendly H&D2 custom mission packages."""
from __future__ import annotations

import json
import re
import zlib
from pathlib import Path


FORMAT_VERSION = 1
CATEGORIES = {
    "multiplayer-adaptation": 20410,
    "original-creation": 20411,
    "free-exploration": 20412,
}
CATEGORY_ORDER = tuple(CATEGORIES)
ALLOWED_PAYLOAD_ROOTS = {
    "maps", "missions", "models", "scripts", "sounds", "tables", "text"
}
PACKAGE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
MISSION_DIRECTORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}$")
TRANSLATION_KEYS = {
    "default", "czech", "english", "englishus", "french", "german",
    "italian", "japan", "spanish",
}
MAX_OBJECTIVES = 31


def _object(value, label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} doit être un objet JSON")
    return value


def _string(value, label: str, maximum: int = 180) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} doit contenir du texte")
    result = value.strip()
    if len(result) > maximum or any(ord(char) < 32 for char in result):
        raise ValueError(f"{label} est trop long ou contient un caractère interdit")
    return result


def _translations(value, label: str) -> dict[str, str]:
    if isinstance(value, str):
        return {"default": _string(value, label)}
    source = _object(value, label)
    unknown = sorted(set(key.casefold() for key in source) - TRANSLATION_KEYS)
    if unknown:
        raise ValueError(f"{label} contient des langues inconnues : {', '.join(unknown)}")
    result = {
        key.casefold(): _string(text, f"{label}.{key}")
        for key, text in source.items()
    }
    if "default" not in result and "english" not in result:
        raise ValueError(f"{label} doit contenir au minimum 'default' ou 'english'")
    return result


def translated(values: dict[str, str], language: str) -> str:
    key = language.casefold()
    if key in values:
        return values[key]
    if key == "englishus" and "english" in values:
        return values["english"]
    if key == "english" and "englishus" in values:
        return values["englishus"]
    return values.get("default") or values.get("english") or values["englishus"]


def _allocated_ids(package_id: str, objective_count: int) -> tuple[int, list[int]]:
    # Every package owns a deterministic block of 32 IDs. Adding another package
    # therefore never changes the IDs already used by a creator.
    base = 1_000_000 + (zlib.crc32(package_id.encode("ascii")) % 20_000_000) * 32
    return base, [base + index + 1 for index in range(objective_count)]


def _safe_payload_files(package_dir: Path, mission_directory: str, catalogue_only: bool):
    payload = package_dir / "payload"
    if not payload.exists():
        if catalogue_only:
            return []
        raise ValueError(f"{package_dir.name}: dossier payload absent")
    if not payload.is_dir() or payload.is_symlink():
        raise ValueError(f"{package_dir.name}: payload doit être un dossier normal")
    files = []
    mission_prefix = f"missions/{mission_directory.casefold()}/"
    has_mission = False
    has_tree = False
    for path in sorted(payload.rglob("*"), key=lambda item: str(item).casefold()):
        if path.is_symlink():
            raise ValueError(f"{package_dir.name}: lien symbolique interdit : {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(payload)
        parts = relative.parts
        if not parts or parts[0].casefold() not in ALLOWED_PAYLOAD_ROOTS:
            raise ValueError(
                f"{package_dir.name}: racine de fichier interdite : {relative}"
            )
        if any(part in ("", ".", "..") or ":" in part for part in parts):
            raise ValueError(f"{package_dir.name}: chemin non sûr : {relative}")
        normalized = relative.as_posix().casefold()
        has_mission = has_mission or normalized.startswith(mission_prefix)
        has_tree = has_tree or normalized == mission_prefix + "tree.klz"
        files.append({"source": path, "relative": relative})
    if not catalogue_only and not has_mission:
        raise ValueError(
            f"{package_dir.name}: aucun fichier dans payload/Missions/{mission_directory}"
        )
    if not catalogue_only and not has_tree:
        raise ValueError(
            f"{package_dir.name}: payload/Missions/{mission_directory}/tree.klz absent"
        )
    return files


def read_package(package_dir: Path) -> dict:
    manifest_path = package_dir / "mission.json"
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{manifest_path}: JSON invalide ({error})") from error
    document = _object(document, str(manifest_path))
    if document.get("format") != FORMAT_VERSION:
        raise ValueError(f"{package_dir.name}: format doit valoir {FORMAT_VERSION}")
    package_id = _string(document.get("id"), f"{package_dir.name}.id", 64).casefold()
    if not PACKAGE_ID_RE.fullmatch(package_id):
        raise ValueError(
            f"{package_dir.name}: id invalide (minuscules, chiffres, '.', '_' ou '-')"
        )
    category = _string(document.get("category"), f"{package_dir.name}.category")
    if category not in CATEGORIES:
        raise ValueError(
            f"{package_dir.name}: catégorie inconnue; utilisez {', '.join(CATEGORY_ORDER)}"
        )
    mission_directory = _string(
        document.get("missionDirectory"), f"{package_dir.name}.missionDirectory", 64
    )
    if not MISSION_DIRECTORY_RE.fullmatch(mission_directory):
        raise ValueError(f"{package_dir.name}: missionDirectory invalide")
    loading_screen = document.get("loadingScreen")
    if loading_screen is not None:
        loading_screen = _string(
            loading_screen, f"{package_dir.name}.loadingScreen", 96
        )
        if not MISSION_DIRECTORY_RE.fullmatch(loading_screen):
            raise ValueError(f"{package_dir.name}: loadingScreen invalide")
    template_mission = document.get("templateMission")
    if template_mission is not None:
        template_mission = _string(
            template_mission, f"{package_dir.name}.templateMission", 64
        )
        if not MISSION_DIRECTORY_RE.fullmatch(template_mission):
            raise ValueError(f"{package_dir.name}: templateMission invalide")
    title = _translations(document.get("title"), f"{package_dir.name}.title")
    raw_objectives = document.get("objectives", [])
    if not isinstance(raw_objectives, list) or len(raw_objectives) > MAX_OBJECTIVES:
        raise ValueError(
            f"{package_dir.name}: objectives doit être une liste de 0 à {MAX_OBJECTIVES} textes"
        )
    objectives = [
        _translations(value, f"{package_dir.name}.objectives[{index}]")
        for index, value in enumerate(raw_objectives)
    ]
    catalogue_only = document.get("catalogueOnly", False)
    if not isinstance(catalogue_only, bool):
        raise ValueError(f"{package_dir.name}: catalogueOnly doit être true ou false")
    title_id, objective_ids = _allocated_ids(package_id, len(objectives))
    files = _safe_payload_files(package_dir, mission_directory, catalogue_only)
    return {
        "id": package_id,
        "category": category,
        "mission_directory": mission_directory,
        "loading_screen": loading_screen,
        "template_mission": template_mission,
        "title": title,
        "title_id": title_id,
        "objectives": objectives,
        "objective_ids": objective_ids,
        "catalogue_only": catalogue_only,
        "package_dir": package_dir,
        "files": files,
    }


def load_library(library: Path) -> list[dict]:
    if not library.is_dir():
        raise FileNotFoundError(f"Bibliothèque de missions introuvable : {library}")
    package_dirs = sorted(
        (
            path for path in library.iterdir()
            if path.is_dir() and not path.name.startswith("_")
            and (path / "mission.json").is_file()
        ),
        key=lambda path: path.name.casefold(),
    )
    packages = [read_package(path) for path in package_dirs]
    ids: dict[str, str] = {}
    directories: dict[str, str] = {}
    text_ids: dict[int, str] = {}
    payload_paths: dict[str, str] = {}
    for package in packages:
        if package["id"] in ids:
            raise ValueError(
                f"Identifiant dupliqué : {package['id']} ({ids[package['id']]})"
            )
        ids[package["id"]] = package["package_dir"].name
        directory_key = package["mission_directory"].casefold()
        if directory_key in directories:
            raise ValueError(
                f"Dossier de mission dupliqué : {package['mission_directory']}"
            )
        directories[directory_key] = package["id"]
        for text_id in [package["title_id"], *package["objective_ids"]]:
            if text_id in text_ids:
                raise ValueError(
                    f"Collision d'identifiants internes : {package['id']} et {text_ids[text_id]}"
                )
            text_ids[text_id] = package["id"]
        for item in package["files"]:
            key = item["relative"].as_posix().casefold()
            if key in payload_paths:
                raise ValueError(
                    f"Fichier fourni par deux paquets : {item['relative']}"
                )
            payload_paths[key] = package["id"]
    return packages


def localized_values(packages: list[dict], language: str) -> dict[int, str]:
    values: dict[int, str] = {}
    for package in packages:
        values[package["title_id"]] = translated(package["title"], language)
        for text_id, objective in zip(
            package["objective_ids"], package["objectives"]
        ):
            values[text_id] = translated(objective, language)
    return values


def package_summary(packages: list[dict]) -> dict:
    return {
        "packages": len(packages),
        "missions": [
            {
                "id": item["id"],
                "category": item["category"],
                "directory": item["mission_directory"],
                "title_id": item["title_id"],
                "payload_files": len(item["files"]),
            }
            for item in packages
        ],
        "payload_files": sum(len(item["files"]) for item in packages),
    }
