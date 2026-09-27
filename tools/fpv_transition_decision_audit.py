#!/usr/bin/env python3
"""Synthetic FPV branch decisions, native active queries and prior-record copies."""
import argparse
from itertools import combinations, permutations
import json
from pathlib import Path
import sys

from fpv_transition_decision_oracle import TransitionDecisionOracle, reference
from item_native_contract import IMAGE_SHA
from ls3d_math_oracle import DLL_SHA


def record(slot, rate=5, weight=.5):
    return {'slot': slot, 'rate': rate, 'weight': weight}


def cases():
    for item in (0, 359, 360, 361, 499):
        for state in range(13):
            for channel in range(4):
                for current, active, present in ((None, False, True),
                        (record(0, 0, 1), False, True), (record(0, 0, 1), True, True),
                        (record(0, 0, 1), True, False)):
                    yield item, state, channel, current, [], active, present
    for current in range(8):
        candidates = [slot for slot in range(8) if slot != current]
        for count in range(8):
            for slots in combinations(candidates, count):
                for active in (False, True):
                    yield 360, 0, 0, record(current), [record(slot) for slot in slots], active, True
    for slots in permutations(range(4)):
        yield 361, 12, 3, record(slots[3], 10, 0), [record(slot, 0, 1) for slot in slots[:3]], True, True


def audit(machine):
    count = queries = saved = collisions = 0
    selected = dict.fromkeys(range(4), 0)
    for args in cases():
        expected = reference(*args)
        row = machine.select(*args)
        if (any(type(row.get(k)) is not type(v) or row.get(k) != v for k, v in expected.items())
                or any(row.get(k) is not True for k in ('native_decision_and_copy_match', 'inputs_preserved',
                    'spare_capacity_is_supplied', 'attach_and_refresh_recorded_not_executed'))
                or any(row.get(k) is not False for k in ('entry_branch_is_supplied', 'allocation_called',
                    'resource_loader_called', 'scene_loaded', 'library_loaded', 'game_started'))
                or row.get('native_active_query_executed') is not (args[3] is not None)
                or row.get('model_call_arguments') != [{'operation': 'attach',
                    'slot': expected['selected_slot'], 'weight': expected['weight'], 'mode': 0},
                    {'operation': 'refresh'}]):
            raise ValueError('Incomplete native transition-decision receipt')
        count += 1
        queries += row['native_active_queries']
        saved += row['previous_clip_saved']
        collisions += row['selected_slot_already_present']
        selected[row['selected_slot']] += 1
    return {'schema_version': 1, 'scope': 'native_fpv_decision_with_preallocated_synthetic_list',
            'client_image_sha256': IMAGE_SHA, 'library_sha256': DLL_SHA,
            'cases': count, 'native_active_queries': queries, 'native_prior_appends': saved,
            'selected_slots': selected, 'synthetic_occupied_slot_three_selections': collisions,
            'native_decision_and_copy_match': True, 'entry_branch_is_supplied': False,
            'spare_capacity_is_supplied': True, 'attach_and_refresh_recorded_not_executed': True,
            'collision_reachable_in_game_qualified': False, 'allocation_called': False,
            'resource_loader_called': False, 'scene_loaded': False, 'library_loaded': False,
            'game_started': False, 'game_modified': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():
            raise ValueError('Report exists; use a fresh name')
        report = audit(TransitionDecisionOracle(args.image.read_bytes(), args.library.read_bytes()))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            with args.json_output.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, indent=2)
                stream.write('\n')
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, ImportError) as error:
        print('Native transition-decision audit refused: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
