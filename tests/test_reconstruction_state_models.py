"""Finite models of reconstruction predicates, not an emulator of the game."""
import itertools
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_reconstruction_variant import load_catalog, apply_edits
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


if __name__ == "__main__":
    unittest.main()
