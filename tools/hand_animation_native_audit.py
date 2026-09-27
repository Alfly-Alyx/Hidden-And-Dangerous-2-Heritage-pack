#!/usr/bin/env python3
"""Private derived clips: persistent native time/pose, then native skin.

Hands and modern equipment share one controller. Commercial rest/model data
stay private. No loaded scene, renderer, events, game or installation.
"""
import argparse
import json
from pathlib import Path
import sys

from build_equipment_hand_animation import compile_hand_bank,PROVENANCE,wrist_from_native,IDENTITY
from build_equipment_hand_grips import RECIPE,effective_hands
from build_modern_equipment_assembly import inputs,compile_assembly,CASES
from build_modern_equipment_hose import compile_hose_bank,digest
from benelli_fpv_rig_audit import read_hands,HAND_MODELS,HAND_PINS
from hand_pose_ik import pinned_skin
from animation_tick_audit import model_poses,bank_cases,audit_cases,check_receipt
from animation_attach_audit import op
from four_ds_skin import read_reviewed
from ls3d_tick_oracle import TickOracle
from ls3d_palette_oracle import PaletteOracle
from ls3d_skin_oracle import SkinOracle,transformed
from ls3d_palette_audit import check_receipt as check_palette
from ls3d_skin_audit import check_receipt as check_skin
from ls3d_math_oracle import DLL_SHA


def audit(hands,spec,library,progress=None):
    if set(hands)!=set(HAND_PINS):raise ValueError('Incomplete pinned hand sources')
    for source,raw in hands.items():
        if (len(raw),digest(raw))!=HAND_PINS[source][1:]:raise ValueError('Changed pinned hand source')
    tick=TickOracle(library);palette=PaletteOracle(library);skin_machine=SkinOracle(library)
    totals=dict.fromkeys(('dense_sequences','observed_ticks','observed_node_poses','hand_joint_poses',
        'hand_vertices','hose_lod_evaluations','hose_vertices','wrist_targets','hose_endpoint_vertices'),0)
    errors=dict.fromkeys(('tick','palette','skin','wrist_at_keys','wrist_between_keys','fixed_hose_endpoint','held_hose_endpoint'),0)
    cases={}
    for case in CASES:
        args=inputs(case);rig,_,assembly=compile_assembly(*args);gear_names,gear_initial=model_poses(rig)
        hose_raw,_,_,hose_report=compile_hose_bank(*args)
        hose_skins=[read_reviewed(hose_raw,allow_multiple_lods=True,lod=i) for i in (0,1)]
        hose_nodes={n['index']:n for n in hose_skins[0]['nodes']}
        hose_names=[hose_nodes[i]['name'] for i in hose_skins[0]['joint_node_indices']]
        rig_root=assembly['root'];held_root=gear_names[assembly['source_index_maps']['held'][1]-1]
        diagnostic_names=[rig_root,held_root,'MOD_held_pivot','MOD_left_hand','MOD_right_hand']
        hand_spec=effective_hands(spec,case);variants={}
        for source in HAND_MODELS:
            _,hand_skin=pinned_skin(hands[source]);hand_names,hand_initial=model_poses(hands[source])
            actual_rig,clips,build=compile_hand_bank(case,hands[source],spec)
            if rig!=actual_rig:raise ValueError('Derived bank changed modern assembly')
            names=hand_names+gear_names;initial=hand_initial+gear_initial;index={name:i for i,name in enumerate(names)}
            if len(index)!=len(names):raise ValueError('Ambiguous combined target names')
            by_node={n['index']:n for n in hand_skin['nodes']}
            hand_bones={node:i for i,node in enumerate(hand_skin['joint_node_indices'])}
            by_name={n['name']:n for n in hand_skin['nodes']}
            boundaries=audit_cases(tick,bank_cases(names,{k:v[1] for k,v in clips.items()},initial))
            errors['tick']=max(errors['tick'],boundaries['max_error'])
            states={}
            for clip,(_,raw) in clips.items():
                end=build['clips'][clip]['frame_end'];deltas=[0]+[20]*(end*2)+[0,20];elapsed=0
                def observe(step,delta,poses):
                    nonlocal elapsed
                    elapsed+=delta
                    if len(poses)!=len(names):raise ValueError('Incomplete combined native pose')
                    # All authored hand positions/scales are the pinned rest
                    # values. No interpolated bone stretching is permissible.
                    for i in range(len(hand_names)):
                        if any(poses[i][kind]!=hand_initial[i][kind] for kind in ('position','scale')):
                            raise ValueError('Native hand animation moved or stretched a joint')
                    if poses[index['a']]!=hand_initial[index['a']]:raise ValueError('Hand root unexpectedly moved')
                    joints=[{**poses[index[by_node[node]['name']]],
                        'parent':-1 if by_node[node]['parent_id']==1 else hand_bones[by_node[node]['parent_id']]}
                        for node in hand_skin['joint_node_indices']]
                    hand_palette=palette.assemble(joints,hand_skin['inverse_binds']);check_palette(hand_palette,36)
                    deformed=skin_machine.deform(hand_skin['vertices'],hand_skin['pairs'],
                        hand_palette['palette'],hand_skin['parents'])
                    check_skin(deformed,len(hand_skin['vertices']))
                    diagnostic=palette.assemble([{**poses[index[name]],'parent':parent}
                        for name,parent in zip(diagnostic_names,(-1,0,1,2,2))],[IDENTITY]*5)
                    check_palette(diagnostic,5)
                    held=diagnostic['world_matrices'][2]
                    for side,anchor_number in (('L',3),('R',4)):
                        requested=wrist_from_native(held,diagnostic['world_matrices'][anchor_number],hand_spec[side])
                        bone=hand_bones[by_name[f'Bip01 {side} Hand']['index']]
                        actual=hand_palette['world_matrices'][bone][12:15]
                        error=max(abs(a-b) for a,b in zip(actual,requested))
                        on_key=min(elapsed,end*40)%40==0
                        label='wrist_at_keys' if on_key else 'wrist_between_keys';limit=5e-6 if on_key else .0002
                        errors[label]=max(errors[label],error)
                        if error>limit:raise ValueError(f'Native grip interpolation drift: {case}/{source}/{clip}/{elapsed}: {error}')
                        totals['wrist_targets']+=1
                    # Explicit diagnostic assembly-root parent for the hose:
                    # model geometry itself remains unchanged and root-local.
                    hose_joints=[{**poses[index[rig_root]],'parent':-1}]+[
                        {**poses[index[name]],'parent':0} for name in hose_names]
                    hose_palette=palette.assemble(hose_joints,[IDENTITY]+hose_skins[0]['inverse_binds'])
                    check_palette(hose_palette,9)
                    errors['palette']=max(errors['palette'],*hand_palette['max_errors'].values(),
                        *diagnostic['max_errors'].values(),*hose_palette['max_errors'].values())
                    errors['skin']=max(errors['skin'],deformed['max_error'])
                    for hose in hose_skins:
                        row=skin_machine.deform(hose['vertices'],hose['pairs'],hose_palette['palette'][1:],hose['parents'])
                        check_skin(row,len(hose['vertices']));errors['skin']=max(errors['skin'],row['max_error'])
                        for vertex,(bone,_),actual in zip(hose['vertices'],hose['pairs'],row['values']):
                            weight=hose_report['influence_weights'][bone-1]
                            if weight not in (0,1):continue
                            if weight==0:
                                expected=transformed(vertex[:3],diagnostic['world_matrices'][0]);label='fixed_hose_endpoint'
                            else:
                                local=[a-b for a,b in zip(vertex[:3],assembly['component_origins']['held'])]
                                expected=transformed(local,held);label='held_hose_endpoint'
                            error=max(abs(a-b) for a,b in zip(actual[:3],expected));errors[label]=max(errors[label],error)
                            if error>2e-6:raise ValueError('Native hose endpoint drift in combined grip clip')
                            totals['hose_endpoint_vertices']+=1
                        totals['hose_lod_evaluations']+=1;totals['hose_vertices']+=row['vertices']
                    totals['observed_ticks']+=1;totals['observed_node_poses']+=len(poses)
                    totals['hand_joint_poses']+=36;totals['hand_vertices']+=deformed['vertices']
                bank={clip:{'data':raw,'mode':1}};operations=[op(clip,7)]
                row=tick.sequence_with_ticks(names,bank,operations,initial,deltas,pose_observer=observe)
                check_receipt(row,names,bank,operations,initial,deltas,9)
                errors['tick']=max(errors['tick'],row['max_error']);totals['dense_sequences']+=1
                states[clip]={'sha256':digest(raw),'frame_end':end,'observed_ticks':len(deltas)}
                if progress:progress(case,source,clip,len(deltas))
            variants[source]={'hand_sha256':HAND_PINS[source][2],'target_count':len(names),
                'boundary_and_overlap_cases':boundaries,'persistent_sequences':states}
        cases[case]={'assembly_sha256':digest(rig),'variants':variants}
    return {'schema_version':1,'scope':'private_derived_grips_combined_native_persistent_animation',
        'provenance':PROVENANCE,'library_sha256':DLL_SHA,'cases':cases,'totals':totals,'max_errors':errors,
        'specification_sha256':digest(json.dumps(spec,sort_keys=True).encode()),
        'hands_held_and_hose_share_one_clip_slot_and_clock':True,'poses_observed_from_native_memory':True,
        'poses_persist_across_ticks':True,'palette_and_skin_use_separate_emulators':True,
        'initial_pose_is_explicit_seed':True,'commercial_rest_skeleton_used_privately':True,
        'commercial_geometry_exported':False,'original_animation_keys_read':False,
        'native_loader_executed':False,'events_renderer_gameplay_called':False,'finger_contact_qualified':False,
        'thumb_pose_authored':False,'camera_calibrated':False,'player_or_ai_attachment_qualified':False,
        'runtime_clip_changes_executed':False,'game_started':False,'game_modified':False,'engine_validated':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--json-output',type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        hands,excluded=read_hands(args.game,archives_only=args.archives_only)
        report=audit(hands,json.loads(RECIPE.read_text(encoding='utf-8')),(args.game/'LS3DF.dll').read_bytes(),
            lambda case,source,clip,count:print(f'Checked native animated grip: {case} / {source} / {clip} / {count}',
                file=sys.stderr,flush=True))
        report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native derived hand animation audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
