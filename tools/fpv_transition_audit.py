#!/usr/bin/env python3
"""Client transition-tail audit; supplied entry branch and already-loaded cache."""
import argparse
from itertools import combinations, permutations
import json
from pathlib import Path
import sys

from item_native_contract import IMAGE_SHA
from fpv_transition_oracle import TransitionOracle, reference


def cases():
    for item in (0, 359, 499):
        for state in range(13):
            for channel in range(4):
                for blended in (False,True):
                    yield item,state,channel,[],blended
    for count in range(9):
        for occupied in combinations(range(8),count):
            for blended in (False,True):
                yield 359,0,0,list(occupied),blended
    for occupied in permutations((0,1,2,3)):
        yield 359,12,3,list(occupied),True


def audit(machine):
    count = collisions = 0; selected = dict.fromkeys(range(4),0)
    for args in cases():
        expected = reference(*args); row = machine.prepare(*args)
        if (any(row.get(key) != value or type(row.get(key)) is not type(value) for key,value in expected.items())
                or any(row.get(key) is not True for key in ('native_transition_tail_match','inputs_preserved',
                    'prior_list_is_supplied','entry_branch_is_supplied','model_calls_recorded_not_executed'))
                or any(row.get(key) is not False for key in ('allocation_called','resource_loader_called','scene_loaded','game_started'))
                or row.get('model_call_arguments') != [{'operation':'attach','slot':expected['selected_slot'],
                    'weight':expected['weight'],'mode':0},{'operation':'refresh'}]):
            raise ValueError('Incomplete native transition-tail receipt')
        count += 1; collisions += expected['selected_slot_already_present']; selected[expected['selected_slot']] += 1
    return {'schema_version':1,'scope':'native_fpv_transition_tail_with_supplied_branch_and_prior_list',
        'client_image_sha256':IMAGE_SHA,'cases':count,'selected_slots':selected,
        'synthetic_cases_selecting_occupied_slot_three':collisions,
        'native_transition_tail_checked':True,'entry_branch_is_supplied':True,'prior_list_is_supplied':True,
        'model_calls_recorded_not_executed':True,'allocation_called':False,'resource_loader_called':False,
        'collision_reachable_in_game_qualified':False,'loaded_scene_qualified':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,required=True);parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(TransitionOracle(args.image.read_bytes()))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native transition-tail audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
