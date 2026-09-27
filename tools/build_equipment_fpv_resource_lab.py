#!/usr/bin/env python3
"""Private disabled flat-FPV clips with explicit modern state associations.

One hand variant per isolated group. No weapon descriptor, central table,
commercial hand model, auto-load companion or installation is emitted.
"""
import argparse
import json
from pathlib import Path
import struct

from build_equipment_fpv_animation import compile_fpv_bank
from build_equipment_fpv_view_bank import compile_view_bank
from build_equipment_hand_animation import PROVENANCE
from build_equipment_hand_grips import RECIPE
from build_modern_equipment_assembly import ROOT,CASES
from build_modern_asset import output_directory
from build_modern_equipment_hose import digest
from build_modern_animation_bank import ALIASES
from benelli_fpv_rig_audit import HAND_MODELS,read_hands
from benelli_table_audit import read_tables,TABLE_PINS
from items_sav import parse as parse_items
from fpv_table import parse as parse_fpv
from item_native_layout import fpv_native_projection
from fpv_resource_oracle import request_plan,inspect_loaded_requests,FpvResourceOracle
from ls3d_animation_load_oracle import AnimationLoadOracle,resource_paths
from item_native_contract import SOURCE_SHA,IMAGE_SHA

# Explicit laboratory choices; NOT allocations or recovered historical IDs.
SLOTS={'F35':360,'F2':361}
STATE_CLIPS=('Idle1','Idle1','Shot','Shot','AimShot','AimShot','Rel','Jammed','Arm','Disarm','Disarm','Aim','Daim')


def chunk(kind,payload):return struct.pack('<HI',kind,6+len(payload))+payload


def group(case,variant,*,view_axes=False):
    if case not in CASES or variant not in ('H','R'):raise ValueError('Unknown equipment/hand variant')
    if type(view_axes) is not bool:raise ValueError('Invalid view-axis choice')
    states=[];bindings=[]
    for index,clip in enumerate(STATE_CLIPS):
        stem=f"PROTOTYPE_{case}{'V' if view_axes else ''}{variant}{ALIASES[clip]}"
        if len(stem)>19:raise ValueError('Animation alias exceeds modern native name bound')
        name=stem+'.I3D';resource_paths(name)
        entry=chunk(1000,name.encode('ascii')+b'\0')+struct.pack('<I',100)
        channels=chunk(3000,entry)+b''.join(chunk(i,b'') for i in (3001,3002,3003))
        states.append(chunk(2000+index,channels))
        bindings.append({'state_index':index,'state_id':2000+index,'clip':clip,'resource_name':name})
    raw=chunk(12345,chunk(SLOTS[case]+100,b''.join(states)))
    projection=fpv_native_projection(parse_fpv(raw))
    for row in bindings:
        for draw in (0,50,100):
            if request_plan(projection,SLOTS[case],row['state_index'],draw)['resource']['name']!=row['resource_name']:
                raise ValueError('Modern state association cannot select the prepared clip')
    return raw,bindings


def require_empty_sources(tables,case):
    slot=SLOTS[case];proof=[]
    for archive in ('SabreSquadron.dta','PatchX01.dta'):
        key=(archive,'tables/items.sav');raw=tables[key]
        if (len(raw),digest(raw))!=TABLE_PINS[key]:raise ValueError('Changed pinned item table')
        parsed=parse_items(raw)
        if slot>=parsed['capacity'] or parsed['slots'][slot]['present']:
            raise ValueError('Modern laboratory candidate is occupied in an archive')
        proof.append({'source':'::'.join(key),'sha256':digest(raw),'slot_empty':slot})
    key=('SabreSquadron.dta','tables/fpvanims.sav');raw=tables[key]
    if (len(raw),digest(raw))!=TABLE_PINS[key]:raise ValueError('Changed pinned FPV source')
    if any(row['id']==slot+100 for row in parse_fpv(raw)['groups']):raise ValueError('Laboratory FPV group is occupied')
    proof.append({'source':'::'.join(key),'sha256':digest(raw),'group_absent':slot+100})
    return proof


def prepare(case,variant,hands,spec,tables,table_machine,load_machine,*,view_axes=False):
    fragment,bindings=group(case,variant,view_axes=view_axes);availability=require_empty_sources(tables,case)
    hand=HAND_MODELS[0 if variant=='H' else 1]
    compiler=compile_view_bank if view_axes else compile_fpv_bank
    rig,clips,bank=compiler(case,hands[hand],spec)
    loaded=table_machine.inspect_table(fragment)
    if (loaded.get('table_sha256')!=digest(fragment)
            or loaded.get('native_nested_traversal_matches') is not True
            or loaded.get('native_strings_and_values_match') is not True):
        raise ValueError('Native fragment traversal incomplete')
    requests=inspect_loaded_requests(table_machine,fragment,SLOTS[case])
    loads={};files={f"PROTOTYPE_{case}_FPV{'View' if view_axes else ''}.4ds.disabled":rig,
        f"PROTOTYPE_{case}{'V' if view_axes else ''}{variant}.fpvgroup.disabled":fragment}
    for clip,(stem,raw) in clips.items():
        aliases={row['resource_name'] for row in bindings if row['clip']==clip}
        if aliases!={stem+'.I3D'}:raise ValueError('Association differs from emitted animation alias')
        receipt=load_machine.load(raw,stem+'.I3D')
        if (receipt.get('animation_sha256')!=digest(raw)
                or receipt.get('native_animation_open_and_relocation_executed') is not True
                or receipt.get('relocated_body_and_name_match') is not True
                or receipt.get('requested_memory_filename')!=stem+'.5ds'):
            raise ValueError('Native animation load incomplete')
        loads[clip]=receipt;files[stem+'.5ds.disabled']=raw
    return files,{'schema_version':1,'case':case,'hand_variant':variant,'provenance':PROVENANCE,
        'scope':'private_disabled_corrected_view_resource_associations' if view_axes else 'private_disabled_flat_fpv_resource_associations',
        'runtime_status':'pending','corrected_view_axes':view_axes,
        'synthetic_slot':SLOTS[case],'isolated_group':SLOTS[case]+100,
        'archive_availability_only':availability,'state_bindings':bindings,'derived_bank':bank,
        'native_fpv_fragment_traversal':loaded,'native_animation_requests':requests,'native_animation_loads':loads,
        'state_mapping_is_modern_design':True,'rel_and_jammed_are_presentation_only':True,
        'hand_variant_must_match_loaded_character_hands':True,'variants_are_mutually_exclusive':True,
        'private_only':True,'commercial_hand_models_exported':False,'auto_load_companions_created':False,
        'central_tables_emitted':False,'item_descriptor_created':False,'global_slot_reservation':False,
        'item_slot_allocated_in_game':False,'scene_or_model_loading_qualified':False,
        'camera_calibrated':False,'events_or_gameplay_implemented':False,
        'installation_allowed':False,'playable_weapon':False,'game_started':False,'game_modified':False,
        'files':{name:{'bytes':len(raw),'sha256':digest(raw)} for name,raw in files.items()}}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--hand',choices=('H','R'),required=True)
    parser.add_argument('--game',type=Path,required=True);parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--view-axes',action='store_true',help='Use the separate corrected-axis model and rebaked hand clips')
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin');parser.add_argument('--output-name')
    args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name) if args.output_name else None
        if digest((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        hands,excluded_hands=read_hands(args.game,archives_only=args.archives_only)
        tables,excluded_tables=read_tables(args.game,archives_only=args.archives_only)
        files,report=prepare(args.case,args.hand,hands,json.loads(RECIPE.read_text(encoding='utf-8')),tables,
            FpvResourceOracle(args.image.read_bytes()),AnimationLoadOracle((args.game/'LS3DF.dll').read_bytes()),
            view_axes=args.view_axes)
        report.update(source_executable_sha256=SOURCE_SHA,private_image_sha256=IMAGE_SHA,
            excluded_loose_overrides={'hands':excluded_hands,'tables':excluded_tables})
        if output:
            output.mkdir(parents=True,exist_ok=False)
            for name,raw in files.items():
                with (output/name).open('xb') as stream:stream.write(raw)
            for name,raw in files.items():
                if (output/name).read_bytes()!=raw:raise ValueError('Private output read-back mismatch')
            with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({'case':args.case,'hand':args.hand,'output':str(output) if output else None,
            'state_bindings':len(report['state_bindings']),'native_requests':len(report['native_animation_requests']),
            'native_animation_loads':len(report['native_animation_loads']),'files':len(files),
            'playable_weapon':False,'game_started':False},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Private FPV resource laboratory refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
