#!/usr/bin/env python3
"""Read-only evidence audit for Norway's missing guards and dormant sender.

This reports structural facts, not game-engine behavior. It neither generates
actors nor repairs scripts. Commercial bytes are never written by this tool.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from build_reconstruction_lab import script_closure
from build_reconstruction_variant import ArchiveSources, digest, typed_names
from mission_closure_audit import MOVE_RE, transitive_scripts
from objective_audit import split_comments
from script_binding_audit import normalize_script_name, parse_bindings


def exact_checkpoint(raw: bytes, name: str) -> bool:
    """NUL-terminated, token-bounded name evidence; no geometry inference."""
    return re.search(rb"(?<![A-Za-z0-9_])" + re.escape(name.encode("ascii")) + b"\0",
                     raw, re.I) is not None


def sender_facts(text: str) -> dict:
    active = split_comments(text)[0]
    loop = re.search(r"\blabel\s+Newer_ending_sending\s*:(.*?)"
                     r"\bgoto\s+Newer_ending_sending\s*;", active, re.I | re.S)
    if not loop:
        raise ValueError("The reviewed sender loop is absent or has changed")
    delays = lambda body: re.findall(r"\bdelay\s*\(\s*([^()]*)\s*\)", body, re.I)
    return {
        "initial_delay_arguments": delays(active[:loop.start()]),
        "loop_delay_arguments": delays(loop.group(1)),
        "waiter_assigned": bool(re.search(r"\bwaiter\s*=", loop.group(1), re.I)),
        "waiter_delay_used": bool(re.search(r"\bdelay\s*\(\s*waiter\s*\)", loop.group(1), re.I)),
        "active_guard_numbers": [int(n) for n in re.findall(
            r"\bIf\s*\(\s*what_soldier\s*==\s*(\d+)\s*\)\s*\{\s*SendSignal\b",
            loop.group(1), re.I)],
        "engine_iteration_timing": "not_measured",
    }


def analyze(files: dict[str, bytes]) -> dict:
    closure = script_closure(files, "norway")  # Reject unknown/dynamic dependencies.
    bindings = parse_bindings(files["missions/norway/scripts.dta"])
    texts = {e.rsplit("/", 1)[1]: split_comments(raw.decode("cp1252", errors="replace"))[0]
             for e, raw in files.items() if e.startswith("scripts/norway/") and e.endswith(".scr")}
    roots = {normalize_script_name(script) for _, script in bindings if script.strip()}
    used, missing = transitive_scripts(roots, texts)
    if missing:
        raise ValueError("Incomplete script closure")
    actors = typed_names(files["missions/norway/actors.bin"], "actors.bin")
    scene = typed_names(files["missions/norway/scene2.bin"], "scene2.bin")
    checkpoint_data = files["missions/norway/check2.bin"]
    guards = []
    for number in range(1, 19):
        actor = f"tirpic_guard_{number}"
        script = f"r_nor_tirpic{number}.scr"
        text = texts.get(script, "")
        paths = sorted(set(MOVE_RE.findall(text)), key=str.casefold)
        guards.append({
            "number": number, "actor": actor, "actor_present": actor in actors,
            "bound_scripts": [s for a, s in bindings if a.casefold() == actor],
            "script_present": script in texts,
            "reachable_script": script in used,
            "checkpoints": {p: exact_checkpoint(checkpoint_data, p) for p in paths},
            "literal_signal_handlers": [int(n) for n in re.findall(r"\bOnSignal\s*\(\s*(\d+)\s*\)", text, re.I)],
        })
    sender = "r_nor_action_sender.scr"
    if sender not in texts:
        raise ValueError("Missing sender source")
    return {
        "status": "read_only_structural_audit", "runtime_status": "pending",
        "installed_into_game": False, "script_closure": closure, "guards": guards,
        "look_frames": {n: n in scene for n in ("dummy_see1", "dummy_see2")},
        "sender": {
            "bound_owners": [a for a, s in bindings if normalize_script_name(s) == sender],
            "reachable_script": sender in used, **sender_facts(texts[sender]),
        },
        "limits": ["No proof of actor identity or equipment from checkpoint names",
                   "Static dependency reachability is not a trace of engine execution",
                   "No activation or automatically inferred owner"],
    }


def audit(sources) -> dict:
    names = [e for e in sources.mission_entries("norway")
             if (e.startswith("scripts/") and e.endswith(".scr"))
             or e in {f"missions/norway/{f}" for f in
                      ("scripts.dta", "actors.bin", "scene2.bin", "check2.bin")}]
    files, provenance = {}, {}
    for name in names:
        archive, raw = sources.read(name)
        files[name] = raw
        provenance[name] = {"archive": archive, "size": len(raw), "sha256": digest(raw)}
    result = analyze(files)
    result["source_files"] = provenance
    result["excluded_loose_overrides"] = {
        e: p for e, p in getattr(sources, "excluded_loose_overrides", {}).items() if e in files}
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--archives-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        with ArchiveSources(args.game, archives_only=args.archives_only) as sources:
            print(json.dumps(audit(sources), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"Norway audit refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
