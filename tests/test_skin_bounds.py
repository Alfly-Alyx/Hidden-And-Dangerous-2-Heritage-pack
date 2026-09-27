"""Synthetic envelopes, float32 sphere reference and offline bounds guards."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_skin_bounds_oracle import SkinBoundsOracle, reference, START
from ls3d_skin_audit import IDENTITY
from skin_bounds_audit import controls, check_receipt, containment
from four_ds_skin import read_reviewed
from build_modern_equipment_assembly import inputs
from build_modern_equipment_hose import compile_hose_bank


class SkinBoundsTests(unittest.TestCase):
    def test_identity_and_translation_union_with_static_root_box(self):
        matrix = IDENTITY[:]
        matrix[12] = 2
        row = reference([0,0,0,0,1,1,1,0], [[-1,-1,-1,0,1,1,1,0]], [matrix])
        self.assertEqual(row['bounds'], [0,-1,-1,0,3,1,1,0])
        self.assertEqual(row['center'], [1.5,0,0])
        self.assertAlmostEqual(row['radius'], 4.25**.5, places=6)

    def test_rotation_uses_all_eight_corners(self):
        rotation = [0,1,0,0,-1,0,0,0,0,0,1,0,0,0,0,1]
        row = reference([0]*8, [[-1,-2,-3,0,1,2,3,0]], [rotation])
        self.assertEqual(row['bounds'], [-2,-1,-3,0,2,1,3,0])

    def test_degenerate_point_has_zero_radius(self):
        row = reference([0]*8, [[0]*8], [IDENTITY])
        self.assertEqual(row, {'bounds': [0.0]*8, 'center': [0.0]*3, 'radius': 0.0})

    def test_cached_affine_shear_and_negative_scale_are_explicit_inputs(self):
        matrix = IDENTITY[:]
        matrix[0], matrix[4], matrix[10] = -2, .5, .5
        row = reference([0]*8, [[-1,-1,-1,0,1,1,1,0]], [matrix])
        self.assertEqual(row['bounds'], [-2.5,-1,-.5,0,2.5,1,.5,0])

    def test_inputs_not_modified(self):
        args = next(controls())
        before = deepcopy(args)
        reference(*args)
        self.assertEqual(args, before)

    def test_invalid_empty_inverted_nonfinite_and_unpaired_inputs_refused(self):
        base, bounds, matrices = next(controls())
        inverted = [1,0,0,0,0,1,1,0]
        padded = base[:]
        padded[3] = 1
        bad_matrix = IDENTITY[:]
        bad_matrix[15] = 0
        for args in ((base, [], []), (base, bounds, []), (base, bounds*65, matrices*65),
                     (inverted, bounds, matrices), (padded, bounds, matrices),
                     ([float('nan')]*8, bounds, matrices), (base, bounds, [bad_matrix])):
            with self.subTest(args=args), self.assertRaises(ValueError):
                reference(*args)

    def test_containment_rejects_box_and_sphere_escapes(self):
        row = reference([-1,-1,-1,0,1,1,1,0], [[0]*8], [IDENTITY])
        box_error, sphere_error = containment(row, [[0,0,0,0,1,0], [1,1,1,0,0,1]])
        self.assertEqual(box_error, 0)
        # The stored float32 radius is slightly below the exact sqrt(3).
        self.assertGreater(sphere_error, 0)
        self.assertLess(sphere_error, 1e-7)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            containment(row, [[1.01,0,0]])
        with self.assertRaisesRegex(ValueError, 'escapes'):
            containment({**row, 'radius': .1}, [[.5,0,0]])
        with self.assertRaises(ValueError):
            containment(row, [[float('nan'),0,0]])

    def test_corpus_covers_capacity_and_general_affine_matrices(self):
        cases = list(controls())
        self.assertEqual(len(cases), 46)
        self.assertEqual(max(len(bounds) for _, bounds, _ in cases), 64)
        for args in cases:
            reference(*args)

    def test_serialized_hose_boxes_are_returned_privately_not_in_report(self):
        for case in ('F35', 'F2'):
            raw, _, _, _ = compile_hose_bank(*inputs(case))
            data = read_reviewed(raw, allow_multiple_lods=True)
            self.assertEqual(len(data['base_bounds']), 8)
            self.assertEqual(len(data['joint_bounds']), 8)
            self.assertNotIn('base_bounds', data['report'])
            self.assertNotIn('joint_bounds', data['report'])
            for box in data['joint_bounds']:
                self.assertEqual(len(box), 8)

    def test_instruction_guard_excludes_matrix_rebuild_binding_and_renderer(self):
        machine = object.__new__(SkinBoundsOracle)
        machine.phase = 'skin_bounds'
        machine.on_code(None, START, 1, None)
        for address in (0x10052480, 0x100527d0, 0x1005307a, 0x1008d41c):
            with self.assertRaises(ValueError):
                machine.on_code(None, address, 1, None)

    def test_incomplete_receipt_is_not_native_proof(self):
        args = next(controls())
        with self.assertRaisesRegex(ValueError, 'receipt'):
            check_receipt(reference(*args), *args)

    def test_invalid_library_refused(self):
        with self.assertRaises(ValueError):
            SkinBoundsOracle(b'')


if __name__ == '__main__':
    unittest.main()
