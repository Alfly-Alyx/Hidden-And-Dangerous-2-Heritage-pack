#!/usr/bin/env python3
"""Check an additive ItemID against commercial and installed mission records."""

from __future__ import annotations

import argparse
import json
import re
import struct
from collections import Counter
from pathlib import Path

from dta_archive import DtaArchive


COMMERCIAL_ARCHIVES = ("missions.dta", "Patch.dta", "SabreSquadron.dta")
HEADER = 0x10
PLACED_PREFIX = bytes(9)
PLACED_RECORD_SIZE = 61
ITEM_ATTRIBUTE_RE = re.compile(
    rb"""\bitem_id\s*=\s*["']([0-9]+)["']""",
    re.IGNORECASE,
)


class ItemsFormatError(ValueError):
    def __init__(
        self,
        message: str,
        records: list[dict[str, object]],
        offset: int,
    ) -> None:
        super().__init__(message)
        self.records = records
        self.offset = offset


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def parse_items(data: bytes, source: str) -> list[dict[str, object]]:
    """Parse assigned and world-placement records from an H&D2 items.dat."""
    records: list[dict[str, object]] = []
    if len(data) < 4 or read_u32(data, 0) != HEADER:
        raise ItemsFormatError(
            f"{source}: invalid items.dat header", records, 0
        )

    offset = 4
    while offset < len(data):
        if data[offset:offset + 9] == PLACED_PREFIX:
            end = offset + PLACED_RECORD_SIZE
            if end > len(data):
                raise ItemsFormatError(
                    f"{source}: truncated placed-item record at {offset}",
                    records,
                    offset,
                )
            item_id = read_u32(data, offset + 9)
            order = read_u32(data, offset + 13)
            enabled = read_u32(data, offset + 17)
            if enabled != 1:
                raise ItemsFormatError(
                    f"{source}: placed-item marker is {enabled} at {offset}",
                    records,
                    offset,
                )
            records.append({
                "kind": "placed",
                "item_id": item_id,
                "order": order,
                "offset": offset + 9,
                "owner": None,
            })
            offset = end
            continue

        if offset + 4 > len(data):
            raise ItemsFormatError(
                f"{source}: truncated owner length at {offset}",
                records,
                offset,
            )
        name_size = read_u32(data, offset)
        end = offset + 29 + name_size
        if name_size < 2 or end > len(data):
            raise ItemsFormatError(
                f"{source}: invalid owner record size {name_size} at {offset}",
                records,
                offset,
            )
        name_start = offset + 4
        name_end = name_start + name_size
        if data[name_end - 1] != 0:
            raise ItemsFormatError(
                f"{source}: unterminated owner name at {offset}",
                records,
                offset,
            )
        owner = data[name_start:name_end - 1].decode(
            "cp1252", errors="replace"
        )
        records.append({
            "kind": "assigned",
            "item_id": read_u32(data, offset + 9 + name_size),
            "order": read_u32(data, offset + 13 + name_size),
            "offset": offset + 9 + name_size,
            "owner": owner,
        })
        offset = end

    return records


def scan_commercial(
    game: Path,
    candidate: int,
) -> tuple[list[dict[str, object]], list[str], list[str]]:
    files: list[dict[str, object]] = []
    errors: list[str] = []
    warnings: list[str] = []
    needle = struct.pack("<I", candidate)
    for archive_name in COMMERCIAL_ARCHIVES:
        archive_path = game / archive_name
        try:
            with DtaArchive(archive_path) as archive:
                for entry in archive.entries:
                    if not entry.name.casefold().endswith("items.dat"):
                        continue
                    source = archive_name + "::" + entry.name.replace("\\", "/")
                    data = archive.read(entry)
                    try:
                        records = parse_items(data, source)
                    except (OSError, ItemsFormatError) as error:
                        parsed = (
                            error.records
                            if isinstance(error, ItemsFormatError) else []
                        )
                        safe_until = (
                            error.offset
                            if isinstance(error, ItemsFormatError) else 0
                        )
                        occurrences = [
                            offset
                            for offset in range(len(data))
                            if data.startswith(needle, offset)
                        ]
                        prefix_safe = all(
                            offset + len(needle) <= safe_until
                            for offset in occurrences
                        )
                        if occurrences and not prefix_safe:
                            errors.append(
                                f"{error}; candidate bytes cannot be "
                                "disambiguated"
                            )
                            continue
                        warnings.append(
                            f"{error}; candidate excluded by "
                            + (
                                "validated prefix"
                                if occurrences else "raw absence"
                            )
                        )
                        files.append({
                            "source": source,
                            "scope": "commercial",
                            "records": parsed,
                            "scan_mode": (
                                "parsed_prefix"
                                if occurrences else "raw_absence"
                            ),
                        })
                        continue
                    files.append({
                        "source": source,
                        "scope": "commercial",
                        "records": records,
                        "scan_mode": "parsed",
                    })
        except OSError as error:
            errors.append(f"{archive_path}: {error}")
    return files, errors, warnings


def scan_loose_missions(
    game: Path,
    candidate: int,
) -> tuple[list[dict[str, object]], list[str], list[str]]:
    files: list[dict[str, object]] = []
    errors: list[str] = []
    warnings: list[str] = []
    needle = struct.pack("<I", candidate)
    missions = game / "Missions"
    if not missions.is_dir():
        return files, errors, warnings
    for path in sorted(
        missions.rglob("items.dat"),
        key=lambda value: str(value).casefold(),
    ):
        source = path.relative_to(game).as_posix()
        data: bytes | None = None
        try:
            data = path.read_bytes()
            records = parse_items(data, source)
        except (OSError, ItemsFormatError) as error:
            parsed = (
                error.records
                if isinstance(error, ItemsFormatError) else []
            )
            safe_until = (
                error.offset
                if isinstance(error, ItemsFormatError) else 0
            )
            occurrences = (
                [
                    offset
                    for offset in range(len(data))
                    if data.startswith(needle, offset)
                ]
                if data is not None else []
            )
            prefix_safe = all(
                offset + len(needle) <= safe_until
                for offset in occurrences
            )
            if data is not None and (not occurrences or prefix_safe):
                warnings.append(
                    f"{error}; candidate excluded by "
                    + (
                        "validated prefix"
                        if occurrences else "raw absence"
                    )
                )
                files.append({
                    "source": source,
                    "scope": "installed",
                    "records": parsed,
                    "scan_mode": (
                        "parsed_prefix"
                        if occurrences else "raw_absence"
                    ),
                })
            else:
                errors.append(
                    f"{error}; candidate bytes cannot be disambiguated"
                )
            continue
        files.append({
            "source": source,
            "scope": "installed",
            "records": records,
            "scan_mode": "parsed",
        })
    return files, errors, warnings


def scan_maplist(game: Path) -> tuple[list[int], list[str]]:
    path = game / "mpmaplist.txt"
    if not path.is_file():
        return [], []
    try:
        data = path.read_bytes()
    except OSError as error:
        return [], [f"{path}: {error}"]
    return [int(match) for match in ITEM_ATTRIBUTE_RE.findall(data)], []


def audit(game: Path, candidate: int) -> dict[str, object]:
    if candidate < 0 or candidate > 0xFFFFFFFF:
        raise ValueError("candidate ItemID must fit an unsigned 32-bit value")

    commercial, commercial_errors, commercial_warnings = scan_commercial(
        game, candidate
    )
    installed, installed_errors, installed_warnings = scan_loose_missions(
        game, candidate
    )
    maplist_ids, maplist_errors = scan_maplist(game)
    files = commercial + installed
    collisions: list[dict[str, object]] = []
    kinds: Counter[str] = Counter()
    total_records = 0
    for item_file in files:
        records = item_file["records"]
        total_records += len(records)
        for record in records:
            kinds[str(record["kind"])] += 1
            if record["item_id"] != candidate:
                continue
            collisions.append({
                "scope": item_file["scope"],
                "source": item_file["source"],
                **record,
            })

    maplist_collisions = sum(1 for item_id in maplist_ids if item_id == candidate)
    errors = commercial_errors + installed_errors + maplist_errors
    if len(commercial) != 80:
        errors.append(
            f"commercial items.dat count is {len(commercial)}, expected 80"
        )

    return {
        "ok": not errors and not collisions and maplist_collisions == 0,
        "candidate_item_id": candidate,
        "candidate_serialized_le": struct.pack("<I", candidate).hex(" "),
        "commercial_files": len(commercial),
        "installed_mission_files": len(installed),
        "records": total_records,
        "record_kinds": dict(sorted(kinds.items())),
        "mpmaplist_item_declarations": len(maplist_ids),
        "mpmaplist_collisions": maplist_collisions,
        "collisions": collisions,
        "warnings": commercial_warnings + installed_warnings,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--candidate", type=int, default=359)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()

    report = audit(arguments.game.resolve(), arguments.candidate)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
