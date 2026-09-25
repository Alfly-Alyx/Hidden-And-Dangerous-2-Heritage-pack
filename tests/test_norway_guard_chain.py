"""Structural audit checks with invented data, without licensed game files."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_norway_guard_chain import analyze, exact_checkpoint, sender_facts


def field(kind, value):
    payload = value.encode('ascii') + b'\0'
    return struct.pack('<HI', kind, len(payload) + 6) + payload


def fixture():
    return {
        'missions/norway/scripts.dta': b'\0' * 6 + field(1, 'tirpic_guard_3') + field(1, 'R_Nor_Tirpic3.scr'),
        'missions/norway/actors.bin': field(0x10, 'tirpic_guard_3'),
        'missions/norway/scene2.bin': field(0x10, 'dummy_see1') + field(0x10, 'dummy_see2'),
        'missions/norway/check2.bin': b'\0T1_1\0T3_1\0',
        'scripts/norway/r_nor_tirpic1.scr': b'HUMAN_Move("T1_1"); OnSignal(1) {}',
        'scripts/norway/r_nor_tirpic3.scr': b'HUMAN_Move("T3_1"); // OnSignal(3) {}\n',
        'scripts/norway/r_nor_action_sender.scr': (
            b'delay(10000); label Newer_ending_sending:\n'
            b'waiter = _RandomInt(10000)+7000;\n'
            b'If (what_soldier==3) { SendSignal(T3, what_signal); }\n'
            b'// Delay(waiter);\ngoto Newer_ending_sending;'),
    }


class NorwayChainTests(unittest.TestCase):
    def test_checkpoint_match_is_case_insensitive_and_token_terminated(self):
        self.assertTrue(exact_checkpoint(b'\0t12_3\0', 'T12_3'))
        for raw in (b'T1_10\0', b'T11_1\0', b'prefixT1_1\0', b'T1_1_suffix\0', b'T1_1'):
            self.assertFalse(exact_checkpoint(raw, 'T1_1'), raw)

    def test_commented_delay_is_not_a_loop_wait(self):
        result = analyze(fixture())
        sender = result['sender']
        self.assertEqual(sender['initial_delay_arguments'], ['10000'])
        self.assertEqual(sender['loop_delay_arguments'], [])
        self.assertTrue(sender['waiter_assigned'])
        self.assertFalse(sender['waiter_delay_used'])

    def test_initial_wait_and_loop_wait_are_distinguished(self):
        body = 'delay(1); label Newer_ending_sending: waiter=2; delay(waiter); goto Newer_ending_sending;'
        result = sender_facts(body)
        self.assertEqual(result['initial_delay_arguments'], ['1'])
        self.assertEqual(result['loop_delay_arguments'], ['waiter'])
        self.assertTrue(result['waiter_delay_used'])

    def test_unbound_sender_is_not_automatically_assumed_active(self):
        result = analyze(fixture())
        self.assertEqual(result['sender']['bound_owners'], [])
        self.assertFalse(result['sender']['reachable_script'])
        self.assertEqual(result['guards'][2]['literal_signal_handlers'], [])
        self.assertTrue(result['guards'][2]['reachable_script'])
        self.assertEqual(result['runtime_status'], 'pending')
        self.assertFalse(result['installed_into_game'])

    def test_checkpoint_presence_does_not_create_actor_identity(self):
        guard = analyze(fixture())['guards'][0]
        self.assertTrue(guard['script_present'])
        self.assertTrue(guard['checkpoints']['T1_1'])
        self.assertFalse(guard['actor_present'])
        self.assertEqual(guard['bound_scripts'], [])

    def test_transitive_include_marks_sender_reachable(self):
        files = fixture()
        files['scripts/norway/r_nor_tirpic3.scr'] += b'#include "R_Nor_action_Sender.scr"\n'
        self.assertTrue(analyze(files)['sender']['reachable_script'])

    def test_changed_sender_shape_and_dynamic_dependency_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'reviewed sender loop'):
            sender_facts('label another: goto another;')
        files = fixture()
        files['scripts/norway/r_nor_tirpic3.scr'] = b'ScriptAssign(me, name);'
        with self.assertRaisesRegex(ValueError, 'Non-literal'):
            analyze(files)


if __name__ == '__main__':
    unittest.main()
