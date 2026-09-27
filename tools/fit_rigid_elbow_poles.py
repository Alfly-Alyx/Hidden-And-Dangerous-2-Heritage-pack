#!/usr/bin/env python3
"""Bounded modern elbow-hint candidates on selected private diagnostic poses.

This only addresses reported arm crossings. It does not certify other frames,
fingers, self-contact, camera appearance or continuous motion. No auto-promotion.
"""
import argparse
from copy import deepcopy
import itertools
import json
from pathlib import Path
import sys

from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS,read_hands
from build_equipment_hand_grips import RECIPE,posed_hand_mesh
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import compile_bank,preview_meshes
from build_rigid_weapon_hand_bank import BASE_PROFILE,PROFILE,configuration,placed_tracks,targets,stow_offset,stow_motion,curl_spec
from convex_contact import surface_measure
from hand_pose_ik import author_pose,pinned_skin
from modern_contact_cells import cells
import modern_animation as motion
from five_ds import parse_5ds

SCENARIOS={('MG34','L'):(('Rel',1600,('MOD_side_drum','MOD_drum_outer_lid')),),
           ('MG34','R'):(('Arm',0,('fpv_weapon','MOD_stock','MOD_charging_handle')),),
           ('ZK383','L'):(('Arm',0,('MOD_side_magazine','MOD_magazine_endplate')),
                          ('Arm',480,('MOD_side_magazine','MOD_magazine_endplate')))}


def candidate_poles(seed,*,wide=False):
    from hand_pose_ik import vector
    seed=vector(seed)
    if type(wide) is not bool or any(abs(v)>1 for v in seed):raise ValueError('Unreviewed elbow candidate domain')
    offsets=(-.5,-.25,0,.25,.5) if wide else (-.25,0,.25)
    return [list(seed)]+[[round(v+d,9) for v,d in zip(seed,delta)] for delta in itertools.product(offsets,repeat=3)
                        if any(delta) and all(abs(v+d)<=1 for v,d in zip(seed,delta))]


def fit(case,side,hands,profile,*,wide=False):
    recipe,rig,clips,_=compile_bank(case)
    base=json.loads(BASE_PROFILE.read_text(encoding='utf-8'));spec=json.loads(RECIPE.read_text(encoding='utf-8'))
    grips,thumb,translation,_=configuration(profile,base,spec,case);prepared=[]
    for name,time,obstacles in SCENARIOS[(case,side)]:
        source=clips[name][1];tracks=placed_tracks(source,translation,stow=stow_offset(profile,case),clip_name=name,
                                               motion_spec=stow_motion(profile,case))
        raw=motion._encode_transform_tracks(parse_5ds(source)['frame_end'],tracks,preserve_native_rotations=True,name_validator=lambda n:True)
        volumes=[v for m in preview_meshes(rig,raw,time) if m.name in obstacles for v in cells(m,recipe['parts'])]
        for model in HAND_MODELS:
            hand=hands[model];_,skin=pinned_skin(hand);names,poses=model_poses(hand)
            by_index={n['index']:n['name'] for n in skin['nodes']};jn=[by_index[i] for i in skin['joint_node_indices']]
            labels=[jn[(skin['parents'][bone-1] if weight>128 else bone)-1] for bone,weight in skin['pairs']]
            selected={i for i,label in enumerate(labels) if label in {f'Bip01 {side} Forearm',f'Bip01 {side} UpperArm'}}
            mesh=posed_hand_mesh(hand,dict(zip(names,poses)),1)
            faces=[face for face in mesh.triangles if any(i in selected for i in face)]
            prepared.append((hand,targets(rig,tracks,time,grips),faces,volumes))
    rows=[]
    for pole in candidate_poles(grips[side]['elbow_pole'],wide=wide):
        count=0;area=0;depth=0
        for raw,wanted,faces,volumes in prepared:
            wanted=deepcopy(wanted);wanted[side]['pole']=pole
            poses,_=author_pose(raw,wanted,curl_spec(grips),
                                 arm_rotation_policy='bend_plane')
            mesh=posed_hand_mesh(raw,poses,1)
            for v in volumes:
                result=surface_measure(mesh.points,faces,v['support'],volume_bounds=v['bounds'],boundary_support=v['boundary_support'])
                count+=result['penetrating_triangles'];area+=result['inset_surface_area'];depth=max(depth,result['max_depth_lower_bound'])
        rows.append({'pole':pole,'penetrating_triangle_cells':count,'inset_area_sum':area,'max_cell_boundary_depth':depth})
    seed=grips[side]['elbow_pole']
    chosen=min(rows,key=lambda r:(r['penetrating_triangle_cells'],r['inset_area_sum'],sum((a-b)**2 for a,b in zip(r['pole'],seed))))
    return {'chosen':chosen,'candidates':rows,'diagnostic_poses':len(prepared),'finger_poses_not_evaluated':True,
            'not_all_equipment_pieces_or_animation_frames_checked':True,'auto_promoted':False,'contact_qualified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--profile',type=Path,default=PROFILE)
    parser.add_argument('--case',choices=('MG34','ZK383'));parser.add_argument('--side',choices=('L','R'))
    parser.add_argument('--wide',action='store_true')
    parser.add_argument('--json-output',type=Path,required=True);args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        profile=json.loads(args.profile.read_text(encoding='utf-8'));hands,excluded=read_hands(args.game,archives_only=args.archives_only)
        rows={}
        for case,side in SCENARIOS:
            if (args.case and case!=args.case) or (args.side and side!=args.side):continue
            row=fit(case,side,hands,profile,wide=args.wide);rows.setdefault(case,{})[side]=row
            print(case,side,json.dumps(row['chosen']),file=sys.stderr,flush=True)
        if not rows:raise ValueError('No reviewed elbow scenario matches selection')
        report={'schema_version':1,'provenance':'MODERNE','runtime_status':'pending','cases':rows,
            'source_profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),'excluded_loose_overrides':excluded,
            'wide_candidates':args.wide,
            'commercial_geometry_exported':False,'derived_poses_exported':False,'game_started':False,'game_modified':False}
        with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Rigid elbow fitting refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
