"""Modern ZK-383 animation geometry and boundaries, without a game install."""
from copy import deepcopy
import hashlib
import math
import struct
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_zk383_animation_bank as zk
from build_modern_animation_bank import ALIASES,write_generated_bank
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms
import build_modern_asset as asset
import modern_animation as motion


class ZK383AnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe,cls.spec=zk.inputs()
        cls.rig,cls.clips,cls.meshes,cls.report=zk.compile_bank(cls.recipe,cls.spec)
        cls.nodes={n['name']:n for n in parse_4ds_nodes(cls.rig)['nodes']}

    def same_pose(self,a,b):
        self.assertEqual(set(a),set(b))
        for i in a:
            for u,v in zip(a[i][0],b[i][0]):
                for x,y in zip(u,v):self.assertAlmostEqual(x,y,places=6)
            for x,y in zip(a[i][1],b[i][1]):self.assertAlmostEqual(x,y,places=6)

    def test_nine_short_explicit_aliases_and_three_transform_tracks_only(self):
        self.assertEqual(set(self.clips),set(ALIASES))
        self.assertEqual(self.report['rig_sha256'],'435af83a166304d70565cb6fe3b354547ae3dc1e82c499291a074e18cbd12af8')
        self.assertEqual(len(self.nodes),41)
        self.assertEqual(len({stem for stem,raw in self.clips.values()}),9)
        for name,(stem,raw) in self.clips.items():
            self.assertTrue(stem.startswith('PROTOTYPE_ZK3_'))
            self.assertLessEqual(len(stem),19)
            parsed=parse_5ds(raw)
            self.assertEqual(parsed['track_count'],3)
            self.assertTrue(all(t['flags']==6 for t in parsed['tracks']))
            self.assertEqual(parsed['frame_end'],self.report['clips'][name]['frame_end'])
        for field in ('commercial_assets_read','player_hands','player_skeleton_binding','playable_weapon',
                      'event_tracks','sounds','damage','item_allocated','native_fps_known'):
            self.assertFalse(self.report[field])

    def test_rig_preserves_rest_geometry_materials_and_both_lods(self):
        original=asset.encode_4ds(self.recipe,self.meshes)
        self.assertEqual(hashlib.sha256(original).hexdigest(),zk.MODEL_SHA)
        source_nodes={n['name']:n for n in parse_4ds_nodes(original)['nodes']}
        parsed_original=parse_4ds_nodes(original);parsed_rig=parse_4ds_nodes(self.rig)
        self.assertEqual(original[:parsed_original['node_count_offset']],self.rig[:parsed_rig['node_count_offset']])
        for name,node in source_nodes.items():
            target=self.nodes[name]
            # Only the parent and local position may change; every other byte,
            # including the full geometry of both LODs, must remain identical.
            adjusted=bytearray(self.rig[target['start']:target['end']])
            struct.pack_into('<H',adjusted,target['parent_offset']-target['start'],node['parent_id'])
            struct.pack_into('<3f',adjusted,target['position_offset']-target['start'],*node['position'])
            self.assertEqual(original[node['start']:node['end']],bytes(adjusted))
        posed=motion.animated_meshes(self.recipe,self.meshes,self.rig,self.clips['Idle1'][1],0)
        for before_pair,after_pair in zip(self.meshes,posed):
            for before,after in zip(before_pair,after_pair):
                self.assertEqual(before.triangles,after.triangles)
                self.assertEqual(before.material,after.material)
                for a,b in zip(before.points,after.points):
                    for x,y in zip(a,b):self.assertAlmostEqual(x,y,places=7)

    def test_rest_loop_and_state_boundaries_are_continuous(self):
        self.same_pose(world_transforms(self.rig,list(self.nodes.values())),motion.pose(self.rig,self.clips['Idle1'][1],0))
        pairs=[('Idle1',60,'Idle1',0),('Aim',12,'AimShot',0),('AimShot',10,'Daim',0),
               ('Daim',12,'Idle1',0),('Arm',24,'Idle1',0),('Idle1',0,'Disarm',0),
               ('Disarm',24,'Arm',0),('Shot',10,'Idle1',0),('Rel',80,'Idle1',0),('Jammed',32,'Idle1',0)]
        for a,fa,b,fb in pairs:
            with self.subTest(pair=(a,b)):
                self.same_pose(motion.pose(self.rig,self.clips[a][1],fa),motion.pose(self.rig,self.clips[b][1],fb))

    def test_magazine_anchor_moves_with_magazine_socket_and_bipod_stay_on_body(self):
        pivot=self.nodes['MOD_magazine_pivot']['index']
        for name in ('MOD_side_magazine','MOD_magazine_endplate','MOD_magazine_anchor'):
            self.assertEqual(self.nodes[name]['parent_id'],pivot)
        for name in ('MOD_magazine_socket','MOD_bipod_left','MOD_bipod_right','MOD_left_hand'):
            self.assertEqual(self.nodes[name]['parent_id'],1)
        pose=motion.pose(self.rig,self.clips['Rel'][1],35)
        self.assertNotEqual(pose[pivot][1],self.spec['groups'][0]['pivot'])
        root=pose[self.nodes[self.report['rig']['root']]['index']]
        self.assertEqual(pose[self.nodes['MOD_magazine_socket']['index']][0],root[0])

    def test_every_key_and_half_key_has_finite_bounded_transforms(self):
        count=0
        for name,(_,raw) in self.clips.items():
            end=parse_5ds(raw)['frame_end']
            for step in range(end*2+1):
                for rotation,translation in motion.pose(self.rig,raw,step/2).values():
                    self.assertTrue(all(math.isfinite(v) and abs(v)<10 for row in rotation for v in row))
                    self.assertTrue(all(math.isfinite(v) and abs(v)<10 for v in translation))
                count+=1
        self.assertEqual(count,537)

    def test_wrong_asset_alias_changed_geometry_and_functional_fields_refused(self):
        for mutate in (lambda r,s:s.update(name='FG42'),lambda r,s:s.update(model_sha256='0'*64),
                       lambda r,s:r.update(name='PROTOTYPE_HERITAGE_GarotaWorld'),
                       lambda r,s:r['materials'][0]['diffuse'].__setitem__(0,.5),
                       lambda r,s:s.update(damage=10),lambda r,s:s['clips'].pop()):
            r,s=deepcopy(self.recipe),deepcopy(self.spec);mutate(r,s)
            with self.assertRaises(ValueError):zk.compile_bank(r,s)

    def test_companions_disabled_private_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'fresh'
            report=write_generated_bank(self.recipe,self.spec,(self.rig,self.clips,self.meshes,deepcopy(self.report)),output)
            self.assertEqual(len(list(output.iterdir())),27)
            self.assertEqual(len(list(output.glob('*.4ds.disabled'))),10)
            self.assertEqual(len(list(output.glob('*.5ds.disabled'))),9)
            self.assertFalse(list(output.glob('*.4ds')));self.assertFalse(list(output.glob('*.5ds')))
            self.assertFalse(report['companion_auto_load_engine_validated'])
            for _,(stem,raw) in self.clips.items():
                self.assertEqual(parse_4ds_nodes((output/(stem+'.4ds.disabled')).read_bytes())['has_animation'],1)
            with self.assertRaises(FileExistsError):write_generated_bank(self.recipe,self.spec,(self.rig,self.clips,self.meshes,self.report),output)

    def test_cli_incomplete_native_request_fails_before_input_reads(self):
        with patch.object(zk,'inputs',side_effect=AssertionError('Must not read sources')):
            self.assertEqual(zk.main(['--native-report','unused.json']),1)
            self.assertEqual(zk.main(['--native-library','unused.dll']),1)


if __name__=='__main__':unittest.main()
