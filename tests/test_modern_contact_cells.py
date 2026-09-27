"""Invented finite surfaces and hollow rings; no game geometry."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_modern_asset import Mesh,ring_mesh
from convex_contact import penetration,surface_measure
from modern_contact_cells import ring_cells,cells,surface_for_cells
from fit_rigid_weapon_grips import point_triangle_distance_squared,finite_digit_gaps,adjustment
from fit_rigid_elbow_poles import candidate_poles


class ModernContactCellsTests(unittest.TestCase):
    def fixture(self,hollow=.5,lod=0):
        part={'name':'MOD_tube','kind':'rings','segments':12,'inner_ratio':hollow,
              'sections':[[0,0,0,1],[1,0,0,1],[2,0,0,.8]]}
        source=ring_mesh(part,1,bool(lod));points=[(source.points[i][0],source.points[i][2],source.points[i][1])
                                                for face in source.triangles for i in face]
        mesh=Mesh(part['name'],1,points,[(i,i+2,i+1) for i in range(0,len(points),3)])
        return part,mesh

    def test_hollow_cells_cover_wall_but_preserve_cavity_both_lods(self):
        for lod in (0,1):
            part,mesh=self.fixture(lod=lod);volumes=ring_cells(mesh,part,lod)
            count=12 if lod==0 else 6;self.assertEqual(len(volumes),2*count)
            theta=math.pi/count
            wall=(.7*math.cos(theta),.7*math.sin(theta),.5)
            self.assertGreater(max(penetration(wall,v['support']) for v in volumes),0)
            self.assertEqual(max(penetration((0,0,.5),v['support']) for v in volumes),0)
            self.assertEqual(max(penetration((2,0,.5),v['support']) for v in volumes),0)
            self.assertTrue(all(len(v['boundary_support'])<len(v['support']) for v in volumes))

    def test_serialized_points_are_used_without_replacing_them_with_recipe_coordinates(self):
        part,mesh=self.fixture();moved=deepcopy(mesh)
        moved.points=[(x+.2,y-.1,z+.3) for x,y,z in moved.points]
        original=ring_cells(mesh,part);actual=ring_cells(moved,part)
        for a,b in zip(original,actual):
            for p,q in zip(a['bounds'],b['bounds']):
                for i,delta in enumerate((.2,-.1,.3)):self.assertAlmostEqual(q[i]-p[i],delta)

    def test_internal_radial_and_station_seams_do_not_erase_penetrating_triangles(self):
        part,mesh=self.fixture();volumes=ring_cells(mesh,part)
        for triangle in ([(.65,0,.3),(.85,0,.3),(.75,0,.7)],
                         [(.65,.05,1),(.8,.05,1),(.7,.2,1)]):
            results=[surface_measure(triangle,[(0,1,2)],v['support'],boundary_support=v['boundary_support']) for v in volumes]
            self.assertGreater(sum(r['penetrating_triangles'] for r in results),0)
            self.assertGreater(max(r['max_depth_lower_bound'] for r in results),.05)
        cavity=[(-.1,-.1,.5),(.1,-.1,.5),(0,.1,.5)]
        self.assertEqual(sum(surface_measure(cavity,[(0,1,2)],v['support'],boundary_support=v['boundary_support'])['penetrating_triangles']
                             for v in volumes),0)

    def test_solid_multisection_rings_have_filled_centers(self):
        part,mesh=self.fixture(hollow=0);volumes=ring_cells(mesh,part)
        point=(.1,.1,.5)
        self.assertGreater(max(penetration(point,v['support']) for v in volumes),0)
        triangle=[(-.1,-.1,.5),(.1,-.1,.5),(0,.1,.5)]
        self.assertGreater(sum(surface_measure(triangle,[(0,1,2)],v['support'],boundary_support=v['boundary_support'])['penetrating_triangles']
                               for v in volumes),0)

    def test_unreviewed_topology_and_boundary_planes_refused(self):
        part,mesh=self.fixture()
        for lod in (-1,2,True):
            with self.assertRaises(ValueError):ring_cells(mesh,part,lod)
        bad=deepcopy(mesh);bad.points.pop()
        with self.assertRaises(ValueError):ring_cells(bad,part)
        bad=deepcopy(mesh);bad.points[0]=(3,3,3)
        with self.assertRaises(ValueError):ring_cells(bad,part)
        volume=ring_cells(mesh,part)[0]
        with self.assertRaises(ValueError):surface_measure([(0,0,0)]*3,[(0,1,2)],volume['support'],boundary_support=[])

    def test_finite_triangle_distance_respects_edges_vertices_and_face_not_infinite_planes(self):
        face=((0,0,0),(1,0,0),(0,1,0))
        for point,distance in (((.2,.2,2),4),((-.5,0,0),.25),((2,0,0),1),((1,1,0),.5),((0,0,0),0)):
            self.assertAlmostEqual(point_triangle_distance_squared(point,*face),distance)
        gaps=finite_digit_gaps([(2,0,0),(.2,.2,0)],{0:[0],1:[1]},[face])
        self.assertEqual(gaps[0],1);self.assertAlmostEqual(gaps[1],0,places=15)

    def test_optimizer_adjustments_are_bounded_modern_choices(self):
        values=[0,0,0,0,0,0,70,50,20,0,0,0]
        self.assertEqual(adjustment(values,'R')['finger_curl_degrees'],[-70,-50,-20])
        for axis,value in ((0,.061),(3,91),(6,111),(9,66),(10,True),(11,math.nan)):
            bad=values[:];bad[axis]=value
            with self.assertRaises(ValueError):adjustment(bad,'L')

    def test_elbow_candidates_preserve_seed_are_unique_and_stay_in_authored_domain(self):
        seed=[.38,-.28,-.12]
        self.assertEqual(len(candidate_poles(seed)),27);self.assertEqual(len(candidate_poles(seed,wide=True)),125)
        for wide in (False,True):
            rows=candidate_poles(seed,wide=wide)
            self.assertEqual(rows[0],seed);self.assertEqual(len(rows),len({tuple(p) for p in rows}))
            self.assertTrue(all(abs(v)<=1 for p in rows for v in p))
        for bad in ([True,0,0],[1.1,0,0],[0,math.nan,0]):
            with self.assertRaises(ValueError):candidate_poles(bad)
        with self.assertRaises(ValueError):candidate_poles(seed,wide=1)

    def test_compacted_broad_phase_preserves_exact_surface_results_including_cell_seams(self):
        part,mesh=self.fixture();volumes=ring_cells(mesh,part)
        for points in ([(.65,0,.3),(.85,0,.3),(.75,0,.7)],
                       [(-2,-2,.5),(2,-2,.5),(0,4,.5)],[(3,3,3),(3,4,3),(4,3,3)]):
            original=[surface_measure(points,[(0,1,2)],v['support'],volume_bounds=v['bounds'],boundary_support=v['boundary_support'])
                      for v in volumes]
            compact=surface_for_cells(points,[(0,1,2)],volumes)
            self.assertEqual(compact['penetrating_triangle_cells'],sum(r['penetrating_triangles'] for r in original))
            self.assertEqual(compact['max_cell_boundary_depth'],max(r['max_depth_lower_bound'] for r in original))
            self.assertEqual(compact['inset_surface_area_sum'],sum(r['inset_surface_area'] for r in original))
        self.assertEqual(compact['broad_phase_candidate_triangle_cells'],0)
        with self.assertRaises(ValueError):surface_for_cells(points,[(0,1,3)],volumes)
        with self.assertRaises(ValueError):surface_for_cells(points,[(0,1,2)],[])


if __name__=='__main__':unittest.main()
