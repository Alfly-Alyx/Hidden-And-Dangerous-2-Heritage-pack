#!/usr/bin/env python3
"""Build an ignored, disabled Arctic 4 guard variant from a licensed game."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from build_reconstruction_variant import (  # noqa: E402
    ArchiveSources, load_catalog, prepare, write_disabled,
)


def build(game: Path, output: Path) -> dict[str, str | int]:
    profile = load_catalog()["arctic4-guard3-alarm-post"]
    with ArchiveSources(game) as sources:
        variant, report = prepare(profile, sources)
    output = write_disabled(output, variant, game)
    return {
        "profile": "legacy_alarm_destination",
        "output": str(output),
        "commercial_sha256": report["source_sha256"],
        "variant_sha256": report["variant_sha256"],
        "changed_line_count": 1,
        "bytes": len(variant),
        "installed_into_game": False,
        "runtime_status": "pending",
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
