"""Complete relay input/report contracts without any commercial input files."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import equipment_hand_relay as native
from equipment_hand_relay_audit import summarize,audit


def receipt():
    row={key:True for key in ('same_cpu_and_node_memory','emulated_patch_restored','native_model_frame_vector_used',
        'context_uses_compiled_binding_directly','native_pose_data_not_reinjected_between_steps','all_records_are_diagnostic_joints',
        'patched','registered','controller_present')}
    row.update({key:False for key in ('game_started','client_hook_installed','loaded_scene_qualified',
        'source_geometry_or_poses_exported','native_scene_loading_qualified','native_palette_or_skin_executed')})
    row.update(complete_hand_nodes=37,total_nodes=60,ticks=[{'corrected':True,'native_controller_calls':1,
        'native_pose_calls':60,'adapter_calls':1,'refresh_calls':1,'max_pose_error':1e-8,'max_rotation_error':2e-8,
        'wrist_before':{'L':.01,'R':.02},'wrist_after':{'L':1e-7,'R':2e-7},'wrist_measurement_is_independent_math':True}])
    return row


class EquipmentHandRelayTests(unittest.TestCase):
    def test_complete_receipt_aggregates_calls_and_independent_wrist_measurements(self):
        result=summarize([receipt(),receipt()])
        self.assertEqual(result['ticks'],2);self.assertEqual(result['native_pose_calls'],120)
        self.assertEqual(result['corrected'],2);self.assertEqual(result['max_wrist_after'],2e-7)
        self.assertEqual(result['max_wrist_before'],.02)

    def test_partial_or_overclaimed_receipts_are_refused(self):
        for key,value in (('complete_hand_nodes',36),('total_nodes',120),('patched',1),
                          ('loaded_scene_qualified',True),('source_geometry_or_poses_exported',True),
                          ('context_uses_compiled_binding_directly',False)):
            row=receipt();row[key]=value
            with self.assertRaisesRegex(ValueError,'receipt'):summarize([row])
        for value in (None,[],{}):
            with self.assertRaises(ValueError):summarize(value)

    def test_numeric_limits_and_nonfinite_measurements_are_refused(self):
        for key,value in (('max_pose_error',float('nan')),('max_rotation_error',3e-6),
                          ('native_pose_calls',129),('native_controller_calls',True)):
            row=receipt();row['ticks'][0][key]=value
            with self.assertRaises(ValueError):summarize([row])
        for value in (6e-6,float('inf'),-1):
            row=receipt();row['ticks'][0]['wrist_after']['L']=value
            with self.assertRaisesRegex(ValueError,'wrist'):summarize([row])

    def test_gated_frames_cannot_claim_correction_or_calls(self):
        for key in ('patched','registered','controller_present'):
            row=receipt();row[key]=False
            with self.assertRaisesRegex(ValueError,'gates'):summarize([row])
        row=receipt();row['ticks'][0]['refresh_calls']=0
        with self.assertRaisesRegex(ValueError,'gates'):summarize([row])

    def test_disabled_correction_has_no_wrist_result(self):
        row=receipt();row['registered']=False;row['ticks'][0]['corrected']=False
        with self.assertRaisesRegex(ValueError,'Uncorrected'):summarize([row])
        for key in ('wrist_before','wrist_after','wrist_measurement_is_independent_math'):row['ticks'][0].pop(key)
        result=summarize([row]);self.assertEqual(result['corrected'],0);self.assertEqual(result['uncorrected_ticks'],1)

    def test_case_copy_is_independent_and_synthetic_rotation_is_refused(self):
        m=object.__new__(native.EquipmentHandRelayOracle);m.equipment={'fixture':([1],)}
        result=m.relay_case(False);result[0].append(2)
        self.assertEqual(m.equipment['fixture'],([1],))
        for turned in (True,0,None):
            with self.assertRaisesRegex(ValueError,'pinned'):m.relay_case(turned)
        m.equipment=None
        with self.assertRaises(ValueError):m.relay_case(False)

    def test_nested_case_refused_and_failed_run_clears_case(self):
        m=object.__new__(native.EquipmentHandRelayOracle);m.equipment={}
        with self.assertRaisesRegex(ValueError,'Nested'):m.run_equipment(None,None,None,None,None)
        m.equipment=None
        with patch.object(native,'equipment_case',return_value={'fixture':()}),\
                patch.object(native.CollectedHandRelayOracle,'run',side_effect=ValueError('native failure')):
            with self.assertRaisesRegex(ValueError,'native failure'):m.run_equipment(None,None,None,None,None)
        self.assertIsNone(m.equipment)

    def test_unreviewed_identity_sets_or_arena_overlap_refused_before_preparation(self):
        hands=sorted(native.HAND_NAMES)
        for hn,gn in ((hands[:-1],['fpv_weapon','MOD_left_hand','MOD_right_hand']),
                      (hands,[hands[0]]),(hands,['Node'+str(i) for i in range(83)])):
            with patch.object(native,'pinned_skin',return_value=('source',{'nodes':[]})),\
                    patch.object(native,'model_poses',side_effect=[(hn,[{}]*len(hn)),(gn,[{}]*len(gn))]),\
                    patch.object(native,'preparation_inputs') as prepare:
                with self.assertRaisesRegex(ValueError,'identities'):native.equipment_case(b'hand',b'rig',{},[],{})
                prepare.assert_not_called()

    def test_audit_rejects_unknown_weapon_before_opening_game(self):
        with self.assertRaisesRegex(ValueError,'weapon'):audit(None,None,None,None,None,None,'unknown')


if __name__=='__main__':unittest.main()
