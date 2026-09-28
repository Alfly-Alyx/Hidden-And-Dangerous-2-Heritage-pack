#!/usr/bin/env python3
"""Private shared-memory animation/correction/refresh audit, no game hook."""
import argparse
import json
import math
from pathlib import Path
import sys

from animation_stream_audit import attach
from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import read_hands,HAND_MODELS
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import CASES,compile_bank
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from native_hand_constraints import ArmSolverOracle
from native_hand_targets import validate_receipt
from native_hand_pipeline import validate_receipt as validate_pipeline_receipt
from rigid_hand_transition_audit import PAIRS,schedule,LIMIT
from rigid_weapon_hand_audit import load_bank,suffix_checked
from unified_hand_pose_oracle import UnifiedHandPoseOracle


def retention_schedule():
    return [attach('Idle1',0),{'kind':'tick','delta':0},{'kind':'tick','delta':40},
            *[{'kind':'tick','delta':0} for _ in range(8)],
            {'kind':'weight','slot':0,'weight':0},{'kind':'tick','delta':40},
            {'kind':'weight','slot':0,'weight':1},{'kind':'tick','delta':20},
            attach(None,0),*[{'kind':'tick','delta':0} for _ in range(4)]]


def summarize(rows):
    if not isinstance(rows,list) or not rows:raise ValueError('Missing unified reports')
    total={'sequences':len(rows),'ticks':0,'native_pose_calls':0,'compiled_arm_calls':0,
           'compiled_target_calls':0,'compiled_pipeline_calls':0,'max_target_input_error':0,
           'committed_rotations':0,'local_rebuilds':0,'clean_ticks_without_native_pose':0,
           'raw_ticks_over_limit':0,'max_before':0,'max_after':0,'max_matrix_error':0,
           'max_native_pose_error':0,'max_solver_rotation_error':0,'owner_allocations':0,'owner_releases':0}
    for row in rows:
        compiled_targets=row.get('target_preparation_compiled',False)
        if type(compiled_targets) is not bool:raise ValueError('Invalid target preparation mode')
        pipeline=row.get('compiled_pipeline_shared_memory',False)
        if (type(pipeline) is not bool or row.get('solver_cpu_separate') is not (not pipeline)
                or (pipeline and not compiled_targets)):raise ValueError('Invalid compiled pipeline memory mode')
        if (any(row.get(k) is not True for k in ('native_animation_compiled_commit_refresh_palette_same_memory',
                'poses_seeded_only_before_first_operation','reference_corrected_poses_carried_independently'))
                or any(row.get(k) is not False for k in ('client_hook_implemented','loaded_scene_qualified',
                    'owning_visual_bounds_evaluated','game_started'))
                or type(row.get('ticks')) is not int or not isinstance(row.get('samples'),list)
                or row['ticks']!=len(row['samples'])):
            raise ValueError('Incomplete unified memory receipt')
        for key in ('max_native_pose_error','max_solver_rotation_error'):
            value=row.get(key)
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=2e-6:
                raise ValueError('Unreviewed unified numerical error')
            total[key]=max(total[key],value)
        for key in ('owner_allocations','owner_releases'):
            value=row.get(key)
            if type(value) is not int or not 0<=value<=4096:raise ValueError('Invalid unified owner count')
            total[key]+=value
        for sample in row['samples']:
            preparation=sample.get('compiled_target_preparation')
            if pipeline:
                if preparation is not None:raise ValueError('Pipeline also reported a separate target processor')
                total['max_target_input_error']=max(total['max_target_input_error'],validate_pipeline_receipt(sample.get('compiled_pipeline')))
                total['compiled_target_calls']+=1;total['compiled_pipeline_calls']+=1
            elif sample.get('compiled_pipeline') is not None:raise ValueError('Unexpected compiled pipeline receipt')
            elif compiled_targets:
                total['max_target_input_error']=max(total['max_target_input_error'],validate_receipt(preparation))
                total['compiled_target_calls']+=1
            elif preparation is not None:raise ValueError('Unexpected compiled target receipt')
            for key,limit in (('native_pose_calls',128),('local_rebuilds',37)):
                value=sample.get(key)
                if type(value) is not int or not 0<=value<=limit:raise ValueError('Invalid unified sample count')
                total[key]+=value
            for key in ('before','after'):
                values=sample.get(key)
                if (not isinstance(values,dict) or set(values)!={'L','R'}
                        or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in values.values())):
                    raise ValueError('Invalid unified wrist sample')
                worst=max(values.values());total['max_'+key]=max(total['max_'+key],worst)
                if key=='after' and worst>5e-6:raise ValueError('Unified corrected wrist missed')
            error=sample.get('max_matrix_error')
            if type(error) not in (int,float) or not math.isfinite(error) or not 0<=error<=5e-5:
                raise ValueError('Invalid persistent palette error')
            total['max_matrix_error']=max(total['max_matrix_error'],error)
            total['ticks']+=1;total['compiled_arm_calls']+=2;total['committed_rotations']+=6
            total['clean_ticks_without_native_pose']+=int(sample['native_pose_calls']==0)
            total['raw_ticks_over_limit']+=int(max(sample['before'].values())>LIMIT)
    return total


def audit(game,bank_root,suffix,profile,compiled_solver,compiled_commit,case,*,archives_only=False,compiled_targets=None,compiled_pipeline=None):
    if case not in CASES:raise ValueError('Unreviewed unified weapon')
    suffix_checked(suffix)
    if (compiled_pipeline is None and compiled_solver is None) or (compiled_pipeline is not None
            and (compiled_solver is not None or compiled_targets is not None)):
        raise ValueError('Choose a compiled pipeline or a separate solver and optional target processor')
    library=(game/'LS3DF.dll').read_bytes();commit_raw=compiled_commit.read_bytes()
    solver_raw=compiled_solver.read_bytes() if compiled_solver is not None else None
    pipeline_raw=compiled_pipeline.read_bytes() if compiled_pipeline is not None else None
    preparer=None;target_raw=None
    if compiled_targets is not None:
        from native_hand_targets import TargetPreparationOracle
        target_raw=compiled_targets.read_bytes();preparer=TargetPreparationOracle(target_raw)
    machine=UnifiedHandPoseOracle(library,commit_raw,ArmSolverOracle(solver_raw) if solver_raw is not None else None,preparer,pipeline_raw)
    hands,excluded=read_hands(game,archives_only=archives_only);compiled=compile_bank(case);variants={}
    for source in HAND_MODELS:
        hand=hands[source]
        rig,bank,grips=load_bank(bank_root/(case+'_'+suffix),case,source,hand,profile,compiled)
        hn,hi=model_poses(hand);gn,gi=model_poses(rig);nodes=parse_4ds_nodes(rig)['nodes']
        clips={k:{'data':v[1],'mode':1} for k,v in bank.items()};rows=[]
        for a,b in PAIRS:
            for phase in (0,1,2):
                steps=schedule(a,b,parse_5ds(clips[a]['data'])['frame_end'],phase)
                row=machine.run(hand,nodes,hn+gn,clips,hi+gi,steps,grips)
                rows.append({'source':a,'target':b,'source_phase_halves':phase,**row})
            print(source+': '+a+' -> '+b+' unified',file=sys.stderr,flush=True)
        retention=machine.run(hand,nodes,hn+gn,clips,hi+gi,retention_schedule(),grips)
        variants[source]={'hand_sha256':digest(hand),'model_sha256':digest(rig),
            'clips':{k:digest(v[1]) for k,v in bank.items()},'transitions':rows,
            'transition_totals':summarize(rows),'retention':retention,'retention_totals':summarize([retention])}
        print(source+': zero-delta, zero-weight and full-detach retention checked',file=sys.stderr,flush=True)
    return {'schema_version':1,'scope':'private_unified_native_rigid_hand_memory','case':case,
        'runtime_status':'pending','library_sha256':digest(library),'compiled_solver_sha256':digest(solver_raw) if solver_raw is not None else None,
        'compiled_commit_sha256':digest(commit_raw),'profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),
        'compiled_targets_sha256':digest(target_raw) if target_raw is not None else None,
        'compiled_pipeline_sha256':digest(pipeline_raw) if pipeline_raw is not None else None,
        'excluded_loose_overrides':excluded,'variants':variants,
        'animation_commit_refresh_palette_share_memory':True,'solver_cpu_separate':pipeline_raw is None,
        'compiled_pipeline_shares_animation_cpu_and_memory':pipeline_raw is not None,
        'hand_root_is_diagnostic_joint':True,'owning_visual_is_supplied_record':True,
        'post_tick_control_is_diagnostic_host_code':True,'client_hook_implemented':False,
        'client_transition_orders_proven_reachable':False,'loaded_scene_qualified':False,
        'surfaces_or_skin_or_renderer_executed':False,'frame_budget_qualified':False,
        'commercial_geometry_or_poses_exported':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('game','bank-root','profile','compiled-commit','json-output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--bank-suffix',required=True);parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--compiled-targets',type=Path)
    parser.add_argument('--compiled-solver',type=Path);parser.add_argument('--compiled-pipeline',type=Path)
    parser.add_argument('--archives-only',action='store_true');args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Use a fresh unified report path')
        report=audit(args.game,args.bank_root,args.bank_suffix,json.loads(args.profile.read_text(encoding='utf-8')),
            args.compiled_solver,args.compiled_commit,args.case,archives_only=args.archives_only,
            compiled_targets=args.compiled_targets,compiled_pipeline=args.compiled_pipeline)
        with args.json_output.open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
        print(json.dumps({s:{k:v[k] for k in ('transition_totals','retention_totals')}
                         for s,v in report['variants'].items()},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Unified hand memory refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
