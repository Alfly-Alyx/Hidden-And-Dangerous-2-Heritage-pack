#!/usr/bin/env python3
"""Fit explicit MODERN elbow-hint paths on private sampled stow poses.

Only authoring hints and measurements are output, never source bone poses.
Sampled authoring is not serialized/continuous surface qualification. The
result is a proposal, not an automatic profile change or game installation.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS,read_hands
from build_equipment_hand_grips import RECIPE,posed_hand_mesh
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import compile_bank,preview_meshes
from build_rigid_weapon_hand_bank import BASE_PROFILE,PROFILE,configuration,placed_tracks,targets,stow_offset,stow_motion,curl_spec
from fit_rigid_elbow_poles import candidate_poles
from hand_pose_ik import author_pose,pinned_skin
from modern_contact_cells import cells,prepare_surface,measure_surface_cells
from modern_thumb_pose import apply,turns
from five_ds import parse_5ds
from build_equipment_hand_animation import f32_row
from ls3d_pose_oracle import reference as pose_reference
import modern_animation as motion


def choose_path(poles,measurements,ready,*,blocked=frozenset()):
    """Lexicographic DP: crossings, inset area, then squared hint movement.

    The final hint is exactly the ready pole, so other clips stay unchanged.
    No count/area penalty can be traded for a shorter path.
    """
    if (not poles or not measurements or ready not in poles
            or any(len(row)!=len(poles) for row in measurements)):
        raise ValueError('Incomplete elbow path candidates')
    states=[]
    for index,row in enumerate(measurements):
        current=[]
        for j,measure in enumerate(row):
            if (len(measure)!=2 or type(measure[0]) is not int or measure[0]<0
                    or type(measure[1]) not in (int,float) or not 0<=measure[1]<float('inf')):
                raise ValueError('Invalid elbow path measurement')
            if index==0:current.append(((measure[0],measure[1],0),[j]));continue
            options=[]
            for k,state in enumerate(states):
                if state is None or (index,k,j) in blocked:continue
                cost,path=state
                movement=sum((a-b)**2 for a,b in zip(poles[j],poles[k]))
                options.append(((cost[0]+measure[0],cost[1]+measure[1],cost[2]+movement),path+[j]))
            current.append(min(options,key=lambda item:(item[0],item[1])) if options else None)
        states=current
    if states[poles.index(ready)] is None:raise ValueError('No sampled elbow path remains')
    cost,indices=states[poles.index(ready)]
    return indices,cost


def interpolate_pose(left,right,seeds,time):
    """Reference the stored float32 keys at one quarter/half/three-quarter step."""
    if type(time) is not int or time not in (10,20,30) or set(left)!=set(right) or set(left)!=set(seeds):
        raise ValueError('Invalid sampled elbow edge')
    result={}
    for name in left:
        channels={kind:{'frames':[0,1],'values':[f32_row(left[name][kind],width),f32_row(right[name][kind],width)]}
                  for kind,width in (('position',3),('rotation',4),('scale',3))}
        result[name]=pose_reference(seeds[name],[{'active':True,'weight':1,'time':time,'channels':channels}])['pose']
    return result


def fit(case,side,hands,profile,*,wide=False,edge_check=False):
    if case not in ('FG42','ZK383') or side!='L':raise ValueError('Unreviewed stow path case')
    recipe,rig,clips,_=compile_bank(case)
    grips,thumb,translation,_=configuration(profile,json.loads(BASE_PROFILE.read_text(encoding='utf-8')),
                                           json.loads(RECIPE.read_text(encoding='utf-8')),case)
    ready=grips[side]['elbow_pole'];poles=candidate_poles(ready,wide=wide)
    # Finer modern diagonal hints permit a gradual bend transition rather than
    # a one-frame jump between the coarse .25-unit grid points.
    poles += [[ready[0],ready[1]+.25*i/20,ready[2]+.25*i/20] for i in range(1,20)]
    prepared_hands=[]
    for source in HAND_MODELS:
        raw=hands[source];_,skin=pinned_skin(raw);names,rest=model_poses(raw)
        by_index={n['index']:n['name'] for n in skin['nodes']};jn=[by_index[i] for i in skin['joint_node_indices']]
        labels=[jn[(skin['parents'][bone-1] if weight>128 else bone)-1] for bone,weight in skin['pairs']]
        selected={i for i,label in enumerate(labels) if label in {f'Bip01 {side} Forearm',f'Bip01 {side} UpperArm'}}
        mesh=posed_hand_mesh(raw,dict(zip(names,rest)),1)
        faces=[f for f in mesh.triangles if any(i in selected for i in f)]
        nodes={n['name']:n for n in skin['nodes']}
        bases={n:skin['rest_world'][nodes[n]['index']][0] for n in turns(thumb)}
        prepared_hands.append((raw,faces,bases,dict(zip(names,rest))))
    original=clips['Arm'][1];end=parse_5ds(original)['frame_end']
    tracks=placed_tracks(original,translation,stow=stow_offset(profile,case),clip_name='Arm',motion_spec=stow_motion(profile,case))
    gear=motion._encode_transform_tracks(end,tracks,preserve_native_rotations=True,name_validator=lambda n:True)
    curls=curl_spec(grips)
    measurements=[];pose_grid=[]
    for frame in range(end+1):
        time=frame*40;wanted=targets(rig,tracks,time,grips,clip_name='Arm')
        volumes=[v for m in preview_meshes(rig,gear,time) for v in cells(m,recipe['parts'])]
        row=[];pose_row=[]
        for pole in poles:
            candidate=deepcopy(wanted);candidate[side]['pole']=pole;count=0;area=0
            candidates=[]
            for raw,faces,bases,seeds in prepared_hands:
                poses,_=author_pose(raw,candidate,curls,arm_rotation_policy='bend_plane')
                poses=apply(poses,bases,thumb);candidates.append(poses)
                mesh=posed_hand_mesh(raw,poses,1)
                result=measure_surface_cells(prepare_surface(mesh.points,faces),volumes)
                count+=result['penetrating_triangle_cells'];area+=result['inset_surface_area_sum']
            row.append((count,area))
            pose_row.append(candidates)
        measurements.append(row);pose_grid.append(pose_row)
        print(case,side,'frame',frame,'best crossing count',min(r[0] for r in row),file=sys.stderr,flush=True)
    indices,cost=choose_path(poles,measurements,ready);blocked=set();edge_receipts={};volume_cache={}
    if edge_check:
        for iteration in range(129):
            failed=False
            if cost[0]:raise ValueError('No zero-crossing sampled key path remains')
            for frame in range(1,end+1):
                edge=(frame,indices[frame-1],indices[frame])
                if edge in edge_receipts:continue
                count=0;depth=0
                for delta in (10,20,30):
                    time=(frame-1)*40+delta
                    if time not in volume_cache:
                        volume_cache[time]=[v for m in preview_meshes(rig,gear,time) for v in cells(m,recipe['parts'])]
                    for h,(raw,faces,bases,seeds) in enumerate(prepared_hands):
                        poses=interpolate_pose(pose_grid[frame-1][edge[1]][h],pose_grid[frame][edge[2]][h],seeds,delta)
                        mesh=posed_hand_mesh(raw,poses,1)
                        measured=measure_surface_cells(prepare_surface(mesh.points,faces),volume_cache[time])
                        count+=measured['penetrating_triangle_cells'];depth=max(depth,measured['max_cell_boundary_depth'])
                edge_receipts[edge]={'penetrating_triangle_cells':count,'max_cell_boundary_depth':depth}
                if count:
                    blocked.add(edge);failed=True
                    print(case,'reject edge',edge,'crossings',count,file=sys.stderr,flush=True)
            if not failed:break
            if iteration==128:raise ValueError('Sampled edge refinement budget exhausted')
            indices,cost=choose_path(poles,measurements,ready,blocked=blocked)
        print(case,'selected path edges checked',end,'rejected edges',len(blocked),file=sys.stderr,flush=True)
    return {'stow_elbow_path':[[i/end,*poles[j]] for i,j in enumerate(indices)],
        'cost':{'penetrating_triangle_cells':cost[0],'inset_area_sum':cost[1],'squared_hint_movement':cost[2]},
        'poles':poles,'measurements':measurements,'selected_indices':indices,'poses_per_variant':end+1,
        'all_equipment_pieces_checked':True,'only_selected_arm_faces_checked':True,
        'sampled_float32_edge_reference_checked':edge_check,'edge_sample_offsets':[10,20,30] if edge_check else [],
        'rejected_edges':len(blocked),'edges_evaluated':len(edge_receipts),
        'final_edge_checks':[{**edge_receipts[(frame,indices[frame-1],indices[frame])],'frame':frame}
                             for frame in range(1,end+1)] if edge_check else [],
        'serialized_clips_and_half_keys_checked':False,'auto_promoted':False,'contact_qualified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--profile',type=Path,default=PROFILE)
    parser.add_argument('--case',choices=('FG42','ZK383'),required=True);parser.add_argument('--wide',action='store_true')
    parser.add_argument('--edge-check',action='store_true')
    parser.add_argument('--json-output',type=Path,required=True);args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Use a fresh path report')
        hands,excluded=read_hands(args.game,archives_only=args.archives_only)
        profile=json.loads(args.profile.read_text(encoding='utf-8'));row=fit(args.case,'L',hands,profile,wide=args.wide,edge_check=args.edge_check)
        report={'schema_version':1,'provenance':'MODERNE','runtime_status':'pending','case':args.case,'side':'L',
            'source_profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),'excluded_loose_overrides':excluded,
            'result':row,'commercial_geometry_exported':False,'game_started':False,'game_modified':False}
        with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(row['cost']));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Modern elbow path fitting refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
