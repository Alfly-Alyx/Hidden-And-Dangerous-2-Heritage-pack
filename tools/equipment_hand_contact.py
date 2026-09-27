#!/usr/bin/env python3
"""Private hand-vertex penetration measurements against serialized modern grips.

This does not qualify contact: triangles crossing a surface with all vertices
outside, other weapon pieces, and hand self-intersections remain separate work.
"""
import argparse
import json
from pathlib import Path

from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS, read_hands
from build_equipment_fpv_animation import numeric_world
from build_equipment_fpv_view_bank import preview_meshes, view_grips
from build_equipment_hand_grips import RECIPE, posed_hand_mesh
from build_modern_equipment_hose import digest
from convex_contact import planes, measure
from five_ds import parse_5ds
from fpv_contact_constraints import targets
from fpv_transition_contact_audit import load_bank
from hand_pose_ik import author_pose, pinned_skin
from menu_gui_audit import parse_4ds_nodes
from modern_thumb_pose import DEFAULT, apply, turns

GRIPS = {'F35': {'L':'MOD_front_handrest','R':'MOD_grip'},
         'F2': {'L':'MOD_front_grip','R':'MOD_rear_grip'}}


def vertex_groups(skin):
    nodes = {n['index']:n for n in skin['nodes']}
    names = [nodes[index]['name'] for index in skin['joint_node_indices']]
    result = {side:{part:[] for part in ('thumb','fingers','palm_or_arm')} for side in ('L','R')}
    for i,(bone,weight) in enumerate(skin['pairs']):
        # Classify by the dominant of the two actual native skin influences.
        index = skin['parents'][bone-1] if weight>128 else bone
        if not index: raise ValueError('Hand vertex has dominant model-root influence')
        name = names[index-1]
        side = next((s for s in result if name.startswith('Bip01 '+s+' ')),None)
        if side is None: raise ValueError('Unclassified private hand vertex')
        part = 'thumb' if 'Finger0' in name else ('fingers' if 'Finger' in name else 'palm_or_arm')
        result[side][part].append(i)
    return result


def measure_pose(hand_raw, poses, gear_meshes, case):
    _,skin = pinned_skin(hand_raw)
    hand = posed_hand_mesh(hand_raw,poses,1)
    groups = vertex_groups(skin)
    result = {}
    for side, name in GRIPS[case].items():
        selected = [m for m in gear_meshes if m.name==name]
        if len(selected)!=1: raise ValueError('Missing or split grip mesh')
        grip=selected[0]
        support=planes(grip.points,grip.triangles)
        result[side]={part:measure([hand.points[i] for i in indices],support)
                      for part,indices in groups[side].items()}
    return result


def sample(case, hand_raw, rig, clip_raw, time, spec, *, thumb=None, curls=None):
    _,skin=pinned_skin(hand_raw)
    names,seeds=model_poses(hand_raw)
    clip=parse_5ds(clip_raw)
    if type(time) is not int or not 0<=time<=clip['frame_end']*40:
        raise ValueError('Unreviewed private contact sample time')
    tracks={t['name']:t['channels'] for t in clip['tracks']}
    _,poses=numeric_world(skin['nodes'],dict(zip(names,seeds)),tracks,time)
    gear=preview_meshes(rig,clip_raw,time)
    if curls is not None:
        nodes=parse_4ds_nodes(rig)['nodes'];gn,gi=model_poses(rig)
        gw,_=numeric_world(nodes,dict(zip(gn,gi)),tracks,time)
        poses,_=author_pose(hand_raw,targets(gw,view_grips(spec,case)),
                           {s:{'finger_curl_degrees':curls[s]} for s in ('L','R')},
                           arm_rotation_policy='bend_plane')
    if thumb is not None:
        by_name={n['name']:n for n in skin['nodes']}
        bases={name:skin['rest_world'][by_name[name]['index']][0] for name in turns(thumb)}
        poses=apply(poses,bases,thumb)
    return poses,measure_pose(hand_raw,poses,gear,case)


def audit(game,bank_root,archives_only=False):
    hands,excluded=read_hands(game,archives_only=archives_only)
    spec=json.loads(RECIPE.read_text(encoding='utf-8'));rows=[]
    for case in GRIPS:
        for source in HAND_MODELS:
            raw=hands[source]
            rig,clips=load_bank(bank_root/(case+'_CorrectedFPV_v1'),case,source,raw)
            for clip,time in (('Idle1',0),('Aim',480)):
                results={label:sample(case,raw,rig,clips[clip]['data'],time,spec,thumb=thumb)[1]
                         for label,thumb in (('source_rest_thumbs',None),('modern_thumb_candidate',DEFAULT))}
                rows.append({'case':case,'source':source,'source_sha256':digest(raw),
                    'model_sha256':digest(rig),'clip':clip,'clip_sha256':digest(clips[clip]['data']),
                    'time':time,'measurements':results})
    return {'schema_version':1,'runtime_status':'pending','scope':'private_vertex_grip_penetration',
        'samples':rows,'thumb_spec':DEFAULT,'excluded_loose_overrides':excluded,
        'source_geometry_modified':False,'commercial_geometry_exported':False,
        'source_animation_keys_read':False,'native_skin_executed':False,
        'skin_numeric_reference_used':True,'all_weapon_parts_checked':False,
        'surface_crossings_checked':False,'hand_self_intersection_checked':False,
        'finger_contact_qualified':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--bank-root',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output.exists(): raise ValueError('Report exists; use a fresh name')
        report=audit(args.game,args.bank_root,args.archives_only)
        with args.json_output.open('x',encoding='utf-8') as output:
            json.dump(report,output,indent=2);output.write('\n')
        print(json.dumps({'samples':len(report['samples']),'output':str(args.json_output),
                          'finger_contact_qualified':False}))
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Private hand contact measurement refused: '+str(error));return 1


if __name__=='__main__': raise SystemExit(main())
