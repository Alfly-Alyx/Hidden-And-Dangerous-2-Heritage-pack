#!/usr/bin/env python3
"""Sparse editor-to-item correspondence. No donor, allocation or game writes.

The native class is an explicit input, NEVER inferred from editor enums. Action
row references and opaque bytes are not silently filled into a new descriptor.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from item_native_layout import ACTION_SIZES, decode_record
from item_shoot_projection import f32, u32

TEXT_FIELDS=((2,88),(6,8),(8,28),(10,48))
SCALAR_FIELDS=((11,68),(4,108),(12,112),(14,116),(44,120),
               (46,124),(48,128),(50,132))
NO_AMMO_SLOTS=(38,56,57,60,61,62,63,65,66,70,71)
UNKNOWN_QUANTITY_SLOTS=(207,208)


def text16(value):
    if not isinstance(value,str) or any(ord(c)<32 for c in value):
        raise ValueError('Invalid base-editor text')
    try:raw=value.encode('cp1252')
    except UnicodeEncodeError as error:raise ValueError('Unencodable base-editor text') from error
    if len(raw)>15:raise ValueError('Base-editor text exceeds terminated sixteen-byte field')
    return raw+b'\0' # Visible prefix only: editor/native stale suffixes differ.


def projection(fields,*,kind):
    if not isinstance(fields,dict) or type(fields.get(1)) is not int or fields[1] not in (0,1):
        raise ValueError('Expected explicit base-editor presence')
    spans=[{'column':1,'offset':0,'raw':u32(fields[1]),'conversion':'presence'}]
    if fields[1]==0:
        if kind is not None:raise ValueError('An empty slot has no native class')
        return spans
    if type(kind) is not int or kind not in (0,1,2):
        raise ValueError('Native class must be provided explicitly')
    derived_columns={0:(26,),1:(5,39,40,24),2:(5,39,40)}[kind]
    required={c for c,_ in TEXT_FIELDS+SCALAR_FIELDS}|{16,20}|set(derived_columns)
    if not required<=fields.keys():raise ValueError('Missing base-editor columns')
    for column,offset in TEXT_FIELDS:
        spans.append({'column':column,'offset':offset,'raw':text16(fields[column]),'conversion':'text16_visible'})
    for column,offset in SCALAR_FIELDS:
        raw=f32(fields[column]) if column==12 else u32(fields[column])
        if column==12 and fields[column]<0:raise ValueError('Negative item weight')
        spans.append({'column':column,'offset':offset,'raw':raw,'conversion':'f32' if column==12 else 'u32'})
    offset=136
    for column in (16,20):
        selector=fields[column]
        if type(selector) is not int or not 0<=selector<len(ACTION_SIZES):
            raise ValueError('Unreviewed action selector')
        spans.append({'column':column,'offset':offset,'raw':u32(selector),'conversion':'selector'})
        offset+=4+ACTION_SIZES[selector]
    offset+=32
    for column in derived_columns:
        spans.append({'column':column,'offset':offset,'raw':f32(fields[column]) if kind==0 else u32(fields[column]),
                      'conversion':'f32' if kind==0 else 'u32'})
        offset+=4
    occupied=set()
    for span in spans:
        area=set(range(span['offset'],span['offset']+len(span['raw'])))
        if occupied&area or max(area)>=508:raise ValueError('Overlapping base projection')
        occupied|=area
    return spans


def compare(fields,raw):
    if not isinstance(raw,bytes) or len(raw) not in (4,508):
        raise ValueError('Expected an immutable empty or present item record')
    if len(raw)==4:
        if raw!=bytes(4) or fields.get(1)!=0:raise ValueError('Presence mismatch')
        layout=None;kind=None
    else:
        layout=decode_record(raw);kind=layout['kind']
        if fields.get(1)!=1:raise ValueError('Presence mismatch')
        if [fields.get(c) for c in (16,20)]!=[a['selector'] for a in layout['actions']]:
            raise ValueError('Action shape differs; refusing shifted field comparison')
    checks=[]
    for span in projection(fields,kind=kind):
        at=span['offset'];width=len(span['raw'])
        checks.append({'column':span['column'],'offset':at,'size':width,
                       'matches':raw[at:at+width]==span['raw'],'conversion':span['conversion']})
    return {'native_class':kind,'checks':checks,
            'all_reviewed_fields_match':all(c['matches'] for c in checks),
            'different_columns':[c['column'] for c in checks if not c['matches']],
            'record_sha256':hashlib.sha256(raw).hexdigest(),
            'action_rows_not_resolved':{str(c):fields.get(c) for c in (18,22)} if layout else {},
            'native_class_inferred_from_editor':False,'opaque_bytes_compared':False,
            'generic_members_0x60_0x64_qualified':False,'complete_descriptor_built':False}


def inspect(tables):
    from item_editor_table import parse as parse_editor
    from items_sav import parse as parse_items
    editor=tables['SabreSquadron.dta','tables/item_base_items.tbl']
    parsed_editor=parse_editor(editor)
    if (parsed_editor['row_count'],parsed_editor['row_stride'])!=(500,133):
        raise ValueError('Changed base-editor shape')
    layers={}
    for archive in ('SabreSquadron.dta','PatchX01.dta'):
        if (archive,'tables/items.sav') not in tables:
            if archive=='PatchX01.dta':continue
            raise ValueError('Missing Sabre item table')
        data=tables[archive,'tables/items.sav'];parsed=parse_items(data,capacity=500)
        results=[]
        for slot in parsed['slots']:
            row=parsed_editor['rows'][slot['slot']];fields=row['fields']
            raw=data[slot['offset']:slot['offset']+slot['size']]
            result=compare(fields,raw);expected=[]
            if slot['slot'] in NO_AMMO_SLOTS:
                expected=[24];layout=decode_record(raw)
                if layout['kind']!=1 or fields[24]!=0 or layout['members']['0x54']['value_raw']!=0xffffffff:
                    raise ValueError('Changed explicit no-ammo exception')
            if slot['slot'] in UNKNOWN_QUANTITY_SLOTS:
                expected=[26];layout=decode_record(raw)
                if layout['kind']!=0 or fields[26]!=0 or layout['members']['0x54']['value_raw']!=0xbf800000:
                    raise ValueError('Changed explicit unknown-quantity exception')
            if result['different_columns']!=expected:
                raise ValueError(f'Unreviewed base projection difference: {archive} item {slot["slot"]}')
            results.append({'slot':slot['slot'],'present':slot['present'],'editor_row_sha256':row['sha256'],
                            'reviewed_exception_preserved':bool(expected),**result})
        layers[archive]={'records':results,'present_records':parsed['present_slots'],
                         'empty_slots':500-parsed['present_slots'],
                         'matching_present_records':sum(r['present'] and r['all_reviewed_fields_match'] for r in results),
                         'reviewed_exceptions':{str(r['slot']):r['different_columns'] for r in results if r['different_columns']}}
    return {'schema_version':1,'scope':'sabre_base_editor_sparse_projection',
            'editor_sha256':hashlib.sha256(editor).hexdigest(),'layers':layers,
            'base_and_patch_projection_qualified':False,
            'native_class_inferred_from_editor':False,'tables_modified':False,
            'game_started':False,'item_slot_allocated':False,'complete_descriptor_built':False}


def main(argv=None):
    from benelli_table_audit import read_tables
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Use a fresh report path')
        tables,excluded=read_tables(args.game,archives_only=args.archives_only)
        report=inspect(tables);report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({name:{k:v for k,v in layer.items() if k!='records'} for name,layer in report['layers'].items()},indent=2))
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Base projection refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
