"""Synthetic bundle identification; no commercial resources or game execution."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import reconstruction_bundle_evidence as evidence
from build_reconstruction_lab import plan_lab, write_bundle
from test_reconstruction_labs import LabSources
from test_reconstruction_variants import fixture


class BundleEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile, self.files = fixture()
        for name in ('tree.klz', 'scene.4ds', 'scene2.bin'):
            self.files[f'missions/example/{name}'] = ('missions.dta', b'invented ' + name.encode())
        self.sources = LabSources(self.files)
        self.path = self.root / '.analysis/test.lab.zip.disabled'
        members, _ = plan_lab(self.profile, self.sources)
        write_bundle(self.path, members, self.root / 'unused-game', root=self.root)
        self.scene_path = self.root / '.analysis/test.scene-patch.zip.disabled'
        self.scene_payload = {name: ('invented ' + name).encode() for name in evidence.MEMBERS}
        self.scene_report = {'kind': 'inert_scene_registry_comparison', 'runtime_status': 'pending',
                             'installed_into_game': False, 'playable_mission': False,
                             'excluded_loose_overrides': {}, 'source_evidence': {}}

    def write_scene(self, payload=None, report=None):
        with zipfile.ZipFile(self.scene_path, 'w') as z:
            for name, raw in (payload or self.scene_payload).items():
                z.writestr(name, raw)
            z.writestr('report.json.disabled', json.dumps(report or self.scene_report))

    def inspect_scene(self):
        with patch.object(evidence, 'prepare_scene', return_value=(self.scene_payload, self.scene_report)):
            return evidence.inspect_scene(self.scene_path, 'co-burgundy3-ambience', object())

    def test_manifest_hash_is_deterministic_and_content_sensitive(self):
        files = {'Scripts/example/a.scr': b'A', 'Missions/example/tree.klz': b'B'}
        rows, sha = evidence.payload_manifest(files)
        self.assertEqual((rows, sha), evidence.payload_manifest(dict(reversed(list(files.items())))))
        files['Scripts/example/a.scr'] = b'changed'
        self.assertNotEqual(sha, evidence.payload_manifest(files)[1])

    def test_empty_unsafe_and_case_colliding_payloads_refused(self):
        for files in ({}, {'../x': b'x'}, {'Missions/../x': b'x'}, {'Missions/ex/x:y': b'x'},
                      {'Scripts/ex/a.scr': b'x', 'Scripts/EX/A.scr': b'y'}):
            with self.subTest(files=list(files)), self.assertRaises(ValueError):
                evidence.payload_manifest(files)

    def test_two_distinct_payloads_required(self):
        raw = {'Missions/ex/tree.klz': b'x'}
        for snapshots in ({'baseline': raw}, {'baseline': raw, 'variant': raw}):
            with self.assertRaises(ValueError):
                evidence.summarize('ex', 'script', 'ex', 'a' * 64, snapshots, {})

    def test_lab_reverified_against_sources_without_runtime_claim(self):
        report = evidence.inspect_lab(self.path, self.profile, self.sources)
        self.assertEqual(report['definition_sha256'], evidence.fingerprint(self.profile))
        self.assertNotEqual(report['baseline_payload_sha256'], report['variant_payload_sha256'])
        self.assertEqual(report['runtime_status'], 'pending')
        self.assertFalse(report['installed_into_game'])
        self.assertFalse(report['engine_executed'])
        self.assertFalse(report['automatic_activation_authorized'])

    def test_wrong_profile_or_active_extension_refused(self):
        with self.assertRaisesRegex(ValueError, 'another profile'):
            evidence.inspect_lab(self.path, {**self.profile, 'id': 'other'}, self.sources)
        with self.assertRaisesRegex(ValueError, 'disabled'):
            evidence.inspect_lab(self.root / 'active.zip', self.profile, self.sources)

    def test_changed_unedited_mission_resource_invalidates_bundle(self):
        self.files['missions/example/tree.klz'] = ('missions.dta', b'new tree')
        with self.assertRaisesRegex(ValueError, 'differs from current'):
            evidence.inspect_lab(self.path, self.profile, self.sources)

    def test_legacy_scene_metadata_needs_exact_fresh_payload(self):
        self.write_scene()
        report = self.inspect_scene()
        self.assertEqual(report['profile'], 'co-burgundy3-ambience')
        self.assertEqual(len(report['payloads']['baseline']['files']), 2)
        self.assertFalse(report['automatic_activation_authorized'])

    def test_scene_wrong_profile_or_claimed_active_state_refused(self):
        for change in ({'profile': 'other'}, {'runtime_status': 'passed'},
                       {'installed_into_game': True}, {'playable_mission': True}):
            with self.subTest(change=change):
                self.write_scene(report={**self.scene_report, **change})
                with self.assertRaises(ValueError):
                    self.inspect_scene()

    def test_scene_tampered_or_extra_payload_refused(self):
        altered = dict(self.scene_payload)
        altered['variant/scene2.bin.disabled'] += b'changed'
        self.write_scene(payload=altered)
        with self.assertRaisesRegex(ValueError, 'differs from current'):
            self.inspect_scene()
        self.write_scene(payload={**self.scene_payload, 'active.scr': b'unreviewed'})
        with self.assertRaisesRegex(ValueError, 'members'):
            self.inspect_scene()

    def test_duplicate_or_oversized_members_refused_before_read(self):
        for names, sizes in [(['a', 'a'], [1, 1]), (['a'], [513 * 1024 * 1024])]:
            fake = SimpleNamespace(namelist=lambda: names,
                                   infolist=lambda: [SimpleNamespace(file_size=s) for s in sizes])
            with self.assertRaisesRegex(ValueError, 'members'):
                evidence.check_members(fake, {'a'})


if __name__ == '__main__':
    unittest.main()
