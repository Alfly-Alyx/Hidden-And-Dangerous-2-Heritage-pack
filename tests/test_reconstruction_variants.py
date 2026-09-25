"""Offline regression tests using invented data, never commercial game scripts."""
from contextlib import redirect_stdout, redirect_stderr
import copy
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_reconstruction_variant as builder


def field(kind, text):
    value = text.encode("cp1252") + b"\0"
    return struct.pack("<HI", kind, len(value) + 6) + value


class MemorySources:
    def __init__(self, files):
        self.files = files

    def read(self, name):
        return self.files[name]


def fixture():
    source = b'// invented fixture\r\n//Move("P1");\r\nEnd();\r\n'
    files = {
        "scripts/example/source.scr": ("Scripts.dta", source),
        "missions/example/scripts.dta": (
            "missions.dta", b"\0" * 6 + field(1, "Owner") + field(1, "Source.scr")),
        "missions/example/actors.bin": ("missions.dta", field(0x10, "Owner")),
        "missions/example/check2.bin": ("missions.dta", b"P1\0"),
    }
    profile = {
        "id": "example-variant", "title": "Invented fixture",
        "source": "scripts/example/source.scr", "actor": "Owner",
        "default_profile": "commercial", "runtime_status": "pending",
        "evidence": {name: {"archive": arc, "size": len(raw),
                            "sha256": builder.digest(raw)}
                     for name, (arc, raw) in files.items()},
        "checks": [{"entry": "missions/example/check2.bin",
                    "kind": "nul_strings", "values": ["P1"]}],
        "edits": [{"before": '//Move("P1");', "after": 'Move("P1");'}],
    }
    return profile, files


class VariantTests(unittest.TestCase):
    def setUp(self):
        self.profile, self.files = fixture()

    def repin(self, name, raw):
        archive = self.files[name][0]
        self.files[name] = (archive, raw)
        self.profile["evidence"][name].update(size=len(raw), sha256=builder.digest(raw))

    def test_minimal_change_preserves_all_other_bytes(self):
        variant, report = builder.prepare(self.profile, MemorySources(self.files))
        source = self.files[self.profile["source"]][1]
        self.assertEqual(variant, source.replace(b"//Move", b"Move"))
        self.assertEqual(report["variant_sha256"], builder.digest(variant))
        self.assertEqual(report["runtime_status"], "pending")
        self.assertFalse(report["installed_into_game"])
        self.assertIsNone(report["output"])

    def test_hash_mismatch_refused(self):
        key = self.profile["source"]
        arc, raw = self.files[key]
        self.files[key] = (arc, raw + b" ")
        with self.assertRaisesRegex(ValueError, "source changed"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_archive_change_refused_even_with_identical_bytes(self):
        key = self.profile["source"]
        self.files[key] = ("Patch.dta", self.files[key][1])
        with self.assertRaisesRegex(ValueError, "source changed"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_missing_binding_refused(self):
        self.repin("missions/example/scripts.dta", b"\0" * 6)
        with self.assertRaisesRegex(ValueError, "owner binding"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_duplicate_binding_refused(self):
        key = "missions/example/scripts.dta"
        self.repin(key, self.files[key][1] + field(1, "OWNER") + field(1, "Source.scr"))
        with self.assertRaisesRegex(ValueError, "owner binding"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_wrong_binding_refused(self):
        self.repin("missions/example/scripts.dta",
                   b"\0" * 6 + field(1, "Owner") + field(1, "Other.scr"))
        with self.assertRaisesRegex(ValueError, "owner binding"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_missing_actor_refused(self):
        self.repin("missions/example/actors.bin", field(0x10, "Other"))
        with self.assertRaisesRegex(ValueError, "serialized actor"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_missing_checkpoint_refused(self):
        self.repin("missions/example/check2.bin", b"P10\0")
        with self.assertRaisesRegex(ValueError, "prerequisite: P1"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_frames_are_structured_names_not_arbitrary_substrings(self):
        self.profile["checks"] = [{"entry": "missions/example/actors.bin",
                                    "kind": "frames", "values": ["Seat"]}]
        self.repin("missions/example/actors.bin", field(0x10, "Owner") + b"Seat\0")
        with self.assertRaisesRegex(ValueError, "prerequisite: Seat"):
            builder.prepare(self.profile, MemorySources(self.files))
        self.repin("missions/example/actors.bin", field(0x10, "Owner") + field(0x10, "Seat"))
        builder.prepare(self.profile, MemorySources(self.files))

    def test_changed_anchor_refused(self):
        self.profile["edits"][0]["before"] = "not in the source"
        with self.assertRaisesRegex(ValueError, "exactly once"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_ambiguous_anchor_refused(self):
        key = self.profile["source"]
        self.repin(key, self.files[key][1] * 2)
        with self.assertRaisesRegex(ValueError, "exactly once"):
            builder.prepare(self.profile, MemorySources(self.files))

    def test_multiline_crlf_preserved(self):
        result = builder.apply_edits(b"A\r\nB\r\nZ\r\n", [
            {"before": "A\nB", "after": "C\nD\nE"}])
        self.assertEqual(result, b"C\r\nD\r\nE\r\nZ\r\n")

    def test_lf_and_cp1252_preserved(self):
        result = builder.apply_edits(b"caf\xe9\nA\n", [{"before": "A", "after": "B"}])
        self.assertEqual(result, b"caf\xe9\nB\n")

    def test_mixed_newlines_untouched_for_single_line_edit(self):
        self.assertEqual(builder.apply_edits(b"A\r\nB\n", [{"before": "A", "after": "C"}]),
                         b"C\r\nB\n")

    def test_multiline_insert_uses_local_line_ending(self):
        self.assertEqual(builder.apply_edits(b"A\nB\r\n", [{"before": "B", "after": "C\nD"}]),
                         b"A\nC\r\nD\r\n")

    def test_ambiguous_multiline_anchor_across_newline_styles_refused(self):
        with self.assertRaisesRegex(ValueError, "exactly once"):
            builder.apply_edits(b"A\r\nB\r\nA\nB\n", [{"before": "A\nB", "after": "C"}])

    def test_empty_and_noop_edits_refused(self):
        for edit in ({"before": "", "after": "A"}, {"before": "A", "after": "A"}):
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                builder.apply_edits(b"A", [edit])


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        self.output = self.root / ".analysis/test.scr.disabled"

    def write(self, path):
        return builder.write_disabled(path, b"invented fixture", self.game, self.root)

    def test_disabled_artifact_writes_once(self):
        self.assertEqual(self.write(self.output), self.output.resolve())
        self.assertEqual(self.output.read_bytes(), b"invented fixture")
        with self.assertRaises(FileExistsError):
            self.write(self.output)
        self.assertEqual(self.output.read_bytes(), b"invented fixture")

    def test_active_extension_refused(self):
        with self.assertRaisesRegex(ValueError, "scr.disabled"):
            self.write(self.output.with_suffix(".scr"))

    def test_output_outside_analysis_refused(self):
        with self.assertRaisesRegex(ValueError, "ignored .analysis"):
            self.write(self.root / "public.scr.disabled")
        self.assertFalse((self.root / "public.scr.disabled").exists())

    def test_parent_traversal_refused(self):
        with self.assertRaisesRegex(ValueError, "ignored .analysis"):
            self.write(self.root / ".analysis/../escape.scr.disabled")

    def test_game_below_analysis_still_cannot_be_written(self):
        game = self.root / ".analysis/licensed-game"
        with self.assertRaisesRegex(ValueError, "game installation"):
            builder.write_disabled(game / "test.scr.disabled", b"test", game, self.root)

    def test_resolved_link_escape_refused(self):
        # Mock the resolved target so the guard is covered without requiring
        # Windows administrator privileges to create filesystem symlinks.
        candidate = unittest.mock.Mock()
        candidate.resolve.return_value = self.root / "elsewhere/test.scr.disabled"
        with self.assertRaisesRegex(ValueError, "ignored .analysis"):
            self.write(candidate)


class FakeArchive:
    def __init__(self, entries):
        self.entries = [SimpleNamespace(name=n, data=b) for n, b in entries]
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    def read(self, entry):
        return entry.data


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game = Path(self.temp.name)
        self.archives = {name: FakeArchive([]) for name in (*builder.ARCHIVES, "PatchX01.dta")}
        self.key = "scripts/example/source.scr"
        self.archives["Scripts.dta"] = FakeArchive([("SCRIPTS\\EXAMPLE\\Source.scr", b"base")])
        mock = patch.object(builder, "DtaArchive", side_effect=lambda p: self.archives[p.name])
        mock.start()
        self.addCleanup(mock.stop)

    def test_effective_patch_is_used_and_handles_are_closed(self):
        self.archives["Patch.dta"] = FakeArchive([(self.key, b"patch")])
        with builder.ArchiveSources(self.game) as reader:
            self.assertEqual(reader.read(self.key), ("Patch.dta", b"patch"))
        self.assertTrue(all(self.archives[a].closed for a in builder.ARCHIVES))

    def test_duplicate_normalized_entry_refused(self):
        self.archives["Scripts.dta"] = FakeArchive([(self.key, b"a"), (self.key.upper(), b"b")])
        with builder.ArchiveSources(self.game) as reader, self.assertRaisesRegex(ValueError, "Ambiguous"):
            reader.read(self.key)

    def test_patchx_override_is_not_guessed(self):
        (self.game / "PatchX01.dta").touch()
        self.archives["PatchX01.dta"] = FakeArchive([(self.key, b"unknown")])
        with builder.ArchiveSources(self.game) as reader, self.assertRaisesRegex(ValueError, "PatchX01"):
            reader.read(self.key)

    def test_loose_override_refused(self):
        loose = self.game / self.key
        loose.parent.mkdir(parents=True)
        loose.write_bytes(b"local mod")
        with builder.ArchiveSources(self.game) as reader, self.assertRaisesRegex(ValueError, "Loose override"):
            reader.read(self.key)

    def test_explicit_archives_only_reports_but_preserves_loose_file(self):
        loose = self.game / self.key
        loose.parent.mkdir(parents=True)
        loose.write_bytes(b"local mod")
        with builder.ArchiveSources(self.game, archives_only=True) as reader:
            self.assertEqual(reader.read(self.key), ("Scripts.dta", b"base"))
            self.assertEqual(reader.excluded_loose_overrides[self.key],
                             {"size": 9, "sha256": builder.digest(b"local mod")})
        self.assertEqual(loose.read_bytes(), b"local mod")

    def test_missing_entry_refused(self):
        with builder.ArchiveSources(self.game) as reader, self.assertRaisesRegex(ValueError, "Missing"):
            reader.read("scripts/example/absent.scr")


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.profile, _ = fixture()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "catalog.json"

    def load(self, profiles):
        self.path.write_text(json.dumps({"schema_version": 1, "profiles": profiles}), encoding="utf-8")
        return builder.load_catalog(self.path)

    def test_shipped_catalog_loads(self):
        profiles = builder.load_catalog()
        self.assertEqual(len(profiles), 11)

    def test_nosic2_pause_replaces_instead_of_stacking_delays(self):
        profile = builder.load_catalog()["czech3-nosic2-long-smoke"]
        source = (b'Smoke(true);\r\n//HUMAN_TurnAt(smoker_eyeball_point);\r\n'
                  b'//delay(42000);\r\ndelay(5000);\r\nSmoke(false);')
        result = builder.apply_edits(source, profile["edits"])
        self.assertEqual(result, b'Smoke(true);\r\nHUMAN_TurnAt(smoker_eyeball_point);\r\n'
                         b'delay(42000);\r\nSmoke(false);')

    def test_flak_exit_does_not_activate_boarding_or_change_death(self):
        profile = builder.load_catalog()["arctic4-gunner1-flak-exit"]
        source = (b'//HUMAN_BoardVehicle("flak", true, 0);\r\nOnAlarmDone()\r\n{\r\n'
                  b'Move();\r\n}\r\nOnDeath(){HUMAN_BoardVehicle("", False, 0);}')
        result = builder.apply_edits(source, profile["edits"])
        self.assertEqual(result, source.replace(b'OnAlarmDone()\r\n{',
                         b'OnAlarmDone()\r\n{\r\n  HUMAN_BoardVehicle("", False, 0);'))

    def test_cold_fallbacks_are_single_modern_insertions(self):
        for name in ("arctic4-guard2-cold-fallback", "arctic4-guard6-cold-fallback"):
            profile = builder.load_catalog()[name]
            self.assertEqual(profile["classification"], "MODERNE")
            edit, = profile["edits"]
            self.assertEqual(edit["after"].splitlines()[0], edit["before"])
            self.assertEqual(edit["after"].splitlines()[1].strip(), "HUMAN_ACTIVITY_Cold();")

    def test_af126_modern_fix_removes_only_the_empty_back_edge(self):
        profile = builder.load_catalog()["africa1-af126-safe-idle"]
        self.assertEqual(profile["classification"], "MODERNE")
        prefix = b"OnAlarmDone(){ goto START; }\r\nLabel ACTIVATE:\r\nIdle();\r\ngoto END;\r\n"
        source = prefix + b"Label START:\r\n//  doplnit\r\ngoto START;\r\n\r\nLabel END:"
        expected = prefix + b"Label START:\r\n//  doplnit\r\ngoto END;\r\n\r\nLabel END:"
        self.assertEqual(builder.apply_edits(source, profile["edits"]), expected)

    def test_af126_fix_refuses_a_loop_that_already_has_an_activity(self):
        profile = builder.load_catalog()["africa1-af126-safe-idle"]
        with self.assertRaisesRegex(ValueError, "exactly once"):
            builder.apply_edits(b"Label START:\r\nMove();\r\ngoto START;", profile["edits"])

    def test_duplicate_profile_refused(self):
        with self.assertRaisesRegex(ValueError, "duplicate profile"):
            self.load([self.profile, copy.deepcopy(self.profile)])

    def test_unpinned_prerequisite_refused(self):
        self.profile["checks"][0]["entry"] = "missions/example/missing.bin"
        with self.assertRaisesRegex(ValueError, "pinned evidence"):
            self.load([self.profile])

    def test_runtime_success_cannot_be_claimed_by_catalog(self):
        self.profile["runtime_status"] = "passed"
        with self.assertRaisesRegex(ValueError, "pending prototypes"):
            self.load([self.profile])

    def test_noncommercial_default_refused(self):
        self.profile["default_profile"] = "experimental"
        with self.assertRaisesRegex(ValueError, "commercial profile"):
            self.load([self.profile])

    def test_path_traversal_and_absolute_paths_refused(self):
        for value in ("scripts/../source.scr", "C:/game/file", "/scripts/example/source.scr",
                      "scripts/example/../../file", "scripts//source.scr"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                builder.entry_path(value)

    def test_missing_owner_evidence_refused(self):
        del self.profile["evidence"]["missions/example/actors.bin"]
        with self.assertRaisesRegex(ValueError, "actor evidence"):
            self.load([self.profile])

    def test_list_does_not_open_game(self):
        with patch.object(builder, "ArchiveSources") as reader, redirect_stdout(io.StringIO()):
            self.assertEqual(builder.main(["--list"]), 0)
            reader.assert_not_called()

    def test_check_is_read_only_by_default(self):
        profile, files = fixture()
        with patch.object(builder, "load_catalog", return_value={profile["id"]: profile}), \
                patch.object(builder, "ArchiveSources") as reader, \
                patch.object(builder, "write_disabled") as writer, redirect_stdout(io.StringIO()):
            reader.return_value.__enter__.return_value = MemorySources(files)
            self.assertEqual(builder.main(["--profile", profile["id"], "--game", "invented"]), 0)
            writer.assert_not_called()

    def test_bulk_build_and_output_without_build_refused(self):
        for args in (["--check-all", "--build"], ["--profile", "test", "--output", "x"]):
            with self.subTest(args=args), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                builder.main(args)


if __name__ == "__main__":
    unittest.main()
