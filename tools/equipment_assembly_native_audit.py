#!/usr/bin/env python3
"""Combined original rig: native attached ticks -> observed poses -> palette/skin.

Held and hose tracks run in the SAME native controller memory; matrices and
skin use separate bounded emulators. No game callbacks, loader or renderer.
"""
import argparse
import json
from pathlib import Path
import sys

from build_modern_equipment_assembly import inputs,compile_assembly,CASES
from build_modern_equipment_hose import compile_hose_bank
from animation_tick_audit import model_poses,bank_cases,audit_cases,check_receipt
from animation_attach_audit import op
from four_ds_skin import read_reviewed
from ls3d_tick_oracle import TickOracle
from ls3d_palette_oracle import PaletteOracle
from ls3d_skin_oracle import SkinOracle,transformed
from ls3d_palette_audit import check_receipt as check_palette
from ls3d_skin_audit import check_receipt as check_skin
from ls3d_math_oracle import DLL_SHA


def audit(library,progress=None):
    tick=TickOracle(library);palette=PaletteOracle(library);skin_machine=SkinOracle(library)
    cases={};identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
    totals=dict.fromkeys(('dense_sequences','observed_ticks','observed_node_poses','lod_evaluations','vertices','endpoint_vertices'),0)
    errors=dict.fromkeys(('tick','palette','skin','fixed_pack_endpoint','held_endpoint'),0)
    for case in CASES:
        args=inputs(case);rig,clips,build=compile_assembly(*args)
        names,initial=model_poses(rig);index={name:i for i,name in enumerate(names)}
        raw_clips={key:value[1] for key,value in clips.items()}
        boundaries=audit_cases(tick,bank_cases(names,raw_clips,initial));errors['tick']=max(errors['tick'],boundaries['max_error'])
        hose_raw,_,_,hose_report=compile_hose_bank(*args)
        skins=[read_reviewed(hose_raw,allow_multiple_lods=True,lod=i) for i in (0,1)]
        hose_map=build['source_index_maps']['hose'];held_root=build['source_index_maps']['held'][1]-1
        bone_indices=[hose_map[node]-1 for node in skins[0]['joint_node_indices']]
        static=set(range(len(names)))-{index['MOD_held_pivot'],*bone_indices}
        # The held root's constant authored origin is equal to its loaded seed.
        def observe(_step,_delta,poses):
            if len(poses)!=len(names):raise ValueError('Incomplete observed assembly pose')
            for i in static:
                if poses[i]!=initial[i]:raise ValueError('Fixed assembly component moved')
            joints=[{**poses[i],'parent':-1} for i in bone_indices]
            native=palette.assemble(joints,skins[0]['inverse_binds']);check_palette(native,len(joints))
            # A diagnostic two-joint hierarchy evaluates the actual held root
            # translation + held pivot. It is not a native rendered model.
            held=palette.assemble([{**poses[held_root],'parent':-1},
                                  {**poses[index['MOD_held_pivot']],'parent':0}],[identity,identity])
            check_palette(held,2)
            errors['palette']=max(errors['palette'],*native['max_errors'].values(),*held['max_errors'].values())
            for source in skins:
                row=skin_machine.deform(source['vertices'],source['pairs'],native['palette'],source['parents'])
                check_skin(row,len(source['vertices']));errors['skin']=max(errors['skin'],row['max_error'])
                for vertex,(bone,_),actual in zip(source['vertices'],source['pairs'],row['values']):
                    weight=hose_report['influence_weights'][bone-1]
                    if weight not in (0,1):continue
                    if weight==0:expected=vertex[:3];key='fixed_pack_endpoint'
                    else:
                        local=[a-b for a,b in zip(vertex[:3],build['component_origins']['held'])]
                        expected=transformed(local,held['palette'][1]);key='held_endpoint'
                    error=max(abs(a-b) for a,b in zip(actual[:3],expected));errors[key]=max(errors[key],error)
                    if error>2e-6:raise ValueError('Observed native assembly endpoint diverged')
                    totals['endpoint_vertices']+=1
                totals['lod_evaluations']+=1;totals['vertices']+=row['vertices']
            totals['observed_ticks']+=1;totals['observed_node_poses']+=len(poses)
        sequence_reports={}
        for name,(_,raw) in clips.items():
            end=build['clips'][name]['frame_end'];deltas=[0]+[20]*(end*2)+[0,20]
            bank={name:{'data':raw,'mode':1}};operations=[op(name,7)]
            row=tick.sequence_with_ticks(names,bank,operations,initial,deltas,pose_observer=observe)
            check_receipt(row,names,bank,operations,initial,deltas,9)
            errors['tick']=max(errors['tick'],row['max_error']);totals['dense_sequences']+=1
            sequence_reports[name]={'observed_ticks':len(deltas),'frame_end':end,'explicit_playback_mode':1}
            if progress:progress(case,name,len(deltas))
        cases[case]={'rig_sha256':build['rig_sha256'],'node_count':len(names),'boundary_and_overlap_cases':boundaries,
                     'persistent_sequences':sequence_reports}
    return {'schema_version':1,'scope':'combined_original_rig_same_native_controller_then_separate_palette_skin',
        'library_sha256':DLL_SHA,'cases':cases,'totals':totals,'max_errors':errors,
        'held_and_hose_share_clip_slot_time_and_pose_memory':True,'poses_observed_from_native_memory':True,
        'poses_persist_across_ticks':True,'both_lods_checked':True,'unanimated_nodes_preserved':True,
        'initial_pose_is_explicit_seed':True,'palette_and_skin_use_separate_emulators':True,
        'held_matrix_uses_diagnostic_two_joint_hierarchy':True,'allocator_is_bounded_double':True,
        'observer_is_python_diagnostic_not_native_callback':True,'commercial_geometry_or_keys_used':False,
        'native_loader_executed':False,'callbacks_events_renderer_called':False,'player_attachment_qualified':False,
        'runtime_clip_changes_executed':False,'loaded_scene_qualified':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',required=True,type=Path);parser.add_argument('--json-output',type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.library.read_bytes(),lambda case,name,count:
            print(f'Checked persistent visual assembly: {case} / {name} / {count}',file=sys.stderr,flush=True))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native modern assembly audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
