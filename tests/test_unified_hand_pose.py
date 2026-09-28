"""No commercial input or emulator needed for shared-memory contract tests."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import unified_hand_pose_oracle as oracle
import unified_hand_pose_audit as audit
from native_hand_targets import BINARY_SHA as TARGET_SHA
from native_hand_pipeline import BINARY_SHA as PIPELINE_SHA,EXPECTED_CALLS


class UnifiedHandPoseTests(unittest.TestCase):
    def row(self):
        return {'native_animation_compiled_commit_refresh_palette_same_memory':True,
            'poses_seeded_only_before_first_operation':True,'reference_corrected_poses_carried_independently':True,
            'solver_cpu_separate':True,'client_hook_implemented':False,'loaded_scene_qualified':False,
            'owning_visual_bounds_evaluated':False,'game_started':False,'max_native_pose_error':0,
            'max_solver_rotation_error':0,'owner_allocations':78,'owner_releases':78,'ticks':1,
            'samples':[{'native_pose_calls':0,'local_rebuilds':6,'before':{'L':.001,'R':0},
                        'after':{'L':1e-7,'R':0},'max_matrix_error':1e-7}]}

    def test_canonical_keeps_orientation_and_does_not_mutate_input(self):
        q=[0,0,0,-1];self.assertEqual(oracle.canonical(q),[0,0,0,1]);self.assertEqual(q,[0,0,0,-1])
        for bad in ([0,0,0,0],[0,0,0,float('nan')],[True,0,0,0]):
            with self.assertRaises(ValueError):oracle.canonical(bad)

    def test_retention_exercises_clean_ticks_weight_zero_and_complete_detachment(self):
        steps=audit.retention_schedule();saved=deepcopy(steps)
        self.assertEqual(steps[0]['clip'],'Idle1')
        self.assertGreaterEqual(sum(s['kind']=='tick' and s['delta']==0 for s in steps),12)
        self.assertIn({'kind':'weight','slot':0,'weight':0},steps)
        self.assertIn({'kind':'weight','slot':0,'weight':1},steps)
        self.assertIsNone(steps[-5]['clip']);self.assertEqual(steps[-5]['slot'],0)
        self.assertEqual(steps,audit.retention_schedule());self.assertEqual(steps,saved)

    def test_summary_counts_clean_frames_without_conflating_original_pose_calls(self):
        row=self.row();before=deepcopy(row);totals=audit.summarize([row])
        self.assertEqual(totals['native_pose_calls'],0);self.assertEqual(totals['compiled_arm_calls'],2)
        self.assertEqual(totals['committed_rotations'],6);self.assertEqual(totals['local_rebuilds'],6)
        self.assertEqual(totals['clean_ticks_without_native_pose'],1);self.assertEqual(totals['raw_ticks_over_limit'],1)
        self.assertEqual(row,before)

    def test_summary_refuses_missing_proofs_promotion_and_invalid_numeric_results(self):
        for field,value in (('client_hook_implemented',True),('solver_cpu_separate',False),('ticks',2),
                ('max_native_pose_error',float('nan')),('max_solver_rotation_error',1),('owner_allocations',True)):
            row=self.row();row[field]=value
            with self.assertRaises(ValueError):audit.summarize([row])
        for field,value in (('native_pose_calls',True),('local_rebuilds',38),('max_matrix_error',float('inf')),
                            ('after',{'L':1,'R':0}),('before',{'L':True,'R':0})):
            row=self.row();row['samples'][0][field]=value
            with self.assertRaises(ValueError):audit.summarize([row])

    def test_shared_machine_rejects_unpinned_code_before_accessing_parent(self):
        for raw in (b'',b'MZ',bytearray(oracle.BINARY_SIZE),bytes(oracle.BINARY_SIZE)):
            with self.assertRaisesRegex(ValueError,'commit image'):oracle.SharedPoseMemory(None,raw)

    def test_compiled_targets_are_counted_only_with_complete_receipts(self):
        row=self.row();row['target_preparation_compiled']=True
        receipt={'status':0,'compiled_sha256':TARGET_SHA,'input_unchanged':True,
            'output_and_scratch_guards_unchanged':True,'failed_output_unchanged':True,
            'native_cdecl_preserved':True,'game_started':False,'client_hook_implemented':False,'max_input_error':1e-8}
        row['samples'][0]['compiled_target_preparation']=receipt
        totals=audit.summarize([row]);self.assertEqual(totals['compiled_target_calls'],1)
        self.assertEqual(totals['max_target_input_error'],1e-8)
        for mode,value in ((False,receipt),(True,None),(1,receipt),(True,{**receipt,'input_unchanged':False})):
            row['target_preparation_compiled']=mode;row['samples'][0]['compiled_target_preparation']=value
            with self.assertRaises(ValueError):audit.summarize([row])

    def test_target_identity_and_case_rejected_before_native_operations(self):
        machine=object.__new__(oracle.UnifiedHandPoseOracle)
        with patch.object(oracle,'pinned_skin',return_value=('invented',{'nodes':[]})):
            with self.assertRaisesRegex(ValueError,'target identities'):machine.run(None,[],[],{},[],[],{})
        with self.assertRaisesRegex(ValueError,'weapon'):audit.audit(None,None,'bad',None,None,None,'Other')
        with self.assertRaisesRegex(ValueError,'suffix'):audit.audit(None,None,'bad',None,None,None,'MG34')

    def test_pipeline_summary_requires_shared_cpu_and_counts_every_compiled_stage(self):
        row=self.row();row.update(target_preparation_compiled=True,compiled_pipeline_shared_memory=True,solver_cpu_separate=False)
        receipt={'status':0,'compiled_sha256':PIPELINE_SHA,'compiled_calls':dict(EXPECTED_CALLS),
            'inputs_unchanged':True,'unrelated_arena_unchanged':True,'failed_arena_unchanged':True,
            'workspace_guard_unchanged':True,'native_cdecl_preserved':True,'shared_animation_arena':True,
            'client_hook_implemented':False,'game_started':False,'max_input_error':0}
        row['samples'][0]['compiled_pipeline']=receipt;result=audit.summarize([row])
        self.assertEqual(result['compiled_pipeline_calls'],1);self.assertEqual(result['compiled_arm_calls'],2)
        self.assertEqual(result['compiled_target_calls'],1);self.assertEqual(result['committed_rotations'],6)
        for key,value in (('solver_cpu_separate',True),('target_preparation_compiled',False),('compiled_pipeline_shared_memory',False)):
            with self.assertRaises(ValueError):audit.summarize([{**row,key:value}])
        row['samples'][0]['compiled_pipeline']=None
        with self.assertRaises(ValueError):audit.summarize([row])

    def test_pipeline_and_separate_processors_cannot_be_silently_combined(self):
        with self.assertRaisesRegex(ValueError,'not both'):oracle.UnifiedHandPoseOracle(None,None,object(),pipeline_raw=b'')
        with self.assertRaisesRegex(ValueError,'not both'):oracle.UnifiedHandPoseOracle(None,None,None,object(),b'')
        with self.assertRaisesRegex(ValueError,'Choose'):audit.audit(None,None,'HandFPV_v10',None,None,None,'MG34')


if __name__=='__main__':unittest.main()
