#!/usr/bin/env python3
"""Synthetic crossfades and native weight writes; detach/refresh only recorded."""
import argparse
import json
from pathlib import Path
import random
import sys

from item_native_contract import IMAGE_SHA
from ls3d_math_oracle import DLL_SHA
from fpv_blend_oracle import FpvBlendOracle,GATES,FACTOR


def record(slot,weight=1,rate=0):return {'slot':slot,'weight':weight,'rate':rate}


def cases():
    gates=dict.fromkeys(GATES,True)
    for count in range(4):
        previous=[record(i,(1,.5,.25)[i],(0,5,10)[i]) for i in range(count)]
        for weight in (0,.001,.5,1):
            for rate in (0,5,10):
                for delta in (0,1,40,100,200,1_000_000):
                    yield record(3,weight,rate),previous,delta,gates
    for key in GATES:yield record(3,.5,5),[record(0),record(1,.5,5)],100,{**gates,key:False}
    yield record(3,.5,5),[record(0)],100,dict.fromkeys(GATES,False)
    rng=random.Random(491440)
    for _ in range(100):
        yield record(3,rng.random(),rng.uniform(0,10)),[record(i,rng.random(),rng.uniform(0,10))
            for i in range(3)],rng.randrange(0,301),gates


def audit(machine):
    count=removed=weight_calls=0;calls={'weight':0,'detach':0,'refresh':0}
    for current,previous,delta,gates in cases():
        row=machine.advance(current,previous,delta,**gates)
        if (any(row.get(k) is not True for k in ('native_blend_state_and_arguments_match','inputs_preserved',
                'native_model_weight_writes_checked','detach_and_refresh_recorded_not_executed'))
                or any(row.get(k) is not False for k in ('model_effects_qualified','time_unit_seconds_qualified',
                                                       'allocation_called','library_loaded','game_started'))):
            raise ValueError('Incomplete native blend receipt')
        count+=1;removed+=len(previous)-len(row['previous'])
        if (type(row.get('native_weight_setter_calls')) is not int or row['native_weight_setter_calls']!=
                sum(c['operation']=='weight' for c in row['model_call_arguments'])):raise ValueError('Invalid native setter count receipt')
        weight_calls+=row['native_weight_setter_calls']
        for call in row['model_call_arguments']:calls[call['operation']]+=1
    return {'schema_version':2,'scope':'synthetic_client_crossfade_with_native_weight_setter',
        'client_image_sha256':IMAGE_SHA,'cases':count,'prior_records_removed':removed,
        'recorded_model_calls':calls,'factor_float32':FACTOR,'library_sha256':DLL_SHA,
        'native_weight_setter_calls':weight_calls,'native_model_weight_writes_checked':True,
        'native_blend_state_and_arguments_match':True,'detach_and_refresh_recorded_not_executed':True,
        'model_effects_qualified':False,'time_unit_seconds_qualified':False,'allocation_called':False,
        'library_loaded':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',required=True,type=Path);parser.add_argument('--json-output',type=Path)
    parser.add_argument('--library',required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(FpvBlendOracle(args.image.read_bytes(),args.library.read_bytes()))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native FPV blend audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
