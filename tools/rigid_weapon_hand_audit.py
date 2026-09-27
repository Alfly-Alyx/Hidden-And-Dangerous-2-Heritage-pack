#!/usr/bin/env python3
"""Private serialized rigid-weapon hand checks, without loading a game scene.

Separate bounded native loading/time/palette checks or numeric convex-surface
checks. Neither mode establishes natural grips, camera alignment or gameplay.
"""
import argparse
import json
from pathlib import Path
import re
import sys

from animation_attach_audit import op
from animation_tick_audit import model_poses,check_receipt
from benelli_fpv_rig_audit import HAND_MODELS,HAND_PINS,read_hands
from build_equipment_fpv_animation import numeric_world
from build_equipment_hand_animation import HAND_NAMES,IDENTITY,PROVENANCE
from build_equipment_hand_grips import RECIPE,posed_hand_mesh
from build_modern_animation_bank import ALIASES
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import CASES,compile_bank,preview_meshes
from build_rigid_weapon_hand_bank import BASE_PROFILE,PROFILE,SHORT,configuration,placed_tracks,targets,stow_offset,stow_motion
from convex_contact import planes,surface_measure
from five_ds import parse_5ds
from fpv_contact_constraints import wrist_errors,correct
from hand_pose_ik import pinned_skin
from menu_gui_audit import parse_4ds_nodes
from modern_contact_cells import cells,prepare_surface,measure_surface_cells


def suffix_checked(suffix):
    if not isinstance(suffix,str) or not re.fullmatch(r'HandFPV_v[1-9][0-9]*',suffix):
        raise ValueError('Invalid rigid hand bank suffix')
    return suffix


def load_bank(directory,case,source,hand_raw,profile,compiled):
    if case not in CASES or source not in HAND_MODELS:raise ValueError('Unreviewed rigid hand bank')
    if (len(hand_raw),digest(hand_raw))!=HAND_PINS[source][1:]:raise ValueError('Changed source hand')
    base=json.loads(BASE_PROFILE.read_text(encoding='utf-8'));spec=json.loads(RECIPE.read_text(encoding='utf-8'))
    grips,thumb,translation,expected=configuration(profile,base,spec,case)
    manifest=json.loads((directory/'MANIFEST.json').read_text(encoding='utf-8'))
    if (manifest.get('private_only') is not True or manifest.get('runtime_status')!='pending'
            or manifest.get('case')!=case or manifest.get('provenance')!=PROVENANCE
            or manifest.get('profile_sha256')!=digest(json.dumps(profile,sort_keys=True).encode())):
        raise ValueError('Unreviewed rigid hand manifest')
    row=manifest['variants'][source];rig=(directory/f'PROTOTYPE_{SHORT[case]}_HandFPV.4ds.disabled').read_bytes()
    if (rig!=compiled[1] or digest(rig)!=expected or row['model_sha256']!=expected
            or row['hand_source']!=source or row['hand_sha256']!=digest(hand_raw)
            or row['grips']!=grips or row['thumb']!=thumb or row['translation']!=translation
            or row.get('stow_offset',[0,0,0])!=stow_offset(profile,case)
            or row.get('stow_motion')!=stow_motion(profile,case)
            or set(row['clips'])!=set(ALIASES)):
        raise ValueError('Changed rigid hand build inputs')
    gear_names,_=model_poses(rig);variant='H' if source==HAND_MODELS[0] else 'R';clips={}
    for name,description in row['clips'].items():
        stem=f'PROTOTYPE_{SHORT[case]}P{variant}{ALIASES[name]}'
        if description['stem']!=stem:raise ValueError('Unexpected rigid hand clip path')
        raw=(directory/(stem+'.5ds.disabled')).read_bytes();original=compiled[2][name][1]
        parsed=parse_5ds(raw)
        if (digest(raw)!=description['sha256'] or description['source_clip_sha256']!=digest(original)
                or parsed['frame_end']!=parse_5ds(original)['frame_end'] or len(raw)-18>0xf000
                or {t['name'] for t in parsed['tracks']}!=HAND_NAMES|set(gear_names)):
            raise ValueError('Changed rigid hand clip or target set')
        expected_gear={t['name']:t['channels'] for t in placed_tracks(original,translation,
            stow=stow_offset(profile,case),clip_name=name,motion_spec=stow_motion(profile,case))}
        actual_gear={t['name']:t['channels'] for t in parsed['tracks'] if t['name'] not in HAND_NAMES}
        if expected_gear!=actual_gear:raise ValueError('Rigid hand bank changed equipment channels')
        clips[name]=(stem,raw)
    return rig,clips,grips


def surface(hand_raw,rig,clip,time,parts):
    _,skin=pinned_skin(hand_raw);names,seeds=model_poses(hand_raw)
    parsed=parse_5ds(clip)
    if type(time) is not int or not 0<=time<=parsed['frame_end']*40:raise ValueError('Invalid surface sample time')
    tracks={t['name']:t['channels'] for t in parsed['tracks']}
    _,poses=numeric_world(skin['nodes'],dict(zip(names,seeds)),tracks,time)
    hand=posed_hand_mesh(hand_raw,poses,1);prepared=prepare_surface(hand.points,hand.triangles);checked={};unchecked={}
    for mesh in preview_meshes(rig,clip,time):
        if mesh.name in checked or mesh.name in unchecked:raise ValueError('Ambiguous rigid surface piece')
        try:volumes=cells(mesh,parts)
        except ValueError as error:
            unchecked[mesh.name]=str(error);continue
        measurement=measure_surface_cells(prepared,volumes)
        checked[mesh.name]={'convex_cells':len(volumes),'internal_cell_seams_are_not_contact_surfaces':True,
            'penetrating_triangles':measurement['penetrating_triangle_cells'],
            'triangle_count_may_repeat_across_cells':len(volumes)>1,
            'max_depth_lower_bound':measurement['max_cell_boundary_depth'],
            'broad_phase_candidate_triangle_cells':measurement['broad_phase_candidate_triangle_cells'],
            'all_input_triangle_cells':measurement['all_input_triangle_cells'],
            'depth_is_cell_boundary_plane_metric_not_global_nonconvex_distance':len(volumes)>1,
            'penetration_tolerance':1e-5,'inset_area_cutoff':1e-14,'depth_search_resolution':1e-7}
    return {'pieces':checked,'unchecked_pieces':unchecked,
        'penetrating_triangles_sum_over_pieces':sum(r['penetrating_triangles'] for r in checked.values()),
        'max_depth_lower_bound':max((r['max_depth_lower_bound'] for r in checked.values()),default=0)}


def audit(game,bank_root,suffix,profile,*,native=False,dense=False,archives_only=False,selected_cases=CASES):
    suffix_checked(suffix)
    if (not isinstance(selected_cases,(tuple,list)) or not selected_cases or len(set(selected_cases))!=len(selected_cases)
            or set(selected_cases)-set(CASES)):raise ValueError('Unreviewed rigid hand case selection')
    if native and dense:raise ValueError('Native mode is already dense; --dense is for surfaces')
    hands,excluded=read_hands(game,archives_only=archives_only)
    totals=dict(loads=0,sequences=0,ticks=0,wrist_targets=0,native_hand_palettes=0,surface_samples=0,
                raw_half_key_ticks_over_limit=0,offline_corrected_poses=0)
    errors=dict(tick=0,palette=0,wrist_at_keys=0,wrist_between_keys=0,wrist_after_offline_correction=0)
    if native:
        from ls3d_animation_load_oracle import AnimationLoadOracle
        from ls3d_palette_oracle import PaletteOracle
        from ls3d_tick_oracle import TickOracle
        library=(game/'LS3DF.dll').read_bytes()
        loader,tick,palette=AnimationLoadOracle(library),TickOracle(library),PaletteOracle(library)
    reports={}
    for case in selected_cases:
        compiled=compile_bank(case);reports[case]={}
        for source in HAND_MODELS:
            rig,clips,grips=load_bank(bank_root/(case+'_'+suffix),case,source,hands[source],profile,compiled)
            hn,hi=model_poses(hands[source]);gn,gi=model_poses(rig);names,seeds=hn+gn,hi+gi
            hnodes=parse_4ds_nodes(hands[source])['nodes'];gnodes=parse_4ds_nodes(rig)['nodes'];rows={}
            for name,(stem,raw) in clips.items():
                end=parse_5ds(raw)['frame_end'];row={'sha256':digest(raw),'frame_end':end}
                if native:
                    receipt=loader.load(raw,stem+'.I3D')
                    if (receipt.get('animation_sha256')!=digest(raw)
                            or receipt.get('native_animation_open_and_relocation_executed') is not True
                            or receipt.get('relocated_body_and_name_match') is not True
                            or receipt.get('requested_memory_filename')!=stem+'.5ds'):
                        raise ValueError('Incomplete native rigid hand load')
                    totals['loads']+=1;elapsed=0
                    gear=[t for t in parse_5ds(raw)['tracks'] if t['name'] not in HAND_NAMES]
                    per_clip={'wrist_at_keys':0,'wrist_between_keys':0,'wrist_after_offline_correction':0}
                    exceeded=[]

                    def observe(index,delta,values):
                        nonlocal elapsed
                        elapsed+=delta;poses=dict(zip(names,values));time=min(elapsed,end*40)
                        if len(values)!=len(names) or poses['a']!=hi[hn.index('a')]:
                            raise ValueError('Incomplete hand observation or moved root')
                        for n,seed in zip(hn,hi):
                            if any(poses[n][k]!=seed[k] for k in ('position','scale')):
                                raise ValueError('Rigid native clip moved or stretched a hand joint')
                        wanted=targets(rig,gear,time,grips,clip_name=name)
                        result=palette.assemble([{**poses[n['name']],'parent':n['parent_id']-1} for n in hnodes],
                                                [IDENTITY]*len(hnodes))
                        actual=wrist_errors(dict(zip(hn,result['world_matrices'])),wanted)
                        key='wrist_at_keys' if time%40==0 else 'wrist_between_keys'
                        if key=='wrist_at_keys' and max(actual.values())>5e-6:
                            raise ValueError(f'Rigid hand drift: {case}/{source}/{name}/{time}: {actual}')
                        if key=='wrist_between_keys' and max(actual.values())>.0002:
                            totals['raw_half_key_ticks_over_limit']+=1
                            exceeded.append({'time':time,'wrist_errors':actual})
                        errors[key]=max(errors[key],*actual.values());per_clip[key]=max(per_clip[key],*actual.values())
                        errors['palette']=max(errors['palette'],*result['max_errors'].values())
                        corrected,description=correct(hands[source],gnodes,poses,grips,root_name='fpv_weapon',
                                                      preserve_observed_elbow_plane=True)
                        fixed=palette.assemble([{**corrected[n['name']],'parent':n['parent_id']-1} for n in hnodes],
                                               [IDENTITY]*len(hnodes))
                        after=wrist_errors(dict(zip(hn,fixed['world_matrices'])),wanted)
                        if max(after.values())>5e-6:raise ValueError('Offline rigid hand correction missed native target')
                        errors['wrist_after_offline_correction']=max(errors['wrist_after_offline_correction'],*after.values())
                        per_clip['wrist_after_offline_correction']=max(per_clip['wrist_after_offline_correction'],*after.values())
                        errors['palette']=max(errors['palette'],*fixed['max_errors'].values())
                        totals['ticks']+=1;totals['wrist_targets']+=4;totals['native_hand_palettes']+=2
                        totals['offline_corrected_poses']+=1

                    deltas=[0]+[20]*(2*end)+[0,20];native_clips={name:{'data':raw,'mode':1}};operations=[op(name,7)]
                    result=tick.sequence_with_ticks(names,native_clips,operations,seeds,deltas,pose_observer=observe)
                    check_receipt(result,names,native_clips,operations,seeds,deltas,9)
                    errors['tick']=max(errors['tick'],result['max_error']);totals['sequences']+=1
                    row.update(load=receipt,ticks=len(deltas),max_errors=per_clip,raw_half_key_exceedances=exceeded)
                else:
                    times=range(0,end*40+1,20) if dense else sorted({0,end*20,end*40})
                    row['samples']=[{'time':t,**surface(hands[source],rig,raw,t,compiled[0]['parts'])} for t in times]
                    totals['surface_samples']+=len(row['samples'])
                rows[name]=row
                print(case,source,name,'native' if native else 'surface','checked',file=sys.stderr,flush=True)
            reports[case][source]={'hand_sha256':digest(hands[source]),'model_sha256':digest(rig),'clips':rows}
    return {'schema_version':1,'scope':'private_rigid_weapon_hand_audit','provenance':PROVENANCE,
        'runtime_status':'pending','bank_suffix':suffix,'profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),
        'mode':'native' if native else 'surface','dense_keys_and_half_keys':native or dense,'selected_cases':list(selected_cases),
        'library_sha256':digest(library) if native else None,'cases':reports,'totals':totals,'max_errors':errors,
        'excluded_loose_overrides':excluded,'equipment_matches_explicit_modern_profile':True,
        'non_root_equipment_channels_preserved':True,
        'equipment_channels_preserved':all(stow_motion(profile,c) is None for c in selected_cases),
        'stow_motion':{c:stow_motion(profile,c) for c in selected_cases},
        'native_loading_time_pose_palette_executed':native,'native_subsystems_use_separate_emulators':native,
        'identity_hand_root_is_diagnostic_joint':native,'equipment_world_uses_numeric_reference':True,
        'convex_surface_crossings_checked':not native,'native_skin_executed':False,
        'raw_half_key_wrist_limit':.0002,'raw_half_key_wrist_limit_passed':totals['raw_half_key_ticks_over_limit']==0 if native else None,
        'offline_six_arm_rotation_correction_verified':native,'corrected_poses_written_to_bank':False,
        'offline_correction_preserves_observed_elbow_plane':native,
        'decomposed_surface_counts_may_repeat_triangles_and_depth_is_cell_local':not native,
        'renderer_or_model_clone_executed':False,'commercial_geometry_exported':False,
        'original_animation_keys_read':False,'source_geometry_modified':False,
        'finger_contact_qualified':False,'hand_self_intersection_checked':False,
        'reload_hand_gestures_implemented':False,'post_blend_constraint_hook_implemented':False,
        'camera_calibrated':False,'game_started':False,'game_modified':False,'engine_validated':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True);parser.add_argument('--bank-root',type=Path,required=True)
    parser.add_argument('--bank-suffix',required=True);parser.add_argument('--profile',type=Path,default=PROFILE)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--native',action='store_true')
    parser.add_argument('--dense',action='store_true');parser.add_argument('--json-output',type=Path,required=True)
    parser.add_argument('--case',choices=CASES,action='append')
    args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.game,args.bank_root,args.bank_suffix,json.loads(args.profile.read_text(encoding='utf-8')),
                     native=args.native,dense=args.dense,archives_only=args.archives_only,selected_cases=args.case or CASES)
        with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Private rigid hand audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
