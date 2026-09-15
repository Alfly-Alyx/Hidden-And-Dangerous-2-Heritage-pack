#!/usr/bin/env python3
"""Verify free-exploration patches across all effective commercial tree.klz files."""
from __future__ import annotations

import argparse
import json
import struct
from collections import Counter
from pathlib import Path

from dta_archive import DtaArchive
from tree_klz import MAGIC, audit_bytes, patch_bytes


MISSION_ARCHIVES = ("missions.dta", "Patch.dta", "SabreSquadron.dta")
RESEARCH_SOURCE = "https://hidden-and-dangerous.net/board/viewtopic.php?t=2173"


def normalized(value: str) -> str:
    return value.replace(chr(92), "/").casefold()


def effective_sources(game: Path) -> dict[str, tuple[str, int, str]]:
    selected = {}
    for archive_name in MISSION_ARCHIVES:
        with DtaArchive(game / archive_name) as archive:
            for entry in archive.entries:
                name = normalized(entry.name)
                if name.startswith("missions/") and name.endswith("/tree.klz"):
                    selected[name] = (archive_name, entry.index, entry.name)
    return selected


def object_labels(data: bytes) -> list[bytes]:
    if len(data) == 16:
        return []
    if len(data) < 24 or struct.unpack_from("<I", data, 0)[0] != MAGIC:
        raise ValueError("invalid tree.klz signature")
    count = struct.unpack_from("<I", data, 12)[0]
    if count > (len(data) - 24) // 4:
        raise ValueError("object table outside file")
    result = []
    for index in range(count):
        offset = struct.unpack_from("<I", data, 24 + index * 4)[0] + 4
        if offset < 0 or offset >= len(data):
            raise ValueError("object label outside file")
        end = data.find(b"\0", offset)
        if end < 0:
            raise ValueError("unterminated object label")
        result.append(data[offset:end])
    return result


def family(label: bytes) -> str | None:
    name = label.decode("cp1252", errors="replace").casefold()
    if "border" in name:
        return "engine_border"
    if "leaving_zone" in name:
        return "leaving_zone"
    if "live_zone" in name or "liv_zone" in name:
        return "live_zone"
    if "wall" in name:
        return "named_wall"
    if "zabr" in name or "barier" in name:
        return "named_fence"
    return None


def verify_labels(before: list[bytes], after: list[bytes]) -> list[str]:
    errors = []
    if len(before) != len(after):
        return ["object label count changed"]
    for index, (old, new) in enumerate(zip(before, after)):
        if b"border" in old.lower():
            if len(old) != len(new) or b"border" in new.lower():
                errors.append(f"border label {index} was not safely neutralized")
        elif old != new:
            errors.append(f"non-border label {index} changed")
    return errors


def audit(game: Path) -> dict[str, object]:
    selected = effective_sources(game)
    rows = []
    totals = Counter()
    families = Counter()
    errors = []
    by_archive: dict[str, list[tuple[str, int, str]]] = {}
    for relative, (archive_name, entry_index, raw_name) in selected.items():
        by_archive.setdefault(archive_name, []).append(
            (relative, entry_index, raw_name)
        )

    for archive_name in MISSION_ARCHIVES:
        entries = by_archive.get(archive_name, [])
        if not entries:
            continue
        with DtaArchive(game / archive_name) as archive:
            for relative, entry_index, raw_name in sorted(entries):
                data = archive.read(archive.entries[entry_index])
                before = audit_bytes(data, relative)
                labels_before = object_labels(data)
                for label in labels_before:
                    label_family = family(label)
                    if label_family:
                        families[label_family] += 1
                patched, _, after = patch_bytes(data)
                labels_after = object_labels(patched)
                current_errors = verify_labels(labels_before, labels_after)
                if len(data) != len(patched):
                    current_errors.append("file size changed")
                if (
                    after.warning_flags
                    or after.failure_flags
                    or after.both_flags
                    or after.boundary_labels
                ):
                    current_errors.append("mission-area limit remains")
                errors.extend(f"{relative}: {item}" for item in current_errors)
                totals["records"] += before.records
                totals["warning_flags"] += before.warning_flags
                totals["failure_flags"] += before.failure_flags
                totals["both_flags"] += before.both_flags
                totals["boundary_labels"] += before.boundary_labels
                totals["placeholders"] += int(before.placeholder)
                if (
                    before.warning_flags
                    or before.failure_flags
                    or before.both_flags
                    or before.boundary_labels
                ):
                    totals["trees_with_limits"] += 1
                rows.append({
                    "path": relative,
                    "archive": archive_name,
                    "archive_entry": raw_name,
                    "placeholder": before.placeholder,
                    "records": before.records,
                    "warning_flags": before.warning_flags,
                    "failure_flags": before.failure_flags,
                    "both_flags": before.both_flags,
                    "boundary_labels": before.boundary_labels,
                    "patched_size_unchanged": len(data) == len(patched),
                    "patched_limits_remaining": (
                        after.warning_flags + after.failure_flags
                        + after.both_flags + after.boundary_labels
                    ),
                })

    return {
        "game": str(game),
        "ok": not errors,
        "errors": errors,
        "research_source": RESEARCH_SOURCE,
        "method": {
            "surface_flags": (
                "clear only mission-area bits 0x40 warning and 0x20 failure"
            ),
            "physical_boundary_objects": (
                "rename the six-byte border substring to H2BORD without "
                "changing offsets or file size"
            ),
            "preserved_names": (
                "wall, fence and zone labels without border are not renamed"
            ),
        },
        "tree_count": len(rows),
        "totals": dict(sorted(totals.items())),
        "lexical_families": dict(sorted(families.items())),
        "trees": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.game.resolve())
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
