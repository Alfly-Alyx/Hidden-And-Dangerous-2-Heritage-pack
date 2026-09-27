#!/usr/bin/env python3
"""Private persistent native clip replacement/weight/tick scenarios, no game."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from animation_attach_audit import invented, op
from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import read_hands, HAND_MODELS
from build_equipment_fpv_animation import compile_fpv_bank
from build_equipment_hand_grips import RECIPE
from five_ds import parse_5ds
from ls3d_animation_stream_oracle import AnimationStreamOracle
from ls3d_math_oracle import DLL_SHA


def attach(clip, slot=0, weight=1, mode=0):
    return {'kind': 'attach', **op(clip, slot, weight, mode)}


def steps_for(keys, last_end):
    if (not isinstance(keys, list) or not 1 <= len(keys) <= 9 or len(set(keys)) != len(keys)
            or type(last_end) is not int or not 1 <= last_end <= 250):
        raise ValueError('Unreviewed stream bank order or duration')
    steps = [attach(keys[0]), {'kind': 'tick', 'delta': 0}]
    slot = 0
    for key in keys[1:]:
        other = 1-slot
        steps.append(attach(key, other, 0))
        for weight in (0, .25, .5, .75, 1):
            steps.extend(({'kind': 'weight', 'slot': slot, 'weight': 1-weight},
                          {'kind': 'weight', 'slot': other, 'weight': weight},
                          {'kind': 'tick', 'delta': 20}))
        steps.append(attach(None, slot))
        slot = other
    # Reach a non-looping endpoint, restart the SAME clip, then release owners.
    steps.extend((attach(keys[-1], slot, 1, 1), {'kind': 'tick', 'delta': last_end*40},
                  attach(keys[-1], slot, 1, 2), {'kind': 'tick', 'delta': 40},
                  attach(None, slot), {'kind': 'tick', 'delta': 0}))
    return steps


def controls():
    seed = {'position': [4, 5, 6], 'rotation': [0, 0, 0, 1], 'scale': [1, 1, 1]}
    for kind in (9, 0):
        for mode in range(4):
            for targets in (['Root', 'Other'], ['Root', 'Missing', 'Root']):
                clips = {'A': {'data': invented(['Root']), 'mode': mode},
                         'B': {'data': invented(['Other']), 'mode': mode}}
                steps = steps_for(['A', 'B'], 10)
                # Inactive slots still accept weights; exercise both clamp edges.
                steps += [{'kind': 'weight', 'slot': 7, 'weight': -1},
                          {'kind': 'weight', 'slot': 7, 'weight': 2}, {'kind': 'tick', 'delta': 0}]
                yield targets, clips, [seed]*len(targets), steps, kind
    clips = {'A': {'data': invented(['Root']), 'mode': 2}}
    for slot in range(8):
        yield ['Root'], clips, [seed], [attach('A', slot), {'kind': 'tick', 'delta': 400},
              attach('A', slot, .5), {'kind': 'tick', 'delta': 0}, attach(None, slot),
              {'kind': 'tick', 'delta': 40}, attach('A', slot), {'kind': 'tick', 'delta': 40}], 9


def check_receipt(row, steps, target_count):
    if (any(row.get(k) is not True for k in ('native_interleaved_attach_weight_tick_checked',
            'same_native_memory_across_steps', 'poses_seeded_only_once',
            'full_state_and_descriptors_checked_each_step', 'source_inputs_preserved',
            'allocator_is_bounded_double', 'clip_relocation_is_synthetic'))
            or any(row.get(k) is not False for k in ('client_transition_decision_executed',
                'native_loader_executed', 'events_or_callbacks_called', 'skin_or_renderer_called',
                'scene_loaded', 'library_loaded', 'game_started'))
            or not isinstance(row.get('steps'), list) or len(row['steps']) != len(steps)
            or type(row.get('ticks')) is not int or row['ticks'] != sum(s['kind'] == 'tick' for s in steps)):
        raise ValueError('Incomplete native stream receipt')
    for supplied, result in zip(steps, row['steps']):
        if (result.get('kind') != supplied['kind']
                or any(type(result.get(k)) is not int or not 0 <= result[k] <= limit for k, limit in
                       (('pose_calls', target_count), ('written_channels', target_count*3),
                        ('active_slots', 8), ('owners', target_count)))
                or type(result.get('max_error')) not in (int, float) or not 0 <= result['max_error'] <= 2e-6):
            raise ValueError('Invalid native stream step receipt')
    if row.get('max_error') != max(s['max_error'] for s in row['steps']):
        raise ValueError('Invalid native stream maximum error')


def audit_cases(machine, cases):
    totals = dict(sequences=0, steps=0, ticks=0, pose_calls=0, written_channels=0,
                  owner_allocations=0, owner_releases=0, max_error=0)
    for names, clips, initial, steps, kind in cases:
        row = machine.stream(names, clips, initial, steps, kind)
        check_receipt(row, steps, len(names))
        totals['sequences'] += 1
        totals['steps'] += len(steps)
        for key in ('ticks', 'owner_allocations', 'owner_releases'):
            totals[key] += row[key]
        for step in row['steps']:
            totals['pose_calls'] += step['pose_calls']
            totals['written_channels'] += step['written_channels']
        totals['max_error'] = max(totals['max_error'], row['max_error'])
    return totals


def audit(game, archives_only=False):
    machine = AnimationStreamOracle((game/'LS3DF.dll').read_bytes())
    synthetic = audit_cases(machine, controls())
    print('Checked native interleaved synthetic streams', file=sys.stderr, flush=True)
    hands, excluded = read_hands(game, archives_only=archives_only)
    spec = json.loads(RECIPE.read_text(encoding='utf-8'))
    banks = {}
    for case in ('F35', 'F2'):
        banks[case] = {}
        for hand in HAND_MODELS:
            rig, bank, build = compile_fpv_bank(case, hands[hand], spec)
            names, initial = model_poses(hands[hand])
            gear_names, gear_initial = model_poses(rig)
            names += gear_names
            initial += gear_initial
            clips = {key: {'data': raw, 'mode': 2} for key, (_, raw) in bank.items()}
            if len(set(names)) != len(names) or any(t['name'] not in names for clip in clips.values()
                    for t in parse_5ds(clip['data'])['tracks']):
                raise ValueError('Ambiguous or unbound stream bank')
            cases = []
            for keys in (list(clips), list(reversed(clips))):
                end = parse_5ds(clips[keys[-1]]['data'])['frame_end']
                cases.append((names, clips, initial, steps_for(keys, end), 9))
            result = audit_cases(machine, cases)
            result.update(target_count=len(names), model_sha256=hashlib.sha256(rig).hexdigest(),
                          hand_sha256=build['hand_sha256'],
                          clips={key: hashlib.sha256(c['data']).hexdigest() for key, c in clips.items()})
            banks[case][hand] = result
            print(f'Checked native interleaved streams: {case} / {hand}', file=sys.stderr, flush=True)
    return {'schema_version': 1, 'scope': 'private_persistent_native_clip_replacement_weight_time_pose',
            'library_sha256': DLL_SHA, 'synthetic': synthetic, 'banks': banks,
            'same_native_memory_across_steps': True, 'poses_seeded_only_once': True,
            'blend_schedule_is_explicit_diagnostic_input': True,
            'client_transition_decision_executed': False, 'native_loader_executed': False,
            'skin_or_renderer_called': False, 'camera_or_grip_continuity_qualified': False,
            'events_or_callbacks_called': False, 'commercial_geometry_exported': False,
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
        print('Native persistent stream audit refused: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
