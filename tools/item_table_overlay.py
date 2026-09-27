"""Compose a disabled addition onto exact current central-table snapshots.

No automatic conflict repair, archive-table replacement, file write or game
operation. Pre-existing custom records and FPV groups stay byte-identical.
"""
from __future__ import annotations

from fpv_table import parse as parse_fpv
from item_native_layout import decode_record,fpv_native_projection
from item_table_additive import build,restore,fingerprint
from items_sav import parse as parse_items

PATHS={'items':'Tables/items.sav','fpv':'Tables/FpvAnims.sav'}


def mapping(value,*,complete):
    if (not isinstance(value,dict) or not set(value)<=set(PATHS)
            or (complete and set(value)!=set(PATHS)) or any(not isinstance(raw,bytes) for raw in value.values())):
        raise ValueError('Expected central-table byte snapshots with known keys')


def differences(original,current):
    """Record identity-based differences without copying or normalizing values."""
    mapping(original,complete=True);mapping(current,complete=True)
    old=parse_items(original['items'],capacity=500);new=parse_items(current['items'],capacity=500)
    items=[]
    for before,after in zip(old['slots'],new['slots']):
        if before['sha256']==after['sha256']:continue
        items.append({'slot':before['slot'],
            'change':'added' if not before['present'] else 'removed' if not after['present'] else 'modified',
            'archive_sha256':before['sha256'],'current_sha256':after['sha256']})
    first=parse_fpv(original['fpv']);second=parse_fpv(current['fpv'])
    fpv_native_projection(first);fpv_native_projection(second)
    old_groups={g['id']:g for g in first['groups']};new_groups={g['id']:g for g in second['groups']}
    groups=[]
    for owner in sorted(set(old_groups)|set(new_groups)):
        before=old_groups.get(owner);after=new_groups.get(owner)
        if before is not None and after is not None and before['sha256']==after['sha256']:continue
        groups.append({'group_id':owner,'change':'added' if before is None else 'removed' if after is None else 'modified',
            'archive_sha256':before['sha256'] if before else None,'current_sha256':after['sha256'] if after else None})
    shared=set(old_groups)&set(new_groups)
    reordered=([g['id'] for g in first['groups'] if g['id'] in shared]
               !=[g['id'] for g in second['groups'] if g['id'] in shared])
    return {'items':items,'fpv_groups':groups,'existing_fpv_group_order_changed':reordered}


def compose(archive,overlays,descriptor,fragment,*,slot):
    mapping(archive,complete=True);mapping(overlays,complete=False)
    current={**archive,**overlays}
    delta=differences(archive,current)
    base=parse_items(archive['items'],capacity=500);effective=parse_items(current['items'],capacity=500)
    for entry in effective['slots']:
        if entry['present']:decode_record(current['items'][entry['offset']:entry['offset']+entry['size']])
    ammunition=decode_record(descriptor)['members'].get('0x54',{}).get('value_raw')
    if (type(ammunition) is not int or not 0<=ammunition<500
            or base['slots'][ammunition].get('kind')!=0 or effective['slots'][ammunition].get('kind')!=0
            or base['slots'][ammunition]['sha256']!=effective['slots'][ammunition]['sha256']):
        raise ValueError('Referenced ammunition differs from reviewed archive; explicit redesign is required')
    result,transaction=build(current['items'],current['fpv'],descriptor,fragment,slot=slot)
    if restore(result,transaction)!=current:raise ValueError('Composition does not restore the exact installed snapshot')
    # The normal additive transaction checks every other record/group against
    # CURRENT, not the archive; custom removals and ordering are preserved too.
    proof={'schema_version':1,'scope':'disabled_addition_preserving_current_central_tables',
        'selected_source':{key:'installed_snapshot' if key in overlays else 'reviewed_archive' for key in PATHS},
        'archive_sources':{key:fingerprint(raw) for key,raw in archive.items()},
        'current_sources':{key:fingerprint(raw) for key,raw in current.items()},
        'preexisting_changes':delta,'protected_ammunition_slot':ammunition,
        'ammunition_unchanged_from_archive':True,'transaction':transaction,
        'all_preexisting_central_table_changes_preserved':True,'reverse_restores_current_snapshot':True,
        'other_resource_overrides_merged':False,'global_id_reservation':False,
        'installation_allowed':False,'game_started':False,'game_modified':False}
    return result,proof


def read_overlays(game):
    """Read only two fixed paths; follow no links or case-ambiguous entries."""
    from reconstruction_sandbox import destination
    result={}
    for key,name in PATHS.items():
        path=destination(game,name)
        if not path.exists():continue
        if not path.is_file():raise ValueError('Central-table override is not a regular file')
        result[key]=path.read_bytes()
    return result


def require_unchanged_overlays(game,snapshot):
    mapping(snapshot,complete=False)
    if read_overlays(game)!=snapshot:raise ValueError('Central-table overrides changed during preparation')
