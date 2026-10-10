#!/usr/bin/env python3
"""Native model tick -> compiled correction -> native Refresh, private emulator only."""
import argparse
import itertools
import json
from pathlib import Path
import sys

from native_hand_relay import HandRelayOracle
from native_hand_hook import BINARY_SHA
from ls3d_math_oracle import DLL_SHA


def audit(library,compiled):
    machine=HandRelayOracle(library,compiled);rows=[]
    for turned,patched,registered,controller in itertools.product((False,True),repeat=4):
        rows.append(machine.run(turned=turned,patched=patched,registered=registered,controller_present=controller))
        print(f'Relay checked: turned={turned}, patched={patched}, registered={registered}, controller={controller}',file=sys.stderr,flush=True)
    ticks=[tick for row in rows for tick in row['ticks']]
    totals={'sequences':len(rows),'ticks':len(ticks),
        **{key:sum(t[key] for t in ticks) for key in ('native_controller_calls','native_pose_calls','adapter_calls','refresh_calls','corrected')},
        'max_pose_error':max(t['max_pose_error'] for t in ticks),
        'max_rotation_error':max(t['max_rotation_error'] for t in ticks)}
    if any(totals[k]!=v for k,v in {'sequences':16,'ticks':208,'native_controller_calls':72,
            'native_pose_calls':112,'adapter_calls':36,'refresh_calls':72,'corrected':18}.items()):
        raise ValueError('Native relay coverage changed')
    return {'schema_version':1,'scope':'private_native_model_hand_relay','runtime_status':'pending',
        'library_sha256':DLL_SHA,'compiled_sha256':BINARY_SHA,'totals':totals,'sequences':rows,
        'commercial_assets_used':False,'native_code_emulated':True,'native_image_restored':True,
        'game_file_patched':False,'windows_library_loaded':False,'game_started':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('library','compiled-hook','json-output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Use a fresh relay report path')
        report=audit(args.library.read_bytes(),args.compiled_hook.read_bytes())
        with args.json_output.open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
        print(json.dumps(report['totals'],indent=2));return 0
    except (ValueError,OSError,ImportError,KeyError) as error:
        print('Native hand relay refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
