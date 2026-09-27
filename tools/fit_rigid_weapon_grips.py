#!/usr/bin/env python3
"""Offline modern grip candidates; private geometry stays in memory only.

Deterministic bounded fitting on Idle1, never auto-promoted and not a contact
qualification. A separate serialized-bank surface/native audit is mandatory.
"""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import sys

from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS,read_hands
from build_equipment_hand_grips import RECIPE,posed_hand_mesh
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import CASES,compile_bank,preview_meshes
from build_rigid_weapon_hand_bank import BASE_PROFILE,PROFILE,configuration,placed_tracks,adjust,targets
from fit_modern_grip_candidates import digit_indices,probe_penalty,surface_witnesses
from hand_pose_ik import author_pose,pinned_skin
from modern_contact_cells import cells
from modern_thumb_pose import apply,turns
import modern_animation as motion

GRIPS={'FG42':{'L':'MOD_fore_end','R':'MOD_pistol_grip'},
       'MG34':{'L':'MOD_barrel_jacket','R':'MOD_pistol_grip'},
       'ZK383':{'L':'MOD_wood_fore_end','R':'MOD_stock'}}
BOUNDS=((-0.06,.06),)*3+((-90,90),)*3+((0,110),)*3+((-65,65),)*3


def point_triangle_distance_squared(p,a,b,c):
    # Closest point by Voronoi regions, including finite edges and vertices.
    sub=lambda u,v:[x-y for x,y in zip(u,v)]
    dot=lambda u,v:sum(x*y for x,y in zip(u,v))
    ab,ac,ap=sub(b,a),sub(c,a),sub(p,a);d1,d2=dot(ab,ap),dot(ac,ap)
    if d1<=0 and d2<=0:return dot(ap,ap)
    bp=sub(p,b);d3,d4=dot(ab,bp),dot(ac,bp)
    if d3>=0 and d4<=d3:return dot(bp,bp)
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0:
        v=d1/(d1-d3);delta=sub(p,[a[i]+v*ab[i] for i in range(3)]);return dot(delta,delta)
    cp=sub(p,c);d5,d6=dot(ab,cp),dot(ac,cp)
    if d6>=0 and d5<=d6:return dot(cp,cp)
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0:
        w=d2/(d2-d6);delta=sub(p,[a[i]+w*ac[i] for i in range(3)]);return dot(delta,delta)
    va=d3*d6-d5*d4
    if va<=0 and d4-d3>=0 and d5-d6>=0:
        w=(d4-d3)/((d4-d3)+(d5-d6));delta=sub(p,[b[i]+w*(c[i]-b[i]) for i in range(3)]);return dot(delta,delta)
    denominator=va+vb+vc
    if denominator<=1e-24:raise ValueError('Degenerate proximity triangle')
    v,w=vb/denominator,vc/denominator
    delta=sub(p,[a[i]+ab[i]*v+ac[i]*w for i in range(3)]);return dot(delta,delta)


def finite_digit_gaps(points,digits,triangles):
    rows=[(t,[min(v[i] for v in t) for i in range(3)],[max(v[i] for v in t) for i in range(3)]) for t in triangles]
    result=[]
    for indices in digits.values():
        best=math.inf
        for i in indices:
            p=points[i]
            for triangle,lower,upper in rows:
                bound=sum(max(lower[j]-p[j],0,p[j]-upper[j])**2 for j in range(3))
                if bound>=best:continue
                best=min(best,point_triangle_distance_squared(p,*triangle))
        if not math.isfinite(best):raise ValueError('Missing finite contact sample')
        result.append(math.sqrt(best))
    return result


def adjustment(values,side):
    if (side not in ('L','R') or len(values)!=len(BOUNDS)
            or any(type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi
                   for v,(lo,hi) in zip(values,BOUNDS))):raise ValueError('Unreviewed rigid fit candidate')
    return {'contact_offset_delta':list(values[:3]),'rotation_degrees':list(values[3:6]),
            'finger_curl_degrees':[v*(1 if side=='L' else -1) for v in values[6:9]],
            'thumb':{'opposition_degrees':values[9],'curl_degrees':list(values[10:12])}}


def fit(hand_raw,case,side,compiled,profile,*,seed_current_profile=False,index_to_trigger=False):
    if any('finger_curl_overrides' in h for h in profile['cases'][case]['hands'].values()):
        raise ValueError('Global grip fitter does not support independent finger choices')
    if type(index_to_trigger) is not bool or (index_to_trigger and (case,side)!=('ZK383','R')):
        raise ValueError('Unreviewed independent index contact case')
    recipe,rig,clips,_=compiled
    base=json.loads(BASE_PROFILE.read_text(encoding='utf-8'));spec=json.loads(RECIPE.read_text(encoding='utf-8'))
    # Fit absolute adjustments relative to the pinned modern F35 seed.
    neutral=deepcopy(profile)
    neutral['cases'][case]['hands']={s:{'contact_offset_delta':[0,0,0],'rotation_degrees':[0,0,0]} for s in ('L','R')}
    grips,thumb,translation,_=configuration(neutral,base,spec,case)
    gear=placed_tracks(clips['Idle1'][1],translation)
    raw=motion._encode_transform_tracks(60,gear,preserve_native_rotations=True,name_validator=lambda n:True)
    meshes=preview_meshes(rig,raw,0);contact=next(m for m in meshes if m.name==GRIPS[case][side])
    contact_triangles=[[contact.points[i] for i in f] for f in contact.triangles]
    digit_contacts={i:contact_triangles for i in range(5)}
    if index_to_trigger:
        trigger=next(m for m in meshes if m.name=='MOD_trigger')
        digit_contacts[1]=[[trigger.points[i] for i in face] for face in trigger.triangles]
    volumes=[];unchecked=[]
    for mesh in meshes:
        try:parts=cells(mesh,recipe['parts'])
        except ValueError as error:
            unchecked.append({'piece':mesh.name,'reason':str(error)});continue
        volumes.extend((v['bounds'][0],v['bounds'][1],v['support']) for v in parts)
    _,skin=pinned_skin(hand_raw);indices,digits=digit_indices(skin,side);membership=set(indices)
    hn,hi=model_poses(hand_raw);rest_mesh=posed_hand_mesh(hand_raw,dict(zip(hn,hi)),1)
    faces=[face for face in rest_mesh.triangles if all(i in membership for i in face)]
    nodes={n['name']:n for n in skin['nodes']};bases={n:skin['rest_world'][nodes[n]['index']][0] for n in turns(thumb)}
    witnesses=[];cache={};evaluations=0

    def points_for(values):
        chosen,turned=adjust(grips,thumb,side,adjustment(values,side))
        poses,_=author_pose(hand_raw,targets(rig,gear,0,chosen),
            {s:{'finger_curl_degrees':g['finger_curl_degrees']} for s,g in chosen.items()},arm_rotation_policy='bend_plane')
        return posed_hand_mesh(hand_raw,apply(poses,bases,turned),1).points

    def evaluate(values):
        nonlocal evaluations
        key=tuple(values)
        if key not in cache:
            evaluations+=1
            try:points=points_for(values)
            except ValueError as error:
                if 'Unreachable or singular' not in str(error):raise
                cache[key]=(math.inf,{'unreachable':True});return cache[key]
            penalty,metrics=probe_penalty(points,indices,faces,volumes,witnesses)
            gaps=[finite_digit_gaps(points,{digit:indices},digit_contacts[digit])[0] for digit,indices in digits.items()]
            score=penalty+sum(g*g for g in gaps)
            cache[key]=(score,{**metrics,'finite_digit_surface_gaps':gaps,'objective':score})
        return cache[key]

    initial=[0,0,0,0,0,0,*[abs(v) for v in grips[side]['finger_curl_degrees']],thumb[side]['opposition_degrees'],*thumb[side]['curl_degrees']]
    seed=initial[:]
    if side=='L':seed[1]=.025
    if case=='ZK383' and side=='R':seed[1]=-.025;seed[3]=-45
    if seed_current_profile:
        current=profile['cases'][case]['hands'][side]
        curls=current.get('finger_curl_degrees',grips[side]['finger_curl_degrees'])
        thumb_choice=current.get('thumb',thumb[side])
        seed=[*current['contact_offset_delta'],*current['rotation_degrees'],*[abs(v) for v in curls],
              thumb_choice['opposition_degrees'],*thumb_choice['curl_degrees']]
        adjustment(seed,side)
    best=seed;score=evaluate(best)[0]
    if not math.isfinite(score):best=initial[:];score=evaluate(best)[0]
    before=evaluate(initial)[1];feedback=[]
    for iteration,(linear,angular) in enumerate(((.01,15),(.005,7.5),(.0025,3.75),(.00125,1.875),(.000625,.9375))):
        if iteration>=2:
            found=surface_witnesses(points_for(best),faces,volumes);feedback.append(len(found));witnesses.extend(found)
            cache.clear();score=evaluate(best)[0]
        for sweep in range(3):
            changed=False
            for axis,(lo,hi) in enumerate(BOUNDS):
                step=linear if axis<3 else angular
                for value in (max(lo,best[axis]-step),min(hi,best[axis]+step)):
                    trial=best[:];trial[axis]=value;candidate=evaluate(trial)[0]
                    if candidate<score-1e-15:best,score,changed=trial,candidate,True
            if not changed:break
        print(case,side,'fit level',iteration,'objective',score,'evaluations',evaluations,file=sys.stderr,flush=True)
    return {'adjustment':adjustment(best,side),'before':before,'after':evaluate(best)[1],
        'digit_contact_pieces':{str(i):'MOD_trigger' if i==1 and index_to_trigger else GRIPS[case][side] for i in range(5)},
        'evaluations':evaluations,'private_surface_feedback_counts':feedback,'unchecked_pieces':unchecked,
        'only_primary_hand_variant_idle_pose_checked':True,'auto_promoted':False,'contact_qualified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--profile',type=Path,default=PROFILE)
    parser.add_argument('--case',choices=CASES);parser.add_argument('--side',choices=('L','R'))
    parser.add_argument('--seed-current-profile',action='store_true')
    parser.add_argument('--index-to-trigger',action='store_true')
    parser.add_argument('--json-output',type=Path,required=True);args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        profile=json.loads(args.profile.read_text(encoding='utf-8'));hands,excluded=read_hands(args.game,archives_only=args.archives_only)
        rows={}
        for case in ([args.case] if args.case else CASES):
            compiled=compile_bank(case)
            rows[case]={s:fit(hands[HAND_MODELS[0]],case,s,compiled,profile,
                            seed_current_profile=args.seed_current_profile,index_to_trigger=args.index_to_trigger)
                        for s in ([args.side] if args.side else ('L','R'))}
        report={'schema_version':1,'provenance':'MODERNE','runtime_status':'pending','cases':rows,
            'source_profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),
            'source_hand_sha256':digest(hands[HAND_MODELS[0]]),'excluded_loose_overrides':excluded,
            'seed_current_profile':args.seed_current_profile,
            'commercial_geometry_exported':False,'derived_poses_exported':False,
            'full_surface_or_animation_contact_qualified':False,'game_started':False,'game_modified':False}
        with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Rigid grip fitting refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
