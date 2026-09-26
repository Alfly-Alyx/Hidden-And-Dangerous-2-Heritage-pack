#!/usr/bin/env python3
"""Read central Benelli/compass/FPV tables; never allocate, patch, or launch."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

from dta_archive import DtaArchive
from items_sav import parse as parse_items, candidate_status
from fpv_table import parse as parse_fpv
from asset_presence_audit import benelli_shoot_evidence,benelli_compass_evidence,BENELLI_COMPASS_SHA256,BENELLI_SHOOT_SHA256

TABLE_PINS={
 ('others.DTA','tables/items.sav'):(128520,'9e82e40543e3c5b65d6004f2d45fac656d1e4f5a8df5259a3a0db2520c5983b6'),
 ('Patch.dta','tables/items.sav'):(128520,'9dbad22a089489eb4bf2e7600f7b88d6be5ffc6104146b1872080c41c60a92f0'),
 ('SabreSquadron.dta','tables/items.sav'):(252000,'8da3655f438cfe73c539a81e0a9abada1488042677675ac56fbdf5597e2176b9'),
 ('PatchX01.dta','tables/items.sav'):(252000,'10fa461d6116c7463fcdb46c404c67af495585b82a574656a72e85f37964b20c'),
 ('others.DTA','tables/fpvanims.sav'):(116783,'baa65d47ffa8cf49f8e8b87c2b14333f81e3a546e89f86507308573971ead3ff'),
 ('SabreSquadron.dta','tables/fpvanims.sav'):(127158,'421c50251277b8f316535c430bf35dd1fcfb36a5a1a59cd0aee974fa63bedb1a'),
 ('others.DTA','tables/item_shoot.tbl'):(34761,'9a0cad7b898549e2a3f61a78c9f5b9b1d937ed3b91dc6f659de1d62518b97f0a'),
 ('SabreSquadron.dta','tables/item_base_items.tbl'):(66788,'96e0a379dcc249e7c9d58b08529987e1bacf8d543b99c702bf3011b5aeb3e8e3'),
}
EXPECTED_STATES=('Idle1','Idle1','Shot','Shot','AimShot','AimShot','Rel','Jammed','Arm','Disarm','Disarm','Aim','Daim')
PROTECTED_COMPASS=9


def sha(raw):return hashlib.sha256(raw).hexdigest()


def read_tables(game,*,archives_only=False):
    tables={};excluded={};wanted={name for _,name in TABLE_PINS}
    for archive_name in ('others.DTA','Patch.dta','SabreSquadron.dta','PatchX01.dta'):
        path=game/archive_name
        if archive_name=='PatchX01.dta' and not path.exists():continue
        with DtaArchive(path) as archive:
            seen=set()
            for entry in archive.entries:
                name=entry.name.replace('\\','/').casefold()
                if name not in wanted:continue
                key=(archive_name,name)
                if name in seen or key not in TABLE_PINS:
                    raise ValueError('Unreviewed or duplicate central table layer: '+archive_name+'::'+name)
                seen.add(name);raw=archive.read(entry);size,digest=TABLE_PINS[key]
                if len(raw)!=size or sha(raw)!=digest:raise ValueError('Changed central table: '+archive_name+'::'+name)
                tables[key]=raw
    required={key for key in TABLE_PINS if key[0]!='PatchX01.dta' or (game/'PatchX01.dta').exists()}
    if set(tables)!=required:raise ValueError('Missing central table source')
    for name in sorted(wanted):
        loose=game.joinpath(*name.split('/'))
        if loose.exists():
            if not archives_only:raise ValueError('Loose central table override: '+name)
            raw=loose.read_bytes();excluded[name]={'size':len(raw),'sha256':sha(raw)}
    return tables,excluded


def benelli_group(parsed):
    matches=[g for g in parsed['groups'] if any('beneli' in v['name'].casefold()
             for s in g['states'] for c in s['channels'] for v in c['variants'])]
    if len(matches)!=1 or matches[0]['id']!=109:raise ValueError('Ambiguous Benelli FPV group')
    group=matches[0]
    if [s['id'] for s in group['states']]!=list(range(2000,2013)):
        raise ValueError('Changed Benelli FPV state IDs')
    for state,suffix in zip(group['states'],EXPECTED_STATES):
        channels={c['id']:c['variants'] for c in state['channels']}
        if (channels.get(3000)!=[{'name':'#FPVBeneli'+suffix+'.I3D','value_raw':100}]
                or any(channels.get(i)!=[] for i in (3001,3002,3003))):
            raise ValueError('Changed Benelli FPV resource associations')
    return group


def inspect(tables,candidate,excluded):
    if type(candidate) is not int or not 0<=candidate<=0xffffffff:raise ValueError('Invalid candidate ItemID')
    item_tables={};fpv_tables={}
    for (archive,name),raw in tables.items():
        if name=='tables/items.sav':
            parsed=parse_items(raw,capacity=255 if archive in ('others.DTA','Patch.dta') else 500)
            for slot_id,kind,label,text_id in ((9,2,'KOMPAS',1009),(10,1,'M1 Garand',1010),
                    (23,1,'Side by Side',1023),(179,0,'AMMO Beneli',1179)):
                slot=parsed['slots'][slot_id]
                if (slot.get('kind'),slot.get('internal_name'),slot.get('text_id'))!=(kind,label,text_id):
                    raise ValueError('Central item control changed')
            item_tables[archive]={k:v for k,v in parsed.items() if k!='slots'}
            item_tables[archive].update(candidate=candidate_status(parsed,candidate),
                        controls=[parsed['slots'][i] for i in (9,10,23,179)],
                        occupied_slots=[s['slot'] for s in parsed['slots'] if s['present']])
        if name=='tables/fpvanims.sav':
            parsed=parse_fpv(raw);group=benelli_group(parsed)
            ids={g['id'] for g in parsed['groups']}
            fpv_tables[archive]={'size':parsed['size'],'sha256':parsed['sha256'],'group_count':len(ids),
                'benelli_group':group,'same_numeric_group_as_candidate_present':candidate in ids,
                'candidate_plus_100_group_present':candidate+100 in ids,
                'candidate_plus_100_is_binding_hypothesis_only':True,
                'event_semantics_qualified':False,'weapon_binding_qualified':False}
    shoot=benelli_shoot_evidence(tables[('others.DTA','tables/item_shoot.tbl')])
    compass=benelli_compass_evidence(tables[('SabreSquadron.dta','tables/item_base_items.tbl')])
    if not shoot['header_ok'] or shoot['sha256']!=BENELLI_SHOOT_SHA256:raise ValueError('Changed Benelli shoot record')
    if compass['sha256']!=BENELLI_COMPASS_SHA256:raise ValueError('Changed compass table record')
    return {'schema_version':1,'scope':'central_tables_only','sources':{
        archive+'::'+name:{'size':len(raw),'sha256':sha(raw)} for (archive,name),raw in tables.items()},
        'candidate_item_id':candidate,'item_tables':item_tables,'fpv_tables':fpv_tables,
        'shoot_record':shoot,'protected_compass_record':compass,
        'excluded_loose_overrides':excluded,'source_mode':'reviewed_commercial_archives',
        'last_reviewed_item_layer':'PatchX01.dta' if 'PatchX01.dta' in item_tables else 'SabreSquadron.dta',
        'mission_collision_audit_included':False,'saved_game_audit_included':False,
        'item_slot_allocated':False,'allocation_allowed':False,'tables_modified':False,
        'save_compatibility_qualified':False,'runtime_status':'pending',
        'next_requirements':['mission_and_override_collision_audit','save_serialization_contract',
                             'weapon_to_fpv_binding','ammo_binding','shoot_field_semantics']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--candidate',type=int,default=359)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report already exists; use a fresh path')
        tables,excluded=read_tables(args.game,archives_only=args.archives_only)
        report=inspect(tables,args.candidate,excluded)
        rendered=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:stream.write(rendered)
        print(rendered)
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Central table audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
