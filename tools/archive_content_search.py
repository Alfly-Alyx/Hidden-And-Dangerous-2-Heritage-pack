#!/usr/bin/env python3
"""Search decoded H&D2 DTA entries for lost-content identifiers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dta_archive import DtaArchive, matches


def encoded_needles(value: str) -> tuple[bytes, bytes]:
    return value.lower().encode("cp1252"), value.lower().encode("utf-16le")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, nargs="+")
    parser.add_argument("--term", action="append", required=True)
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--max-entry-size", type=int, default=16 * 1024 * 1024)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()

    terms = {term: encoded_needles(term) for term in arguments.term}
    found_entries: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    scanned = 0

    for archive_path in arguments.archive:
        with DtaArchive(archive_path) as archive:
            for entry in archive.entries:
                if not matches(entry.name, arguments.include):
                    continue
                if entry.size > arguments.max_entry_size:
                    continue
                if entry.name.lower().endswith((".wav", ".ogg")):
                    continue
                try:
                    data = archive.read(entry).lower()
                except ValueError as error:
                    errors.append({
                        "archive": archive_path.name,
                        "entry": entry.name,
                        "error": str(error),
                    })
                    continue
                scanned += 1
                found = [
                    term
                    for term, variants in terms.items()
                    if term.lower() in entry.name.lower()
                    or any(needle in data for needle in variants)
                ]
                if found:
                    found_entries.append({
                        "archive": archive_path.name,
                        "entry": entry.name,
                        "size": entry.size,
                        "terms": found,
                    })

    result = {"scanned": scanned, "matches": found_entries, "errors": errors}
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded + "\n", encoding="utf-8")
    if arguments.json:
        print(encoded)
    else:
        print(
            f"{scanned} entries scanned; "
            f"{len(found_entries)} matches; {len(errors)} errors"
        )
        for match in found_entries:
            print(
                f"{match['archive']} | {match['entry']} | "
                f"{match['size']} | {', '.join(match['terms'])}"
            )
        for error in errors:
            print(f"ERROR | {error['archive']} | {error['entry']} | {error['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())