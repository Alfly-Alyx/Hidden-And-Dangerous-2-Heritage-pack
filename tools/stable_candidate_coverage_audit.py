#!/usr/bin/env python3
"""Require an explicit, evidenced disposition for every high-value H&D2 candidate."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import full_game_audit
import installer_wiring_audit


MANIFEST = Path("validation/stable-candidate-dispositions.json")
FIELD_CATEGORIES = {
    "inactive_unique_declared_indices": "inactive_unique_objective",
    "script_only_objective_indices": "script_only_objective",
    "unbound_scripts_with_free_matching_actor": "unbound_script_free_owner",
    "missing_attached_scripts": "missing_attached_script",
}
DISPOSITIONS = {
    "stable_integrated",
    "already_active_or_replaced",
    "reconstruction_delegated",
}


def candidate_key(mission: str, category: str, item: object) -> str:
    return f"{mission.casefold()}|{category}|{str(item).casefold()}"


def derive_candidates(report: dict[str, object]) -> dict[str, dict[str, object]]:
    candidates: dict[str, dict[str, object]] = {}
    for mission_row in report.get("missions", []):
        mission = str(mission_row["mission"]).casefold()
        for field, category in FIELD_CATEGORIES.items():
            for item in mission_row.get(field, []):
                key = candidate_key(mission, category, item)
                if key in candidates:
                    raise ValueError(f"Duplicate derived candidate: {key}")
                candidates[key] = {
                    "mission": mission,
                    "category": category,
                    "item": item,
                }
    return candidates


def audit(
    root: Path,
    game: Path | None = None,
    full_game_report: dict[str, object] | None = None,
) -> dict[str, object]:
    root = root.resolve()
    manifest_path = root / MANIFEST
    errors: list[str] = []
    if not manifest_path.is_file():
        return {
            "ok": False,
            "candidate_count": 0,
            "manifest_count": 0,
            "errors": [f"Missing manifest: {MANIFEST.as_posix()}"],
        }
    if full_game_report is None:
        if game is None:
            raise ValueError("game or full_game_report is required")
        full_game_report = full_game_audit.build(game.resolve())

    derived = derive_candidates(full_game_report)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("schema_version") != 1:
        errors.append("Unsupported candidate disposition schema")
    if manifest.get("candidate_fields") != list(FIELD_CATEGORIES):
        errors.append("Manifest candidate_fields no longer matches the audit scope")

    declared: dict[str, dict[str, object]] = {}
    for index, entry in enumerate(manifest.get("entries", []), 1):
        if not isinstance(entry, dict):
            errors.append(f"Manifest entry {index} is not an object")
            continue
        mission = str(entry.get("mission", "")).casefold()
        category = str(entry.get("category", ""))
        item = entry.get("item")
        key = candidate_key(mission, category, item)
        if key in declared:
            errors.append(f"Duplicate manifest entry: {key}")
            continue
        declared[key] = entry

    missing = sorted(set(derived) - set(declared))
    stale = sorted(set(declared) - set(derived))
    if missing:
        errors.append("Candidates without disposition: " + ", ".join(missing))
    if stale:
        errors.append("Stale dispositions without candidate: " + ", ".join(stale))

    core_path = root / "installer" / "InstallerCore.cs"
    core = core_path.read_text(encoding="utf-8-sig", errors="replace")
    stable_entries = []
    disposition_counts: Counter[str] = Counter()
    for key, entry in sorted(declared.items()):
        disposition = entry.get("disposition")
        if disposition not in DISPOSITIONS:
            errors.append(f"Invalid disposition for {key}: {disposition}")
            continue
        disposition_counts[disposition] += 1
        note = entry.get("note")
        if not isinstance(note, str) or not note.strip():
            errors.append(f"Missing explanatory note for {key}")

        evidence_paths = entry.get("evidence_paths")
        if not isinstance(evidence_paths, list) or not evidence_paths:
            errors.append(f"Missing evidence paths for {key}")
            evidence_paths = []
        for relative in evidence_paths:
            path = root / str(relative)
            if not path.is_file():
                errors.append(f"Missing evidence for {key}: {relative}")

        sources = entry.get("installer_sources")
        if not isinstance(sources, list):
            errors.append(f"installer_sources is not a list for {key}")
            sources = []
        if disposition == "stable_integrated":
            if not sources:
                errors.append(f"Stable candidate has no installer source: {key}")
            for relative in sources:
                path = root / str(relative)
                if not path.is_file() or path.suffix.casefold() != ".cs":
                    errors.append(f"Missing installer source for {key}: {relative}")
                    continue
                class_name = path.stem
                if f"{class_name}.Install(" not in core:
                    errors.append(f"Installer source not wired for {key}: {class_name}")
            stable_entries.append(key)
        elif sources:
            errors.append(f"Non-stable candidate unexpectedly names an installer: {key}")

        if disposition == "reconstruction_delegated" and not any(
            str(relative).replace("\\", "/").startswith("experimental/")
            for relative in evidence_paths
        ):
            errors.append(f"Delegated reconstruction has no experimental dossier: {key}")

    wiring = installer_wiring_audit.audit(root) if stable_entries else {"ok": True}
    if wiring.get("ok") is not True:
        errors.append("The global installer wiring audit fails")

    return {
        "ok": not errors,
        "candidate_count": len(derived),
        "manifest_count": len(declared),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "missing_candidates": missing,
        "stale_dispositions": stale,
        "installer_wiring_ok": wiring.get("ok") is True,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.root, arguments.game)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
