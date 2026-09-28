"""Memory-only union of three disabled weapon labs; never a deployment.

Each individual transaction must restore exactly the SAME pair of source
tables. Shared resources must have identical bytes. No last-writer-wins merge.
"""
from copy import deepcopy
import json

from item_table_additive import build as add_weapon,restore as remove_weapon,fingerprint
from item_ammo_additive import build_pair,restore_pair
from item_table_overlay import mapping
from items_sav import parse as parse_items,text_field
from reconstruction_sandbox import relative

CASES=('FG42','MG34','ZK383')
SHORT={'FG42':'FG4','MG34':'MG3','ZK383':'ZK3'}
SLOTS={'FG42':362,'MG34':363,'ZK383':364}
SCOPES={'FG42':'private_disabled_fg42_full_tables','MG34':'private_disabled_portable_mg34_full_tables',
        'ZK383':'private_disabled_zk383_full_tables'}
CENTRAL={'items':'Tables/items.sav.disabled','fpv':'Tables/FpvAnims.sav.disabled'}
SCHEMA='disabled_three_rigid_weapons_v1'


def fixed_contract():
    return {'allocation_bytes_consumed':2016,'slots':[362,363,364,365],'groups':[462,463,464],
            'global_slots_reserved':False,'installation_allowed':False,'saved_game_compatibility_qualified':False}


def payloads(files,report,case):
    if (case not in CASES or not isinstance(report,dict) or report.get('scope')!=SCOPES[case]
            or type(report.get('schema_version')) is not int or report['schema_version']!=1
            or report.get('runtime_status')!='pending' or report.get('hand_variant') not in ('H','R')
            or any(report.get(k) is not False for k in ('game_modified','game_started','playable_weapon','installation_allowed'))
            or report.get('reverse_verified_in_memory') is not True
            or not isinstance(files,dict) or not isinstance(report.get('files'),dict) or set(files)!=set(report['files'])):
        raise ValueError('Expected a complete disabled single-weapon laboratory')
    seen=set()
    for name,raw in files.items():
        relative(name)
        if not name.endswith('.disabled') or name.casefold() in seen or not isinstance(raw,bytes):
            raise ValueError('Active or case-colliding laboratory payload')
        seen.add(name.casefold())
        if report['files'][name]!=fingerprint(raw):raise ValueError('Laboratory payload differs from receipt')
    try:
        current={k:files[n] for k,n in CENTRAL.items()};proof=report['transaction']
        original=restore_pair(current,proof) if case=='ZK383' else remove_weapon(current,proof)
        weapon=files[f'PROTOTYPE_{case}.item.disabled']
        fragment=files[f"PROTOTYPE_{SHORT[case]}P{report['hand_variant']}.fpvgroup.disabled"]
        ammunition=files['PROTOTYPE_ZK3MAG.item.disabled'] if case=='ZK383' else None
        inner=proof['weapon'] if case=='ZK383' else proof
        if (inner['slot']!=SLOTS[case] or inner['descriptor']!=fingerprint(weapon)
                or inner['fragment']!=fingerprint(fragment) or text_field(weapon,88)!='MODERN_'+case):
            raise ValueError('Single-weapon transaction owner or payload differs')
        if case=='ZK383' and (proof['ammo']['slot']!=365 or proof['ammo']['descriptor']!=fingerprint(ammunition)):
            raise ValueError('Modern ZK383 magazine differs')
        return original,{'weapon':weapon,'fragment':fragment,'ammunition':ammunition}
    except (KeyError,TypeError,IndexError) as error:raise ValueError('Incomplete single-weapon transaction') from error


def merge_resources(labs):
    result={};owners={};folded={};shared=[]
    for case in CASES:
        files,_=labs[case]
        for name,raw in files.items():
            if name in CENTRAL.values():continue
            key=name.casefold()
            if key in folded:
                old=folded[key]
                if name!=old or raw!=result[old]:raise ValueError('Conflicting shared laboratory resource: '+name)
                owners[name].append(case)
            else:result[name]=raw;folded[key]=name;owners[name]=[case]
    shared=[{'path':name,'owners':cases,'fingerprint':fingerprint(result[name])}
            for name,cases in owners.items() if len(cases)>1]
    return result,shared


def build(labs):
    if not isinstance(labs,dict) or set(labs)!=set(CASES):raise ValueError('Exactly three rigid weapon labs required')
    source=None;entries={};hand=None;layer=None
    for case in CASES:
        value=labs[case]
        if not isinstance(value,(tuple,list)) or len(value)!=2:raise ValueError('Incomplete laboratory pair')
        files,report=value;original,entries[case]=payloads(files,report,case)
        if source is None:source=original;hand=report['hand_variant'];layer=report.get('item_layer')
        if original!=source:raise ValueError('Laboratories do not share exact source table snapshots')
        if report['hand_variant']!=hand:raise ValueError('Cannot combine different hand variants')
        if report.get('item_layer')!=layer or layer not in ('SabreSquadron.dta','PatchX01.dta'):
            raise ValueError('Cannot combine different archive layers')
    result,shared=merge_resources(labs);current=dict(source);transactions=[]
    for case in CASES:
        row=entries[case]
        if case=='ZK383':
            current,proof=build_pair(current['items'],current['fpv'],row['weapon'],row['fragment'],row['ammunition'],
                                     weapon_slot=SLOTS[case],ammo_slot=365)
        else:current,proof=add_weapon(current['items'],current['fpv'],row['weapon'],row['fragment'],slot=SLOTS[case])
        transactions.append({'case':case,'transaction':proof})
    receipt={'schema':SCHEMA,'sources':{k:fingerprint(v) for k,v in source.items()},
             'results':{k:fingerprint(v) for k,v in current.items()},'transactions':transactions,**fixed_contract()}
    if restore(current,receipt)!=source:raise ValueError('Combined reversal differs from source snapshots')
    result.update({CENTRAL[k]:v for k,v in current.items()})
    return result,{'schema_version':1,'scope':'private_disabled_three_rigid_weapon_tables','runtime_status':'pending',
        'provenance':'ASSEMBLAGE_MODERNE_RESSOURCES_MIXTES','hand_variant':hand,'item_layer':layer,
        'transaction':receipt,'input_labs':{c:deepcopy(labs[c][1]) for c in CASES},'identical_shared_resources':shared,
        'files':{n:fingerprint(r) for n,r in result.items()},'reverse_verified_in_memory':True,
        'existing_present_items_preserved':parse_items(source['items'])['present_slots'],
        'pending_requirements':sorted({p for _,r in labs.values() for p in r['pending_requirements']}
                                      |{'simultaneous_weapon_runtime_qualification'}),
        'central_table_sources_must_be_identical':True,'shared_resources_must_be_byte_identical':True,
        'single_lab_central_tables_overwritten_by_copy':False,'installation_allowed':False,
        'global_slots_reserved':False,'commercial_hand_geometry_exported':False,
        'game_started':False,'game_modified':False,'playable_weapons':False,'engine_validated':False}


def restore(current,proof):
    mapping(current,complete=True)
    try:
        expected={'schema','sources','results','transactions',*fixed_contract()}
        if not isinstance(proof,dict) or set(proof)!=expected or proof['schema']!=SCHEMA:
            raise ValueError('Unknown combined laboratory receipt')
        if json.dumps({k:proof[k] for k in fixed_contract()},sort_keys=True)!=json.dumps(fixed_contract(),sort_keys=True):
            raise ValueError('Changed combined laboratory contract')
        if {k:fingerprint(v) for k,v in current.items()}!=proof['results']:
            raise ValueError('Combined tables changed; refusing rollback')
        rows=proof['transactions']
        if (not isinstance(rows,list) or len(rows)!=3
                or any(not isinstance(r,dict) or set(r)!={'case','transaction'} for r in rows)
                or [r['case'] for r in rows]!=list(CASES)):
            raise ValueError('Changed combined transaction order')
        original=dict(current)
        for row in reversed(rows):
            case=row['case'];tx=row['transaction'];inner=tx['weapon'] if case=='ZK383' else tx
            if inner['slot']!=SLOTS[case] or (case=='ZK383' and tx['ammo']['slot']!=365):
                raise ValueError('Changed combined transaction owner')
            original=restore_pair(original,tx) if case=='ZK383' else remove_weapon(original,tx)
        if {k:fingerprint(v) for k,v in original.items()}!=proof['sources']:
            raise ValueError('Combined restored source differs')
        return original
    except (KeyError,TypeError,IndexError) as error:raise ValueError('Malformed combined laboratory receipt') from error
