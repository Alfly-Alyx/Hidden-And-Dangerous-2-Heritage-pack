"""Invented persistent-animation sequences and strict offline phase guards."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from animation_attach_audit import invented
from animation_stream_audit import attach, steps_for, controls, audit_cases
from ls3d_animation_stream_oracle import (validate, reference_step, AnimationStreamOracle,
                                        BOOTSTRAP, WEIGHT)
from ls3d_attach_oracle import reference_sequence


class AnimationStreamTests(unittest.TestCase):
    def setUp(self):
        self.names = ['Root', 'Other']
        seed = {'position': [4, 5, 6], 'rotation': [0, 0, 0, 1], 'scale': [1, 1, 1]}
        self.initial = [deepcopy(seed), deepcopy(seed)]
        self.clips = {'A': {'data': invented(['Root']), 'mode': 2},
                      'B': {'data': invented(['Other']), 'mode': 1}}

    def reference(self, steps):
        parsed, poses, steps = validate(self.names, self.clips, self.initial, steps)
        state = reference_sequence(self.names, self.clips, [BOOTSTRAP])[-1]
        flags = [8]*len(self.names)
        rows = []
        for step in steps:
            row = reference_step(state, poses, flags, self.names, self.clips, parsed, step)
            state, poses, flags = row['state'], row['poses'], row['flags']
            rows.append(row)
        return rows

    def test_attach_during_playback_preserves_other_slot_clock(self):
        rows = self.reference([attach('A'), {'kind': 'tick', 'delta': 80}, attach('B', 1)])
        self.assertEqual(rows[-1]['state']['slots'][0]['time'], 80)
        self.assertEqual(rows[-1]['state']['slots'][1]['time'], 0)
        self.assertEqual(rows[-1]['poses'], rows[-2]['poses'])

    def test_restart_same_clip_retains_owner_and_last_delta(self):
        rows = self.reference([attach('A'), {'kind': 'tick', 'delta': 80}, attach('A')])
        slot = rows[-1]['state']['slots'][0]
        self.assertEqual((slot['time'], slot['previous'], slot['last_delta']), (0, -40, 80))
        self.assertEqual(rows[-1]['state']['allocated'], 1)
        self.assertEqual(rows[-1]['poses'], rows[-2]['poses'])

    def test_detach_preserves_pose_and_releases_last_owner(self):
        rows = self.reference([attach('A'), {'kind': 'tick', 'delta': 80}, attach(None),
                               {'kind': 'tick', 'delta': 40}])
        self.assertEqual(rows[-1]['poses'], rows[1]['poses'])
        self.assertEqual(rows[-1]['state']['owners'], {})
        self.assertEqual(rows[-1]['state']['freed'], 1)

    def test_replacement_retains_empty_owner_until_all_slots_inactive(self):
        rows = self.reference([attach('A'), {'kind': 'tick', 'delta': 40}, attach('B'),
                               {'kind': 'tick', 'delta': 40}, attach(None)])
        self.assertEqual(len(rows[2]['state']['owners']), 2)
        self.assertEqual(rows[3]['poses'][0], rows[1]['poses'][0])
        self.assertEqual(rows[-1]['state']['freed'], 2)

    def test_weight_clamps_and_dirty_zero_tick_resamples_without_resetting_time(self):
        rows = self.reference([attach('A'), {'kind': 'tick', 'delta': 80},
                {'kind': 'weight', 'slot': 0, 'weight': -1}, {'kind': 'tick', 'delta': 0},
                {'kind': 'weight', 'slot': 0, 'weight': 2}, {'kind': 'tick', 'delta': 0}])
        self.assertEqual(rows[2]['state']['slots'][0]['weight'], 0)
        self.assertEqual(rows[4]['state']['slots'][0]['weight'], 1)
        self.assertEqual(rows[3]['written_channels'], 0)
        self.assertEqual(rows[5]['written_channels'], 3)
        self.assertEqual(rows[5]['state']['slots'][0]['time'], 80)

    def test_nonloop_endpoint_then_restart_works_after_deactivation(self):
        rows = self.reference([attach('B'), {'kind': 'tick', 'delta': 400}, attach('B'),
                               {'kind': 'tick', 'delta': 0}])
        self.assertFalse(rows[1]['state']['slots'][0]['active'])
        self.assertTrue(rows[2]['state']['slots'][0]['active'])
        self.assertEqual(rows[3]['poses'][1]['position'], [0, 0, 0])

    def test_supplied_data_and_prior_snapshots_remain_detached(self):
        steps = [attach('A'), {'kind': 'tick', 'delta': 80}, attach('B')]
        before = deepcopy((self.names, self.clips, self.initial, steps))
        rows = self.reference(steps)
        rows[-1]['state']['owners'].clear()
        self.assertTrue(rows[0]['state']['owners'])
        self.assertEqual((self.names, self.clips, self.initial, steps), before)

    def test_invalid_operations_and_oversized_sequences_refused(self):
        invalid = ([], [attach('A')]*513, [{}], [{'kind': 'tick', 'delta': -1}],
                   [{'kind': 'tick', 'delta': True}], [{'kind': 'tick', 'delta': 10001}],
                   [{'kind': 'weight', 'slot': 8, 'weight': 1}],
                   [{'kind': 'weight', 'slot': 0, 'weight': float('nan')}],
                   [{'kind': 'weight', 'slot': 0, 'weight': -3}],
                   [attach('Missing')], [{**attach('A'), 'callback': 'forbidden'}])
        for steps in invalid:
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                validate(self.names, self.clips, self.initial, steps)

    def test_stream_weight_instructions_are_strictly_bounded(self):
        machine = object.__new__(AnimationStreamOracle)
        machine.phase, machine.visited = 'stream_weight', set()
        machine.on_code(None, WEIGHT, 4, None)
        for address, size in ((WEIGHT-1, 1), (0x100344dd, 1), (0x100344dc, 2), (0x1008d41c, 1)):
            with self.assertRaises(ValueError):
                machine.on_code(None, address, size, None)

    def test_corpus_has_all_slots_modes_containers_and_bank_orders(self):
        cases = list(controls())
        self.assertEqual(len(cases), 24)
        for names, clips, initial, steps, kind in cases:
            validate(names, clips, initial, steps, kind)
        steps = steps_for([str(i) for i in range(9)], 64)
        self.assertEqual(len(steps), 144)
        self.assertEqual(sum(s['kind'] == 'tick' for s in steps), 44)
        for keys, end in (([], 10), (['A', 'A'], 10), (['A'], True), (['A'], 251)):
            with self.assertRaises(ValueError):
                steps_for(keys, end)

    def test_incomplete_receipt_is_not_a_native_result(self):
        class Fake:
            def stream(self, *args):
                return {'native_interleaved_attach_weight_tick_checked': True}
        with self.assertRaisesRegex(ValueError, 'receipt'):
            audit_cases(Fake(), [next(controls())])

    def test_invalid_library_refused(self):
        with self.assertRaises(ValueError):
            AnimationStreamOracle(b'')


if __name__ == '__main__':
    unittest.main()
