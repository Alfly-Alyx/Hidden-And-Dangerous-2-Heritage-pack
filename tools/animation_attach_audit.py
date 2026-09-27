#!/usr/bin/env python3
"""Private native attachment/restart/detach of Benelli and modern clips."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from ls3d_attach_oracle import AttachOracle, reference_sequence
from ls3d_math_oracle import DLL_SHA
from modern_animation import encode_5ds
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from build_benelli_fpv_lab import read_sources, MANIFEST, STATES
from benelli_fpv_rig_audit import read_hands, HAND_MODELS, HAND_PINS
from benelli_fpv_static import derive
from build_modern_animation_bank import compile_bank, CASES, ROOT


def op(clip, slot=0, weight=1, mode=0):
    return dict(clip=clip, slot=slot, weight=weight, mode=mode)


def invented(names):
    return encode_5ds({'provenance': 'MODERNE', 'runtime_status': 'pending', 'frame_end': 10,
        'tracks': [{'name': name, 'channels': {
            'rotation': {'frames': [0, 10], 'values': [[0,0,0,1], [0,1,0,0]]},
            'position': {'frames': [0,5,10], 'values': [[0,0,0], [1,2,3], [2,1,0]]},
            'scale': {'frames': [0], 'values': [[1,1,1]]}}} for name in names]})


def controls():
    clips = {'A': {'data': invented(['Root', 'Prop']), 'mode': 2},
             'B': {'data': invented(['Other']), 'mode': 1}}
    long_names = ['A'*60+f'{i:03d}' for i in range(128)]
    for kind in (9, 0):
        for names in ([], ['root'], ['Root', 'Prop'], ['Root', 'Root', 'Prop'], ['Root', 'Other']):
            for mode in range(4):
                yield names, clips, [op(None), op('A', 7, 1.5, mode), op('A', 7, .2, mode),
                    op('B', 3, .5), op(None, 7), op(None, 3), op(None, 3)], kind
        yield long_names, {'Long': {'data': invented(long_names), 'mode': 3}}, [op('Long'), op(None)], kind
    yield ['Root', 'Prop'], clips, [op('A', i, i/4) for i in range(8)]+[op(None, i) for i in range(8)], 9
    yield ['Root', 'Other'], clips, [op('A'), op('B'), op('A'), op(None)], 9


def check_receipt(row, names, clips, operations, kind=9):
    flags_true = ('native_attachment_sequence_match', 'native_target_descriptors_checked',
        'inputs_preserved', 'allocator_is_bounded_double', 'model_controller_preallocated',
        'clip_relocation_is_synthetic')
    flags_false = ('native_loader_executed', 'poses_or_events_evaluated', 'scene_loaded',
                   'library_loaded', 'game_started')
    if any(row.get(k) is not True for k in flags_true) or any(row.get(k) is not False for k in flags_false):
        raise ValueError('Incomplete native attachment receipt')
    expected = reference_sequence(names, clips, operations, kind)
    summaries = [{'slot': action['slot'], 'clip': action['clip'], 'owners': len(state['owners']),
        'allocated': state['allocated'], 'freed': state['freed'],
        'active_slots': sum(s['active'] for s in state['slots'])} for action, state in zip(operations, expected)]
    if row.get('operations') != summaries:
        raise ValueError('Native attachment operation receipt differs')
    for field, key in (('owner_allocations', 'allocated'), ('owner_releases', 'freed')):
        if type(row.get(field)) is not int or row[field] != expected[-1][key]:
            raise ValueError('Native attachment owner-count receipt differs')


def audit_cases(machine, cases, progress=None):
    totals = dict(sequences=0, operations=0, owner_allocations=0, owner_releases=0)
    for names, clips, operations, kind in cases:
        row = machine.sequence(names, clips, operations, kind)
        check_receipt(row, names, clips, operations, kind)
        totals['sequences'] += 1; totals['operations'] += len(operations)
        for field in ('owner_allocations', 'owner_releases'):
            totals[field] += row[field]
        if progress:
            progress(totals['sequences'])
    return totals


def bank_cases(names, raw_clips):
    if not isinstance(names, list) or len(set(names)) != len(names):
        raise ValueError('Ambiguous bank target names')
    if not isinstance(raw_clips, dict) or not 1 <= len(raw_clips) <= 9:
        raise ValueError('Invalid attachment bank')
    # This mode is an explicit fixture, NOT a claim about a loaded stock clip.
    clips = {name: {'data': raw, 'mode': 2} for name, raw in raw_clips.items()}
    for key, item in clips.items():
        for track in parse_5ds(item['data'])['tracks']:
            if track['name'] not in names:
                raise ValueError('Unbound exact bank target')
    for kind in (9, 0):
        for key in clips:
            for slot in range(8):
                yield names, {key: clips[key]}, [op(key, slot, .25), op(key, slot, 1.5, 1), op(None, slot)], kind
        operations = [op(key, index % 8, .5) for index, key in enumerate(clips)]
        operations += [op(None, index) for index in reversed(range(8))]
        yield names, clips, operations, kind


def audit(game, archives_only=False):
    machine = AttachOracle((game/'LS3DF.dll').read_bytes())
    synthetic = audit_cases(machine, controls())
    print('Checked synthetic attachment controls', file=sys.stderr, flush=True)
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    sources, excluded = read_sources(game, manifest, archives_only=archives_only)
    hands, hand_excluded = read_hands(game, archives_only=archives_only)
    weapon, _ = derive(sources['models/#fpvbeneliaim.4ds'])
    weapon_names = [node['name'] for node in parse_4ds_nodes(weapon)['nodes']]
    stock = {state: sources['models/#fpvbeneli'+state+'.5ds'] for state in STATES}
    banks = {}
    def run(label, names, clips):
        row = audit_cases(machine, bank_cases(names, clips),
            lambda count: print(f'Checked attachment: {label} / {count} sequences', file=sys.stderr, flush=True) if count % 24 == 0 else None)
        row['target_count'] = len(names)
        row['target_names_sha256'] = hashlib.sha256(json.dumps(names, ensure_ascii=True).encode('ascii')).hexdigest()
        row['clips'] = {name: {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for name, raw in clips.items()}
        row['default_mode_is_explicit_synthetic_fixture'] = True
        return row
    for name in HAND_MODELS:
        names = [node['name'] for node in parse_4ds_nodes(hands[name])['nodes']] + weapon_names
        banks[name] = run(name, names, stock)
        banks[name]['model_sha256'] = hashlib.sha256(hands[name]).hexdigest()
        banks[name]['weapon_sha256'] = hashlib.sha256(weapon).hexdigest()
    for name, folder in CASES.items():
        directory = ROOT/'experimental'/folder
        recipe = json.loads((directory/'modern-world-model.json').read_text(encoding='utf-8'))
        spec = json.loads((directory/'modern-animation-bank.json').read_text(encoding='utf-8'))
        rig, clips, _, _ = compile_bank(recipe, spec)
        names = [node['name'] for node in parse_4ds_nodes(rig)['nodes']]
        banks[name] = run(name, names, {key: value[1] for key, value in clips.items()})
        banks[name]['provenance'] = 'MODERNE'; banks[name]['model_sha256'] = hashlib.sha256(rig).hexdigest()
    return {'schema_version': 1, 'scope': 'native_attachment_on_synthetic_models_with_bounded_owner_allocator',
        'library_sha256': DLL_SHA, 'synthetic_controls': synthetic, 'banks': banks,
        'bank_totals': {key: sum(bank[key] for bank in banks.values()) for key in synthetic},
        'source_pins': manifest['sources'], 'hand_pins': HAND_PINS,
        'excluded_loose_overrides': {**excluded, **hand_excluded},
        'native_attachment_sequence_checked': True, 'allocator_is_bounded_double': True,
        'model_controller_preallocated': True, 'clip_relocation_is_synthetic': True,
        'poses_or_events_evaluated': False, 'native_loader_executed': False,
        'loaded_scene_qualified': False, 'library_loaded': False, 'game_started': False,
        'game_modified': False, 'commercial_geometry_or_keys_exported': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--archives-only', action='store_true')
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():
            raise ValueError('Report exists; use a fresh name')
        report = audit(args.game, args.archives_only)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            with args.json_output.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, indent=2); stream.write('\n')
        print(json.dumps({key: value for key, value in report.items()
            if key not in ('banks', 'source_pins', 'hand_pins', 'excluded_loose_overrides')}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, ImportError) as error:
        print('Native attachment audit refused: '+str(error), file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
