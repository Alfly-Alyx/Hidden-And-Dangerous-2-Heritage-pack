"""Recipe contracts and abstract state checks, never a script-engine simulation."""
import itertools
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_reconstruction_variant as builder


class DialoguePaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = builder.load_catalog()
        cls.pace = catalog['alps2-agent-segment-pace']
        cls.gestures = catalog['burgundy3-interrogation-visual-phases']

    def test_six_choices_precede_moves_and_not_retry_labels(self):
        decisions = [e for e in self.pace['edits'] if '_PlayerInRange(7)' in e['after']]
        self.assertEqual(len(decisions), 6)
        for edit in decisions:
            self.assertTrue(edit['after'].endswith(edit['before']))
            self.assertLess(edit['after'].index('HUMAN_SETMODE_Run'), edit['after'].index('HUMAN_Move'))
            self.assertIn('else\n  {\n    HUMAN_SETMODE_Walk();', edit['after'])
            self.assertNotRegex(edit['after'], r'(?i)\b(?:goto|label|SendSignal|SetWaitForPlayer)\b')
        self.assertEqual(len(self.pace['edits']), 8)

    def test_walk_is_restored_at_door_and_player_handoff(self):
        for needle in ('HUMAN_Move("AL2_ag_07_1");', 'SetNPCTeamStatus(me, 1);'):
            edit = next(e for e in self.pace['edits'] if needle in e['before'])
            self.assertLess(edit['after'].index('HUMAN_SETMODE_Walk'), edit['after'].index(needle))
        for edit in self.pace['edits']:
            self.assertEqual(edit['after'].count('HUMAN_Move('), edit['before'].count('HUMAN_Move('))
            self.assertEqual(edit['after'].count('SetNPCTeamStatus('), edit['before'].count('SetNPCTeamStatus('))

    def test_all_three_visual_scripts_form_an_atomic_profile(self):
        changes = builder.change_specs(self.gestures)
        self.assertEqual(len(changes), 3)
        self.assertEqual({c['actor'] for c in changes}, {'BUR03_20','BUR03_SAS02','dummy_rozhovor01'})
        self.assertEqual(changes[2]['owner_entry'], 'missions/burgundy3/scene2.bin')
        with self.assertRaisesRegex(ValueError, 'Atomic multi-script'):
            builder.prepare(self.gestures, None)

    def test_receivers_advance_only_ordered_alive_phases(self):
        for change, signals in zip(builder.change_specs(self.gestures), ([11,13,15,17],[10,12,14,16])):
            added = next(e['after'] for e in change['edits'] if e['before'] == 'OnDeath()')
            for phase, signal in enumerate(signals):
                start = added.index(f'OnSignal({signal})')
                next_handler = added.find('OnSignal(', start+1)
                body = added[start:next_handler]
                self.assertIn(f'heritage_visual_phase == {phase}', body)
                self.assertIn(f'heritage_visual_phase = {phase+1}', body)
                self.assertEqual(body.count('_ACTOR_GetState('), 2)
                self.assertLess(body.index(f'heritage_visual_phase = {phase+1}'), body.index('HUMAN_SetAnim'))
                self.assertNotIn('ACTIVITY', body)

    def test_duplicate_or_late_signals_do_not_advance_abstract_protocol(self):
        # Validate the specified state machine, not HD2 handler scheduling.
        def step(phase, signal, alive=True):
            if signal == 99 or not alive:
                return 99
            return phase+1 if phase < 4 and signal == 11+phase*2 else phase
        for signals in itertools.product((11,13,15,17,99), repeat=5):
            phase = 0
            for signal in signals:
                following = step(phase, signal)
                self.assertGreaterEqual(following, phase)
                if phase == 99:
                    self.assertEqual(following, 99)
                phase = following
        self.assertEqual(step(0, 17), 0)
        self.assertEqual(step(1, 11), 1)
        self.assertEqual(step(1, 13, alive=False), 99)

    def test_prisoner_never_gets_standing_gestures(self):
        sas = builder.change_specs(self.gestures)[1]
        combined = '\n'.join(e['after'] for e in sas['edits'])
        self.assertEqual(combined.count('HUMAN_SetAnim("%%kucasedi.i3d"'), 4)
        self.assertNotIn('%%rozhovor', combined)
        self.assertNotRegex(combined, r'HUMAN_(?:Move|Suspend|TurnAt|SETMODE)')

    def test_death_alarm_and_rescue_disable_new_signals_first(self):
        changes = builder.change_specs(self.gestures)
        for change, prefixes in ((changes[0], ['OnDeath()\n{','OnAlarm()\n{']),
                                 (changes[1], ['OnDeath()\n{','Whenever incloserange (_PlayerInRange(4))\n{'])):
            for prefix in prefixes:
                edit = next(e for e in change['edits'] if e['before'] == prefix)
                self.assertTrue(edit['after'].startswith(prefix+'\n  DisableSignals(true);'))
                self.assertNotIn('DisableSignals(false)', edit['after'])

    def test_controller_only_adds_two_pairs_of_modern_stop_signals(self):
        edits = builder.change_specs(self.gestures)[2]['edits']
        self.assertEqual(len(edits), 2)
        for edit in edits:
            self.assertTrue(edit['after'].startswith(edit['before']))
            addition = edit['after'][len(edit['before']):]
            self.assertEqual(re.findall(r'SendSignal\((\w+), (\d+)\)', addition), [('en20','99'),('sas','99')])
            self.assertNotRegex(addition, r'(?:MorphSpeech|Subtitles|SetObjective|SaveGame|Delay)')
        for change in builder.change_specs(self.gestures):
            added = '\n'.join(e['after'] for e in change['edits'])
            self.assertNotRegex(added, r'(?:SetObjectiveStatus|SaveGameValue|SetNPCTeamStatus)\(')


if __name__ == '__main__':
    unittest.main()
