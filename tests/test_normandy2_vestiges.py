"""Synthetic structural facts, not an emulation of the game scripting engine."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_normandy2_vestiges import analyze, movement_facts, signal_facts


def field(kind, text):
    raw = text.encode('ascii') + b'\0'
    return struct.pack('<HI', kind, 6 + len(raw)) + raw


def fixture():
    files = {
        'missions/normandy2/scripts.dta': b'\0' * 6 + field(1, 'Red_31') + field(1, 'r_n2_red_31.scr'),
        'missions/normandy2/actors.bin': field(0x10, 'Red_31') + field(0x10, 'Wave1_1'),
        'missions/normandy2/scene2.bin': field(0x10, 'dummy_Red31_turn') + field(0x10, 'la_N2_balkon'),
        'missions/normandy2/check2.bin': b'\0Red31_1\0W1_1\0',
        'scripts/normandy2/r_n2_red_31.scr': b'HUMAN_Move("Red31_1");',
        'scripts/normandy2/r_n2_ger_tank_driver.scr': b'Goto End; Label End:',
        'scripts/normandy2/r_n2_fake_defence_sender.scr': (
            b'SaveGameValue(25, selected); SendSignal(Ally1,25);'),
    }
    for i in range(1, 6):
        files[f'scripts/normandy2/r_n2_ally{i}_end.scr'] = (
            b'OnSignal(25) { FRM_FindFrame(target,"fixed_target"); }' if i < 5 else b'Goto End; Label End:')
        for family in (1, 2):
            files[f'scripts/normandy2/r_n2_wave{family}_{i}.scr'] = b'// HUMAN_Move("");\nHUMAN_Move("W1_1");'
    return files


class Normandy2VestigeTests(unittest.TestCase):
    def test_literal_signal_is_not_shared_value_protocol(self):
        facts = signal_facts('OnSignal(25) { FRM_FindFrame(t,"fixed"); }', 25)
        self.assertEqual(facts['literal_frame_targets'], ['fixed'])
        self.assertFalse(facts['loads_shared_value_25'])

    def test_comments_and_other_signals_are_excluded(self):
        text = '// OnSignal(25) { FRM_FindFrame(t,"wrong"); }\nOnSignal(250) {}'
        self.assertEqual(signal_facts(text, 25)['handler_count'], 0)
        self.assertFalse(signal_facts('// _LoadGameValue(25);', 25)['loads_shared_value_25'])
        self.assertTrue(signal_facts('x = _LoadGameValue (25);', 25)['loads_shared_value_25'])

    def test_nested_handler_is_reported_uninterpreted(self):
        facts = signal_facts('OnSignal(25) { If (x) { FRM_FindFrame(t,"nested"); } }', 25)
        self.assertEqual(facts['handler_count'], 1)
        self.assertEqual(facts['simple_handler_count'], 0)
        self.assertEqual(facts['literal_frame_targets'], [])

    def test_vehicle_stop_is_not_a_missing_movement(self):
        facts = movement_facts('HUMAN_Drive("",0); // HUMAN_Move("");\nHUMAN_Move("route");', b'\0route\0')
        self.assertEqual(facts['active_vehicle_stops'], 1)
        self.assertEqual(facts['active_empty_moves'], 0)
        self.assertEqual(facts['commented_empty_moves'], 1)
        self.assertEqual(facts['named_checkpoints'], {'route': True})

    def test_missing_actor_is_not_inferred_from_route(self):
        waves = analyze(fixture())['waves']
        self.assertTrue(waves[0]['actor_present'])
        self.assertFalse(waves[1]['actor_present'])
        self.assertTrue(waves[1]['named_checkpoints']['W1_1'])

    def test_unbound_sender_stays_unreachable_and_uninstalled(self):
        result = analyze(fixture())
        self.assertEqual(result['sender']['bound_owners'], [])
        self.assertFalse(result['sender']['reachable_script'])
        self.assertEqual(result['signal25_receivers'][4]['handler_count'], 0)
        self.assertEqual(result['runtime_status'], 'pending')
        self.assertFalse(result['automatic_activation_authorized'])
        self.assertFalse(result['installed_into_game'])

    def test_literal_assignment_is_followed(self):
        files = fixture()
        files['scripts/normandy2/r_n2_red_31.scr'] += b'ScriptAssign(me,"r_n2_fake_defence_sender");'
        self.assertTrue(analyze(files)['sender']['reachable_script'])

    def test_dynamic_assignment_and_missing_source_refuse(self):
        files = fixture()
        files['scripts/normandy2/r_n2_red_31.scr'] = b'ScriptAssign(me, unknown);'
        with self.assertRaisesRegex(ValueError, 'Non-literal'):
            analyze(files)
        files = fixture()
        del files['scripts/normandy2/r_n2_ally5_end.scr']
        with self.assertRaisesRegex(ValueError, 'Missing reviewed source'):
            analyze(files)


if __name__ == '__main__':
    unittest.main()
