#!/usr/bin/env python3
"""Bounded native clip/tick and diagnostic palette checks for rigid FPV banks.

Rigid frames are represented as diagnostic joints solely to check matrix
composition. No real skin, model loader, clone, renderer or game is executed.
"""
import argparse
import json
from pathlib import Path
import sys

from animation_attach_audit import op
from animation_tick_audit import model_poses,check_receipt
from build_equipment_fpv_animation import numeric_world
from build_equipment_hand_animation import IDENTITY
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import CASES,original,compile_bank
from five_ds import parse_5ds
from ls3d_animation_load_oracle import AnimationLoadOracle
from ls3d_math_oracle import DLL_SHA
from ls3d_palette_oracle import PaletteOracle
from ls3d_tick_oracle import TickOracle
from menu_gui_audit import parse_4ds_nodes
from modern_fpv_axes import matrix


def audit(library):
    loader,tick,palette=AnimationLoadOracle(library),TickOracle(library),PaletteOracle(library)
    reports={};totals={'loads':0,'sequences':0,'ticks':0,'diagnostic_palettes':0}
    errors={'tick':0,'palette':0,'source_at_keys':0,'source_between_keys':0}
    for case in CASES:
        _,view,clips,build=compile_bank(case)
        _,_,(source,old_clips,_,_)=original(case)
        if digest(source)!=build['source_rig_sha256']:raise ValueError('Changed original rigid bank')
        names,seeds=model_poses(view);nodes=parse_4ds_nodes(view)['nodes']
        sn,sp=model_poses(source);snodes=parse_4ds_nodes(source)['nodes']
        rows={}
        for name,(stem,raw) in clips.items():
            receipt=loader.load(raw,stem+'.I3D')
            if (receipt.get('animation_sha256')!=digest(raw)
                    or receipt.get('native_animation_open_and_relocation_executed') is not True
                    or receipt.get('relocated_body_and_name_match') is not True
                    or receipt.get('requested_memory_filename')!=stem+'.5ds'):
                raise ValueError('Incomplete native rigid FPV load')
            totals['loads']+=1;end=parse_5ds(raw)['frame_end'];elapsed=0
            old_tracks={t['name']:t['channels'] for t in parse_5ds(old_clips[name][1])['tracks']}
            per_clip={'source_at_keys':0,'source_between_keys':0}

            def observe(index,delta,values):
                nonlocal elapsed
                elapsed+=delta
                if len(values)!=len(nodes):raise ValueError('Incomplete rigid pose observation')
                actual=palette.assemble([{**pose,'parent':node['parent_id']-1} for pose,node in zip(values,nodes)],
                                        [IDENTITY]*len(nodes))
                expected,_=numeric_world(snodes,dict(zip(sn,sp)),old_tracks,min(elapsed,end*40))
                world=dict(zip(names,actual['world_matrices']))
                key='source_at_keys' if min(elapsed,end*40)%40==0 else 'source_between_keys'
                error=max(abs(a-b) for old,new in build['flattening']['source_to_fpv_names'].items()
                          for a,b in zip(matrix(expected[old]),world[new]))
                if error>(5e-6 if key=='source_at_keys' else .0002):
                    raise ValueError(f'Rigid rebake drift: {case}/{name}/{elapsed}: {error}')
                errors[key]=max(errors[key],error);per_clip[key]=max(per_clip[key],error)
                errors['palette']=max(errors['palette'],*actual['max_errors'].values())
                totals['ticks']+=1;totals['diagnostic_palettes']+=1

            deltas=[0]+[20]*(2*end)+[0,20]
            native_clips={name:{'data':raw,'mode':1}};operations=[op(name,7)]
            result=tick.sequence_with_ticks(names,native_clips,operations,seeds,deltas,pose_observer=observe)
            check_receipt(result,names,native_clips,operations,seeds,deltas,9)
            errors['tick']=max(errors['tick'],result['max_error']);totals['sequences']+=1
            rows[name]={'sha256':digest(raw),'frame_end':end,'ticks':len(deltas),'load':receipt,'max_errors':per_clip}
            print(case,name,'native rigid FPV poses checked',file=sys.stderr,flush=True)
        reports[case]={'model_sha256':digest(view),'source_rig_sha256':digest(source),'clips':rows}
    return {'schema_version':1,'scope':'modern_rigid_fpv_native_clips_and_diagnostic_matrices',
        'provenance':'MODERNE','runtime_status':'pending','library_sha256':DLL_SHA,'cases':reports,
        'totals':totals,'max_errors':errors,'native_subsystems_use_separate_emulators':True,
        'rigid_frames_are_diagnostic_joints':True,'source_world_uses_numeric_reference':True,
        'pinned_commercial_code_emulated':True,'commercial_geometry_or_animation_keys_used':False,
        'real_skin_or_renderer_executed':False,'model_load_or_clone_executed':False,
        'player_hands_created':False,'camera_calibrated':False,'events_or_gameplay_implemented':False,
        'game_started':False,'game_modified':False,'engine_validated':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',required=True,type=Path)
    parser.add_argument('--json-output',required=True,type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.library.read_bytes())
        with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native rigid FPV audit refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
