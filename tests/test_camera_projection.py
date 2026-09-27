"""Independent camera reference and guards, without commercial binary data."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_camera_projection_oracle import reference, changed_settings, validate, controls, PI, MIN_FOV, CameraProjectionOracle
from ls3d_math_oracle import f32


def settings():
    return {'primary_fov': math.pi/2, 'secondary_fov': .8, 'aspect': 16/9,
            'near': 1, 'far': 1000, 'secondary_near': .01, 'secondary_far': 20}


class CameraProjectionTests(unittest.TestCase):
    def test_horizontal_angle_and_aspect_are_independent(self):
        s = settings()
        row = reference(s)
        self.assertAlmostEqual(row['primary'][0], 1, places=6)
        self.assertAlmostEqual(row['primary'][5], 16/9, places=6)
        self.assertEqual(row['primary'][11], 1)
        self.assertEqual(row['primary'][15], 0)
        s['aspect'] = 4/3
        self.assertEqual(reference(s)['primary'][0], row['primary'][0])

    def test_positive_forward_near_and_far_project_to_zero_and_one(self):
        s = settings()
        row = reference(s)
        for key, near, far in (('primary', s['near'], s['far']),
                               ('secondary', s['secondary_near'], s['secondary_far']),
                               ('extended', s['near']*10, s['far']*1000)):
            m = row[key]
            self.assertAlmostEqual((near*m[10]+m[14])/near, 0, places=6)
            self.assertAlmostEqual((far*m[10]+m[14])/far, 1, places=6)

    def test_ultrawide_exact_boundary_and_half_angle_cap(self):
        s = settings()
        s['aspect'] = 2.5
        self.assertFalse(reference(s)['ultrawide_branch'])
        s['aspect'] = 2.50001
        row = reference(s)
        self.assertTrue(row['ultrawide_branch'])
        self.assertEqual(row['effective_horizontal_fov_radians'][0], 3)
        s['primary_fov'] = .4
        self.assertEqual(reference(s)['effective_horizontal_fov_radians'][0], f32(.4)*2)

    def test_clamps_and_only_selected_angle_changes(self):
        s = settings()
        before = deepcopy(s)
        for target in ('primary', 'secondary'):
            for value, expected in ((-1, MIN_FOV), (0, MIN_FOV), (.7, f32(.7)), (4, PI)):
                changed = changed_settings(s, target, value)
                self.assertEqual(changed[target+'_fov'], expected)
                for key in changed:
                    if key != target+'_fov':
                        self.assertEqual(changed[key], f32(s[key]))
        self.assertEqual(s, before)

    def test_primary_and_secondary_projection_matrices_are_independent(self):
        original = reference(settings())
        a = reference(changed_settings(settings(), 'primary', 1.2))
        b = reference(changed_settings(settings(), 'secondary', 1.2))
        self.assertEqual(a['secondary'], original['secondary'])
        self.assertEqual(b['primary'], original['primary'])
        self.assertEqual(b['extended'], original['extended'])
        self.assertNotEqual(a['primary'], original['primary'])
        self.assertNotEqual(b['secondary'], original['secondary'])

    def test_unsupported_or_nonfinite_settings_rejected(self):
        for key, value in (('aspect', 0), ('aspect', 5), ('near', 0), ('far', 1),
                           ('secondary_far', .009), ('primary_fov', 0), ('secondary_fov', 4),
                           ('near', True), ('aspect', math.nan)):
            s = settings()
            s[key] = value
            with self.assertRaises(ValueError): validate(s)
        s = settings()
        s['orthographic'] = False
        with self.assertRaises(ValueError): validate(s)
        for target, value in (('other', 1), ('primary', math.inf), ('primary', True), ('primary', 8)):
            with self.assertRaises(ValueError): changed_settings(settings(), target, value)

    def test_native_control_case_matrix_has_both_setters_and_wide_cases(self):
        cases = list(controls())
        self.assertEqual(len(cases), 352)
        self.assertEqual(sum(s['aspect'] > 2.5 for s, _ in cases), 88)
        self.assertEqual(sum(not options for _, options in cases), 32)
        self.assertEqual(sum(options.get('target') == 'primary' for _, options in cases), 160)

    def test_changed_library_rejected_before_emulation(self):
        with self.assertRaises(ValueError): CameraProjectionOracle(b'not a commercial DLL')


if __name__ == '__main__':
    unittest.main()
