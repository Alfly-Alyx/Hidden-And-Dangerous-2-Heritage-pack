#!/usr/bin/env python3
"""Private flat FPV candidate: native lookup, persistent poses and CPU skins.

The original hierarchical equipment is compared through its reviewed numeric
reference. This does not execute a scene loader, clone, renderer or the game.
"""
import argparse
import json
from pathlib import Path
import sys

from build_equipment_fpv_animation import compile_fpv_bank,numeric_world
from build_equipment_hand_animation import compile_hand_bank,IDENTITY,wrist_from_native,PROVENANCE
from build_modern_equipment_fpv_rig import compile_flat_rig
from build_equipment_hand_grips import RECIPE,effective_hands
from build_modern_equipment_assembly import inputs,compile_assembly,CASES
from build_modern_equipment_hose import compile_hose_bank,digest
from benelli_fpv_rig_audit import read_hands,HAND_MODELS,HAND_PINS
from hand_pose_ik import pinned_skin
from animation_tick_audit import model_poses,bank_cases,audit_cases,check_receipt
from animation_attach_audit import op
from four_ds_skin import read_reviewed
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from ls3d_frame_find_oracle import FrameFindOracle
from ls3d_tick_oracle import TickOracle
from ls3d_palette_oracle import PaletteOracle
from ls3d_skin_oracle import SkinOracle,transformed
from ls3d_palette_audit import check_receipt as check_palette
from ls3d_skin_audit import check_receipt as check_skin
from ls3d_math_oracle import DLL_SHA


def audit(hands,spec,library,progress=None):
    if set(hands)!=set(HAND_PINS):raise ValueError('Incomplete pinned hand source set')
    for name,raw in hands.items():
        if (len(raw),digest(raw))!=HAND_PINS[name][1:]:raise ValueError('Changed pinned hand source')
    finder=FrameFindOracle(library);tick=TickOracle(library);palette=PaletteOracle(library);skin_machine=SkinOracle(library)
    totals=dict.fromkeys(('dense_sequences','observed_ticks','observed_node_poses','equipment_matrix_comparisons',
        'hand_joint_poses','hand_vertices','hose_lod_evaluations','hose_vertices','wrist_targets','hose_endpoint_vertices'),0)
    errors=dict.fromkeys(('tick','palette','skin','equipment_at_keys','equipment_between_keys','wrist_at_keys',
        'wrist_between_keys','fixed_hose_endpoint','held_hose_endpoint'),0);cases={}
    for case in CASES:
        args=inputs(case);flat,original,rig_report=compile_flat_rig(case);_,_,assembly=compile_assembly(*args)
        old_nodes=parse_4ds_nodes(original)['nodes'];old_names,old_seeds=model_poses(original);old_seeds=dict(zip(old_names,old_seeds))
        gear_nodes=parse_4ds_nodes(flat)['nodes'];gear_names,gear_initial=model_poses(flat)
        gear_index={name:i for i,name in enumerate(gear_names)}
        scene=[{'name':n['name'],'frame_type':n['frame_type'],'parent':n['parent_id']-1} for n in gear_nodes]
        selection=finder.find(scene,'fpv_weapon',1)
        if selection['index']!=0 or selection['direct_children']!=list(range(1,len(gear_nodes))):
            raise ValueError('Native FPV frame selection failed')
        hose_raw,_,_,hose_report=compile_hose_bank(*args)
        hoses=[read_reviewed(hose_raw,allow_multiple_lods=True,lod=i) for i in (0,1)]
        hose_nodes={n['index']:n for n in hoses[0]['nodes']}
        hose_names=[hose_nodes[n]['name'] for n in hoses[0]['joint_node_indices']]
        # Diagnostic joint-only matrix hierarchy. The visual root is represented
        # as a joint so CPU output is in a common world space. This is NOT a
        # claim about the loaded skin/renderer division of model transforms.
        inverse_binds=[IDENTITY[:] for _ in gear_nodes]
        for name,inverse in zip(hose_names,hoses[0]['inverse_binds']):inverse_binds[gear_index[name]]=inverse
        chosen=effective_hands(spec,case);variants={}
        for source in HAND_MODELS:
            _,hand_skin=pinned_skin(hands[source]);hand_names,hand_initial=model_poses(hands[source])
            actual,clips,build=compile_fpv_bank(case,hands[source],spec)
            source_rig,source_clips,_=compile_hand_bank(case,hands[source],spec)
            if flat!=actual or source_rig!=original:raise ValueError('Mismatched flat/source FPV rigs')
            names=hand_names+gear_names;initial=hand_initial+gear_initial;index={name:i for i,name in enumerate(names)}
            if len(index)!=len(names):raise ValueError('Ambiguous combined FPV names')
            bones={node:i for i,node in enumerate(hand_skin['joint_node_indices'])}
            hand_by_index={n['index']:n for n in hand_skin['nodes']};hand_by_name={n['name']:n for n in hand_skin['nodes']}
            boundaries=audit_cases(tick,bank_cases(names,{k:v[1] for k,v in clips.items()},initial))
            errors['tick']=max(errors['tick'],boundaries['max_error']);states={}
            for clip,(_,raw) in clips.items():
                source_animation=source_clips[clip][1]
                if digest(source_animation)!=build['clips'][clip]['original_clip_sha256']:
                    raise ValueError('Reference source clip changed')
                source_tracks={t['name']:t['channels'] for t in parse_5ds(source_animation)['tracks']}
                end=build['clips'][clip]['frame_end'];deltas=[0]+[20]*(end*2)+[0,20];elapsed=0
                def observe(step,delta,poses):
                    nonlocal elapsed
                    elapsed+=delta
                    if len(poses)!=len(names):raise ValueError('Incomplete native flat FPV pose')
                    for i in range(len(hand_names)):
                        if any(poses[i][kind]!=hand_initial[i][kind] for kind in ('position','scale')):
                            raise ValueError('Native flat FPV stretched or moved a hand joint')
                    if poses[index['a']]!=hand_initial[index['a']]:raise ValueError('Unexpected native hand root motion')
                    hand_joints=[{**poses[index[hand_by_index[node]['name']]],
                        'parent':-1 if hand_by_index[node]['parent_id']==1 else bones[hand_by_index[node]['parent_id']]}
                        for node in hand_skin['joint_node_indices']]
                    hp=palette.assemble(hand_joints,hand_skin['inverse_binds']);check_palette(hp,36)
                    hand_values=skin_machine.deform(hand_skin['vertices'],hand_skin['pairs'],hp['palette'],hand_skin['parents'])
                    check_skin(hand_values,len(hand_skin['vertices']))
                    gp=palette.assemble([{**poses[index[n['name']]],'parent':n['parent_id']-1} for n in gear_nodes],inverse_binds)
                    check_palette(gp,len(gear_nodes));world=dict(zip(gear_names,gp['world_matrices']))
                    errors['palette']=max(errors['palette'],*hp['max_errors'].values(),*gp['max_errors'].values())
                    errors['skin']=max(errors['skin'],hand_values['max_error'])
                    reference,_=numeric_world(old_nodes,old_seeds,source_tracks,min(elapsed,end*40))
                    on_key=min(elapsed,end*40)%40==0
                    for old,new in rig_report['source_to_fpv_names'].items():
                        error=max(abs(a-b) for a,b in zip(reference[old],world[new]))
                        label='equipment_at_keys' if on_key else 'equipment_between_keys'
                        errors[label]=max(errors[label],error)
                        if error>(2e-6 if on_key else .0002):raise ValueError('Flat equipment differs from original hierarchy')
                        totals['equipment_matrix_comparisons']+=1
                    held=world['MOD_held_pivot']
                    for side,label in (('L','left'),('R','right')):
                        requested=wrist_from_native(held,world['MOD_'+label+'_hand'],chosen[side])
                        actual=hp['world_matrices'][bones[hand_by_name[f'Bip01 {side} Hand']['index']]][12:15]
                        error=max(abs(a-b) for a,b in zip(requested,actual))
                        label='wrist_at_keys' if on_key else 'wrist_between_keys';errors[label]=max(errors[label],error)
                        if error>(5e-6 if on_key else .0002):raise ValueError('Native flat FPV wrist drift')
                        totals['wrist_targets']+=1
                    matrices=[gp['palette'][gear_index[name]] for name in hose_names]
                    for hose in hoses:
                        row=skin_machine.deform(hose['vertices'],hose['pairs'],matrices,hose['parents'])
                        check_skin(row,len(hose['vertices']));errors['skin']=max(errors['skin'],row['max_error'])
                        for vertex,(bone,_),actual in zip(hose['vertices'],hose['pairs'],row['values']):
                            weight=hose_report['influence_weights'][bone-1]
                            if weight not in (0,1):continue
                            if weight==0:
                                expected=transformed(vertex[:3],world['fpv_weapon']);label='fixed_hose_endpoint'
                            else:
                                local=[a-b for a,b in zip(vertex[:3],assembly['component_origins']['held'])]
                                expected=transformed(local,held);label='held_hose_endpoint'
                            error=max(abs(a-b) for a,b in zip(actual[:3],expected));errors[label]=max(errors[label],error)
                            if error>2e-6:raise ValueError('Native flat FPV hose endpoint drift')
                            totals['hose_endpoint_vertices']+=1
                        totals['hose_vertices']+=row['vertices'];totals['hose_lod_evaluations']+=1
                    totals['observed_ticks']+=1;totals['observed_node_poses']+=len(poses)
                    totals['hand_joint_poses']+=36;totals['hand_vertices']+=hand_values['vertices']
                bank={clip:{'data':raw,'mode':1}};operations=[op(clip,7)]
                row=tick.sequence_with_ticks(names,bank,operations,initial,deltas,pose_observer=observe)
                check_receipt(row,names,bank,operations,initial,deltas,9);errors['tick']=max(errors['tick'],row['max_error'])
                totals['dense_sequences']+=1;states[clip]={'sha256':digest(raw),'frame_end':end,'observed_ticks':len(deltas)}
                if progress:progress(case,source,clip,len(deltas))
            variants[source]={'hand_sha256':HAND_PINS[source][2],'target_count':len(names),
                'boundary_and_overlap_cases':boundaries,'persistent_sequences':states}
        cases[case]={'flat_model_sha256':digest(flat),'original_model_sha256':digest(original),
            'native_frame_selection':selection,'variants':variants}
    return {'schema_version':1,'scope':'private_flat_fpv_native_lookup_time_pose_palette_skin',
        'provenance':PROVENANCE,'library_sha256':DLL_SHA,'cases':cases,'totals':totals,'max_errors':errors,
        'specification_sha256':digest(json.dumps(spec,sort_keys=True).encode()),
        'poses_observed_from_persistent_native_memory':True,'original_equipment_compared_to_numeric_reference':True,
        'palette_and_skin_use_separate_emulators':True,'equipment_palette_uses_diagnostic_joint_only_hierarchy':True,
        'source_hand_geometry_used_privately':True,'original_animation_keys_read':False,
        'commercial_geometry_exported':False,'native_loader_executed':False,'native_clone_qualified':False,
        'actual_loaded_skin_root_renderer_transform_division_qualified':False,
        'camera_calibrated':False,'events_renderer_gameplay_called':False,'runtime_clip_changes_executed':False,
        'game_started':False,'game_modified':False,'engine_validated':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--json-output',type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        hands,excluded=read_hands(args.game,archives_only=args.archives_only)
        report=audit(hands,json.loads(RECIPE.read_text(encoding='utf-8')),(args.game/'LS3DF.dll').read_bytes(),
            lambda case,source,clip,count:print(f'Checked native flat FPV: {case} / {source} / {clip} / {count}',
                file=sys.stderr,flush=True))
        report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native flat FPV audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
