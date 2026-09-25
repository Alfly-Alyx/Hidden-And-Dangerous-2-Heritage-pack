#!/usr/bin/env python3
"""Read-only Normandy 2 vestige audit; no actor, route or signal is generated."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from audit_norway_guard_chain import exact_checkpoint
from build_reconstruction_lab import script_closure
from build_reconstruction_variant import ArchiveSources, digest, typed_names
from mission_closure_audit import MOVE_RE, transitive_scripts
from objective_audit import split_comments
from script_binding_audit import normalize_script_name, parse_bindings


def signal_facts(text: str, number: int) -> dict:
    """Report literal single-block mappings, without interpreting nested code."""
    active = split_comments(text)[0]
    start = rf'\bOnSignal\s*\(\s*{number}\s*\)'
    bodies = re.findall(start + r'\s*\{([^{}]*)\}', active, re.I | re.S)
    return {
        'handler_count': len(re.findall(start, active, re.I)),
        'simple_handler_count': len(bodies),
        'literal_frame_targets': [name for body in bodies for name in re.findall(
            r'\bFRM_FindFrame\s*\(\s*\w+\s*,\s*"([^"]+)"\s*\)', body, re.I)],
        'loads_shared_value_25': bool(re.search(
            r'\b_?LoadGameValue\s*\(\s*25\s*\)', active, re.I)),
    }


def movement_facts(text: str, checkpoints: bytes) -> dict:
    active, comments = split_comments(text)
    names = sorted(set(MOVE_RE.findall(active)), key=str.casefold)
    empty_move = r'\bHUMAN_Move\s*\(\s*""\s*\)'
    return {
        'named_checkpoints': {n: exact_checkpoint(checkpoints, n) for n in names},
        'active_empty_moves': len(re.findall(empty_move, active, re.I)),
        'commented_empty_moves': len(re.findall(empty_move, comments, re.I)),
        # An empty Drive at speed zero is a commercial stop, not a missing path.
        'active_vehicle_stops': len(re.findall(
            r'\bHUMAN_Drive\s*\(\s*""\s*,\s*0\s*\)', active, re.I)),
    }


def analyze(files: dict[str, bytes]) -> dict:
    mission = 'normandy2'
    closure = script_closure(files, mission)
    bindings = parse_bindings(files[f'missions/{mission}/scripts.dta'])
    texts = {e.rsplit('/', 1)[1]: raw.decode('cp1252', errors='replace')
             for e, raw in files.items() if e.startswith(f'scripts/{mission}/')}
    active = {n: split_comments(t)[0] for n, t in texts.items()}
    roots = {normalize_script_name(v) for _, v in bindings if v.strip()}
    used, missing = transitive_scripts(roots, active)
    if missing:
        raise ValueError('Incomplete script closure')
    actors = typed_names(files[f'missions/{mission}/actors.bin'], 'actors.bin')
    scene = typed_names(files[f'missions/{mission}/scene2.bin'], 'scene2.bin')
    checkpoints = files[f'missions/{mission}/check2.bin']

    def script_info(name):
        if name not in texts:
            raise ValueError(f'Missing reviewed source: {name}')
        return {'script': name, 'reachable_script': name in used,
                'bound_owners': [o for o, v in bindings if normalize_script_name(v) == name]}

    sender_name = 'r_n2_fake_defence_sender.scr'
    sender_info = script_info(sender_name)
    sender = active[sender_name]
    sender_info.update({
        'proximity_target_variables': re.findall(
            r'\b_FrameInRange\s*\(\s*(\w+)\s*\)\s*<\s*4\b', sender, re.I),
        'saves_shared_value_25': bool(re.search(
            r'\bSaveGameValue\s*\(\s*25\s*,', sender, re.I)),
        'literal_signal25_destinations': re.findall(
            r'\bSendSignal\s*\(\s*(\w+)\s*,\s*25\s*\)', sender, re.I),
    })
    receivers = []
    for i in range(1, 6):
        name = f'r_n2_ally{i}_end.scr'
        receivers.append({'actor': f'Ally_{i}', **script_info(name),
                          **signal_facts(texts[name], 25)})
    waves = []
    for family in (1, 2):
        for i in range(1, 6):
            actor = f'wave{family}_{i}'
            name = f'r_n2_{actor}.scr'
            waves.append({'actor': actor, 'actor_present': actor in actors,
                          **script_info(name), **movement_facts(texts[name], checkpoints)})
    return {
        'status': 'read_only_structural_audit', 'runtime_status': 'pending',
        'installed_into_game': False, 'automatic_activation_authorized': False,
        'script_closure': closure, 'sender': sender_info, 'signal25_receivers': receivers,
        'waves': waves,
        'active_placeholders': {
            'red31': {**script_info('r_n2_red_31.scr'),
                      'actor_present': 'red_31' in actors,
                      'turn_frame_present': 'dummy_red31_turn' in scene,
                      **movement_facts(texts['r_n2_red_31.scr'], checkpoints)},
            'tank_driver': {**script_info('r_n2_ger_tank_driver.scr'),
                            'balcony_frame_present': 'la_n2_balkon' in scene},
            'blue_turn_to_ally1': [
                {**script_info(n), 'actor_present': f'blue_{i}' in actors}
                for i in range(1, 18) for n in [f'r_n2_blue_{i}.scr']
                if n in texts and re.search(
                    r'FRM_FindFrame\s*\(\s*turn\s*,\s*"Ally_1"', active[n], re.I)],
        },
        'limits': ['Literal dependencies are not an engine execution trace',
                   'Checkpoint names do not prove geometry or traversability',
                   'Signal 25 is not interpreted as a generic shared-value protocol',
                   'Nested handler bodies are explicitly not interpreted'],
    }


def audit(sources) -> dict:
    wanted = {f'missions/normandy2/{f}' for f in
              ('scripts.dta', 'actors.bin', 'scene2.bin', 'check2.bin')}
    names = [e for e in sources.mission_entries('normandy2')
             if e in wanted or e.startswith('scripts/') and e.endswith('.scr')]
    files, provenance = {}, {}
    for name in names:
        archive, raw = sources.read(name)
        files[name] = raw
        provenance[name] = {'archive': archive, 'size': len(raw), 'sha256': digest(raw)}
    result = analyze(files)
    result['source_files'] = provenance
    result['excluded_loose_overrides'] = {
        e: p for e, p in getattr(sources, 'excluded_loose_overrides', {}).items() if e in files}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', required=True, type=Path)
    parser.add_argument('--archives-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        with ArchiveSources(args.game, archives_only=args.archives_only) as sources:
            print(json.dumps(audit(sources), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f'Normandy 2 audit refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
