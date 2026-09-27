"""Invented poses and transforms only; private skeletons are not fixtures."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from fpv_contact_constraints import ARM_NAMES, replace_arm_rotations, targets, world, wrist_errors
from build_equipment_hand_animation import IDENTITY
from animation_attach_audit import invented
from animation_stream_audit import attach, steps_for
from fpv_transition_contact_audit import trace


class ContactConstraintTests(unittest.TestCase):
    def fixture(self):
        pose = {'position': [.01, .02, .03], 'rotation': [0, 0, 0, 1], 'scale': [1, 1, 1]}
        initial = {name: deepcopy(pose) for name in ARM_NAMES | {'Finger', 'Equipment', 'Root'}}
        authored = deepcopy(initial)
        for name in authored:
            authored[name]['rotation'] = [0, .6, 0, .8]
        return initial, authored

    def test_only_six_rotations_change_and_inputs_remain_detached(self):
        initial, authored = self.fixture()
        saved = deepcopy((initial, authored))
        result = replace_arm_rotations(initial, authored)
        for name in initial:
            self.assertEqual(result[name], authored[name] if name in ARM_NAMES else initial[name])
        result['Equipment']['position'][0] = 9
        result[next(iter(ARM_NAMES))]['rotation'][0] = 9
        self.assertEqual((initial, authored), saved)

    def test_missing_bones_stretching_and_unexpected_channels_are_refused(self):
        initial, authored = self.fixture()
        name = next(iter(ARM_NAMES))
        for key in ('position', 'scale'):
            bad = deepcopy(authored)
            bad[name][key][0] += .001
            with self.assertRaises(ValueError): replace_arm_rotations(initial, bad)
        del authored[name]
        with self.assertRaises(ValueError): replace_arm_rotations(initial, authored)
        initial, authored = self.fixture()
        authored[name]['extra'] = 0
        with self.assertRaises(ValueError): replace_arm_rotations(initial, authored)

    def test_world_preserves_parent_composition_and_rejects_ambiguity(self):
        pose = {'position': [.1, .2, .3], 'rotation': [0, 0, 0, 1], 'scale': [1, 1, 1]}
        nodes = [{'name': 'root', 'parent_id': 0}, {'name': 'child', 'parent_id': 1}]
        result = world(nodes, {'root': pose, 'child': pose})
        for actual, expected in zip(result['child'][12:15], [.2, .4, .6]):
            self.assertAlmostEqual(actual, expected, places=7)
        with self.assertRaises(ValueError): world(nodes, {'root': pose})
        with self.assertRaises(ValueError): world([nodes[0], nodes[0]], {'root': pose})

    def test_contact_offsets_follow_held_basis_and_wrist_error_is_axis_maximum(self):
        gear = {'MOD_held_pivot': IDENTITY[:], 'MOD_left_hand': IDENTITY[:], 'MOD_right_hand': IDENTITY[:]}
        grips = {side: {'rest_to_equipment_rotation': [[1,0,0],[0,1,0],[0,0,1]],
                       'contact_offset': [.01,.02,.03], 'wrist_to_contact_in_rest': [.1,0,0],
                       'elbow_pole': [.3,.4,.5]} for side in ('L','R')}
        gear['MOD_left_hand'][12:15] = [.2,.3,.4]
        wanted = targets(gear, grips)
        for actual, expected in zip(wanted['L']['position'], [.11,.32,.43]):
            self.assertAlmostEqual(actual, expected)
        hands = {f'Bip01 {side} Hand': IDENTITY[:] for side in ('L','R')}
        for side in ('L','R'): hands[f'Bip01 {side} Hand'][12:15] = wanted[side]['position'][:]
        hands['Bip01 L Hand'][13] += .04
        self.assertAlmostEqual(wrist_errors(hands, wanted)['L'], .04)
        self.assertEqual(wrist_errors(hands, wanted)['R'], 0)
        with self.assertRaises(ValueError): targets(gear, {'L': grips['L']})

    def test_trace_records_sample_time_before_loop_wrap_and_detaches_poses(self):
        pose = {'position': [0,0,0], 'rotation': [0,0,0,1], 'scale': [1,1,1]}
        clips = {'A': {'data': invented(['Root']), 'mode': 2}}
        rows = trace(['Root'], clips, [pose], [attach('A'), {'kind':'tick','delta':420},
                     {'kind':'tick','delta':20}])
        self.assertEqual([r['step'] for r in rows], [1,2])
        self.assertEqual([r['slots'][0]['sample_time'] for r in rows], [420,40])
        rows[0]['poses'][0]['position'][0] = 99
        self.assertNotEqual(rows[1]['poses'][0]['position'][0], 99)
        self.assertEqual(pose['position'], [0,0,0])

    def test_trace_preserves_slot_order_and_entire_diagnostic_schedule(self):
        pose = {'position': [0,0,0], 'rotation': [0,0,0,1], 'scale': [1,1,1]}
        clips = {key: {'data': invented(['Root']), 'mode':2} for key in ('A','B','C')}
        steps = steps_for(list(clips),10)
        rows = trace(['Root'],clips,[pose],steps)
        self.assertEqual(len(rows),14)
        for row in rows:
            self.assertEqual([s['slot'] for s in row['slots']], sorted(s['slot'] for s in row['slots']))
        self.assertEqual(rows[-1]['slots'], [])
        with self.assertRaises(ValueError): trace(['Root'],clips,[pose],[{'kind':'tick','delta':-1}])


if __name__ == '__main__': unittest.main()
