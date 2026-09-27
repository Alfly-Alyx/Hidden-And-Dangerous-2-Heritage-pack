#!/usr/bin/env python3
"""PRIVATE disabled modern ZK383 plus its original game magazine.

No recovered ZK383 behavior is claimed. The two new class-1/class-0 records,
their original geometry/audio/icons and text are kept separate from all old
objects, with exact memory-only reversal and no game installation or launch.
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
from item_ammo_descriptor import build_ammunition
from item_native_layout import decode_record
from item_weapon_descriptor import build_weapon,RAW_BASE,RAW_WEAPON,exact_keys
from item_shoot_projection import FIELDS
from item_sound_audit import editor_references
from items_sav import parse as parse_items,text_field
from fpv_table import parse as parse_fpv
from menu_gui_audit import parse_4ds_nodes
from modern_inventory_icon import prepare as prepare_icon
from sound_definition import parse as parse_sounds
from sound_definition_additive import restore as restore_audio,fingerprint

SLOT=SLOTS['ZK383'];AMMO_SLOT=365
DIRECTORY=ROOT/'experimental/GAROTA_AND_ZK383'
RECIPE=DIRECTORY/'modern-zk383-item.json'
PROFILE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/modern-rigid-hand-grips-zk383-trigger.json'
WEAPON_BASE_SHA='1d29675dbd844952fff28120073d92402798a6e461695e82bc7d668607f3753b'
AMMO_BASE_SHA='1124c21a12c8d43a118fc8b04f93250d3fe1393bb903c7bb3861ba19cb8e5cb9'
FPV_PIN='554a5721a39fffc7d65ac94fb4762a7847f233eef4a214bb9376953c4256b6ef'
MODEL_PINS={'world':(193258,'1730926a7468d5a91ec4ae19467ee2613905146caa329f7c0a163f09a9c30032'),
    'magazine':(5486,'021b5186b93245073c6cf56f81e3ce8a46e2e2e0b93184eed81f3c461b73b847')}
PENDING=['additive_weapon_and_ammunition_tables','global_item_and_resource_collision_clearance',
    'trigger_hand_visual_review_and_reload_gestures','scene_model_loading_clone_and_camera',
    'native_icon_loading_background_and_inventory_layout','inventory_text_rendering_and_fonts',
    'sound_listening_full_definition_loading_and_playback','animation_shoot_reload_event_timing',
    'modern_game_balance','character_animations_and_ai','complete_save_compatibility','network_and_live_gameplay']


def checked_recipe(recipe):
    exact_keys(recipe,('schema_version','provenance','status','case','description','category_weapon_slot',
        'category_weapon_sha256','category_ammo_slot','category_ammo_sha256','weapon_slot','ammo_slot',
        'ammo_quantity','shoot_fields'),'modern ZK383 recipe')
    expected={'schema_version':1,'provenance':'MODERN_GAME_DESIGN','status':'prototype_disabled','case':'ZK383',
        'category_weapon_slot':18,'category_weapon_sha256':WEAPON_BASE_SHA,'category_ammo_slot':187,
        'category_ammo_sha256':AMMO_BASE_SHA,'weapon_slot':SLOT,'ammo_slot':AMMO_SLOT}
    if any(type(recipe[k]) is not type(v) or recipe[k]!=v for k,v in expected.items()):raise ValueError('Unreviewed ZK383 recipe identity')
    if (not isinstance(recipe['description'],str) or not recipe['description']
            or type(recipe['ammo_quantity']) is not int or not 1<=recipe['ammo_quantity']<=10000):
        raise ValueError('Invalid modern ZK383 design quantity or provenance')
    exact_keys(recipe['shoot_fields'],{str(c) for c,_,_ in FIELDS},'modern ZK383 shooting fields')
    fields={int(k):v for k,v in recipe['shoot_fields'].items()}
    if (fields[2],fields[8],fields[10])!=('ZK 383','MOD_ZK383_F','MOD_ZK383_R'):
        raise ValueError('Modern ZK383 identity or audio alias differs')
    return fields


def specifications(recipe,weapon_base,ammo_base,texts,audio_files,audio_report):
    fields=checked_recipe(recipe)
    weapon=decode_record(weapon_base);ammo=decode_record(ammo_base)
    if (digest(weapon_base)!=WEAPON_BASE_SHA or text_field(weapon_base,88)!='MP 40 '
            or weapon['kind']!=1 or [a['selector'] for a in weapon['actions']]!=[4,5]):
        raise ValueError('Changed MP40 game-category weapon baseline')
    if (digest(ammo_base)!=AMMO_BASE_SHA or text_field(ammo_base,88)!='AMMO MP 40'
            or ammo['kind']!=0 or [a['selector'] for a in ammo['actions']]!=[0,0]):
        raise ValueError('Changed MP40 game-category ammunition baseline')
    if (audio_report.get('scope')!='private_disabled_modern_audio_lab'
            or set(audio_files)!=set(audio_report.get('files',{}))
            or any(audio_report['files'][n]!=fingerprint(r) for n,r in audio_files.items())):
        raise ValueError('Changed modern ZK383 audio assembly')
    definition=audio_files['Tables/IngameSounds.def.disabled'];restore_audio(definition,audio_report['transaction'])
    choices=[]
    for column,bank,kind in ((8,2,'SHOT'),(10,3,'RELOAD')):
        alias=fields[column];rows=[r for r in audio_report['transaction']['additions'] if r['label']=='MODERN ZK383 '+kind]
        if len(rows)!=1 or rows[0]['bank']!=bank or rows[0]['filename']!=alias+'.wav' or 'Sounds/'+alias+'.wav.disabled' not in audio_files:
            raise ValueError('Missing or changed modern ZK383 audio association')
        fields[column]=str(rows[0]['index']);choices.append({'column':column,'modern_alias':alias,'bank':bank,'index':rows[0]['index']})
    references=editor_references(fields,parse_sounds(definition))
    if any(not r['resolved'] or r['filenames']!=[c['modern_alias']+'.wav'] for r,c in zip(references,choices)):
        raise ValueError('Modern ZK383 sound reference differs')
    reserved,kind,mode,scalar=struct.unpack_from('<IIIf',weapon_base,weapon['actions'][1]['payload_offset'])
    if (reserved,kind,mode)!=(0,4,5):raise ValueError('Changed MP40 secondary constants')
    common={'provenance':'ASSEMBLAGE_MODERNE','status':'prototype_disabled'}
    gun={**common,'native_class':1,
        'names':{'internal':'MODERN_ZK383','fpv':'PROTOTYPE_ZK3FPV','world':'PROTOTYPE_ZK383','icon':'MOD_ZK383_ICON'},
        'text_id':texts['zk383']['text_id'],'weight':struct.unpack_from('<f',weapon_base,112)[0],
        'base_members_raw':{m:weapon['members'][f'0x{m:02x}']['value_raw'] for m in RAW_BASE},
        'weapon_members_raw':{m:AMMO_SLOT if m==0x54 else weapon['members'][f'0x{m:02x}']['value_raw'] for m in RAW_WEAPON},
        'primary':{'selector':4,'editor_fields':fields},'secondary':{'selector':5,'mode_raw':mode,'scalar':scalar}}
    magazine={**common,'native_class':0,
        'names':{'internal':'MODERN_ZK383_AMMO','fpv':'','world':'PROTOTYPE_ZK3MAG','icon':'MOD_ZK3MAG_ICON'},
        'text_id':texts['zk383_magazine']['text_id'],'weight':struct.unpack_from('<f',ammo_base,112)[0],
        'base_members_raw':{m:ammo['members'][f'0x{m:02x}']['value_raw'] for m in RAW_BASE},'quantity':recipe['ammo_quantity']}
    return gun,magazine,choices,references


def model_assets():
    files={};reports={}
    for role,filename,alias,icon_alias in (
        ('world','modern-zk383-world.json','PROTOTYPE_ZK383','MOD_ZK383_ICON'),
        ('magazine','modern-zk383-magazine.json','PROTOTYPE_ZK3MAG','MOD_ZK3MAG_ICON')):
        recipe=json.loads((DIRECTORY/filename).read_text(encoding='utf-8'));meshes=build_meshes(recipe)
        raw=encode_4ds(recipe,meshes)
        if (len(raw),digest(raw))!=MODEL_PINS[role]:raise ValueError('Changed modern ZK383 '+role+' geometry')
        decoded=parse_4ds_nodes(raw);icon,icon_report=prepare_icon(recipe)
        files[alias+'.4ds.disabled']=raw;files['Maps/'+icon_alias+'.bmp.disabled']=icon
        reports[role]={'model':fingerprint(raw),'nodes':decoded['node_count'],'pieces':len(meshes),
            'triangles_per_lod':[sum(len(pair[i].triangles) for pair in meshes) for i in (0,1)],
            'icon':icon_report,'commercial_model_or_icon_used':False,'engine_loaded':False}
    return files,reports


def availability(tables):
    checked=[]
    for archive in ('SabreSquadron.dta','PatchX01.dta'):
        key=(archive,'tables/items.sav');raw=tables[key]
        if (len(raw),digest(raw))!=TABLE_PINS[key]:raise ValueError('Changed ZK383 candidate archive')
        slots=parse_items(raw)['slots']
        if any(slots[s]['present'] for s in (SLOT,AMMO_SLOT)):raise ValueError('Modern ZK383 or ammunition candidate occupied')
        for slot,owner,pin in ((18,'MP 40 ',WEAPON_BASE_SHA),(187,'AMMO MP 40',AMMO_BASE_SHA)):
            row=slots[slot]
            if (row['internal_name'],row['sha256'])!=(owner,pin):raise ValueError('Changed ZK383 category source layer')
        checked.append({'archive':archive,'candidate_slots_empty':[SLOT,AMMO_SLOT],'sha256':digest(raw)})
    key=('SabreSquadron.dta','tables/fpvanims.sav');raw=tables[key]
    if (len(raw),digest(raw))!=TABLE_PINS[key]:raise ValueError('Changed ZK383 FPV source')
    if {g['id'] for g in parse_fpv(raw)['groups']}&{SLOT+100,AMMO_SLOT+100}:raise ValueError('ZK383 candidate FPV owner already present')
    return checked


def prepare(tables,definition,recipes,recipe,hand_raw,bank,profile,variant,state_machine,sound_machine,table_machine,loader,*,inventory):
    checked_recipe(recipe);free=availability(tables)
    if not isinstance(inventory,dict) or set(inventory)!={'catalogue','sources','occupied_item_text_ids','mission_range'}:
        raise ValueError('Complete ZK383 inventory snapshot required')
    text_files,text_report=prepare_texts(**inventory)
    if not {'zk383','zk383_magazine'}<=set(text_report['labels']):raise ValueError('Missing modern ZK383 inventory labels')
    audio_files,audio_report=prepare_audio(definition,recipes,sound_machine)
    raw=tables['SabreSquadron.dta','tables/items.sav'];slots=parse_items(raw)['slots']
    sources=[raw[slots[n]['offset']:slots[n]['offset']+slots[n]['size']] for n in (18,187)]
    gun_spec,ammo_spec,choices,references=specifications(recipe,*sources,text_report['labels'],audio_files,audio_report)
    gun=build_weapon(gun_spec);ammo=build_ammunition(ammo_spec);native={}
    for name,descriptor,slot in (('weapon',gun,SLOT),('ammunition',ammo,AMMO_SLOT)):
        native[name]=state_machine.inspect_record(descriptor,slot)
        if any(native[name].get(k) is not True for k in ('native_decode_matches','native_descriptor_measure_matches')):
            raise ValueError('Incomplete native modern ZK383 '+name+' receipt')
    binding=state_machine.ammo_binding(gun,ammo,weapon_slot=SLOT,ammo_slot=AMMO_SLOT)
    if binding.get('native_ammo_binding_matches') is not True or binding.get('initial_quantity')!=recipe['ammo_quantity']:
        raise ValueError('Incomplete native modern ZK383 ammunition binding')
    sound=sound_machine.selection(gun,SLOT)
    if (sound.get('native_argument_flow_matches') is not True
            or sound.get('shoot')!={'bank':2,'index':choices[0]['index']}
            or sound.get('reload')!={'bank':3,'index':choices[1]['index']}):raise ValueError('Incomplete native ZK383 sound flow')
    files,resources=prepare_resources('ZK383',variant,hand_raw,bank,profile,tables,table_machine,loader)
    if digest(files['PROTOTYPE_ZK3_HandFPV.4ds.disabled'])!=FPV_PIN:raise ValueError('Changed modern ZK383 FPV model')
    files=dict(files);files['PROTOTYPE_ZK3FPV.4ds.disabled']=files.pop('PROTOTYPE_ZK3_HandFPV.4ds.disabled')
    assets,models=model_assets()
    files={**files,**assets,**text_files,**audio_files,'PROTOTYPE_ZK383.item.disabled':gun,'PROTOTYPE_ZK3MAG.item.disabled':ammo}
    return files,{'schema_version':1,'scope':'private_disabled_zk383_and_ammunition','runtime_status':'pending',
        'provenance':'MODERN_GAME_DESIGN_WITH_PRIVATE_DERIVED_HAND_CLIPS','synthetic_slot':SLOT,'synthetic_ammo_slot':AMMO_SLOT,
        'hand_variant':variant,'archive_availability_only':free,'modern_game_recipe':recipe,
        'modern_design_decisions':{'weapon_category':'Sabre MP 40 slot 18, individual category values only',
            'ammo_category':'Sabre AMMO MP 40 slot 187, individual category values only, new quantity',
            'weapon_specification':gun_spec,'ammunition_specification':ammo_spec,
            'whole_donor_records_copied':False,'historical_zk383_data_recovered':False,
            'opaque_bytes_policy':'modern_zero_fill_not_recovered','physical_properties_or_game_balance_qualified':False},
        'native_descriptors':native,'native_ammunition_binding':binding,'native_sound_arguments':sound,
        'native_fpv_bindings':[state_machine.fpv_binding(SLOT,i) for i in range(13)],
        'modern_sound_choices':choices,'sound_references':references,'audio_lab':audio_report,
        'inventory_texts':text_report,'modern_models_and_icons':models,'resource_associations_before_model_alias':resources,
        'modern_fpv_alias':{'source':'PROTOTYPE_ZK3_HandFPV','item_stem':'PROTOTYPE_ZK3FPV','bytes_and_target_names_unchanged':True},
        'files':{n:fingerprint(r) for n,r in files.items()},'pending_requirements':list(PENDING),
        'existing_mp40_and_ammunition_187_unchanged':True,'commercial_hand_model_exported':False,'commercial_audio_exported':False,
        'source_sound_definition_and_texts_private_only':True,'central_item_tables_emitted':False,
        'item_slots_allocated_in_game':False,'installation_allowed':False,'game_started':False,'game_modified':False,'playable_weapon':False}


def full_tables(tables,files,report,*,item_layer,state_machine,table_machine,fpv_machine,overlays=None):
    from item_ammo_additive import build_pair,restore_pair,compose
    from fpv_resource_oracle import inspect_loaded_requests
    if item_layer not in ('SabreSquadron.dta','PatchX01.dta'):raise ValueError('Unreviewed ZK383 item layer')
    if (report.get('scope')!='private_disabled_zk383_and_ammunition' or report.get('synthetic_slot')!=SLOT
            or report.get('synthetic_ammo_slot')!=AMMO_SLOT or report.get('hand_variant') not in ('H','R')
            or report.get('inventory_texts') is None or report.get('audio_lab') is None):raise ValueError('Complete modern ZK383 assembly required')
    if set(files)!=set(report['files']) or any(report['files'][n]!=fingerprint(r) for n,r in files.items()):
        raise ValueError('Changed modern ZK383 bundle')
    restore_audio(files['Tables/IngameSounds.def.disabled'],report['audio_lab']['transaction'])
    keys={'items':(item_layer,'tables/items.sav'),'fpv':('SabreSquadron.dta','tables/fpvanims.sav')}
    for key in keys.values():
        if key not in tables or (len(tables[key]),digest(tables[key]))!=TABLE_PINS[key]:raise ValueError('Changed ZK383 central table source')
    selected={n:tables[k] for n,k in keys.items()};composition=None
    gun=files['PROTOTYPE_ZK383.item.disabled'];ammo=files['PROTOTYPE_ZK3MAG.item.disabled']
    fragment=files[f"PROTOTYPE_ZK3P{report['hand_variant']}.fpvgroup.disabled"]
    if overlays is None:current,proof=build_pair(selected['items'],selected['fpv'],gun,fragment,ammo,weapon_slot=SLOT,ammo_slot=AMMO_SLOT)
    else:
        current,composition=compose(selected,overlays,gun,fragment,ammo,weapon_slot=SLOT,ammo_slot=AMMO_SLOT)
        proof=composition['transaction'];selected={**selected,**overlays}
    if restore_pair(current,proof)!=selected:raise ValueError('Modern ZK383 pair reversal differs')
    checked=[]
    for row in parse_items(current['items'])['slots']:
        if not row['present']:continue
        native=state_machine.inspect_record(current['items'][row['offset']:row['offset']+row['size']],row['slot'])
        if any(native.get(k) is not True for k in ('native_decode_matches','native_descriptor_measure_matches')):
            raise ValueError('Incomplete native ZK383 full-table descriptor verification')
        checked.append(row['slot'])
    traversal={'items':table_machine.inspect_table(current['items']),'fpv':fpv_machine.inspect_table(current['fpv'])}
    required={'items':('native_slot_loop_matches','native_loaded_descriptors_match','source_read_only_unchanged'),
        'fpv':('native_nested_traversal_matches','native_strings_and_values_match','source_read_only_unchanged','unpopulated_cells_unchanged')}
    for key,fields in required.items():
        if traversal[key].get('table_sha256')!=digest(current[key]) or any(traversal[key].get(f) is not True for f in fields):
            raise ValueError('Incomplete native ZK383 full-table traversal')
    requests=inspect_loaded_requests(fpv_machine,current['fpv'],SLOT)
    result={**files,'Tables/items.sav.disabled':current['items'],'Tables/FpvAnims.sav.disabled':current['fpv']}
    return result,{'schema_version':1,'scope':'private_disabled_zk383_full_tables','runtime_status':'pending',
        'descriptor_lab':report,'item_layer':item_layer,'hand_variant':report['hand_variant'],'transaction':proof,
        'central_table_overlay_composition':composition,'reverse_verified_in_memory':True,
        'native_descriptor_records_checked':len(checked),'native_descriptor_slots_checked':checked,
        'native_table_traversal':traversal,'native_animation_resource_requests':requests,
        'files':{n:fingerprint(r) for n,r in result.items()},
        'pending_requirements':[p for p in report['pending_requirements'] if p!='additive_weapon_and_ammunition_tables']
            +['isolated_file_deployment_transaction','other_resource_override_compatibility'],
        'sound_definition_reversal_verified':True,'ammunition_has_no_fpv_group':True,
        'global_slots_reserved':False,'installation_allowed':False,'game_started':False,'game_modified':False,'playable_weapon':False}


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
    parser.add_argument('--recipe',type=Path,default=RECIPE);parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--output-name',required=True);parser.add_argument('--item-layer',choices=('SabreSquadron.dta','PatchX01.dta'))
    parser.add_argument('--preserve-central-overrides',action='store_true');args=parser.parse_args(argv)
    try:
        if args.preserve_central_overrides and not args.item_layer:raise ValueError('Central overrides require an item layer')
        output=output_directory(args.output_name)
        if digest((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        tables,excluded=read_tables(args.game,archives_only=args.archives_only or args.preserve_central_overrides)
        definition,preflight=read_audio(args.game,archives_only=args.archives_only)
        hands,hand_excluded=read_hands(args.game,archives_only=args.archives_only);image=args.image.read_bytes();overlays=None
        inventory={'catalogue':json.loads(CATALOGUE.read_text(encoding='utf-8')),'sources':read_text_sources(args.game),
            'occupied_item_text_ids':occupied_item_text_ids(args.game,tables),'mission_range':(TEXT_ID_START,TEXT_ID_END)}
        recipes={case:json.loads(path.read_text(encoding='utf-8')) for case,path in RECIPES.items()}
        if args.preserve_central_overrides:
            from item_table_overlay import read_overlays
            overlays=read_overlays(args.game)
        source=HAND_MODELS[0 if args.hand=='H' else 1]
        files,report=prepare(tables,definition,recipes,json.loads(args.recipe.read_text(encoding='utf-8')),hands[source],args.bank,
            json.loads(args.profile.read_text(encoding='utf-8')),args.hand,StateOracle(image),SoundOracle(image),FpvResourceOracle(image),
            AnimationLoadOracle((args.game/'LS3DF.dll').read_bytes()),inventory=inventory)
        from item_secondary_oracle import SecondaryOracle,checked_action
        report['native_secondary_action']=checked_action(SecondaryOracle(image),files['PROTOTYPE_ZK383.item.disabled'],SLOT)
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
        print('Private modern ZK383 assembly refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
