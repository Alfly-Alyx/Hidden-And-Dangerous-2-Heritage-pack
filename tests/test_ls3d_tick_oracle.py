"""Unified-time references and sandbox guards using invented tracks only."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_tick_oracle import TickOracle,reference_tick,validate_ticks,TIME_START
from ls3d_attach_oracle import reference_sequence
from animation_tick_audit import boundary_steps,controls,audit_cases,bank_cases
from animation_attach_audit import op,invented
from five_ds import parse_5ds


class TickTests(unittest.TestCase):
    def setUp(self):
        self.seed={'position':[4,5,6],'rotation':[0,0,0,1],'scale':[1,1,1]}
        self.clips={'A':{'data':invented(['Root']),'mode':2}}
        self.parsed={'A':parse_5ds(self.clips['A']['data'])}
        self.state=reference_sequence(['Root'],self.clips,[op('A')])[-1]

    def tick(self,delta,state=None,pose=None,flags=None):
        return reference_tick(state or self.state,[pose or self.seed],[0x10000008] if flags is None else flags,self.parsed,delta)

    def test_pose_uses_endpoint_before_loop_wrap(self):
        row=self.tick(400)
        self.assertEqual(row['poses'][0]['position'],[2,1,0])
        self.assertEqual(row['state']['slots'][0]['time'],0)
        self.assertEqual(row['state']['slots'][0]['previous'],400)
        self.assertTrue(row['state']['slots'][0]['active'])

    def test_clean_zero_tick_does_not_resample_wrapped_start(self):
        row=self.tick(400)
        later=self.tick(0,row['state'],row['poses'][0],row['flags'])
        self.assertFalse(later['controller_processed']);self.assertEqual(later['pose_calls'],0)
        self.assertEqual(later['poses'],row['poses'])

    def test_nonloop_deactivates_after_endpoint_pose_and_retains_it(self):
        state=deepcopy(self.state);state['slots'][0]['mode']=1
        row=self.tick(400,state)
        self.assertFalse(row['state']['slots'][0]['active'])
        later=self.tick(40,row['state'],row['poses'][0],row['flags'])
        self.assertEqual(later['poses'],row['poses']);self.assertEqual(later['written_channels'],0)

    def test_initial_dirty_zero_tick_samples_frame_zero(self):
        row=self.tick(0)
        self.assertEqual(row['poses'][0]['position'],[0,0,0]);self.assertEqual(row['written_channels'],3)

    def test_zero_weight_preserves_seed_even_when_time_advances(self):
        state=deepcopy(self.state);state['slots'][0]['weight']=0
        row=self.tick(40,state)
        self.assertEqual(row['poses'][0],self.seed);self.assertEqual(row['written_channels'],0)
        self.assertEqual(row['state']['slots'][0]['time'],40)

    def test_target_without_attached_descriptor_keeps_seed(self):
        state=reference_sequence(['Absent'],self.clips,[op('A')])[-1]
        row=self.tick(40,state,flags=[8])
        self.assertEqual(row['pose_calls'],0);self.assertEqual(row['poses'][0],self.seed)

    def test_inputs_are_not_modified(self):
        before=deepcopy((self.state,self.seed,self.parsed));self.tick(40)
        self.assertEqual((self.state,self.seed,self.parsed),before)

    def test_large_step_wraps_once_after_held_last_pose(self):
        row=self.tick(801)
        self.assertEqual(row['state']['slots'][0]['time'],401)
        self.assertEqual(row['poses'][0]['position'],[2,1,0])

    def test_negative_bool_or_oversized_deltas_rejected(self):
        for delta in (-1,True,10001):
            with self.assertRaises(ValueError):self.tick(delta)
        for deltas in ([],[0]*1025,[False]):
            with self.assertRaises(ValueError):validate_ticks([self.seed],['Root'],deltas)
        with self.assertRaises(ValueError):validate_ticks([],['Root'],[0])

    def test_callbacks_matrix_fallback_and_extra_pose_paths_are_closed(self):
        machine=object.__new__(TickOracle);machine.phase='tick';machine.visited=set();machine.pose_calls=0
        machine.on_code(None,TIME_START,4,None)
        for address in (0x10020203,0x1001fadc,0x1001fb10,0x1001f446,0x1008d41c):
            with self.assertRaises(ValueError):machine.on_code(None,address,1,None)

    def test_corpus_and_boundaries_are_explicit_diagnostic_sequences(self):
        cases=list(controls());self.assertEqual(len(cases),22)
        self.assertEqual(boundary_steps(10),[0,0,1,19,20,359,1,0,20])
        for value in (0,1,251,True):
            with self.assertRaises(ValueError):boundary_steps(value)
        self.assertEqual(len(list(bank_cases(['Root'],{'A':self.clips['A']['data']},[self.seed]))),4)

    def test_incomplete_receipt_is_not_accepted(self):
        class Invalid:
            def sequence_with_ticks(self,*args):return {'native_attached_time_pose_checked':True}
        with self.assertRaisesRegex(ValueError,'receipt'):audit_cases(Invalid(),[next(controls())])

    def test_unreviewed_library_rejected_before_emulation(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed LS3DF'):TickOracle(b'')


if __name__=='__main__':unittest.main()
