from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from convex_contact import planes,penetration,measure,surface_measure,clip_polygon,polygon_area


class ConvexContactTests(unittest.TestCase):
    def fixture(self):
        points = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                  (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
        faces = [(0,1,2),(0,2,3),(4,6,5),(4,7,6),(0,4,5),(0,5,1),
                 (1,5,6),(1,6,2),(2,6,7),(2,7,3),(3,7,4),(3,4,0)]
        return points,faces

    def test_inside_face_edge_outside_and_orientation_independence(self):
        points,faces=self.fixture()
        for faces in (faces,[tuple(reversed(f)) for f in faces]):
            support=planes(points,faces)
            for point,expected in (((0,0,0),1),((.75,.1,.2),.25),((1,0,0),0),((1,1,1),0),((2,0,0),0)):
                self.assertEqual(penetration(point,support),expected)

    def test_duplicate_face_vertices_are_joined_geometrically(self):
        points,faces=self.fixture()
        expanded=[points[i] for f in faces for i in f]
        remapped=[(i,i+1,i+2) for i in range(0,len(expanded),3)]
        self.assertEqual(penetration((0,0,0),planes(expanded,remapped)),1)

    def test_open_flat_degenerate_nonconvex_and_nonfinite_fail_closed(self):
        points,faces=self.fixture()
        with self.assertRaises(ValueError): planes(points,faces[:-1])
        with self.assertRaises(ValueError): planes(points,faces+[(0,0,1)])
        flat=[(p[0],p[1],0) for p in points]
        with self.assertRaises(ValueError): planes(flat,faces)
        dented=points[:];dented[6]=(0,0,0)
        with self.assertRaises(ValueError): planes(dented,faces)
        bad=points[:];bad[0]=(float('nan'),0,0)
        with self.assertRaises(ValueError): planes(bad,faces)

    def test_measure_does_not_claim_surface_or_complete_collision(self):
        points,faces=self.fixture()
        row=measure([(0,0,0),(.5,0,0),(2,0,0)],planes(points,faces))
        self.assertEqual((row['samples'],row['inside'],row['max_depth'],row['sum_depth']),(3,2,1,1.5))
        self.assertFalse(row['surface_crossings_checked'])
        self.assertFalse(row['full_contact_qualified'])
        with self.assertRaises(ValueError): measure([],planes(points,faces),True)

    def test_surface_crossing_detected_when_every_vertex_is_outside(self):
        points,faces=self.fixture();support=planes(points,faces)
        triangle=[(-3,-2,0),(3,-2,0),(0,4,0)]
        self.assertEqual(measure(triangle,support)['inside'],0)
        result=surface_measure(triangle,[(0,1,2)],support)
        self.assertEqual(result['penetrating_triangles'],1)
        self.assertAlmostEqual(result['max_depth_lower_bound'],1,places=6)
        self.assertAlmostEqual(result['inset_surface_area'],4*(1-1e-5)**2,places=6)
        self.assertTrue(result['surface_crossings_checked'])
        self.assertFalse(result['full_contact_qualified'])

    def test_tangent_outside_and_degenerate_surfaces_are_not_penetration(self):
        points,faces=self.fixture();support=planes(points,faces)
        for triangle in ([(-3,-2,1),(3,-2,1),(0,4,1)],
                         [(2,0,0),(2,1,0),(2,0,1)],[(0,0,0)]*3):
            self.assertEqual(surface_measure(triangle,[(0,1,2)],support)['penetrating_triangles'],0)

    def test_fully_inside_triangle_depth_and_surface_input_refusals(self):
        points,faces=self.fixture();support=planes(points,faces)
        triangle=[(-.1,-.1,.75),(.1,-.1,.75),(0,.1,.75)]
        result=surface_measure(triangle,[(0,1,2)],support)
        self.assertAlmostEqual(result['max_depth_lower_bound'],.25,places=6)
        self.assertAlmostEqual(polygon_area(clip_polygon(triangle,support)),.02)
        with self.assertRaises(ValueError):surface_measure(triangle,[(0,1,4)],support)
        with self.assertRaises(ValueError):surface_measure(triangle,[(0,1,2)],support,True)

    def test_supplied_exact_volume_bounds_preserve_crossing_result(self):
        points,faces=self.fixture();support=planes(points,faces)
        for triangle in ([(-3,-2,0),(3,-2,0),(0,4,0)],[(2,0,0),(2,1,0),(2,0,1)]):
            expected=surface_measure(triangle,[(0,1,2)],support)
            self.assertEqual(surface_measure(triangle,[(0,1,2)],support,
                                             volume_bounds=[(-1,-1,-1),(1,1,1)]),expected)
        with self.assertRaises(ValueError):
            surface_measure(points,faces,support,volume_bounds=[(1,1,1),(-1,-1,-1)])


if __name__=='__main__': unittest.main()
