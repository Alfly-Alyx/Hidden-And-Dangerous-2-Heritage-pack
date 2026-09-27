"""Wholly invented rest bases/poses, no commercial skeleton fixture."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from modern_thumb_pose import DEFAULT, validate, turns, apply
from model_transform import matmul, rotation, conjugate, transpose


class ThumbPoseTests(unittest.TestCase):
    def fixture(self):
        bases = {name: [[1,0,0],[0,1,0],[0,0,1]] for name in turns(DEFAULT)}
        poses = {name: {'position': [.01,.02,.03], 'rotation': [0,0,0,1], 'scale': [1,1,1]} for name in bases}
        poses['Unrelated'] = {'position': [.4,.5,.6], 'rotation': [0,0,0,1], 'scale': [1,1,1]}
        return bases, poses

    def test_only_four_thumb_rotations_change_and_inputs_are_detached(self):
        bases, poses = self.fixture()
        before = deepcopy(poses)
        result = apply(poses, bases, DEFAULT)
        self.assertEqual(poses, before)
        self.assertEqual(result['Unrelated'], poses['Unrelated'])
        for name in bases:
            self.assertNotEqual(result[name]['rotation'], poses[name]['rotation'])
            self.assertEqual(result[name]['position'], poses[name]['position'])
            self.assertEqual(result[name]['scale'], poses[name]['scale'])
        result['Unrelated']['position'][0] = 99
        self.assertEqual(poses, before)

    def test_local_turn_reconstructs_authored_rest_world_turn(self):
        bases, poses = self.fixture()
        bases = {name: rotation([0,math.sin(.2),0,math.cos(.2)]) for name in bases}
        result = apply(poses, bases, DEFAULT)
        for name, wanted in turns(DEFAULT).items():
            actual = matmul(matmul(bases[name], rotation(conjugate(result[name]['rotation']))), transpose(bases[name]))
            self.assertLess(max(abs(a-b) for row_a, row_b in zip(actual, wanted) for a,b in zip(row_a,row_b)), 1e-12)

    def test_zero_angles_preserve_identity_pose(self):
        bases, poses = self.fixture()
        spec = deepcopy(DEFAULT)
        for side in ('L','R'): spec[side] = {'opposition_degrees': 0, 'curl_degrees': [0,0]}
        self.assertEqual(apply(poses, bases, spec), poses)

    def test_near_unit_rest_scale_is_not_applied_twice(self):
        bases, poses = self.fixture()
        bases = {name: [[.9999998 if i==j else 0 for j in range(3)] for i in range(3)] for name in bases}
        result = apply(poses, bases, DEFAULT)
        for name, expected in turns(DEFAULT).items():
            actual = rotation(conjugate(result[name]['rotation']))
            self.assertLess(max(abs(a-b) for ra,rb in zip(actual,expected) for a,b in zip(ra,rb)), 1e-12)

    def test_unreviewed_provenance_angles_and_reflections_fail_closed(self):
        for value in (True, math.nan, 76):
            spec = deepcopy(DEFAULT)
            spec['L']['opposition_degrees'] = value
            with self.assertRaises(ValueError): validate(spec)
        spec = deepcopy(DEFAULT)
        spec['provenance'] = 'OFFICIEL'
        with self.assertRaises(ValueError): validate(spec)
        bases, poses = self.fixture()
        bases[next(iter(bases))] = [[-1,0,0],[0,1,0],[0,0,1]]
        with self.assertRaises(ValueError): apply(poses, bases, DEFAULT)
        bases, poses = self.fixture()
        del bases[next(iter(bases))]
        with self.assertRaises(ValueError): apply(poses, bases, DEFAULT)


if __name__ == '__main__':
    unittest.main()
