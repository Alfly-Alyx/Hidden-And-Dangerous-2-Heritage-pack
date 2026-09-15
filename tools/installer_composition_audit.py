#!/usr/bin/env python3
"""Check that installers sharing a target compose instead of overwriting it."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


INSTALL_RE = re.compile(
    r"^\s*(?P<class>[A-Za-z0-9_]+)\.Install\(", re.MULTILINE
)

SHARED_TARGETS = {
    "mpmaplist.txt": [
        "ExperimentalContentInstaller",
        "CmpInstaller",
        "CoLibye2ObjectiveInstaller",
        "CoBrestGeneratorObjectiveInstaller",
        "CoBurgundy1StealthObjectiveInstaller",
    ],
    "Missions/Co_brest/Scripts.dta": [
        "CoBrestGeneratorObjectiveInstaller",
        "BrestRouteInstaller",
        "CoBrestHintInstaller",
    ],
    "Missions/Co_brest/mpscripts.dta": [
        "CoBrestGeneratorObjectiveInstaller",
        "BrestRouteInstaller",
    ],
}

CURRENT_SOURCE_MARKERS = {
    "ExperimentalContentInstaller": (
        "File.ReadAllText(mapListPath, ansi)",
        "AddVestiges(originalMapList)",
    ),
    "CmpInstaller": (
        "File.Exists(rootMapList)",
        "File.ReadAllText(rootMapList, ansi)",
        "ExperimentalContentInstaller.AddVestiges(merged)",
    ),
    "CoLibye2ObjectiveInstaller": (
        "File.ReadAllText(target, Encoding.GetEncoding(1252))",
        "AddVehicleObjective(original)",
    ),
    "CoBrestGeneratorObjectiveInstaller": (
        "File.Exists(target)",
        "File.ReadAllBytes(target)",
        "File.ReadAllText( mapTarget, Encoding.GetEncoding(1252))",
        "AddObjective(originalList)",
    ),
    "CoBurgundy1StealthObjectiveInstaller": (
        "File.Exists(scriptTarget)",
        "File.ReadAllBytes(scriptTarget)",
        "File.ReadAllText( mapTarget, Encoding.GetEncoding(1252))",
        "AddObjectives(originalList)",
    ),
    "BrestRouteInstaller": (
        "File.Exists(target)",
        "File.ReadAllBytes(target)",
        "PatchRegistry(original)",
    ),
    "CoBrestHintInstaller": (
        "File.Exists(target)",
        "File.ReadAllBytes(target)",
        "PatchRegistry(original)",
    ),
}

EXPECTED_ORDER = [
    "ExperimentalContentInstaller",
    "CmpInstaller",
    "CoLibye2ObjectiveInstaller",
    "CoBrestGeneratorObjectiveInstaller",
    "CoBurgundy1StealthObjectiveInstaller",
    "BrestRouteInstaller",
    "CoBrestHintInstaller",
]


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def audit(root: Path) -> dict[str, object]:
    installer = root / "installer"
    core_path = installer / "InstallerCore.cs"
    journal_path = installer / "StateJournal.cs"
    core = core_path.read_text(encoding="utf-8-sig")
    journal = journal_path.read_text(encoding="utf-8-sig")
    install_order = INSTALL_RE.findall(core)
    errors: list[str] = []

    missing_installers: list[str] = []
    missing_current_source_markers: dict[str, list[str]] = {}
    missing_hash_writers: list[str] = []
    for class_name, markers in CURRENT_SOURCE_MARKERS.items():
        source_path = installer / f"{class_name}.cs"
        if not source_path.is_file():
            missing_installers.append(class_name)
            continue
        source = source_path.read_text(encoding="utf-8-sig")
        normalized = compact(source)
        missing = [
            marker for marker in markers if compact(marker) not in normalized
        ]
        if missing:
            missing_current_source_markers[class_name] = missing
        if ".RecordHash(" not in source:
            missing_hash_writers.append(class_name)

    if missing_installers:
        errors.append(
            "Missing shared-target installers: " + ", ".join(missing_installers)
        )
    for class_name, markers in missing_current_source_markers.items():
        errors.append(
            f"{class_name} no longer reads/merges the current target: "
            + ", ".join(markers)
        )
    if missing_hash_writers:
        errors.append(
            "Shared-target writers without final hash: "
            + ", ".join(missing_hash_writers)
        )

    positions: dict[str, int] = {}
    for class_name in EXPECTED_ORDER:
        try:
            positions[class_name] = install_order.index(class_name)
        except ValueError:
            errors.append(f"{class_name} is absent from InstallerCore.Install")
    for left, right in zip(EXPECTED_ORDER, EXPECTED_ORDER[1:]):
        if left in positions and right in positions:
            if positions[left] >= positions[right]:
                errors.append(f"Unsafe installer order: {left} must precede {right}")

    single_backup_policy = all(
        marker in compact(core)
        for marker in (
            "if (!prepared.Add(relative)) return;",
            "File.Copy(target, backup, false);",
        )
    )
    if not single_backup_policy:
        errors.append("PrepareTarget no longer preserves one original backup per target")

    last_hash_wins = all(
        marker in compact(journal)
        for marker in (
            "for (int index = State.Changes.Count - 1; index >= 0; index--)",
            "State.Changes[index].InstalledSha256 = sha256;",
            "break;",
        )
    )
    if not last_hash_wins:
        errors.append("StateJournal no longer records the final composed target hash")

    writers = sorted(
        {
            writer
            for target_writers in SHARED_TARGETS.values()
            for writer in target_writers
        }
    )
    return {
        "ok": not errors,
        "shared_targets": len(SHARED_TARGETS),
        "shared_writers": len(writers),
        "targets": SHARED_TARGETS,
        "install_order": [
            class_name for class_name in install_order if class_name in writers
        ],
        "current_target_merge": not missing_current_source_markers,
        "single_original_backup": single_backup_policy,
        "final_hash_after_each_write": not missing_hash_writers and last_hash_wins,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root", nargs="?", type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    arguments = parser.parse_args()
    result = audit(arguments.root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
