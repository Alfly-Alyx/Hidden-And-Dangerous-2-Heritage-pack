"""Original optional thumb opposition on unchanged, privately supplied poses.

The authored rotations act around rest-palm axes. No geometry, translations or
scales change, and no source animation keys are read or reproduced.
"""
from copy import deepcopy
import math

from hand_pose_ik import validate_basis
from model_transform import conjugate, invert, matmul, quaternion, rotation

DEFAULT = {
    'provenance': 'MODERNE', 'runtime_status': 'pending',
    'L': {'opposition_degrees': -30, 'curl_degrees': [25, 20]},
    'R': {'opposition_degrees': 30, 'curl_degrees': [-25, -20]},
}


def validate(spec):
    if (not isinstance(spec, dict) or set(spec) != {'provenance', 'runtime_status', 'L', 'R'}
            or spec['provenance'] != 'MODERNE' or spec['runtime_status'] != 'pending'):
        raise ValueError('Expected explicitly modern thumb authoring')
    for side in ('L', 'R'):
        hand = spec[side]
        if (not isinstance(hand, dict) or set(hand) != {'opposition_degrees', 'curl_degrees'}
                or not isinstance(hand['curl_degrees'], list) or len(hand['curl_degrees']) != 2
                or any(type(v) not in (int, float) or not math.isfinite(v) or not -75 <= v <= 75
                       for v in [hand['opposition_degrees'], *hand['curl_degrees']])):
            raise ValueError('Unreviewed thumb opposition or bend')
    return deepcopy(spec)


def turns(spec):
    spec = validate(spec)
    def axis(index, degrees):
        half = math.radians(degrees)/2
        value = [0, 0, 0, math.cos(half)]
        value[index] = math.sin(half)
        return rotation(value)
    return {f'Bip01 {side} Finger0'+suffix: (
                matmul(axis(1, spec[side]['opposition_degrees']), axis(2, spec[side]['curl_degrees'][0]))
                if suffix == '' else axis(2, spec[side]['curl_degrees'][1]))
            for side in ('L', 'R') for suffix in ('', '1')}


def apply(poses, rest_bases, spec):
    """Return a detached pose; callers must separately pin their private source."""
    authored = turns(spec)
    if set(rest_bases) != set(authored) or not set(authored) <= set(poses):
        raise ValueError('Missing or ambiguous thumb rest bases')
    result = deepcopy(poses)
    for name, turn in authored.items():
        basis = validate_basis(rest_bases[name])
        pose = result[name]
        if not isinstance(pose, dict) or set(pose) != {'position', 'rotation', 'scale'}:
            raise ValueError('Incomplete thumb pose')
        # Additional local rotation is B^-1 * R_rest * B, never a reflection.
        # Rounded source rest matrices are nearly orthonormal, not exact.
        # Use the true inverse so their tiny scale residual is not applied twice.
        local = matmul(matmul(invert((basis, [0,0,0]))[0], turn), basis)
        active = matmul(rotation(conjugate(pose['rotation'])), local)
        validate_basis(active)
        pose['rotation'] = conjugate(quaternion(active))
    if any(result[name][key] != pose[key] for name, pose in poses.items() for key in ('position', 'scale')):
        raise ValueError('Thumb authoring moved or stretched a joint')
    if any(result[name] != pose for name, pose in poses.items() if name not in authored):
        raise ValueError('Thumb authoring changed an unrelated joint')
    return result
