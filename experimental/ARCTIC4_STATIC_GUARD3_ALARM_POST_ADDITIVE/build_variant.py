#!/usr/bin/env python3
"""Build an ignored, disabled Arctic 4 guard variant from a licensed game."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from dta_archive import DtaArchive  # noqa: E402
from script_binding_audit import parse_bindings  # noqa: E402


SCRIPT_ENTRY = "scripts/arctic4/r_arc3_static_guard_3.scr"
REGISTRY_ENTRY = "missions/arctic4/scripts.dta"
CHECKPOINT_ENTRY = "missions/arctic4/check2.bin"
EXPECTED_SCRIPT_SHA256 = (
    "73e72535024bedf65787ae3fda305724ab1386c6941c9809ea786fbe9a41208b"
)
OLD_LINE = b'//  HUMAN_Move("StaticGuard3_5");'
NEW_LINE = OLD_LINE[2:]


def read_entry(archive_path: Path, wanted: str) -> bytes | None:
    with DtaArchive(archive_path) as archive:
        matches = [
            entry for entry in archive.entries
            if entry.name.replace("\\", "/").casefold() == wanted
        ]
        if len(matches) > 1:
            raise ValueError(f"Multiple archive entries match {wanted}")
        return archive.read(matches[0]) if matches else None


def build(game: Path, output: Path) -> dict[str, str | int]:
    ignored_root = (ROOT / ".analysis").resolve()
    output = output.resolve()
    if not output.is_relative_to(ignored_root):
        raise ValueError("Output must stay inside the ignored .analysis directory")
    if not output.name.endswith(".scr.disabled"):
        raise ValueError("Output must end in .scr.disabled")

    script = read_entry(game / "Scripts.dta", SCRIPT_ENTRY)
    if script is None:
        raise ValueError(f"Missing commercial script: {SCRIPT_ENTRY}")
    actual_sha = hashlib.sha256(script).hexdigest()
    if actual_sha != EXPECTED_SCRIPT_SHA256:
        raise ValueError(f"Unexpected commercial script SHA-256: {actual_sha}")
    for later_archive in ("Patch.dta", "SabreSquadron.dta"):
        if read_entry(game / later_archive, SCRIPT_ENTRY) is not None:
            raise ValueError(f"Unexpected override in {later_archive}")

    registry = read_entry(game / "missions.dta", REGISTRY_ENTRY)
    if registry is None or (
        "Static_Guard_3", "R_Arc3_static_guard_3.scr"
    ) not in parse_bindings(registry):
        raise ValueError("Static_Guard_3 binding is missing or changed")
    checkpoint = read_entry(game / "missions.dta", CHECKPOINT_ENTRY)
    if checkpoint is None or b"StaticGuard3_5\x00" not in checkpoint:
        raise ValueError("StaticGuard3_5 checkpoint is missing")
    if script.count(OLD_LINE) != 1:
        raise ValueError("Expected exactly one commented alarm movement")

    variant = script.replace(OLD_LINE, NEW_LINE, 1)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as destination:
        destination.write(variant)
    return {
        "profile": "legacy_alarm_destination",
        "output": str(output),
        "commercial_sha256": actual_sha,
        "variant_sha256": hashlib.sha256(variant).hexdigest(),
        "changed_line_count": 1,
        "bytes": len(variant),
        "installed_into_game": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / ".analysis/generated/arctic4-guard3-fixed-post.scr.disabled",
    )
    arguments = parser.parse_args()
    try:
        report = build(arguments.game, arguments.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Variant not built: {error}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
