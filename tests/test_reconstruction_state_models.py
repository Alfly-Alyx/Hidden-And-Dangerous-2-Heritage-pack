"""Finite models of reconstruction predicates, not an emulator of the game."""
import itertools
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_reconstruction_variant import load_catalog, apply_edits


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


if __name__ == "__main__":
    unittest.main()
