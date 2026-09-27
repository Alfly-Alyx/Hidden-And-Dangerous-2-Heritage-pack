#!/usr/bin/env python3
"""Native loading and dense pose/palette checks of private fitted hand banks.

Separate bounded emulators; no source geometry export, scene clone, skin,
renderer, callback or game. Surface contact is a distinct audit.
"""
import argparse
import json
from pathlib import Path
import re
import sys

from animation_attach_audit import op
from animation_tick_audit import model_poses, check_receipt
from benelli_fpv_rig_audit import HAND_MODELS, read_hands
from build_equipment_hand_animation import HAND_NAMES, IDENTITY
from build_equipment_hand_grips import RECIPE
from build_fitted_fpv_bank import fitted_grips
from build_modern_animation_bank import ALIASES
from build_modern_equipment_hose import digest
from fitted_grip_surface_audit import fitted
from five_ds import parse_5ds
from fpv_contact_constraints import world, targets, wrist_errors
from fpv_transition_contact_audit import load_bank
from ls3d_animation_load_oracle import AnimationLoadOracle
from ls3d_math_oracle import DLL_SHA
from ls3d_palette_oracle import PaletteOracle
from ls3d_tick_oracle import TickOracle
from menu_gui_audit import parse_4ds_nodes


def audit(game,bank_root,bank_suffix,fitting,archives_only=False):
    if not re.fullmatch(r'FittedGrips_v[1-9][0-9]*',bank_suffix):raise ValueError('Invalid fitted bank suffix')
    library=(game/'LS3DF.dll').read_bytes()
    loader,tick,palette=AnimationLoadOracle(library),TickOracle(library),PaletteOracle(library)
    hands,excluded=read_hands(game,archives_only=archives_only)
    spec=json.loads(RECIPE.read_text(encoding='utf-8'));reports={}
    totals=dict(loads=0,sequences=0,ticks=0,wrist_targets=0,native_hand_palettes=0)
    errors=dict(tick=0,palette=0,wrist_at_keys=0,wrist_between_keys=0)
    for case in ('F35','F2'):
        grips,thumb=fitted_grips(fitting,spec,case);reports[case]={}
        directory=bank_root/(case+'_'+bank_suffix)
        manifest=json.loads((directory/'MANIFEST.json').read_text(encoding='utf-8'))
        for source in HAND_MODELS:
            rig,clips=fitted(directory,case,source,hands[source])
            _,old=load_bank(bank_root/(case+'_CorrectedFPV_v1'),case,source,hands[source])
            if manifest['variants'][source]['grips']!=grips or manifest['variants'][source]['thumb']!=thumb:
                raise ValueError('Native audit fitting inputs differ from the emitted bank')
            hn,hi=model_poses(hands[source]);gn,gi=model_poses(rig)
            names,initial=hn+gn,hi+gi
            hnodes=parse_4ds_nodes(hands[source])['nodes'];gnodes=parse_4ds_nodes(rig)['nodes']
            if len(set(names))!=len(names):raise ValueError('Ambiguous fitted targets')
            clip_reports={}
            for name,raw in clips.items():
                parsed=parse_5ds(raw);end=parsed['frame_end']
                gear={t['name']:t['channels'] for t in parsed['tracks'] if t['name'] not in HAND_NAMES}
                old_gear={t['name']:t['channels'] for t in parse_5ds(old[name]['data'])['tracks'] if t['name'] not in HAND_NAMES}
                if gear!=old_gear:raise ValueError('Fitted bank changed previously audited equipment motion')
                variant='H' if source==HAND_MODELS[0] else 'R'
                receipt=loader.load(raw,f'PROTOTYPE_{case}G{variant}{ALIASES[name]}.I3D')
                totals['loads']+=1
                elapsed=0

                def observe(index,delta,values):
                    nonlocal elapsed
                    elapsed+=delta
                    poses=dict(zip(names,values))
                    if len(values)!=len(names) or poses['a']!=hi[hn.index('a')]:
                        raise ValueError('Incomplete fitted pose or moved hand root')
                    for n,seed in zip(hn,hi):
                        if any(poses[n][key]!=seed[key] for key in ('position','scale')):
                            raise ValueError('Fitted native clip moved or stretched a hand joint')
                    wanted=targets(world(gnodes,poses),grips)
                    result=palette.assemble([{**poses[n['name']],'parent':n['parent_id']-1} for n in hnodes],
                                             [IDENTITY]*len(hnodes))
                    actual=wrist_errors(dict(zip(hn,result['world_matrices'])),wanted)
                    key='wrist_at_keys' if min(elapsed,end*40)%40==0 else 'wrist_between_keys'
                    if max(actual.values())>(5e-6 if key=='wrist_at_keys' else .0002):
                        raise ValueError(f'Fitted wrist drift: {case}/{source}/{name}/{elapsed}: {actual}')
                    errors[key]=max(errors[key],*actual.values())
                    errors['palette']=max(errors['palette'],*result['max_errors'].values())
                    totals['ticks']+=1;totals['wrist_targets']+=2;totals['native_hand_palettes']+=1

                deltas=[0]+[20]*(2*end)+[0,20]
                native_clips={name:{'data':raw,'mode':1}};operations=[op(name,7)]
                result=tick.sequence_with_ticks(names,native_clips,operations,initial,deltas,pose_observer=observe)
                check_receipt(result,names,native_clips,operations,initial,deltas,9)
                errors['tick']=max(errors['tick'],result['max_error']);totals['sequences']+=1
                clip_reports[name]={'sha256':digest(raw),'frame_end':end,'ticks':len(deltas),'load':receipt}
                print(case,source,name,'native fitted poses checked',file=sys.stderr,flush=True)
            reports[case][source]={'hand_sha256':digest(hands[source]),'model_sha256':digest(rig),'clips':clip_reports}
    return {'schema_version':1,'scope':'private_native_fitted_hand_clips','runtime_status':'pending',
        'library_sha256':DLL_SHA,'bank_suffix':bank_suffix,'cases':reports,'totals':totals,'max_errors':errors,
        'fitting_report_sha256':digest(json.dumps(fitting,sort_keys=True).encode()),
        'excluded_loose_overrides':excluded,'equipment_channels_preserved':True,
        'source_hand_root_positions_scales_preserved':True,'native_loading_time_pose_palette_executed':True,
        'native_subsystems_use_separate_emulators':True,'identity_hand_root_is_diagnostic_joint':True,
        'equipment_world_uses_numeric_reference':True,'skin_executed':False,'renderer_executed':False,
        'surface_contact_qualified':False,'post_blend_constraint_hook_implemented':False,
        'original_animation_keys_read':False,'commercial_geometry_exported':False,
        'camera_calibrated':False,'game_started':False,'game_modified':False,'engine_validated':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--bank-root',required=True,type=Path)
    parser.add_argument('--bank-suffix',required=True)
    parser.add_argument('--fitting',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        fitting=json.loads(args.fitting.read_text(encoding='utf-8'))
        report=audit(args.game,args.bank_root,args.bank_suffix,fitting,args.archives_only)
        with args.json_output.open('x',encoding='utf-8') as output:
            json.dump(report,output,indent=2);output.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native fitted bank audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
