#!/usr/bin/env python3
"""Validate the in-game test register and its evidence policy."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ALLOWED_STATES = {"pending", "blocked", "passed", "failed"}
REQUIRED_AREAS = {
    "alternate_paths", "community_maps", "dormant_sequences", "easter_eggs",
    "exploration", "graphics", "installation", "mp_to_solo", "network",
    "objectives", "progression", "prototypes", "rollback",
}
REQUIRED_CASES = {
    "install.clean_112", "install.update_existing", "install.modified_conflict",
    "install.rollback", "install.detect_existing", "network.internet_list",
    "network.internet_join", "graphics.native_resolution",
    "graphics.adaptive_quality", "progress.unlock_all_missions",
    "exploration.no_failure_messages", "exploration.no_invisible_borders",
    "easter.africa1", "easter.africa4_dummy_owner",
    "easter.africa4_mg42_owner", "objectives.arctic3_two_routes",
    "multiplayer.prototype_normandy3", "multiplayer.prototype_africa5",
    "multiplayer.community_package", "conversion.mp_to_solo_gate",
}
EVIDENCE_FIELDS = {"tester", "date", "build_hash", "captures", "logs", "notes"}
MP_SOLO_RUNTIME_FIELDS = {
    "menu_start", "player_spawn", "objective_progress", "mission_end",
}


def non_empty_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def audit(root: Path) -> dict[str, object]:
    register_path = root / "validation" / "runtime-validation.json"
    mp_solo_path = root / "validation" / "multiplayer-solo-runtime.json"
    errors: list[str] = []
    register = json.loads(register_path.read_text(encoding="utf-8"))
    cases = register.get("cases")
    if register.get("schema_version") != 1:
        errors.append("runtime-validation.json must use schema_version 1")
    if not isinstance(cases, list) or not cases:
        errors.append("runtime-validation.json has no cases")
        cases = []

    ids: list[str] = []
    areas: list[str] = []
    states: Counter[str] = Counter()
    for index, case in enumerate(cases):
        label = f"case #{index + 1}"
        if not isinstance(case, dict):
            errors.append(f"{label} is not an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{label} has no stable id")
        else:
            ids.append(case_id)
            label = case_id
        area = case.get("area")
        if not isinstance(area, str) or not area.strip():
            errors.append(f"{label} has no area")
        else:
            areas.append(area)
        for field in ("title", "mode"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                errors.append(f"{label} has no {field}")
        if not non_empty_strings(case.get("steps")):
            errors.append(f"{label} has no executable steps")
        if not non_empty_strings(case.get("expected")):
            errors.append(f"{label} has no expected results")

        state = case.get("state")
        if state not in ALLOWED_STATES:
            errors.append(f"{label} has invalid state {state!r}")
            continue
        states[state] += 1
        evidence = case.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"{label} has no evidence object")
            continue
        missing = sorted(EVIDENCE_FIELDS - set(evidence))
        extra = sorted(set(evidence) - EVIDENCE_FIELDS)
        if missing:
            errors.append(f"{label} evidence misses: {', '.join(missing)}")
        if extra:
            errors.append(f"{label} evidence has unknown fields: {', '.join(extra)}")
        if not isinstance(evidence.get("captures"), list):
            errors.append(f"{label} captures must be a list")
        if not isinstance(evidence.get("logs"), list):
            errors.append(f"{label} logs must be a list")
        if state == "passed":
            for field in ("tester", "date", "build_hash"):
                value = evidence.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{label} is passed without {field}")
            if not evidence.get("captures") and not evidence.get("logs"):
                errors.append(f"{label} is passed without capture or log")
        if state == "blocked":
            notes = evidence.get("notes")
            if not isinstance(notes, str) or not notes.strip():
                errors.append(f"{label} is blocked without an explanation")

    duplicates = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicates:
        errors.append("Duplicate case ids: " + ", ".join(duplicates))
    missing_areas = sorted(REQUIRED_AREAS - set(areas))
    if missing_areas:
        errors.append("Missing validation areas: " + ", ".join(missing_areas))
    missing_cases = sorted(REQUIRED_CASES - set(ids))
    if missing_cases:
        errors.append("Missing required cases: " + ", ".join(missing_cases))

    mp_solo = json.loads(mp_solo_path.read_text(encoding="utf-8"))
    if mp_solo.get("schema_version") != 1:
        errors.append("multiplayer-solo-runtime.json must use schema_version 1")
    missions = mp_solo.get("missions")
    if not isinstance(missions, list):
        errors.append("multiplayer-solo-runtime.json missions must be a list")
        missions = []
    validated_mp_solo = 0
    for index, mission in enumerate(missions):
        label = f"multiplayer-solo mission #{index + 1}"
        if not isinstance(mission, dict):
            errors.append(f"{label} is not an object")
            continue
        if mission.get("state") != "validated":
            continue
        validated_mp_solo += 1
        runtime = mission.get("runtime")
        if not isinstance(runtime, dict):
            errors.append(f"{label} is validated without runtime evidence")
            continue
        missing = sorted(
            field for field in MP_SOLO_RUNTIME_FIELDS if runtime.get(field) is not True
        )
        if missing:
            errors.append(f"{label} is validated without: {', '.join(missing)}")

    return {
        "ok": not errors,
        "schema_version": register.get("schema_version"),
        "milestone": register.get("milestone"),
        "cases": len(cases),
        "areas": dict(sorted(Counter(areas).items())),
        "states": dict(sorted(states.items())),
        "required_cases": len(REQUIRED_CASES),
        "validated_mp_to_solo": validated_mp_solo,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", nargs="?", type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to the parent of tools)",
    )
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.root.resolve())
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
