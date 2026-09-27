"""Original disabled class-0 ammunition serialization, not physical ammunition.

All values describe a game inventory object. No historical descriptor or
unknown bytes are copied, and no item slot is allocated by this module.
"""
import struct

from item_native_layout import BASE_MEMBERS,decode_record
from item_shoot_projection import f32,u32
from item_weapon_descriptor import exact_keys,resource_field,RAW_BASE


def build_ammunition(spec):
    exact_keys(spec,('provenance','status','native_class','names','text_id','weight','base_members_raw','quantity'),
               'modern ammunition specification')
    if (spec['provenance']!='ASSEMBLAGE_MODERNE' or spec['status']!='prototype_disabled'
            or type(spec['native_class']) is not int or spec['native_class']!=0):
        raise ValueError('Only explicitly modern disabled class-0 ammunition is supported')
    names=spec['names'];exact_keys(names,('internal','fpv','icon','world'),'ammunition names')
    if (not isinstance(names['internal'],str) or not names['internal'].startswith('MODERN_')
            or names['fpv']!='' or not names['world'] or not names['icon']):
        raise ValueError('Explicit modern ammunition world/icon and absent FPV are required')
    exact_keys(spec['base_members_raw'],RAW_BASE,'ammunition base members')
    quantity=spec['quantity']
    if type(quantity) is not int or not 1<=quantity<=10000:raise ValueError('Invalid discrete game ammunition quantity')
    weight=f32(spec['weight'])
    if struct.unpack('<f',weight)[0]<0:raise ValueError('Negative ammunition inventory weight')
    if type(spec['text_id']) is not int or not 0<=spec['text_id']<0xffffffff:
        raise ValueError('Prepared ammunition inventory text ID required')
    raw=bytearray(508);struct.pack_into('<II',raw,0,1,0)
    for name,offset in (('fpv',8),('icon',28),('world',48),('internal',88)):
        raw[offset:offset+20]=resource_field(names[name],icon=name=='icon')
    raw[108:112]=u32(spec['text_id']);raw[112:116]=weight
    for offset,member in BASE_MEMBERS.items():
        if member in RAW_BASE:raw[offset:offset+4]=u32(spec['base_members_raw'][member])
    # Two absent actions occupy 136..143; 144..175 is the explicit modern zero gap.
    raw[176:180]=f32(quantity);result=bytes(raw);layout=decode_record(result)
    if (layout['kind']!=0 or layout['derived_offset']!=176
            or [a['selector'] for a in layout['actions']]!=[0,0]):raise ValueError('Independent ammunition layout differs')
    return result
