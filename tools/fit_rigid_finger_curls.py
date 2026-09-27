#!/usr/bin/env python3
"""Fit MODERN individual ZK383 right-digit choices in private Idle poses.

Both hand variants and every equipment cell participate in exact face checks.
Only modern curl choices and metrics are emitted; no commercial poses/meshes,
automatic profile promotion, game launch or contact qualification.
"""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import sys

from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS,read_hands
from build_equipment_hand_grips import posed_hand_mesh
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import compile_bank,preview_meshes
from build_rigid_weapon_hand_bank import BASE_PROFILE,PROFILE,RECIPE,configuration,placed_tracks,targets,curl_spec
from fit_modern_grip_candidates import digit_indices
from fit_rigid_weapon_grips import finite_digit_gaps
from hand_pose_ik import author_pose,pinned_skin,finger_curls
from modern_contact_cells import cells,prepare_surface,measure_surface_cells
from modern_thumb_pose import apply,turns
from five_ds import parse_5ds
import modern_animation as motion

CONTACTS={'1':'MOD_trigger','2':'MOD_stock','3':'MOD_stock','4':'MOD_stock'}


def refine(seed,evaluate):
    """Never trade a new crossing for a better proximity score."""
    finger_curls({'finger_curl_degrees':seed})
    def checked(values):
        cost=evaluate(values)
        if (not isinstance(cost,tuple) or len(cost)!=2 or type(cost[0]) is not int or cost[0]<0
                or type(cost[1]) not in (int,float) or not math.isfinite(cost[1]) or cost[1]<0):
            raise ValueError('Invalid individual finger measurement')
        return (*cost,sum((a-b)**2 for a,b in zip(values,seed)))
    best=seed[:];cost=checked(best)
    for step in (15,7.5,3.75,1.875,.9375):
        for sweep in range(3):
            changed=False
            for axis in range(3):
                for value in (max(-110,best[axis]-step),min(110,best[axis]+step)):
                    trial=best[:];trial[axis]=value;candidate=checked(trial)
                    if candidate<cost:best,cost,changed=trial,candidate,True
            if not changed:break
    return best,cost


def fit(hands,profile):
    recipe,rig,clips,_=compile_bank('ZK383')
    grips,thumb,translation,_=configuration(profile,json.loads(BASE_PROFILE.read_text(encoding='utf-8')),
                                           json.loads(RECIPE.read_text(encoding='utf-8')),'ZK383')
    source=clips['Idle1'][1];tracks=placed_tracks(source,translation)
    raw=motion._encode_transform_tracks(parse_5ds(source)['frame_end'],tracks,
                                       preserve_native_rotations=True,name_validator=lambda n:True)
    meshes=preview_meshes(rig,raw,0);volumes=[v for mesh in meshes for v in cells(mesh,recipe['parts'])]
    surfaces={digit:[[m.points[i] for i in face] for m in meshes if m.name==name for face in m.triangles]
              for digit,name in CONTACTS.items()}
    if any(not faces for faces in surfaces.values()):raise ValueError('Missing explicit digit contact piece')
    prepared=[]
    for source in HAND_MODELS:
        hand=hands[source];_,skin=pinned_skin(hand);nodes={n['name']:n for n in skin['nodes']}
        bases={n:skin['rest_world'][nodes[n]['index']][0] for n in turns(thumb)}
        _,digits=digit_indices(skin,'R');prepared.append((source,hand,bases,digits))
    wanted=targets(rig,tracks,0,grips,clip_name='Idle1');chosen=curl_spec(grips)
    before=deepcopy(chosen);rows={}
    for digit in CONTACTS:
        cache={}
        def measure(values):
            key=tuple(values)
            if key not in cache:
                trial=deepcopy(chosen);trial['R'].setdefault('finger_curl_overrides',{})[digit]=values[:]
                variants={}
                for source,hand,bases,digits in prepared:
                    poses,_=author_pose(hand,wanted,trial,arm_rotation_policy='bend_plane')
                    mesh=posed_hand_mesh(hand,apply(poses,bases,thumb),1)
                    measured=measure_surface_cells(prepare_surface(mesh.points,mesh.triangles),volumes)
                    gap=finite_digit_gaps(mesh.points,{int(digit):digits[int(digit)]},surfaces[digit])[0]
                    variants[source]={'penetrating_triangle_cells':measured['penetrating_triangle_cells'],
                        'max_cell_boundary_depth':measured['max_cell_boundary_depth'],'finite_digit_gap':gap}
                cost=(sum(v['penetrating_triangle_cells'] for v in variants.values()),
                      sum(v['finite_digit_gap']**2 for v in variants.values()))
                cache[key]=(cost,variants)
            return cache[key][0]
        seed=finger_curls(chosen['R'])[digit];measure(seed);initial=deepcopy(cache[tuple(seed)][1])
        values,cost=refine(seed,measure)
        chosen['R'].setdefault('finger_curl_overrides',{})[digit]=values
        rows[digit]={'contact_piece':CONTACTS[digit],'before':initial,'after':cache[tuple(values)][1],
                     'angles':values,'cost':list(cost),'evaluations':len(cache)}
        print('ZK383 R digit',digit,json.dumps(rows[digit]),file=sys.stderr,flush=True)
    return {'finger_curl_overrides':chosen['R']['finger_curl_overrides'],'digits':rows,
        'input_curls':before,'all_equipment_pieces_checked':True,'all_hand_faces_checked':True,
        'both_hand_variants_checked':True,'idle_sample_time':0,'self_intersection_checked':False,
        'serialized_animation_contacts_checked':False,'camera_qualified':False,'auto_promoted':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--profile',type=Path,default=PROFILE)
    parser.add_argument('--json-output',type=Path,required=True);args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Use a fresh finger report')
        profile=json.loads(args.profile.read_text(encoding='utf-8'));hands,excluded=read_hands(args.game,archives_only=args.archives_only)
        report={'schema_version':1,'provenance':'MODERNE','runtime_status':'pending','case':'ZK383','side':'R',
            'profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),'excluded_loose_overrides':excluded,
            'result':fit(hands,profile),'commercial_geometry_exported':False,'commercial_poses_exported':False,
            'game_started':False,'game_modified':False,'contact_qualified':False}
        with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Individual rigid finger fitting refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
