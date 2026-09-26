"""Strict isolated item-instance framing, not a complete player-save editor.

This original codec covers a leaf item envelope and the reviewed common/weapon
state tags. No filesystem API, allocation decision, migration or save writes.
Unknown fields, nested inventory, duplicates and malformed bounds fail closed.
"""
import struct

ENVELOPE = 0xad2c
STATE = 0x2cc
CHILDREN = 0x268
COMMON = 0x2e6b
COMMON_MEMBERS = {100:0x10,101:0x14,102:0x24,103:0x20,104:0x1c}
# This client's reader does NOT mirror its writer: 102/103 are skipped,
# while 202/203 inside COMMON restore those members. Do not silently repair.
COMMON_READER_MEMBERS = {100:0x10,101:0x14,104:0x1c,202:0x24,203:0x20}
WEAPON_MEMBERS = dict(zip(range(200,211),(0x50,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x7c,0x90,0x94)))


def chunk(kind, body):
    return struct.pack('<HI',kind,len(body)+6)+body


def children(raw):
    result=[];offset=0
    while offset<len(raw):
        if len(raw)-offset<6:raise ValueError('Truncated item-instance chunk')
        kind,size=struct.unpack_from('<HI',raw,offset)
        if size<6 or offset+size>len(raw):raise ValueError('Invalid item-instance chunk size')
        result.append((kind,raw[offset+6:offset+size]));offset+=size
    if len({kind for kind,_ in result})!=len(result):raise ValueError('Duplicate item-instance field')
    return result


def checked_values(values,expected):
    if set(values)!=set(expected):raise ValueError('Missing or unknown item-instance fields')
    if any(type(v) is not int or not 0<=v<=0xffffffff for v in values.values()):
        raise ValueError('Item-instance field must be a raw unsigned 32-bit integer')


def scalar_chunk(kind,value):
    return chunk(kind,struct.pack('<I',value))


def encode_leaf(slot, placement, common, weapon=None):
    if type(slot) is not int or not 0<=slot<500:raise ValueError('Item slot outside reviewed 1.12 capacity')
    checked_values(placement,(1,2,3));checked_values(common,COMMON_MEMBERS)
    if common[104] not in (0,1):raise ValueError('Noncanonical common boolean')
    body=chunk(COMMON,b''.join(scalar_chunk(k,common[k]) for k in COMMON_MEMBERS))
    if weapon is not None:
        checked_values(weapon,WEAPON_MEMBERS)
        if weapon[209] not in (0,1):raise ValueError('Noncanonical weapon boolean')
        body+=b''.join(scalar_chunk(k,weapon[k]) for k in WEAPON_MEMBERS)
    return chunk(ENVELOPE,scalar_chunk(0,slot)+b''.join(scalar_chunk(k,placement[k]) for k in (1,2,3))
                 +chunk(STATE,body)+chunk(CHILDREN,b''))


def decode_leaf(raw,*,weapon):
    if type(weapon) is not bool:raise ValueError('Explicit item-state kind required')
    roots=children(raw)
    if len(roots)!=1 or roots[0][0]!=ENVELOPE:raise ValueError('Expected one item-instance envelope')
    field_list=children(roots[0][1])
    if tuple(k for k,_ in field_list)!=(0,1,2,3,STATE,CHILDREN):
        raise ValueError('Incomplete, reordered or unreviewed item envelope')
    fields=dict(field_list)
    if fields[CHILDREN]:raise ValueError('Nested item inventories are outside this leaf codec')
    def scalar(body):
        if len(body)!=4:raise ValueError('Item-instance scalar must occupy four bytes')
        return struct.unpack('<I',body)[0]
    slot=scalar(fields[0])
    if slot>=500:raise ValueError('Item slot outside reviewed 1.12 capacity')
    state_list=children(fields[STATE])
    if not state_list or state_list[0][0]!=COMMON:raise ValueError('Common state must precede derived state')
    state=dict(state_list)
    if set(state)!=({COMMON}|(set(WEAPON_MEMBERS) if weapon else set())):
        raise ValueError('Missing or unexpected item state fields')
    common={k:scalar(b) for k,b in children(state[COMMON])}
    checked_values(common,COMMON_MEMBERS)
    if common[104] not in (0,1):raise ValueError('Noncanonical common boolean')
    gun={k:scalar(state[k]) for k in WEAPON_MEMBERS} if weapon else None
    if gun is not None and gun[209] not in (0,1):raise ValueError('Noncanonical weapon boolean')
    return {'slot':slot,'placement':{k:scalar(fields[k]) for k in (1,2,3)},
            'common':common,'weapon':gun,'whole_saved_game_qualified':False}
