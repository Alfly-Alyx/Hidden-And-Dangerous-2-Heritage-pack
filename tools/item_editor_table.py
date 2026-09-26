"""Original read-only codec for the reviewed uniform-row LS3D v7 item tables.

Column IDs/types/offsets come from the file, not string proximity or guessed
record boundaries. Names and gameplay meanings of numeric columns are NOT
inferred. Mixed arrays, gaps, overlaps and unreviewed field types are refused.
This restricted decoder is not a general LS3D table editor.
"""
import hashlib
import math
import struct

MAGIC=0x14448408
FIELD_SIZES={3:1,4:4,5:4,6:8,7:16,18:4}


def parse(data):
    if len(data)<24:raise ValueError('Truncated item-editor table header')
    magic,version,flags,count,data_size,reserved=struct.unpack_from('<6I',data)
    if magic!=MAGIC or version!=7 or reserved!=0 or not 1<=count<=512:
        raise ValueError('Unreviewed item-editor table header')
    start=24+12*count
    if start+data_size!=len(data):raise ValueError('Item-editor table size mismatch')
    columns=[]
    for index in range(count):
        field,offset,rows,stride,kind=struct.unpack_from('<HIHHH',data,24+12*index)
        if kind not in FIELD_SIZES or rows==0 or stride==0 or rows*stride!=data_size:
            raise ValueError('Unreviewed column type or mixed item-editor array')
        columns.append({'id':field,'offset':offset,'row_count':rows,'row_stride':stride,
                        'type_raw':kind,'size':FIELD_SIZES[kind]})
    if len({c['id'] for c in columns})!=count:raise ValueError('Duplicate item-editor column ID')
    if len({(c['row_count'],c['row_stride']) for c in columns})!=1:
        raise ValueError('Mixed item-editor row shapes')
    cursor=0
    for column in sorted(columns,key=lambda c:c['offset']):
        if column['offset']!=cursor:raise ValueError('Gap or overlap in item-editor row')
        cursor+=column['size']
    rows,stride=columns[0]['row_count'],columns[0]['row_stride']
    if cursor!=stride:raise ValueError('Item-editor row not completely covered')
    decoded=[]
    for index in range(rows):
        offset=start+index*stride;raw=data[offset:offset+stride];values={}
        for column in columns:
            at,kind=column['offset'],column['type_raw']
            if kind==3:
                value=raw[at]
                if value not in (0,1):raise ValueError('Noncanonical item-editor boolean')
            elif kind in (4,18):value=struct.unpack_from('<I',raw,at)[0]
            elif kind==5:
                value=struct.unpack_from('<f',raw,at)[0]
                if not math.isfinite(value):raise ValueError('Non-finite item-editor scalar')
            else:
                part=raw[at:at+column['size']]
                if b'\0' not in part:raise ValueError('Unterminated item-editor string')
                visible=part.split(b'\0',1)[0]
                if any(b<32 for b in visible):raise ValueError('Control byte in item-editor string')
                try:value=visible.decode('cp1252')
                except UnicodeDecodeError as error:raise ValueError('Invalid item-editor string encoding') from error
            values[column['id']]=value
        decoded.append({'index':index,'offset':offset,'size':stride,
                        'sha256':hashlib.sha256(raw).hexdigest(),'fields':values})
    return {'version':version,'opaque_header_flags':flags,'size':len(data),
            'sha256':hashlib.sha256(data).hexdigest(),'data_offset':start,
            'data_size':data_size,'column_count':count,'columns':columns,
            'row_count':rows,'row_stride':stride,'rows':decoded,
            'gameplay_field_names_qualified':False}


def require_row(data,index,*,stride,name_column,name):
    parsed=parse(data)
    if type(index) is not int or not 0<=index<parsed['row_count'] or parsed['row_stride']!=stride:
        raise ValueError('Item-editor row outside expected shape')
    row=parsed['rows'][index]
    if row['fields'].get(name_column)!=name:raise ValueError('Item-editor row has a different owner')
    return row
