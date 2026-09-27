"""Reversible memory-only addition of a modern game magazine and its weapon.

No files, slot reservation, redistribution or deployment. The ammo addition
has no FPV group: only the weapon uses the existing reviewed pair transaction.
"""
import json
import math
import struct

from item_native_layout import decode_record
from items_sav import parse,text_field
from item_table_additive import CAPACITY,DELTA,slot_number,fingerprint,build as add_weapon,restore as remove_weapon

SCHEMA='disabled_modern_ammunition_addition_v1'
PAIR_SCHEMA='disabled_modern_weapon_and_ammunition_v1'


def build(items,descriptor,*,slot):
    slot_number(slot);before=parse(items,capacity=CAPACITY);target=before['slots'][slot]
    if target['present']:raise ValueError('Modern ammunition candidate already occupied')
    if before['allocation_tail_size']<=DELTA:raise ValueError('Insufficient ammunition allocation tail')
    layout=decode_record(descriptor);name=text_field(descriptor,88);text_id=struct.unpack_from('<I',descriptor,108)[0]
    if (layout['kind']!=0 or [a['selector'] for a in layout['actions']]!=[0,0]
            or not name.startswith('MODERN_') or text_id==0xffffffff):
        raise ValueError('Expected modern class-0 ammunition with no actions and prepared inventory text')
    quantity=struct.unpack('<f',struct.pack('<I',layout['members']['0x54']['value_raw']))[0]
    if not math.isfinite(quantity) or quantity<=0 or quantity>10000 or quantity!=int(quantity):
        raise ValueError('Invalid discrete modern ammunition quantity')
    occupied=[s for s in before['slots'] if s['present']]
    if any(s['internal_name'].casefold()==name.casefold() or s['text_id']==text_id for s in occupied):
        raise ValueError('Modern ammunition identity or text collision')
    at=target['offset'];current=items[:at]+descriptor+items[at+4:len(items)-DELTA];after=parse(current,capacity=CAPACITY)
    if any(a['sha256']!=b['sha256'] or a['size']!=b['size'] for a,b in zip(before['slots'],after['slots']) if a['slot']!=slot):
        raise ValueError('Existing record changed during ammunition insertion')
    if (after['slots'][slot]['sha256']!=fingerprint(descriptor)['sha256']
            or after['serialized_size']!=before['serialized_size']+DELTA
            or after['allocation_tail_size']!=before['allocation_tail_size']-DELTA):
        raise ValueError('Modern ammunition layout differs')
    return current,{'schema':SCHEMA,'slot':slot,'capacity':CAPACITY,'item_offset':at,
        'source':fingerprint(items),'result':fingerprint(current),'descriptor':fingerprint(descriptor),
        'original_present_records':before['present_slots'],'original_tail_size':before['allocation_tail_size'],
        'existing_records_preserved':True,'global_slot_reservation':False,'installation_allowed':False}


def restore(current,proof):
    try:
        if not isinstance(proof,dict) or proof.get('schema')!=SCHEMA:raise ValueError('Unknown ammunition receipt')
        slot_number(proof['slot'])
        if fingerprint(current)!=proof['result']:raise ValueError('Ammunition output changed; refusing rollback')
        parsed=parse(current,capacity=CAPACITY);entry=parsed['slots'][proof['slot']];at=entry['offset']
        if not entry['present'] or at!=proof['item_offset']:raise ValueError('Ammunition target differs')
        descriptor=current[at:at+508];original=current[:at]+bytes(4)+current[at+508:]+b'\xcd'*DELTA
        if fingerprint(original)!=proof['source']:raise ValueError('Restored ammunition source differs')
        repeated,receipt=build(original,descriptor,slot=proof['slot'])
        if repeated!=current or json.dumps(receipt,sort_keys=True)!=json.dumps(proof,sort_keys=True):
            raise ValueError('Ammunition receipt differs from reconstructed operation')
        return original
    except (KeyError,TypeError,IndexError,struct.error) as error:raise ValueError('Malformed ammunition receipt') from error


def build_pair(items,fpv,weapon,fragment,ammunition,*,weapon_slot,ammo_slot):
    slot_number(weapon_slot);slot_number(ammo_slot)
    layout=decode_record(weapon)
    if (weapon_slot==ammo_slot or layout['kind']!=1 or layout['members']['0x54']['value_raw']!=ammo_slot):
        raise ValueError('Modern weapon must reference its distinct modern ammunition slot')
    intermediate,ammo_proof=build(items,ammunition,slot=ammo_slot)
    current,weapon_proof=add_weapon(intermediate,fpv,weapon,fragment,slot=weapon_slot)
    proof={'schema':PAIR_SCHEMA,'ammo':ammo_proof,'weapon':weapon_proof,
        'sources':{'items':fingerprint(items),'fpv':fingerprint(fpv)},'results':{k:fingerprint(v) for k,v in current.items()},
        'ammo_has_fpv_group':False,'existing_records_and_groups_preserved':True,'allocation_bytes_consumed':2*DELTA,
        'global_slots_reserved':False,'installation_allowed':False,'saved_game_compatibility_qualified':False}
    if restore_pair(current,proof)!={'items':items,'fpv':fpv}:raise ValueError('Modern pair reversal differs')
    return current,proof


def restore_pair(current,proof):
    try:
        expected={'schema','ammo','weapon','sources','results','ammo_has_fpv_group',
            'existing_records_and_groups_preserved','allocation_bytes_consumed','global_slots_reserved',
            'installation_allowed','saved_game_compatibility_qualified'}
        if not isinstance(proof,dict) or set(proof)!=expected or proof['schema']!=PAIR_SCHEMA:
            raise ValueError('Unknown modern ammunition/weapon receipt')
        fixed={'ammo_has_fpv_group':False,'existing_records_and_groups_preserved':True,'allocation_bytes_consumed':2*DELTA,
            'global_slots_reserved':False,'installation_allowed':False,'saved_game_compatibility_qualified':False}
        if any(type(proof[k]) is not type(v) or proof[k]!=v for k,v in fixed.items()):raise ValueError('Changed modern pair contract')
        if set(current)!={'items','fpv'} or {k:fingerprint(v) for k,v in current.items()}!=proof['results']:
            raise ValueError('Modern pair output changed; refusing rollback')
        intermediate=remove_weapon(current,proof['weapon'])
        weapon_slot=proof['weapon']['slot'];ammo_slot=proof['ammo']['slot']
        if weapon_slot==ammo_slot:raise ValueError('Modern pair owners overlap')
        row=parse(current['items'],capacity=CAPACITY)['slots'][weapon_slot]
        weapon=current['items'][row['offset']:row['offset']+row['size']]
        if decode_record(weapon)['members']['0x54']['value_raw']!=ammo_slot:raise ValueError('Modern pair reference differs')
        original={'items':restore(intermediate['items'],proof['ammo']),'fpv':intermediate['fpv']}
        if {k:fingerprint(v) for k,v in original.items()}!=proof['sources']:raise ValueError('Modern pair sources differ')
        return original
    except (KeyError,TypeError,IndexError,struct.error) as error:raise ValueError('Malformed modern pair receipt') from error


def compose(archive,overlays,weapon,fragment,ammunition,*,weapon_slot,ammo_slot):
    from item_table_overlay import mapping,differences
    mapping(archive,complete=True);mapping(overlays,complete=False)
    slot_number(weapon_slot);slot_number(ammo_slot)
    base=parse(archive['items'],capacity=CAPACITY)
    if any(base['slots'][slot]['present'] for slot in (weapon_slot,ammo_slot)):
        raise ValueError('Modern pair candidate occupied in reviewed archive')
    current={**archive,**overlays};changes=differences(archive,current)
    for entry in parse(current['items'],capacity=CAPACITY)['slots']:
        if entry['present']:decode_record(current['items'][entry['offset']:entry['offset']+entry['size']])
    result,transaction=build_pair(current['items'],current['fpv'],weapon,fragment,ammunition,
        weapon_slot=weapon_slot,ammo_slot=ammo_slot)
    if restore_pair(result,transaction)!=current:raise ValueError('Modern pair does not restore personal snapshots')
    return result,{'schema_version':1,'scope':'disabled_modern_pair_preserving_current_tables',
        'archive_sources':{k:fingerprint(v) for k,v in archive.items()},'current_sources':{k:fingerprint(v) for k,v in current.items()},
        'selected_source':{k:'installed_snapshot' if k in overlays else 'reviewed_archive' for k in current},
        'preexisting_changes':changes,'transaction':transaction,'all_preexisting_central_table_changes_preserved':True,
        'reverse_restores_current_snapshot':True,'other_resource_overrides_merged':False,'global_id_reservation':False,
        'installation_allowed':False,'game_started':False,'game_modified':False}
