"""Two fully original rigid-part banks; gameplay/character binding stays pending."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_modern_animation_bank as bank
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms
import modern_animation as motion

HASHES={'FG42':'531c5364f46776d53ff5e4ae4ba9033c3c736c0cfc02f8d74cb8914bb1412d18',
        'MG34':'e87a3403e887ddec2a792fde39eedc1968ab299e435e1490acdf32cb116c33ba'}


class ModernAnimationBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={}
        for case,folder in bank.CASES.items():
            directory=ROOT/'experimental'/folder
            recipe=json.loads((directory/'modern-world-model.json').read_text(encoding='utf-8'))
            spec=json.loads((directory/'modern-animation-bank.json').read_text(encoding='utf-8'))
            cls.cases[case]=(recipe,spec,bank.compile_bank(recipe,spec))

    def same_pose(self,left,right):
        self.assertEqual(set(left),set(right))
        for index in left:
            for a,b in zip(left[index][0],right[index][0]):
                for x,y in zip(a,b):self.assertAlmostEqual(x,y,places=6)
            for x,y in zip(left[index][1],right[index][1]):self.assertAlmostEqual(x,y,places=6)

    def test_all_eighteen_clips_bind_with_short_unique_aliases_and_no_events(self):
        for case,(_,spec,(rig,clips,meshes,report)) in self.cases.items():
            self.assertEqual(set(clips),set(bank.ALIASES))
            self.assertEqual(report['rig_sha256'],HASHES[case])
            self.assertEqual(parse_4ds_nodes(rig)['node_count'],33 if case=='FG42' else 42)
            self.assertEqual(len(set(stem.casefold() for stem,_ in clips.values())),9)
            for name,(stem,data) in clips.items():
                self.assertLessEqual(len(stem),19)
                parsed=parse_5ds(data)
                self.assertEqual(parsed['track_count'],1+len(spec['groups']))
                self.assertTrue(all(t['flags']==6 for t in parsed['tracks']))
                self.assertIsNone(parsed['frame_rate'])
                self.assertEqual(parsed['frame_end'],report['clips'][name]['frame_end'])
            self.assertEqual(report['preview_fps'],24)
            for flag in ('commercial_assets_read','game_modified','game_launched','player_hands',
                         'player_skeleton_binding','playable_weapon','event_tracks','sounds',
                         'damage','item_allocated','native_fps_known'):
                self.assertFalse(report[flag])

    def test_loop_and_cross_clip_boundaries_are_continuous(self):
        pairs=[('Idle1',60,'Idle1',0),('Aim',12,'AimShot',0),
               ('AimShot',8,'Daim',0),('Daim',12,'Idle1',0),
               ('Arm',20,'Idle1',0),('Idle1',0,'Disarm',0),
               ('Shot',8,'Idle1',0),('Rel',80,'Idle1',0),('Jammed',28,'Idle1',0)]
        for case,(_,_,(rig,clips,_,_)) in self.cases.items():
            rest=world_transforms(rig,parse_4ds_nodes(rig)['nodes'])
            self.same_pose(rest,motion.pose(rig,clips['Idle1'][1],0))
            for a,fa,b,fb in pairs:
                with self.subTest(case=case,pair=(a,b)):
                    self.same_pose(motion.pose(rig,clips[a][1],fa),motion.pose(rig,clips[b][1],fb))

    def test_reload_changes_owned_groups_and_mg34_feed_marker_remains_fixed_to_body(self):
        for case,(_,spec,(rig,clips,_,report)) in self.cases.items():
            nodes={n['name']:n for n in parse_4ds_nodes(rig)['nodes']}
            transforms=motion.pose(rig,clips['Rel'][1],40)
            root=transforms[nodes[report['rig']['root']]['index']]
            magazine=transforms[nodes['MOD_magazine_pivot']['index']]
            self.assertNotEqual(magazine[1],spec['groups'][0]['pivot'])
            if case=='MG34':
                self.assertEqual(nodes['MOD_feed_anchor']['parent_id'],1)
                self.assertNotEqual(transforms[nodes['MOD_cover_pivot']['index']][0],root[0])
            else:self.assertNotIn('MOD_cover_pivot',nodes)

    def test_invalid_specs_and_changed_geometry_cannot_silently_build(self):
        recipe,spec,_=self.cases['FG42']
        bad=[]
        for changes in ({'provenance':'OFFICIEL'},{'runtime_status':'passed'},{'ammo_id':196},
                        {'model_sha256':'0'*64},{'preview_fps':True}):
            value=copy.deepcopy(spec);value.update(changes);bad.append(value)
        value=copy.deepcopy(spec);value['clips'].pop();bad.append(value)
        value=copy.deepcopy(spec);value['clips'][0]['motions']['missing']=[[0,[0,0,0],[0,0,0]]];bad.append(value)
        value=copy.deepcopy(spec);value['clips'][0]['motions']['ROOT'][-1][1]=[1,0,0];bad.append(value)
        value=copy.deepcopy(spec);value['clips'][1]['motions']['ROOT'][0][0]=1;bad.append(value)
        for value in bad:
            with self.subTest(value=value),self.assertRaises(ValueError):bank.compile_bank(recipe,value)
        changed=copy.deepcopy(recipe);changed['materials'][0]['diffuse'][0]+=.01
        with self.assertRaisesRegex(ValueError,'geometry changed'):bank.compile_bank(changed,spec)

    def test_pairs_export_disabled_with_explicit_companion_flag_and_no_overwrite(self):
        for case,(recipe,spec,_) in self.cases.items():
            with tempfile.TemporaryDirectory() as directory:
                output=Path(directory)/'fresh';report=bank.build(recipe,spec,output)
                self.assertEqual(report['companion_pairs'],9)
                self.assertFalse(report['companion_auto_load_engine_validated'])
                self.assertEqual(len(report['files']),26)
                self.assertEqual(len(list(output.iterdir())),27)
                self.assertEqual(len(list(output.glob('*.4ds.disabled'))),10)
                self.assertEqual(len(list(output.glob('*.5ds.disabled'))),9)
                self.assertFalse(list(output.glob('*.4ds')));self.assertFalse(list(output.glob('*.5ds')))
                for name,description in report['clips'].items():
                    model=(output/(description['stem']+'.4ds.disabled')).read_bytes()
                    self.assertEqual(parse_4ds_nodes(model)['has_animation'],1)
                with self.assertRaises(FileExistsError):bank.build(recipe,spec,output)

    def test_euler_rotation_order_matches_static_original_part_transform(self):
        import build_modern_asset as asset
        from model_transform import affine,point
        mesh=asset.Mesh('MOD_test',1,[(1,2,3),(0,0,0),(1,0,0)],[(0,1,2)])
        angles=[21,-35,73]
        posed=asset.transform_mesh(mesh,{'rotation_degrees':angles})
        matrix=affine([0,0,0],bank.euler(angles),[1,1,1])
        for original,expected in zip(mesh.points,posed.points):
            for a,b in zip(point(matrix,original),expected):self.assertAlmostEqual(a,b)


if __name__=='__main__':unittest.main()

