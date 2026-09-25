"""Atomic multi-script reconstructions and typed 4DS owners: invented fixtures."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_reconstruction_variant as builder
import build_reconstruction_lab as lab
from test_reconstruction_variants import fixture, field, MemorySources
from test_reconstruction_labs import LabSources


def scene4ds(name):
    # One synthetic frame of supported type 10, no geometry or materials.
    header = b"4DS\0" + struct.pack("<H", 41) + b"\0" * 8 + struct.pack("<HH", 0, 1)
    node = (struct.pack("<BH", 10, 0) + struct.pack("<3f4f3f", 0, 0, 0, 0, 0, 0, 1, 1, 1, 1)
            + b"\0" * 5 + bytes([len(name)]) + name.encode() + b"\0" + b"\0" * 4)
    return header + node + b"\0"


def atomic_fixture():
    profile, files = fixture()
    files["scripts/example/helper.scr"] = ("Scripts.dta", b"//Enable();\r\n")
    files["missions/example/scripts.dta"] = (
        "missions.dta", files["missions/example/scripts.dta"][1]
        + field(1, "Helper") + field(1, "helper.scr"))
    files["missions/example/actors.bin"] = (
        "missions.dta", files["missions/example/actors.bin"][1] + field(0x10, "Helper"))
    for name in ("tree.klz", "scene2.bin"):
        files[f"missions/example/{name}"] = ("missions.dta", b"invented data")
    files["missions/example/scene.4ds"] = ("missions.dta", scene4ds("Owner"))
    profile["evidence"] = {name: {"archive": arc, "size": len(raw), "sha256": builder.digest(raw)}
                           for name, (arc, raw) in files.items()}
    profile["additional_changes"] = [{"source": "scripts/example/helper.scr", "actor": "Helper",
                                      "edits": [{"before": "//Enable();", "after": "Enable();"}]}]
    return profile, files


class AtomicTests(unittest.TestCase):
    def setUp(self):
        self.profile, self.files = atomic_fixture()

    def load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps({"schema_version": 1, "profiles": [self.profile]}))
            return builder.load_catalog(path)

    def test_all_changes_verified_together(self):
        self.load()
        data, report = builder.prepare_changes(self.profile, MemorySources(self.files))
        self.assertEqual(set(data), {self.profile["source"], "scripts/example/helper.scr"})
        self.assertEqual(data["scripts/example/helper.scr"], b"Enable();\r\n")
        self.assertEqual(report["changed_script_count"], 2)
        self.assertEqual(report["edit_count"], 2)
        self.assertEqual(report["runtime_status"], "pending")

    def test_single_script_api_refuses_incomplete_atomic_profile(self):
        with self.assertRaisesRegex(ValueError, "Atomic multi-script"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_cli_refuses_partial_export_without_creating_a_file(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(builder, "load_catalog", return_value={self.profile["id"]: self.profile}), \
                patch.object(builder, "ArchiveSources") as archive, redirect_stdout(io.StringIO()):
            archive.return_value.__enter__.return_value = MemorySources(self.files)
            output = Path(directory) / "partial.scr.disabled"
            result = builder.main(["--profile", self.profile["id"], "--game", directory,
                                   "--build", "--output", str(output)])
            self.assertEqual(result, 1)
            self.assertFalse(output.exists())

    def test_changed_companion_refuses_whole_profile(self):
        self.files["scripts/example/helper.scr"] = ("Scripts.dta", b"tampered")
        with self.assertRaisesRegex(ValueError, "source changed"):
            builder.prepare_changes(self.profile, MemorySources(self.files))

    def test_companion_requires_own_binding(self):
        self.profile["additional_changes"][0]["actor"] = "Missing"
        with self.assertRaisesRegex(ValueError, "owner binding"):
            builder.prepare_changes(self.profile, MemorySources(self.files))

    def test_duplicate_source_or_owner_refused(self):
        original = copy.deepcopy(self.profile)
        for key in ("source", "actor"):
            self.profile = copy.deepcopy(original)
            self.profile["additional_changes"][0][key] = self.profile[key]
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                self.load()

    def test_companion_cannot_escape_mission_or_override_evidence(self):
        self.profile["additional_changes"][0]["source"] = "scripts/other/helper.scr"
        with self.assertRaisesRegex(ValueError, "source mission"):
            self.load()
        self.profile, _ = atomic_fixture()
        self.profile["additional_changes"][0]["evidence"] = {}
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            self.load()

    def test_missing_companion_evidence_refused(self):
        del self.profile["evidence"]["scripts/example/helper.scr"]
        with self.assertRaisesRegex(ValueError, "Missing script"):
            self.load()

    def test_4ds_owner_decoded_from_typed_node_not_substring(self):
        self.profile["owner_entry"] = "missions/example/scene.4ds"
        self.profile["checks"].append({"kind": "4ds_frames", "entry": self.profile["owner_entry"],
                                       "values": ["Owner"]})
        self.load()
        _, report = builder.prepare_changes(self.profile, MemorySources(self.files))
        self.assertEqual(report["changes"][0]["owner_entry"], "missions/example/scene.4ds")
        self.assertEqual(report["changes"][1]["owner_entry"], "missions/example/actors.bin")
        self.files[self.profile["owner_entry"]] = ("missions.dta", b"not 4DS Owner\0")
        raw = self.files[self.profile["owner_entry"]][1]
        self.profile["evidence"][self.profile["owner_entry"]].update(size=len(raw), sha256=builder.digest(raw))
        with self.assertRaisesRegex(ValueError, "4DS"):
            builder.prepare_changes(self.profile, MemorySources(self.files))

    def test_4ds_owner_with_unknown_tail_refused(self):
        with self.assertRaisesRegex(ValueError, "Unparsed 4DS tail"):
            builder.typed_names(scene4ds("Owner") + b"unknown", "scene.4ds")

    def test_two_file_lab_roundtrip(self):
        members, report = lab.plan_lab(self.profile, LabSources(self.files))
        self.assertEqual(sum(r["changed_from_commercial"] for r in report["packages"][1]["files"]), 2)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = lab.write_bundle(root / ".analysis/result.lab.zip.disabled", members, root / "game", root)
            self.assertEqual(lab.verify_bundle(output)["variant"]["changed_script_count"], 2)

    def test_partial_atomic_payload_refused_even_with_matching_member_metadata(self):
        members, report = lab.plan_lab(self.profile, LabSources(self.files))
        record = next(r for r in report["packages"][1]["files"] if r["source_entry"].endswith("helper.scr"))
        raw = self.files[record["source_entry"]][1]
        members[record["member"]] = raw
        record.update(size=len(raw), sha256=builder.digest(raw))
        members["lab-report.json"] = json.dumps(report).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "omits a member"):
                lab.write_bundle(root / ".analysis/result.lab.zip.disabled", members, root / "game", root)

    def test_inconsistent_primary_proof_refused(self):
        members, report = lab.plan_lab(self.profile, LabSources(self.files))
        report["variant"]["variant_sha256"] = "0" * 64
        members["lab-report.json"] = json.dumps(report).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "Primary script proof"):
                lab.write_bundle(root / ".analysis/result.lab.zip.disabled", members, root / "game", root)

    def test_inconsistent_atomic_member_count_refused(self):
        members, report = lab.plan_lab(self.profile, LabSources(self.files))
        report["variant"]["changed_script_count"] = 1
        members["lab-report.json"] = json.dumps(report).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "omits a member"):
                lab.write_bundle(root / ".analysis/result.lab.zip.disabled", members, root / "game", root)


if __name__ == "__main__":
    unittest.main()
