"""Finite models of reconstruction predicates, not an emulator of the game."""
import itertools
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_reconstruction_variant import load_catalog, apply_edits, change_specs
from objective_audit import split_comments


class ChargePredicateTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_catalog()["sicily2-three-cleared-wave"]
        self.edit, = self.profile["edits"]

    def test_generated_predicate_counts_six_unique_charges_at_zero(self):
        expression = self.edit["after"]
        self.assertEqual(re.findall(r'_ACTOR_GetState\(N(\d)\)==(\d)', expression),
                         [(str(i), "0") for i in range(1, 7)])
        self.assertRegex(expression, r'\) >= 3\s*\) \)$')
        self.assertEqual(expression.count("("), expression.count(")"))

    def test_all_4096_state_vectors_exclude_live_exploded_and_legacy_states(self):
        # Evaluate only the parsed sum/comparison, without running game script.
        terms = re.findall(r'_ACTOR_GetState\(N(\d)\)==(\d)', self.edit["after"])
        for states in itertools.product(range(4), repeat=6):
            actual = sum(states[int(i) - 1] == int(state) for i, state in terms) >= 3
            self.assertEqual(actual, states.count(0) >= 3, states)
        self.assertFalse(sum(state == 0 for state in (2, 2, 2, 3, 3, 3)) >= 3)

    def test_skipping_the_exact_three_boundary_still_triggers(self):
        sequence = [(0, 0, 1, 1, 1, 1), (0, 0, 0, 0, 1, 1)]
        self.assertEqual([states.count(0) >= 3 for states in sequence], [False, True])

    def test_only_the_wave_predicate_changes_not_charge_states_or_objective(self):
        source = (self.edit["before"] + "\n{ goto tak; }\n"
                  "Whenever near(Range()) { goto tak; }\n"
                  "Label tak:\nSendSignal(enemy, 1);\nEndScript();").encode("ascii")
        result = apply_edits(source, self.profile["edits"])
        self.assertEqual(result.split(b"\n", 1)[1], source.split(b"\n", 1)[1])
        self.assertNotIn(b"SetActorState", result)
        self.assertNotIn(b"SetObjectiveStatus", result)


class SeatedGuardContractTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_catalog()["arctic4-guard3-sit-smoke"]
        self.edits = {edit["before"]: edit["after"] for edit in self.profile["edits"]}

    def test_unverified_named_animation_stays_commented(self):
        active = split_comments("\n".join(self.edits.values()))[0]
        self.assertNotIn("%%kourimsed2", active)
        self.assertIn("HUMAN_ACTIVITY_Sit(sit)", active)
        self.assertNotIn("StaticGuard3_5", active)
        self.assertEqual(self.profile["classification"], "MODERNE")

    def test_patrol_returns_to_standing_before_any_new_movement(self):
        source = b"label loop:\nMoveToNextPoint();"
        result = apply_edits(source, [{"before": "label loop:", "after": self.edits["label loop:"]}])
        self.assertLess(result.index(b"HUMAN_SETMODE_Stand"), result.index(b"MoveToNextPoint"))
        self.assertIn(b"SitActive = 0", result)

    def test_signal_cleans_posture_but_death_does_not_stand_up_a_corpse(self):
        signal = self.edits["OnSignal(1)\n{"]
        self.assertIn("HUMAN_ACTIVITY_Smoke(False)", signal)
        self.assertIn("HUMAN_SETMODE_Stand()", signal)
        self.assertIn("SitActive = 0", signal)
        death = self.edits["OnDeath()\n{"]
        self.assertIn("HUMAN_ACTIVITY_Smoke(False)", death)
        self.assertNotIn("Stand", death)
        self.assertNotIn("HUMAN_SetAnim", death)

    def test_sitting_flag_is_armed_before_sit_can_be_interrupted(self):
        body = next(after for before, after in self.edits.items() if "HUMAN_TurnAt(see)" in before)
        self.assertLess(body.index("SitActive = 1"), body.index("HUMAN_ACTIVITY_Sit(sit)"))
        self.assertIn("Delay(RNDwait)", body)


class InnerGuardContractTests(unittest.TestCase):
    def test_both_guards_only_enable_the_existing_detector(self):
        specs = change_specs(load_catalog()["normandy-inner-guards-proximity"])
        self.assertEqual([s["actor"] for s in specs], ["N24", "N25"])
        for spec in specs:
            self.assertEqual(spec["edits"], [{"before": "SetWhenever(player, false);",
                                             "after": "SetWhenever(player, true);"}])

    def test_signal_routes_and_mode_three_seven_branch_stay_byte_identical(self):
        # Invented contract fixture: the changed statement is after the 3/7 jump.
        prefix = (b"If((gametype==3) OR (gametype==7))\r\n{\r\n"
                  b" SetWhenever(player, true);\r\n GoTo dalej;\r\n}\r\n")
        suffix = (b"\r\nLabel dalej:\r\nWhenever activate(_SignalReceived(1))\r\n"
                  b"{ HUMAN_Suspend(false); GoTo alarmed; }\r\n"
                  b"Label alarmed:\r\nHUMAN_Move(\"N25_1\");\r\n")
        source = prefix + b"SetWhenever(player, false);" + suffix
        for spec in change_specs(load_catalog()["normandy-inner-guards-proximity"]):
            self.assertEqual(apply_edits(source, spec["edits"]),
                             prefix + b"SetWhenever(player, true);" + suffix)


class DepotSoundContractTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_catalog()["burgundy3-direct-explosion-sound"]
        self.sender, self.receiver = change_specs(self.profile)

    def test_new_signal_is_scoped_to_direct_label_and_keeps_old_signal(self):
        edit, = self.sender["edits"]
        self.assertTrue(edit["before"].startswith("Label DESTROY_DMG:\n"))
        self.assertEqual(edit["after"], edit["before"] + "\n    SendSignal(snd_strom, 11);")
        cinematic = b'OnCutscene(4) { SendSignal(snd_strom, 10); }\r\n'
        direct = edit["before"].replace("\n", "\r\n").encode("ascii")
        result = apply_edits(cinematic + direct + b'\r\nMakeExplosion(expl, 1, 1);\r\n}', [edit])
        self.assertTrue(result.startswith(cinematic))
        self.assertEqual(result.count(b'SendSignal(snd_strom, 11);'), 1)

    def test_receiver_is_monostable_before_first_sound_and_keeps_cinematic_body(self):
        edit, = self.receiver["edits"]
        body = edit["after"].split("OnCutscene(4)", 1)[0]
        self.assertTrue(body.startswith("OnSignal(11)"))
        self.assertLess(body.index("EnableSignal(11, false)"), body.index("FRM_SetOn"))
        self.assertNotIn("OnSignal(10)", body)
        self.assertNotIn("EnableSignal(11, true)", body)
        source = b'OnCutscene(4)\r\n{ ORIGINAL_BODY(); }\r\nOnCutsceneDone(4) {}'
        self.assertTrue(apply_edits(source, [edit]).endswith(source))

    def test_sound_order_delays_and_source_frames_are_explicit(self):
        body = self.receiver["edits"][0]["after"]
        self.assertEqual(re.findall(r'FRM_SetOn\(snd(\d), true\)', body),
                         ['7', '8', '9', '1', '2', '3', '4', '5', '6'])
        self.assertEqual(re.findall(r'Delay\((\d+)\)', body), ['150', '150', '100', '100', '100'])
        check = next(c for c in self.profile["checks"] if c["entry"].endswith('sounds.bin'))
        self.assertEqual(len(set(check["values"])), 9)
        self.assertIn(check["entry"], self.profile["evidence"])
        self.assertEqual(self.receiver["owner_entry"], 'missions/burgundy3/scene2.bin')

    def test_receiver_delta_matches_existing_reviewed_fragment(self):
        root = Path(__file__).resolve().parents[1]
        fragment = (root / 'experimental/BURGUNDY3_DEPOT_EXPLOSION_SOUND/'
                    'PROTOTYPE_ADDITIF_DIRECT_SIGNAL11.scr.disabled').read_text(encoding='utf-8')
        fragment = split_comments(fragment)[0].strip()
        inserted = self.receiver["edits"][0]["after"].split('OnCutscene(4)', 1)[0].strip()
        self.assertEqual(inserted, fragment)


class PanzerDriverContractTests(unittest.TestCase):
    def test_only_two_historical_alarm_masks_are_uncommented(self):
        p = load_catalog()['libye3-panzer-driver-alarm-gate']
        self.assertEqual(len(change_specs(p)), 1)
        self.assertEqual(p['actor'], 'Li3_German_Con_1')
        self.assertEqual(p['edits'], [
            {'before': '//SetAlarmType(1023, false);', 'after': 'SetAlarmType(1023, false);'},
            {'before': '//\tSetAlarmType(1023, true);', 'after': '\tSetAlarmType(1023, true);'},
        ])

    def test_alarm_reenable_stays_after_stop_without_changing_the_drive_calls(self):
        p = load_catalog()['libye3-panzer-driver-alarm-gate']
        route = (b'HUMAN_Drive("CON_4", 40);\r\nHUMAN_Drive("CON_5", 50);\r\n'
                 b'HUMAN_Drive("CON_107", 50);\r\nHUMAN_Drive("CON_108", 50);\r\n'
                 b'HUMAN_Drive("", 0);\r\n')
        source = b'//SetAlarmType(1023, false);\r\n' + route + b'//\tSetAlarmType(1023, true);'
        result = apply_edits(source, p['edits'])
        self.assertEqual(result, b'SetAlarmType(1023, false);\r\n' + route + b'\tSetAlarmType(1023, true);')
        self.assertNotIn(b'SendSignal', result)


if __name__ == "__main__":
    unittest.main()
