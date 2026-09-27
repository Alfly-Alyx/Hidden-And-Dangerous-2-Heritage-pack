#!/usr/bin/env python3
"""Original ZK-383 rigid-part bank, disabled; not a functional/FPV weapon."""
import argparse
import json
from pathlib import Path

import build_modern_asset as asset
from build_modern_animation_bank import compile_generated_model,write_generated_bank
from build_modern_equipment_hose import digest

DIRECTORY=asset.ROOT/'experimental/GAROTA_AND_ZK383'
MODEL_SHA='1730926a7468d5a91ec4ae19467ee2613905146caa329f7c0a163f09a9c30032'


def inputs():
    return tuple(json.loads((DIRECTORY/name).read_text(encoding='utf-8')) for name in
                 ('modern-zk383-world.json','modern-zk383-animation.json'))


def compile_bank(recipe,spec):
    if (recipe.get('name')!='PROTOTYPE_HERITAGE_ZK383World' or spec.get('name')!='ZK3'
            or spec.get('model_sha256')!=MODEL_SHA):
        raise ValueError('Expected the pinned original ZK-383 visual model and short alias')
    meshes=asset.build_meshes(recipe);source=asset.encode_4ds(recipe,meshes)
    if digest(source)!=MODEL_SHA:raise ValueError('Modern ZK-383 source geometry changed')
    return compile_generated_model(source,meshes,spec)


def audit_native(library,compiled):
    from animation_tick_audit import model_poses,audit_cases as audit_tick,bank_cases as tick_cases
    from animation_attach_audit import audit_cases as audit_attach,bank_cases as attachment_cases
    from ls3d_attach_oracle import AttachOracle
    from ls3d_tick_oracle import TickOracle
    from ls3d_animation_load_oracle import AnimationLoadOracle
    from ls3d_math_oracle import DLL_SHA
    rig,clips,_,build=compiled;names,poses=model_poses(rig)
    loader=AnimationLoadOracle(library);loads={}
    for name,(stem,raw) in clips.items():
        receipt=loader.load(raw,stem+'.I3D')
        if (receipt.get('animation_sha256')!=digest(raw)
                or receipt.get('native_animation_open_and_relocation_executed') is not True
                or receipt.get('relocated_body_and_name_match') is not True
                or receipt.get('requested_memory_filename')!=stem+'.5ds'):
            raise ValueError('Incomplete native ZK-383 animation load')
        loads[name]=receipt
    raw_clips={name:raw for name,(_,raw) in clips.items()}
    attached=audit_attach(AttachOracle(library),attachment_cases(names,raw_clips))
    ticks=audit_tick(TickOracle(library),tick_cases(names,raw_clips,poses))
    return {'schema_version':1,'scope':'modern_zk383_rigid_part_native_animation','provenance':'MODERNE',
        'runtime_status':'pending','library_sha256':DLL_SHA,'rig_sha256':build['rig_sha256'],
        'recipe_sha256':build['recipe_sha256'],'native_loads':loads,'attachment':attached,'ticks':ticks,
        'pinned_commercial_code_emulated':True,'native_subsystems_use_separate_emulators':True,
        'initial_pose_is_explicit_seed':True,'allocator_is_bounded_double':True,
        'commercial_geometry_or_animation_keys_used':False,'player_hands_created':False,
        'events_or_callbacks_called':False,'skin_or_renderer_called':False,
        'functional_weapon_implemented':False,'companion_model_loading_qualified':False,
        'time_unit_seconds_qualified':False,'engine_validated':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-name')
    parser.add_argument('--native-library',type=Path)
    parser.add_argument('--native-report',type=Path)
    args=parser.parse_args(argv)
    try:
        if bool(args.native_library)!=bool(args.native_report):
            raise ValueError('Native library and fresh report path must be provided together')
        if args.native_report and args.native_report.exists():raise ValueError('Native report exists; use a fresh name')
        output=asset.output_directory(asset.ROOT,args.output_name) if args.output_name else None
        recipe,spec=inputs();compiled=compile_bank(recipe,spec)
        report=compiled[3]
        if output:report=write_generated_bank(recipe,spec,compiled,output)
        if args.native_library:
            native=audit_native(args.native_library.read_bytes(),compiled)
            with args.native_report.open('x',encoding='utf-8') as stream:
                json.dump(native,stream,indent=2);stream.write('\n')
        print(json.dumps({'output':str(output) if output else None,'rig_sha256':report['rig_sha256'],
            'clips':len(report['clips']),'native_report':str(args.native_report) if args.native_report else None,
            'player_hands':False,'engine_validated':False,'game_started':False},indent=2))
        return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Modern ZK-383 animation bank refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
