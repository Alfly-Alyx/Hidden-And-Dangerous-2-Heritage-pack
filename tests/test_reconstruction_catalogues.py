"""Catalogue inspection helpers tested without commercial data or a game."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reconstruction_catalogue_audit import mission_nodes, objective_bytes


def block(kind, payload):
    return struct.pack("<HI", kind, len(payload) + 6) + payload


def mission(name, objectives):
    return block(0x32, block(0x36, name.encode() + b"\0")
                 + b"".join(block(0x28, raw) for raw in objectives))


class CatalogueInspectionTests(unittest.TestCase):
    def test_objective_order_and_flags_are_not_normalized(self):
        originals = [block(0x29, b"first-id") + block(0x2A, b"flag-A"),
                     block(0x29, b"second-id") + block(0x2A, b"flag-B")]
        nodes = mission_nodes(block(0x01, mission("Example", originals)))
        self.assertEqual(objective_bytes(nodes["example"]), originals)

    def test_malformed_catalogue_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unreadable"):
            mission_nodes(b"not a catalogue")

    def test_duplicate_mission_names_ignore_case(self):
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            mission_nodes(mission("Example", []) + mission("EXAMPLE", []))

    def test_zero_objectives_are_preserved_as_zero(self):
        self.assertEqual(objective_bytes(mission_nodes(mission("Empty", []))["empty"]), [])


if __name__ == "__main__":
    unittest.main()
