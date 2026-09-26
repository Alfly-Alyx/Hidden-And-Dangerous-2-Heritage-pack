#!/usr/bin/env python3
"""Build a PRIVATE disabled Benelli descriptor/resource laboratory, not B2.

No items.sav or FpvAnims.sav is emitted. Slot 359 is only an emulator argument;
there is no installation, table insertion, saved-game access or game launch.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from item_weapon_descriptor import build_weapon,RAW_BASE,RAW_WEAPON
from item_native_layout import decode_record,fpv_native_projection
from items_sav import parse as parse_items,text_field
from fpv_table import parse as parse_fpv

ROOT=Path(__file__).resolve().parents[1]
SYNTHETIC_SLOT=359
MODEL_PINS={'PROTOTYPE_BenFPV':(61351,'0c54e499b6b6b434b3bdd02ed78cc2f7f99b304d44e162e11e787d323234300f'),
            'PROTOTYPE_BenM4':(207614,'6bc815610019739adc101d3e00319fa7819dd3d436b05e66d0521d258f291c8c')}
PENDING=('inventory_text_allocation','shoot_consumer_semantics_and_sound_ids',
         'secondary_mode_and_scalar_semantics','fpv_camera_hands_and_events',
         'complete_saved_game_compatibility','global_id_collision_clearance',
         'additive_table_transaction','engine_gameplay_and_multiplayer_tests')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def specification(shoot_fields,baseline):
    """Explicit modern baseline choice, not a recovered historical base record."""
    layout=decode_record(baseline)
    if layout['kind']!=1 or text_field(baseline,88)!='Side by Side':
        raise ValueError('Unexpected modern baseline owner')
    if [a['selector'] for a in layout['actions']]!=[4,5]:
        raise ValueError('Unexpected baseline action shape')
    secondary=layout['actions'][1];at=secondary['payload_offset']
    reserved,runtime_type,mode,scalar=struct.unpack_from('<IIIf',baseline,at)
    if (reserved,runtime_type,mode)!=(0,4,5):raise ValueError('Changed baseline secondary constants')
    members=layout['members']
    return {'provenance':'ASSEMBLAGE_MODERNE','status':'prototype_disabled','native_class':1,
            'names':{'internal':'MODERN_Benelli','fpv':'PROTOTYPE_BenFPV','icon':'wi_it-benelli','world':'PROTOTYPE_BenM4'},
            # Sentinel means UNRESOLVED, not an allocated translation or a
            # claim that the native inventory handles this value gracefully.
            'text_id':0xffffffff,'weight':struct.unpack_from('<f',baseline,112)[0],
            'base_members_raw':{m:members[f'0x{m:02x}']['value_raw'] for m in RAW_BASE},
            'weapon_members_raw':{m:179 if m==0x54 else members[f'0x{m:02x}']['value_raw'] for m in RAW_WEAPON},
            'primary':{'selector':4,'editor_fields':dict(shoot_fields)},
            'secondary':{'selector':5,'mode_raw':mode,'scalar':scalar}}


def isolated_fpv_group(source):
    from benelli_table_audit import benelli_group
    group=benelli_group(parse_fpv(source))
    raw=source[group['offset']:group['offset']+group['size']]
    # Retain the fully checked thirteen states. Only the owner ID is a modern
    # reassociation, and the group stays in a standalone disabled fragment.
    changed=struct.pack('<H',SYNTHETIC_SLOT+100)+raw[2:]
    result=struct.pack('<HI',12345,len(changed)+6)+changed
    projection=fpv_native_projection(parse_fpv(result))
    if projection['group_count']!=1 or projection['cell_count']!=52:
        raise ValueError('Invalid isolated FPV shape')
    return result


def output_directory(name,root=ROOT):
    if (not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',name)
            or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',name)):
        raise ValueError('Unsafe descriptor laboratory name')
    base=root/'.analysis'/'item-descriptor-labs';output=base/name
    for path in (root,root/'.analysis',base,output):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
            raise ValueError('Linked descriptor laboratory path')
    if output.exists():raise ValueError('Descriptor laboratory exists; use a fresh name')
    return output


def prepare(tables,sources,machine):
    from item_editor_table import require_row
    from benelli_fpv_static import derive
    from build_benelli_fpv_lab import native_assets
    data=tables['SabreSquadron.dta','tables/items.sav'];parsed=parse_items(data)
    if parsed['capacity']!=500 or parsed['slots'][SYNTHETIC_SLOT]['present']:
        raise ValueError('Synthetic candidate not empty in reviewed Sabre table')
    slot=parsed['slots'][23];baseline=data[slot['offset']:slot['offset']+slot['size']]
    row=require_row(tables['others.DTA','tables/item_shoot.tbl'],9,stride=135,name_column=2,name='Benelli')
    spec=specification(row['fields'],baseline);descriptor=build_weapon(spec)
    native=machine.inspect_record(descriptor,SYNTHETIC_SLOT)
    ammo=[]
    for archive in ('SabreSquadron.dta','PatchX01.dta'):
        if (archive,'tables/items.sav') not in tables:continue
        layer=tables[archive,'tables/items.sav'];slots=parse_items(layer)['slots']
        if slots[SYNTHETIC_SLOT]['present']:raise ValueError('Synthetic candidate occupied in an item layer')
        source=slots[179]
        if (source.get('kind'),source.get('internal_name'))!=(0,'AMMO Beneli'):
            raise ValueError('Unexpected ammunition owner')
        raw=layer[source['offset']:source['offset']+source['size']]
        ammo.append({'archive':archive,**machine.ammo_binding(descriptor,raw,weapon_slot=SYNTHETIC_SLOT,ammo_slot=179)})
    bindings=[machine.fpv_binding(SYNTHETIC_SLOT,state) for state in range(13)]
    derived,_=derive(sources['models/#fpvbeneliaim.4ds'])
    models,model_report=native_assets(derived)
    for name,raw in models.items():
        if (len(raw),sha(raw))!=MODEL_PINS[name]:raise ValueError('Changed prepared model: '+name)
    group=isolated_fpv_group(tables['SabreSquadron.dta','tables/fpvanims.sav'])
    files={'PROTOTYPE_Benelli.item.disabled':descriptor,'PROTOTYPE_Benelli.fpvgroup.disabled':group,
           **{name+'.4ds.disabled':raw for name,raw in models.items()}}
    report={'schema_version':1,'scope':'private_disabled_benelli_descriptor_lab',
            'provenance':'ASSEMBLAGE_MODERNE_RESSOURCES_MIXTES',
            'source_pins':{archive+'::'+name:{'size':len(raw),'sha256':sha(raw)} for (archive,name),raw in tables.items()},
            'modern_design_decisions':{
                'baseline_owner':'Sabre Side by Side, slot 23; individual live attributes only',
                'baseline_record_sha256':sha(baseline),'baseline_weight':spec['weight'],
                'adopted_raw_base_members':{hex(k):v for k,v in spec['base_members_raw'].items()},
                'adopted_weapon_members':{hex(k):v for k,v in spec['weapon_members_raw'].items()},
                'secondary':spec['secondary'],'internal_name':spec['names']['internal'],
                'text_id':spec['text_id'],'text_id_allocated':False,
                'opaque_bytes_policy':'modern_zero_fill_not_historical_reconstruction',
                'historical_base_record_recovered':False,'whole_donor_record_copied':False},
            'historical_shoot_row_sha256':row['sha256'],'native_descriptor':native,
            'native_ammunition_checks':ammo,'native_fpv_binding_checks':bindings,
            'model_references':model_report,'icon':{'stem':'wi_it-benelli','source':'maps/wi_it-benelli.bmp','sha256':sha(sources['maps/wi_it-benelli.bmp'])},
            'fpv_group':{'owner':SYNTHETIC_SLOT+100,'size':len(group),'sha256':sha(group),'commercial_group_109_preserved':True},
            'files':{name:{'size':len(raw),'sha256':sha(raw)} for name,raw in files.items()},
            'pending_requirements':list(PENDING),'complete_binary_descriptor_built':True,
            'game_started':False,'game_modified':False,'central_tables_modified':False,
            'item_slot_allocated':False,'playable_weapon':False,'runtime_status':'pending',
            'full_save_compatibility_qualified':False}
    return files,report


def main(argv=None):
    from benelli_table_audit import read_tables
    from build_benelli_fpv_lab import read_sources,MANIFEST
    from item_state_oracle import StateOracle
    from item_native_contract import SOURCE_SHA
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--output-name')
    args=parser.parse_args(argv)
    try:
        output=output_directory(args.output_name) if args.output_name else None
        if sha((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        tables,excluded=read_tables(args.game,archives_only=args.archives_only)
        source_manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
        sources,source_excluded=read_sources(args.game,source_manifest,archives_only=args.archives_only)
        machine=StateOracle(args.image.read_bytes())
        files,report=prepare(tables,sources,machine)
        report['resource_source_pins']=source_manifest['sources']
        report['excluded_loose_overrides']={**excluded,**source_excluded}
        if output:
            output.mkdir(parents=True,exist_ok=False)
            for name,raw in files.items():
                with (output/name).open('xb') as stream:stream.write(raw)
            with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
            with (output/'LIRE_AVANT_ESSAI.txt').open('x',encoding='utf-8') as stream:
                stream.write('ASSEMBLAGE MODERNE, RESSOURCES COMMERCIALES DERIVEES: USAGE PRIVE.\n'
                    'Ce dossier ne peut pas etre installe: libelle, contrats et integration incomplets.\n'
                    'Aucune entree allouee. Ni sauvegarde complete, ni comportement de jeu valide.\n'
                    'Les fichiers restent disabled. Ne pas redistribuer les modeles derives.\n')
        print(json.dumps({'output':str(output) if output else None,'files':report['files'],
                          'native_ammunition_checks':report['native_ammunition_checks'],
                          'fpv_states_checked':len(report['native_fpv_binding_checks']),
                          'pending_requirements':report['pending_requirements'],'playable_weapon':False},indent=2))
        return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Benelli descriptor laboratory refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
