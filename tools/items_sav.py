"""Read HD2 item slots strictly, preserving empty slots and opaque payloads.

Locally verified Base/Patch: 255 slots; Sabre: 500. A slot is a presence word
(zero: 4 bytes; one: 4-byte presence + 504-byte payload). The remaining bytes
of the allocated 504*capacity buffer are 0xCD, not additional empty slots.
This is not the historical 508/512/516 record-size heuristic. Text IDs and
record ordinals are separate; unqualified gameplay fields stay opaque.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import math
import re
import struct

PAYLOAD_SIZE=504
PRESENT_SIZE=508


def u32(data,offset): return struct.unpack_from('<I',data,offset)[0]
def digest(data): return hashlib.sha256(data).hexdigest()


def model_name_field(name):
    """Encode a NEW ASCII model reference, never truncate a long resource name."""
    if (not isinstance(name,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,18}',name)
            or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',name)):
        raise ValueError('Model reference must be a safe stem of at most 19 ASCII characters')
    return name.encode('ascii').ljust(20,b'\0')


def text_field(record,offset):
    raw=record[offset:offset+20]
    if len(raw)!=20 or b'\0' not in raw: raise ValueError('Unterminated items.sav text field')
    value=raw.split(b'\0',1)[0]
    if any(b<32 for b in value): raise ValueError('Control character in items.sav text field')
    return value.decode('cp1252')


def parse(data,*,capacity=None):
    if capacity is None:
        if not data or len(data)%PAYLOAD_SIZE: raise ValueError('Invalid items.sav allocated buffer length')
        capacity=len(data)//PAYLOAD_SIZE
    if type(capacity) is not int or not 1<=capacity<=65536 or len(data)!=capacity*PAYLOAD_SIZE:
        raise ValueError('Invalid items.sav capacity or buffer length')
    slots=[]; offset=0
    for slot_id in range(capacity):
        if offset+4>len(data): raise ValueError('Truncated items.sav presence word')
        present=u32(data,offset)
        if present not in (0,1): raise ValueError('Unknown items.sav presence marker')
        size=PRESENT_SIZE if present else 4
        if offset+size>len(data): raise ValueError('Truncated items.sav payload')
        raw=data[offset:offset+size]
        slot={'slot':slot_id,'offset':offset,'size':size,'present':bool(present),'sha256':digest(raw)}
        if present:
            kind=u32(raw,4)
            if kind not in (0,1,2): raise ValueError('Unreviewed items.sav record kind')
            weight=struct.unpack_from('<f',raw,112)[0]
            if not math.isfinite(weight) or weight<0: raise ValueError('Invalid items.sav weight field')
            slot.update(kind=kind,fpv_model=text_field(raw,8),icon=text_field(raw,28),
                        world_model=text_field(raw,48),internal_name=text_field(raw,88),
                        text_id=u32(raw,108),weight_raw=weight)
        slots.append(slot);offset+=size
    tail=data[offset:]
    if not tail or any(b!=0xcd for b in tail): raise ValueError('Noncanonical items.sav allocation tail')
    return {'capacity':capacity,'slots':slots,'serialized_size':offset,
            'allocation_tail_size':len(tail),'allocation_tail_sha256':digest(tail),
            'present_slots':sum(s['present'] for s in slots),
            'kind_counts':dict(sorted(Counter(s['kind'] for s in slots if s['present']).items())),
            'size':len(data),'sha256':digest(data),'runtime_semantics_qualified':False}


def candidate_status(parsed,candidate):
    if type(candidate) is not int or candidate<0: raise ValueError('Invalid candidate slot')
    if candidate>=parsed['capacity']:
        return {'slot':candidate,'status':'outside_serialized_capacity','allocation_allowed':False}
    slot=parsed['slots'][candidate]
    return {**slot,'status':'occupied' if slot['present'] else 'serialized_empty',
            # An empty central slot is necessary, never sufficient for safety.
            'allocation_allowed':False,'save_compatibility_qualified':False}
