"""Invented clips and bounded attachment state; no commercial fixture."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_attach_oracle import AttachOracle, reference_sequence, START, ALLOC, FREE
from animation_attach_audit import op, invented, controls, audit_cases, bank_cases, check_receipt


class AttachTests(unittest.TestCase):
    def setUp(self):
        self.clips = {'A': {'data': invented(['Root']), 'mode': 2},
                      'B': {'data': invented(['Other']), 'mode': 1}}

    def run_ref(self, operations, names=None):
        return reference_sequence(['Root', 'Other'] if names is None else names, self.clips, operations)

    def test_default_mode_and_explicit_mode_restart_time_previous_without_clamping_weight(self):
        rows = self.run_ref([op('A', 7, 1.5), op('A', 7, .25, 3)])
        self.assertEqual(rows[0]['slots'][7]['mode'], 2)
        self.assertEqual(rows[0]['slots'][7]['weight'], 1.5)
        self.assertEqual(rows[1]['slots'][7]['mode'], 3)
        self.assertEqual([rows[1]['slots'][7][k] for k in ('time','previous','last_delta')], [0,-40,23])
        self.assertEqual(rows[1]['allocated'], 1)
        self.assertEqual(rows[1]['references'], {'A': 2, 'B': 1})

    def test_same_clip_in_two_slots_is_reference_counted_once_per_slot(self):
        rows = self.run_ref([op('A',0), op('A',1), op(None,0), op(None,1)])
        self.assertEqual([row['references']['A'] for row in rows], [2,3,2,1])
        self.assertEqual([len(row['owners']) for row in rows], [1,1,1,0])
        self.assertEqual(rows[-1]['freed'], 1)

    def test_different_clip_clears_old_flags_but_keeps_unbound_owner_until_all_slots_inactive(self):
        rows = self.run_ref([op('A'), op('B'), op(None)])
        self.assertEqual(rows[1]['owners'][0], [None]*8)
        self.assertEqual(rows[1]['owners'][1][0], ('B',0))
        self.assertEqual(rows[-1]['owners'], {})
        self.assertEqual(rows[-1]['freed'], 2)

    def test_empty_detach_is_noop_including_dirty_and_time(self):
        row = self.run_ref([op(None)])[0]
        self.assertFalse(row['dirty']); self.assertEqual(row['slots'][0]['time'], 17)
        self.assertEqual(row['slots'][0]['weight'], .25)

    def test_missing_and_case_mismatched_names_do_not_allocate(self):
        for names in ([], ['root'], ['Other']):
            row = self.run_ref([op('A')], names)[0]
            self.assertEqual(row['allocated'], 0); self.assertTrue(row['slots'][0]['active'])

    def test_duplicate_target_uses_first_exact_match(self):
        row = self.run_ref([op('A')], ['Root','Root'])[0]
        self.assertEqual(list(row['owners']), [0])

    def test_node_animation_flag_remains_marked_after_final_detach(self):
        row = self.run_ref([op('A'), op(None)])[1]
        self.assertEqual(row['touched'], [0]); self.assertEqual(row['owners'], {})

    def test_inputs_and_prior_snapshots_are_not_mutated(self):
        operations = [op('A'), op('B'), op(None)]; before = deepcopy((self.clips,operations))
        rows = self.run_ref(operations)
        self.assertEqual((self.clips,operations), before)
        self.assertEqual(rows[0]['owners'], {0:[('A',0)]+[None]*7})

    def test_invalid_operation_domains_and_source_shapes_are_rejected(self):
        for operation in (op('Missing'), op('A',8), op('A',True), op('A',0,math.nan), op('A',0,-1),
                          op('A',0,2.1), op('A',0,1,4), {**op('A'),'extra':0}):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.run_ref([operation])
        for operations in ([], [op('A')]*33):
            with self.assertRaises(ValueError): self.run_ref(operations)
        with self.assertRaises(ValueError): self.run_ref([op('A')], ['Root']*129)
        with self.assertRaises(ValueError): reference_sequence([], {'A':{'data':b'', 'mode':0}}, [op('A')])

    def test_instruction_allowlist_excludes_windows_loader_pose_and_native_allocators(self):
        machine = object.__new__(AttachOracle); machine.phase='attach'; machine.visited=set()
        machine.on_code(None, START, 6, None)
        for address in (0x10034336,0x10020827,0x10004c92,0x1001eed0,0x100343c7):
            with self.assertRaises(ValueError): machine.on_code(None, address, 2, None)

    def test_write_guard_refuses_readonly_sources_and_inactive_phase(self):
        machine=object.__new__(AttachOracle); machine.phase='attach'; machine.writes=((machine.STATE+4,machine.STATE+5),)
        machine.on_write(None,None,machine.STATE+4,1,0,None)
        for address in (machine.SOURCE,machine.STATE,machine.STATE+5):
            with self.assertRaises(ValueError): machine.on_write(None,None,address,1,0,None)
        machine.phase=None
        with self.assertRaises(ValueError): machine.on_write(None,None,machine.STATE+4,1,0,None)

    def test_unreviewed_library_rejected_before_emulator_import(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed LS3DF'): AttachOracle(b'')

    def test_control_corpus_covers_128_targets_and_eight_slots(self):
        rows = list(controls()); self.assertEqual(len(rows),44)
        for names,clips,operations,kind in rows: reference_sequence(names,clips,operations,kind)
        self.assertEqual(max(len(row[0]) for row in rows),128)
        self.assertEqual({op['slot'] for row in rows for op in row[2]},set(range(8)))

    def test_bank_corpus_checks_eight_slots_two_kinds_and_overlapping_clips(self):
        cases = list(bank_cases(['Root','Other'], {key: row['data'] for key,row in self.clips.items()}))
        self.assertEqual(len(cases),34)
        self.assertEqual(sum(len(row[2]) for row in cases),116)
        for names, clips, operations, kind in cases: reference_sequence(names,clips,operations,kind)
        with self.assertRaises(ValueError): list(bank_cases(['Root'],{'B': self.clips['B']['data']}))

    def test_incomplete_receipt_cannot_claim_native_attachment(self):
        class Invalid:
            def sequence(self,*args): return {'native_attachment_sequence_match':True}
        with self.assertRaisesRegex(ValueError,'receipt'):
            audit_cases(Invalid(), [next(controls())])


if __name__ == '__main__': unittest.main()
