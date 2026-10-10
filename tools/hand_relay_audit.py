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


def audit(library,compiled,*,scattered=False,compiled_binding=None,compiled_collection=None):
    if type(scattered) is not bool:raise ValueError('Expected explicit scattered relay switch')
    if compiled_collection is not None:
        if not scattered or compiled_binding is not None:
            raise ValueError('Compiled collection requires the scattered relay without a separate binding image')
        from native_collected_hand_relay import CollectedHandRelayOracle
        from native_hand_scatter_hook import BINARY_SHA as compiled_sha
        from native_hand_model_collect import BINARY_SHA as collection_sha
        machine=CollectedHandRelayOracle(library,compiled,compiled_collection)
    elif compiled_binding is not None:
        if not scattered:raise ValueError('Compiled binding requires the scattered relay')
        from native_bound_hand_relay import BoundHandRelayOracle
        from native_hand_scatter_hook import BINARY_SHA as compiled_sha
        from native_hand_model_binding import BINARY_SHA as binding_sha
        machine=BoundHandRelayOracle(library,compiled,compiled_binding)
    elif scattered:
        from native_scattered_hand_relay import ScatteredHandRelayOracle
        from native_hand_scatter_hook import BINARY_SHA as compiled_sha
        machine=ScatteredHandRelayOracle(library,compiled)
    else:machine=HandRelayOracle(library,compiled);compiled_sha=BINARY_SHA
    rows=[]
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
        'library_sha256':DLL_SHA,'compiled_sha256':compiled_sha,'totals':totals,'sequences':rows,
        'native_node_allocations_are_scattered':scattered,
        'compiled_binding_sha256':binding_sha if compiled_binding is not None else None,
        'compiled_collection_sha256':collection_sha if compiled_collection is not None else None,
        'commercial_assets_used':False,'native_code_emulated':True,'native_image_restored':True,
        'game_file_patched':False,'windows_library_loaded':False,'game_started':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('library','compiled-hook','json-output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--scattered',action='store_true')
    parser.add_argument('--compiled-binding',type=Path)
    parser.add_argument('--compiled-collection',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Use a fresh relay report path')
        report=audit(args.library.read_bytes(),args.compiled_hook.read_bytes(),scattered=args.scattered,
                     compiled_binding=args.compiled_binding.read_bytes() if args.compiled_binding is not None else None,
                     compiled_collection=args.compiled_collection.read_bytes() if args.compiled_collection is not None else None)
        with args.json_output.open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
        print(json.dumps(report['totals'],indent=2));return 0
    except (ValueError,OSError,ImportError,KeyError) as error:
        print('Native hand relay refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
