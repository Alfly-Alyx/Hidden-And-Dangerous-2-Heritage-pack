#!/usr/bin/env python3
"""Read-only Co_Burgundy3 closure, Maquis routing and model-node evidence.

No scene, script, model, registry or game file is written. Structural presence
does not validate engine frame lookup, particles, alarms or network authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct
import sys

from audit_norway_guard_chain import exact_checkpoint
from build_burgundy_ambient_patch import record_name, scene_group
from build_reconstruction_lab import script_closure
from build_reconstruction_variant import ARCHIVES, ArchiveSources, digest
from menu_gui_audit import parse_4ds_nodes
from mission_closure_audit import FRAME_RE, MOVE_RE, transitive_scripts
from objective_audit import direct, split_comments
from script_binding_audit import normalize_script_name, parse_bindings

MODEL_ENTRY = 'models/la_bu3_fuelstorage.4ds'
MODEL_SHA = 'b24bdeb7b0af5b8dbe4e0bb95a904b2cec5dff1fa78ff717c64f7ef0802a0385'
INSTANCE = 'la_bu3_fuelstorage_01'
BARRELS = ('f_Sud34', 'f_Sud30', 'F_SudB07', 'F_SudB14', 'F_SudB19', 'F_SudB27')


def model_instance(raw: bytes, name: str) -> str:
    """Require a real typed model instance, not an LMAP or parent reference."""
    matches = [r for r in scene_group(raw).children
               if r.kind == 0x4010 and record_name(r) == name.casefold()
               and direct(r, 0x4011)]
    if len(matches) != 1:
        raise ValueError('Expected one typed model instance')
    record = matches[0]
    types, models = direct(record, 0x4011), direct(record, 0x2012)
    if len(types) != 1 or types[0].payload != struct.pack('<I', 9) or len(models) != 1:
        raise ValueError('Expected a model instance of type 9 with one resource')
    value = models[0].payload
    if not value.endswith(b'\0') or not value[:-1] or b'\0' in value[:-1]:
        raise ValueError('Invalid model resource name')
    resource = value[:-1].decode('cp1252').casefold()
    if '/' in resource or '\\' in resource or ':' in resource or resource in ('.', '..'):
        raise ValueError('Non-local model resource requires separate review')
    return resource


def node_evidence(parsed: dict, names: tuple[str, ...]) -> list[dict]:
    """Exact node identity plus a valid ancestry, never substring matching."""
    nodes = parsed['nodes']
    by_id = {n['index']: n for n in nodes}
    if len(by_id) != len(nodes) or 0 in by_id:
        raise ValueError('Ambiguous model node indices')
    result = []
    for name in names:
        matches = [n for n in nodes if n['name'].casefold() == name.casefold()]
        if len(matches) != 1:
            raise ValueError(f'Missing or ambiguous model node: {name}')
        node, chain, seen = matches[0], [], set()
        current = node['index']
        while current:
            if current in seen or current not in by_id:
                raise ValueError(f'Invalid model ancestry: {name}')
            seen.add(current)
            parent = by_id[current]
            chain.append(parent['name'])
            current = parent['parent_id']
        result.append({'name': node['name'], 'index': node['index'],
                       'parent_id': node['parent_id'], 'frame_type': node['frame_type'],
                       'ancestry_child_first': chain})
    return result


def signal_facts(texts: dict[str, str]) -> dict:
    active = {n: split_comments(t)[0] for n, t in texts.items()}
    maquis = active['bur3_maquis01.scr']
    explosion = active['bur3_vybuch.scr']
    return {
        'maquis_active_signal1_handler_count': len(re.findall(r'\bOnSignal\s*\(\s*1\s*\)', maquis, re.I)),
        'maquis_alarm_goto_destroy': bool(re.search(
            r'\bOnAlarm\s*\(\s*\)\s*\{\s*goto\s+DESTROY\s*;\s*\}', maquis, re.I)),
        'maquis_literal_frame_reference_scripts': sorted(
            n for n, t in active.items() if 'maquis01' in {v.casefold() for v in FRAME_RE.findall(t)}),
        'signal_pistol_scripts': sorted(n for n, t in active.items()
                                       if re.search(r'\b_SignalPistolFired\s*\(', t, re.I)),
        'explosion_active_signal1_handler_count': len(re.findall(
            r'\bOnSignal\s*\(\s*1\s*\)', explosion, re.I)),
        'explosion_signal1_disabled_in_script': bool(re.search(
            r'\bDisableSignals\s*\(\s*true\s*\)', explosion, re.I)),
        'limits': ['Literal references only; no dynamic alias or engine event inference',
                   'No alarm re-entry or network execution trace'],
    }


def fuel_model(sources) -> tuple[str, bytes]:
    """Read just the reviewed Sabre resource; do not widen variant source paths."""
    loose = sources.game.joinpath(*MODEL_ENTRY.split('/'))
    if loose.exists():
        if not sources.archives_only:
            raise ValueError(f'Loose override must be reviewed separately: {MODEL_ENTRY}')
        raw = loose.read_bytes()
        sources.excluded_loose_overrides[MODEL_ENTRY] = {'size': len(raw), 'sha256': digest(raw)}
    if ('PatchX01.dta' in sources.index
            and MODEL_ENTRY in sources.index['PatchX01.dta'][1]):
        raise ValueError('Unreviewed PatchX01 model override')
    found = None
    for name in ARCHIVES:
        archive, entries = sources.index[name]
        matches = entries.get(MODEL_ENTRY, [])
        if len(matches) > 1:
            raise ValueError('Ambiguous model archive entry')
        if matches:
            found = (name, archive, matches[0])
    if found is None or found[0] != 'SabreSquadron.dta':
        raise ValueError('Reviewed Sabre model is absent')
    name, archive, entry = found
    raw = archive.read(entry)
    if len(raw) != 54457 or digest(raw) != MODEL_SHA:
        raise ValueError('Reviewed Sabre model has changed')
    return name, raw


def audit(sources) -> dict:
    mission = 'co_burgundy3'
    wanted = {f'missions/{mission}/{n}' for n in
              ('mpscripts.dta', 'actors.bin', 'scene2.bin', 'scene.4ds', 'check2.bin')}
    files, provenance = {}, {}
    for name in sources.mission_entries(mission):
        if name in wanted or name.startswith('scripts/') and name.endswith('.scr'):
            archive, raw = sources.read(name)
            files[name] = raw
            provenance[name] = {'archive': archive, 'size': len(raw), 'sha256': digest(raw)}
    closure = script_closure(files, mission, 'mpscripts.dta')
    bindings = parse_bindings(files[f'missions/{mission}/mpscripts.dta'])
    texts = {n.rsplit('/', 1)[1]: r.decode('cp1252', errors='replace')
             for n, r in files.items() if n.startswith('scripts/')}
    active = {n: split_comments(t)[0] for n, t in texts.items()}
    used, missing = transitive_scripts(
        {normalize_script_name(v) for _, v in bindings if v.strip()}, active)
    if missing:
        raise ValueError('Incomplete script closure')
    moves = [v for n in used for v in MOVE_RE.findall(active[n])]
    paths = sorted(set(moves), key=str.casefold)
    references = {v.casefold() for t in active.values() for v in FRAME_RE.findall(t)}
    scene_nodes = parse_4ds_nodes(files[f'missions/{mission}/scene.4ds'])
    names = tuple(n['name'] for n in scene_nodes['nodes'] if n['name'].casefold() in references)
    geometry = node_evidence(scene_nodes, names)
    resource = model_instance(files[f'missions/{mission}/actors.bin'], INSTANCE)
    if resource != 'la_bu3_fuelstorage':
        raise ValueError('Fuel depot instance points to a different model')
    archive, raw = fuel_model(sources)
    provenance[MODEL_ENTRY] = {'archive': archive, 'size': len(raw), 'sha256': digest(raw)}
    barrels = node_evidence(parse_4ds_nodes(raw), BARRELS)
    return {
        'status': 'read_only_structural_audit', 'runtime_status': 'pending',
        'installed_into_game': False, 'automatic_activation_authorized': False,
        'registry': 'mpscripts.dta', 'binding_count': len(bindings), 'script_closure': closure,
        'unreachable_scripts': sorted(set(texts) - used),
        'movement_call_count': len(moves), 'distinct_checkpoint_count': len(paths),
        'missing_checkpoint_names': [n for n in paths
            if not exact_checkpoint(files[f'missions/{mission}/check2.bin'], n)],
        'signal_facts': signal_facts(texts), 'direct_scene_geometry': geometry,
        'fuel_instance': INSTANCE, 'fuel_model': MODEL_ENTRY, 'fuel_model_nodes': barrels,
        'source_files': provenance,
        'excluded_loose_overrides': {n: p for n, p in sources.excluded_loose_overrides.items()
                                     if n in provenance},
        'limits': ['Named checkpoints do not establish traversability',
                   'Model ancestry does not establish engine resolution or world coordinates',
                   'No objective fix, extra signal, actor or particle is created'],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--archives-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        with ArchiveSources(args.game, archives_only=args.archives_only) as sources:
            print(json.dumps(audit(sources), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f'Co_Burgundy3 audit refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
