"""Source-free decorative geometry; never a weapon/gameplay fixture."""
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

EXPECTED={
    'garota':(7,10,4,(732,388),'f51cfaf83e947527849c056538206dc7a7feaa840ffbd7c14ba06d9ae64a5cd4'),
    'zk383':(33,39,5,(1120,720),'1730926a7468d5a91ec4ae19467ee2613905146caa329f7c0a163f09a9c30032'),
}


def recipe(name):
    return json.loads((ROOT/'experimental/GAROTA_AND_ZK383'/f'modern-{name}-world.json').read_text(encoding='utf-8'))


class ModernGarotaZK383Tests(unittest.TestCase):
    def test_separate_modern_static_recipes_without_commercial_or_gameplay_binding(self):
        self.assertNotEqual(recipe('garota')['name'],recipe('zk383')['name'])
        for name,(pieces,nodes,materials,lods,digest) in EXPECTED.items():
            r=recipe(name)
            self.assertEqual(r['provenance'],'MODERNE')
            self.assertEqual(r['runtime_status'],'pending')
            self.assertEqual(len(r['parts']),pieces)
            self.assertEqual(len(r['materials']),materials)
            self.assertEqual(len(r['anchors'])+pieces+1,nodes)
            for field in ('weapon_id','item_id','damage','textures','sounds','animation'):
                self.assertNotIn(field,r)

    def test_native_fingerprints_lods_and_two_independent_readers(self):
        for name,(pieces,nodes,materials,lods,digest) in EXPECTED.items():
            r=recipe(name);meshes=asset.build_meshes(r);raw=asset.encode_4ds(r,meshes)
            parsed=parse_4ds_nodes(raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
            self.assertEqual(raw,asset.encode_4ds(r,asset.build_meshes(r)))
            self.assertEqual(parsed['node_count'],nodes)
            self.assertEqual(parsed['material_count'],materials)
            self.assertFalse(parsed['has_animation'])
            self.assertTrue(all(n['parent_id']==1 for n in parsed['nodes'][1:]))
            self.assertEqual(tuple(sum(len(pair[i].triangles) for pair in meshes) for i in (0,1)),lods)
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'original.4ds.disabled';path.write_bytes(raw)
                vertices,faces,names=parse_geometry(path)
            self.assertEqual((len(vertices),len(faces),len(names)),(3*lods[0],lods[0],nodes))

    def test_every_piece_is_closed_outward_and_nondegenerate_at_both_lods(self):
        for name in EXPECTED:
            for pair in asset.build_meshes(recipe(name)):
                for mesh in pair:
                    with self.subTest(recipe=name,piece=mesh.name):
                        mesh.validate()
                        edges=Counter((a,b) for face in mesh.triangles for a,b in zip(face,face[1:]+face[:1]))
                        self.assertTrue(all(n==1 and edges[b,a]==1 for (a,b),n in edges.items()))
                        volume=sum(sum(a*b for a,b in zip(mesh.points[i],asset.cross(mesh.points[j],mesh.points[k])))
                                   for i,j,k in mesh.triangles)/6
                        self.assertGreater(volume,0)
                        for vertex in mesh.expanded():
                            self.assertTrue(all(math.isfinite(v) for v in vertex))
                            self.assertAlmostEqual(sum(v*v for v in vertex[3:6]),1)

    def test_zk_visual_features_are_explicit_modern_parts_not_stolen_assets(self):
        r=recipe('zk383');parts={p['name']:p for p in r['parts']}
        self.assertEqual(r['reference']['url'],'https://www.vhu.cz/samopal-zk-383/')
        self.assertEqual(len([p for p in parts if p.startswith('MOD_shroud_rail_')]),8)
        meshes={high.name:high for high,low in asset.build_meshes(r)}
        magazine=meshes['MOD_side_magazine'].points
        self.assertLess(max(p[0] for p in magazine),0)
        self.assertLess(min(p[2] for p in magazine),0)
        self.assertIn('MOD_bipod_left',meshes);self.assertIn('MOD_bipod_right',meshes)
        points=[p for mesh in meshes.values() for p in mesh.points]
        self.assertAlmostEqual(max(p[1] for p in points)-min(p[1] for p in points),.875)
        self.assertTrue(all(parts[n]['inner_ratio']>0 for n in parts if n.startswith('MOD_shroud_') and 'rail' not in n))

    def test_garota_is_static_display_with_two_handles_and_no_character_target(self):
        r=recipe('garota');parts={p['name']:p for p in r['parts']}
        self.assertEqual(len(r['anchors']),2)
        self.assertEqual(parts['MOD_slack_cord']['kind'],'sweep')
        self.assertFalse(parts['MOD_slack_cord'].get('closed',False))
        self.assertEqual(parts['MOD_slack_cord']['path'][0],[-.14,.065,0])
        self.assertEqual(parts['MOD_slack_cord']['path'][-1],[.14,.065,0])
        self.assertTrue(all('not a character bone' in a['purpose'] for a in r['anchors']))

    def test_builds_are_source_free_disabled_and_refuse_overwrite(self):
        for name in EXPECTED:
            with tempfile.TemporaryDirectory() as directory:
                output=Path(directory)/'fresh';report=asset.build(recipe(name),output)
                for key in ('commercial_assets_read','game_modified','game_launched','playable_weapon','animation_binding'):
                    self.assertFalse(report[key])
                self.assertEqual(len(list(output.glob('*.4ds.disabled'))),1)
                self.assertEqual(len(list(output.glob('*.4ds'))),0)
                self.assertEqual(len(report['files']),4)
                for filename,digest in report['files'].items():
                    self.assertEqual(hashlib.sha256((output/filename).read_bytes()).hexdigest(),digest)
                with self.assertRaises(FileExistsError):asset.build(recipe(name),output)


if __name__=='__main__':unittest.main()
