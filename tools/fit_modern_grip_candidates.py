#!/usr/bin/env python3
"""Deterministic offline fitting of modern grip choices, never auto-promoted.

The objective uses private skin vertices and convex grip planes, not a full
collision solver. Only modern input parameters and scalar metrics are saved;
commercial geometry and derived skeleton poses are never exported.
"""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import sys

from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS, read_hands
from build_equipment_fpv_animation import numeric_world
from build_equipment_fpv_view_bank import preview_meshes, view_grips
from build_equipment_hand_grips import RECIPE, posed_hand_mesh
from build_modern_equipment_hose import digest
from convex_contact import planes, clip_polygon, polygon_area
from equipment_hand_contact import GRIPS
from five_ds import parse_5ds
from fpv_contact_constraints import targets
from fpv_transition_contact_audit import load_bank
from hand_pose_ik import author_pose, pinned_skin
from menu_gui_audit import parse_4ds_nodes
from model_transform import matmul, rotation
from modern_thumb_pose import apply, turns

BOUNDS = ((0,.04),(-.02,.055),(-30,30),(35,110),(0,110),(0,90),(-65,65),(-65,65),(-65,65))
PARAMETERS = ('normal_shift','forward_shift','tilt_degrees','finger_base','finger_middle',
              'finger_tip','thumb_opposition','thumb_base','thumb_tip')


def recipe(base, case, side, values):
    if (case not in GRIPS or side not in ('L','R') or not isinstance(values,(list,tuple))
            or len(values)!=len(BOUNDS) or any(type(v) not in (int,float) or not math.isfinite(v)
            or not lo<=v<=hi for v,(lo,hi) in zip(values,BOUNDS))):
        raise ValueError('Unreviewed grip fitting parameters')
    chosen=deepcopy(base);grip=chosen[side]
    support_hand = case=='F35' and side=='L'
    normal_axis,forward_axis=(1,0) if support_hand else (0,2)
    grip['contact_offset'][normal_axis]+=values[0]*(-1 if side=='L' else 1)
    grip['contact_offset'][forward_axis]+=values[1]
    angle=math.radians(values[2])/2
    q=[0,0,0,math.cos(angle)];q[2 if support_hand else 0]=math.sin(angle)
    grip['rest_to_equipment_rotation']=matmul(rotation(q),grip['rest_to_equipment_rotation'])
    grip['finger_curl_degrees']=[v*(1 if side=='L' else -1) for v in values[3:6]]
    thumb={'provenance':'MODERNE','runtime_status':'pending',
           'L':{'opposition_degrees':0,'curl_degrees':[0,0]},
           'R':{'opposition_degrees':0,'curl_degrees':[0,0]}}
    thumb[side]={'opposition_degrees':values[6],'curl_degrees':list(values[7:9])}
    return chosen,thumb


def digit_indices(skin,side):
    by_index={n['index']:n for n in skin['nodes']}
    names=[by_index[i]['name'] for i in skin['joint_node_indices']]
    digits={i:[] for i in range(5)};all_indices=[]
    for i,(bone,weight) in enumerate(skin['pairs']):
        index=skin['parents'][bone-1] if weight>128 else bone
        name=names[index-1] if index else ''
        if not name.startswith(f'Bip01 {side} '):continue
        all_indices.append(i)
        for finger in digits:
            if name.startswith(f'Bip01 {side} Finger{finger}'):digits[finger].append(i)
    if any(not v for v in digits.values()):raise ValueError('Missing private digit sample group')
    return all_indices,digits


def objective(points,support,indices,digits):
    signed={i:max(sum(n[j]*points[i][j] for j in range(3))-offset for n,offset in support)
            for i in indices}
    depths=[max(0,-v) for v in signed.values()]
    # Near-plane samples are not themselves proof of a natural/complete grasp.
    gaps=[min(abs(signed[i]) for i in group) for group in digits.values()]
    score=100*sum(d*d for d in depths)+20*max(depths,default=0)**2+sum(g*g for g in gaps)
    return score,{'inside':sum(d>1e-5 for d in depths),'max_depth':max(depths,default=0),
                  'nearest_digit_plane_gaps':gaps,'objective':score}


def probe_penalty(points,indices,triangles,volumes,witnesses=()):
    """Bounded surface probes for optimization, NOT exhaustive face collision."""
    samples=[points[i] for i in indices]
    for a,b,c in triangles:
        vertices=[points[i] for i in (a,b,c)]
        samples.append(tuple(sum(p[j] for p in vertices)/3 for j in range(3)))
        for u,v in ((0,1),(1,2),(2,0)):
            samples.append(tuple((vertices[u][j]+vertices[v][j])*.5 for j in range(3)))
    for face,weights in witnesses:
        samples.append(tuple(sum(points[index][j]*weight for index,weight in zip(face,weights)) for j in range(3)))
    total=0;maximum=0;inside=0
    for lower,upper,support in volumes:
        for p in samples:
            if any(p[i]<lower[i] or p[i]>upper[i] for i in range(3)):continue
            depth=min(offset-(n[0]*p[0]+n[1]*p[1]+n[2]*p[2]) for n,offset in support)
            if depth>0:
                total+=depth*depth;maximum=max(maximum,depth);inside+=int(depth>1e-5)
    return 100*total+20*maximum*maximum,{'probe_inside':inside,'probe_max_depth':maximum,
                                       'probe_count':len(samples),'convex_volumes':len(volumes)}


def surface_witnesses(points,triangles,volumes):
    """Private barycentric witnesses from exact convex clipping of triangles."""
    witnesses=[]
    for lower,upper,support in volumes:
        for face in triangles:
            vertices=[points[i] for i in face]
            if any(max(p[j] for p in vertices)<lower[j] or min(p[j] for p in vertices)>upper[j] for j in range(3)):
                continue
            polygon=clip_polygon(vertices,support,1e-5)
            if polygon_area(polygon)<=1e-14:continue
            point=[sum(p[j] for p in polygon)/len(polygon) for j in range(3)]
            a,b,c=vertices
            u=[x-y for x,y in zip(b,a)];v=[x-y for x,y in zip(c,a)];w=[x-y for x,y in zip(point,a)]
            dot=lambda x,y:sum(p*q for p,q in zip(x,y))
            uu,uv,vv,wu,wv=dot(u,u),dot(u,v),dot(v,v),dot(w,u),dot(w,v)
            denominator=uu*vv-uv*uv
            if denominator<=1e-24:raise ValueError('Degenerate private collision witness')
            beta=(vv*wu-uv*wv)/denominator;gamma=(uu*wv-uv*wu)/denominator
            weights=[1-beta-gamma,beta,gamma]
            if min(weights)<-1e-6 or max(weights)>1+1e-6:raise ValueError('Witness left its source triangle')
            weights=[max(0,min(1,x)) for x in weights];total=sum(weights)
            witnesses.append((tuple(face),tuple(x/total for x in weights)))
    return witnesses


def fit(raw,case,side,rig,clip,spec,*,surface_aware=False,extra_seed=None,refine_only=False):
    _,skin=pinned_skin(raw)
    base=view_grips(spec,case);gear=preview_meshes(rig,clip,0)
    mesh=next(m for m in gear if m.name==GRIPS[case][side]);support=planes(mesh.points,mesh.triangles)
    indices,digits=digit_indices(skin,side)
    volumes=[];probe_faces=[];unchecked=[]
    if surface_aware:
        # Only authored held pieces can touch these local grips. The backpack
        # and hose remain explicitly outside this fitting objective.
        from build_modern_equipment_assembly import inputs
        components=inputs(case)[1]
        held=set(components['components']['held']['parts'])
        for m in gear:
            if m.name not in held:continue
            try:volume=planes(m.points,m.triangles)
            except ValueError:
                unchecked.append(m.name);continue
            volumes.append((tuple(min(p[i] for p in m.points) for i in range(3)),
                            tuple(max(p[i] for p in m.points) for i in range(3)),volume))
        rest_names,rest_values=model_poses(raw)
        preview=posed_hand_mesh(raw,dict(zip(rest_names,rest_values)),1)
        membership=set(indices)
        probe_faces=[face for face in preview.triangles if all(i in membership for i in face)]
    names,seeds=model_poses(rig)
    gw,_=numeric_world(parse_4ds_nodes(rig)['nodes'],dict(zip(names,seeds)),
                       {t['name']:t['channels'] for t in parse_5ds(clip)['tracks']},0)
    by_name={n['name']:n for n in skin['nodes']}
    neutral={'provenance':'MODERNE','runtime_status':'pending',
             'L':{'opposition_degrees':0,'curl_degrees':[0,0]},
             'R':{'opposition_degrees':0,'curl_degrees':[0,0]}}
    bases={name:skin['rest_world'][by_name[name]['index']][0] for name in turns(neutral)}
    cache={};witnesses=[];evaluation_count=0
    def points_for(values):
        chosen,thumb=recipe(base,case,side,values)
        poses,_=author_pose(raw,targets(gw,chosen),
                 {s:{'finger_curl_degrees':g['finger_curl_degrees']} for s,g in chosen.items()},
                 arm_rotation_policy='bend_plane')
        poses=apply(poses,bases,thumb)
        return posed_hand_mesh(raw,poses,1).points
    def evaluate(values):
        nonlocal evaluation_count
        key=tuple(values)
        if key not in cache:
            evaluation_count+=1
            points=points_for(values)
            score,metrics=objective(points,support,indices,digits)
            if surface_aware:
                penalty,probes=probe_penalty(points,indices,probe_faces,volumes,witnesses)
                # Keep five-digit proximity while using all held collision probes.
                score=penalty+sum(g*g for g in metrics['nearest_digit_plane_gaps'])
                metrics.update(probes,objective=score)
            cache[key]=(score,metrics)
        return cache[key]
    initial=[0,0,0,*[abs(v) for v in base[side]['finger_curl_degrees']],0,0,0]
    seeds=[initial,[.02,.025,0,90,75,30,0,0,0],[.02,0,0,60,30,15,0,0,0]]
    if extra_seed is not None:
        recipe(base,case,side,extra_seed)
        seeds.insert(0,list(extra_seed))
    if refine_only:
        if not surface_aware or extra_seed is None:raise ValueError('Refinement requires surface fitting and a seed')
        seeds=[list(extra_seed)]
    candidates=[]
    for seed in seeds:
        best=list(seed);score=evaluate(best)[0]
        levels=((.0025,3.75),(.00125,1.875)) if refine_only else ((.01,15),(.005,7.5),(.0025,3.75),(.00125,1.875))
        for linear,angular in levels:
            for sweep in range(4):
                changed=False
                for axis,(lo,hi) in enumerate(BOUNDS):
                    step=linear if axis<2 else angular
                    for value in (max(lo,best[axis]-step),min(hi,best[axis]+step)):
                        trial=best[:];trial[axis]=value
                        candidate=evaluate(trial)[0]
                        if candidate < score-1e-15:
                            best,score,changed=trial,candidate,True
                if not changed:break
        candidates.append((score,best))
    _,best=min(candidates)
    feedback=[]
    if refine_only:
        # Escape opposition/curl local minima without moving the rest of the hand.
        score=evaluate(best)[0]
        for opposition in (-60,-30,0,30,60):
            for bend in (-60,-30,0,30,60):
                for tip in (-45,0,45):
                    trial=best[:6]+[opposition,bend,tip]
                    value=evaluate(trial)[0]
                    if value<score:best,score=trial,value
        # Add exact missed-face witnesses, then refine the same bounded choices.
        for iteration in range(5):
            found=surface_witnesses(points_for(best),probe_faces,volumes)
            feedback.append(len(found))
            witnesses.extend(found);cache.clear();score=evaluate(best)[0]
            for linear,angular in ((.00125,3.75),(.000625,1.875),(.0003125,.9375)):
                for sweep in range(4):
                    changed=False
                    for axis,(lo,hi) in enumerate(BOUNDS):
                        step=linear if axis<2 else angular
                        for value in (max(lo,best[axis]-step),min(hi,best[axis]+step)):
                            trial=best[:];trial[axis]=value;candidate=evaluate(trial)[0]
                            if candidate<score-1e-15:best,score,changed=trial,candidate,True
                    if not changed:break
            if not surface_witnesses(points_for(best),probe_faces,volumes):break
        feedback.append(len(surface_witnesses(points_for(best),probe_faces,volumes)))
    chosen,thumb=recipe(base,case,side,best)
    return {'parameters':dict(zip(PARAMETERS,best)), 'grip':chosen[side], 'thumb':thumb[side],
            'before':evaluate(initial)[1],'after':evaluate(best)[1],'evaluations':evaluation_count,
            'exact_surface_feedback_counts':feedback,'private_witness_count':len(witnesses),
            'surface_probe_objective':surface_aware,'unchecked_held_pieces':unchecked,
            'contact_qualified':False,'auto_promoted':False}


def build(game,bank_root,archives_only=False,*,surface_aware=False,seed_fitting=None,refine_only=False):
    hands,excluded=read_hands(game,archives_only=archives_only)
    spec=json.loads(RECIPE.read_text(encoding='utf-8'));rows={}
    source=HAND_MODELS[0]
    if seed_fitting is not None:
        from build_fitted_fpv_bank import fitted_grips
        for case in GRIPS:fitted_grips(seed_fitting,spec,case)
    for case in GRIPS:
        rig,clips=load_bank(bank_root/(case+'_CorrectedFPV_v1'),case,source,hands[source])
        rows[case]={}
        for side in ('L','R'):
            seed=None if seed_fitting is None else [seed_fitting['cases'][case][side]['parameters'][k] for k in PARAMETERS]
            rows[case][side]=fit(hands[source],case,side,rig,clips['Idle1']['data'],spec,
                                 surface_aware=surface_aware,extra_seed=seed,refine_only=refine_only)
            print(case,side,json.dumps(rows[case][side]),file=sys.stderr,flush=True)
    return {'schema_version':1,'provenance':'MODERNE','runtime_status':'pending',
        'source_hand_sha256':digest(hands[source]),'source_recipe_sha256':digest(RECIPE.read_bytes()),
        'fit_pose':'Idle1/time=0','cases':rows,'excluded_loose_overrides':excluded,
        'surface_probe_objective':surface_aware,
        'exact_surface_feedback_used':refine_only,
        'seed_fitting_sha256':None if seed_fitting is None else digest(json.dumps(seed_fitting,sort_keys=True).encode()),
        'commercial_geometry_exported':False,'derived_poses_exported':False,
        'other_hand_variant_or_animation_frames_checked':False,
        'surface_crossings_checked':False,'engine_validated':False,
        'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--bank-root',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path,required=True)
    parser.add_argument('--surface-aware',action='store_true')
    parser.add_argument('--seed-fitting',type=Path)
    parser.add_argument('--refine-only',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Candidate report exists; use a fresh name')
        seed=None if args.seed_fitting is None else json.loads(args.seed_fitting.read_text(encoding='utf-8'))
        if args.refine_only and (not args.surface_aware or seed is None):
            raise ValueError('Refinement requires --surface-aware and --seed-fitting')
        report=build(args.game,args.bank_root,args.archives_only,surface_aware=args.surface_aware,
                     seed_fitting=seed,refine_only=args.refine_only)
        with args.json_output.open('x',encoding='utf-8') as out:
            json.dump(report,out,indent=2);out.write('\n')
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Private grip fitting refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
