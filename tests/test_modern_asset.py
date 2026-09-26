import copy
from collections import Counter
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_modern_asset as asset
from menu_gui_audit import FourDsReader, parse_4ds_nodes, skip_material
from model_wireframe import parse as parse_geometry


class ModernAssetTests(unittest.TestCase):
    def setUp(self):
        self.recipe = json.loads(asset.RECIPE.read_text(encoding="utf-8"))
        self.meshes = asset.build_meshes(self.recipe)

    def test_recipe_does_not_claim_official_or_playable(self):
        self.assertEqual(self.recipe['provenance'], 'MODERNE')
        self.assertEqual(self.recipe['runtime_status'], 'pending')
        self.assertTrue(self.recipe['name'].startswith('PROTOTYPE_HERITAGE_'))
        self.assertNotIn('weapon_id', self.recipe)
        self.assertNotIn('textures', self.recipe)

    def test_static_native_model_and_independent_geometry_parser(self):
        data = asset.encode_4ds(self.recipe, self.meshes)
        parsed = parse_4ds_nodes(data)
        self.assertEqual(parsed['node_count'], 30)
        self.assertEqual(parsed['material_count'], 6)
        self.assertEqual(parsed['has_animation'], 0)
        self.assertEqual(parsed['nodes'][0]['parent_id'], 0)
        self.assertTrue(all(n['parent_id'] == 1 for n in parsed['nodes'][1:]))
        self.assertEqual(sum(n['frame_type'] == 6 for n in parsed['nodes']), 5)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.4ds.disabled'
            path.write_bytes(data)
            vertices, faces, names = parse_geometry(path)
        self.assertEqual(len(faces), 1264)
        self.assertEqual(len(vertices), len(faces)*3)
        self.assertEqual(len(names), 30)

    def test_lods_and_face_materials_are_really_serialized(self):
        data = asset.encode_4ds(self.recipe, self.meshes)
        parsed = parse_4ds_nodes(data)
        for node, meshes in zip(parsed['nodes'][1:], self.meshes):
            reader = FourDsReader(data)
            reader.position = node['name_offset'] + node['name_length']
            reader.take(reader.u8())
            self.assertEqual(reader.u16(), 0)
            self.assertEqual(reader.u8(), 2)
            for level, distance in zip(meshes, (25, 0)):
                self.assertEqual(struct.unpack('<f', reader.take(4))[0], distance)
                self.assertEqual(reader.u32(), 0)
                count = reader.u16()
                self.assertEqual(count, len(level.triangles)*3)
                reader.take(count*32)
                self.assertEqual(reader.u8(), 1)
                face_count = reader.u16()
                self.assertEqual(face_count, len(level.triangles))
                indices = struct.unpack('<' + 'H'*face_count*3, reader.take(face_count*6))
                self.assertEqual(indices, tuple(range(count)))
                self.assertEqual(reader.u16(), level.material)
            self.assertEqual(reader.position, node['end'])

    def test_materials_have_no_external_texture_names(self):
        data = asset.encode_4ds(self.recipe, self.meshes)
        reader = FourDsReader(data)
        reader.take(14)
        count = reader.u16()
        for _ in range(count):
            start = reader.position
            skip_material(reader)
            self.assertEqual(reader.position-start, 77)
            self.assertEqual(struct.unpack_from('<I', data, start)[0], 1)
        self.assertNotIn(b'.bmp', data)
        self.assertNotIn(b'.tga', data)

    def test_closed_consistently_wound_original_surfaces(self):
        for levels in self.meshes:
            for mesh in levels:
                edges = Counter((a, b) for f in mesh.triangles for a, b in zip(f, f[1:]+f[:1]))
                self.assertTrue(all(count == 1 and edges[b, a] == 1 for (a, b), count in edges.items()), mesh.name)
                volume = 0
                for face in mesh.triangles:
                    a, b, c = [mesh.points[i] for i in face]
                    volume += sum(x*y for x, y in zip(a, asset.cross(b, c))) / 6
                self.assertGreater(volume, 0, mesh.name)

    def test_flat_normals_are_unit_and_finite(self):
        for high, low in self.meshes:
            for level in (high, low):
                for vert in level.expanded():
                    self.assertEqual(len(vert), 8)
                    self.assertTrue(all(math.isfinite(v) for v in vert))
                    self.assertAlmostEqual(sum(n*n for n in vert[3:6]), 1)

    def test_lower_lod_is_smaller_and_same_bounds(self):
        self.assertEqual([sum(len(p[i].triangles) for p in self.meshes) for i in (0, 1)], [1264, 728])
        for axis in range(3):
            for fn in (min, max):
                high = fn(p[axis] for h, _ in self.meshes for p in h.points)
                low = fn(p[axis] for _, lo in self.meshes for p in lo.points)
                self.assertAlmostEqual(high, low)

    def test_determinism(self):
        self.assertEqual(asset.encode_4ds(self.recipe, self.meshes),
                         asset.encode_4ds(self.recipe, asset.build_meshes(copy.deepcopy(self.recipe))))
        self.assertEqual(asset.encode_obj(self.recipe, self.meshes), asset.encode_obj(self.recipe, self.meshes))

    def test_obj_uses_only_local_materials_and_valid_normals(self):
        obj, mtl = asset.encode_obj(self.recipe, self.meshes)
        lines = obj.splitlines()
        self.assertEqual(sum(s.startswith('v ') for s in lines), 3792)
        self.assertEqual(sum(s.startswith('vn ') for s in lines), 3792)
        self.assertEqual(sum(s.startswith('f ') for s in lines), 1264)
        self.assertNotIn('map_Kd', mtl)
        self.assertIn('MODERNE', obj)

    def test_rejects_invalid_or_misrepresented_recipe(self):
        for field, value in [('provenance','OFFICIEL'), ('runtime_status','passed'),
                             ('units','millimetres'), ('name','w_compass')]:
            recipe = copy.deepcopy(self.recipe)
            recipe[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                asset.build_meshes(recipe)
        for value in (float('nan'), float('inf'), True, '0.01'):
            recipe = copy.deepcopy(self.recipe)
            recipe['parts'][0]['width'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                asset.build_meshes(recipe)

    def test_rejects_invalid_geometry(self):
        for mutation in ('duplicate', 'clockwise', 'radius', 'material', 'empty', 'anchor'):
            recipe = copy.deepcopy(self.recipe)
            if mutation == 'duplicate': recipe['parts'][1]['name'] = recipe['parts'][0]['name']
            elif mutation == 'clockwise': recipe['parts'][0]['outline_yz'].reverse()
            elif mutation == 'radius': recipe['parts'][4]['sections'][0][3] = 0
            elif mutation == 'material': recipe['parts'][0]['material'] = 'absent'
            elif mutation == 'empty': recipe['parts'] = []
            else: recipe['anchors'][0]['name'] = recipe['parts'][0]['name']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                asset.build_meshes(recipe)

    def test_output_is_new_and_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('../escape', '..', '/outside', 'CON', 'AUX', 'name.4ds', 'C:escape'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    asset.output_directory(root, name)
            output = asset.output_directory(root, 'modern_demo')
            self.assertTrue(output.is_relative_to(root / '.analysis'))
            output.mkdir(parents=True)
            with self.assertRaises(ValueError):
                asset.output_directory(root, 'modern_demo')

    def test_build_manifest_and_preview_without_game(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'fresh'
            report = asset.build(self.recipe, output)
            self.assertFalse(report['game_modified'])
            self.assertFalse(report['commercial_assets_read'])
            self.assertFalse(report['playable_weapon'])
            self.assertEqual(report['runtime_status'], 'pending')
            self.assertEqual(len(report['files']), 4)
            from PIL import Image
            with Image.open(output / 'preview.png') as img:
                self.assertEqual(img.size, (1600, 900))
            self.assertTrue((output / (self.recipe['name'] + '.4ds.disabled')).is_file())
            self.assertFalse(list(output.glob('*.4ds')))
            with self.assertRaises(FileExistsError):
                asset.build(self.recipe, output)


if __name__ == '__main__':
    unittest.main()
