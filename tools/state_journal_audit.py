#!/usr/bin/env python3
"""Audit an H&D2 Heritage Pack restoration journal without changing it."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath


def decode(value: str) -> str:
    return base64.b64decode(value, validate=True).decode("utf-8")


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            result.update(block)
    return result.hexdigest().upper()


def safe_target(root: Path, relative: str) -> Path:
    windows = PureWindowsPath(relative)
    if (not relative.strip() or windows.is_absolute() or windows.drive
            or ".." in windows.parts):
        raise ValueError(f"unsafe tracked path: {relative!r}")
    target = root.joinpath(*windows.parts).resolve()
    resolved_root = root.resolve()
    try:
        target.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"tracked path outside root: {relative!r}") from exc
    return target


def audit(path: Path, verify_hashes: bool) -> dict[str, object]:
    if not path.is_file():
        return {
            "present": False,
            "path": str(path),
            "structural_ok": True,
            "sealed": False,
            "errors": [],
        }

    errors: list[str] = []
    game_path: Path | None = None
    backup_root: Path | None = None
    format_version: str | None = None
    changes: list[dict[str, object]] = []
    by_path: dict[str, dict[str, object]] = {}
    profile_unlocks: list[dict[str, object]] = []
    graphics_records = 0
    update_records = 0

    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        return {
            "present": True,
            "path": str(path),
            "structural_ok": False,
            "sealed": False,
            "errors": [str(exc)],
        }

    for number, line in enumerate(lines, 1):
        fields = line.split("\t")
        if not fields or not fields[0]:
            continue
        kind = fields[0]
        try:
            if kind == "FORMAT" and len(fields) >= 2:
                format_version = fields[1]
            elif kind == "GAME" and len(fields) >= 2:
                game_path = Path(decode(fields[1]))
            elif kind == "BACKUP" and len(fields) >= 2:
                backup_root = Path(decode(fields[1]))
            elif kind in ("CREATED", "REPLACED") and len(fields) >= 2:
                relative = decode(fields[1])
                key = str(PureWindowsPath(relative)).casefold()
                if key in by_path:
                    errors.append(f"line {number}: duplicate tracked path {relative}")
                    continue
                change = {
                    "relative": relative,
                    "created": kind == "CREATED",
                    "sha256": None,
                }
                changes.append(change)
                by_path[key] = change
            elif kind == "HASH" and len(fields) >= 3:
                relative = decode(fields[1])
                key = str(PureWindowsPath(relative)).casefold()
                change = by_path.get(key)
                if change is None:
                    errors.append(f"line {number}: hash without tracked path {relative}")
                elif not all(character in "0123456789abcdefABCDEF" for character in fields[2]) \
                        or len(fields[2]) != 64:
                    errors.append(f"line {number}: invalid SHA-256 for {relative}")
                else:
                    change["sha256"] = fields[2].upper()
            elif kind == "PROFILE_UNLOCK" and len(fields) >= 5:
                profile_unlocks.append({
                    "relative": decode(fields[1]),
                    "base_bytes": len(base64.b64decode(fields[2], validate=True)),
                    "sabre_bytes": len(base64.b64decode(fields[3], validate=True)),
                    "sha256": fields[4].upper(),
                })
            elif kind == "GRAPHICS" and len(fields) >= 4:
                original = base64.b64decode(fields[1], validate=True)
                installed = base64.b64decode(fields[2], validate=True)
                if len(original) < 35 or len(installed) < 35:
                    errors.append(f"line {number}: truncated graphics record")
                graphics_records += 1
            elif kind == "UPDATE":
                update_records += 1
        except (ValueError, UnicodeError) as exc:
            errors.append(f"line {number}: {exc}")

    if format_version != "1":
        errors.append(f"unsupported or absent format: {format_version!r}")
    if game_path is None:
        errors.append("game path is absent")
    if backup_root is None:
        errors.append("backup root is absent")

    missing_targets: list[str] = []
    missing_backups: list[str] = []
    unsafe_paths: list[str] = []
    missing_hashes: list[str] = []
    mismatched_hashes: list[str] = []
    verified_hashes = 0
    created_count = sum(bool(change["created"]) for change in changes)
    replaced_count = len(changes) - created_count

    if game_path is not None and backup_root is not None:
        data_root = path.parent.resolve()
        try:
            backup_root.resolve().relative_to(data_root)
        except ValueError:
            errors.append("backup root is outside the journal data directory")
        for change in changes:
            relative = str(change["relative"])
            try:
                target = safe_target(game_path, relative)
                backup = safe_target(backup_root / "files", relative)
            except ValueError:
                unsafe_paths.append(relative)
                continue
            if not target.is_file():
                missing_targets.append(relative)
            if not change["created"] and not backup.is_file():
                missing_backups.append(relative)
            expected = change["sha256"]
            if expected is None:
                missing_hashes.append(relative)
            elif verify_hashes and target.is_file():
                verified_hashes += 1
                if digest(target) != expected:
                    mismatched_hashes.append(relative)

        for item in profile_unlocks:
            relative = str(item["relative"])
            try:
                target = safe_target(game_path, relative)
            except ValueError:
                unsafe_paths.append(relative)
                continue
            item["current_present"] = target.is_file()
            item["current_matches_installed"] = (
                digest(target) == item["sha256"] if target.is_file() else False
            )
            if item["base_bytes"] != 16 or item["sabre_bytes"] != 16:
                errors.append(f"invalid saved campaign values for {relative}")

    structural_ok = not (
        errors or unsafe_paths or missing_targets or missing_backups
    )
    sealed = bool(changes) and not missing_hashes
    return {
        "present": True,
        "path": str(path),
        "format": format_version,
        "game": str(game_path) if game_path else None,
        "backup_root": str(backup_root) if backup_root else None,
        "changes": len(changes),
        "created": created_count,
        "replaced": replaced_count,
        "missing_targets": missing_targets,
        "missing_backups": missing_backups,
        "unsafe_paths": unsafe_paths,
        "missing_hashes": missing_hashes,
        "verified_hashes": verified_hashes,
        "mismatched_hashes": mismatched_hashes,
        "profile_unlocks": profile_unlocks,
        "graphics_records": graphics_records,
        "update_records": update_records,
        "structural_ok": structural_ok,
        "sealed": sealed,
        "errors": errors,
    }


def main() -> int:
    default_root = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "journal", nargs="?", type=Path,
        default=default_root / "HD2 Community Pack" / "state-v1.tsv",
    )
    parser.add_argument("--verify-hashes", action="store_true")
    parser.add_argument("--require-state", action="store_true")
    parser.add_argument("--require-sealed", action="store_true")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    report = audit(args.journal, args.verify_hashes)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({
        "present": report["present"],
        "structural_ok": report["structural_ok"],
        "changes": report.get("changes", 0),
        "missing_hashes": len(report.get("missing_hashes", [])),
        "verified_hashes": report.get("verified_hashes", 0),
        "mismatched_hashes": len(report.get("mismatched_hashes", [])),
        "sealed": report["sealed"],
    }, ensure_ascii=False))
    if args.require_state and not report["present"]:
        return 1
    if not report["structural_ok"]:
        return 1
    if args.require_sealed and not report["sealed"]:
        return 1
    if report.get("mismatched_hashes"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
