#!/usr/bin/env python3
"""Verify that the documented H&D2 candidate table matches the commercial audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import full_game_audit


DOCUMENT = Path("docs/AUDIT_COMPLET_JEU.md")


def candidate_rows(markdown: str) -> list[str]:
    rows: list[str] = []
    in_table = False
    for line in markdown.splitlines():
        if line.startswith("| Mission | Obj. déclarés |"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|---"):
            continue
        if not line.startswith("|"):
            break
        rows.append(line.rstrip())
    return rows


def audit(root: Path, report: dict[str, object]) -> dict[str, object]:
    root = root.resolve()
    document_path = root / DOCUMENT
    errors: list[str] = []
    if not document_path.is_file():
        return {
            "ok": False,
            "expected_rows": 0,
            "documented_rows": 0,
            "errors": [f"Missing document: {DOCUMENT.as_posix()}"],
        }
    expected = candidate_rows(full_game_audit.markdown(report))
    documented = candidate_rows(
        document_path.read_text(encoding="utf-8-sig", errors="strict")
    )
    expected_set = set(expected)
    documented_set = set(documented)
    missing = sorted(expected_set - documented_set)
    stale = sorted(documented_set - expected_set)
    if len(expected) != len(expected_set):
        errors.append("Generated candidate table contains duplicate rows")
    if len(documented) != len(documented_set):
        errors.append("Documented candidate table contains duplicate rows")
    if missing:
        errors.append(f"Missing or changed documented rows: {len(missing)}")
    if stale:
        errors.append(f"Stale documented rows: {len(stale)}")

    documented_text = document_path.read_text(
        encoding="utf-8-sig", errors="strict"
    )
    required_sections = (
        "## Conclusions manuelles sur les derniers scripts orphelins",
        "## Règle de validation",
    )
    missing_sections = [
        section for section in required_sections if section not in documented_text
    ]
    if missing_sections:
        errors.append("Missing closure sections: " + ", ".join(missing_sections))

    return {
        "ok": not errors,
        "expected_rows": len(expected),
        "documented_rows": len(documented),
        "missing_rows": missing,
        "stale_rows": stale,
        "missing_sections": missing_sections,
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
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--game", type=Path)
    source.add_argument("--audit-json", type=Path)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    if arguments.audit_json:
        report = json.loads(
            arguments.audit_json.read_text(encoding="utf-8-sig")
        )
    else:
        report = full_game_audit.build(arguments.game.resolve())
    result = audit(arguments.root, report)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
