#!/usr/bin/env python3
"""Invented forward/reverse playback and loop boundaries, never a game clock."""
import argparse
import json
from pathlib import Path
import sys

from ls3d_time_oracle import TimeOracle
from ls3d_math_oracle import DLL_SHA


def slot(active=True,mode=2,end=10,time=0):
    return {'active':active,'mode':mode,'frame_end':end,'time':time,'previous':-40,'last_delta':13}


def cases():
    for end in (1,10,146,65535):
        duration=end*40
        for mode in range(4):
            for time in (-duration-1,-1,0,duration-1,duration,duration*2+1):
                for delta in (-41,0,1,40):
                    for dirty in (False,True):
                        yield [slot(mode=mode,end=end,time=time) for _ in range(8)],delta,dirty
    for delta in (-41,0,40):
        for dirty in (False,True):
            yield [slot(active=i%2==0,mode=i%4,time=i*100) for i in range(8)],delta,dirty


def audit(machine):
    count=0;processed=0;deactivated=0
    for slots,delta,dirty in cases():
        row=machine.advance(slots,delta,dirty)
        if (row.get('native_time_controller_match') is not True or row.get('inputs_preserved') is not True
                or row.get('duration_integer_units_per_terminal_frame')!=40
                or any(row.get(k) is not False for k in ('time_unit_seconds_qualified','target_pose_evaluated',
                    'callbacks_called','scene_loaded','library_loaded','game_started'))):raise ValueError('Incomplete native time receipt')
        count+=1;processed+=row['controller_processed']
        deactivated+=sum(before['active'] and not after['active'] for before,after in zip(slots,row['slots']))
    return {'schema_version':1,'scope':'synthetic_time_controller_without_targets',
            'library_sha256':DLL_SHA,'cases':count,'processed_cases':processed,'deactivated_slots':deactivated,
            'duration_integer_units_per_terminal_frame':40,'wraps_once_per_update':True,
            'time_unit_seconds_qualified':False,'target_pose_evaluated':False,'callbacks_called':False,
            'scene_loaded':False,'library_loaded':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(TimeOracle(args.library.read_bytes()))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native time audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
