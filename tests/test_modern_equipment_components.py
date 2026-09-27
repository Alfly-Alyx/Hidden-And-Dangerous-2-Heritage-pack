"""Original visual equipment partitioning; no commercial fixture or game."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_modern_asset as asset
from build_modern_equipment_components import compile_components,build,DIRECTORY,CASES,PARTS
from menu_gui_audit import parse_4ds_nodes
from model_wireframe import parse as read_geometry

HASHES={
    'F35':('f9ae716954711af8b8d2f35295b9efdd48be5351069185294185f6ad2eb34017',
           '6f998142fdaab2bc84010e184c95d0e8796ebc4326f34d2b0384161304ae7a7b',
           '55f7285f2e09b68d1f091b2ad878193a1a2b1a66df9295cc76eecf160b47d54e'),
    'F2':('7799824e1da25e40932903eee673b303720a9b6ef3d132a0b73870f9e2375364',
          'b1d169656976965188d6660a7ecf041764fa131a19f30b62dfc97ef325a17a0f',
          'b71aed7f5507f2a5a73647f142ccdfadfb72b83405a28945c610129dc458e2fb')}


def inputs(case):
    stem=CASES[case]
    return (json.loads((DIRECTORY/f'modern-{stem}-world.json').read_text(encoding='utf-8')),
            json.loads((DIRECTORY/f'modern-{stem}-components.json').read_text(encoding='utf-8')))


class ComponentTests(unittest.TestCase):
    def test_six_models_are_stable_disabled_static_native_components(self):
        for case in CASES:
            recipe,spec=inputs(case);products,report=compile_components(recipe,spec)
            for role,digest in zip(PARTS,HASHES[case]):
                product=products[role];parsed=parse_4ds_nodes(product['data'])
                self.assertEqual(hashlib.sha256(product['data']).hexdigest(),digest)
                self.assertEqual(parsed['has_animation'],0);self.assertEqual(parsed['material_count'],5)
                self.assertTrue(parsed['nodes'][0]['name'].startswith('PROTOTYPE_HERITAGE_'))
                self.assertTrue(all(node['parent_id']==1 for node in parsed['nodes'][1:]))
                self.assertLessEqual(len(product['report']['alias']),19)

    def test_every_mesh_and_source_anchor_is_owned_exactly_once(self):
        for case in CASES:
            recipe,spec=inputs(case);products,report=compile_components(recipe,spec)
            parts=[name for product in products.values() for name in product['report']['parts']]
            self.assertCountEqual(parts,[part['name'] for part in recipe['parts']])
            self.assertEqual(len(parts),len(set(parts)))
            self.assertTrue(report['all_source_anchors_owned_once'])
            self.assertEqual(products['hose']['report']['parts'],['MOD_hose'])

    def test_two_lod_triangle_totals_are_preserved(self):
        for case in CASES:
            recipe,spec=inputs(case);products,_=compile_components(recipe,spec)
            original=asset.build_meshes(recipe)
            for lod in (0,1):
                self.assertEqual(sum(p['report']['lod_triangles'][lod] for p in products.values()),
                                 sum(len(pair[lod].triangles) for pair in original))

    def test_native_node_bytes_except_local_positions_are_preserved(self):
        for case in CASES:
            recipe,spec=inputs(case);source=asset.encode_4ds(recipe,asset.build_meshes(recipe))
            original={node['name']:node for node in parse_4ds_nodes(source)['nodes']}
            products,_=compile_components(recipe,spec)
            for product in products.values():
                for node in parse_4ds_nodes(product['data'])['nodes'][1:]:
                    if node['name'] not in original:continue
                    before=original[node['name']];raw=bytearray(product['data'][node['start']:node['end']])
                    offset=node['position_offset']-node['start']
                    raw[offset:offset+12]=source[before['position_offset']:before['position_offset']+12]
                    self.assertEqual(bytes(raw),source[before['start']:before['end']])

    def test_reassembly_translations_restore_original_nodes(self):
        for case in CASES:
            recipe,spec=inputs(case);source=asset.encode_4ds(recipe,asset.build_meshes(recipe))
            original={node['name']:node for node in parse_4ds_nodes(source)['nodes']}
            products,report=compile_components(recipe,spec)
            self.assertLess(report['reassembly_max_error'],1e-6)
            for product in products.values():
                origin=product['report']['source_origin']
                for node in parse_4ds_nodes(product['data'])['nodes'][1:]:
                    if node['name'] not in original:continue
                    for value,shift,before in zip(node['position'],origin,original[node['name']]['position']):
                        self.assertAlmostEqual(value+shift,before,places=6)

    def test_secondary_reader_sees_all_geometry_without_missing_triangles(self):
        for case in CASES:
            recipe,spec=inputs(case);products,_=compile_components(recipe,spec)
            with tempfile.TemporaryDirectory() as directory:
                for role,product in products.items():
                    path=Path(directory)/(role+'.4ds.disabled');path.write_bytes(product['data'])
                    points,faces,names=read_geometry(path)
                    triangles=product['report']['lod_triangles'][0]
                    self.assertEqual(len(points),triangles*3);self.assertEqual(len(faces),triangles)
                    # This reader reports mesh-local vertices, before the new
                    # child translation. Compare those original source bytes.
                    expected=[row[:3] for part in product['report']['parts']
                        for pair in asset.build_meshes(recipe) if pair[0].name==part for row in pair[0].expanded()]
                    for actual,wanted in zip(points,expected):
                        self.assertEqual(actual,struct.unpack('<3f',struct.pack('<3f',*wanted)))

    def test_static_links_have_matching_endpoints_without_runtime_claim(self):
        for case in CASES:
            _,report=compile_components(*inputs(case))
            self.assertEqual(len(report['static_rest_links']),2)
            for link in report['static_rest_links']:
                self.assertLess(link['static_rest_error'],1e-6);self.assertFalse(link['runtime_link_created'])
            for flag in ('commercial_assets_read','game_modified','game_launched','player_skeleton_bound',
                         'hose_deformation_implemented','fpv_camera_calibrated','animations_created',
                         'effect_or_damage_bound','playable_weapon'):
                self.assertFalse(report[flag])
            self.assertTrue(all(row['target_player_bone'] is None for row in report['components'].values()))

    def test_recipes_and_specifications_are_not_mutated(self):
        recipe,spec=inputs('F35');before=deepcopy((recipe,spec));compile_components(recipe,spec)
        self.assertEqual((recipe,spec),before)

    def test_missing_duplicate_or_foreign_members_are_refused(self):
        recipe,spec=inputs('F35')
        changes=[]
        missing=deepcopy(spec);missing['components']['held']['parts'].pop();changes.append(missing)
        duplicate=deepcopy(spec);duplicate['components']['backpack']['parts'].append('MOD_hand_body');changes.append(duplicate)
        foreign=deepcopy(spec);foreign['components']['held']['parts'][0]='Unknown';changes.append(foreign)
        anchor=deepcopy(spec);anchor['components']['held']['anchors'].pop();changes.append(anchor)
        for changed in changes:
            with self.assertRaises(ValueError):compile_components(recipe,changed)

    def test_alias_collisions_unsafe_names_and_invented_player_binding_are_refused(self):
        recipe,spec=inputs('F35')
        for alias in ('../escape','PROTOTYPE_'+'A'*20,spec['components']['held']['alias']):
            changed=deepcopy(spec);changed['components']['backpack']['alias']=alias
            with self.assertRaises(ValueError):compile_components(recipe,changed)
        changed=deepcopy(spec);changed['components']['held']['player_bone']='invented'
        with self.assertRaises(ValueError):compile_components(recipe,changed)
        changed=deepcopy(spec);changed['components']['held']['origin_anchor']='MOD_muzzle_anchor'
        with self.assertRaises(ValueError):compile_components(recipe,changed)

    def test_source_pin_and_modern_pending_provenance_are_required(self):
        recipe,spec=inputs('F35')
        for changes in ({'source_model_sha256':'0'*64},{'provenance':'OFFICIEL'},{'runtime_status':'validated'},
                        {'components':{}},{'item_id':359}):
            changed=deepcopy(spec);changed.update(changes)
            with self.assertRaises(ValueError):compile_components(recipe,changed)

    def test_exports_are_disabled_and_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'fresh';report=build(*inputs('F35'),output)
            self.assertEqual(len(list(output.iterdir())),13)
            self.assertEqual(len(list(output.glob('*.4ds.disabled'))),3)
            self.assertFalse(list(output.glob('*.4ds')))
            self.assertEqual(len(report['files']),12)
            with self.assertRaises(FileExistsError):build(*inputs('F35'),output)


if __name__=='__main__':unittest.main()
