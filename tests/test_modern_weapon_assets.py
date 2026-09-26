"""Original modern geometry only; no game resources are opened."""
from collections import Counter
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

RECIPES={
    'FG42':(25,31,(876,564),'111c3e8cb882bc67b53415097165f6ca8f63533af528ac554e6e16aa57091aba'),
    'MG34_PORTABLE':(33,39,(1536,960),'d45597f0c720991a468fe8064c5ee972efeb884dc1be6acef45bb06dfc924dac'),
}


def volume(mesh):
    return sum(sum(a*b for a,b in zip(mesh.points[i],asset.cross(mesh.points[j],mesh.points[k])))
               for i,j,k in mesh.triangles)/6


class ModernPartTransformTests(unittest.TestCase):
    def setUp(self):
        self.mesh=asset.profile_mesh({'name':'MOD_test','width':.2,
                       'outline_yz':[[0,0],[.3,0],[.3,.4],[0,.4]]},1)

    def test_transform_order_is_xyz_then_translation_and_never_mutates_source(self):
        original=list(self.mesh.points)
        result=asset.transform_mesh(self.mesh,{'rotation_degrees':[0,0,90],'translation':[1,2,3]})
        for before,after in zip(original,result.points):
            expected=(-before[1]+1,before[0]+2,before[2]+3)
            for left,right in zip(expected,after):self.assertAlmostEqual(left,right)
        self.assertEqual(self.mesh.points,original)
        self.assertEqual(result.triangles,self.mesh.triangles)
        self.assertIs(asset.transform_mesh(self.mesh,None),self.mesh)

    def test_rigid_transform_preserves_distances_orientation_and_volume(self):
        result=asset.transform_mesh(self.mesh,{'rotation_degrees':[33,-26,91],'translation':[.02,-.03,.01]})
        self.assertAlmostEqual(volume(result),volume(self.mesh))
        result.validate()
        for i in range(len(result.points)):
            for j in range(i):
                self.assertAlmostEqual(math.dist(result.points[i],result.points[j]),
                                       math.dist(self.mesh.points[i],self.mesh.points[j]))
        for vert in result.expanded():self.assertAlmostEqual(sum(v*v for v in vert[3:6]),1)

    def test_scale_reflections_nonfinite_and_malformed_transforms_are_refused(self):
        for spec in ([],{'scale':[-1,1,1]},{'rotation_degrees':[361,0,0]},
                     {'rotation_degrees':[True,0,0]},{'translation':[0,0]},
                     {'translation':[0,float('nan'),0]},{'translation':[0,float('inf'),0]}):
            with self.subTest(spec=spec),self.assertRaises(ValueError):asset.transform_mesh(self.mesh,spec)


class ModernWeaponAssetTests(unittest.TestCase):
    def recipes(self):
        for name,expected in RECIPES.items():
            yield name,json.loads((ROOT/'experimental'/name/'modern-world-model.json').read_text(encoding='utf-8')),expected

    def test_original_recipes_have_no_commercial_binding_and_distinct_parts(self):
        for name,recipe,(parts,nodes,lods,digest) in self.recipes():
            self.assertEqual(recipe['provenance'],'MODERNE')
            self.assertEqual(recipe['runtime_status'],'pending')
            self.assertTrue(recipe['name'].startswith('PROTOTYPE_HERITAGE_'))
            self.assertNotIn('weapon_id',recipe);self.assertNotIn('textures',recipe)
            self.assertEqual(len(recipe['parts']),parts)
            names={p['name'] for p in recipe['parts']}
            self.assertEqual(len(names),parts)
            self.assertIn('MOD_side_magazine' if name=='FG42' else 'MOD_side_drum',names)
            self.assertEqual(len(recipe['anchors']),5)

    def test_both_lods_are_closed_non_degenerate_and_outward_after_transform(self):
        for name,recipe,(_,_,expected,_) in self.recipes():
            meshes=asset.build_meshes(recipe)
            self.assertEqual(tuple(sum(len(pair[level].triangles) for pair in meshes) for level in (0,1)),expected)
            for pair in meshes:
                for mesh in pair:
                    with self.subTest(recipe=name,part=mesh.name):
                        mesh.validate()
                        edges=Counter((a,b) for face in mesh.triangles for a,b in zip(face,face[1:]+face[:1]))
                        self.assertTrue(all(n==1 and edges[b,a]==1 for (a,b),n in edges.items()))
                        self.assertGreater(volume(mesh),0)
                        for vert in mesh.expanded():
                            self.assertTrue(all(math.isfinite(v) for v in vert))
                            self.assertAlmostEqual(sum(v*v for v in vert[3:6]),1)

    def test_two_independent_readers_and_stable_native_fingerprints(self):
        for name,recipe,(parts,nodes,lods,digest) in self.recipes():
            data=asset.encode_4ds(recipe,asset.build_meshes(recipe))
            parsed=parse_4ds_nodes(data)
            self.assertEqual(parsed['node_count'],nodes)
            self.assertEqual(parsed['material_count'],5)
            self.assertEqual(parsed['has_animation'],0)
            self.assertEqual(hashlib.sha256(data).hexdigest(),digest)
            self.assertEqual(data,asset.encode_4ds(recipe,asset.build_meshes(recipe)))
            self.assertTrue(all(n['parent_id']==1 for n in parsed['nodes'][1:]))
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'original.4ds.disabled';path.write_bytes(data)
                vertices,faces,names=parse_geometry(path)
            self.assertEqual(len(faces),lods[0]);self.assertEqual(len(vertices),3*lods[0])
            self.assertEqual(len(names),nodes)

    def test_generated_outputs_stay_disabled_and_do_not_read_game_assets(self):
        for name,recipe,_ in self.recipes():
            with tempfile.TemporaryDirectory() as directory:
                output=Path(directory)/'fresh'
                report=asset.build(recipe,output)
                for field in ('commercial_assets_read','game_modified','game_launched','playable_weapon','animation_binding'):
                    self.assertFalse(report[field])
                self.assertEqual(len(list(output.glob('*.4ds.disabled'))),1)
                self.assertEqual(len(list(output.glob('*.4ds'))),0)
                self.assertEqual(len(report['files']),4)
                with self.assertRaises(FileExistsError):asset.build(recipe,output)

    def test_existing_benelli_geometry_is_byte_identical_without_part_transforms(self):
        recipe=json.loads(asset.RECIPE.read_text(encoding='utf-8'))
        data=asset.encode_4ds(recipe,asset.build_meshes(recipe))
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         '6bc815610019739adc101d3e00319fa7819dd3d436b05e66d0521d258f291c8c')


if __name__=='__main__':unittest.main()
