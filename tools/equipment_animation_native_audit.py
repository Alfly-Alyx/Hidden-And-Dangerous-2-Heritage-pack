#!/usr/bin/env python3
"""Pinned native attachment/ticks for freshly generated modern held-only banks."""
import argparse
import json
from pathlib import Path
import sys

from build_modern_equipment_animation import inputs,compile_equipment_bank,CASES
from ls3d_attach_oracle import AttachOracle
from ls3d_tick_oracle import TickOracle
from ls3d_math_oracle import DLL_SHA
from animation_attach_audit import audit_cases as audit_attach,bank_cases as attachment_cases
from animation_tick_audit import audit_cases as audit_tick,bank_cases as tick_cases,model_poses


def audit(library):
    attach=AttachOracle(library);tick=TickOracle(library);banks={}
    for case in CASES:
        rig,clips,_,build=compile_equipment_bank(*inputs(case));names,poses=model_poses(rig)
        raw_clips={key:value[1] for key,value in clips.items()}
        bindings=audit_attach(attach,attachment_cases(names,raw_clips))
        updates=audit_tick(tick,tick_cases(names,raw_clips,poses))
        banks[case]={'provenance':'MODERNE','rig_sha256':build['rig_sha256'],
            'recipe_sha256':build['recipe_sha256'],'attachment':bindings,'ticks':updates}
        print('Checked native held-component bank: '+case,file=sys.stderr,flush=True)
    return {'schema_version':1,'scope':'modern_held_equipment_banks_native_attachment_and_ticks',
        'library_sha256':DLL_SHA,'banks':banks,
        'attachment_totals':{key:sum(row['attachment'][key] for row in banks.values())
            for key in ('sequences','operations','owner_allocations','owner_releases')},
        'tick_totals':{key:sum(row['ticks'][key] for row in banks.values())
            for key in ('sequences','ticks','pose_calls','written_channels')},
        'max_pose_error':max(row['ticks']['max_error'] for row in banks.values()),
        'commercial_geometry_or_keys_used':False,'pinned_commercial_code_emulated':True,
        'allocator_is_bounded_double':True,'initial_pose_is_explicit_seed':True,
        'events_or_callbacks_called':False,'native_loader_executed':False,
        'skin_or_renderer_called':False,'player_hands_created':False,'hose_deformation_implemented':False,
        'functional_weapon_implemented':False,'loaded_scene_qualified':False,
        'time_unit_seconds_qualified':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',required=True,type=Path);parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.library.read_bytes())
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native modern-equipment audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
