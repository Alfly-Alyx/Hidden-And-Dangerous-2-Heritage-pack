"""Original structural plan for separate stock hands and a static FPV weapon.

Name/parent compatibility is NOT native animation binding or skin evaluation.
No model merge, key interpolation, pose mutation or inferred events occur.
"""
from __future__ import annotations

from benelli_fpv_static import NAMES as WEAPON_NAMES


def hierarchy(nodes):
    if not isinstance(nodes,list) or not nodes:raise ValueError('Expected nonempty rig nodes')
    by_id={};names={};folded=set()
    for node in nodes:
        index=node['index'];name=node['name'];parent=node['parent_id']
        if (type(index) is not int or index<1 or index in by_id or type(parent) is not int or parent<0
                or not isinstance(name,str) or not name or any(ord(c)<32 for c in name)
                or name.casefold() in folded):
            raise ValueError('Ambiguous or invalid rig node')
        by_id[index]=node;names[name]=node;folded.add(name.casefold())
    parents={}
    for node in nodes:
        parent=node['parent_id']
        if parent and parent not in by_id:raise ValueError('Rig parent outside its model')
        parents[node['name']]=by_id[parent]['name'] if parent else None
        seen={node['index']}
        while parent:
            if parent in seen:raise ValueError('Cyclic rig hierarchy')
            seen.add(parent);parent=by_id[parent]['parent_id']
            if parent and parent not in by_id:raise ValueError('Rig ancestor outside its model')
    return names,parents


def bind(hand_nodes,weapon_nodes,animation_nodes,tracks):
    hands,hand_parents=hierarchy(hand_nodes)
    weapon,weapon_parents=hierarchy(weapon_nodes)
    animated,animation_parents=hierarchy(animation_nodes)
    if set(weapon)!=WEAPON_NAMES:raise ValueError('Unexpected static Benelli weapon rig')
    if {name.casefold() for name in hands}&{name.casefold() for name in weapon}:
        raise ValueError('Hands and weapon own colliding target names')
    if (hands.get('a',{}).get('frame_type')!=1 or hands['a'].get('visual_type')!=2
            or hand_parents['a'] is not None
            or any(n['frame_type']!=10 for name,n in hands.items() if name!='a')):
        raise ValueError('Expected skinned hands root a and joint descendants')
    combined={**hands,**weapon};parents={**hand_parents,**weapon_parents}
    if set(animated)!=set(combined):raise ValueError('Animation model and assembled target names differ')
    if animation_parents!=parents:raise ValueError('Animation and assembled target parent names differ')
    for name,node in animated.items():
        expected=10 if name=='a' else combined[name]['frame_type']
        if node['frame_type']!=expected:raise ValueError('Unexpected animation target frame kind')
    if not isinstance(tracks,list) or not tracks:raise ValueError('Expected nonempty animation tracks')
    bindings=[];seen=set()
    for track in tracks:
        name=track['name']
        if not isinstance(name,str) or name.casefold() in seen or name not in combined:
            raise ValueError('Unknown, duplicate or inexact animation track target')
        seen.add(name.casefold());owner='hands' if name in hands else 'weapon'
        bindings.append({'track':name,'target_owner':owner,'target_node_index':combined[name]['index'],
                         'parent_name':parents[name]})
    present={b['track'] for b in bindings}
    return {'matching_policy':'exact_names_and_parent_names_not_file_ordinals',
        'assembled_target_count':len(combined),'hand_target_count':len(hands),'weapon_target_count':len(weapon),
        'hand_track_count':sum(b['target_owner']=='hands' for b in bindings),
        'weapon_track_count':sum(b['target_owner']=='weapon' for b in bindings),
        'bindings':bindings,'targets_without_track':sorted(set(combined)-present),
        'root_a_role_difference':'skinned_mesh_in_hands_joint_in_animation_source',
        'partial_track_state_inheritance_qualified':False,'native_name_binding_executed':False,
        'skin_weights_evaluated':False,'camera_or_events_qualified':False,'engine_validated':False}
