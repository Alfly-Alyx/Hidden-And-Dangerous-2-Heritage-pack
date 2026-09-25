"""Inert mission A/B bundle tests; fixtures are invented and contain no game data."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_reconstruction_lab as lab
from test_reconstruction_variants import fixture, field, MemorySources


class LabSources(MemorySources):
    def mission_entries(self, mission):
        return sorted(self.files)


class LabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        self.output = self.root / ".analysis/result.lab.zip.disabled"
        self.profile, self.files = fixture()
        for name in ("tree.klz", "scene.4ds", "scene2.bin"):
            self.files[f"missions/example/{name}"] = ("missions.dta", b"invented " + name.encode())
        self.sources = LabSources(self.files)

    def plan(self):
        return lab.plan_lab(self.profile, self.sources)

    def write(self, members):
        return lab.write_bundle(self.output, members, self.game, root=self.root)

    def unchecked_zip(self, members):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(self.output, "w") as archive:
            for name, raw in members.items():
                archive.writestr(name, raw)

    def update_report(self, members, report):
        members["lab-report.json"] = json.dumps(report).encode()

    def test_roundtrip_only_one_script_differs(self):
        members, report = self.plan()
        self.write(members)
        checked = lab.verify_bundle(self.output)
        self.assertEqual(checked["profile"], self.profile["id"])
        self.assertEqual(checked["script_closure"]["reachable_scripts"], 1)
        self.assertEqual(checked["runtime_status"], "pending")
        self.assertFalse(checked["installed_into_game"])
        self.assertNotEqual(report["packages"][0]["mission_directory"],
                            report["packages"][1]["mission_directory"])

    def test_unrelated_loose_override_is_not_attributed_to_this_lab(self):
        self.sources.excluded_loose_overrides = {
            "missions/other/scripts.dta": {"size": 1, "sha256": "0" * 64},
            "missions/example/scripts.dta": {"size": 2, "sha256": "1" * 64},
        }
        _, report = self.plan()
        self.assertEqual(set(report["excluded_loose_overrides"]), {"missions/example/scripts.dta"})

    def test_all_manifest_and_payload_members_are_disabled(self):
        members, _ = self.plan()
        self.assertTrue(all(name == "lab-report.json" or name.endswith(".disabled") for name in members))
        self.assertFalse(any(name.endswith((".scr", "/tree.klz", "/mission.json")) for name in members))

    def test_deterministic_zip(self):
        members, _ = self.plan()
        self.write(members)
        second = self.root / ".analysis/second.lab.zip.disabled"
        lab.write_bundle(second, members, self.game, root=self.root)
        self.assertEqual(self.output.read_bytes(), second.read_bytes())

    def test_existing_output_refused_and_preserved(self):
        members, _ = self.plan()
        self.write(members)
        before = self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            self.write(members)
        self.assertEqual(self.output.read_bytes(), before)

    def test_missing_geometry_refused_before_output(self):
        del self.files["missions/example/tree.klz"]
        with self.assertRaisesRegex(ValueError, "Incomplete source mission"):
            self.plan()
        self.assertFalse(self.output.exists())

    def test_missing_dynamic_dependency_refused(self):
        self.files["scripts/example/helper.scr"] = ("Scripts.dta", b'ScriptAssign(owner, "missing");')
        self.files["missions/example/scripts.dta"] = (
            "missions.dta", b"\0" * 6 + field(1, "Owner") + field(1, "Source.scr")
            + field(1, "Helper") + field(1, "helper.scr"))
        raw = self.files["missions/example/scripts.dta"][1]
        self.profile["evidence"]["missions/example/scripts.dta"].update(size=len(raw), sha256=lab.digest(raw))
        with self.assertRaisesRegex(ValueError, "Missing script dependencies"):
            self.plan()

    def test_transitive_include_copied(self):
        self.files["scripts/example/helper.scr"] = ("Scripts.dta", b"End();")
        key = self.profile["source"]
        raw = self.files[key][1] + b'\r\n#include "helper.scr"\r\n'
        self.files[key] = ("Scripts.dta", raw)
        self.profile["evidence"][key].update(size=len(raw), sha256=lab.digest(raw))
        _, report = self.plan()
        self.assertEqual(report["script_closure"]["reachable_scripts"], 2)
        self.assertEqual(report["script_closure"]["available_scripts"], 2)

    def test_dynamic_script_name_refused(self):
        key = self.profile["source"]
        raw = self.files[key][1] + b"\r\nScriptAssign(owner, variable);"
        self.files[key] = ("Scripts.dta", raw)
        self.profile["evidence"][key].update(size=len(raw), sha256=lab.digest(raw))
        with self.assertRaisesRegex(ValueError, "Non-literal"):
            self.plan()

    def test_empty_literal_script_detachment_is_not_a_missing_dependency(self):
        key = self.profile["source"]
        raw = self.files[key][1] + b'\r\nScriptAssign(owner, "");'
        self.files[key] = ("Scripts.dta", raw)
        self.profile["evidence"][key].update(size=len(raw), sha256=lab.digest(raw))
        _, report = self.plan()
        self.assertEqual(report["script_closure"]["reachable_scripts"], 1)

    def test_concatenated_script_name_is_not_mistaken_for_a_literal(self):
        key = self.profile["source"]
        raw = self.files[key][1] + b'\r\nScriptAssign(owner, "helper" + variable);'
        self.files[key] = ("Scripts.dta", raw)
        self.files["scripts/example/helper.scr"] = ("Scripts.dta", b"End();")
        self.profile["evidence"][key].update(size=len(raw), sha256=lab.digest(raw))
        with self.assertRaisesRegex(ValueError, "Non-literal"):
            self.plan()

    def test_hardcoded_original_path_refused(self):
        self.files["missions/example/tree.klz"] = ("missions.dta", b"Missions\\Example\\collision.bin")
        with self.assertRaisesRegex(ValueError, "Hard-coded original"):
            self.plan()

    def test_member_path_traversal_refused(self):
        members, _ = self.plan()
        members["../escape"] = b"no"
        self.unchecked_zip(members)
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            lab.verify_bundle(self.output)

    def test_extra_active_script_refused(self):
        members, _ = self.plan()
        members["variant/extra.scr"] = b"no"
        self.unchecked_zip(members)
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            lab.verify_bundle(self.output)

    def test_corrupt_payload_refused(self):
        members, report = self.plan()
        member = report["packages"][1]["files"][0]["member"]
        members[member] += b"changed"
        self.unchecked_zip(members)
        with self.assertRaisesRegex(ValueError, "Corrupt"):
            lab.verify_bundle(self.output)

    def test_second_script_change_refused_even_with_updated_member_hash(self):
        members, report = self.plan()
        record = report["packages"][1]["files"][0]
        changed = members[record["member"]] + b"extra change"
        members[record["member"]] = changed
        record.update(size=len(changed), sha256=lab.digest(changed))
        self.update_report(members, report)
        self.unchecked_zip(members)
        with self.assertRaisesRegex(ValueError, "more than the approved"):
            lab.verify_bundle(self.output)

    def test_original_namespace_cannot_be_payload_destination(self):
        members, report = self.plan()
        report["packages"][0]["files"][0]["proposed_relative_path"] = "Missions/example/actors.bin"
        self.update_report(members, report)
        self.unchecked_zip(members)
        with self.assertRaisesRegex(ValueError, "escapes"):
            lab.verify_bundle(self.output)

    def test_two_modes_cannot_share_namespace(self):
        members, report = self.plan()
        report["packages"][1]["mission_directory"] = report["packages"][0]["mission_directory"]
        self.update_report(members, report)
        self.unchecked_zip(members)
        with self.assertRaisesRegex(ValueError, "namespace"):
            lab.verify_bundle(self.output)

    def test_objective_override_refused(self):
        members, report = self.plan()
        member = report["packages"][0]["manifest_member"]
        manifest = json.loads(members[member])
        manifest["objectives"] = []
        members[member] = json.dumps(manifest).encode()
        self.unchecked_zip(members)
        with self.assertRaisesRegex(ValueError, "objective contract"):
            lab.verify_bundle(self.output)

    def test_output_outside_analysis_and_game_inside_analysis_refused(self):
        members, _ = self.plan()
        with self.assertRaisesRegex(ValueError, "under .analysis"):
            lab.write_bundle(self.root / "unsafe.lab.zip.disabled", members, self.game, self.root)
        game = self.root / ".analysis/game"
        with self.assertRaisesRegex(ValueError, "outside the game"):
            lab.write_bundle(game / "unsafe.lab.zip.disabled", members, game, self.root)


if __name__ == "__main__":
    unittest.main()
