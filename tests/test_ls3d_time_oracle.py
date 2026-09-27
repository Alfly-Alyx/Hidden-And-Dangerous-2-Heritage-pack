"""Synthetic time reference tests; no engine library in the test suite."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_time_oracle import reference,TimeOracle,LIMIT
from ls3d_time_audit import slot,cases,audit


class TimeReferenceTests(unittest.TestCase):
    def test_clean_zero_delta_does_not_process_boundary_or_previous_time(self):
        slots=[slot(time=400) for _ in range(8)];result=reference(slots,0)
        self.assertFalse(result['controller_processed']);self.assertEqual(result['slots'],slots)

    def test_dirty_zero_delta_processes_boundary_without_replacing_last_delta(self):
        result=reference([slot(time=400) for _ in range(8)],0,True)
        self.assertTrue(result['controller_processed']);self.assertFalse(result['dirty'])
        self.assertEqual(result['slots'][0]['time'],0);self.assertEqual(result['slots'][0]['previous'],400)
        self.assertEqual(result['slots'][0]['last_delta'],13)

    def test_forward_end_is_exclusive_and_previous_captures_pre_wrap_time(self):
        result=reference([slot(time=399) for _ in range(8)],1)['slots'][0]
        self.assertEqual((result['time'],result['previous'],result['last_delta']),(0,400,1))

    def test_reverse_wrap_occurs_once_not_modulo(self):
        for start,expected in ((0,399),(-400,-1),(800,399),(1201,800)):
            result=reference([slot(time=start) for _ in range(8)],-1)['slots'][0]
            self.assertEqual(result['time'],expected);self.assertTrue(result['active'])

    def test_nonloop_modes_deactivate_but_do_not_clamp_outside_time(self):
        for mode in (0,1,3):
            result=reference([slot(mode=mode,time=399) for _ in range(8)],40)['slots'][0]
            self.assertFalse(result['active']);self.assertEqual(result['time'],439)

    def test_inactive_slots_keep_time_previous_and_delta(self):
        slots=[slot(active=False,time=123) for _ in range(8)]
        self.assertEqual(reference(slots,40)['slots'],slots)

    def test_each_slot_keeps_independent_mode_and_duration(self):
        slots=[slot(mode=i%4,end=i+1,time=40*(i+1)-1) for i in range(8)]
        result=reference(slots,1)['slots']
        for i,row in enumerate(result):
            self.assertEqual(row['active'],i%4==2)
            self.assertEqual(row['time'],0 if i%4==2 else 40*(i+1))

    def test_inputs_are_preserved(self):
        slots=[slot() for _ in range(8)];before=deepcopy(slots)
        reference(slots,41);self.assertEqual(slots,before)

    def test_invalid_slot_count_flags_values_and_overflow_are_rejected(self):
        with self.assertRaises(ValueError):reference([slot()],0)
        for field,value in (('active',1),('mode',4),('frame_end',0),('time',LIMIT+1),('previous',True)):
            slots=[slot() for _ in range(8)];slots[0][field]=value
            with self.assertRaises(ValueError):reference(slots,0)
        with self.assertRaises(ValueError):reference([slot(time=LIMIT) for _ in range(8)],1)
        with self.assertRaises(ValueError):reference([slot() for _ in range(8)],0,1)

    def test_pose_callback_and_other_duration_getters_are_outside_allowlist(self):
        machine=object.__new__(TimeOracle);machine.phase='time';machine.visited=set()
        machine.on_code(None,0x10004e80,4,None)
        for address in (0x100201a2,0x100201e4,0x1002020c,0x10004c80,0x1001eed0):
            with self.assertRaises(ValueError):machine.on_code(None,address,1,None)

    def test_corpus_size_and_all_references(self):
        rows=list(cases());self.assertEqual(len(rows),774)
        for slots,delta,dirty in rows:reference(slots,delta,dirty)

    def test_incomplete_proof_is_rejected(self):
        class Invalid:
            def advance(self,*args):return {'native_time_controller_match':True}
        with self.assertRaisesRegex(ValueError,'receipt'):audit(Invalid())


if __name__=='__main__':unittest.main()
