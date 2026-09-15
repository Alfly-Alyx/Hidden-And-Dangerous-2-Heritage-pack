#!/usr/bin/env python3
"""Refuse a Heritage Pack release until source, runtime and artifact gates pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import installer_composition_audit
import installer_wiring_audit
import network_runtime_preflight
import runtime_validation_audit


FINAL_SETUP = "H-D2-Heritage-Pack-Setup.exe"
CUSTOM_CASES = {
    "custom.single_setup_integration",
    "custom.three_categories",
    "custom.manager_roundtrip",
}
CUSTOM_BUILD_FILES = {
    "build-custom-mission-manager.ps1",
    "tools/build_static_custom_menu.py",
    "tools/custom_mission_packages.py",
    "tools/custom_mission_tool.py",
}
SOURCE_DIRECTORIES = {
    "installer",
    "payload",
    "custom-mission-tool",
    "custom-missions",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def working_tree(root: Path) -> dict[str, object]:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as git_error:
        return {"clean": False, "changes": [], "error": str(git_error)}
    changes = [line for line in completed.stdout.splitlines() if line.strip()]
    return {
        "clean": completed.returncode == 0 and not changes,
        "changes": changes,
        "error": completed.stderr.strip() or None,
    }


def integration_state(root: Path) -> dict[str, object]:
    installer_sources = list((root / "installer").glob("*.cs"))
    build_sources = [root / "build.ps1", *installer_sources]
    combined = "\n".join(
        path.read_text(encoding="utf-8-sig", errors="replace")
        for path in build_sources
        if path.is_file()
    ).casefold()
    markers = {
        "manager_payload": "hd2-custom-mission-manager.exe" in combined,
        "custom_catalogue": "gamedata02.gdt" in combined,
        "custom_game_menu": (
            "build_static_custom_menu" in combined
            or "static_menu_patch" in combined
            or "customsolomenu" in combined
        ),
        "custom_status_detection": (
            "custommissions" in combined and "detectstatus" in combined
        ),
    }
    return {
        "markers": markers,
        "complete": all(markers.values()),
    }


def runtime_state(root: Path) -> dict[str, object]:
    path = root / "validation" / "runtime-validation.json"
    register = json.loads(path.read_text(encoding="utf-8-sig"))
    cases = register.get("cases", [])
    states = {
        case.get("id"): case.get("state")
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }
    custom_states = {case_id: states.get(case_id) for case_id in CUSTOM_CASES}
    return {
        "case_count": len(cases),
        "all_passed": bool(cases) and all(
            case.get("state") == "passed"
            for case in cases
            if isinstance(case, dict)
        ),
        "custom_cases": custom_states,
        "custom_cases_passed": all(
            state == "passed" for state in custom_states.values()
        ),
    }


def artifact_state(root: Path) -> dict[str, object]:
    path = root / "dist" / FINAL_SETUP
    source_paths = [root / "build.ps1"]
    source_paths.extend(root / item for item in sorted(CUSTOM_BUILD_FILES))
    for directory in sorted(SOURCE_DIRECTORIES):
        source_paths.extend((root / directory).rglob("*"))
    newest_source = max(
        (item.stat().st_mtime for item in source_paths if item.is_file()),
        default=0.0,
    )
    exists = path.is_file()
    modified = path.stat().st_mtime if exists else None
    return {
        "path": str(path),
        "exists": exists,
        "size": path.stat().st_size if exists else None,
        "sha256": sha256(path) if exists else None,
        "modified_after_all_sources": bool(
            exists and modified is not None and modified >= newest_source
        ),
    }


def audit(root: Path, game: Path | None, timeout: float) -> dict[str, object]:
    wiring = installer_wiring_audit.audit(root)
    composition = installer_composition_audit.audit(root)
    runtime_schema = runtime_validation_audit.audit(root)
    runtime = runtime_state(root)
    integration = integration_state(root)
    artifact = artifact_state(root)
    tree = working_tree(root)
    network = None
    if game is not None:
        network = network_runtime_preflight.audit(
            root,
            game,
            network_runtime_preflight.default_hosts_path(),
            timeout,
        )

    gates = {
        "installer_wiring": wiring["ok"],
        "installer_composition": composition["ok"],
        "runtime_register_schema": runtime_schema["ok"],
        "custom_integration": integration["complete"],
        "custom_runtime_validation": runtime["custom_cases_passed"],
        "all_runtime_validation": runtime["all_passed"],
        "clean_working_tree": tree["clean"],
        "final_setup_exists": artifact["exists"],
        "final_setup_fresh": artifact["modified_after_all_sources"],
    }
    if network is not None:
        gates["network_preflight"] = network["ok"]
    blockers = [name for name, passed in gates.items() if not passed]
    return {
        "ok": not blockers,
        "gates": gates,
        "blockers": blockers,
        "installer_wiring": wiring,
        "installer_composition": composition,
        "runtime_register": runtime_schema,
        "runtime": runtime,
        "custom_integration": integration,
        "working_tree": tree,
        "artifact": artifact,
        "network_preflight": network,
        "note": (
            "A previous executable in dist is not a release candidate unless "
            "it is newer than every installer and payload source and all runtime "
            "evidence is passed."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--game", type=Path)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    if arguments.timeout <= 0 or arguments.timeout > 10:
        parser.error("--timeout must be greater than 0 and at most 10 seconds")
    report = audit(
        arguments.root.resolve(),
        arguments.game.resolve() if arguments.game else None,
        arguments.timeout,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
