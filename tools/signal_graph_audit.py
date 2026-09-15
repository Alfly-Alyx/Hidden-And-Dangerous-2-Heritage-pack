#!/usr/bin/env python3
"""Build a conservative actor/script signal graph for commercial H&D2 missions."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from objective_audit import split_comments
from script_binding_audit import (
    MISSION_ARCHIVES,
    SCRIPT_ARCHIVES,
    effective_entries,
    normalize_script_name,
    parse_bindings,
)

FRAME_RE = re.compile(
    r'\bFRM_FindFrame\s*\(\s*([A-Za-z_]\w*)\s*,\s*"([^"]+)"', re.I)
SEND_RE = re.compile(
    r'\bSendSignal\s*\(\s*([^,\r\n]+?)\s*,\s*(-?\d+)\s*\)', re.I)
HANDLER_RE = re.compile(
    r'\bOnSignal\s*\(\s*(-?\d+)\s*\)|\b_SignalReceived\s*\(\s*(-?\d+)\s*\)',
    re.I,
)
ASSIGN_RE = re.compile(
    r'\bScriptAssign\s*\(\s*([A-Za-z_]\w*)\s*,\s*"([^"]*)"', re.I)
INCLUDE_RE = re.compile(r'^\s*#include\s+"([^"]+\.scr)"', re.I | re.M)


def active_text(data: bytes) -> str:
    return split_comments(data.decode("cp1252", errors="replace"))[0]


def frame_map(text: str) -> dict[str, str]:
    return {match.group(1).lower(): match.group(2).lower()
            for match in FRAME_RE.finditer(text)}


def literal_handlers(text: str) -> set[int]:
    values = set()
    for match in HANDLER_RE.finditer(text):
        values.add(int(match.group(1) or match.group(2)))
    return values


def effective_handlers(
    script: str,
    texts: dict[str, str],
    cache: dict[str, set[int]],
    visiting: set[str] | None = None,
) -> set[int]:
    """Return handlers declared by a script and its recursive includes."""
    if script in cache:
        return cache[script]
    if visiting is None:
        visiting = set()
    if script in visiting:
        return set()
    text = texts.get(script)
    if text is None:
        return set()
    visiting.add(script)
    values = literal_handlers(text)
    for include in INCLUDE_RE.findall(text):
        target = normalize_script_name(include)
        if target:
            values.update(effective_handlers(target, texts, cache, visiting))
    visiting.remove(script)
    cache[script] = values
    return values


def target_actor(expression: str, frames: dict[str, str]) -> str | None:
    value = expression.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1].lower()
    return frames.get(value.lower())


def build(game: Path) -> dict:
    registry_entries = effective_entries(
        game, MISSION_ARCHIVES,
        lambda name: name.startswith("missions/")
        and name.endswith(("/scripts.dta", "/mpscripts.dta")),
    )
    script_entries = effective_entries(
        game, SCRIPT_ARCHIVES,
        lambda name: name.startswith("scripts/") and name.endswith(".scr"),
    )

    registries = defaultdict(list)
    for name, (_, data) in registry_entries.items():
        parts = name.split("/")
        if len(parts) >= 3:
            registries[parts[1]].extend(parse_bindings(data))

    mission_rows = []
    totals = defaultdict(int)
    for mission, bindings in sorted(registries.items()):
        prefix = f"scripts/{mission}/"
        texts = {
            name[len(prefix):]: active_text(data)
            for name, (_, data) in script_entries.items()
            if name.startswith(prefix)
        }
        actors_to_scripts = defaultdict(set)
        used_scripts = set()
        for actor, script in bindings:
            normalized = normalize_script_name(script)
            if normalized:
                actors_to_scripts[actor.lower()].add(normalized)
                used_scripts.add(normalized)

        # Follow official includes and runtime ScriptAssign branches from scripts
        # that are reachable through a mission registry.
        changed = True
        while changed:
            changed = False
            for script in list(used_scripts):
                text = texts.get(script)
                if text is None:
                    continue
                frames = frame_map(text)
                for include in INCLUDE_RE.findall(text):
                    target = normalize_script_name(include)
                    if target and target not in used_scripts:
                        used_scripts.add(target)
                        changed = True
                for match in ASSIGN_RE.finditer(text):
                    target_script = normalize_script_name(match.group(2))
                    actor = frames.get(match.group(1).lower())
                    if not actor or not target_script:
                        continue
                    if target_script not in actors_to_scripts[actor]:
                        actors_to_scripts[actor].add(target_script)
                        changed = True
                    if target_script not in used_scripts:
                        used_scripts.add(target_script)
                        changed = True

        edges = []
        for script in sorted(used_scripts):
            text = texts.get(script)
            if text is None:
                continue
            frames = frame_map(text)
            source_actors = sorted(
                actor for actor, scripts in actors_to_scripts.items()
                if script in scripts
            )
            for match in SEND_RE.finditer(text):
                actor = target_actor(match.group(1), frames)
                if not actor:
                    continue
                edges.append({
                    "source_script": script,
                    "source_actors": source_actors,
                    "target_actor": actor,
                    "signal": int(match.group(2)),
                })

        mismatches = []
        handler_cache = {}
        for edge in edges:
            target_scripts = sorted(actors_to_scripts.get(edge["target_actor"], set()))
            existing = [script for script in target_scripts if script in texts]
            if not existing:
                continue
            handlers = sorted(set().union(*(
                effective_handlers(script, texts, handler_cache)
                for script in existing
            )))
            if edge["signal"] in handlers:
                continue
            mismatches.append({
                **edge,
                "target_scripts": existing,
                "handled_signals": handlers,
                "reason": "target_has_no_literal_signal_handler"
                if not handlers else "sent_signal_not_handled",
            })

        # Collapse exact duplicate calls while retaining distinct senders.
        unique = {}
        for item in mismatches:
            key = (item["source_script"], item["target_actor"], item["signal"],
                   tuple(item["target_scripts"]))
            unique[key] = item
        mismatches = sorted(unique.values(), key=lambda item: (
            item["target_actor"], item["signal"], item["source_script"]))
        totals["missions"] += 1
        totals["used_scripts"] += len(used_scripts)
        totals["resolved_signal_calls"] += len(edges)
        totals["mismatched_signal_calls"] += len(mismatches)
        if mismatches:
            mission_rows.append({
                "mission": mission,
                "used_script_count": len(used_scripts),
                "resolved_signal_call_count": len(edges),
                "mismatches": mismatches,
            })

    return {
        "game": str(game),
        "scope": dict(totals),
        "missions": mission_rows,
    }


def markdown(report: dict) -> str:
    scope = report["scope"]
    lines = [
        "# Audit du graphe de signaux",
        "",
        "Analyse statique conservative des scripts effectivement reliés, y compris "
        "leurs modules inclus. Un écart reste un candidat à vérifier : certains "
        "objets du moteur peuvent traiter un signal sans gestionnaire de script littéral.",
        "",
        f"- {scope['missions']} missions ou variantes ;",
        f"- {scope['used_scripts']} scripts atteignables ;",
        f"- {scope['resolved_signal_calls']} envois résolus vers un acteur ;",
        f"- {scope['mismatched_signal_calls']} écarts à examiner.",
        "",
        "| Mission | Émetteur | Cible | Signal | Script cible | Signaux gérés | Type |",
        "|---|---|---|---:|---|---|---|",
    ]
    for mission in report["missions"]:
        for item in mission["mismatches"]:
            handled = ", ".join(map(str, item["handled_signals"])) or "—"
            lines.append(
                f"| {mission['mission']} | {item['source_script']} | "
                f"{item['target_actor']} | {item['signal']} | "
                f"{', '.join(item['target_scripts'])} | {handled} | "
                f"{item['reason']} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    arguments = parser.parse_args()
    report = build(arguments.game)
    arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
    arguments.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    arguments.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    arguments.markdown_output.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["scope"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())