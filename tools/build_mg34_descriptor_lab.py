#!/usr/bin/env python3
"""PRIVATE disabled portable MG34 assembly; never a game table or installer.

Historical shoot row/audio/icon/ammunition are explicitly distinguished from
modern category choices, geometry and derived hand animations. Neither the
helmet at slot 32 nor TANK MG34/ammo 211 is replaced, borrowed or renamed.
"""
import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import struct
import sys
import wave

from audit_audio_resources import pcm_metadata
from benelli_table_audit import read_tables,TABLE_PINS
from build_benelli_descriptor_lab import output_directory
from build_modern_asset import ROOT,build_meshes,encode_4ds
from build_modern_equipment_hose import digest
from build_rigid_weapon_resource_lab import prepare as prepare_resources,SLOTS
from dta_archive import DtaArchive
from item_native_layout import decode_record
from item_weapon_descriptor import build_weapon,RAW_BASE,RAW_WEAPON
from items_sav import parse as parse_items,text_field
from item_editor_table import require_row
from item_sound_audit import editor_references
from sound_definition import parse as parse_sounds

SLOT=SLOTS['MG34']
PROFILE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/modern-rigid-hand-grips-mg34-linear.json'
ARCHIVES=('models.dta','Maps.dta','Sounds.dta','others.DTA','LangEnglish.dta','Patch.dta','SabreSquadron.dta','PatchX01.dta')
SOURCE_PINS={
    'maps/wi_ge-mg34.bmp':('Maps.dta',3128,'9d101281f23e575eabd0a903812dced69bf20ed1cc46a1575bb1b38bef7276ef'),
    'sounds/mg34_r.wav':('Sounds.dta',152876,'121188b694db91d829a84fd57ad0290b6a3ad812912c99a49362555bc71a7c25'),
    'sounds/f_mg34_a.wav':('Sounds.dta',48238,'ca56fb3a2aac19aa5c0fa07d6f8cd3a7a05b51658990f686a4b6ddd048675500'),
    'tables/ingamesounds.def':('Patch.dta',104700,'ab374c805b6bc663593bfd788f9e437b6998ffe8a3d02e83a393aa201dfd94f3')}
BASELINE_SHA='f3f34fd2d68efb6caa515fb65007a2c9e84ec1837056a67c68bef6627c66e1fe'
SHOOT_ROW_SHA='d577c7866fa84d9deb9f69765657d87f51278852e3d4fbfb9c09f0f9869abbb2'
WORLD_PIN=(260160,'d45597f0c720991a468fe8064c5ee972efeb884dc1be6acef45bb06dfc924dac')
FPV_PIN='9cc238c77e9a1a38f844977f417e802118026258a27f40103af9d680b076e672'
PENDING=('additive_central_table_transaction','global_item_and_resource_collision_clearance',
    'inventory_text_rendering_and_font_tests','shoot_and_secondary_semantics_and_balance',
    'raw_animation_contacts_and_reload_hand_gestures','post_blend_constraint_engine_hook',
    'scene_model_loading_and_clone','camera_alignment','reload_and_sound_event_timing',
    'character_animations_and_ai','complete_save_compatibility','network_and_live_gameplay')


def read_sources(game,*,archives_only=False):
    data={};excluded={}
    with ExitStack() as stack:
        effective={}
        for name in ARCHIVES:
            path=game/name
            if name=='PatchX01.dta' and not path.exists():continue
            archive=stack.enter_context(DtaArchive(path));seen=set()
            for entry in archive.entries:
                resource=entry.name.replace('\\','/').casefold()
                if resource not in SOURCE_PINS:continue
                if resource in seen:raise ValueError('Ambiguous MG34 source')
                seen.add(resource);effective[resource]=(name,archive,entry)
        for resource,pin in SOURCE_PINS.items():
            if resource not in effective:raise ValueError('Missing MG34 resource: '+resource)
            name,archive,entry=effective[resource];raw=archive.read(entry)
            if (name,len(raw),digest(raw))!=pin:raise ValueError('Changed or shadowed MG34 resource: '+resource)
            loose=game.joinpath(*resource.split('/'))
            if loose.exists():
                if not archives_only:raise ValueError('Loose MG34 resource requires explicit archive-only inspection')
                other=loose.read_bytes();excluded[resource]={'size':len(other),'sha256':digest(other)}
            data[resource]=raw
    return data,excluded


def specification(fields,baseline):
    layout=decode_record(baseline)
    if (layout['kind']!=1 or text_field(baseline,88)!='MG 42' or digest(baseline)!=BASELINE_SHA
            or [a['selector'] for a in layout['actions']]!=[4,5]):
        raise ValueError('Changed explicit modern MG42 category baseline')
    reserved,kind,mode,scalar=struct.unpack_from('<IIIf',baseline,layout['actions'][1]['payload_offset'])
    if (reserved,kind,mode)!=(0,4,5):raise ValueError('Changed MG42 secondary constants')
    members=layout['members']
    return {'provenance':'ASSEMBLAGE_MODERNE','status':'prototype_disabled','native_class':1,
        'names':{'internal':'MODERN_MG34','fpv':'PROTOTYPE_MG3FPV','world':'PROTOTYPE_MG34','icon':'wi_ge-mg34'},
        'text_id':0xffffffff,'weight':struct.unpack_from('<f',baseline,112)[0],
        'base_members_raw':{m:members[f'0x{m:02x}']['value_raw'] for m in RAW_BASE},
        'weapon_members_raw':{m:201 if m==0x54 else members[f'0x{m:02x}']['value_raw'] for m in RAW_WEAPON},
        'primary':{'selector':4,'editor_fields':dict(fields)},
        'secondary':{'selector':5,'mode_raw':mode,'scalar':scalar}}


def world_model():
    recipe=json.loads((ROOT/'experimental/MG34_PORTABLE/modern-world-model.json').read_text(encoding='utf-8'))
    raw=encode_4ds(recipe,build_meshes(recipe))
    if (len(raw),digest(raw))!=WORLD_PIN:raise ValueError('Changed modern MG34 world model')
    return raw


def prepare(tables,sources,hand_raw,bank,profile,variant,state_machine,sound_machine,table_machine,loader,*,inventory=None):
    if set(sources)!=set(SOURCE_PINS):raise ValueError('Incomplete MG34 source set')
    for name,raw in sources.items():
        if (len(raw),digest(raw))!=SOURCE_PINS[name][1:]:raise ValueError('Changed pinned MG34 source: '+name)
    row=require_row(tables['others.DTA','tables/item_shoot.tbl'],32,stride=135,name_column=2,name='MG 34')
    if row['sha256']!=SHOOT_ROW_SHA:raise ValueError('Changed historical MG34 shoot row')
    data=tables['SabreSquadron.dta','tables/items.sav'];slots=parse_items(data)['slots'];base=slots[33]
    baseline=data[base['offset']:base['offset']+base['size']];spec=specification(row['fields'],baseline)
    references=editor_references(row['fields'],parse_sounds(sources['tables/ingamesounds.def']))
    for ref,expected in zip(references,((2,34,'G MG34',['f_mg34_a.wav']),(3,38,'G MG34 Reload',['mg34_r.wav']))):
        if not ref['resolved'] or (ref['bank'],ref['index'],ref['label'],ref['filenames'])!=expected:
            raise ValueError('Changed MG34 sound association')
    text_files={};text_report=None
    if inventory is not None:
        from build_modern_inventory_text_lab import prepare as prepare_texts
        if not isinstance(inventory,dict) or set(inventory)!={'catalogue','sources','occupied_item_text_ids','mission_range'}:
            raise ValueError('Incomplete inventory snapshot')
        text_files,text_report=prepare_texts(**inventory)
        if 'mg34_portable' not in text_report['labels']:raise ValueError('Missing modern portable MG34 label')
        spec['text_id']=text_report['labels']['mg34_portable']['text_id']
    descriptor=build_weapon(spec)
    native=state_machine.inspect_record(descriptor,SLOT);ammo=[]
    for archive in ('SabreSquadron.dta','PatchX01.dta'):
        raw=tables[archive,'tables/items.sav'];entries=parse_items(raw)['slots'];slot=entries[201]
        if (slot.get('kind'),slot.get('internal_name'))!=(0,'AMMO MG 34'):
            raise ValueError('Portable MG34 ammunition owner differs')
        source=raw[slot['offset']:slot['offset']+slot['size']]
        ammo.append({'archive':archive,'source_record_sha256':digest(source),
                     **state_machine.ammo_binding(descriptor,source,weapon_slot=SLOT,ammo_slot=201)})
    bindings=[state_machine.fpv_binding(SLOT,i) for i in range(13)]
    sound=sound_machine.selection(descriptor,SLOT)
    if (sound.get('native_argument_flow_matches') is not True or sound.get('shoot')!={'bank':2,'index':34}
            or sound.get('reload')!={'bank':3,'index':38}):raise ValueError('Incomplete native MG34 sound flow')
    files,resources=prepare_resources('MG34',variant,hand_raw,bank,profile,tables,table_machine,loader)
    if digest(files['PROTOTYPE_MG3_HandFPV.4ds.disabled'])!=FPV_PIN:raise ValueError('Changed MG34 FPV model')
    # The bank's descriptive filename exceeds Item's 19-byte stem limit.
    # Rename only its output alias; geometry and animation target names stay exact.
    files=dict(files)
    files['PROTOTYPE_MG3FPV.4ds.disabled']=files.pop('PROTOTYPE_MG3_HandFPV.4ds.disabled')
    files={**files,'PROTOTYPE_MG34.item.disabled':descriptor,'PROTOTYPE_MG34.4ds.disabled':world_model(),**text_files}
    report={'schema_version':1,'scope':'private_disabled_portable_mg34_descriptor','runtime_status':'pending',
        'provenance':'ASSEMBLAGE_MODERNE_RESSOURCES_MIXTES','synthetic_slot':SLOT,'hand_variant':variant,
        'source_pins':SOURCE_PINS,'historical_shoot_row_sha256':row['sha256'],
        'modern_design_decisions':{'baseline_owner':'Sabre MG 42 slot 33, individual category attributes only',
            'baseline_sha256':digest(baseline),'weight':spec['weight'],'secondary':spec['secondary'],
            'base_members_raw':{hex(k):v for k,v in spec['base_members_raw'].items()},
            'weapon_members_raw':{hex(k):v for k,v in spec['weapon_members_raw'].items()},
            'text_id':spec['text_id'],'historical_base_record_recovered':False,'whole_donor_record_copied':False,
            'opaque_bytes_policy':'modern_zero_fill_not_recovered','balance_qualified':False},
        'native_descriptor':native,'native_ammunition_checks':ammo,'native_fpv_binding_checks':bindings,
        'sound_references':references,'native_sound_arguments':sound,
        'audio_metadata':{name:pcm_metadata(raw) for name,raw in sources.items() if name.endswith('.wav')},
        'source_resource_audit_before_model_alias':resources,'inventory_texts':text_report,
        'modern_fpv_alias':{'source':'PROTOTYPE_MG3_HandFPV','item_stem':'PROTOTYPE_MG3FPV',
                            'model_bytes_unchanged':True,'animation_target_names_unchanged':True},
        'files':{name:{'size':len(raw),'sha256':digest(raw)} for name,raw in files.items()},
        'pending_requirements':list(PENDING)+(['inventory_text_allocation'] if text_report is None else []),
        'tank_mg34_and_ammo_211_untouched':True,'helmet_slot_32_untouched':True,
        'audio_or_icon_exported':False,'commercial_hand_model_exported':False,'complete_binary_descriptor_built':True,
        'central_tables_emitted':False,'item_slot_allocated_in_game':False,'installation_allowed':False,
        'game_started':False,'game_modified':False,'playable_weapon':False}
    return files,report


def full_tables(tables,files,report,*,item_layer,state_machine,table_machine,fpv_machine,overlays=None):
    """Compose and reverse an inert pair; preserve all existing source bytes."""
    from item_table_additive import build,restore,fingerprint
    from item_table_overlay import compose
    from fpv_resource_oracle import inspect_loaded_requests
    if item_layer not in ('SabreSquadron.dta','PatchX01.dta'):raise ValueError('Unreviewed full-table item layer')
    if (report.get('scope')!='private_disabled_portable_mg34_descriptor' or report.get('inventory_texts') is None
            or report.get('synthetic_slot')!=SLOT or report.get('hand_variant') not in ('H','R')):
        raise ValueError('Complete disabled MG34 inventory descriptor required')
    for name,raw in files.items():
        if report['files'].get(name)!=fingerprint(raw):raise ValueError('Changed MG34 descriptor bundle')
    if set(files)!=set(report['files']):raise ValueError('Incomplete MG34 descriptor bundle')
    keys={'items':(item_layer,'tables/items.sav'),'fpv':('SabreSquadron.dta','tables/fpvanims.sav')}
    for key in keys.values():
        if key not in tables or (len(tables[key]),digest(tables[key]))!=TABLE_PINS[key]:
            raise ValueError('Changed MG34 central table source')
    selected={name:tables[key] for name,key in keys.items()};composition=None
    descriptor=files['PROTOTYPE_MG34.item.disabled']
    fragment=files[f"PROTOTYPE_MG3P{report['hand_variant']}.fpvgroup.disabled"]
    if overlays is None:current,proof=build(selected['items'],selected['fpv'],descriptor,fragment,slot=SLOT)
    else:
        current,composition=compose(selected,overlays,descriptor,fragment,slot=SLOT)
        proof=composition['transaction'];selected={**selected,**overlays}
    if restore(current,proof)!=selected:raise ValueError('MG34 full-table reversal differs from selected snapshots')
    checked=[]
    for slot in parse_items(current['items'])['slots']:
        if not slot['present']:continue
        raw=current['items'][slot['offset']:slot['offset']+slot['size']]
        receipt=state_machine.inspect_record(raw,slot['slot'])
        if receipt.get('native_decode_matches') is not True or receipt.get('native_descriptor_measure_matches') is not True:
            raise ValueError('Incomplete native MG34 full-table descriptor verification')
        checked.append(slot['slot'])
    traversal={'items':table_machine.inspect_table(current['items']),'fpv':fpv_machine.inspect_table(current['fpv'])}
    required={'items':('native_slot_loop_matches','native_loaded_descriptors_match','source_read_only_unchanged'),
              'fpv':('native_nested_traversal_matches','native_strings_and_values_match','source_read_only_unchanged','unpopulated_cells_unchanged')}
    for key,fields in required.items():
        if traversal[key].get('table_sha256')!=digest(current[key]) or any(traversal[key].get(f) is not True for f in fields):
            raise ValueError('Incomplete native MG34 full-table traversal')
    requests=inspect_loaded_requests(fpv_machine,current['fpv'],SLOT)
    result={**files,'Tables/items.sav.disabled':current['items'],'Tables/FpvAnims.sav.disabled':current['fpv']}
    return result,{'schema_version':1,'scope':'private_disabled_portable_mg34_full_tables','runtime_status':'pending',
        'provenance':'ASSEMBLAGE_MODERNE_RESSOURCES_MIXTES','descriptor_lab':report,
        'item_layer':item_layer,'hand_variant':report['hand_variant'],'transaction':proof,
        'central_table_overlay_composition':composition,'reverse_verified_in_memory':True,
        'native_descriptor_records_checked':len(checked),'native_descriptor_slots_checked':checked,
        'native_table_traversal':traversal,'native_animation_resource_requests':requests,
        'files':{name:fingerprint(raw) for name,raw in result.items()},
        'pending_requirements':[p for p in report['pending_requirements'] if p!='additive_central_table_transaction']
            +['isolated_file_deployment_transaction','other_resource_override_compatibility'],
        'disabled_table_entry_prepared':True,'disabled_fpv_group_prepared':True,
        'item_slot_allocated_in_game':False,'global_slot_reservation':False,'installation_allowed':False,
        'game_modified':False,'game_started':False,'playable_weapon':False,'full_save_compatibility_qualified':False}


def main(argv=None):
    from benelli_fpv_rig_audit import read_hands,HAND_MODELS
    from item_native_contract import SOURCE_SHA,IMAGE_SHA
    from item_state_oracle import StateOracle
    from item_sound_oracle import SoundOracle
    from fpv_resource_oracle import FpvResourceOracle
    from ls3d_animation_load_oracle import AnimationLoadOracle
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--bank',type=Path,required=True)
    parser.add_argument('--hand',choices=('H','R'),required=True);parser.add_argument('--profile',type=Path,default=PROFILE)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--output-name',required=True);parser.add_argument('--inventory-texts',action='store_true')
    parser.add_argument('--item-layer',choices=('SabreSquadron.dta','PatchX01.dta'),help='Also prepare a full disabled table pair')
    parser.add_argument('--preserve-central-overrides',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.preserve_central_overrides and args.item_layer is None:raise ValueError('Central overrides require a selected full-table layer')
        if args.item_layer and not args.inventory_texts:raise ValueError('Full tables require --inventory-texts')
        if args.item_layer:
            from build_benelli_table_lab import output_directory as table_output
            output=table_output(args.output_name)
        else:output=output_directory(args.output_name)
        if digest((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        tables,excluded=read_tables(args.game,archives_only=args.archives_only or args.preserve_central_overrides)
        overlays=None
        if args.preserve_central_overrides:
            from item_table_overlay import read_overlays
            overlays=read_overlays(args.game)
        sources,source_excluded=read_sources(args.game,archives_only=args.archives_only)
        hands,hand_excluded=read_hands(args.game,archives_only=args.archives_only)
        image=args.image.read_bytes();inventory=None
        if args.inventory_texts:
            from build_modern_inventory_text_lab import CATALOGUE,read_text_sources,occupied_item_text_ids
            from custom_mission_packages import TEXT_ID_START,TEXT_ID_END
            inventory={'catalogue':json.loads(CATALOGUE.read_text(encoding='utf-8')),'sources':read_text_sources(args.game),
                'occupied_item_text_ids':occupied_item_text_ids(args.game,tables),'mission_range':(TEXT_ID_START,TEXT_ID_END)}
        source=HAND_MODELS[0 if args.hand=='H' else 1]
        files,report=prepare(tables,sources,hands[source],args.bank,json.loads(args.profile.read_text(encoding='utf-8')),
            args.hand,StateOracle(image),SoundOracle(image),FpvResourceOracle(image),
            AnimationLoadOracle((args.game/'LS3DF.dll').read_bytes()),inventory=inventory)
        report.update(source_executable_sha256=SOURCE_SHA,private_image_sha256=IMAGE_SHA,
                      excluded_loose_overrides={'tables':excluded,'resources':source_excluded,'hands':hand_excluded})
        if args.item_layer:
            from item_table_oracle import TableOracle
            from build_benelli_table_lab import write_lab
            files,report=full_tables(tables,files,report,item_layer=args.item_layer,state_machine=StateOracle(image),
                                    table_machine=TableOracle(image),fpv_machine=FpvResourceOracle(image),overlays=overlays)
            if overlays is not None:
                from item_table_overlay import require_unchanged_overlays
                require_unchanged_overlays(args.game,overlays)
            write_lab(output,files,report)
            print(json.dumps({'output':str(output),'files':len(files)+2,'reverse_verified_in_memory':True,
                'native_descriptor_records_checked':report['native_descriptor_records_checked'],
                'native_resource_requests':len(report['native_animation_resource_requests']),'playable_weapon':False}));return 0
        output.mkdir(parents=True,exist_ok=False)
        for name,raw in files.items():
            path=output.joinpath(*name.split('/'));path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(raw)
            if path.read_bytes()!=raw:raise ValueError('Private MG34 output readback mismatch')
        with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({'output':str(output),'files':len(files)+1,'native_ammunition_checks':report['native_ammunition_checks'],
                         'native_sound_arguments':report['native_sound_arguments'],'playable_weapon':False},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError,EOFError,wave.Error) as error:
        print('Private portable MG34 assembly refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
