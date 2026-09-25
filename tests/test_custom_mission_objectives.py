"""Template objective preservation tests with synthetic mission data only."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from custom_mission_packages import read_package, load_library, localized_values
from objective_audit import blocks
from build_static_custom_menu import rewrite_mission, encode_existing_block


def block(kind, payload):
    return struct.pack("<HI", kind, len(payload) + 6) + payload


class ObjectiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = Path(self.temp.name)
        self.package = self.library / "fixture"
        tree = self.package / "payload/Missions/LabMission/tree.klz"
        tree.parent.mkdir(parents=True)
        tree.write_bytes(b"synthetic tree")
        self.document = {"format": 1, "id": "test.objectives", "category": "user-mission",
                         "missionDirectory": "LabMission", "title": "Laboratoire"}
        self.objectives = [
            block(0x28, block(0x29, struct.pack("<I", 111)) + block(0x2A, b"first-flags")),
            block(0x28, block(0x29, struct.pack("<I", 222)) + block(0x2A, b"second-flags")),
        ]
        source = block(0x32, block(0x33, struct.pack("<I", 333))
                       + block(0x36, b"SourceMission\0") + b"".join(self.objectives))
        self.node = blocks(source, 0, len(source))[0]

    def read(self):
        (self.package / "mission.json").write_text(json.dumps(self.document), encoding="utf-8")
        return read_package(self.package)

    def preserved(self):
        self.document.update(templateMission="SourceMission", preserveTemplateObjectives=True)
        return self.read()

    def rewritten_objectives(self, package):
        data = rewrite_mission(self.node, package)
        return [encode_existing_block(n) for n in blocks(data, 0, len(data))[0].children
                if n.kind == 0x28]

    def test_preserve_exact_objectives_including_different_flags(self):
        self.assertEqual(self.rewritten_objectives(self.preserved()), self.objectives)

    def test_existing_empty_default_still_removes_objectives(self):
        self.assertEqual(self.rewritten_objectives(self.read()), [])

    def test_explicit_custom_objectives_still_work(self):
        self.document["objectives"] = ["New first", "New second", "New third"]
        package = self.read()
        self.assertEqual(len(self.rewritten_objectives(package)), 3)

    def test_explicit_false_keeps_existing_semantics(self):
        self.document["preserveTemplateObjectives"] = False
        self.assertEqual(self.rewritten_objectives(self.read()), [])

    def test_true_requires_template(self):
        self.document["preserveTemplateObjectives"] = True
        with self.assertRaisesRegex(ValueError, "exige templateMission"):
            self.read()

    def test_true_refuses_even_empty_objective_override(self):
        self.document.update(templateMission="SourceMission", preserveTemplateObjectives=True, objectives=[])
        with self.assertRaisesRegex(ValueError, "interdit le champ objectives"):
            self.read()

    def test_flag_must_be_boolean(self):
        for value in ("true", 1, None, []):
            with self.subTest(value=value):
                self.document["preserveTemplateObjectives"] = value
                with self.assertRaisesRegex(ValueError, "booléen"):
                    self.read()

    def test_library_keeps_preservation_without_allocating_objective_texts(self):
        self.preserved()
        packages = load_library(self.library)
        self.assertTrue(packages[0]["preserve_template_objectives"])
        self.assertEqual(packages[0]["objective_ids"], [])
        self.assertEqual(len(localized_values(packages, "french")), 1)
        self.assertEqual(self.rewritten_objectives(packages[0]), self.objectives)


if __name__ == "__main__":
    unittest.main()
