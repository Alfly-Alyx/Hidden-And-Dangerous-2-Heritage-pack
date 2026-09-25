#!/usr/bin/env python3
"""Verify inert A/B laboratories against the compiled manager and real catalogues.

Only manifests and an invented tree placeholder enter a temporary fixture library.
No commercial mission is activated, installed, extracted or launched. The manager
is invoked exclusively through its two offline catalogue inspection commands.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from build_reconstruction_lab import verify_bundle
from build_reconstruction_variant import ROOT, digest, normalized
from dta_archive import DtaArchive
from objective_audit import blocks, direct, walk


def mission_nodes(raw: bytes) -> dict:
    parsed = blocks(raw, 0, len(raw))
    if parsed is None:
        raise ValueError("Unreadable catalogue")
    result = {}
    for node in walk(parsed):
        names = direct(node, 0x36) if node.kind == 0x32 else []
        if not names:
            continue
        name = names[0].payload.rstrip(b"\0").decode("cp1252").casefold()
        if name in result:
            raise ValueError(f"Ambiguous mission: {name}")
        result[name] = node
    return result


def objective_bytes(node) -> list[bytes]:
    # The complete payload includes text IDs, flags and nested data, in order.
    return [child.payload for child in direct(node, 0x28)]


def invoke(manager: Path, *args: str) -> str:
    process = subprocess.run([str(manager), *map(str, args)], capture_output=True,
                             text=True, encoding="utf-8-sig", timeout=90)
    if process.returncode:
        raise ValueError(f"Offline manager check failed: {process.stdout} {process.stderr}")
    return process.stdout.strip()


def audit(game: Path, manager: Path, bundles: list[Path]) -> dict:
    game, manager = game.resolve(), manager.resolve()
    if not manager.is_file():
        raise ValueError("Build the console manager first")
    scratch = (ROOT / ".analysis").resolve()
    if scratch.is_relative_to(game):
        raise ValueError("Temporary catalogue fixtures must stay outside the game")
    scratch.mkdir(exist_ok=True)
    reports = [(path, verify_bundle(path)) for path in bundles]
    archive_path = game / "SabreSquadron.dta"
    with DtaArchive(archive_path) as archive:
        source_catalogues = {}
        for name in ("gamedata/gamedata00.gdt", "gamedata/gamedata01.gdt"):
            matches = [entry for entry in archive.entries if normalized(entry.name) == name]
            if len(matches) != 1:
                raise ValueError(f"Missing or ambiguous source catalogue: {name}")
            source_catalogues[name] = archive.read(matches[0])
    templates = {}
    for raw in source_catalogues.values():
        for name, node in mission_nodes(raw).items():
            if name in templates:
                raise ValueError(f"Ambiguous Base/Sabre template: {name}")
            templates[name] = node
    official = mission_nodes(source_catalogues["gamedata/gamedata01.gdt"])
    with tempfile.TemporaryDirectory(prefix="catalogue-audit-", dir=scratch) as temporary:
        root = Path(temporary)
        library, output = root / "fixtures-not-playable", root / "catalogue.gdt"
        mappings = {}
        for path, report in reports:
            with zipfile.ZipFile(path) as archive:
                for package in report["packages"]:
                    directory = package["mission_directory"]
                    if directory.casefold() in mappings:
                        raise ValueError("Duplicate laboratory supplied")
                    mappings[directory.casefold()] = report["source_mission"]
                    manifest = archive.read(package["manifest_member"])
                    fixture = library / package["id"]
                    tree = fixture / "payload/Missions" / directory / "tree.klz"
                    tree.parent.mkdir(parents=True)
                    tree.write_bytes(b"INVENTED CATALOGUE-ONLY TEST PLACEHOLDER; NOT PLAYABLE")
                    (fixture / "mission.json").write_bytes(manifest)
        invoke(manager, "--catalogue-test", library, game, output)
        result_bytes = output.read_bytes()
        result = mission_nodes(result_bytes)
        if set(result) != set(official) | set(mappings):
            raise ValueError("Unexpected mission list in generated catalogue")
        for name, node in official.items():
            if result[name].payload != node.payload:
                raise ValueError(f"Official expansion mission changed: {name}")
        details = []
        for name, template in sorted(mappings.items()):
            expected = objective_bytes(templates[template])
            if objective_bytes(result[name]) != expected:
                raise ValueError(f"Inherited objective bytes/order changed: {name}")
            details.append({"mission": name, "template": template,
                            "objectives_preserved": len(expected)})
        runtime_hashes = json.loads(invoke(manager, "--runtime-test", library, game))
        if not runtime_hashes or not all(len(value) == 64 for value in runtime_hashes.values()):
            raise ValueError("Incomplete offline runtime-file generation")
    return {"status": "offline_catalogue_checks_passed", "runtime_status": "pending",
            "installed_into_game": False, "playable_packages_extracted": False,
            "official_expansion_missions_unchanged": len(official), "packages": details,
            "catalogue_sha256": digest(result_bytes), "runtime_files_sha256": runtime_hashes,
            "source_catalogues_sha256": {name: digest(raw) for name, raw in source_catalogues.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--manager", type=Path,
                        default=ROOT / "build/HD2CustomMissionManager.Console.exe")
    parser.add_argument("bundles", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.game, args.manager, args.bundles), indent=2))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        print(f"Catalogue check failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
