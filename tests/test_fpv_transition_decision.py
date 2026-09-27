"""Synthetic state only; no commercial image or native execution in this suite."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from fpv_transition_decision_oracle import reference, TransitionDecisionOracle, START, IS_ACTIVE, END
from fpv_transition_decision_audit import cases, audit, record


class TransitionDecisionTests(unittest.TestCase):
    def test_no_clip_is_immediate_without_query(self):
        row = reference(360, 0, 0, None, [record(0)], True)
        self.assertEqual((row['selected_slot'], row['weight'], row['rate']), (1, 1, 0))
        self.assertEqual(row['native_active_queries'], 0)
        self.assertFalse(row['previous_clip_saved'])

    def test_active_clip_is_appended_without_changing_its_rate(self):
        row = reference(360, 12, 3, record(0, 0, 1), [record(1)], True)
        self.assertEqual(row['previous'], [record(1), record(0, 0, 1)])
        self.assertEqual((row['selected_slot'], row['weight'], row['rate']), (2, 0, 5))

    def test_inactive_or_missing_controller_does_not_append(self):
        for active, present in ((False, True), (True, False), (False, False)):
            row = reference(361, 1, 0, record(0), [record(1)], active, present)
            self.assertEqual(row['previous'], [record(1)])
            self.assertEqual((row['selected_slot'], row['weight'], row['rate']), (0, 1, 0))
            self.assertEqual(row['native_active_queries'], 1)

    def test_fourth_slot_is_not_silently_deduplicated(self):
        row = reference(361, 1, 0, record(3), [record(i) for i in range(3)], True)
        self.assertEqual(row['selected_slot'], 3)
        self.assertTrue(row['selected_slot_already_present'])
        self.assertEqual(len(row['previous']), 4)

    def test_reference_preserves_supplied_records(self):
        current, previous = record(0), [record(1)]
        old = deepcopy((current, previous))
        row = reference(0, 0, 0, current, previous, True)
        row['previous'][0]['weight'] = 0
        self.assertEqual((current, previous), old)

    def test_invalid_flags_capacity_slots_values_and_cache_refused(self):
        good = [360, 0, 0, record(0), [], True, True]
        replacements = ((0, 500), (1, 13), (2, True), (2, 4), (3, {}),
                        (3, record(True)), (3, record(8)), (3, record(0, float('nan'))),
                        (3, record(0, 11)), (3, record(0, 0, 1.1)),
                        (4, [record(0)]), (4, [record(1), record(1)]),
                        (4, [record(i) for i in range(8)]), (5, 1), (6, 0))
        for index, value in replacements:
            args = deepcopy(good)
            args[index] = value
            with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                reference(*args)

    def test_instruction_allowlist_excludes_allocator_and_unused_copy_branch(self):
        machine = object.__new__(TransitionDecisionOracle)
        machine.active = True
        machine.on_code(None, START, 3, None)
        machine.on_code(None, IS_ACTIVE+4, 3, None)
        for address, size in ((0x492fd5, 1), (0x4930f8, 1), (0x493127, 1),
                              (0x7e566f, 1), (END, 1), (IS_ACTIVE+0x29, 3)):
            with self.assertRaises(ValueError):
                machine.on_code(None, address, size, None)

    def test_write_guard_disallows_controller_cache_and_other_records(self):
        machine = object.__new__(TransitionDecisionOracle)
        machine.active = True
        machine.writes = ((machine.HEAP+0x100, machine.HEAP+0x110),)
        machine.on_write(None, None, machine.HEAP+0x100, 16, 0, None)
        for address in (machine.HEAP+0x110, machine.HEAP+0x100c, machine.INPUT, machine.FPV+0xa0):
            with self.assertRaises(ValueError):
                machine.on_write(None, None, address, 4, 0, None)

    def test_corpus_has_every_distinct_current_and_prior_subset(self):
        rows = list(cases())
        self.assertEqual(len(rows), 3112)
        corpus = {(r[3]['slot'], tuple(p['slot'] for p in r[4])) for r in rows[1040:3088]}
        self.assertEqual(len(corpus), 8*128)
        for args in rows:
            reference(*args)

    def test_reference_only_receipt_rejected(self):
        class Fake:
            def select(self, *args):
                return reference(*args)
        with self.assertRaisesRegex(ValueError, 'receipt'):
            audit(Fake())

    def test_library_pin_checked_before_emulator_import(self):
        with self.assertRaises(ValueError):
            TransitionDecisionOracle(b'', b'')


if __name__ == '__main__':
    unittest.main()
