#!/usr/bin/env python3
"""Private surface crossings against every convex serialized equipment piece.

Nonconvex/open pieces are explicitly reported as unchecked, never silently
accepted. A surface measurement does not establish natural hand contact or
hand self-intersection, and no renderer or game is run.
"""
import argparse
import json
from pathlib import Path
import re
import sys

from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS, read_hands
from build_equipment_fpv_animation import numeric_world
from build_equipment_fpv_view_bank import preview_meshes
from build_equipment_hand_grips import posed_hand_mesh
from build_modern_animation_bank import ALIASES
from build_modern_equipment_hose import digest
from convex_contact import planes, surface_measure
from five_ds import parse_5ds
from fpv_transition_contact_audit import load_bank
from hand_pose_ik import pinned_skin
from modern_fpv_axes import compile_view_rig


def fitted(directory,case,source,hand_raw):
    manifest=json.loads((directory/'MANIFEST.json').read_text(encoding='utf-8'))
    if (manifest.get('private_only') is not True or manifest.get('runtime_status')!='pending'
            or manifest.get('provenance')!='DERIVE_MODERNE_SUR_SQUELETTE_COMMERCIAL'):
        raise ValueError('Not a private fitted bank')
    row=manifest['variants'][source]
    rig=(directory/f'PROTOTYPE_{case}_FPVView.4ds.disabled').read_bytes()
    if (rig!=compile_view_rig(case)[0] or digest(rig)!=row['model_sha256']
            or digest(hand_raw)!=row['hand_sha256'] or set(row['clips'])!=set(ALIASES)):
        raise ValueError('Changed fitted source/model/clip set')
    variant='H' if source==HAND_MODELS[0] else 'R';clips={}
    for name,description in row['clips'].items():
        stem=f'PROTOTYPE_{case}G{variant}{ALIASES[name]}'
        if description['stem']!=stem:raise ValueError('Unexpected fitted clip path')
        raw=(directory/(stem+'.5ds.disabled')).read_bytes()
        if digest(raw)!=description['sha256']:raise ValueError('Changed fitted clip')
        clips[name]=raw
    return rig,clips


def measure(raw,rig,clip,time):
    _,skin=pinned_skin(raw);names,seeds=model_poses(raw)
    tracks={t['name']:t['channels'] for t in parse_5ds(clip)['tracks']}
    _,poses=numeric_world(skin['nodes'],dict(zip(names,seeds)),tracks,time)
    hand=posed_hand_mesh(raw,poses,1)
    results,unchecked={},{}
    for mesh in preview_meshes(rig,clip,time):
        try:support=planes(mesh.points,mesh.triangles)
        except ValueError as error:
            unchecked[mesh.name]=str(error);continue
        if mesh.name in results:raise ValueError('Ambiguous split equipment piece')
        bounds=[tuple(fn(p[i] for p in mesh.points) for i in range(3)) for fn in (min,max)]
        results[mesh.name]=surface_measure(hand.points,hand.triangles,support,volume_bounds=bounds)
    return {'pieces':results,'unchecked_pieces':unchecked,'all_equipment_pieces_checked':not unchecked,
            'penetrating_triangles_sum_over_pieces':sum(r['penetrating_triangles'] for r in results.values()),
            'max_depth_lower_bound':max((r['max_depth_lower_bound'] for r in results.values()),default=0)}


def audit(game,bank_root,archives_only=False,bank_suffix='FittedGrips_v1',dense=False):
    if not re.fullmatch(r'FittedGrips_v[1-9][0-9]*',bank_suffix):raise ValueError('Invalid fitted bank suffix')
    hands,excluded=read_hands(game,archives_only=archives_only);samples=[]
    for case in ('F35','F2'):
        for source in HAND_MODELS:
            raw=hands[source]
            rig,clips=fitted(bank_root/(case+'_'+bank_suffix),case,source,raw)
            old_rig,old=load_bank(bank_root/(case+'_CorrectedFPV_v1'),case,source,raw)
            if old_rig!=rig:raise ValueError('Comparison changes equipment geometry')
            scenarios=[('old','Idle1',0,old['Idle1']['data'])]
            scenarios += ([( 'fitted',name,time,raw_clip) for name,raw_clip in clips.items()
                           for time in range(0,parse_5ds(raw_clip)['frame_end']*40+1,20)] if dense else
                          [('fitted',name,time,clips[name]) for name,time in
                           (('Idle1',0),('Aim',480),('Arm',540),('Rel',1300))])
            for label,name,time,clip in scenarios:
                result=measure(raw,rig,clip,time)
                samples.append({'case':case,'source':source,'bank':label,'clip':name,'time':time,
                    'hand_sha256':digest(raw),'model_sha256':digest(rig),'clip_sha256':digest(clip),**result})
                if not dense or time==0:
                    print(case,source,label,name,time,result['penetrating_triangles_sum_over_pieces'],
                          result['max_depth_lower_bound'],file=sys.stderr,flush=True)
    return {'schema_version':1,'scope':'private_equipment_convex_surface_crossings','runtime_status':'pending',
        'bank_suffix':bank_suffix,'dense_keys_and_half_keys':dense,'samples':samples,
        'excluded_loose_overrides':excluded,'commercial_geometry_exported':False,
        'source_geometry_modified':False,'surface_crossings_checked_for_reported_convex_pieces':True,
        'skin_numeric_reference_used':True,'native_skin_executed':False,
        'hand_self_intersection_checked':False,'finger_contact_qualified':False,
        'game_started':False,'game_modified':False,'engine_validated':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--bank-root',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',required=True,type=Path)
    parser.add_argument('--bank-suffix',default='FittedGrips_v1')
    parser.add_argument('--dense',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.game,args.bank_root,args.archives_only,args.bank_suffix,args.dense)
        with args.json_output.open('x',encoding='utf-8') as output:
            json.dump(report,output,indent=2);output.write('\n')
        print(json.dumps({'samples':len(report['samples']),'output':str(args.json_output)}))
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Private fitted surface audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
