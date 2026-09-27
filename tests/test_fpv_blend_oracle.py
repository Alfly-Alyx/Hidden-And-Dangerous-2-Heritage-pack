"""Client-crossfade reference and sandbox tests, using invented states."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fpv_blend_oracle import reference,FpvBlendOracle,GATES,START,END
from fpv_blend_audit import record,cases,audit


class BlendTests(unittest.TestCase):
    def setUp(self):self.gates=dict.fromkeys(GATES,True)

    def test_each_disabled_gate_preserves_state_without_model_arguments(self):
        current=record(3,.5,5);previous=[record(0)]
        for gate in GATES:
            row=reference(current,previous,100,{**self.gates,gate:False})
            self.assertEqual(row['current'],current);self.assertEqual(row['previous'],previous)
            self.assertEqual(row['model_call_arguments'],[])

    def test_already_full_weight_detaches_previous_in_reverse_order_without_refresh(self):
        row=reference(record(3),[record(0),record(1),record(2)],0,self.gates)
        self.assertEqual(row['previous'],[])
        self.assertEqual([c['slot'] for c in row['model_call_arguments']],[2,1,0])
        self.assertTrue(all(c['operation']=='detach' for c in row['model_call_arguments']))

    def test_reaching_full_weight_keeps_positive_prior_until_next_update(self):
        row=reference(record(3,.5,5),[record(0)],100,self.gates)
        self.assertEqual(row['current']['weight'],1);self.assertEqual(row['previous'],[record(0)])
        later=reference(row['current'],row['previous'],0,self.gates)
        self.assertEqual(later['previous'],[])

    def test_zero_weight_prior_is_removed_even_at_zero_delta_when_current_not_full(self):
        row=reference(record(3,.5,5),[record(0,0,0)],0,self.gates)
        self.assertEqual(row['previous'],[])
        self.assertEqual([c['operation'] for c in row['model_call_arguments']],['weight','detach','refresh'])

    def test_prior_rates_are_independent_and_middle_removal_preserves_order(self):
        row=reference(record(3,0,5),[record(0),record(1,.25,5),record(2,1,5)],100,self.gates)
        self.assertEqual([r['slot'] for r in row['previous']],[0,2])
        self.assertAlmostEqual(row['previous'][1]['weight'],.5,places=6)

    def test_zero_current_rate_still_updates_positive_prior_and_requests_refresh(self):
        row=reference(record(3,.5,0),[record(0,1,5)],40,self.gates)
        self.assertEqual(row['current']['weight'],.5)
        self.assertLess(row['previous'][0]['weight'],1)
        self.assertEqual(row['model_call_arguments'][-1],{'operation':'refresh'})

    def test_inputs_are_not_mutated(self):
        current=record(3,.5,5);previous=[record(0),record(1,.5,5)]
        before=deepcopy((current,previous,self.gates));reference(current,previous,100,self.gates)
        self.assertEqual((current,previous,self.gates),before)

    def test_invalid_slots_duplicates_steps_and_scalars_rejected(self):
        for current,previous,delta in ((record(8),[],0),(record(3),[record(3)],0),
                (record(3),[],True),(record(3),[],-1),(record(3,math.nan),[],0),
                (record(3,1,11),[],0),(record(3),[record(i) for i in range(4)],0)):
            with self.assertRaises(ValueError):reference(current,previous,delta,self.gates)
        with self.assertRaises(ValueError):reference(record(3),[],0,{})

    def test_execution_outside_controller_or_recording_stubs_is_refused(self):
        machine=object.__new__(FpvBlendOracle);machine.active=True
        machine.on_code(None,START,5,None)
        machine.on_code(None,0x100344c0,2,None)
        for address,size in ((START-1,1),(END,1),(END-1,2),(0x41fc10,1),(0x7e566f,1)):
            with self.assertRaises(ValueError):machine.on_code(None,address,size,None)

    def test_memory_writes_cannot_reach_inputs_or_other_state(self):
        machine=object.__new__(FpvBlendOracle);machine.active=True;machine.writes=((machine.FPV+0x7c,machine.FPV+0x80),)
        machine.on_write(None,None,machine.FPV+0x7c,4,0,None)
        for address in (machine.INPUT,machine.FPV+0x70,machine.HEAP):
            with self.assertRaises(ValueError):machine.on_write(None,None,address,4,0,None)

    def test_corpus_references_and_size(self):
        rows=list(cases());self.assertEqual(len(rows),393)
        for row in rows:reference(*row)

    def test_incomplete_native_receipts_are_not_accepted(self):
        class Invalid:
            def advance(self,*args,**kwargs):return {'native_blend_state_and_arguments_match':True}
        with self.assertRaisesRegex(ValueError,'receipt'):audit(Invalid())

    def test_unreviewed_library_is_rejected_before_machine_construction(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed LS3DF'):FpvBlendOracle(b'',b'')


if __name__=='__main__':unittest.main()
