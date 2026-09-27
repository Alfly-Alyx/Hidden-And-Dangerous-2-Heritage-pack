#!/usr/bin/env python3
"""Private authored grip poses through pinned native palette/skin, no animation.

Every pose is an explicit modern IK result on a commercial rest skeleton.
No 5DS playback, native loader, rendering, camera or gameplay is qualified.
"""
import argparse
import json
from pathlib import Path
import sys

from build_equipment_hand_grips import RECIPE,validate_spec,effective_hands,targets
from build_modern_equipment_assembly import inputs,compile_assembly,CASES
from benelli_fpv_rig_audit import read_hands,HAND_MODELS,HAND_PINS
from hand_pose_ik import author_pose,pinned_skin
from ls3d_palette_oracle import PaletteOracle
from ls3d_skin_oracle import SkinOracle
from ls3d_palette_audit import check_receipt as check_palette
from ls3d_skin_audit import check_receipt as check_skin
from ls3d_math_oracle import DLL_SHA
from build_modern_equipment_hose import digest


def audit(hands,spec,library,progress=None):
    if set(hands)!=set(HAND_PINS):raise ValueError('Incomplete pinned hand source set')
    for name,raw in hands.items():
        if (len(raw),digest(raw))!=HAND_PINS[name][1:]:raise ValueError('Changed pinned hand source')
    palette_machine=PaletteOracle(library);skin_machine=SkinOracle(library);reports={}
    totals=dict.fromkeys(('poses','joint_poses','vertices','wrist_targets'),0)
    errors=dict.fromkeys(('palette','skin','wrist_position'),0)
    for case in CASES:
        rig,clips,assembly=compile_assembly(*inputs(case));validate_spec(spec,case,rig);variants={}
        grips={side:{'finger_curl_degrees':hand['finger_curl_degrees']} for side,hand in effective_hands(spec,case).items()}
        for name in HAND_MODELS:
            _,skin=pinned_skin(hands[name]);nodes={n['index']:n for n in skin['nodes']}
            bones={node:i for i,node in enumerate(skin['joint_node_indices'])};by_name={n['name']:n for n in skin['nodes']}
            states={}
            for clip,(_,animation) in clips.items():
                end=assembly['clips'][clip]['frame_end'];count=0
                for frame in range(end+1):
                    requested=targets(rig,animation,frame,spec,case);poses,_=author_pose(hands[name],requested,grips)
                    joints=[{**poses[nodes[index]['name']],
                        'parent':-1 if nodes[index]['parent_id']==1 else bones[nodes[index]['parent_id']]}
                        for index in skin['joint_node_indices']]
                    matrices=palette_machine.assemble(joints,skin['inverse_binds']);check_palette(matrices,len(joints))
                    deformed=skin_machine.deform(skin['vertices'],skin['pairs'],matrices['palette'],skin['parents'])
                    check_skin(deformed,len(skin['vertices']))
                    errors['palette']=max(errors['palette'],max(matrices['max_errors'].values()))
                    errors['skin']=max(errors['skin'],deformed['max_error'])
                    for side in ('L','R'):
                        bone=bones[by_name[f'Bip01 {side} Hand']['index']]
                        actual=matrices['world_matrices'][bone][12:15]
                        error=max(abs(a-b) for a,b in zip(actual,requested[side]['position']))
                        if error>5e-6:raise ValueError('Native wrist missed authored target')
                        errors['wrist_position']=max(errors['wrist_position'],error)
                        totals['wrist_targets']+=1
                    count+=1;totals['poses']+=1;totals['joint_poses']+=len(joints);totals['vertices']+=deformed['vertices']
                states[clip]={'poses':count,'frame_end':end}
                if progress:progress(case,name,clip,count)
            variants[name]={'sha256':HAND_PINS[name][2],'states':states}
        reports[case]={'assembly_sha256':assembly['rig_sha256'],'variants':variants}
    return {'schema_version':1,'scope':'private_modern_hand_grip_pose_native_palette_and_skin',
        'provenance':'DERIVE_MODERNE_SUR_SQUELETTE_COMMERCIAL','library_sha256':DLL_SHA,
        'specification_sha256':digest(json.dumps(spec,sort_keys=True).encode()),'cases':reports,
        'totals':totals,'max_errors':errors,'seed_policy':'independent_authored_IK_pose_per_integer_frame',
        'commercial_hand_geometry_used_privately':True,'commercial_geometry_or_keys_exported':False,
        'original_animation_keys_read':False,'native_animation_playback_executed':False,'native_loader_executed':False,
        'finger_contact_qualified':False,'thumb_pose_authored':False,'camera_calibrated':False,
        'events_renderer_gameplay_called':False,'player_or_ai_attachment_qualified':False,
        'game_started':False,'game_modified':False,'engine_validated':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path);parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        hands,excluded=read_hands(args.game,archives_only=args.archives_only)
        report=audit(hands,json.loads(RECIPE.read_text(encoding='utf-8')),(args.game/'LS3DF.dll').read_bytes(),
            lambda case,source,clip,count:print(f'Checked native grip: {case} / {source} / {clip} / {count}',file=sys.stderr,flush=True))
        report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native hand grip audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
