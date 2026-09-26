import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from model_transform import affine,compose,invert,point,decompose,matmul,rotation,world_transforms


class TransformTests(unittest.TestCase):
    def test_inverse_roundtrip_nonuniform_rotated_transform(self):
        t=affine([1,2,3],[0,math.sin(.4),0,math.cos(.4)],[2,3,4])
        for v in ([0,0,0],[1,2,3],[-8,.1,6]):
            out=point(invert(t),point(t,v))
            for a,b in zip(v,out): self.assertAlmostEqual(a,b)

    def test_decomposition_all_quaternion_branches(self):
        for q in ([0,0,0,1],[1,0,0,0],[0,1,0,0],[0,0,1,0],[.5,.5,.5,.5]):
            t=affine([2,3,4],q,[2,3,4]); p,r,s,error=decompose(t)
            self.assertLess(error,1e-10)
            rebuilt=affine(p,r,s)
            for i in range(3):
                for j in range(3): self.assertAlmostEqual(t[0][i][j],rebuilt[0][i][j])

    def test_shear_reflection_and_singular_rejected(self):
        for m in ([[1,.2,0],[0,1,0],[0,0,1]],[[-1,0,0],[0,1,0],[0,0,1]],[[0,0,0],[0,1,0],[0,0,1]]):
            with self.assertRaises(ValueError): decompose((m,[0,0,0]))
        with self.assertRaises(ValueError): invert(affine([0,0,0],[0,0,0,1],[0,1,1]))
        with self.assertRaises(ValueError): rotation([0,0,0,0])
        with self.assertRaises(ValueError): rotation([0,math.nan,0,1])

    def test_parent_child_composition_preserves_placement(self):
        parent=affine([1,2,3],[0,1,0,0],[1,1,1])
        child=affine([.1,.2,.3],[0,0,0,1],[1,1,1])
        self.assertEqual(point(compose(parent,child),[0,0,0]),[.9,2.2,2.7])


if __name__=='__main__': unittest.main()
