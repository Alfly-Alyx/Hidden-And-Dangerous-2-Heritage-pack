#!/usr/bin/env python3
"""Original hose clips -> native poses/palette/skin, both LODs, no game scene."""
import argparse
import json
from pathlib import Path
import sys

from build_modern_equipment_hose import inputs,compile_hose_bank,CASES
from build_modern_equipment_animation import compile_equipment_bank
from five_ds import parse_5ds
from four_ds_skin import read_reviewed
from benelli_pose_chain_audit import key_window,initial_poses,check_pose
from ls3d_math_oracle import DLL_SHA
from ls3d_pose_oracle import PoseOracle
from ls3d_palette_oracle import PaletteOracle
from ls3d_skin_oracle import SkinOracle,transformed
from ls3d_palette_audit import check_receipt as check_palette
from ls3d_skin_audit import check_receipt as check_skin


def held_endpoint(matrix,source,pivot):
    moved=transformed([a-b for a,b in zip(source[:3],pivot)],matrix)
    return [a+b for a,b in zip(moved,pivot)]


def audit(library,*,step=20,progress=None):
    if step not in (20,40):raise ValueError('Expected integer or half-frame samples')
    pose_machine=PoseOracle(library);palette_machine=PaletteOracle(library);skin_machine=SkinOracle(library)
    reports={};totals=dict.fromkeys(('samples','node_poses','joint_poses','lod_evaluations','vertices','endpoint_vertices'),0)
    errors=dict.fromkeys(('pose','palette','skin','fixed_pack_endpoint','held_endpoint'),0)
    for case in CASES:
        args=inputs(case);raw,clips,_,built=compile_hose_bank(*args)
        held,held_clips,_,_=compile_equipment_bank(*args[:3])
        skins=[read_reviewed(raw,allow_multiple_lods=True,lod=i) for i in (0,1)]
        initial=initial_poses(raw,skins[0]);nodes=skins[0]['nodes'];clip_reports={}
        held_initial={'position':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]}
        for name,(_,animation) in clips.items():
            clip=parse_5ds(animation);tracks={t['name']:t for t in clip['tracks']}
            held_track=next(t for t in parse_5ds(held_clips[name][1])['tracks'] if t['name']=='MOD_held_pivot')
            samples=0
            for time in range(0,clip['frame_end']*40+1,step):
                poses={}
                for node in nodes:
                    channels={k:key_window(v,time) for k,v in tracks[node['name']]['channels'].items()}
                    row=pose_machine.apply(initial[node['name']],[{'active':True,'weight':1,'time':time,'channels':channels}])
                    check_pose(row);poses[node['index']]=row['pose'];errors['pose']=max(errors['pose'],row['max_error'])
                channels={k:key_window(v,time) for k,v in held_track['channels'].items()}
                held_pose=pose_machine.apply(held_initial,[{'active':True,'weight':1,'time':time,'channels':channels}])
                check_pose(held_pose);errors['pose']=max(errors['pose'],held_pose['max_error'])
                # Native SetRot keeps identity when float32 |w| >= 1, even if
                # tiny x/y/z remain. A normalized mathematical matrix here
                # would falsely diagnose a separated endpoint at small angles.
                identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
                held_palette=palette_machine.assemble([{**held_pose['pose'],'parent':-1}],[identity])
                check_palette(held_palette,1)
                errors['palette']=max(errors['palette'],max(held_palette['max_errors'].values()))
                joints=[{**poses[index],'parent':-1} for index in skins[0]['joint_node_indices']]
                palette=palette_machine.assemble(joints,skins[0]['inverse_binds']);check_palette(palette,len(joints))
                errors['palette']=max(errors['palette'],max(palette['max_errors'].values()))
                for skin in skins:
                    row=skin_machine.deform(skin['vertices'],skin['pairs'],palette['palette'],skin['parents'])
                    check_skin(row,len(skin['vertices']));errors['skin']=max(errors['skin'],row['max_error'])
                    for source,(bone,_),actual in zip(skin['vertices'],skin['pairs'],row['values']):
                        weight=built['influence_weights'][bone-1]
                        if weight not in (0,1):continue
                        if weight==0:expected=source[:3];key='fixed_pack_endpoint'
                        else:
                            expected=held_endpoint(held_palette['palette'][0],source,built['pivot']);key='held_endpoint'
                        error=max(abs(a-b) for a,b in zip(actual[:3],expected));errors[key]=max(errors[key],error)
                        if error>2e-6:raise ValueError(f'Native visual hose endpoint mismatch: {case}/{name}, time={time}, bone={bone}, error={error}')
                        totals['endpoint_vertices']+=1
                    totals['lod_evaluations']+=1;totals['vertices']+=row['vertices']
                totals['samples']+=1;totals['node_poses']+=len(nodes)+1;totals['joint_poses']+=len(joints);samples+=1
            clip_reports[name]={'frame_end':clip['frame_end'],'samples':samples}
            if progress:progress(case,name,samples)
        reports[case]={'rig_sha256':built['rig_sha256'],'clips':clip_reports,'lod_vertices':built['lod_vertices']}
    return {'schema_version':1,'scope':'original_hose_native_pose_palette_skin_and_fixed_pack_held_raccords',
        'library_sha256':DLL_SHA,'sampling':'half-frames' if step==20 else 'integer-frames',
        'seed_policy':'explicit_generated_rest_at_each_sample','cases':reports,'totals':totals,'max_errors':errors,
        'both_lods_checked':True,'commercial_geometry_or_keys_used':False,'pinned_commercial_code_emulated':True,
        'native_loader_executed':False,'same_runtime_memory_chain':False,'runtime_clip_transitions_qualified':False,
        'events_or_callbacks_called':False,'renderer_called':False,'collision_or_length_constraint':False,
        'player_attachment_qualified':False,'loaded_scene_qualified':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',required=True,type=Path);parser.add_argument('--json-output',type=Path)
    parser.add_argument('--sampling',choices=('integer-frames','half-frames'),default='half-frames');args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.library.read_bytes(),step=20 if args.sampling=='half-frames' else 40,
            progress=lambda case,clip,count:print(f'Checked native visual hose: {case} / {clip} / {count}',file=sys.stderr,flush=True))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native modern hose audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
