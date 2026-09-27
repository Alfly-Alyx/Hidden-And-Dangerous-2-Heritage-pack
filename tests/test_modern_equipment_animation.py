"""Original held-only motion, continuous boundaries and explicit pending state."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_modern_equipment_animation import inputs,compile_equipment_bank,build,CASES
from build_modern_equipment_components import compile_components
from build_modern_animation_bank import ALIASES,compile_bank
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms
import modern_animation as motion

HASHES={'F35':'ff9a8f3e649f91ef5556fb5dd148c53862985ad6c993d1aa862505e599b9e299',
        'F2':'d7fff8ff80378350be9487e5720041c6613156bd34c3c85410495bcb54921bab'}


class EquipmentMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={case:(inputs(case),compile_equipment_bank(*inputs(case))) for case in CASES}

    def same_pose(self,left,right):
        self.assertEqual(set(left),set(right))
        for index in left:
            for a,b in zip(left[index][0],right[index][0]):
                for x,y in zip(a,b):self.assertAlmostEqual(x,y,places=6)
            for x,y in zip(left[index][1],right[index][1]):self.assertAlmostEqual(x,y,places=6)

    def test_eighteen_clips_and_native_rig_hashes(self):
        frames=0
        for case,(_, (rig,clips,_,report)) in self.cases.items():
            self.assertEqual(set(clips),set(ALIASES));self.assertEqual(hashlib.sha256(rig).hexdigest(),HASHES[case])
            self.assertEqual(parse_4ds_nodes(rig)['node_count'],15 if case=='F35' else 16)
            for name,(alias,raw) in clips.items():
                self.assertLessEqual(len(alias),19);parsed=parse_5ds(raw)
                self.assertEqual(parsed['track_count'],2);self.assertTrue(all(row['flags']==6 for row in parsed['tracks']))
                frames+=parsed['frame_end']+1
        self.assertEqual(frames,570)

    def test_no_backpack_hose_mesh_or_character_bones_are_in_held_rigs(self):
        for _,(_, (rig,_,_,report)) in self.cases.items():
            names={node['name'] for node in parse_4ds_nodes(rig)['nodes']}
            self.assertNotIn('MOD_hose',names);self.assertNotIn('MOD_backpack_anchor',names)
            self.assertFalse(any('pack' in name for name in names))
            self.assertIn('MOD_hose_anchor',names);self.assertTrue(report['held_component_only'])
            self.assertFalse(report['player_hands']);self.assertFalse(report['player_skeleton_binding'])

    def test_rest_preview_uses_mesh_local_vertices_without_double_recentering(self):
        for _,((recipe,partition,_),(rig,clips,meshes,_)) in self.cases.items():
            components,_=compile_components(recipe,partition)
            expected=components['held']['meshes']
            actual=motion.animated_meshes(recipe,meshes,rig,clips['Idle1'][1],0)
            for a,b in zip(actual,expected):
                for lod in (0,1):
                    self.assertEqual(a[lod].triangles,b[lod].triangles)
                    for x,y in zip(a[lod].points,b[lod].points):
                        for v,w in zip(x,y):self.assertAlmostEqual(v,w,places=6)

    def test_loops_and_cross_clip_boundaries_match(self):
        pairs=[('Idle1',60,'Idle1',0),('Aim',12,'AimShot',0),('AimShot',24,'Daim',0),
               ('Daim',12,'Idle1',0),('Arm',24,'Idle1',0),('Idle1',0,'Disarm',0),
               ('Shot',24,'Idle1',0),('Rel',64,'Idle1',0),('Jammed',32,'Idle1',0)]
        for case,(_, (rig,clips,_,report)) in self.cases.items():
            self.same_pose(world_transforms(rig,parse_4ds_nodes(rig)['nodes']),motion.pose(rig,clips['Idle1'][1],0))
            for a,fa,b,fb in pairs:
                with self.subTest(case=case,pair=(a,b)):
                    self.same_pose(motion.pose(rig,clips[a][1],fa),motion.pose(rig,clips[b][1],fb))
            for name in ('Idle1','Shot','AimShot'):self.assertTrue(report['clips'][name]['loop'])

    def test_held_pivot_moves_while_root_stays_identity(self):
        for _,(_, (rig,clips,_,report)) in self.cases.items():
            nodes={node['name']:node for node in parse_4ds_nodes(rig)['nodes']}
            poses=motion.pose(rig,clips['Rel'][1],32)
            self.assertEqual(poses[nodes[report['rig']['root']]['index']][1],[0,0,0])
            self.assertNotEqual(poses[nodes['MOD_held_pivot']['index']][1],[0,0,0])

    def test_output_claims_remain_visual_and_pending(self):
        for _,(_,(_,_,_,report)) in self.cases.items():
            self.assertEqual(report['provenance'],'MODERNE');self.assertEqual(report['runtime_status'],'pending')
            self.assertTrue(report['visual_state_labels_are_not_gameplay'])
            for key in ('commercial_assets_read','backpack_in_animation','hose_in_animation',
                        'hose_deformation_implemented','functional_reload_implemented','fpv_camera_calibrated',
                        'damage','sounds','item_allocated','playable_weapon','game_launched'):
                self.assertFalse(report[key])

    def test_inputs_and_static_component_sources_are_unchanged(self):
        recipe,partition,spec=inputs('F35');before=deepcopy((recipe,partition,spec))
        source=compile_components(recipe,partition)[1]
        compile_equipment_bank(recipe,partition,spec)
        self.assertEqual((recipe,partition,spec),before)
        self.assertEqual(compile_components(recipe,partition)[1],source)

    def test_incomplete_members_wrong_component_and_wrong_source_refused(self):
        recipe,partition,spec=inputs('F35')
        bad=[]
        changed=deepcopy(spec);changed['groups'][0]['members'].pop();bad.append(changed)
        changed=deepcopy(spec);changed['groups'][0]['members'].append('MOD_hose');bad.append(changed)
        changed=deepcopy(spec);changed['name']='F2';bad.append(changed)
        changed=deepcopy(spec);changed['model_sha256']='0'*64;bad.append(changed)
        changed=deepcopy(spec);changed['groups'][0]['pivot']=[1,0,0];bad.append(changed)
        for changed in bad:
            with self.assertRaises(ValueError):compile_equipment_bank(recipe,partition,changed)
        with self.assertRaises(ValueError):compile_bank(recipe,spec)

    def test_functional_fields_or_unmarked_provenance_are_rejected(self):
        recipe,partition,spec=inputs('F35')
        for changes in ({'ammo_id':207},{'provenance':'OFFICIEL'},{'runtime_status':'passed'}):
            changed=deepcopy(spec);changed.update(changes)
            with self.assertRaises(ValueError):compile_equipment_bank(recipe,partition,changed)

    def test_disabled_companions_and_fresh_output_only(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'fresh';report=build(*inputs('F2'),output)
            self.assertEqual(len(list(output.glob('*.5ds.disabled'))),9)
            self.assertEqual(len(list(output.glob('*.4ds.disabled'))),10)
            self.assertEqual(len(list(output.iterdir())),27)
            self.assertFalse(list(output.glob('*.5ds')));self.assertFalse(list(output.glob('*.4ds')))
            self.assertFalse(report['companion_auto_load_engine_validated'])
            for desc in report['clips'].values():
                self.assertEqual(parse_4ds_nodes((output/(desc['stem']+'.4ds.disabled')).read_bytes())['has_animation'],1)
            with self.assertRaises(FileExistsError):build(*inputs('F2'),output)


if __name__=='__main__':unittest.main()
