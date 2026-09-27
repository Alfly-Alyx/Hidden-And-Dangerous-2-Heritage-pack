"""Root-relative FPV rebake on wholly original clips; no commercial poses."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_equipment_fpv_animation import rebake_clip,numeric_world,position_curve,flat_preview_meshes
import build_modern_asset as asset
from ls3d_skin_oracle import transformed
from build_modern_equipment_fpv_rig import compile_flat_rig
from build_modern_equipment_assembly import compile_assembly,inputs
from build_equipment_hand_animation import encode_derived_clip,PROVENANCE
from animation_tick_audit import model_poses
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes


class FlatFPVAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={}
        for case in ('F35','F2'):
            flat,original,report=compile_flat_rig(case);_,clips,_=compile_assembly(*inputs(case))
            rebuilt={name:rebake_clip(original,flat,report,raw) for name,(_,raw) in clips.items()}
            cls.cases[case]=(flat,original,report,clips,rebuilt)

    def test_every_flat_target_bound_and_no_obsolete_root_names(self):
        for flat,_,rig_report,_,rebuilt in self.cases.values():
            names={n['name'] for n in parse_4ds_nodes(flat)['nodes']}
            for raw,report in rebuilt.values():
                self.assertEqual({t['name'] for t in parse_5ds(raw)['tracks']},names)
                self.assertNotIn(rig_report['removed_dummy_root'],names)
                self.assertEqual(report['preserved_hose_tracks'],8)
                self.assertEqual(report['hand_tracks'],0)

    def test_native_numeric_world_matrices_match_at_keys_and_remain_close_between(self):
        for flat,original,report,clips,rebuilt in self.cases.values():
            old_nodes=parse_4ds_nodes(original)['nodes'];new_nodes=parse_4ds_nodes(flat)['nodes']
            old_names,old_seeds=model_poses(original);new_names,new_seeds=model_poses(flat)
            for name,(_,source) in clips.items():
                a,b=parse_5ds(source),parse_5ds(rebuilt[name][0])
                for time in (0,20,a['frame_end']*20,a['frame_end']*40):
                    before,_=numeric_world(old_nodes,dict(zip(old_names,old_seeds)),{t['name']:t['channels'] for t in a['tracks']},time)
                    after,_=numeric_world(new_nodes,dict(zip(new_names,new_seeds)),{t['name']:t['channels'] for t in b['tracks']},time)
                    limit=2e-6 if time%40==0 else .0002
                    for old,new in report['source_to_fpv_names'].items():
                        self.assertLessEqual(max(abs(x-y) for x,y in zip(before[old],after[new])),limit,(name,time,old))

    def test_synthetic_hand_channels_are_carried_without_reauthoring(self):
        flat,original,report,clips,_=self.cases['F35'];source=parse_5ds(clips['Aim'][1])
        hand={'name':'Bip01 L Hand','channels':{'rotation':{'frames':[0,12],'values':[[0,0,0,1],[0,0,1,0]]}}}
        value={'provenance':PROVENANCE,'runtime_status':'pending','frame_end':12,
            'tracks':[{'name':t['name'],'channels':t['channels']} for t in source['tracks']]+[hand]}
        raw,_=rebake_clip(original,flat,report,encode_derived_clip(value))
        actual={t['name']:t['channels'] for t in parse_5ds(raw)['tracks']}
        self.assertEqual(actual[hand['name']],hand['channels'])

    def test_changed_source_pins_and_animated_skin_root_are_refused(self):
        flat,original,report,clips,_=self.cases['F35'];bad=deepcopy(report);bad['model_sha256']='0'*64
        with self.assertRaises(ValueError):rebake_clip(original,flat,bad,clips['Aim'][1])
        source=parse_5ds(clips['Aim'][1]);tracks=[{'name':t['name'],'channels':t['channels']} for t in source['tracks']]
        skin=next(t for t in tracks if t['name']==report['source_hose_skin'])
        skin['channels']['position']['values'][-1]=[1,0,0]
        raw=encode_derived_clip({'provenance':PROVENANCE,'runtime_status':'pending','frame_end':12,'tracks':tracks})
        with self.assertRaises(ValueError):rebake_clip(original,flat,report,raw)

    def test_constant_position_compression_is_bit_exact(self):
        self.assertEqual(position_curve([[1,2,3]]*3,2),{'frames':[0,2],'values':[[1,2,3]]*2})
        self.assertEqual(position_curve([[0,0,0],[0,-0.0,0],[0,0,0]],2)['frames'],[0,1,2])
        with self.assertRaises(ValueError):position_curve([[0,0,0]],2)

    def test_flat_preview_samples_serialized_positions_and_both_hose_lods(self):
        for case,(flat,_,_,_,clips) in self.cases.items():
            raw=clips['Arm'][0];time=540;nodes=parse_4ds_nodes(flat)['nodes']
            names,seeds=model_poses(flat);tracks={t['name']:t['channels'] for t in parse_5ds(raw)['tracks']}
            world,_=numeric_world(nodes,dict(zip(names,seeds)),tracks,time)
            originals={pair[0].name:pair for pair in asset.build_meshes(inputs(case)[0])}
            for lod,count in ((0,576),(1,288)):
                meshes=flat_preview_meshes(case,flat,raw,time,lod)
                self.assertEqual(len(meshes[-1][0].points),count)
                for pair in meshes[:-1]:
                    for actual,original in zip(pair,originals[pair[0].name]):
                        self.assertEqual(actual.triangles,original.triangles)
                        self.assertEqual(actual.points,[tuple(transformed(p,world[original.name])) for p in original.points])

    def test_preview_rejects_unreviewed_lod_and_outside_clip_time(self):
        flat,_,_,_,clips=self.cases['F35'];raw=clips['Aim'][0]
        for time,lod in ((0,2),(0,True),(-1,0),(481,0),(20.5,0)):
            with self.assertRaises(ValueError):flat_preview_meshes('F35',flat,raw,time,lod)


if __name__=='__main__':unittest.main()
