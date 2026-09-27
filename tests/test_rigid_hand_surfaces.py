"""Correction orchestration with invented poses, no commercial fixtures."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import rigid_weapon_hand_audit as checks


class CorrectedRigidSurfaceTests(unittest.TestCase):
    def sample(self,receipt,*,enabled=True,time=20):
        pose={'position':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]}
        hand={'a':deepcopy(pose),'Bip01 L Hand':deepcopy(pose)}
        gear={'fpv_weapon':deepcopy(pose)};combined={**deepcopy(hand),**deepcopy(gear)}
        combined['Bip01 L Hand']['rotation']=[0,0,.6,.8]
        nodes=[{'name':'fpv_weapon','parent_id':0}]
        with patch.object(checks,'pinned_skin',return_value=('invented',{'nodes':[]})), \
             patch.object(checks,'model_poses',side_effect=[(list(hand),list(hand.values())),(list(gear),list(gear.values()))]), \
             patch.object(checks,'parse_5ds',return_value={'frame_end':1,'tracks':[]}), \
             patch.object(checks,'parse_4ds_nodes',return_value={'nodes':nodes}), \
             patch.object(checks,'numeric_world',side_effect=[({},hand),({},gear)]), \
             patch.object(checks,'correct',return_value=(combined,receipt)) as correction:
            result=checks.sampled_hand_pose(b'hand',b'rig',b'clip',time,
                                           corrected_grips={'L':{},'R':{}} if enabled else None)
            if enabled:
                correction.assert_called_once_with(b'hand',nodes,{**hand,**gear},{'L':{},'R':{}},
                    root_name='fpv_weapon',preserve_observed_elbow_plane=True)
            else:correction.assert_not_called()
        return result,hand,combined

    def receipt(self):
        return {'finger_poses_preserved':True,'equipment_poses_preserved':True,
                'source_rest_transforms_preserved':True,'changed_channels':'six_arm_rotations_only',
                'engine_hook_implemented':False,'before':{'L':.001,'R':.002},'after':{'L':0,'R':0}}

    def test_corrected_measurement_uses_combined_gear_then_only_hand_output(self):
        (poses,receipt),hand,combined=self.sample(self.receipt())
        self.assertEqual(poses,{name:combined[name] for name in hand})
        self.assertNotIn('fpv_weapon',poses);self.assertEqual(receipt,self.receipt())
        self.assertEqual(hand['Bip01 L Hand']['rotation'],[0,0,0,1])

    def test_raw_measurement_never_runs_correction(self):
        (poses,receipt),hand,_=self.sample(self.receipt(),enabled=False)
        self.assertEqual(poses,hand);self.assertIsNone(receipt)

    def test_incomplete_receipt_and_invalid_sampling_refused(self):
        for key,value in (('finger_poses_preserved',False),('equipment_poses_preserved',False),
                          ('source_rest_transforms_preserved',False),('changed_channels','all'),
                          ('engine_hook_implemented',True)):
            bad=self.receipt();bad[key]=value
            with self.assertRaisesRegex(ValueError,'receipt'):self.sample(bad)
        for time in (-1,41,True,20.0):
            with self.assertRaisesRegex(ValueError,'sample time'):self.sample(self.receipt(),time=time)

    def test_corrected_mode_requires_dense_surfaces_before_reading_game(self):
        for native,dense,flag in ((True,False,True),(False,False,True),(False,True,1)):
            with patch.object(checks,'read_hands') as reader:
                with self.assertRaisesRegex(ValueError,'Post-blend'):
                    checks.audit(None,None,'HandFPV_v7',None,native=native,dense=dense,post_blend_surfaces=flag)
                reader.assert_not_called()


if __name__=='__main__':unittest.main()
