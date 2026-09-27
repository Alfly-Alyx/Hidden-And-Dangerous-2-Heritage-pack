"""Offline post-blend wrist constraints on pinned private FPV skeletons.

This is an authoring implementation, NOT an installed engine hook. Six arm
rotations are recomputed after equipment blending; all other channels remain
exact. No source animation, geometry, hierarchy or bind transform is changed.
"""
from copy import deepcopy

from animation_tick_audit import model_poses
from build_equipment_hand_animation import HAND_NAMES, IDENTITY, wrist_from_native
from hand_pose_ik import author_pose, pinned_skin
from ls3d_palette_oracle import reference as palette_reference
from model_transform import matmul

ARM_NAMES = frozenset(f'Bip01 {side} {part}' for side in ('L', 'R')
                      for part in ('UpperArm', 'Forearm', 'Hand'))


def world(nodes, poses):
    names = [node['name'] for node in nodes]
    if len(set(names)) != len(names) or not set(names) <= set(poses):
        raise ValueError('Missing or ambiguous constraint target')
    result = palette_reference([{**poses[n['name']], 'parent': n['parent_id']-1} for n in nodes],
                               [IDENTITY]*len(nodes))
    return dict(zip(names, result['world_matrices']))


def targets(equipment_world, grips, *, root_name='MOD_held_pivot'):
    if set(grips) != {'L', 'R'}:
        raise ValueError('Both wrist constraints are required')
    if root_name not in ('MOD_held_pivot','fpv_weapon') or root_name not in equipment_world:
        raise ValueError('Unreviewed or absent constraint root')
    held = equipment_world[root_name]
    basis = [[held[i+4*j] for j in range(3)] for i in range(3)]
    return {side: {'position': wrist_from_native(held, equipment_world['MOD_'+label+'_hand'], grips[side]),
                   'rotation': matmul(basis, grips[side]['rest_to_equipment_rotation']),
                   'pole': grips[side]['elbow_pole'][:]}
            for side, label in (('L', 'left'), ('R', 'right'))}


def wrist_errors(hand_world, wanted):
    return {side: max(abs(a-b) for a, b in zip(hand_world[f'Bip01 {side} Hand'][12:15],
                                              wanted[side]['position'])) for side in ('L', 'R')}


def replace_arm_rotations(poses, authored):
    if not ARM_NAMES <= set(poses) or not ARM_NAMES <= set(authored):
        raise ValueError('Incomplete constrained arm pose')
    result = deepcopy(poses)
    for name in ARM_NAMES:
        if (set(poses[name]) != {'position', 'rotation', 'scale'}
                or set(authored[name]) != {'position', 'rotation', 'scale'}
                or any(poses[name][key] != authored[name][key] for key in ('position', 'scale'))):
            raise ValueError('Constraint would move or stretch an arm bone')
        result[name]['rotation'] = deepcopy(authored[name]['rotation'])
    return result


def observed_elbow_hints(wanted,hand_world):
    from hand_pose_ik import vector
    if set(wanted)!={'L','R'}:raise ValueError('Both observed elbows are required')
    result=deepcopy(wanted)
    for side in ('L','R'):
        name=f'Bip01 {side} Forearm'
        if name not in hand_world:raise ValueError('Missing observed elbow')
        result[side]['pole']=vector(hand_world[name][12:15])
    return result


def correct(hand_raw, equipment_nodes, poses, grips, *, root_name='MOD_held_pivot',preserve_observed_elbow_plane=False):
    if type(preserve_observed_elbow_plane) is not bool:raise ValueError('Invalid observed elbow policy')
    source, skin = pinned_skin(hand_raw)
    hand_names, initial = model_poses(hand_raw)
    gear_names = {node['name'] for node in equipment_nodes}
    if (set(hand_names) != HAND_NAMES or gear_names & HAND_NAMES
            or set(poses) != HAND_NAMES | gear_names):
        raise ValueError('Unexpected post-blend target set')
    seeds = dict(zip(hand_names, initial))
    if (poses['a'] != seeds['a'] or any(poses[name][key] != seeds[name][key]
            for name in hand_names for key in ('position', 'scale'))):
        raise ValueError('Source hand root, positions or scales have changed')
    wanted = targets(world(equipment_nodes, poses), grips,root_name=root_name)
    hand_world=world(skin['nodes'],poses)
    if preserve_observed_elbow_plane:wanted=observed_elbow_hints(wanted,hand_world)
    before = wrist_errors(hand_world, wanted)
    authored, _ = author_pose(hand_raw, wanted,
        {side: {'finger_curl_degrees': [0, 0, 0]} for side in ('L', 'R')},
        arm_rotation_policy='bend_plane')
    result = replace_arm_rotations(poses, authored)
    after = wrist_errors(world(skin['nodes'], result), wanted)
    if max(after.values()) > 5e-6:
        raise ValueError('Post-blend wrist constraint missed its target')
    return result, {'hand_source': source, 'before': before, 'after': after,
        'changed_channels': 'six_arm_rotations_only', 'finger_poses_preserved': True,
        'equipment_poses_preserved': True, 'source_rest_transforms_preserved': True,
        'engine_hook_implemented': False, 'runtime_status': 'pending'}
