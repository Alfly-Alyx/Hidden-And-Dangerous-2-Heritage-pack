"""Synthetic runtime records: these tests never launch or validate the game."""
import copy
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import reconstruction_runtime_audit as audit


class RuntimeRegisterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        study = self.root / 'experimental/example/ETUDE.md'
        study.parent.mkdir(parents=True)
        study.write_text('Synthetic study', encoding='utf-8')
        self.artifact = self.root / 'validation/evidence/reconstruction/fixture.txt'
        self.artifact.parent.mkdir(parents=True)
        self.artifact.write_text('Invented evidence, not an in-game test', encoding='utf-8')
        self.expected = {'example': {'kind': 'script', 'mission': 'example', 'definition_sha256': 'a' * 64}}
        self.profile = {'id': 'example', **self.expected['example'], 'title': 'Invented test',
                        'study': 'experimental/example/ETUDE.md', 'mode': 'solo',
                        'prerequisites': ['Use an isolated test copy'],
                        'steps': ['Observe the baseline', 'Compare the single changed behavior'],
                        'results': {s: {'state': 'pending', 'evidence': None} for s in audit.SCENARIOS}}
        self.register = {'schema_version': 1, 'scope': 'experimental-reconstruction',
                         'default_profile': 'commercial', 'profiles': [self.profile],
                         'common_scenarios': {s: 'Execute the invented test' for s in audit.SCENARIOS | {'network'}}}

    def run_audit(self):
        return audit.validate(self.register, self.expected, self.root)

    def evidence(self):
        return {'tester': 'Synthetic unit-test fixture', 'date': '2000-01-01', 'mode': 'solo',
                'game_build_sha256': 'b' * 64, 'baseline_payload_sha256': 'c' * 64,
                'variant_payload_sha256': 'd' * 64,
                'test_plan_sha256': audit.test_plan_fingerprint(
                    self.profile, self.register['common_scenarios'],
                    audit.study_fingerprint(self.root / self.profile['study'])),
                'notes': 'Invented data only; no game execution.',
                'artifacts': [{'path': self.artifact.relative_to(self.root).as_posix(),
                               'sha256': audit.file_hash(self.artifact)}]}

    def record(self, state='passed'):
        self.profile['results']['effect'] = {'state': state, 'evidence': self.evidence()}
        return self.profile['results']['effect']['evidence']

    def test_pending_is_structurally_valid_but_not_validated(self):
        report = self.run_audit()
        self.assertTrue(report['ok'])
        self.assertEqual(report['states'], {'pending': 6})
        self.assertFalse(report['all_recorded_passes'])
        self.assertFalse(report['engine_executed_by_this_audit'])
        self.assertFalse(report['automatic_activation_authorized'])

    def test_repository_register_covers_current_recipes_without_claiming_passes(self):
        report = audit.audit(ROOT)
        self.assertTrue(report['ok'], report['errors'])
        self.assertEqual(report['profiles'], report['expected_profiles'])
        self.assertEqual(report['profiles'], 50)
        self.assertEqual(report['states'], {'pending': 304})

    def test_unknown_missing_and_duplicate_profiles_are_refused(self):
        original = copy.deepcopy(self.register)
        for profiles in ([], [self.profile, self.profile], [{**self.profile, 'id': 'other'}]):
            self.register = {**original, 'profiles': profiles}
            self.assertFalse(self.run_audit()['ok'])

    def test_changed_definition_kind_or_mission_invalidates_record(self):
        for field, value in [('definition_sha256', '0' * 64), ('kind', 'other'), ('mission', 'elsewhere')]:
            with self.subTest(field=field):
                old = self.profile[field]
                self.profile[field] = value
                self.assertFalse(self.run_audit()['ok'])
                self.profile[field] = old

    def test_experimental_cannot_be_default(self):
        self.register['default_profile'] = 'example'
        self.assertFalse(self.run_audit()['ok'])

    def test_study_paths_are_local_existing_markdown(self):
        for path in ('../secret.md', '/absolute.md', 'D:/secret.md', 'experimental/missing.md',
                     'validation/evidence/reconstruction/fixture.txt'):
            with self.subTest(path=path):
                self.profile['study'] = path
                self.assertFalse(self.run_audit()['ok'])

    def test_exact_scenarios_and_network_for_cooperative_recipe(self):
        original = copy.deepcopy(self.profile['results'])
        del self.profile['results']['rollback']
        self.assertFalse(self.run_audit()['ok'])
        self.profile['results'] = original
        self.profile['kind'] = self.expected['example']['kind'] = 'scene_registry'
        self.profile['mode'] = 'cooperation'
        self.assertFalse(self.run_audit()['ok'])
        self.profile['results']['network'] = {'state': 'pending', 'evidence': None}
        self.assertTrue(self.run_audit()['ok'])

    def test_malformed_records_report_errors(self):
        for value in (None, [], {}, {'profiles': [None]}, {'profiles': 'invalid'}):
            with self.subTest(value=value):
                self.assertFalse(audit.validate(value, self.expected, self.root)['ok'])
        self.profile['results']['effect']['state'] = []
        self.assertFalse(self.run_audit()['ok'])

    def test_pending_cannot_carry_claimed_results(self):
        self.profile['results']['effect']['evidence'] = self.evidence()
        self.assertFalse(self.run_audit()['ok'])

    def test_blocked_requires_precise_notes(self):
        result = self.profile['results']['effect']
        result.update(state='blocked', evidence=None)
        self.assertFalse(self.run_audit()['ok'])
        result['evidence'] = {'notes': 'The synthetic test copy has not been prepared.'}
        self.assertTrue(self.run_audit()['ok'])
        self.assertFalse(self.run_audit()['all_recorded_passes'])

    def test_pass_without_complete_evidence_is_refused(self):
        self.profile['results']['effect'].update(state='passed', evidence=None)
        self.assertFalse(self.run_audit()['ok'])
        evidence = self.record()
        evidence['artifacts'] = []
        self.assertFalse(self.run_audit()['ok'])

    def test_recorded_passes_do_not_authorize_activation(self):
        for name in self.profile['results']:
            self.profile['results'][name] = {'state': 'passed', 'evidence': self.evidence()}
        report = self.run_audit()
        self.assertTrue(report['ok'], report['errors'])
        self.assertTrue(report['all_recorded_passes'])
        self.assertFalse(report['automatic_activation_authorized'])
        self.assertFalse(report['stable_release_register_modified'])

    def test_artifact_hash_and_presence_are_checked(self):
        evidence = self.record()
        evidence['artifacts'][0]['sha256'] = '0' * 64
        self.assertFalse(self.run_audit()['ok'])
        evidence['artifacts'][0]['path'] = 'validation/evidence/reconstruction/missing.txt'
        self.assertFalse(self.run_audit()['ok'])

    def test_unsafe_evidence_paths_are_refused(self):
        evidence = self.record()
        for path in ('/tmp/x', '../x', 'C:/x', 'validation/evidence/reconstruction/../x',
                     'validation\\evidence\\x', 'experimental/example/ETUDE.md'):
            with self.subTest(path=path):
                evidence['artifacts'][0]['path'] = path
                self.assertFalse(self.run_audit()['ok'])

    def test_dates_build_hashes_and_modes_are_checked(self):
        for field, value in [('date', '9999-01-01'), ('date', '2000-02-30'), ('date', None),
                             ('mode', 'cooperation'), ('game_build_sha256', 'unknown'),
                             ('variant_payload_sha256', 'c' * 64), ('tester', '')]:
            with self.subTest(field=field, value=value):
                evidence = self.record()
                evidence[field] = value
                self.assertFalse(self.run_audit()['ok'])

    def test_failure_requires_evidence_and_is_not_a_pass(self):
        self.record('failed')
        report = self.run_audit()
        self.assertTrue(report['ok'], report['errors'])
        self.assertFalse(report['all_recorded_passes'])

    def test_changed_plan_or_common_instructions_invalidate_old_evidence(self):
        self.record()
        self.profile['steps'].append('A newly required observation')
        self.assertFalse(self.run_audit()['ok'])
        self.record()
        self.register['common_scenarios']['save_load'] = 'A changed save/load protocol'
        self.assertFalse(self.run_audit()['ok'])

    def test_cli_complete_gate_is_distinct_from_structural_success(self):
        report = self.run_audit()
        with patch.object(audit, 'audit', return_value=report), redirect_stdout(io.StringIO()):
            self.assertEqual(audit.main([]), 0)
            self.assertEqual(audit.main(['--require-recorded-passes']), 1)

    def test_changed_study_invalidates_old_evidence(self):
        self.record()
        (self.root / self.profile['study']).write_text('Changed synthetic contract', encoding='utf-8')
        self.assertFalse(self.run_audit()['ok'])

    def test_study_fingerprint_ignores_checkout_line_endings(self):
        path = self.root / self.profile['study']
        path.write_bytes(b'line one\nline two\n')
        before = audit.study_fingerprint(path)
        path.write_bytes(b'line one\r\nline two\r\n')
        self.assertEqual(before, audit.study_fingerprint(path))


if __name__ == '__main__':
    unittest.main()
