#!/usr/bin/env python3
"""Audit invented poses against bounded native eight-slot application."""
import argparse
import json
import math
from pathlib import Path
import sys

from ls3d_math_oracle import DLL_SHA
from ls3d_pose_oracle import PoseOracle


def quaternion(angle):return [0,0,math.sin(angle/2),math.cos(angle/2)]


def slot(kinds=('position','rotation','scale'),weight=1,active=True,time=120,angle=1):
    curves={'position':{'frames':[0,2,5],'values':[[0,0,0],[1,2,3],[-1,3,2]]},
            'rotation':{'frames':[0,2,5],'values':[quaternion(0),quaternion(angle),quaternion(angle*2)]},
            'scale':{'frames':[0,2,5],'values':[[1,1,1],[1.5,.5,2],[1,2,.5]]}}
    return {'active':active,'weight':weight,'time':time,'channels':{k:curves[k] for k in kinds}}


def cases():
    initial={'position':[4,-3,2],'rotation':quaternion(4),'scale':[.7,1.3,1.1]}
    for flags in (8,0x88):
        yield 'empty',initial,[],flags
        for index in range(8):
            for kind in initial:
                for weight in (0,.0001,.25,1,2):
                    for active in (False,True):
                        slots=[slot((),active=False) for _ in range(index)]
                        slots.append(slot((kind,),weight,active))
                        yield 'single_slot',initial,slots,flags
        for amount in (.1,.5,.9,1,2):
            for time in (0,1,79,80,120,199,200,201):
                slots=[slot(weight=.25,time=20,angle=.028),slot(weight=amount,time=time,angle=2.2)]
                yield 'two_slots',initial,slots,flags
        for reverse in (False,True):
            for angle in (.028,.029,.5,2.5):
                slots=[slot(tuple(initial)[i%3:i%3+1],weight=.125*(i+1),time=i*29,angle=angle) for i in range(8)]
                yield 'eight_partial_slots',initial,list(reversed(slots)) if reverse else slots,flags
        for angle in (.028,.029,4,5):
            yield 'eight_rotation_slots',initial,[slot(('rotation',),weight=.1,time=120,angle=angle) for _ in range(8)],flags


def audit(machine):
    count=0;groups={};maximum=0;normalized=0
    for label,initial,slots,flags in cases():
        row=machine.apply(initial,slots,flags)
        if (row.get('native_synthetic_pose_match') is not True or row.get('inputs_preserved') is not True
                or any(row.get(k) is not False for k in ('extra_pose_evaluated','matrix_rotation_fallback_evaluated',
                    'event_or_scene_called','skin_evaluated','model_loading_qualified','game_started','library_loaded'))
                or type(row.get('max_error')) not in (int,float) or not math.isfinite(row['max_error'])
                or not 0<=row['max_error']<=2e-6):raise ValueError('Incomplete native pose proof')
        maximum=max(maximum,row['max_error']);count+=1;groups[label]=groups.get(label,0)+1
        normalized+=row['accumulation_counts']['rotation']>0
    return {'schema_version':1,'scope':'synthetic_eight_slot_pose_application',
            'library_sha256':DLL_SHA,'cases':count,'case_groups':groups,'max_error':maximum,
            'rotation_written_cases':normalized,'synthetic_x87_control_word':0x27f,
            'channel_order_and_absence_qualified_on_synthetic_object':True,
            'extra_pose_evaluated':False,'matrix_rotation_fallback_evaluated':False,
            'game_model_initialization_qualified':False,'benelli_runtime_pose_qualified':False,
            'skin_evaluated':False,'events_called':False,'game_started':False,'game_modified':False,
            'library_loaded':False,'commercial_geometry_or_keys_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(PoseOracle(args.library.read_bytes()))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native pose audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
