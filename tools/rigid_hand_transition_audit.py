#!/usr/bin/env python3
"""Private diagnostic crossfades of rigid hand banks, never a game hook.

The schedules deliberately include interrupted clips. They are test inputs,
not a claim that the client selects every sampled transition. Source poses,
commercial geometry and derived animation bytes are never exported here.
"""
import argparse
import json
import math
from pathlib import Path
import sys

from animation_stream_audit import attach, check_receipt
from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import HAND_MODELS, read_hands
from build_equipment_hand_animation import IDENTITY
from build_modern_animation_bank import ALIASES
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import CASES, compile_bank
from build_rigid_weapon_hand_bank import PROFILE
from five_ds import parse_5ds
from fpv_contact_constraints import correct, targets, world, wrist_errors
from fpv_transition_contact_audit import trace
from menu_gui_audit import parse_4ds_nodes
from rigid_weapon_hand_audit import load_bank, suffix_checked

PAIRS=(('Idle1','Aim'),('Aim','AimShot'),('AimShot','Aim'),('Aim','Daim'),
       ('Daim','Idle1'),('Idle1','Rel'),('Rel','Idle1'),('Idle1','Disarm'),
       ('Arm','Idle1'),('Shot','Idle1'),('Idle1','Shot'),('Jammed','Idle1'),('Idle1','Jammed'))
LIMIT=.0002


def schedule(source,target,source_end,phase):
    if ((source,target) not in PAIRS or source not in ALIASES or target not in ALIASES
            or type(source_end) is not int or not 1<=source_end<=179
            or type(phase) is not int or phase not in (0,1,2)):
        raise ValueError('Unreviewed diagnostic transition')
    steps=[attach(source,0),{'kind':'tick','delta':source_end*20*phase},attach(target,1,0)]
    for weight in (0,.25,.5,.75,1):
        steps.extend(({'kind':'weight','slot':0,'weight':1-weight},
                      {'kind':'weight','slot':1,'weight':weight},{'kind':'tick','delta':20}))
    steps.extend((attach(None,0),{'kind':'tick','delta':0}))
    return steps


def correction_receipt(row):
    if (any(row.get(k) is not True for k in ('finger_poses_preserved','equipment_poses_preserved',
                                           'source_rest_transforms_preserved'))
            or row.get('changed_channels')!='six_arm_rotations_only'
            or row.get('engine_hook_implemented') is not False):
        raise ValueError('Incomplete transition correction receipt')
    for key in ('before','after'):
        values=row.get(key)
        if (not isinstance(values,dict) or set(values)!={'L','R'}
                or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in values.values())):
            raise ValueError('Invalid transition wrist errors')
    if max(row['after'].values())>5e-6:raise ValueError('Transition correction missed wrist target')


def check_pose(values,expected):
    if (not isinstance(values,list) or len(values)!=len(expected)
            or any(not isinstance(p,dict) or set(p)!={'position','rotation','scale'} for p in values)):
        raise ValueError('Incomplete transition pose observation')
    error=0
    for pose,ref in zip(values,expected):
        for key,width in (('position',3),('rotation',4),('scale',3)):
            if (not isinstance(pose[key],list) or len(pose[key])!=width
                    or any(type(v) not in (int,float) or not math.isfinite(v) for v in pose[key])):
                raise ValueError('Invalid transition pose channel')
            error=max(error,*(abs(a-b) for a,b in zip(pose[key],ref[key])))
    if error>2e-6:raise ValueError('Transition observation differs from reference')
    return error


def audit_bank(hand,rig,bank,grips,*,stream=None,palette=None,corrector=None):
    if corrector is None:corrector=correct
    if not callable(corrector):raise ValueError('Invalid transition corrector')
    if (stream is None)!=(palette is None):raise ValueError('Both native transition subsystems required')
    if set(bank)!=set(ALIASES):raise ValueError('Incomplete transition bank')
    hn,hi=model_poses(hand);gn,gi=model_poses(rig)
    if set(hn)&set(gn):raise ValueError('Ambiguous transition targets')
    names,initial=hn+gn,hi+gi
    hnodes=parse_4ds_nodes(hand)['nodes'];gnodes=parse_4ds_nodes(rig)['nodes']
    clips={k:{'data':v[1],'mode':1} for k,v in bank.items()}
    totals=dict(sequences=0,ticks=0,wrist_observations=0,raw_ticks_over_limit=0,native_palettes=0)
    maxima=dict(before=0,after=0,stream=0,palette=0);sequences=[];worst=None
    for source,target in PAIRS:
        end=parse_5ds(clips[source]['data'])['frame_end']
        for phase in (0,1,2):
            steps=schedule(source,target,end,phase);reference=trace(names,clips,initial,steps);samples=[]

            def observe(index,delta,values):
                nonlocal worst
                if index!=len(samples) or index>=len(reference) or delta!=reference[index]['delta']:
                    raise ValueError('Misaligned transition observation')
                maxima['stream']=max(maxima['stream'],check_pose(values,reference[index]['poses']))
                before=dict(zip(names,values))
                after,receipt=corrector(hand,gnodes,before,grips,root_name='fpv_weapon',
                                      preserve_observed_elbow_plane=True)
                correction_receipt(receipt)
                if palette is not None:
                    wanted=targets(world(gnodes,before),grips,root_name='fpv_weapon')
                    for label,poses in (('before',before),('after',after)):
                        result=palette.assemble([{**poses[n['name']],'parent':n['parent_id']-1} for n in hnodes],
                                                [IDENTITY]*len(hnodes))
                        receipt[label]=wrist_errors(dict(zip(hn,result['world_matrices'])),wanted)
                        maxima['palette']=max(maxima['palette'],*result['max_errors'].values())
                        totals['native_palettes']+=1
                    correction_receipt(receipt)
                sample={k:reference[index][k] for k in ('step','delta','slots')}
                sample.update(before=receipt['before'],after=receipt['after'])
                samples.append(sample)
                totals['ticks']+=1;totals['wrist_observations']+=4
                totals['raw_ticks_over_limit']+=int(max(receipt['before'].values())>LIMIT)
                for label in ('before','after'):maxima[label]=max(maxima[label],*receipt[label].values())
                if worst is None or max(receipt['before'].values())>worst['error']:
                    worst={'source':source,'target':target,'source_phase_halves':phase,
                           'error':max(receipt['before'].values()),**sample}

            if stream is None:
                for i,row in enumerate(reference):observe(i,row['delta'],row['poses'])
            else:
                result=stream.stream(names,clips,initial,steps,pose_observer=observe)
                check_receipt(result,steps,len(names))
                maxima['stream']=max(maxima['stream'],result['max_error'])
            if len(samples)!=len(reference):raise ValueError('Missing transition observations')
            sequences.append({'source':source,'target':target,'source_phase_halves':phase,
                              'steps':len(steps),'samples':samples})
            totals['sequences']+=1
        print(source+' -> '+target+' checked',file=sys.stderr,flush=True)
    return {'totals':totals,'max_errors':maxima,'worst_before':worst,'sequences':sequences,
            'raw_wrist_limit':LIMIT,'raw_wrist_limit_passed':totals['raw_ticks_over_limit']==0}


def audit(game,bank_root,suffix,profile,*,selected_cases=CASES,archives_only=False,native=False,compiled_solver=None):
    suffix_checked(suffix)
    if (not isinstance(selected_cases,(list,tuple)) or not selected_cases
            or len(set(selected_cases))!=len(selected_cases) or set(selected_cases)-set(CASES)):
        raise ValueError('Unreviewed transition case selection')
    if type(native) is not bool:raise ValueError('Invalid native transition mode')
    corrector=None
    if compiled_solver is not None:
        from native_hand_constraints import ArmSolverOracle,ComparedCorrector
        corrector=ComparedCorrector(ArmSolverOracle(compiled_solver.read_bytes()))
    stream=palette=None;library=None
    if native:
        from ls3d_animation_stream_oracle import AnimationStreamOracle
        from ls3d_palette_oracle import PaletteOracle
        library=(game/'LS3DF.dll').read_bytes();stream=AnimationStreamOracle(library);palette=PaletteOracle(library)
    hands,excluded=read_hands(game,archives_only=archives_only);cases={}
    for case in selected_cases:
        compiled=compile_bank(case);cases[case]={}
        for source in HAND_MODELS:
            rig,bank,grips=load_bank(bank_root/(case+'_'+suffix),case,source,hands[source],profile,compiled)
            result=audit_bank(hands[source],rig,bank,grips,stream=stream,palette=palette,corrector=corrector)
            cases[case][source]={'hand_sha256':digest(hands[source]),'model_sha256':digest(rig),
                                'clips':{k:digest(v[1]) for k,v in bank.items()},**result}
            print(case+' / '+source+' transitions checked',file=sys.stderr,flush=True)
    return {'schema_version':1,'scope':'private_rigid_hand_diagnostic_crossfades','runtime_status':'pending',
        'profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),'bank_suffix':suffix,'cases':cases,
        'library_sha256':digest(library) if native else None,'excluded_loose_overrides':excluded,
        'clip_playback_mode':1,'source_phases_halves':[0,1,2],'blend_weights':[0,.25,.5,.75,1],
        'blend_step_time_units':20,'source_detachment_checked':True,
        'native_stream_and_palette_executed':native,'native_subsystems_use_separate_emulators':native,
        'correction_is_offline_python':compiled_solver is None,'engine_hook_implemented':False,
        'compiled_correction':corrector.report() if corrector is not None else None,
        'client_transition_decision_executed':False,'diagnostic_orders_proven_reachable_in_client':False,
        'continuous_time_or_all_weights_proven':False,'surfaces_checked':False,'skin_or_renderer_executed':False,
        'native_loader_executed':False,'commercial_geometry_exported':False,'derived_poses_exported':False,
        'game_started':False,'game_modified':False,'engine_validated':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True);parser.add_argument('--bank-root',type=Path,required=True)
    parser.add_argument('--bank-suffix',required=True);parser.add_argument('--profile',type=Path,default=PROFILE)
    parser.add_argument('--case',choices=CASES,action='append');parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--native',action='store_true');parser.add_argument('--json-output',type=Path,required=True)
    parser.add_argument('--compiled-solver',type=Path,help='Private original compiled arm solver, compared to Python')
    args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.game,args.bank_root,args.bank_suffix,json.loads(args.profile.read_text(encoding='utf-8')),
                     selected_cases=args.case or CASES,archives_only=args.archives_only,native=args.native,
                     compiled_solver=args.compiled_solver)
        with args.json_output.open('x',encoding='utf-8') as output:json.dump(report,output,indent=2);output.write('\n')
        print(json.dumps({c:{s:{k:r[k] for k in ('totals','max_errors','raw_wrist_limit_passed')}
                             for s,r in variants.items()} for c,variants in report['cases'].items()},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Private rigid transitions refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
