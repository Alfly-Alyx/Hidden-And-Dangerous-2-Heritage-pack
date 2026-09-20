#!/usr/bin/env python3
"""Verify Heritage setup packaging for the custom mission manager."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SKELETON = {
    "README.md": "A68618FCEE71845E95A6967F830CF1556E4D0916E5B2446761E4A1820F6E8415",
    "mission.schema.json": "C53CDD71AAB058D3B8E4E94B6A1140663B7D9A0B577B040FFD6850CA3EDE9D75",
    "_modele/mission.json": "9439500FB79D571160E22B2884DE1662E73ED779641329A3C7AA5E737DA5946F",
    "_modele/payload/Missions/MaMission/LISEZ_MOI.txt": (
        "A48C1FFE82BDD37BD943CF259B7468AD4DF5D65F96096A6C5CD3269BAE834A03"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def audit(root: Path) -> dict[str, object]:
    manager = root / "dist" / "HD2-Custom-Mission-Manager.exe"
    manager_hash_path = root / "build" / "HD2-Custom-Mission-Manager.sha256"
    library = root / "custom-missions"
    installer_path = root / "installer" / "CustomMissionManagerInstaller.cs"
    core_path = root / "installer" / "InstallerCore.cs"
    program_path = root / "installer" / "Program.cs"
    build_path = root / "build.ps1"
    errors: list[str] = []

    manager_bytes = manager.read_bytes() if manager.is_file() else b""
    if len(manager_bytes) < 65_536 or not manager_bytes.startswith(b"MZ"):
        errors.append("Built custom mission manager is missing or not a PE executable")
    manager_sha256 = sha256(manager) if manager.is_file() else None
    recorded_manager_hash = (
        manager_hash_path.read_text(encoding="ascii").strip().upper()
        if manager_hash_path.is_file() else None
    )
    if recorded_manager_hash != manager_sha256:
        errors.append("Embedded manager hash manifest is missing or stale")

    actual_hashes: dict[str, str | None] = {}
    for relative, expected in SKELETON.items():
        path = library / Path(relative)
        actual = sha256(path) if path.is_file() else None
        actual_hashes[relative] = actual
        if actual != expected:
            errors.append("Missing or changed CustomMissions skeleton: " + relative)

    installer = installer_path.read_text(encoding="utf-8-sig")
    core = core_path.read_text(encoding="utf-8-sig")
    program = program_path.read_text(encoding="utf-8-sig")
    build = build_path.read_text(encoding="utf-8-sig")

    installer_markers = [
        'RelativePath = "HD2-Custom-Mission-Manager.exe"',
        "InstallerCore.SafeGameTarget(gamePath, relative)",
        "InstallerCore.PrepareTarget(",
        "journal.RecordHash(",
        "file.PreserveExisting && File.Exists(target) && !tracked",
        "ValidateExecutable(content)",
        "string expected = ReadManagerHash();",
        "string actual = ComputeSha256(content);",
    ]
    for relative, expected in SKELETON.items():
        installer_markers.extend((
            'RelativePath = "CustomMissions/' + relative + '"',
            'Sha256 = "' + expected + '"',
        ))
    missing = [marker for marker in installer_markers if marker not in installer]
    if missing:
        errors.append("Manager installer safety wiring changed: " + ", ".join(missing))

    build_markers = [
        "& (Join-Path $projectRoot 'build-custom-mission-manager.ps1')",
        "/resource:$missionManager,HD2CommunityInstaller.CustomMissionManager.exe",
        "/resource:$missionManagerHash,HD2CommunityInstaller.CustomMissionManager.sha256",
        "/resource:$customMissionReadme,HD2CommunityInstaller.CustomMissions.Readme",
        "/resource:$customMissionSchema,HD2CommunityInstaller.CustomMissions.Schema",
        "/resource:$customMissionTemplate,HD2CommunityInstaller.CustomMissions.TemplateManifest",
        "/resource:$customMissionTemplateReadme,HD2CommunityInstaller.CustomMissions.TemplateReadme",
    ]
    missing = [marker for marker in build_markers if marker not in build]
    if missing:
        errors.append("Manager resources are not embedded by build.ps1: " + ", ".join(missing))

    if "CustomMissionManagerInstaller.Install(" not in core:
        errors.append("InstallerCore does not install the custom mission manager")
    if "CustomMissionManagerInstaller.DetectStatus(" not in core:
        errors.append("InstallerCore diagnostic does not report manager status")
    if program.count("CustomMissionManagerInstaller.ValidateOnly()") != 2:
        errors.append("Both local and full self-tests must validate manager resources")

    return {
        "ok": not errors,
        "manager_size": len(manager_bytes),
        "manager_sha256": manager_sha256,
        "manager_hash_manifest_matches": recorded_manager_hash == manager_sha256,
        "skeleton_files": len(SKELETON),
        "verified_skeleton_files": sum(
            actual_hashes[name] == expected
            for name, expected in SKELETON.items()
        ),
        "preserves_untracked_user_content": (
            "file.PreserveExisting && File.Exists(target) && !tracked" in installer
        ),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", nargs="?", type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    result = audit(parser.parse_args().root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
