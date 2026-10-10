#!/usr/bin/env python3
"""Full private rigid-hand banks through native tick, compiled relay and refresh."""
import argparse
import json
import math
from pathlib import Path
import sys

from benelli_fpv_rig_audit import read_hands,HAND_MODELS
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import CASES,compile_bank
from equipment_hand_relay import EquipmentHandRelayOracle
from five_ds import parse_5ds
from rigid_hand_transition_audit import PAIRS,schedule
from rigid_weapon_hand_audit import load_bank,suffix_checked
from unified_hand_pose_audit import retention_schedule


def summarize(rows):
    if not isinstance(rows,list) or not rows:raise ValueError('Missing complete equipment relay rows')
    total={'sequences':len(rows),'ticks':0,'native_controller_calls':0,'native_pose_calls':0,
           'adapter_calls':0,'refresh_calls':0,'corrected':0,'max_pose_error':0,'max_rotation_error':0,
           'max_wrist_before':0,'max_wrist_after':0,'uncorrected_ticks':0}
    for row in rows:
        if (row.get('complete_hand_nodes')!=37 or type(row.get('total_nodes')) is not int or not 40<=row['total_nodes']<120
                or any(type(row.get(k)) is not bool for k in ('patched','registered','controller_present'))
                or any(row.get(k) is not True for k in ('same_cpu_and_node_memory','emulated_patch_restored',
                    'native_model_frame_vector_used','context_uses_compiled_binding_directly',
                    'native_pose_data_not_reinjected_between_steps','all_records_are_diagnostic_joints'))
                or any(row.get(k) is not False for k in ('game_started','client_hook_installed','loaded_scene_qualified',
                    'source_geometry_or_poses_exported','native_scene_loading_qualified','native_palette_or_skin_executed'))
                or not isinstance(row.get('ticks'),list) or not row['ticks']):
            raise ValueError('Incomplete equipment relay receipt')
        for tick in row['ticks']:
            if type(tick.get('corrected')) is not bool:raise ValueError('Invalid correction gate')
            total['ticks']+=1;total['corrected']+=tick['corrected'];total['uncorrected_ticks']+=not tick['corrected']
            for key,limit in (('native_controller_calls',1),('native_pose_calls',128),('adapter_calls',1),('refresh_calls',1)):
                value=tick.get(key)
                if type(value) is not int or not 0<=value<=limit:raise ValueError('Invalid native relay call count')
                total[key]+=value
            calls=tick['native_controller_calls']
            if (tick['refresh_calls']!=calls or tick['adapter_calls']!=calls*row['patched']
                    or tick['corrected']!=bool(calls and row['patched'] and row['registered'])
                    or (not calls and tick['native_pose_calls']) or (not row['controller_present'] and calls)):
                raise ValueError('Native relay gates or call ordering disagree')
            for key in ('max_pose_error','max_rotation_error'):
                value=tick.get(key)
                if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=2e-6:
                    raise ValueError('Invalid complete relay numerical comparison')
                total[key]=max(total[key],value)
            if tick['corrected']:
                if tick.get('wrist_measurement_is_independent_math') is not True:raise ValueError('Missing independent wrist check')
                for key in ('before','after'):
                    values=tick.get('wrist_'+key)
                    if (not isinstance(values,dict) or set(values)!={'L','R'}
                            or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in values.values())
                            or (key=='after' and max(values.values())>5e-6)):
                        raise ValueError('Invalid full-hand wrist measurement')
                    total['max_wrist_'+key]=max(total['max_wrist_'+key],*values.values())
            elif any(key in tick for key in ('wrist_before','wrist_after','wrist_measurement_is_independent_math')):
                raise ValueError('Uncorrected frame claimed a corrected wrist measurement')
    return total


def audit(game,bank_root,suffix,profile,compiled_hook,compiled_collection,case,*,archives_only=False):
    if case not in CASES:raise ValueError('Unreviewed complete relay weapon')
    suffix_checked(suffix)
    library=(game/'LS3DF.dll').read_bytes();hook=compiled_hook.read_bytes();collection=compiled_collection.read_bytes()
    machine=EquipmentHandRelayOracle(library,hook,collection)
    hands,excluded=read_hands(game,archives_only=archives_only);compiled=compile_bank(case);variants={};all_rows=[]
    for source in HAND_MODELS:
        hand=hands[source];rig,bank,grips=load_bank(bank_root/(case+'_'+suffix),case,source,hand,profile,compiled)
        clips={k:{'data':v[1],'mode':1} for k,v in bank.items()};rows=[]
        for a,b in PAIRS:
            for phase in (0,1,2):
                steps=schedule(a,b,parse_5ds(clips[a]['data'])['frame_end'],phase)
                row=machine.run_equipment(hand,rig,clips,steps,grips)
                rows.append({'source':a,'target':b,'source_phase_halves':phase,**row})
            print(source+': '+a+' -> '+b+' collected relay checked',file=sys.stderr,flush=True)
        rows.append({'retention':True,**machine.run_equipment(hand,rig,clips,retention_schedule(),grips)})
        controls=[];steps=schedule('Idle1','Aim',parse_5ds(clips['Idle1']['data'])['frame_end'],1)
        for patched,registered,controller in ((False,True,True),(True,False,True),(True,True,False)):
            controls.append(machine.run_equipment(hand,rig,clips,steps,grips,patched=patched,
                                                  registered=registered,controller_present=controller))
        variants[source]={'hand_sha256':digest(hand),'model_sha256':digest(rig),
            'clips':{k:digest(v[1]) for k,v in bank.items()},'sequences':rows,'controls':controls,
            'totals':summarize(rows),'control_totals':summarize(controls)}
        all_rows.extend([*rows,*controls]);print(source+': retention and disabled paths checked',file=sys.stderr,flush=True)
    return {'schema_version':1,'scope':'private_complete_equipment_native_relay','case':case,'runtime_status':'pending',
        'library_sha256':digest(library),'compiled_hook_sha256':digest(hook),'compiled_collection_sha256':digest(collection),
        'profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),'excluded_loose_overrides':excluded,
        'variants':variants,'totals':summarize(all_rows),'all_records_are_diagnostic_joints':True,
        'client_transition_orders_proven_reachable':False,'live_allocation_ownership_qualified':False,
        'frame_budget_qualified':False,'native_palette_or_skin_executed':False,
        'game_started':False,'game_modified':False,'commercial_geometry_or_poses_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('game','bank-root','profile','compiled-hook','compiled-collection','json-output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--bank-suffix',required=True);parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--archives-only',action='store_true');args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Use a fresh complete relay report path')
        report=audit(args.game,args.bank_root,args.bank_suffix,json.loads(args.profile.read_text(encoding='utf-8')),
                     args.compiled_hook,args.compiled_collection,args.case,archives_only=args.archives_only)
        with args.json_output.open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
        print(json.dumps(report['totals'],indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Complete equipment hand relay refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
