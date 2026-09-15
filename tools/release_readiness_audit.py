#!/usr/bin/env python3
"""Refuse a Heritage Pack release until source, runtime and artifact gates pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import africa4_key_trigger_audit
import aircraft_scenic_audit
import asset_presence_audit
import boundary_label_audit
import burma1_easter_egg_audit
import community_package_policy_audit
import easter_egg_position_audit
import embedded_dependency_audit
import flamethrower_evidence_audit
import full_game_audit
import full_game_documentation_audit
import installer_composition_audit
import installer_wiring_audit
import item_id_collision_audit
import map_inventory_audit
import network_runtime_preflight
import orphan_weapon_evidence_audit
import prototype_deployment_audit
import runtime_validation_audit
import signal_graph_audit
import stable_candidate_coverage_audit


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
EXPECTED_FULL_GAME_SCOPE = {
    "registry_missions": 68,
    "registry_files": 79,
    "script_directories": 71,
    "effective_scripts": 5347,
    "catalogue_missions": 54,
    "singleplayer_catalogue_missions": 33,
    "multiplayer_catalogue_missions": 21,
    "overridden_scripts": 619,
}
EXPECTED_SIGNAL_GRAPH_SCOPE = {
    "missions": 68,
    "used_scripts": 4894,
    "resolved_signal_calls": 5711,
    "mismatched_signal_calls": 152,
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


def project_evidence_state(root: Path) -> dict[str, object]:
    reports: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for name, run in (
        ("community_package_policy", lambda: community_package_policy_audit.audit(root)),
        ("embedded_dependencies", lambda: embedded_dependency_audit.audit(root)),
    ):
        try:
            reports[name] = run()
        except Exception as error:  # keep a release audit diagnostic, not a traceback
            reports[name] = {"ok": False, "errors": [str(error)]}
        if reports[name].get("ok") is not True:
            errors.append(name)
    return {"ok": not errors, "failed": errors, "reports": reports}


def commercial_evidence_state(root: Path, game: Path) -> dict[str, object]:
    try:
        maps = map_inventory_audit.audit(game)
        unlisted = [
            row for row in maps["directories"]
            if row["interesting_name"] and not row["listed_multiplayer"]
        ]
        full_game = full_game_audit.build(game)
        stable_coverage = stable_candidate_coverage_audit.audit(
            root, game, full_game_report=full_game
        )
        documentation = full_game_documentation_audit.audit(root, full_game)
        signal_graph = signal_graph_audit.build(game)
        prototypes = {
            "archive_plan": prototype_deployment_audit.archive_plan(game),
            "installed": prototype_deployment_audit.installed_state(game),
        }
        assets = asset_presence_audit.audit(game)
        reports = {
            "exploration_boundaries": boundary_label_audit.audit(game),
            "flamethrowers": flamethrower_evidence_audit.audit(game),
            "orphan_weapons": orphan_weapon_evidence_audit.audit(game),
            "aircraft": aircraft_scenic_audit.audit(game),
            "item_id_359": item_id_collision_audit.audit(game, 359),
            "africa4_easter_egg": africa4_key_trigger_audit.audit(game),
            "burma1_easter_egg": burma1_easter_egg_audit.audit(game),
            "easter_egg_positions": easter_egg_position_audit.audit(game),
        }
        checks = {
            "map_inventory": (
                maps["mission_directories"] == 82
                and maps["commercial_multiplayer_directories"] == 47
                and len(unlisted) == 2
            ),
            "full_game_inventory": full_game["scope"] == EXPECTED_FULL_GAME_SCOPE,
            "signal_graph_inventory": (
                signal_graph["scope"] == EXPECTED_SIGNAL_GRAPH_SCOPE
            ),
            "prototype_archive_plan": prototypes["archive_plan"]["ok"],
            "asset_inventory": assets["evidence_ok"],
            "stable_candidate_coverage": stable_coverage["ok"],
            "full_game_documentation": documentation["ok"],
        }
        checks.update(
            (name, report.get("ok") is True)
            for name, report in reports.items()
        )
        return {
            "ok": all(checks.values()),
            "checks": checks,
            "failed": [name for name, passed in checks.items() if not passed],
            "prototype_installed": prototypes["installed"]["ready"],
            "summaries": {
                "maps": {
                    "mission_directories": maps["mission_directories"],
                    "commercial_multiplayer_directories": (
                        maps["commercial_multiplayer_directories"]
                    ),
                    "unlisted_interesting": len(unlisted),
                },
                "full_game": full_game["scope"],
                "stable_candidate_coverage": stable_coverage,
                "full_game_documentation": documentation,
                "signal_graph": signal_graph["scope"],
                "prototype_archive_plan": prototypes["archive_plan"],
                "prototype_installed": prototypes["installed"],
                "assets": {
                    "evidence_ok": assets["evidence_ok"],
                    "evidence_errors": assets["evidence_errors"],
                    "summary": assets["summary"],
                },
                "reports": reports,
            },
        }
    except Exception as error:  # missing/corrupt commercial input must block release
        return {
            "ok": False,
            "checks": {},
            "failed": ["commercial_evidence_exception"],
            "prototype_installed": False,
            "error": str(error),
        }


def audit(root: Path, game: Path | None, timeout: float) -> dict[str, object]:
    wiring = installer_wiring_audit.audit(root)
    composition = installer_composition_audit.audit(root)
    runtime_schema = runtime_validation_audit.audit(root)
    runtime = runtime_state(root)
    integration = integration_state(root)
    artifact = artifact_state(root)
    tree = working_tree(root)
    project_evidence = project_evidence_state(root)
    commercial_evidence = None
    network = None
    if game is not None:
        commercial_evidence = commercial_evidence_state(root, game)
        network = network_runtime_preflight.audit(
            root,
            game,
            network_runtime_preflight.default_hosts_path(),
            timeout,
        )

    gates = {
        "installer_wiring": wiring["ok"],
        "installer_composition": composition["ok"],
        "project_evidence": project_evidence["ok"],
        "runtime_register_schema": runtime_schema["ok"],
        "custom_integration": integration["complete"],
        "custom_runtime_validation": runtime["custom_cases_passed"],
        "all_runtime_validation": runtime["all_passed"],
        "clean_working_tree": tree["clean"],
        "final_setup_exists": artifact["exists"],
        "final_setup_fresh": artifact["modified_after_all_sources"],
    }
    if network is not None:
        gates["commercial_evidence"] = commercial_evidence["ok"]
        gates["prototypes_installed"] = commercial_evidence[
            "prototype_installed"
        ]
        gates["network_preflight"] = network["ok"]
    blockers = [name for name, passed in gates.items() if not passed]
    return {
        "ok": not blockers,
        "gates": gates,
        "blockers": blockers,
        "installer_wiring": wiring,
        "installer_composition": composition,
        "project_evidence": project_evidence,
        "commercial_evidence": commercial_evidence,
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
