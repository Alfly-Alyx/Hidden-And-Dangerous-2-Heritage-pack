"""Modern analytic hand targeting: synthetic numbers, no commercial geometry."""
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from hand_pose_ik import two_bone,shortest_rotation,bend_plane_rotation,norm,sub,validate_basis,pinned_skin
from model_transform import matvec,determinant


class HandIKTests(unittest.TestCase):
    def test_both_lengths_and_pole_side_are_preserved(self):
        elbow=two_bone([0,0,0],[0,.4,0],[1,0,0],.3,.25)
        self.assertAlmostEqual(norm(elbow),.3)
        self.assertAlmostEqual(norm(sub(elbow,[0,.4,0])),.25);self.assertGreater(elbow[0],0)

    def test_mirrored_poles_produce_mirrored_elbows(self):
        a=two_bone([0,0,0],[0,.4,0],[1,0,0],.3,.25)
        b=two_bone([0,0,0],[0,.4,0],[-1,0,0],.3,.25)
        self.assertAlmostEqual(a[0],-b[0]);self.assertEqual(a[1:],b[1:])

    def test_unreachable_or_singular_targets_never_stretch(self):
        for target in ([0,1,0],[0,.55,0],[0,0,0],[0,.01,0]):
            with self.assertRaises(ValueError):two_bone([0,0,0],target,[1,0,0],.3,.25)
        with self.assertRaises(ValueError):two_bone([0,0,0],[0,.4,0],[0,1,0],.3,.25)

    def test_invalid_vectors_lengths_and_booleans_refused(self):
        for length in (True,0,3,float('nan')):
            with self.assertRaises(ValueError):two_bone([0,0,0],[0,.4,0],[1,0,0],length,.25)
        for target in ([0,math.inf,0],[True,.4,0],[0,.4]):
            with self.assertRaises(ValueError):two_bone([0,0,0],target,[1,0,0],.3,.25)

    def test_shortest_rotation_regular_parallel_and_antiparallel(self):
        for target in ([0,1,0],[1,0,0],[-1,0,0],[0,0,-1]):
            matrix=shortest_rotation([1,0,0],target);actual=matvec(matrix,[1,0,0])
            for a,b in zip(actual,target):self.assertAlmostEqual(a,b)
            self.assertAlmostEqual(determinant(matrix),1)

    def test_orientation_rejects_scale_reflection_and_bad_shape(self):
        for matrix in ([[2,0,0],[0,1,0],[0,0,1]],[[-1,0,0],[0,1,0],[0,0,1]],[[1,0,0]]):
            with self.assertRaises(ValueError):validate_basis(matrix)

    def test_unreviewed_commercial_input_refused_before_parsing(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed'):pinned_skin(b'not a commercial model')

    def test_bend_plane_rotation_maps_bone_and_resolves_antipodal_twist(self):
        for target in ([1,0,0],[-1,0,0],[0,1,0],[.6,.8,0]):
            matrix=bend_plane_rotation([1,0,0],target,[0,0,1])
            validate_basis(matrix)
            for a,b in zip(matvec(matrix,[1,0,0]),target):self.assertAlmostEqual(a,b)
            self.assertEqual(matvec(matrix,[0,0,1]),[0,0,1])

    def test_bend_plane_rotation_refuses_collinear_hint(self):
        with self.assertRaises(ValueError):bend_plane_rotation([1,0,0],[0,1,0],[0,1,0])


if __name__=='__main__':unittest.main()
