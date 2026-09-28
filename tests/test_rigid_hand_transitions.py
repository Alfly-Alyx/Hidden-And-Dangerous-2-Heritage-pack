"""Invented transition fixtures only, without commercial animation or geometry."""
from copy import deepcopy
from contextlib import redirect_stderr
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import rigid_hand_transition_audit as checks
from animation_attach_audit import invented


class RigidHandTransitionTests(unittest.TestCase):
    def pose(self):return {'position':[0.,0.,0.],'rotation':[0.,0.,0.,1.],'scale':[1.,1.,1.]}

    def receipt(self):
        return {'before':{'L':.001,'R':.002},'after':{'L':0,'R':0},
                'finger_poses_preserved':True,'equipment_poses_preserved':True,
                'source_rest_transforms_preserved':True,'engine_hook_implemented':False,
                'changed_channels':'six_arm_rotations_only'}

    def test_schedule_has_three_explicit_phases_complementary_weights_and_detachment(self):
        for a,b in checks.PAIRS:
            for phase in (0,1,2):
                steps=checks.schedule(a,b,17,phase)
                self.assertEqual(steps[1],{'kind':'tick','delta':340*phase})
                self.assertEqual(steps[2],{'kind':'attach','clip':b,'slot':1,'weight':0,'mode':0})
                for i,w in enumerate((0,.25,.5,.75,1)):
                    old,new,tick=steps[3+3*i:6+3*i]
                    self.assertEqual((old['slot'],old['weight'],new['slot'],new['weight']),(0,1-w,1,w))
                    self.assertEqual(tick,{'kind':'tick','delta':20})
                self.assertEqual(steps[-2]['clip'],None);self.assertEqual(steps[-2]['slot'],0)
                self.assertEqual(steps[-1],{'kind':'tick','delta':0})

    def test_unreviewed_schedule_and_case_selection_rejected_before_reading_sources(self):
        for args in [('Idle1','Idle1',20,0),('Jam','Idle1',20,0),('Arm','Idle1',180,0),
                     ('Arm','Idle1',True,0),('Arm','Idle1',20,True),('Arm','Idle1',20,.5)]:
            with self.assertRaises(ValueError):checks.schedule(*args)
        for cases in ([],['MG34','MG34'],['Other'],'MG34'):
            with patch.object(checks,'read_hands') as reader:
                with self.assertRaises(ValueError):checks.audit(None,None,'HandFPV_v10',None,selected_cases=cases)
                reader.assert_not_called()

    def test_pose_observer_rejects_missing_channels_lengths_nonfinite_and_changed_values(self):
        pose=self.pose();saved=deepcopy(pose)
        self.assertEqual(checks.check_pose([pose],[saved]),0)
        for bad in ([],[{}],[{**pose,'position':[0,0]}],[{**pose,'rotation':[0,0,0,float('nan')]}],
                    [{**pose,'scale':[1,1,True]}],[{**pose,'position':[.01,0,0]}]):
            with self.assertRaises(ValueError):checks.check_pose(bad,[saved])
        self.assertEqual(pose,saved)

    def test_correction_receipt_never_promotes_hook_or_allows_missing_arm_errors(self):
        checks.correction_receipt(self.receipt())
        for key,value in [('finger_poses_preserved',False),('equipment_poses_preserved',False),
                          ('source_rest_transforms_preserved',False),('engine_hook_implemented',True),
                          ('changed_channels','all'),('before',{'L':0}),('before',{'L':True,'R':0}),
                          ('after',{'L':1e-4,'R':0}),('after',{'L':float('inf'),'R':0}),
                          ('after',{'L':-1,'R':0})]:
            bad=self.receipt();bad[key]=value
            with self.assertRaises(ValueError):checks.correction_receipt(bad)

    def run_bank(self,stream=None,palette=None):
        pose=self.pose();bank={k:(k,invented(['Hand','Gear'])) for k in checks.ALIASES}
        nodes={'nodes':[{'name':'Hand','parent_id':0}]};gear={'nodes':[{'name':'Gear','parent_id':0}]}
        with patch.object(checks,'model_poses',side_effect=[(['Hand'],[deepcopy(pose)]),(['Gear'],[deepcopy(pose)])]), \
             patch.object(checks,'parse_4ds_nodes',side_effect=[nodes,gear]), \
             patch.object(checks,'correct',side_effect=lambda hand,nodes,poses,grips,**kw:(deepcopy(poses),self.receipt())) as correction:
            with redirect_stderr(io.StringIO()):
                result=checks.audit_bank(b'invented hand',b'invented rig',bank,{},stream=stream,palette=palette)
            for call in correction.call_args_list:
                self.assertEqual(call.kwargs,{'root_name':'fpv_weapon','preserve_observed_elbow_plane':True})
        return result

    def test_numeric_report_keeps_raw_failure_separate_from_corrected_success_and_exports_no_poses(self):
        result=self.run_bank()
        self.assertEqual(result['totals'],{'sequences':39,'ticks':273,'wrist_observations':1092,
                                          'raw_ticks_over_limit':273,'native_palettes':0})
        self.assertFalse(result['raw_wrist_limit_passed'])
        self.assertEqual(result['max_errors'],{'before':.002,'after':0,'stream':0,'palette':0})
        for seq in result['sequences']:
            self.assertEqual(len(seq['samples']),7)
            self.assertNotIn('poses',seq['samples'][0]);self.assertEqual(len(seq['samples'][-1]['slots']),1)

    def test_native_observation_gaps_and_incomplete_subsystems_refused(self):
        with self.assertRaisesRegex(ValueError,'Both native'):
            checks.audit_bank(None,None,None,None,stream=object())
        with self.assertRaisesRegex(ValueError,'Incomplete transition bank'):
            checks.audit_bank(None,None,{},None)
        class EmptyStream:
            def stream(self,*args,**kwargs):return {'max_error':0}
        with patch.object(checks,'check_receipt'):
            with self.assertRaisesRegex(ValueError,'Missing transition observations'):
                self.run_bank(EmptyStream(),object())


if __name__=='__main__':unittest.main()
