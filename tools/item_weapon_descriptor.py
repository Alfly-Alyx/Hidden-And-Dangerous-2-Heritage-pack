"""Original assembly of ONE disabled modern weapon descriptor, never a table.

Inputs name every live common/derived member explicitly. Unmapped bytes are
zero-filled as a MODERN serialization policy, not recovered historical data.
This module does not choose item/text IDs, resolve resources, copy donor bytes,
write files, install anything or claim weapon/game-save compatibility.
"""
from __future__ import annotations
import struct
import re

from item_native_layout import BASE_MEMBERS,decode_record
from item_shoot_projection import f32,u32,projection as shoot_projection
from items_sav import model_name_field

RAW_BASE=(0x0c,0x1c,0x38,0x3c,0x40,0x44)
RAW_WEAPON=(0x58,0x5c,0x60,0x54)
SPEC_KEYS={'provenance','status','native_class','names','text_id','weight',
           'base_members_raw','weapon_members_raw','primary','secondary'}


def exact_keys(mapping,keys,label):
    if not isinstance(mapping,dict) or set(mapping)!=set(keys):
        raise ValueError('Expected exact '+label+' keys')


def resource_field(value,*,icon=False):
    if not isinstance(value,str):raise ValueError('Expected an explicit resource string')
    if not value:return bytes(20)
    if icon:
        # Commercial icon stems include hyphens; models retain the narrower
        # previously reviewed convention. Neither accepts paths/extensions.
        if (not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,18}',value)
                or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',value)):
            raise ValueError('Unsafe icon stem')
        return value.encode('ascii').ljust(20,b'\0')
    return model_name_field(value)


def shoot_action(fields):
    """Selector 4. Symbolic references are refused, not converted to zero."""
    payload=bytearray(128)
    for span in shoot_projection(fields):
        at=span['offset'];payload[at:at+len(span['raw'])]=span['raw']
    return bytes(payload)


def secondary_action(mode_raw,scalar):
    """Selector 5, constructor type 4. Mode and scalar meanings stay unqualified."""
    value=f32(scalar)
    if struct.unpack('<f',value)[0]<=0:raise ValueError('Expected positive secondary scalar')
    return u32(0)+u32(4)+u32(mode_raw)+value


def build_weapon(spec):
    exact_keys(spec,SPEC_KEYS,'modern weapon specification')
    if (spec['provenance']!='ASSEMBLAGE_MODERNE' or spec['status']!='prototype_disabled'
            or type(spec['native_class']) is not int or spec['native_class']!=1):
        raise ValueError('Only an explicitly disabled modern Weapon assembly is supported')
    names=spec['names'];exact_keys(names,('internal','fpv','icon','world'),'weapon name')
    if not isinstance(names['internal'],str) or not names['internal'].startswith('MODERN_'):
        raise ValueError('Modern internal name must remain visibly identified')
    encoded_names={key:resource_field(value,icon=key=='icon') for key,value in names.items()}
    raw_members=spec['base_members_raw'];weapon=spec['weapon_members_raw']
    exact_keys(raw_members,RAW_BASE,'raw base member');exact_keys(weapon,RAW_WEAPON,'raw weapon member')
    primary=spec['primary'];secondary=spec['secondary']
    exact_keys(primary,('selector','editor_fields'),'primary action')
    if type(primary['selector']) is not int or primary['selector']!=4:
        raise ValueError('Only reviewed primary selector 4 can be assembled')
    primary_bytes=shoot_action(primary['editor_fields'])
    if not isinstance(secondary,dict) or type(secondary.get('selector')) is not int:
        raise ValueError('Expected explicit secondary selector')
    if secondary['selector']==0:
        exact_keys(secondary,('selector',),'absent secondary');secondary_bytes=b''
    elif secondary['selector']==5:
        exact_keys(secondary,('selector','mode_raw','scalar'),'secondary action')
        secondary_bytes=secondary_action(secondary['mode_raw'],secondary['scalar'])
    else:raise ValueError('Unreviewed secondary action shape')
    weight=f32(spec['weight'])
    if struct.unpack('<f',weight)[0]<0:raise ValueError('Negative weapon weight')
    raw=bytearray(508)
    struct.pack_into('<II',raw,0,1,1)
    for name,offset in (('fpv',8),('icon',28),('world',48),('internal',88)):
        raw[offset:offset+20]=encoded_names[name]
    raw[108:112]=u32(spec['text_id']);raw[112:116]=weight
    for offset,member in BASE_MEMBERS.items():
        if member in RAW_BASE:raw[offset:offset+4]=u32(raw_members[member])
    offset=136
    for selector,payload in ((4,primary_bytes),(secondary['selector'],secondary_bytes)):
        raw[offset:offset+4]=u32(selector);offset+=4
        raw[offset:offset+len(payload)]=payload;offset+=len(payload)
    offset+=32 # Opaque native base gap: modern zero-fill, not a recovered value.
    for member in RAW_WEAPON:
        raw[offset:offset+4]=u32(weapon[member]);offset+=4
    result=bytes(raw);layout=decode_record(result)
    if layout['kind']!=1 or layout['derived_offset']+16!=offset:
        raise ValueError('Independent layout rejected assembled descriptor')
    return result
