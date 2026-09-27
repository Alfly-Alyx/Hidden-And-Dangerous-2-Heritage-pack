#!/usr/bin/env python3
"""PRIVATE disabled FG42 assembly, with explicit modern numeric audio choices.

Original shoot fields survive except the two unresolved sound symbols in this
new descriptor only. The historical editor table and helmet slot 27 are never
changed. Modern audio, icon, models and category choices are not recovered data.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

from benelli_table_audit import read_tables,TABLE_PINS
from build_benelli_table_lab import output_directory,write_lab
from build_modern_asset import ROOT,build_meshes,encode_4ds
from build_modern_equipment_hose import digest
from build_modern_audio_lab import prepare as prepare_audio,read_sources as read_audio,RECIPES
from build_modern_inventory_text_lab import prepare as prepare_texts
from build_rigid_weapon_resource_lab import prepare as prepare_resources,SLOTS
from build_rigid_weapon_hand_bank import PROFILE
from item_editor_table import require_row
from item_native_layout import decode_record
from item_sound_audit import editor_references
from item_weapon_descriptor import build_weapon,RAW_BASE,RAW_WEAPON
from items_sav import parse as parse_items,text_field
from modern_inventory_icon import prepare as prepare_icon
from sound_definition import parse as parse_sounds
from sound_definition_additive import restore as restore_audio,fingerprint

SLOT=SLOTS['FG42']
BASELINE_SHA='e097423c6e8efa6e9565459ad44238a6ceb36df3fc487b6f21cd020501b44291'
SHOOT_ROW_SHA='3c1c1186dbee311e4239297a3d1b460165fc59300c706d6b1f3492e21a3bdfb5'
AMMO_SHA='5b7e3b38eb13ae12de1d49207e0c926368c8307a99a0bdb859d10001f476c263'
WORLD_PIN=(151395,'111c3e8cb882bc67b53415097165f6ca8f63533af528ac554e6e16aa57091aba')
FPV_PIN='0ae8254f8ad43678ac7e02086ffc72eff7bb03ba9a1a996eb7e85f432f1062f6'
WORLD_RECIPE=ROOT/'experimental/FG42/modern-world-model.json'
PENDING=['additive_central_table_transaction','global_item_and_resource_collision_clearance',
    'icon_native_loading_background_and_inventory_layout','inventory_text_rendering_and_fonts',
    'sound_listening_full_definition_loading_and_playback','sound_event_timing',
    'raw_animation_contacts_and_reload_hand_gestures','post_blend_constraint_engine_hook',
    'scene_model_loading_and_clone','camera_alignment','secondary_and_balance',
    'character_animations_and_ai','complete_save_compatibility','network_and_live_gameplay']


def modern_sound_fields(fields,audio_files,audio_report):
    if (fields.get(8),fields.get(10))!=('FG42_F','FG42_R'):
        raise ValueError('Expected original unresolved FG42 sound symbols')
    if (audio_report.get('scope')!='private_disabled_modern_audio_lab'
            or set(audio_files)!=set(audio_report.get('files',{}))
            or any(audio_report['files'][n]!=fingerprint(r) for n,r in audio_files.items())):
        raise ValueError('Changed modern audio assembly')
    definition=audio_files['Tables/IngameSounds.def.disabled']
    restore_audio(definition,audio_report['transaction'])
    result=dict(fields);choices=[]
    for column,bank,kind,stem in ((8,2,'SHOT','MOD_FG42_F'),(10,3,'RELOAD','MOD_FG42_R')):
        selected=[r for r in audio_report['transaction']['additions'] if r['label']=='MODERN FG42 '+kind]
        if len(selected)!=1:raise ValueError('Missing or duplicate modern FG42 sound')
        row=selected[0]
        if row['bank']!=bank or row['filename']!=stem+'.wav' or 'Sounds/'+stem+'.wav.disabled' not in audio_files:
            raise ValueError('Wrong modern FG42 sound owner')
        result[column]=str(row['index'])
        choices.append({'column':column,'historical_symbol':fields[column],'modern_bank':bank,
            'modern_index':row['index'],'filename':row['filename'],'historical_symbol_resolved':False})
    references=editor_references(result,parse_sounds(definition))
    if any(not r['resolved'] or r['filenames']!=[c['filename']] for r,c in zip(references,choices)):
        raise ValueError('Modern FG42 direct references differ')
    return result,choices,references


def specification(fields,baseline):
    layout=decode_record(baseline)
    if (layout['kind']!=1 or text_field(baseline,88)!='MP 44' or digest(baseline)!=BASELINE_SHA
            or [a['selector'] for a in layout['actions']]!=[4,5]):
        raise ValueError('Changed explicit modern MP44 category baseline')
    reserved,kind,mode,scalar=struct.unpack_from('<IIIf',baseline,layout['actions'][1]['payload_offset'])
    if (reserved,kind,mode)!=(0,4,5):raise ValueError('Changed MP44 secondary constants')
    members=layout['members']
    return {'provenance':'ASSEMBLAGE_MODERNE','status':'prototype_disabled','native_class':1,
        'names':{'internal':'MODERN_FG42','fpv':'PROTOTYPE_FG4FPV','world':'PROTOTYPE_FG42','icon':'MOD_FG42_ICON'},
        'text_id':0xffffffff,'weight':struct.unpack_from('<f',baseline,112)[0],
        'base_members_raw':{m:members[f'0x{m:02x}']['value_raw'] for m in RAW_BASE},
        'weapon_members_raw':{m:196 if m==0x54 else members[f'0x{m:02x}']['value_raw'] for m in RAW_WEAPON},
        'primary':{'selector':4,'editor_fields':dict(fields)},
        'secondary':{'selector':5,'mode_raw':mode,'scalar':scalar}}


def world_assets():
    recipe=json.loads(WORLD_RECIPE.read_text(encoding='utf-8'));raw=encode_4ds(recipe,build_meshes(recipe))
    if (len(raw),digest(raw))!=WORLD_PIN:raise ValueError('Changed modern FG42 world geometry')
    icon,report=prepare_icon(recipe)
    return raw,icon,report


def prepare(tables,definition,recipes,hand_raw,bank,profile,variant,state_machine,sound_machine,table_machine,loader,*,inventory):
    if not isinstance(inventory,dict) or set(inventory)!={'catalogue','sources','occupied_item_text_ids','mission_range'}:
        raise ValueError('Complete FG42 inventory snapshot required')
    text_files,text_report=prepare_texts(**inventory)
    if 'fg42' not in text_report['labels']:raise ValueError('Missing explicitly modern FG42 label')
    row=require_row(tables['others.DTA','tables/item_shoot.tbl'],27,stride=135,name_column=2,name='FG 42')
    if row['sha256']!=SHOOT_ROW_SHA:raise ValueError('Changed historical FG42 shoot row')
    audio_files,audio_report=prepare_audio(definition,recipes,sound_machine)
    fields,choices,references=modern_sound_fields(row['fields'],audio_files,audio_report)
    data=tables['SabreSquadron.dta','tables/items.sav'];slot=parse_items(data)['slots'][26]
    baseline=data[slot['offset']:slot['offset']+slot['size']];spec=specification(fields,baseline)
    spec['text_id']=text_report['labels']['fg42']['text_id'];descriptor=build_weapon(spec)
    native=state_machine.inspect_record(descriptor,SLOT)
    if any(native.get(k) is not True for k in ('native_decode_matches','native_descriptor_measure_matches')):
        raise ValueError('Incomplete native FG42 descriptor receipt')
    ammo=[]
    for archive in ('SabreSquadron.dta','PatchX01.dta'):
        raw=tables[archive,'tables/items.sav'];slot=parse_items(raw)['slots'][196]
        source=raw[slot['offset']:slot['offset']+slot['size']]
        if (slot.get('kind'),slot.get('internal_name'),digest(source))!=(0,'AMMO FG 42',AMMO_SHA):
            raise ValueError('Changed FG42 ammunition owner or bytes')
        receipt=state_machine.ammo_binding(descriptor,source,weapon_slot=SLOT,ammo_slot=196)
        if receipt.get('native_ammo_binding_matches') is not True or receipt.get('initial_quantity')!=20.0:
            raise ValueError('Incomplete native FG42 ammunition receipt')
        ammo.append({'archive':archive,'source_record_sha256':digest(source),**receipt})
    bindings=[state_machine.fpv_binding(SLOT,i) for i in range(13)]
    sound=sound_machine.selection(descriptor,SLOT)
    if (sound.get('native_argument_flow_matches') is not True
            or sound.get('shoot')!={'bank':2,'index':choices[0]['modern_index']}
            or sound.get('reload')!={'bank':3,'index':choices[1]['modern_index']}):
        raise ValueError('Incomplete native FG42 modern sound flow')
    files,resources=prepare_resources('FG42',variant,hand_raw,bank,profile,tables,table_machine,loader)
    if digest(files['PROTOTYPE_FG4_HandFPV.4ds.disabled'])!=FPV_PIN:raise ValueError('Changed FG42 FPV model')
    files=dict(files);files['PROTOTYPE_FG4FPV.4ds.disabled']=files.pop('PROTOTYPE_FG4_HandFPV.4ds.disabled')
    world,icon,icon_report=world_assets()
    files={**files,**text_files,**audio_files,'PROTOTYPE_FG42.item.disabled':descriptor,
        'PROTOTYPE_FG42.4ds.disabled':world,'Maps/MOD_FG42_ICON.bmp.disabled':icon}
    return files,{'schema_version':1,'scope':'private_disabled_fg42_descriptor','runtime_status':'pending',
        'provenance':'ASSEMBLAGE_MODERNE_RESSOURCES_MIXTES','synthetic_slot':SLOT,'hand_variant':variant,
        'historical_shoot_row_sha256':row['sha256'],'historical_shoot_sound_symbols_resolved':False,
        'historical_shoot_table_changed':False,'modern_sound_choices':choices,'sound_references':references,
        'modern_design_decisions':{'baseline_owner':'Sabre MP 44 slot 26, individual category attributes only',
            'baseline_sha256':digest(baseline),'weight':spec['weight'],'secondary':spec['secondary'],
            'base_members_raw':{hex(k):v for k,v in spec['base_members_raw'].items()},
            'weapon_members_raw':{hex(k):v for k,v in spec['weapon_members_raw'].items()},'text_id':spec['text_id'],
            'historical_base_record_recovered':False,'whole_donor_record_copied':False,
            'opaque_bytes_policy':'modern_zero_fill_not_recovered','physical_weight_or_balance_qualified':False},
        'native_descriptor':native,'native_ammunition_checks':ammo,'native_fpv_binding_checks':bindings,
        'native_sound_arguments':sound,'audio_lab':audio_report,'inventory_texts':text_report,'modern_icon':icon_report,
        'source_resource_audit_before_model_alias':resources,
        'modern_fpv_alias':{'source':'PROTOTYPE_FG4_HandFPV','item_stem':'PROTOTYPE_FG4FPV',
            'model_bytes_unchanged':True,'animation_target_names_unchanged':True},
        'files':{name:fingerprint(raw) for name,raw in files.items()},'pending_requirements':list(PENDING),
        'helmet_slot_27_untouched':True,'commercial_hand_model_exported':False,'commercial_audio_exported':False,
        'commercial_central_sound_definition_private_only':True,'complete_binary_descriptor_built':True,
        'central_item_tables_emitted':False,'global_sound_indices_reserved':False,'item_slot_allocated_in_game':False,
        'installation_allowed':False,'game_started':False,'game_modified':False,'playable_weapon':False}


def full_tables(tables,files,report,*,item_layer,state_machine,table_machine,fpv_machine,overlays=None):
    from item_table_additive import build,restore
    from item_table_overlay import compose
    from fpv_resource_oracle import inspect_loaded_requests
    if item_layer not in ('SabreSquadron.dta','PatchX01.dta'):raise ValueError('Unreviewed FG42 full-table item layer')
    if (report.get('scope')!='private_disabled_fg42_descriptor' or report.get('inventory_texts') is None
            or report.get('audio_lab') is None or report.get('synthetic_slot')!=SLOT
            or report.get('hand_variant') not in ('H','R')):raise ValueError('Complete FG42 descriptor required')
    if set(files)!=set(report['files']) or any(report['files'][n]!=fingerprint(r) for n,r in files.items()):
        raise ValueError('Changed FG42 descriptor bundle')
    restore_audio(files['Tables/IngameSounds.def.disabled'],report['audio_lab']['transaction'])
    keys={'items':(item_layer,'tables/items.sav'),'fpv':('SabreSquadron.dta','tables/fpvanims.sav')}
    for key in keys.values():
        if key not in tables or (len(tables[key]),digest(tables[key]))!=TABLE_PINS[key]:
            raise ValueError('Changed FG42 central table source')
    selected={name:tables[key] for name,key in keys.items()};composition=None
    descriptor=files['PROTOTYPE_FG42.item.disabled'];fragment=files[f"PROTOTYPE_FG4P{report['hand_variant']}.fpvgroup.disabled"]
    if overlays is None:current,proof=build(selected['items'],selected['fpv'],descriptor,fragment,slot=SLOT)
    else:
        current,composition=compose(selected,overlays,descriptor,fragment,slot=SLOT)
        proof=composition['transaction'];selected={**selected,**overlays}
    if restore(current,proof)!=selected:raise ValueError('FG42 central table reversal differs')
    checked=[]
    for slot in parse_items(current['items'])['slots']:
        if not slot['present']:continue
        raw=current['items'][slot['offset']:slot['offset']+slot['size']]
        receipt=state_machine.inspect_record(raw,slot['slot'])
        if any(receipt.get(k) is not True for k in ('native_decode_matches','native_descriptor_measure_matches')):
            raise ValueError('Incomplete native FG42 full-table descriptor verification')
        checked.append(slot['slot'])
    traversal={'items':table_machine.inspect_table(current['items']),'fpv':fpv_machine.inspect_table(current['fpv'])}
    required={'items':('native_slot_loop_matches','native_loaded_descriptors_match','source_read_only_unchanged'),
        'fpv':('native_nested_traversal_matches','native_strings_and_values_match','source_read_only_unchanged','unpopulated_cells_unchanged')}
    for key,fields in required.items():
        if traversal[key].get('table_sha256')!=digest(current[key]) or any(traversal[key].get(f) is not True for f in fields):
            raise ValueError('Incomplete native FG42 full-table traversal')
    requests=inspect_loaded_requests(fpv_machine,current['fpv'],SLOT)
    result={**files,'Tables/items.sav.disabled':current['items'],'Tables/FpvAnims.sav.disabled':current['fpv']}
    return result,{'schema_version':1,'scope':'private_disabled_fg42_full_tables','runtime_status':'pending',
        'provenance':'ASSEMBLAGE_MODERNE_RESSOURCES_MIXTES','descriptor_lab':report,
        'item_layer':item_layer,'hand_variant':report['hand_variant'],'transaction':proof,
        'central_table_overlay_composition':composition,'reverse_verified_in_memory':True,
        'native_descriptor_records_checked':len(checked),'native_descriptor_slots_checked':checked,
        'native_table_traversal':traversal,'native_animation_resource_requests':requests,
        'files':{name:fingerprint(raw) for name,raw in result.items()},
        'pending_requirements':[p for p in report['pending_requirements'] if p!='additive_central_table_transaction']
            +['isolated_file_deployment_transaction','other_resource_override_compatibility'],
        'sound_definition_reversal_verified':True,'disabled_table_entry_prepared':True,'disabled_fpv_group_prepared':True,
        'item_slot_allocated_in_game':False,'global_slot_reservation':False,'installation_allowed':False,
        'game_modified':False,'game_started':False,'playable_weapon':False,'full_save_compatibility_qualified':False}


def main(argv=None):
    from benelli_fpv_rig_audit import read_hands,HAND_MODELS
    from item_native_contract import SOURCE_SHA,IMAGE_SHA
    from item_state_oracle import StateOracle
    from item_sound_oracle import SoundOracle
    from fpv_resource_oracle import FpvResourceOracle
    from ls3d_animation_load_oracle import AnimationLoadOracle
    from build_modern_inventory_text_lab import CATALOGUE,read_text_sources,occupied_item_text_ids
    from custom_mission_packages import TEXT_ID_START,TEXT_ID_END
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--bank',type=Path,required=True)
    parser.add_argument('--hand',choices=('H','R'),required=True);parser.add_argument('--profile',type=Path,default=PROFILE)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin');parser.add_argument('--output-name',required=True)
    parser.add_argument('--item-layer',choices=('SabreSquadron.dta','PatchX01.dta'));parser.add_argument('--preserve-central-overrides',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.preserve_central_overrides and args.item_layer is None:raise ValueError('Central overrides require a selected full-table layer')
        output=output_directory(args.output_name)
        if digest((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        tables,excluded=read_tables(args.game,archives_only=args.archives_only or args.preserve_central_overrides)
        definition,preflight=read_audio(args.game,archives_only=args.archives_only)
        hands,hand_excluded=read_hands(args.game,archives_only=args.archives_only);image=args.image.read_bytes()
        inventory={'catalogue':json.loads(CATALOGUE.read_text(encoding='utf-8')),'sources':read_text_sources(args.game),
            'occupied_item_text_ids':occupied_item_text_ids(args.game,tables),'mission_range':(TEXT_ID_START,TEXT_ID_END)}
        recipes={case:json.loads(path.read_text(encoding='utf-8')) for case,path in RECIPES.items()}
        overlays=None
        if args.preserve_central_overrides:
            from item_table_overlay import read_overlays
            overlays=read_overlays(args.game)
        source=HAND_MODELS[0 if args.hand=='H' else 1]
        files,report=prepare(tables,definition,recipes,hands[source],args.bank,json.loads(args.profile.read_text(encoding='utf-8')),
            args.hand,StateOracle(image),SoundOracle(image),FpvResourceOracle(image),
            AnimationLoadOracle((args.game/'LS3DF.dll').read_bytes()),inventory=inventory)
        from item_secondary_oracle import SecondaryOracle,checked_action
        report['native_secondary_action']=checked_action(SecondaryOracle(image),files['PROTOTYPE_FG42.item.disabled'],SLOT)
        report.update(source_executable_sha256=SOURCE_SHA,private_image_sha256=IMAGE_SHA,audio_preflight=preflight,
            excluded_loose_overrides={'tables':excluded,'hands':hand_excluded})
        if args.item_layer:
            from item_table_oracle import TableOracle
            files,report=full_tables(tables,files,report,item_layer=args.item_layer,state_machine=StateOracle(image),
                table_machine=TableOracle(image),fpv_machine=FpvResourceOracle(image),overlays=overlays)
        if overlays is not None:
            from item_table_overlay import require_unchanged_overlays
            require_unchanged_overlays(args.game,overlays)
        write_lab(output,files,report)
        print(json.dumps({'output':str(output),'files':len(files)+2,'scope':report['scope'],
            'native_descriptor_records_checked':report.get('native_descriptor_records_checked'),
            'playable_weapon':False,'game_modified':False}));return 0
    except (OSError,ValueError,KeyError,ImportError,EOFError) as error:
        print('Private FG42 assembly refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
