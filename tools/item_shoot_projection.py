#!/usr/bin/env python3
"""Project editor shoot fields onto reviewed selector-4 bytes, without allocation.

This is a bounded format correspondence, not a gameplay or timing specification.
No donor record is copied and no item/save/game table is written.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys

# Offsets relative to the 128-byte serialized action payload; the native loader
# copies its first 88 bytes. Three padding bytes and stale string suffixes are
# never compared. The last forty bytes remain unqualified editor-only data.
FIELDS=((2,76,'text8'),(3,36,'u32'),(4,8,'f32'),(6,12,'f32'),
        (8,16,'decimal'),(10,40,'decimal'),(12,24,'u32'),
        (24,44,'times1000'),(26,48,'f32'),(28,52,'f32'),(30,56,'f32'),
        (38,20,'times1000'),(40,60,'f32'),(42,64,'times_f32_percent'),
        (46,84,'f32'),(58,28,'bool8'),(77,68,'u32'),(79,72,'u32'))
CONSTANTS={0:0,4:3,32:0}
UNLINKED_COLUMNS=(1,81,84,86,88,92,94,98)
PERCENT=struct.unpack('<f',struct.pack('<f',.01))[0]


def f32(value):
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValueError('Expected finite shoot scalar')
    try:result=struct.pack('<f',value)
    except (OverflowError,struct.error) as error:raise ValueError('Shoot scalar outside float32') from error
    if not math.isfinite(struct.unpack('<f',result)[0]):raise ValueError('Nonfinite float32 projection')
    return result


def u32(value):
    if type(value) is not int or not 0<=value<=0xffffffff:
        raise ValueError('Expected unsigned shoot integer')
    return struct.pack('<I',value)


def encode_field(value,kind):
    if kind=='text8':
        if not isinstance(value,str) or not value or any(ord(c)<32 for c in value):
            raise ValueError('Invalid shoot label')
        try:raw=value.encode('cp1252')
        except UnicodeEncodeError as error:raise ValueError('Unencodable shoot label') from error
        if len(raw)>7:raise ValueError('Shoot label exceeds eight-byte terminated field')
        return raw+b'\0' # Stale bytes after the first NUL are not live text.
    if kind=='decimal':
        if not isinstance(value,str) or not re.fullmatch(r'(?:-1|0|[1-9][0-9]*)',value):
            raise ValueError('Only one canonical decimal shoot reference is supported')
        number=int(value)
        return u32(0xffffffff if number==-1 else number)
    if kind=='u32':return u32(value)
    if kind=='bool8':
        if type(value) is not int or value not in (0,1):raise ValueError('Invalid shoot boolean')
        return bytes([value])
    if kind not in ('f32','times1000','times_f32_percent'):
        raise ValueError('Unknown shoot conversion')
    # Source is a float32 column. Multiplication uses its decoded float value
    # and the explicit single-precision constant observed across all 40 rows.
    source=struct.unpack('<f',f32(value))[0]
    if kind=='times1000':source*=1000
    if kind=='times_f32_percent':source*=PERCENT
    return f32(source)


def projection(fields,*,omit_symbolic=False):
    """Return sparse reviewed spans, not a full action/item serialization."""
    if not isinstance(fields,dict) or any(column not in fields for column,_,_ in FIELDS):
        raise ValueError('Missing editor shoot columns')
    spans=[]
    for column,offset,kind in FIELDS:
        value=fields[column]
        if (omit_symbolic and kind=='decimal' and isinstance(value,str)
                and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,14}',value)):
            continue
        spans.append({'column':column,'offset':offset,'raw':encode_field(value,kind),'conversion':kind})
    spans.extend({'column':None,'offset':offset,'raw':u32(value),'conversion':'observed_constant'}
                 for offset,value in CONSTANTS.items())
    occupied=set()
    for span in spans:
        area=set(range(span['offset'],span['offset']+len(span['raw'])))
        if occupied&area or max(area)>=88:raise ValueError('Overlapping shoot projection')
        occupied|=area
    return spans


def compare(fields,payload):
    if not isinstance(payload,bytes) or len(payload)!=128:
        raise ValueError('Expected one full selector-4 serialized payload')
    checks=[]
    for span in projection(fields):
        at=span['offset'];width=len(span['raw'])
        checks.append({'column':span['column'],'offset':at,'size':width,
                       'conversion':span['conversion'],'matches':payload[at:at+width]==span['raw']})
    return {'checks':checks,'all_reviewed_fields_match':all(c['matches'] for c in checks),
            'different_columns':[c['column'] for c in checks if not c['matches']],
            'payload_sha256':hashlib.sha256(payload).hexdigest(),
            'unlinked_editor_columns':list(UNLINKED_COLUMNS),
            'padding_and_stale_suffix_compared':False,'gameplay_semantics_qualified':False}


def inspect(tables):
    from item_editor_table import parse as parse_editor
    from items_sav import parse as parse_items
    from item_native_layout import decode_record
    editor=tables['others.DTA','tables/item_shoot.tbl']
    rows=parse_editor(editor)['rows']
    base=tables['others.DTA','tables/items.sav']
    selected=[]
    for slot in parse_items(base)['slots']:
        if not slot['present'] or slot['kind']!=1:continue
        raw=base[slot['offset']:slot['offset']+slot['size']]
        if decode_record(raw)['actions'][0]['selector']==4:selected.append(slot['slot'])
    if len(selected)!=40:raise ValueError('Changed forty-record control set')
    expected={'others.DTA':{},'Patch.dta':{},'SabreSquadron.dta':{5:[24],23:[28]},
              'PatchX01.dta':{5:[24],23:[28],26:[6,26,28],28:[6,28,30,40]}}
    layers={}
    for (archive,name),data in tables.items():
        if name!='tables/items.sav':continue
        parsed=parse_items(data);results=[]
        for index in selected:
            slot=parsed['slots'][index]
            if not slot['present'] or slot['kind']!=1:raise ValueError('Changed native shoot owner')
            raw=data[slot['offset']:slot['offset']+slot['size']]
            action=decode_record(raw)['actions'][0]
            if action['selector']!=4:raise ValueError('Changed primary action selector')
            payload=raw[action['payload_offset']:action['payload_offset']+128]
            row=rows[index]
            result=compare(row['fields'],payload)
            difference=result['different_columns']
            if None in difference or sorted(difference)!=expected[archive].get(index,[]):
                raise ValueError(f'Unreviewed shoot projection difference: {archive} item {index}')
            results.append({'slot':index,'editor_row_sha256':row['sha256'],
                            'native_record_sha256':slot['sha256'],**result})
        layers[archive]={'table_sha256':hashlib.sha256(data).hexdigest(),
                         'records':results,'matching_records':sum(r['all_reviewed_fields_match'] for r in results),
                         'changed_columns':{str(r['slot']):r['different_columns'] for r in results if not r['all_reviewed_fields_match']}}
    candidates=[]
    for index,name in ((9,'Benelli'),(27,'FG 42'),(32,'MG 34')):
        row=rows[index]
        if row['fields'][2]!=name:raise ValueError('Changed orphan shoot owner')
        spans=projection(row['fields'],omit_symbolic=True)
        covered={s['column'] for s in spans}
        unresolved=[{'column':column,'symbol':row['fields'][column]}
                    for column,_,_ in FIELDS if column not in covered]
        candidates.append({'editor_row':index,'name':name,'row_sha256':row['sha256'],
                           'reviewed_spans':len(spans),'covered_bytes':sum(len(s['raw']) for s in spans),
                           'unresolved_symbolic_references':unresolved,
                           'projection_sha256':hashlib.sha256(b''.join(struct.pack('<II',s['offset'],len(s['raw']))+s['raw'] for s in spans)).hexdigest(),
                           'commercial_weapon_record_present':False,'complete_descriptor_built':False})
    return {'schema_version':1,'scope':'editor_to_primary_action_sparse_projection',
            'shoot_table_sha256':hashlib.sha256(editor).hexdigest(),
            'mapped_source_columns':len(FIELDS),'unlinked_columns':list(UNLINKED_COLUMNS),
            'layers':layers,'orphan_projections':candidates,
            'float32_percent_constant':PERCENT,
            'tables_modified':False,'item_slot_allocated':False,'saved_games_opened':False,
            'game_started':False,'gameplay_semantics_qualified':False,
            'full_weapon_descriptor_built':False}


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
        print(json.dumps({'mapped_columns':len(FIELDS),'layers':{
            key:{'checked':len(value['records']),'matching':value['matching_records'],
                 'changed_columns':value['changed_columns']} for key,value in report['layers'].items()},
            'orphan_projections':report['orphan_projections'],'gameplay_semantics_qualified':False},indent=2))
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Shoot projection refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
