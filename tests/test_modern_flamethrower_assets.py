"""Original non-functional game props and decorative planar tube topology."""
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_modern_asset as asset
from menu_gui_audit import parse_4ds_nodes
from model_wireframe import parse as parse_geometry

DIRECTORY=ROOT/'experimental/FLAMMENWERFER_35_AND_NO2'
RECIPES={
    'modern-flmwr35-world.json':(21,(1504,856),244661,'a4b0aa9811cf0f69b1fe678813d933aeec2c4d230ec1a6822952e3ce9f21d3c6'),
    'modern-flmthr2-world.json':(19,(1464,848),239502,'2d2bbb39e6c2774c56c713047c073d8b95e803591cfa692e6cb7739de1943a3b'),
}


def assert_surface(test,mesh,characteristic=2):
    mesh.validate()
    directed=Counter((a,b) for face in mesh.triangles for a,b in zip(face,face[1:]+face[:1]))
    test.assertTrue(all(n==1 and directed[b,a]==1 for (a,b),n in directed.items()))
    edges={tuple(sorted(edge)) for edge in directed}
    test.assertEqual(len(mesh.points)-len(edges)+len(mesh.triangles),characteristic)
    volume=sum(sum(a*b for a,b in zip(mesh.points[i],asset.cross(mesh.points[j],mesh.points[k])))
               for i,j,k in mesh.triangles)/6
    test.assertGreater(volume,0)
    for vertex in mesh.expanded():
        test.assertTrue(all(math.isfinite(v) for v in vertex))
        test.assertAlmostEqual(sum(v*v for v in vertex[3:6]),1)


class PlanarSweepTests(unittest.TestCase):
    def setUp(self):
        self.part={'name':'MOD_tube','segments':12,'radius':.025,'plane_normal':[1,0,0],
                   'path':[[0,0,0],[0,.25,0],[0,.5,.12],[0,.55,.4]]}

    def test_open_path_caps_are_watertight_and_outward_at_both_lods(self):
        for low,count in ((False,12),(True,6)):
            mesh=asset.sweep_mesh(self.part,1,low)
            assert_surface(self,mesh)
            self.assertEqual(len(mesh.points),4*count+2)
            self.assertEqual(len(mesh.triangles),8*count)

    def test_closed_ring_has_no_duplicate_seam_or_caps(self):
        part=copy.deepcopy(self.part)
        part.update(closed=True,radius=.08,plane_normal=[0,1,0],
                    path=[[.3*math.cos(i*math.pi/8),0,.3*math.sin(i*math.pi/8)] for i in range(16)])
        for reverse in (False,True):
            if reverse:part['path'].reverse()
            for low,count in ((False,12),(True,6)):
                mesh=asset.sweep_mesh(part,1,low)
                assert_surface(self,mesh,0)
                self.assertEqual(len(mesh.points),16*count)
                self.assertEqual(len(mesh.triangles),32*count)

    def test_plane_normal_scale_and_reversal_do_not_change_surface_bounds(self):
        reference=asset.sweep_mesh(self.part,1)
        for normal in ([20,0,0],[-1,0,0]):
            part=copy.deepcopy(self.part);part['plane_normal']=normal
            mesh=asset.sweep_mesh(part,1)
            assert_surface(self,mesh)
            for axis in range(3):
                for fn in (min,max):
                    self.assertAlmostEqual(fn(p[axis] for p in mesh.points),fn(p[axis] for p in reference.points))

    def test_invalid_paths_radii_and_frames_are_refused(self):
        invalid=({'radius':0},{'radius':float('nan')},{'radius':.5},
                 {'segments':True},{'segments':5},{'closed':1},
                 {'plane_normal':[0,0,0]},{'plane_normal':[0,1,0]},
                 {'path':[[0,0,0]]},{'path':[[0,0,0],[0,0,0]]},
                 {'path':[[0,0,0],[0,.25,0],[0,.1,0]]},
                 {'path':[[0,0,0],[0,.25,0],[0,.25,.01]]},
                 {'path':[[0,0,0],[0,.25,0],[.01,.5,.2]]})
        for changes in invalid:
            part=copy.deepcopy(self.part);part.update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):asset.sweep_mesh(part,1)


class ModernFlamethrowerAssetsTests(unittest.TestCase):
    def recipes(self):
        for filename,expected in RECIPES.items():
            yield filename,json.loads((DIRECTORY/filename).read_text(encoding='utf-8')),expected

    def test_distinct_modern_silhouettes_and_no_functional_binding(self):
        for filename,recipe,(parts,lods,size,digest) in self.recipes():
            self.assertEqual(recipe['provenance'],'MODERNE')
            self.assertEqual(recipe['runtime_status'],'pending')
            self.assertTrue(recipe['name'].startswith('PROTOTYPE_HERITAGE_'))
            self.assertEqual(len(recipe['parts']),parts)
            self.assertEqual(len(recipe['materials']),5)
            self.assertEqual(len(recipe['anchors']),5)
            for field in ('weapon_id','item_id','ammo_id','fuel','damage','sound','textures','animations'):
                self.assertNotIn(field,recipe)
            names={p['name'] for p in recipe['parts']}
            self.assertIn('MOD_ring_pack' if 'flmthr2' in filename else 'MOD_main_pack',names)
            self.assertIn('MOD_hose',names)

    def test_each_lod_is_closed_and_oriented_with_ring_genus_preserved(self):
        for filename,recipe,(_,expected,_,_) in self.recipes():
            meshes=asset.build_meshes(recipe)
            self.assertEqual(tuple(sum(len(pair[i].triangles) for pair in meshes) for i in (0,1)),expected)
            for part,pair in zip(recipe['parts'],meshes):
                torus=part.get('closed',False) or bool(part.get('inner_ratio',0))
                for mesh in pair:
                    with self.subTest(filename=filename,part=part['name']):
                        assert_surface(self,mesh,0 if torus else 2)

    def test_native_format_stable_hashes_and_second_geometry_reader(self):
        for filename,recipe,(parts,lods,size,digest) in self.recipes():
            data=asset.encode_4ds(recipe,asset.build_meshes(recipe))
            parsed=parse_4ds_nodes(data)
            self.assertEqual(parsed['node_count'],parts+6)
            self.assertEqual(parsed['material_count'],5)
            self.assertEqual(parsed['has_animation'],0)
            self.assertTrue(all(n['parent_id']==1 for n in parsed['nodes'][1:]))
            self.assertEqual(len(data),size)
            self.assertEqual(hashlib.sha256(data).hexdigest(),digest)
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'modern.4ds.disabled';path.write_bytes(data)
                vertices,faces,names=parse_geometry(path)
            self.assertEqual(len(vertices),3*lods[0]);self.assertEqual(len(faces),lods[0])
            self.assertEqual(len(names),parts+6)

    def test_outputs_remain_disabled_and_refuse_overwrite(self):
        for filename,recipe,(_,lods,size,digest) in self.recipes():
            with tempfile.TemporaryDirectory() as directory:
                target=Path(directory)/'fresh'
                report=asset.build(recipe,target)
                self.assertEqual(report['model_sha256'],digest)
                self.assertEqual(report['size'],size)
                self.assertEqual(report['lod_triangles'],list(lods))
                for field in ('commercial_assets_read','game_modified','game_launched','playable_weapon','animation_binding'):
                    self.assertFalse(report[field])
                self.assertEqual(len(list(target.glob('*.4ds.disabled'))),1)
                self.assertFalse(list(target.glob('*.4ds')))
                with self.assertRaises(FileExistsError):asset.build(recipe,target)


if __name__=='__main__':unittest.main()
