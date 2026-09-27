#!/usr/bin/env python3
"""Private disabled resource associations for verified rigid-hand banks.

Synthetic slots are checked against pinned archives, never globally allocated.
No central tables, item descriptors, commercial models or game files are written.
"""
import argparse
import json
from pathlib import Path
import struct

from benelli_fpv_rig_audit import HAND_MODELS,read_hands
from benelli_table_audit import read_tables
from build_equipment_fpv_resource_lab import chunk,require_empty_slot,STATE_CLIPS
from build_equipment_hand_animation import PROVENANCE
from build_modern_asset import ROOT,output_directory
from build_modern_animation_bank import ALIASES
from build_modern_equipment_hose import digest
from build_rigid_weapon_fpv_bank import CASES,compile_bank
from build_rigid_weapon_hand_bank import PROFILE,SHORT
from fpv_resource_oracle import request_plan,inspect_loaded_requests,FpvResourceOracle
from fpv_table import parse as parse_fpv
from item_native_contract import SOURCE_SHA,IMAGE_SHA
from item_native_layout import fpv_native_projection
from ls3d_animation_load_oracle import AnimationLoadOracle,resource_paths
from rigid_weapon_hand_audit import load_bank

SLOTS={'FG42':362,'MG34':363,'ZK383':364}


def group(case,variant):
    if case not in CASES or variant not in ('H','R'):raise ValueError('Unknown rigid weapon/hand variant')
    states=[];bindings=[]
    for index,clip in enumerate(STATE_CLIPS):
        stem=f'PROTOTYPE_{SHORT[case]}P{variant}{ALIASES[clip]}'
        if len(stem)>19:raise ValueError('Rigid hand alias too long')
        name=stem+'.I3D';resource_paths(name)
        entry=chunk(1000,name.encode('ascii')+b'\0')+struct.pack('<I',100)
        states.append(chunk(2000+index,chunk(3000,entry)+b''.join(chunk(i,b'') for i in (3001,3002,3003))))
        bindings.append({'state_index':index,'state_id':2000+index,'clip':clip,'resource_name':name})
    raw=chunk(12345,chunk(SLOTS[case]+100,b''.join(states)))
    projection=fpv_native_projection(parse_fpv(raw))
    for row in bindings:
        for draw in (0,50,100):
            if request_plan(projection,SLOTS[case],row['state_index'],draw)['resource']['name']!=row['resource_name']:
                raise ValueError('Rigid resource association mismatch')
    return raw,bindings


def prepare(case,variant,hand_raw,bank,profile,tables,table_machine,loader):
    fragment,bindings=group(case,variant);availability=require_empty_slot(tables,SLOTS[case])
    source=HAND_MODELS[0 if variant=='H' else 1]
    compiled=compile_bank(case);rig,clips,grips=load_bank(bank,case,source,hand_raw,profile,compiled)
    traversal=table_machine.inspect_table(fragment)
    if (traversal.get('table_sha256')!=digest(fragment) or traversal.get('native_nested_traversal_matches') is not True
            or traversal.get('native_strings_and_values_match') is not True):raise ValueError('Incomplete native resource traversal')
    requests=inspect_loaded_requests(table_machine,fragment,SLOTS[case])
    files={f'PROTOTYPE_{SHORT[case]}_HandFPV.4ds.disabled':rig,
           f'PROTOTYPE_{SHORT[case]}P{variant}.fpvgroup.disabled':fragment};loads={}
    for name,(stem,raw) in clips.items():
        if {r['resource_name'] for r in bindings if r['clip']==name}!={stem+'.I3D'}:
            raise ValueError('Rigid association differs from serialized clip')
        receipt=loader.load(raw,stem+'.I3D')
        if (receipt.get('animation_sha256')!=digest(raw)
                or receipt.get('native_animation_open_and_relocation_executed') is not True
                or receipt.get('relocated_body_and_name_match') is not True
                or receipt.get('requested_memory_filename')!=stem+'.5ds'):
            raise ValueError('Incomplete native rigid hand animation loading')
        files[stem+'.5ds.disabled']=raw;loads[name]=receipt
    return files,{'schema_version':1,'case':case,'hand_variant':variant,'provenance':PROVENANCE,
        'runtime_status':'pending','scope':'private_disabled_rigid_hand_resource_associations',
        'synthetic_slot':SLOTS[case],'isolated_group':SLOTS[case]+100,'archive_availability_only':availability,
        'profile_sha256':digest(json.dumps(profile,sort_keys=True).encode()),'source_hand_sha256':digest(hand_raw),
        'modern_model_sha256':digest(rig),'state_bindings':bindings,'native_fpv_fragment_traversal':traversal,
        'native_animation_requests':requests,'native_animation_loads':loads,
        'state_mapping_is_modern_design':True,'reload_and_jammed_are_presentation_only':True,
        'hand_variant_must_match_loaded_character_hands':True,'variants_are_mutually_exclusive':True,
        'private_only':True,'commercial_hand_models_exported':False,'auto_load_companions_created':False,
        'global_slot_reservation':False,'central_tables_emitted':False,'item_descriptor_created':False,
        'item_slot_allocated_in_game':False,'scene_or_model_loading_qualified':False,
        'post_blend_constraint_hook_implemented':False,'finger_contact_qualified':False,
        'camera_calibrated':False,'events_or_gameplay_implemented':False,'installation_allowed':False,
        'playable_weapon':False,'game_started':False,'game_modified':False,
        'files':{name:{'bytes':len(raw),'sha256':digest(raw)} for name,raw in files.items()}}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--hand',choices=('H','R'),required=True);parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--bank',type=Path,required=True)
    parser.add_argument('--profile',type=Path,default=PROFILE);parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name)
        if output.exists():raise ValueError('Output exists; use a fresh name')
        if digest((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        hands,excluded_hands=read_hands(args.game,archives_only=args.archives_only)
        tables,excluded_tables=read_tables(args.game,archives_only=args.archives_only)
        source=HAND_MODELS[0 if args.hand=='H' else 1]
        files,report=prepare(args.case,args.hand,hands[source],args.bank,json.loads(args.profile.read_text(encoding='utf-8')),
            tables,FpvResourceOracle(args.image.read_bytes()),AnimationLoadOracle((args.game/'LS3DF.dll').read_bytes()))
        report.update(source_executable_sha256=SOURCE_SHA,private_image_sha256=IMAGE_SHA,
            excluded_loose_overrides={'hands':excluded_hands,'tables':excluded_tables})
        output.mkdir(parents=True,exist_ok=False)
        for name,raw in files.items():
            with (output/name).open('xb') as stream:stream.write(raw)
        for name,raw in files.items():
            if (output/name).read_bytes()!=raw:raise ValueError('Rigid resource output readback mismatch')
        with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({'case':args.case,'hand':args.hand,'files':len(files)+1,'native_requests':len(report['native_animation_requests']),
                          'native_animation_loads':len(report['native_animation_loads']),'playable_weapon':False}));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Private rigid FPV resource lab refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
