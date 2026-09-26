"""Original, memory-only additive transaction for two PRIVATE disabled tables.

The reviewed 500-slot allocation is retained. Existing records/groups remain
byte-identical; an empty presence word consumes 504 bytes of the 0xCD tail.
This is not an installer, a global slot reservation or a saved-game migration.
"""
from __future__ import annotations
import hashlib
import struct

from fpv_table import parse as parse_fpv
from item_native_layout import decode_record,fpv_native_projection
from items_sav import parse as parse_items,text_field

CAPACITY=500
DELTA=504
SCHEMA='disabled_item_and_fpv_addition_v1'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def fingerprint(raw):return {'size':len(raw),'sha256':sha(raw)}


def slot_number(slot):
    if type(slot) is not int or not 0<=slot<CAPACITY:
        raise ValueError('Candidate outside the reviewed 500-slot domain')


def build(items,fpv,descriptor,fragment,*,slot):
    """Validate both additions before returning either resulting byte string."""
    slot_number(slot)
    before=parse_items(items,capacity=CAPACITY)
    target=before['slots'][slot]
    if target['present']:raise ValueError('Candidate already occupied')
    if before['allocation_tail_size']<=DELTA:
        raise ValueError('Insufficient canonical allocation tail; capacity will not grow')
    layout=decode_record(descriptor)
    name=text_field(descriptor,88);text_id=struct.unpack_from('<I',descriptor,108)[0]
    if layout['kind']!=1 or not name.startswith('MODERN_') or text_id==0xffffffff:
        raise ValueError('Expected a modern Weapon with a prepared inventory text ID')
    occupied=[s for s in before['slots'] if s['present']]
    if any(s['internal_name'].casefold()==name.casefold() for s in occupied):
        raise ValueError('Modern internal name already present')
    if any(s['text_id']==text_id for s in occupied):
        raise ValueError('Modern text ID already referenced by an item')
    ammo=layout['members']['0x54']['value_raw']
    if ammo>=CAPACITY or before['slots'][ammo].get('kind')!=0:
        raise ValueError('Weapon ammunition does not reference an existing class-0 item')

    old_fpv=parse_fpv(fpv);new_group=parse_fpv(fragment)
    # Existing groups must already be consumable; never normalize or reorder
    # their payloads to make the new group pass validation.
    fpv_native_projection(old_fpv);fpv_native_projection(new_group)
    group_id=slot+100
    if len(new_group['groups'])!=1 or new_group['groups'][0]['id']!=group_id:
        raise ValueError('Expected exactly the candidate-plus-100 FPV group')
    if group_id in {g['id'] for g in old_fpv['groups']}:
        raise ValueError('Candidate FPV owner already present')
    if len(fpv)+len(fragment)-6>0xffffffff:raise ValueError('FPV root size overflow')

    at=target['offset']
    changed_items=items[:at]+descriptor+items[at+4:len(items)-DELTA]
    changed_fpv=struct.pack('<HI',12345,len(fpv)+len(fragment)-6)+fpv[6:]+fragment[6:]
    after=parse_items(changed_items,capacity=CAPACITY)
    after_fpv=parse_fpv(changed_fpv);fpv_native_projection(after_fpv)
    for original,changed in zip(before['slots'],after['slots']):
        if original['slot']==slot:continue
        if original['sha256']!=changed['sha256'] or original['size']!=changed['size']:
            raise ValueError('Existing item record changed')
    if (after['slots'][slot]['sha256']!=sha(descriptor)
            or after['serialized_size']!=before['serialized_size']+DELTA
            or after['allocation_tail_size']!=before['allocation_tail_size']-DELTA):
        raise ValueError('Unexpected item insertion layout')
    if after_fpv['groups'][:-1]!=old_fpv['groups']:
        raise ValueError('Existing FPV group changed or moved')
    proof={'schema':SCHEMA,'slot':slot,'group_id':group_id,'capacity':CAPACITY,
        'item_offset':at,'original_serialized_size':before['serialized_size'],
        'original_tail_size':before['allocation_tail_size'],
        'descriptor':fingerprint(descriptor),'fragment':fingerprint(fragment),
        'sources':{'items':fingerprint(items),'fpv':fingerprint(fpv)},
        'results':{'items':fingerprint(changed_items),'fpv':fingerprint(changed_fpv)},
        'existing_item_slots_preserved':CAPACITY-1,
        'existing_present_items_preserved':before['present_slots'],
        'existing_fpv_groups_preserved':len(old_fpv['groups']),
        'item_allocation_size_unchanged':True,'global_slot_reservation':False,
        'installation_allowed':False,'saved_game_compatibility_qualified':False}
    return {'items':changed_items,'fpv':changed_fpv},proof


def restore(current,proof):
    """Reverse this exact pair only, refusing later edits or altered metadata.

    The proof is an integrity receipt, not an authenticated authorization.
    No files are opened or changed by either operation.
    """
    if not isinstance(current,dict) or set(current)!={'items','fpv'}:
        raise ValueError('Expected both current transaction tables')
    if not isinstance(proof,dict) or proof.get('schema')!=SCHEMA:
        raise ValueError('Unknown additive transaction proof')
    try:
        slot_number(proof['slot'])
        for key in ('item_offset','original_serialized_size','original_tail_size'):
            if type(proof[key]) is not int or proof[key]<0:raise ValueError('Invalid transaction offset/size')
        for name in ('items','fpv'):
            if fingerprint(current[name])!=proof['results'][name]:
                raise ValueError('Transaction result changed; refusing rollback')
        if proof['capacity']!=CAPACITY or proof['group_id']!=proof['slot']+100:
            raise ValueError('Transaction owner/capacity mismatch')
        items=current['items'];fpv=current['fpv'];at=proof['item_offset']
        parsed=parse_items(items,capacity=CAPACITY)
        target=parsed['slots'][proof['slot']]
        if not target['present'] or target['offset']!=at:raise ValueError('Transaction slot position mismatch')
        group=parse_fpv(fpv)['groups'][-1]
        if group['id']!=proof['group_id']:raise ValueError('Transaction group is not the final appended group')
        original_size=group['offset']
        descriptor=items[at:at+508]
        fragment=struct.pack('<HI',12345,group['size']+6)+fpv[original_size:]
        originals={'items':items[:at]+bytes(4)+items[at+508:]+b'\xcd'*DELTA,
                   'fpv':struct.pack('<HI',12345,original_size)+fpv[6:original_size]}
        if any(fingerprint(raw)!=proof['sources'][name] for name,raw in originals.items()):
            raise ValueError('Restored source fingerprint mismatch')
        repeated,receipt=build(originals['items'],originals['fpv'],descriptor,fragment,slot=proof['slot'])
        # Compare canonical JSON as well: Python treats True==1 and 359.0==359,
        # but neither is acceptable in this strict integer receipt.
        import json
        if repeated!=current or json.dumps(receipt,sort_keys=True)!=json.dumps(proof,sort_keys=True):
            raise ValueError('Transaction proof differs from the reconstructed operation')
        return originals
    except (KeyError,TypeError,IndexError,struct.error) as error:
        raise ValueError('Malformed additive transaction proof') from error
