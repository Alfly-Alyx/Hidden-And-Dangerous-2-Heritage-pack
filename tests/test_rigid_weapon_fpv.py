"""Modern source-free rigid FPV geometry, serialization and frame rebaking."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_rigid_weapon_fpv_bank as rigid
from build_modern_equipment_hose import digest
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from modern_fpv_axes import _remap_generated_model,position,native_rotation
from modern_fpv_geometry import geometry

EXPECTED={
    'FG42':(32,25,505,'0ae8254f8ad43678ac7e02086ffc72eff7bb03ba9a1a996eb7e85f432f1062f6'),
    'MG34':(41,33,505,'9cc238c77e9a1a38f844977f417e802118026258a27f40103af9d680b076e672'),
    'ZK383':(40,33,537,'554a5721a39fffc7d65ac94fb4762a7847f233eef4a214bb9376953c4256b6ef'),
}


class RigidWeaponFPVTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={case:rigid.compile_bank(case) for case in rigid.CASES}

    def test_visual_receiver_root_and_all_direct_children_have_stable_fingerprints(self):
        for case,(_,raw,clips,report) in self.cases.items():
            count,meshes,samples,sha=EXPECTED[case];parsed=parse_4ds_nodes(raw);nodes=parsed['nodes']
            self.assertEqual(digest(raw),sha);self.assertEqual(len(nodes),count)
            self.assertEqual((nodes[0]['name'],nodes[0]['frame_type'],nodes[0]['visual_type'],nodes[0]['parent_id']),('fpv_weapon',1,0,0))
            self.assertTrue(all(n['parent_id']==1 for n in nodes[1:]))
            self.assertFalse(parsed['has_animation']);self.assertEqual(len(clips),9)
            self.assertEqual(len({stem for stem,raw in clips.values()}),9)
            for stem,raw in clips.values():
                self.assertLessEqual(len(stem),19)
                self.assertEqual({t['name'] for t in parse_5ds(raw)['tracks']},{n['name'] for n in nodes})
            for key in ('old_banks_compatible','player_hands','camera_placement_authored','native_loader_executed',
                        'native_clone_qualified','events_or_gameplay_implemented','item_allocated','game_started','engine_validated'):
                self.assertFalse(report[key])

    def test_both_lods_remap_positions_normals_winding_and_preserve_uv_materials(self):
        for case,(_,view,_,report) in self.cases.items():
            flat,_=_remap_generated_model(view)
            self.assertEqual(_remap_generated_model(flat)[0],view)
            self.assertEqual(digest(flat),report['flattening']['flat_sha256'])
            for lod in (0,1):
                old,old_skin=geometry(flat,lod);new,new_skin=geometry(view,lod)
                self.assertIsNone(old_skin);self.assertIsNone(new_skin)
                self.assertEqual(len(new),EXPECTED[case][1])
                for a,b in zip(old,new):
                    self.assertEqual(a['name'],b['name'])
                    for u,v in zip(a['vertices'],b['vertices']):
                        self.assertEqual(v,position(u[:3])+position(u[3:6])+u[6:])
                    for u,v in zip(a['face_groups'],b['face_groups']):
                        self.assertEqual(u['material'],v['material'])
                        self.assertEqual(v['triangles'],[[a,c,b] for a,b,c in u['triangles']])

    def test_source_world_comparison_covers_all_keys_and_half_keys_without_hiding_residual(self):
        for case,(_,view,clips,report) in self.cases.items():
            self.assertEqual(sum(r['samples'] for r in report['clips'].values()),EXPECTED[case][2])
            for row in report['clips'].values():
                self.assertLess(row['matrix_max_errors']['keys'],5e-6)
                self.assertLess(row['matrix_max_errors']['half_keys'],.0002)
                self.assertFalse(row['continuous_equivalence_proven'])
                self.assertFalse(row['native_code_executed'])
        self.assertGreater(max(r['matrix_max_errors']['half_keys'] for r in self.cases['MG34'][3]['clips'].values()),.0001)

    def test_root_animation_is_axis_converted_without_incorporating_preview_offset(self):
        for case,(_,view,clips,report) in self.cases.items():
            _,_,(source,old,_,_)=rigid.original(case)
            for name,(_,raw) in clips.items():
                source_root=next(t for t in parse_5ds(old[name][1])['tracks'] if t['name']==report['flattening']['removed_dummy_root'])
                actual=next(t for t in parse_5ds(raw)['tracks'] if t['name']=='fpv_weapon')
                for kind,convert in (('position',position),('rotation',native_rotation)):
                    expected=source_root['channels'][kind]
                    self.assertEqual(actual['channels'][kind]['frames'],expected['frames'])
                    self.assertEqual(actual['channels'][kind]['values'],[convert(v) for v in expected['values']])
            self.assertEqual(parse_4ds_nodes(view)['nodes'][0]['position'],[0,0,0])

    def test_flatten_preserves_entire_geometry_payload_before_axis_conversion(self):
        for case in self.cases:
            _,_,(source,_,_,_)=rigid.original(case)
            flat,report=rigid.flatten(source);after={n['name']:n for n in parse_4ds_nodes(flat)['nodes']}
            for node in parse_4ds_nodes(source)['nodes'][1:]:
                target=after[report['source_to_fpv_names'][node['name']]]
                self.assertEqual(source[node['name_offset']+node['name_length']:node['end']],
                                 flat[target['name_offset']+target['name_length']:target['end']])

    def test_unknown_case_unmarked_rest_and_changed_rebake_sources_refused(self):
        with self.assertRaises(ValueError):rigid.original('Other')
        _,_,(source,clips,_,_)=rigid.original('FG42');nodes=parse_4ds_nodes(source)['nodes']
        with self.assertRaises(ValueError):rigid.flatten(source.replace(b'MODERNE;',b'ORIGINE;',1))
        changed=bytearray(source);struct.pack_into('<f',changed,nodes[1]['position_offset']+28,2)
        with self.assertRaises(ValueError):rigid.flatten(bytes(changed))
        flat,report=rigid.flatten(source);bad=deepcopy(report);bad['flat_sha256']='0'*64
        with self.assertRaises(ValueError):rigid.rebake(source,flat,bad,clips['Idle1'][1])
        view=self.cases['FG42'][1]
        for lod in (-1,2,True):
            with self.assertRaises(ValueError):geometry(view,lod)

    def test_build_serializes_only_disabled_banks_and_diagnostic_previews(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'fresh';compiled=deepcopy(self.cases['FG42'])
            with patch.object(rigid,'compile_bank',return_value=compiled):
                report=rigid.build('FG42',output)
                self.assertEqual(len(list(output.iterdir())),14)
                self.assertEqual(len(list(output.glob('*.4ds.disabled'))),1)
                self.assertEqual(len(list(output.glob('*.5ds.disabled'))),9)
                self.assertFalse(list(output.glob('*.4ds')));self.assertFalse(list(output.glob('*.5ds')))
                self.assertEqual(report['preview_only_translation'],[.07,-.15,.25])
                with self.assertRaises(FileExistsError):rigid.build('FG42',output)
                for name,sha in report['files'].items():self.assertEqual(digest((output/name).read_bytes()),sha)


if __name__=='__main__':unittest.main()
