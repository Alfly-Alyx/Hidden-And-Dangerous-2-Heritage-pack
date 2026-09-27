#!/usr/bin/env python3
"""Private native bounds checked against skinned hose vertices during clip changes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

from animation_stream_audit import steps_for, check_receipt as check_stream
from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import read_hands, HAND_MODELS
from build_equipment_fpv_animation import compile_fpv_bank
from build_equipment_hand_grips import RECIPE
from build_modern_equipment_assembly import inputs
from build_modern_equipment_hose import compile_hose_bank
from five_ds import parse_5ds
from four_ds_skin import read_reviewed
from ls3d_animation_stream_oracle import AnimationStreamOracle
from ls3d_palette_oracle import PaletteOracle
from ls3d_palette_audit import check_receipt as check_palette
from ls3d_skin_oracle import SkinOracle
from ls3d_skin_audit import check_receipt as check_skin, IDENTITY
from ls3d_skin_bounds_oracle import SkinBoundsOracle, reference
from ls3d_math_oracle import DLL_SHA
from menu_gui_audit import parse_4ds_nodes


def controls():
    base = [-.1, -.1, -.1, 0, .1, .1, .1, 0]
    bound = [-1, -2, -3, 0, 1, 2, 3, 0]
    for count in (1, 2, 8, 36, 64):
        yield base, [bound]*count, [IDENTITY]*count
    yield [0]*8, [[0]*8], [IDENTITY]
    rng = random.Random(52330)
    for _ in range(40):
        count = rng.randrange(1, 9)
        matrices, boxes = [], []
        for _ in range(count):
            m = [rng.uniform(-2, 2) for _ in range(16)]
            for i, value in ((3, 0), (7, 0), (11, 0), (15, 1)):
                m[i] = value
            low = [rng.uniform(-1, 0) for _ in range(3)]
            high = [rng.uniform(0, 1) for _ in range(3)]
            matrices.append(m)
            boxes.append(low+[0]+high+[0])
        yield base, boxes, matrices


def check_receipt(row, base, bounds, matrices):
    expected = reference(base, bounds, matrices)
    if (any(row.get(k) is not True for k in ('native_bounds_and_sphere_match', 'inputs_preserved',
            'cached_joint_matrices_are_supplied', 'skin_root_has_no_parent'))
            or any(row.get(k) is not False for k in ('native_joint_discovery_executed', 'native_loader_executed',
                'native_clone_executed', 'animation_skin_renderer_executed', 'allocation_called',
                'library_loaded', 'game_started'))
            or type(row.get('native_corner_transforms')) is not int
            or row['native_corner_transforms'] != 8*len(bounds)
            or type(row.get('max_error')) not in (int, float) or not 0 <= row['max_error'] <= 2e-5):
        raise ValueError('Incomplete native bounds receipt')
    for key, length in (('bounds', 8), ('center', 3)):
        if (not isinstance(row.get(key), list) or len(row[key]) != length
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in row[key])
                or max(abs(a-b) for a, b in zip(row[key], expected[key])) > 2e-5):
            raise ValueError('Invalid native bounds values receipt')
    if type(row.get('radius')) not in (int, float) or not math.isfinite(row['radius']) or abs(row['radius']-expected['radius']) > 2e-5:
        raise ValueError('Invalid native bounding sphere receipt')


def containment(row, values):
    box_error = sphere_error = 0.0
    for vertex in values:
        if len(vertex) < 3 or any(not math.isfinite(v) for v in vertex[:3]):
            raise ValueError('Invalid containment vertex')
        box_error = max(box_error, *(row['bounds'][i]-vertex[i] for i in range(3)),
                        *(vertex[i]-row['bounds'][4+i] for i in range(3)))
        sphere_error = max(sphere_error, math.dist(vertex[:3], row['center'])-row['radius'])
    if max(box_error, sphere_error) > 2e-6:
        raise ValueError('Deformed geometry escapes native skin bounds')
    return box_error, sphere_error


def payload(raw, node):
    offset = node['name_offset']+node['name_length']
    return raw[offset+1+raw[offset]:node['end']]


def audit(game, archives_only=False):
    library = (game/'LS3DF.dll').read_bytes()
    bounds_machine = SkinBoundsOracle(library)
    synthetic_count, synthetic_error = 0, 0
    for args in controls():
        row = bounds_machine.compute(*args)
        check_receipt(row, *args)
        synthetic_count += 1
        synthetic_error = max(synthetic_error, row['max_error'])
    hands, excluded = read_hands(game, archives_only=archives_only)
    spec = json.loads(RECIPE.read_text(encoding='utf-8'))
    stream, palette, skin = AnimationStreamOracle(library), PaletteOracle(library), SkinOracle(library)
    results = {}
    for case in ('F35', 'F2'):
        hose_raw, _, _, _ = compile_hose_bank(*inputs(case))
        hose = [read_reviewed(hose_raw, allow_multiple_lods=True, lod=i) for i in (0, 1)]
        hose_nodes = {n['index']: n for n in hose[0]['nodes']}
        bone_names = [hose_nodes[i]['name'] for i in hose[0]['joint_node_indices']]
        results[case] = {}
        for hand in HAND_MODELS:
            rig, bank, build = compile_fpv_bank(case, hands[hand], spec)
            gear_nodes = parse_4ds_nodes(rig)['nodes']
            if payload(rig, gear_nodes[0]) != payload(hose_raw, hose[0]['nodes'][0]):
                raise ValueError('Serialized hose skin payload differs from flat root')
            if any(n['parent_id'] != 1 for n in gear_nodes if n['name'] in bone_names):
                raise ValueError('Expected independent hose joints under visual root')
            names, initial = model_poses(hands[hand])
            gn, gi = model_poses(rig)
            names += gn
            initial += gi
            indices = {name: i for i, name in enumerate(names)}
            if len(indices) != len(names):
                raise ValueError('Ambiguous bounds animation target names')
            clips = {key: {'data': raw, 'mode': 2} for key, (_, raw) in bank.items()}
            totals = dict(sequences=0, observed_ticks=0, lod_evaluations=0, deformed_vertices=0,
                          corner_transforms=0, max_palette_error=0, max_bounds_error=0,
                          max_skin_error=0, max_box_escape=0, max_sphere_escape=0)
            def observe(index, delta, poses):
                # A visual root stops the native ancestor walk. These eight
                # independent joints produce root-local, NOT world matrices.
                joints = [{**poses[indices[name]], 'parent': -1} for name in bone_names]
                p = palette.assemble(joints, hose[0]['inverse_binds'])
                check_palette(p, 8)
                b = bounds_machine.compute(hose[0]['base_bounds'], hose[0]['joint_bounds'], p['world_matrices'])
                check_receipt(b, hose[0]['base_bounds'], hose[0]['joint_bounds'], p['world_matrices'])
                totals['observed_ticks'] += 1
                totals['corner_transforms'] += b['native_corner_transforms']
                totals['max_bounds_error'] = max(totals['max_bounds_error'], b['max_error'])
                totals['max_palette_error'] = max(totals['max_palette_error'], *p['max_errors'].values())
                for lod in hose:
                    row = skin.deform(lod['vertices'], lod['pairs'], p['palette'], lod['parents'])
                    check_skin(row, len(lod['vertices']))
                    box_error, sphere_error = containment(b, row['values'])
                    totals['lod_evaluations'] += 1
                    totals['deformed_vertices'] += len(row['values'])
                    totals['max_skin_error'] = max(totals['max_skin_error'], row['max_error'])
                    totals['max_box_escape'] = max(totals['max_box_escape'], box_error)
                    totals['max_sphere_escape'] = max(totals['max_sphere_escape'], sphere_error)
            for keys in (list(clips), list(reversed(clips))):
                steps = steps_for(keys, parse_5ds(clips[keys[-1]]['data'])['frame_end'])
                row = stream.stream(names, clips, initial, steps, pose_observer=observe)
                check_stream(row, steps, len(names))
                totals['sequences'] += 1
            results[case][hand] = {**totals, 'model_sha256': hashlib.sha256(rig).hexdigest(),
                'hand_sha256': build['hand_sha256'],
                'clips': {key: hashlib.sha256(c['data']).hexdigest() for key, c in clips.items()}}
            print(f'Checked native hose bounds: {case} / {hand}', file=sys.stderr, flush=True)
    return {'schema_version': 1, 'scope': 'private_native_root_local_hose_bounds_during_clip_changes',
            'library_sha256': DLL_SHA, 'synthetic_cases': synthetic_count,
            'synthetic_max_error': synthetic_error, 'banks': results,
            'actual_serialized_skin_bounds_read': True, 'persistent_native_poses_observed': True,
            'palette_bounds_and_skin_use_separate_emulators': True, 'visual_root_transform_excluded': True,
            'native_loader_executed': False, 'native_clone_executed': False,
            'whole_scene_culling_or_renderer_qualified': False, 'commercial_geometry_exported': False,
            'game_started': False, 'game_modified': False, 'engine_validated': False,
            'excluded_loose_overrides': excluded}


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
                json.dump(report, stream, indent=2)
                stream.write('\n')
        print(json.dumps({k: v for k, v in report.items() if k != 'banks'}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, ImportError) as error:
        print('Native animated bounds audit refused: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
