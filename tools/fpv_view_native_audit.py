#!/usr/bin/env python3
"""Private corrected-axis clips: native loading, poses, wrists, skin and bounds.

Each bounded native subsystem runs in its own emulator. No scene loader,
clone, renderer or actual FPV camera is executed or claimed as qualified.
"""
import argparse
import json
from pathlib import Path
import sys

from animation_attach_audit import op
from animation_stream_audit import steps_for, check_receipt as check_stream
from animation_tick_audit import model_poses, check_receipt as check_tick
from benelli_fpv_rig_audit import read_hands, HAND_MODELS
from build_equipment_fpv_view_bank import compile_view_bank, view_grips
from build_equipment_hand_animation import IDENTITY, wrist_from_native
from build_equipment_hand_grips import RECIPE
from build_modern_equipment_hose import digest
from five_ds import parse_5ds
from hand_pose_ik import pinned_skin
from ls3d_animation_load_oracle import AnimationLoadOracle
from ls3d_animation_stream_oracle import AnimationStreamOracle
from ls3d_frame_find_oracle import FrameFindOracle
from ls3d_math_oracle import DLL_SHA
from ls3d_palette_audit import check_receipt as check_palette
from ls3d_palette_oracle import PaletteOracle
from ls3d_skin_audit import check_receipt as check_skin
from ls3d_skin_binding_oracle import SkinBindingOracle
from ls3d_skin_bounds_oracle import SkinBoundsOracle
from ls3d_skin_oracle import SkinOracle
from ls3d_tick_oracle import TickOracle
from menu_gui_audit import parse_4ds_nodes
from modern_fpv_geometry import geometry
from skin_binding_audit import from_model, check_receipt as check_binding
from skin_bounds_audit import containment, check_receipt as check_bounds


def audit(game, archives_only=False, bank_root=None):
    library = (game/'LS3DF.dll').read_bytes()
    loader, finder = AnimationLoadOracle(library), FrameFindOracle(library)
    binding, tick = SkinBindingOracle(library), TickOracle(library)
    stream, palette = AnimationStreamOracle(library), PaletteOracle(library)
    skin, bounds = SkinOracle(library), SkinBoundsOracle(library)
    hands, excluded = read_hands(game, archives_only=archives_only)
    spec = json.loads(RECIPE.read_text(encoding='utf-8'))
    results = {}
    totals = dict.fromkeys(('loaded_clips', 'dense_sequences', 'transition_sequences', 'observed_ticks',
        'hand_vertices', 'hose_vertices', 'hose_lod_evaluations', 'bounds_corner_transforms',
        'dense_wrist_targets', 'transition_wrist_observations'), 0)
    errors = dict.fromkeys(('tick', 'stream', 'palette', 'skin', 'bounds', 'box_escape', 'sphere_escape',
        'wrist_at_keys', 'wrist_between_keys', 'transition_wrist_deviation'), 0)
    for case in ('F35', 'F2'):
        variants = {}
        for source in HAND_MODELS:
            rig, bank, build = compile_view_bank(case, hands[source], spec)
            if bank_root:
                directory = bank_root/(case+'_CorrectedFPV_v1')
                if (directory/f'PROTOTYPE_{case}_FPVView.4ds.disabled').read_bytes() != rig:
                    raise ValueError('Saved corrected model differs from the audited model')
                for stem, raw in bank.values():
                    if (directory/(stem+'.5ds.disabled')).read_bytes() != raw:
                        raise ValueError('Saved corrected clip differs from the audited clip')
            gn, gi = model_poses(rig)
            nodes = parse_4ds_nodes(rig)['nodes']
            scene = [{'name': n['name'], 'frame_type': n['frame_type'], 'parent': n['parent_id']-1} for n in nodes]
            selection = finder.find(scene, 'fpv_weapon', 1)
            if selection['index'] != 0 or selection['direct_children'] != list(range(1, len(nodes))):
                raise ValueError('Corrected FPV native frame registration differs')
            tree = from_model(rig)
            bound = binding.bind(tree)
            check_binding(bound, tree, True)
            if bound['bone_count'] != 8 or bound['stopped_at_nested_skin_nodes']:
                raise ValueError('Corrected hose failed native bone binding')
            hoses = [geometry(rig, i)[1] for i in (0, 1)]
            hose_by_index = {n['index']: n for n in hoses[0]['nodes']}
            hose_names = [hose_by_index[i]['name'] for i in hoses[0]['joint_node_indices']]
            _, hand = pinned_skin(hands[source])
            hn, hi = model_poses(hands[source])
            names, initial = hn+gn, hi+gi
            indices = {name: i for i, name in enumerate(names)}
            if len(indices) != len(names):
                raise ValueError('Duplicate corrected FPV target')
            hand_nodes = {n['index']: n for n in hand['nodes']}
            hand_bones = {node: i for i, node in enumerate(hand['joint_node_indices'])}
            hand_by_name = {n['name']: n for n in hand['nodes']}
            chosen = view_grips(spec, case)
            elapsed, duration, transition = 0, 0, False

            def observe(index, delta, poses):
                nonlocal elapsed
                elapsed += delta
                if len(poses) != len(names):
                    raise ValueError('Incomplete corrected native pose')
                for i in range(len(hn)):
                    if any(poses[i][key] != hi[i][key] for key in ('position', 'scale')):
                        raise ValueError('Corrected animation stretched or moved a hand bone')
                if poses[indices['a']] != hi[hn.index('a')]:
                    raise ValueError('Corrected animation moved the hand root')
                hj = [{**poses[indices[hand_nodes[node]['name']]],
                       'parent': -1 if hand_nodes[node]['parent_id'] == 1 else hand_bones[hand_nodes[node]['parent_id']]}
                      for node in hand['joint_node_indices']]
                hp = palette.assemble(hj, hand['inverse_binds'])
                check_palette(hp, 36)
                hv = skin.deform(hand['vertices'], hand['pairs'], hp['palette'], hand['parents'])
                check_skin(hv, len(hand['vertices']))
                # Diagnostic world hierarchy only; this is not a renderer root test.
                gp = palette.assemble([{**poses[indices[n['name']]], 'parent': n['parent_id']-1} for n in nodes],
                                      [IDENTITY]*len(nodes))
                check_palette(gp, len(nodes))
                world = dict(zip(gn, gp['world_matrices']))
                for side, label in (('L', 'left'), ('R', 'right')):
                    wanted = wrist_from_native(world['MOD_held_pivot'], world['MOD_'+label+'_hand'], chosen[side])
                    actual = hp['world_matrices'][hand_bones[hand_by_name[f'Bip01 {side} Hand']['index']]][12:15]
                    error = max(abs(a-b) for a, b in zip(actual, wanted))
                    if transition:
                        key = 'transition_wrist_deviation'
                        totals['transition_wrist_observations'] += 1
                    else:
                        key = 'wrist_at_keys' if min(elapsed, duration)%40 == 0 else 'wrist_between_keys'
                        if error > (5e-6 if key == 'wrist_at_keys' else .0002):
                            raise ValueError(f'Corrected native wrist drift: {case} {source} {error}')
                        totals['dense_wrist_targets'] += 1
                    errors[key] = max(errors[key], error)
                # The actual visual root terminates the native ancestor walk.
                # Bounds/skin therefore use the eight ROOT-LOCAL joint matrices.
                lp = palette.assemble([{**poses[indices[name]], 'parent': -1} for name in hose_names],
                                      hoses[0]['inverse_binds'])
                check_palette(lp, 8)
                b = bounds.compute(hoses[0]['base_bounds'], hoses[0]['joint_bounds'], lp['world_matrices'])
                check_bounds(b, hoses[0]['base_bounds'], hoses[0]['joint_bounds'], lp['world_matrices'])
                errors['bounds'] = max(errors['bounds'], b['max_error'])
                errors['palette'] = max(errors['palette'], *hp['max_errors'].values(), *gp['max_errors'].values(),
                                        *lp['max_errors'].values())
                errors['skin'] = max(errors['skin'], hv['max_error'])
                totals['observed_ticks'] += 1
                totals['hand_vertices'] += len(hv['values'])
                totals['bounds_corner_transforms'] += b['native_corner_transforms']
                for hose in hoses:
                    values = skin.deform(hose['vertices'], hose['pairs'], lp['palette'], hose['parents'])
                    check_skin(values, len(hose['vertices']))
                    box, sphere = containment(b, values['values'])
                    errors['skin'] = max(errors['skin'], values['max_error'])
                    errors['box_escape'] = max(errors['box_escape'], box)
                    errors['sphere_escape'] = max(errors['sphere_escape'], sphere)
                    totals['hose_vertices'] += len(values['values'])
                    totals['hose_lod_evaluations'] += 1

            loaded, dense, changed = {}, {}, []
            for name, (stem, raw) in bank.items():
                loaded[name] = loader.load(raw, stem+'.I3D')
                totals['loaded_clips'] += 1
                end = parse_5ds(raw)['frame_end']
                deltas = [0]+[20]*(2*end)+[0, 20]
                elapsed, duration = 0, end*40
                clips, operations = {name: {'data': raw, 'mode': 1}}, [op(name, 7)]
                row = tick.sequence_with_ticks(names, clips, operations, initial, deltas, pose_observer=observe)
                check_tick(row, names, clips, operations, initial, deltas, 9)
                errors['tick'] = max(errors['tick'], row['max_error'])
                totals['dense_sequences'] += 1
                dense[name] = {'sha256': digest(raw), 'frame_end': end, 'ticks': len(deltas)}
                print(f'Corrected native FPV: {case} / {source} / {name}', file=sys.stderr, flush=True)
            transition = True
            clips = {key: {'data': raw, 'mode': 2} for key, (_, raw) in bank.items()}
            for keys in (list(clips), list(reversed(clips))):
                steps = steps_for(keys, parse_5ds(clips[keys[-1]]['data'])['frame_end'])
                row = stream.stream(names, clips, initial, steps, pose_observer=observe)
                check_stream(row, steps, len(names))
                errors['stream'] = max(errors['stream'], row['max_error'])
                totals['transition_sequences'] += 1
                changed.append({'steps': len(steps), 'tick_count': row['ticks']})
            variants[source] = {'hand_sha256': build['hand_sha256'], 'model_sha256': digest(rig),
                'native_frame_selection': selection, 'native_bone_binding': bound,
                'loads': loaded, 'dense_clips': dense, 'transitions': changed}
        results[case] = variants
    return {'schema_version': 1, 'scope': 'private_corrected_view_native_components', 'library_sha256': DLL_SHA,
        'cases': results, 'totals': totals, 'max_errors': errors, 'excluded_loose_overrides': excluded,
        'saved_private_bank_bytes_verified': bank_root is not None,
        'original_animation_keys_read': False, 'commercial_geometry_exported': False,
        'native_subsystems_use_separate_emulators': True, 'persistent_poses_observed': True,
        'native_scene_loader_or_clone_executed': False, 'renderer_executed': False,
        'transition_wrist_contact_qualified': False, 'finger_contact_qualified': False,
        'camera_calibrated': False, 'game_started': False, 'game_modified': False, 'engine_validated': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--archives-only', action='store_true')
    parser.add_argument('--bank-root', type=Path)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():
            raise ValueError('Report exists; use a fresh name')
        report = audit(args.game, args.archives_only, args.bank_root)
        if args.json_output:
            with args.json_output.open('x', encoding='utf-8') as out:
                json.dump(report, out, indent=2)
                out.write('\n')
        print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, ImportError) as error:
        print('Corrected native FPV audit refused: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
