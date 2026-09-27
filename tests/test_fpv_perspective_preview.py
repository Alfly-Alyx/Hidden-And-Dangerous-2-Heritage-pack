from pathlib import Path
import math
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from fpv_perspective_preview import clip_near, project


class PerspectiveTests(unittest.TestCase):
    def test_center_forward_right_and_up(self):
        self.assertEqual(project([0, 0, 1], 960, 600, 90), (480, 300, 1))
        self.assertAlmostEqual(project([1, 0, 1], 960, 600, 90)[0], 960)
        self.assertAlmostEqual(project([0, 1, 1], 960, 600, 90)[1], -180)
        self.assertGreater(project([0, 0, .5], 960, 600, 90)[2], project([0, 0, 2], 960, 600, 90)[2])

    def test_near_crossing_is_clipped_not_dropped(self):
        points = [[-1, 0, 0], [1, 0, 1], [0, 1, 1]]
        result = clip_near(points, .5)
        self.assertEqual(result, [[0, 0, .5], [1, 0, 1], [0, 1, 1], [-.5, .5, .5]])
        self.assertEqual(points, [[-1, 0, 0], [1, 0, 1], [0, 1, 1]])
        self.assertEqual(clip_near([[0, 0, 0], [1, 0, 0], [0, 1, 0]], .1), [])

    def test_invalid_projection_and_near_plane_rejected(self):
        for point in ([0, 0, 0], [0, 0, -1], [math.inf, 0, 1]):
            with self.assertRaises(ValueError): project(point, 960, 600, 90)
        for fov in (0, 180, math.nan, True):
            with self.assertRaises(ValueError): project([0, 0, 1], 960, 600, fov)
        for near in (0, 2, math.nan, True):
            with self.assertRaises(ValueError): clip_near([[0, 0, 1]]*3, near)


if __name__ == '__main__':
    unittest.main()
