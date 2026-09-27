#!/usr/bin/env python3
"""Private fitted-grip clips; existing corrected banks remain byte-unchanged.

Modern fitting parameters are reproduced and checked before use. Original hand
rest sources stay pinned; only derived transform clips and private previews
are emitted, disabled. No client binding or runtime constraint hook is added.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path

import build_modern_asset as asset
import modern_animation as motion
from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS, HAND_PINS, read_hands
from build_equipment_fpv_animation import numeric_world
from build_equipment_fpv_view_bank import targets_at, view_grips, preview_bank, preview_meshes
from build_equipment_hand_animation import HAND_NAMES, PROVENANCE, bake_tracks
from build_equipment_hand_grips import RECIPE, posed_hand_mesh
from build_modern_animation_bank import ALIASES
from build_modern_equipment_assembly import ROOT, inputs
from build_modern_equipment_hose import digest
from build_thumb_grip_preview import detail
from equipment_hand_contact import measure_pose
from fit_modern_grip_candidates import PARAMETERS, recipe
from five_ds import parse_5ds
from fpv_transition_contact_audit import load_bank
from hand_pose_ik import author_pose, pinned_skin
from modern_thumb_pose import apply, turns


def profile_report(profile, spec):
    """Portable modern parameters only, without exported commercial poses."""
    if (not isinstance(profile,dict) or set(profile)!={'schema_version','kind','provenance','runtime_status',
            'description','source_hand_sha256','source_recipe_sha256','source_recipe_digest_mode','cases'}
            or profile['schema_version']!=1 or profile['kind']!='modern_grip_profile'
            or profile['provenance']!='MODERNE' or profile['runtime_status']!='pending'
            or profile['source_hand_sha256']!=HAND_PINS[HAND_MODELS[0]][2]
            or profile['source_recipe_digest_mode']!='canonical_json'
            or profile['source_recipe_sha256']!=digest(json.dumps(spec,sort_keys=True).encode())
            or set(profile['cases'])!={'F35','F2'}):
        raise ValueError('Unreviewed portable modern grip profile')
    result={'schema_version':1,'provenance':'MODERNE','runtime_status':'pending',
            'source_hand_sha256':profile['source_hand_sha256'],
            'source_recipe_sha256':digest(RECIPE.read_bytes()),'cases':{}}
    for case,hands in profile['cases'].items():
        if set(hands)!={'L','R'}:raise ValueError('Incomplete portable hand profile')
        base=view_grips(spec,case);result['cases'][case]={}
        for side,row in hands.items():
            if set(row)!={'parameters'} or set(row['parameters'])!=set(PARAMETERS):
                raise ValueError('Unexpected fields in portable hand profile')
            chosen,thumb=recipe(base,case,side,[row['parameters'][key] for key in PARAMETERS])
            result['cases'][case][side]={'parameters':deepcopy(row['parameters']),
                'grip':chosen[side],'thumb':thumb[side],'auto_promoted':False,'contact_qualified':False}
    return result


def fitted_grips(report, spec, case):
    if report.get('kind')=='modern_grip_profile':report=profile_report(report,spec)
    if (report.get('schema_version') != 1 or report.get('provenance') != 'MODERNE'
            or report.get('runtime_status') != 'pending' or set(report.get('cases',{})) != {'F35','F2'}
            or report.get('source_hand_sha256') != HAND_PINS[HAND_MODELS[0]][2]
            or report.get('source_recipe_sha256') != digest(RECIPE.read_bytes())):
        raise ValueError('Unreviewed or changed modern fitting report')
    base = view_grips(spec,case)
    result = deepcopy(base)
    thumb = {'provenance':'MODERNE','runtime_status':'pending'}
    if set(report['cases'][case]) != {'L','R'}:
        raise ValueError('Both fitted hands are required')
    for side in ('L','R'):
        row=report['cases'][case][side]
        if (set(row.get('parameters',{})) != set(PARAMETERS) or row.get('auto_promoted') is not False
                or row.get('contact_qualified') is not False):
            raise ValueError('Unexpected fitted parameter set or promotion claim')
        chosen,thumb_spec=recipe(base,case,side,[row['parameters'][name] for name in PARAMETERS])
        if chosen[side] != row['grip'] or thumb_spec[side] != row['thumb']:
            raise ValueError('Fitted recipe differs from its reproducible parameters')
        result[side],thumb[side]=chosen[side],thumb_spec[side]
    return result,thumb


def compile_bank(case, hand_raw, rig, source_clips, grips, thumb):
    source,skin=pinned_skin(hand_raw)
    names=[n['name'] for n in skin['nodes']]
    by_name={n['name']:n for n in skin['nodes']}
    bases={name:skin['rest_world'][by_name[name]['index']][0] for name in turns(thumb)}
    gear_names,_=model_poses(rig)
    allowed=HAND_NAMES | set(gear_names)
    if len(allowed) != len(names)+len(gear_names) or set(source_clips)!=set(ALIASES):
        raise ValueError('Unexpected fitted bank targets or clips')
    variant='H' if source==HAND_MODELS[0] else 'R'
    clips,rows={},{}
    for name,description in source_clips.items():
        raw=description['data'];parsed=parse_5ds(raw);end=parsed['frame_end']
        gear=[{'name':t['name'],'channels':deepcopy(t['channels'])} for t in parsed['tracks'] if t['name'] in gear_names]
        if len(gear)!=len(gear_names) or {t['name'] for t in parsed['tracks']}!=allowed:
            raise ValueError('Missing fitted-bank source channels')
        curls={s:{'finger_curl_degrees':g['finger_curl_degrees']} for s,g in grips.items()}
        samples=[]
        for frame in range(end+1):
            poses,_=author_pose(hand_raw,targets_at(rig,gear,frame*40,grips),curls,arm_rotation_policy='bend_plane')
            samples.append(apply(poses,bases,thumb))
        hands=bake_tracks(samples,names,end)
        encoded=motion._encode_transform_tracks(end,hands+gear,preserve_native_rotations=True,
                                                name_validator=lambda n:n in allowed)
        if len(encoded)-18>0xf000:raise ValueError('Fitted clip exceeds native reviewed body size')
        actual={t['name']:t['channels'] for t in parse_5ds(encoded)['tracks']}
        if any(actual[t['name']] != t['channels'] for t in gear):
            raise ValueError('Fitted hands changed serialized equipment channels')
        stem=f'PROTOTYPE_{case}G{variant}{ALIASES[name]}'
        if len(stem)>19:raise ValueError('Fitted alias exceeds native limit')
        clips[name]=(stem,encoded)
        rows[name]={'stem':stem,'frame_end':end,'sha256':digest(encoded),'bytes':len(encoded),
                    'source_clip_sha256':digest(raw),'authored_frames':len(samples)}
    return clips,{'hand_source':source,'hand_sha256':digest(hand_raw),'model_sha256':digest(rig),
                  'grips':deepcopy(grips),'thumb':deepcopy(thumb),'clips':rows,
                  'equipment_channels_preserved':True,'rest_transforms_preserved':True,
                  'finger_contact_qualified':False,'engine_validated':False}


def build(case,hands,bank,fitting,output,previews=False):
    spec=json.loads(RECIPE.read_text(encoding='utf-8'))
    grips,thumb=fitted_grips(fitting,spec,case)
    prepared=[]
    for source in HAND_MODELS:
        rig,source_clips=load_bank(bank,case,source,hands[source])
        clips,row=compile_bank(case,hands[source],rig,source_clips,grips,thumb)
        prepared.append((source,rig,clips,row))
    if prepared[0][1]!=prepared[1][1]:raise ValueError('Hand variant changed modern model')
    output.mkdir(parents=True,exist_ok=False)
    (output/f'PROTOTYPE_{case}_FPVView.4ds.disabled').write_bytes(prepared[0][1])
    recipes=deepcopy(inputs(case)[0])
    recipes['materials'].append({'name':'private_hand_preview','diffuse':[.68,.65,.60]})
    measures=[]
    for source,rig,clips,row in prepared:
        for stem,raw in clips.values():(output/(stem+'.5ds.disabled')).write_bytes(raw)
        _,skin=pinned_skin(hands[source]);hn,hi=model_poses(hands[source])
        if previews:preview_bank(case,hands[source],rig,clips,output)
        for name,time in (('Idle1',0),('Aim',480)):
            raw=clips[name][1]
            tracks={t['name']:t['channels'] for t in parse_5ds(raw)['tracks']}
            hw,poses=numeric_world(skin['nodes'],dict(zip(hn,hi)),tracks,time)
            gear=preview_meshes(rig,raw,time)
            measures.append({'source':source,'clip':name,'time':time,
                             'contact':measure_pose(hands[source],poses,gear,case)})
            if previews:
                centers={s:[(a+b)*.5 for a,b in zip(hw[f'Bip01 {s} Hand'][12:15],
                         hw[f'Bip01 {s} Finger2'][12:15])] for s in ('L','R')}
                detail(recipes,gear+[posed_hand_mesh(hands[source],poses,len(recipes['materials']))],centers,
                       output/f'{Path(source).stem}_{name}_fitted_detail.png',case+' / '+name+' / FIT CANDIDATE')
    report={'schema_version':1,'provenance':PROVENANCE,'runtime_status':'pending','private_only':True,
        'fitting_report_sha256':digest(json.dumps(fitting,sort_keys=True).encode()),
        'variants':{source:row for source,_,_,row in prepared},'contact_samples':measures,
        'original_banks_changed':False,'commercial_geometry_exported':False,
        'equipment_geometry_or_clips_changed':False,'thumb_pose_authored':True,
        'all_authored_keys_reachable':True,'native_loader_executed':False,
        'surface_crossings_checked':False,'finger_contact_qualified':False,
        'post_blend_constraint_hook_implemented':False,'camera_calibrated':False,
        'engine_validated':False,'game_started':False,'game_modified':False,
        'files':{p.name:digest(p.read_bytes()) for p in sorted(output.iterdir())}}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--case',choices=('F35','F2'),required=True)
    parser.add_argument('--bank',required=True,type=Path)
    parser.add_argument('--fitting',required=True,type=Path,help='Private fitting report or portable modern grip profile')
    parser.add_argument('--output-name',required=True)
    parser.add_argument('--previews',action='store_true')
    args=parser.parse_args(argv)
    try:
        output=asset.output_directory(ROOT,args.output_name)
        hands,_=read_hands(args.game,archives_only=args.archives_only)
        fitting=json.loads(args.fitting.read_text(encoding='utf-8'))
        report=build(args.case,hands,args.bank,fitting,output,args.previews)
        print(json.dumps({'output':str(output),'files':len(report['files'])+1,
                          'all_authored_keys_reachable':True,'engine_validated':False}))
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Private fitted FPV bank refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
