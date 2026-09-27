#!/usr/bin/env python3
"""Private, localized blend defects and offline six-rotation wrist correction.

Optional native streams and native palettes use separate bounded emulators.
The correction itself is Python authoring code, not native runtime integration.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

from animation_stream_audit import steps_for, check_receipt
from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS, read_hands
from build_equipment_fpv_view_bank import view_grips
from build_equipment_hand_animation import IDENTITY
from build_equipment_hand_grips import RECIPE
from build_modern_animation_bank import ALIASES
from build_modern_equipment_hose import digest
from five_ds import parse_5ds
from fpv_contact_constraints import correct, targets, world, wrist_errors
from ls3d_animation_stream_oracle import BOOTSTRAP, validate, reference_step
from ls3d_attach_oracle import reference_sequence
from menu_gui_audit import parse_4ds_nodes
from modern_fpv_axes import compile_view_rig


def trace(names, clips, initial, steps):
    parsed, poses, clean = validate(names, clips, initial, steps)
    state = reference_sequence(names, clips, [BOOTSTRAP])[-1]
    flags, rows = [8]*len(names), []
    for index, step in enumerate(clean):
        active = [{'slot': i, 'clip': slot['clip'], 'weight': slot['weight'],
                   'sample_time': slot['time']+step.get('delta', 0)}
                  for i, slot in enumerate(state['slots']) if slot['active']]
        result = reference_step(state, poses, flags, names, clips, parsed, step)
        state, poses, flags = result['state'], result['poses'], result['flags']
        if step['kind'] == 'tick':
            rows.append({'step': index, 'delta': step['delta'], 'slots': active,
                         'poses': deepcopy(poses)})
    return rows


def load_bank(directory, case, source, hand_raw):
    manifest = json.loads((directory/'MANIFEST.json').read_text(encoding='utf-8'))
    if (manifest.get('private_only') is not True or manifest.get('runtime_status') != 'pending'
            or manifest.get('provenance') != 'DERIVE_MODERNE_SUR_SQUELETTE_COMMERCIAL'):
        raise ValueError('Expected explicitly private derived view bank')
    row = manifest['variants'][source]
    rig = (directory/f'PROTOTYPE_{case}_FPVView.4ds.disabled').read_bytes()
    if (rig != compile_view_rig(case)[0] or digest(rig) != row['rig']['model_sha256']
            or digest(hand_raw) != row['hand_sha256'] or set(row['clips']) != set(ALIASES)):
        raise ValueError('Changed source skeleton, modern rig or clip set')
    variant = 'H' if source == HAND_MODELS[0] else 'R'
    clips = {}
    for name, entry in row['clips'].items():
        stem = f'PROTOTYPE_{case}V{variant}{ALIASES[name]}'
        if entry['stem'] != stem:
            raise ValueError('Unexpected or unsafe private clip path')
        raw = (directory/(stem+'.5ds.disabled')).read_bytes()
        if digest(raw) != entry['sha256']:
            raise ValueError('Changed serialized source clip')
        clips[name] = {'data': raw, 'mode': 2}
    return rig, clips


def audit(game, bank_root, archives_only=False, native=False):
    stream = palette = None
    if native:
        from ls3d_animation_stream_oracle import AnimationStreamOracle
        from ls3d_palette_oracle import PaletteOracle
        library = (game/'LS3DF.dll').read_bytes()
        stream, palette = AnimationStreamOracle(library), PaletteOracle(library)
    hands, excluded = read_hands(game, archives_only=archives_only)
    spec = json.loads(RECIPE.read_text(encoding='utf-8'))
    reports, maxima = {}, {'before': 0, 'after': 0, 'native_stream': 0, 'native_palette': 0}
    totals = dict(sequences=0, ticks=0, wrist_observations=0, native_palettes=0)
    worst = None
    for case in ('F35', 'F2'):
        reports[case] = {}
        for source in HAND_MODELS:
            hand_raw = hands[source]
            rig, clips = load_bank(bank_root/(case+'_CorrectedFPV_v1'), case, source, hand_raw)
            hn, hi = model_poses(hand_raw)
            gn, gi = model_poses(rig)
            hnodes = parse_4ds_nodes(hand_raw)['nodes']
            gnodes = parse_4ds_nodes(rig)['nodes']
            names, initial, grips = hn+gn, hi+gi, view_grips(spec, case)
            sequences = []
            for order_name, keys in (('forward', list(clips)), ('reverse', list(reversed(clips)))):
                steps = steps_for(keys, parse_5ds(clips[keys[-1]]['data'])['frame_end'])
                rows = trace(names, clips, initial, steps)
                samples = []

                def observe(index, delta, values):
                    nonlocal worst
                    expected = rows[index]
                    if delta != expected['delta']:
                        raise ValueError('Misaligned localized stream sample')
                    error = max(abs(a-b) for pose, ref in zip(values, expected['poses'])
                                for key in pose for a,b in zip(pose[key],ref[key]))
                    if error > 2e-6:
                        raise ValueError('Localized stream differs from native pose')
                    before_poses = dict(zip(names, values))
                    after_poses, correction = correct(hand_raw, gnodes, before_poses, grips)
                    if palette:
                        wanted = targets(world(gnodes, before_poses), grips)
                        for label, poses in (('before', before_poses), ('after', after_poses)):
                            result = palette.assemble([{**poses[n['name']], 'parent': n['parent_id']-1}
                                                       for n in hnodes], [IDENTITY]*len(hnodes))
                            correction[label] = wrist_errors(dict(zip(hn, result['world_matrices'])), wanted)
                            maxima['native_palette'] = max(maxima['native_palette'], *result['max_errors'].values())
                            totals['native_palettes'] += 1
                    if max(correction['after'].values()) > 5e-6:
                        raise ValueError('Native palette rejected corrected wrist contact')
                    sample = {k: expected[k] for k in ('step', 'delta', 'slots')}
                    sample.update(before=correction['before'], after=correction['after'])
                    samples.append(sample)
                    for label in ('before', 'after'):
                        maxima[label] = max(maxima[label], *correction[label].values())
                    for side, value in correction['before'].items():
                        if worst is None or value > worst['error']:
                            worst = {'case': case, 'source': source, 'order': order_name, 'side': side,
                                     'error': value, **deepcopy(sample)}
                    totals['ticks'] += 1
                    totals['wrist_observations'] += 2

                if stream:
                    receipt = stream.stream(names, clips, initial, steps, pose_observer=observe)
                    check_receipt(receipt, steps, len(names))
                    maxima['native_stream'] = max(maxima['native_stream'], receipt['max_error'])
                else:
                    for i, row in enumerate(rows): observe(i, row['delta'], row['poses'])
                sequences.append({'order': order_name, 'steps': len(steps), 'samples': samples})
                totals['sequences'] += 1
            reports[case][source] = {'hand_sha256': digest(hand_raw), 'model_sha256': digest(rig),
                'clips': {key: digest(value['data']) for key, value in clips.items()}, 'sequences': sequences}
            print(f'Localized contact correction: {case} / {source}', file=sys.stderr, flush=True)
    return {'schema_version': 1, 'scope': 'private_offline_post_blend_wrist_constraints',
        'runtime_status': 'pending', 'cases': reports, 'totals': totals, 'max_errors': maxima,
        'worst_before': worst, 'excluded_loose_overrides': excluded,
        'native_stream_executed': native, 'native_hand_palette_executed': native,
        'native_subsystems_use_separate_emulators': native,
        'correction_is_python_authoring_code': True, 'engine_hook_implemented': False,
        'source_geometry_or_rest_transforms_changed': False, 'finger_poses_preserved': True,
        'equipment_poses_preserved': True, 'original_animation_keys_read': False,
        'commercial_geometry_exported': False, 'derived_poses_exported': False,
        'diagnostic_orders_proven_reachable_in_client': False, 'renderer_executed': False,
        'skin_executed': False, 'camera_calibrated': False, 'engine_validated': False,
        'game_started': False, 'game_modified': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', required=True, type=Path)
    parser.add_argument('--bank-root', required=True, type=Path)
    parser.add_argument('--archives-only', action='store_true')
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--json-output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.json_output.exists(): raise ValueError('Report exists; use a fresh name')
        report = audit(args.game, args.bank_root, args.archives_only, args.native)
        with args.json_output.open('x', encoding='utf-8') as output:
            json.dump(report, output, indent=2)
            output.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k != 'cases'}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, ImportError) as error:
        print('Offline contact audit refused: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__': raise SystemExit(main())
