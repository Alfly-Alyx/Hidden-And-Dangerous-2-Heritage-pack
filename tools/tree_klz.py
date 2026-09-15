#!/usr/bin/env python3
"""Audit or clear Hidden & Dangerous 2 mission-area collision flags.

The public tree.klz layout research is documented at:
https://hidden-and-dangerous.net/board/viewtopic.php?t=2173

HD2 extends the Mafia layout with a third grid axis and additional primitive
tables. The first four bytes of every collision record are properties. In
the second byte, 0x40 marks the warning surface and 0x20 marks the mission-
failed surface. Clearing only these bits preserves material and collision.
"""
from __future__ import annotations

import argparse
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path

MAGIC = 0x43666947
MIN_HEADER = 24
COLLISION_HEADER_SIZE = 164
MISSION_AREA_MASK = 0x60

# Record order, count offsets within the HD2 collision header, and sizes.
SECTIONS = (
    ("faces", 72, 32),
    ("aabbs", 88, 32),
    ("xtobbs", 80, 192),
    ("cylinders", 112, 32),
    ("obbs", 104, 160),
    ("spheres", 96, 32),
)


@dataclass(frozen=True)
class Audit:
    path: str
    placeholder: bool
    records: int
    warning_flags: int
    failure_flags: int
    both_flags: int


def _u32(data: bytes | bytearray, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise ValueError(f"offset outside file: {offset}")
    return struct.unpack_from("<I", data, offset)[0]


def _record_offsets(data: bytes | bytearray):
    if len(data) < MIN_HEADER:
        # Official placeholder files contain no collision table.
        if len(data) == 16:
            return
        raise ValueError("truncated tree.klz header")
    if _u32(data, 0) != MAGIC:
        raise ValueError("invalid tree.klz signature")
    collision = _u32(data, 8)
    if collision < MIN_HEADER or collision + COLLISION_HEADER_SIZE > len(data):
        raise ValueError("collision header outside file")

    grid_x = _u32(data, collision + 24)
    grid_z = _u32(data, collision + 28)
    grid_y = _u32(data, collision + 48)
    if grid_x == 0 or grid_y == 0 or grid_z == 0:
        raise ValueError("invalid collision grid dimensions")

    position = collision + COLLISION_HEADER_SIZE
    position += 4 * ((grid_x + 1) + (grid_y + 1) + (grid_z + 1))
    position += 16  # Four HD2 collision-data magic values.

    for name, count_offset, size in SECTIONS:
        count = _u32(data, collision + count_offset)
        if count > len(data) // size:
            raise ValueError(f"implausible {name} count: {count}")
        end = position + count * size
        if end > len(data):
            raise ValueError(f"{name} table outside file")
        for index in range(count):
            yield name, position + index * size
        position = end


def audit_bytes(data: bytes | bytearray, path: str = "") -> Audit:
    if len(data) == 16:
        return Audit(path, True, 0, 0, 0, 0)
    records = warning = failure = both = 0
    for _, offset in _record_offsets(data):
        flags = data[offset + 1] & MISSION_AREA_MASK
        records += 1
        warning += flags == 0x40
        failure += flags == 0x20
        both += flags == MISSION_AREA_MASK
    return Audit(path, False, records, warning, failure, both)


def patch_bytes(data: bytes) -> tuple[bytes, Audit, Audit]:
    before = audit_bytes(data)
    if before.placeholder:
        return data, before, before
    result = bytearray(data)
    for _, offset in _record_offsets(result):
        result[offset + 1] &= ~MISSION_AREA_MASK
    after = audit_bytes(result)
    return bytes(result), before, after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--patch", action="store_true", help="patch files in place")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    reports: list[Audit] = []
    for path in args.paths:
        source = path.read_bytes()
        if args.patch:
            patched, before, after = patch_bytes(source)
            if patched != source:
                temporary = path.with_name(path.name + ".hd2pack.tmp")
                temporary.write_bytes(patched)
                temporary.replace(path)
            report = before
            if after.warning_flags or after.failure_flags or after.both_flags:
                raise ValueError(f"mission-area flags remain in {path}")
        else:
            report = audit_bytes(source, str(path))
        reports.append(Audit(str(path), report.placeholder, report.records,
                             report.warning_flags, report.failure_flags,
                             report.both_flags))

    if args.json:
        print(json.dumps([asdict(item) for item in reports], indent=2))
    else:
        totals = Audit(
            "TOTAL",
            all(item.placeholder for item in reports),
            sum(item.records for item in reports),
            sum(item.warning_flags for item in reports),
            sum(item.failure_flags for item in reports),
            sum(item.both_flags for item in reports),
        )
        print(
            f"{len(reports)} files, {totals.records} records, "
            f"warning={totals.warning_flags}, failure={totals.failure_flags}, "
            f"both={totals.both_flags}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
