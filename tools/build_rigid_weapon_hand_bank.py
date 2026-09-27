#!/usr/bin/env python3
"""Private hand/weapon clips for original rigid FPV candidates, never installed.

Only pinned commercial rest skeletons and geometry are read. Modern targets,
finger/thumb choices and placement are authored here; no commercial animation
keys are read or source hand geometry exported. Initial grips remain unqualified.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re

import build_modern_asset as asset
import modern_animation as motion
from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS,read_hands
from build_equipment_fpv_animation import numeric_world
from build_equipment_hand_animation import HAND_NAMES,PROVENANCE,bake_tracks,wrist_from_native,f32_row
from build_equipment_hand_grips import RECIPE,posed_hand_mesh
from build_fitted_fpv_bank import fitted_grips
from build_modern_animation_bank import ALIASES,euler
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import CASES,compile_bank as rigid_bank,preview_meshes
from build_thumb_grip_preview import detail
from five_ds import parse_5ds
from hand_pose_ik import author_pose,pinned_skin,validate_basis
from menu_gui_audit import parse_4ds_nodes
from model_transform import matmul,rotation
from modern_thumb_pose import apply,turns

PROFILE=asset.ROOT/'experimental/RECONSTRUCTION_BACKLOG/modern-rigid-hand-grips.json'
BASE_PROFILE=RECIPE.parent/'modern-fitted-hand-grips.json'
SHORT={'FG42':'FG4','MG34':'MG3','ZK383':'ZK3'}


def stow_offset(profile,case):
    offset=asset.vector(profile['cases'][case].get('stow_offset',[0,0,0]))
    if any(abs(v)>.2 for v in offset):raise ValueError('Stow placement outside authoring domain')
    return list(offset)


def adjust(grips,thumb,side,adjustment):
    required={'contact_offset_delta','rotation_degrees'}
    if (side not in ('L','R') or not isinstance(adjustment,dict) or not required<=set(adjustment)
            or set(adjustment)-required-{'finger_curl_degrees','thumb','elbow_pole','stow_elbow_pole'}):
        raise ValueError('Unexpected hand adjustment')
    delta=asset.vector(adjustment['contact_offset_delta']);angles=asset.vector(adjustment['rotation_degrees'])
    if any(abs(v)>.1 for v in delta) or any(abs(v)>90 for v in angles):raise ValueError('Rigid hand adjustment outside domain')
    grips=deepcopy(grips);thumb=deepcopy(thumb)
    grips[side]['contact_offset']=[a+b for a,b in zip(grips[side]['contact_offset'],delta)]
    grips[side]['rest_to_equipment_rotation']=matmul(rotation(euler(list(angles))),grips[side]['rest_to_equipment_rotation'])
    validate_basis(grips[side]['rest_to_equipment_rotation'])
    if 'finger_curl_degrees' in adjustment:
        curls=asset.vector(adjustment['finger_curl_degrees'])
        if any(abs(v)>110 for v in curls):raise ValueError('Unreviewed rigid finger curl')
        grips[side]['finger_curl_degrees']=list(curls)
    if 'thumb' in adjustment:
        thumb[side]=deepcopy(adjustment['thumb']);turns(thumb)
    for key in ('elbow_pole','stow_elbow_pole'):
        if key not in adjustment:continue
        pole=asset.vector(adjustment[key])
        if any(abs(v)>1 for v in pole):raise ValueError('Elbow pole outside authoring domain')
        grips[side][key]=list(pole)
    return grips,thumb


def configuration(profile,base,spec,case):
    if (not isinstance(profile,dict) or set(profile)!={'schema_version','kind','provenance','runtime_status',
            'description','source_grip_profile_sha256','source_grip_digest_mode','base_grip_case','cases'}
            or type(profile['schema_version']) is not int or profile['schema_version']!=1 or profile['kind']!='modern_rigid_hand_profile'
            or profile['provenance']!='MODERNE' or profile['runtime_status']!='pending'
            or profile['source_grip_digest_mode']!='canonical_json'
            or profile['source_grip_profile_sha256']!=digest(json.dumps(base,sort_keys=True).encode())
            or profile['base_grip_case']!='F35' or not isinstance(profile['cases'],dict)
            or set(profile['cases'])!=set(CASES) or case not in CASES):
        raise ValueError('Unreviewed rigid hand authoring profile')
    grips,thumb=fitted_grips(base,spec,profile['base_grip_case']);row=profile['cases'][case]
    if (not isinstance(row,dict) or not {'model_sha256','translation','hands'}<=set(row)
            or set(row)-{'model_sha256','translation','hands','stow_offset'}
            or not isinstance(row['hands'],dict) or set(row['hands'])!={'L','R'}
            or not isinstance(row['model_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',row['model_sha256'])):
        raise ValueError('Incomplete rigid hand profile case')
    translation=asset.vector(row['translation'])
    stow_offset(profile,case)
    if any(abs(v)>.5 for v in translation):raise ValueError('Rigid hand placement outside authoring domain')
    for side,adjustment in row['hands'].items():
        grips,thumb=adjust(grips,thumb,side,adjustment)
    return grips,thumb,list(translation),row['model_sha256']


def placed_tracks(raw,translation,*,stow=(0,0,0),clip_name=None):
    translation=asset.vector(translation)
    if any(abs(v)>.5 for v in translation):raise ValueError('Rigid placement outside authoring domain')
    if not isinstance(stow,(list,tuple)):raise ValueError('Invalid stow vector')
    stow=asset.vector(list(stow))
    if any(abs(v)>.2 for v in stow) or (any(stow) and clip_name not in ALIASES):
        raise ValueError('Unreviewed stow offset or missing clip identity')
    parsed=parse_5ds(raw);tracks=[{'name':t['name'],'channels':deepcopy(t['channels'])} for t in parsed['tracks']]
    selected=[t for t in tracks if t['name']=='fpv_weapon']
    if len(selected)!=1 or 'position' not in selected[0]['channels']:raise ValueError('Missing rigid root placement track')
    channel=selected[0]['channels']['position']
    channel['values']=[f32_row([a+b+c*((1-frame/parsed['frame_end']) if clip_name=='Arm' else
                          (frame/parsed['frame_end'] if clip_name=='Disarm' else 0))
                          for a,b,c in zip(value,translation,stow)],3)
                       for frame,value in zip(channel['frames'],channel['values'])]
    return tracks


def elbow_hint(grip,clip_name,time,end):
    pole=grip['elbow_pole'][:]
    if 'stow_elbow_pole' in grip and clip_name in ('Arm','Disarm'):
        if type(end) is not int or end<=0 or type(time) not in (int,float) or not 0<=time<=end*40:
            raise ValueError('Unreviewed stow elbow sample')
        weight=min(1,2*(1-time/(end*40))) if clip_name=='Arm' else min(1,2*time/(end*40))
        pole=[a+weight*(b-a) for a,b in zip(pole,grip['stow_elbow_pole'])]
    return pole


def targets(rig,tracks,time,grips,*,clip_name=None):
    names,seeds=model_poses(rig)
    world,_=numeric_world(parse_4ds_nodes(rig)['nodes'],dict(zip(names,seeds)),
                          {t['name']:t['channels'] for t in tracks},time)
    root=world['fpv_weapon'];basis=[[root[i+4*j] for j in range(3)] for i in range(3)]
    end=max(max(c['frames']) for t in tracks for c in t['channels'].values())
    return {side:{'position':wrist_from_native(root,world['MOD_'+label+'_hand'],grips[side]),
        'rotation':matmul(basis,grips[side]['rest_to_equipment_rotation']),'pole':elbow_hint(grips[side],clip_name,time,end)}
        for side,label in (('L','left'),('R','right'))}


def compile_hand_bank(case,hand_raw,rig,source_clips,grips,thumb,translation,*,stow=(0,0,0)):
    source,skin=pinned_skin(hand_raw);names=[n['name'] for n in skin['nodes']]
    by_name={n['name']:n for n in skin['nodes']}
    bases={name:skin['rest_world'][by_name[name]['index']][0] for name in turns(thumb)}
    gear_names,_=model_poses(rig);allowed=HAND_NAMES|set(gear_names)
    if (case not in CASES or len(allowed)!=len(names)+len(gear_names) or set(source_clips)!=set(ALIASES)
            or set(names)!=HAND_NAMES):raise ValueError('Unexpected rigid hand bank targets')
    variant='H' if source==HAND_MODELS[0] else 'R';clips={};rows={}
    curls={s:{'finger_curl_degrees':g['finger_curl_degrees']} for s,g in grips.items()}
    for name,(_,raw) in source_clips.items():
        end=parse_5ds(raw)['frame_end'];gear=placed_tracks(raw,translation,stow=stow,clip_name=name);samples=[];worst=0
        if {t['name'] for t in gear}!=set(gear_names):raise ValueError('Incomplete rigid source tracks')
        for frame in range(end+1):
            poses,report=author_pose(hand_raw,targets(rig,gear,frame*40,grips,clip_name=name),curls,arm_rotation_policy='bend_plane')
            worst=max(worst,*(v['wrist_error'] for v in report['arms'].values()))
            samples.append(apply(poses,bases,thumb))
        encoded=motion._encode_transform_tracks(end,bake_tracks(samples,names,end)+gear,
            preserve_native_rotations=True,name_validator=lambda n:n in allowed)
        if len(encoded)-18>0xf000:raise ValueError('Rigid hand clip exceeds reviewed native body capacity')
        actual={t['name']:t['channels'] for t in parse_5ds(encoded)['tracks']}
        if any(actual[t['name']]!=t['channels'] for t in gear):raise ValueError('Rigid hand merge changed placed gear tracks')
        stem=f'PROTOTYPE_{SHORT[case]}P{variant}{ALIASES[name]}'
        if len(stem)>19:raise ValueError('Private rigid hand alias exceeds native limit')
        clips[name]=(stem,encoded);rows[name]={'stem':stem,'sha256':digest(encoded),'bytes':len(encoded),
            'source_clip_sha256':digest(raw),'frame_end':end,'authored_frames':len(samples),
            'unserialized_authoring_wrist_max_error':worst}
    return clips,{'hand_source':source,'hand_sha256':digest(hand_raw),'model_sha256':digest(rig),
        'grips':deepcopy(grips),'thumb':deepcopy(thumb),'translation':list(translation),'stow_offset':list(stow),'clips':rows,
        'rest_positions_scales_and_geometry_preserved':True,'finger_contact_qualified':False,
        'reload_hand_gestures_implemented':False,'engine_validated':False}


def previews(case,recipe,rig,source,hand_raw,clips,output):
    from fpv_perspective_preview import preview
    recipe=deepcopy(recipe);recipe['materials'].append({'name':'private_hand_preview','diffuse':[.68,.65,.60]})
    _,skin=pinned_skin(hand_raw);names,seeds=model_poses(hand_raw)
    for name,time in (('Idle1',0),('Aim',480),('Rel',1400),('Arm',0)):
        raw=clips[name][1];tracks={t['name']:t['channels'] for t in parse_5ds(raw)['tracks']}
        world,poses=numeric_world(skin['nodes'],dict(zip(names,seeds)),tracks,time)
        meshes=preview_meshes(rig,raw,time)+[posed_hand_mesh(hand_raw,poses,len(recipe['materials']))]
        label=Path(source).stem+'_'+name
        preview(recipe,meshes,output/(label+'_view.png'),case+' / '+name+' / PRIVATE DERIVED HANDS / INITIAL GRIP',horizontal_fov=65)
        centers={s:[(a+b)*.5 for a,b in zip(world[f'Bip01 {s} Hand'][12:15],world[f'Bip01 {s} Finger2'][12:15])] for s in ('L','R')}
        detail(recipe,meshes,centers,output/(label+'_detail.png'),case+' / '+name+' / INITIAL GRIP')


def build(case,hands,profile,output,with_previews=False):
    if output.exists():raise FileExistsError('Private hand bank exists; use a fresh name')
    base=json.loads(BASE_PROFILE.read_text(encoding='utf-8'));spec=json.loads(RECIPE.read_text(encoding='utf-8'))
    grips,thumb,translation,expected=configuration(profile,base,spec,case)
    recipe,rig,source_clips,source_report=rigid_bank(case)
    if digest(rig)!=expected:raise ValueError('Rigid model differs from hand profile')
    prepared=[]
    for source in HAND_MODELS:
        clips,row=compile_hand_bank(case,hands[source],rig,source_clips,grips,thumb,translation,stow=stow_offset(profile,case))
        prepared.append((source,clips,row))
    output.mkdir(parents=True,exist_ok=False)
    (output/f'PROTOTYPE_{SHORT[case]}_HandFPV.4ds.disabled').write_bytes(rig)
    for source,clips,row in prepared:
        for stem,raw in clips.values():(output/(stem+'.5ds.disabled')).write_bytes(raw)
        if with_previews:previews(case,recipe,rig,source,hands[source],clips,output)
    report={'schema_version':1,'case':case,'provenance':PROVENANCE,'runtime_status':'pending','private_only':True,
        'profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),'source_rigid_bank':source_report,
        'variants':{source:row for source,clips,row in prepared},'modern_equipment_model_unchanged':True,
        'root_translation_is_clip_only':True,'other_equipment_channels_preserved':True,
        'stow_offset':stow_offset(profile,case),'stow_curve_is_modern_authoring':any(stow_offset(profile,case)),
        'commercial_geometry_exported':False,'original_animation_keys_read':False,
        'initial_grips_seeded_from_modern_F35':True,'source_geometry_modified':False,
        'native_loader_executed':False,'surface_contact_qualified':False,'reload_hand_gestures_implemented':False,
        'post_blend_constraint_hook_implemented':False,'camera_calibrated':False,
        'events_or_gameplay_implemented':False,'game_started':False,'game_modified':False,'engine_validated':False,
        'files':{p.name:digest(p.read_bytes()) for p in sorted(output.iterdir())}}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--game',type=Path,required=True);parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--profile',type=Path,default=PROFILE);parser.add_argument('--output-name',required=True)
    parser.add_argument('--previews',action='store_true');args=parser.parse_args(argv)
    try:
        output=asset.output_directory(asset.ROOT,args.output_name)
        profile=json.loads(args.profile.read_text(encoding='utf-8'));hands,_=read_hands(args.game,archives_only=args.archives_only)
        report=build(args.case,hands,profile,output,args.previews)
        print(json.dumps({'case':args.case,'output':str(output),'files':len(report['files'])+1,
            'max_clip_bytes':max(c['bytes'] for v in report['variants'].values() for c in v['clips'].values()),
            'surface_contact_qualified':False,'engine_validated':False}));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Private rigid hand bank refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
