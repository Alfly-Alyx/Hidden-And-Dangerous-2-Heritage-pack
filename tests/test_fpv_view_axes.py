"""Original model/clip fixtures only: no commercial hands or animation keys."""
from copy import deepcopy
import json
import math
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from modern_fpv_axes import position, matrix, bounds, native_rotation, compile_view_rig, _remap_generated_model
from modern_fpv_geometry import geometry
from build_modern_equipment_fpv_rig import compile_flat_rig
from build_modern_equipment_assembly import compile_assembly, inputs
from build_equipment_fpv_animation import rebake_clip, numeric_world
from build_equipment_fpv_view_bank import converted_gear_tracks, view_grips, targets_at, preview_meshes
from build_equipment_hand_grips import RECIPE, effective_hands
from animation_tick_audit import model_poses
from hand_pose_ik import validate_basis, two_bone, cross, sub
from menu_gui_audit import parse_4ds_nodes
from ls3d_math_oracle import basis
from model_transform import matvec
from five_ds import parse_5ds
import modern_animation as motion
from ls3d_skin_oracle import transformed


class ViewAxisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(RECIPE.read_text(encoding='utf-8'))
        cls.cases = {}
        for case in ('F35', 'F2'):
            flat, original, report = compile_flat_rig(case)
            view, view_report = compile_view_rig(case)
            _, clips, _ = compile_assembly(*inputs(case))
            flat_clips = {name: rebake_clip(original, flat, report, raw)[0] for name, (_, raw) in clips.items()}
            cls.cases[case] = (flat, view, view_report, flat_clips)

    def test_all_model_bytes_restored_and_source_unchanged(self):
        for case, (original, view, report, _) in self.cases.items():
            self.assertEqual(_remap_generated_model(view)[0], original)
            self.assertEqual(compile_flat_rig(case)[0], original)
            self.assertTrue(report['byte_reversible'])
            self.assertFalse(report['camera_calibrated'])
            self.assertFalse(report['commercial_geometry_modified'])
            self.assertFalse(report['old_animation_banks_compatible'])
            self.assertEqual(report['counts']['inverse_binds'], 8)

    def test_geometry_normals_winding_uv_membership_and_bone_boxes(self):
        for original, view, _, _ in self.cases.values():
            for lod in (0, 1):
                old_meshes, old_hose = geometry(original, lod)
                new_meshes, new_hose = geometry(view, lod)
                for before, after in zip(old_meshes+[old_hose], new_meshes+[new_hose]):
                    for old, new in zip(before['vertices'], after['vertices']):
                        self.assertEqual(new, position(old[:3])+position(old[3:6])+old[6:])
                    for old, new in zip(before['face_groups'], after['face_groups']):
                        self.assertEqual(new['material'], old['material'])
                        self.assertEqual(new['triangles'], [[a, c, b] for a, b, c in old['triangles']])
                self.assertEqual(new_hose['pairs'], old_hose['pairs'])
                self.assertEqual(new_hose['parents'], old_hose['parents'])
                self.assertEqual(new_hose['inverse_binds'], [matrix(m) for m in old_hose['inverse_binds']])
                self.assertEqual(new_hose['base_bounds'], bounds(old_hose['base_bounds']))
                self.assertEqual(new_hose['joint_bounds'], [bounds(b) for b in old_hose['joint_bounds']])

    def test_quaternion_basis_matches_matrix_conjugation_without_normalization(self):
        for angle in (0, .00001, .3, 1.9, math.pi):
            q = [math.sin(angle/2)/math.sqrt(3)]*3+[math.cos(angle/2)]
            before = basis(q)
            actual = basis(native_rotation(q))
            axes = (0, 2, 1)
            expected = [[before[i][j] for j in axes] for i in axes]
            self.assertEqual(actual, expected)
            self.assertEqual(native_rotation(native_rotation(q)), list(struct.unpack('<4f', struct.pack('<4f', *q))))

    def test_converted_equipment_world_matches_at_keys_and_half_keys(self):
        for original, view, _, clips in self.cases.values():
            names, old_seeds = model_poses(original)
            _, new_seeds = model_poses(view)
            old_nodes = parse_4ds_nodes(original)['nodes']
            new_nodes = parse_4ds_nodes(view)['nodes']
            for raw in clips.values():
                clip = parse_5ds(raw)
                old_tracks = {t['name']: t['channels'] for t in clip['tracks']}
                new_tracks = {t['name']: t['channels'] for t in converted_gear_tracks(raw, names)}
                for time in (0, 20, clip['frame_end']*20, clip['frame_end']*40):
                    old, _ = numeric_world(old_nodes, dict(zip(names, old_seeds)), old_tracks, time)
                    new, _ = numeric_world(new_nodes, dict(zip(names, new_seeds)), new_tracks, time)
                    for name in names:
                        self.assertLess(max(abs(a-b) for a, b in zip(matrix(old[name]), new[name])), 3e-7)

    def test_reauthored_grips_are_proper_and_contacts_are_mapped_not_hands_reflected(self):
        before = deepcopy(self.spec)
        for case in self.cases:
            old, new = effective_hands(self.spec, case), view_grips(self.spec, case)
            for side in ('L', 'R'):
                validate_basis(new[side]['rest_to_equipment_rotation'])
                a = matvec(old[side]['rest_to_equipment_rotation'], old[side]['wrist_to_contact_in_rest'])
                b = matvec(new[side]['rest_to_equipment_rotation'], new[side]['wrist_to_contact_in_rest'])
                self.assertLess(max(abs(x-y) for x, y in zip(b, position(a))), 3e-9)
                self.assertEqual(new[side]['finger_curl_degrees'], [-v for v in old[side]['finger_curl_degrees']])
        self.assertEqual(self.spec, before)

    def test_every_view_target_reachable_on_synthetic_lengths(self):
        count = 0
        for case, (_, view, _, clips) in self.cases.items():
            names, _ = model_poses(view)
            grips = view_grips(self.spec, case)
            for raw in clips.values():
                gear = converted_gear_tracks(raw, names)
                for frame in range(parse_5ds(raw)['frame_end']+1):
                    for side, target in targets_at(view, gear, frame*40, grips).items():
                        two_bone([-.16 if side == 'L' else .16, 0, 0], target['position'], target['pole'], .28, .24)
                        validate_basis(target['rotation'])
                        count += 1
        self.assertEqual(count, 1140)

    def test_unreviewed_inputs_fail_closed(self):
        original, view, _, clips = self.cases['F35']
        with self.assertRaises(ValueError):
            _remap_generated_model(original.replace(b'MODERNE;', b'ORIGINE;', 1))
        with self.assertRaises(ValueError):
            geometry(view.replace(b'MODERNE;', b'ORIGINE;', 1))
        for value in (-1, 2, True):
            with self.assertRaises(ValueError): geometry(view, value)
        names, _ = model_poses(view)
        with self.assertRaises(ValueError): converted_gear_tracks(clips['Idle1'], names[:-1])
        for value in ([math.nan, 0, 0], [11, 0, 0], [True, 0, 0]):
            with self.assertRaises(ValueError): position(value)
        with self.assertRaises(ValueError): native_rotation([0, 0, 0, .5])

    def test_preview_reads_serialized_mesh_vertices_and_reversed_faces(self):
        for _, view, _, clips in self.cases.values():
            names, seeds = model_poses(view)
            tracks = converted_gear_tracks(clips['Arm'], names)
            raw = motion._encode_transform_tracks(24, tracks, preserve_native_rotations=True,
                                                   name_validator=lambda name: name in names)
            world, _ = numeric_world(parse_4ds_nodes(view)['nodes'], dict(zip(names, seeds)),
                                      {t['name']: t['channels'] for t in tracks}, 540)
            for lod in (0, 1):
                source, hose = geometry(view, lod)
                result = preview_meshes(view, raw, 540, lod)
                by_name = {m['name']: m for m in source}
                for mesh in result:
                    if mesh.name == 'MOD_hose':
                        self.assertEqual(len(mesh.points), len(hose['vertices']))
                    else:
                        expected = by_name[mesh.name]
                        self.assertEqual(mesh.points, [tuple(transformed(v[:3], world[mesh.name])) for v in expected['vertices']])
                        self.assertIn({'material': mesh.material, 'triangles': [list(t) for t in mesh.triangles]}, expected['face_groups'])


if __name__ == '__main__':
    unittest.main()
