"""Synthetic preparation packs; no real game, installer or runtime evidence."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import prepare_reconstruction_trials as trials
from build_reconstruction_lab import plan_lab, write_bundle
from reconstruction_runtime_audit import SCENARIOS, fingerprint
from test_reconstruction_labs import LabSources
from test_reconstruction_variants import fixture


class TrialPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'source-game'
        self.game.mkdir()
        (self.game / 'HD2_SabreSquadron.exe').write_bytes(b'INVENTED, NOT EXECUTABLE')
        self.study = self.root / 'experimental/example/ETUDE.md'
        self.study.parent.mkdir(parents=True)
        self.study.write_text('Invented study.', encoding='utf-8')
        self.profile, self.files = fixture()
        for name in ('tree.klz', 'scene.4ds', 'scene2.bin'):
            self.files[f'missions/example/{name}'] = ('missions.dta', b'INVENTED ' + name.encode())
        self.sources = LabSources(self.files)
        self.labs = self.root / '.analysis/labs'
        self.labs.mkdir(parents=True)
        self.scenes = self.root / '.analysis/scenes'
        self.scenes.mkdir()
        self.bundle = self.labs / (self.profile['id'] + '.lab.zip.disabled')
        members, _ = plan_lab(self.profile, self.sources)
        write_bundle(self.bundle, members, self.game, root=self.root)
        self.catalog = {self.profile['id']: self.profile}
        self.expected = {self.profile['id']: {'kind': 'script', 'mission': 'example',
                                             'definition_sha256': fingerprint(self.profile)}}
        self.entry = {'id': self.profile['id'], **self.expected[self.profile['id']],
                      'title': 'Invented trial', 'study': 'experimental/example/ETUDE.md',
                      'mode': 'solo', 'prerequisites': ['Use an isolated copy'],
                      'steps': ['Observe baseline', 'Compare behavior'],
                      'results': {s: {'state': 'pending', 'evidence': None} for s in SCENARIOS}}
        self.register = {'schema_version': 1, 'scope': 'experimental-reconstruction',
                         'default_profile': 'commercial', 'profiles': [self.entry],
                         'common_scenarios': {s: 'Invented instructions' for s in SCENARIOS | {'network'}}}
        self.output = self.root / '.analysis/reconstruction-trials/fixture'

    def collect(self):
        return trials.collect(self.root, self.game, self.labs, self.scenes, self.sources,
                              self.catalog, self.register, self.expected)

    def test_prepare_is_read_only_and_keeps_all_runtime_gates_closed(self):
        before = copy.deepcopy(self.register)
        report = self.collect()
        self.assertEqual(report['preparation_counts'], {'source_verified_inert_lab': 1})
        self.assertEqual(report['recorded_result_counts'], {'pending': 6})
        for flag in ('game_launched', 'installer_launched', 'payloads_activated',
                     'installed_into_game', 'runtime_register_modified', 'automatic_activation_authorized'):
            self.assertFalse(report[flag])
        self.assertEqual(report['profiles'][0]['deployment_status'], 'not_prepared')
        self.assertEqual(self.register, before)
        self.assertFalse(self.output.exists())

    def test_fresh_documents_roundtrip_without_commercial_payload(self):
        files = trials.documents(self.collect())
        trials.persist(self.output, files, self.root, self.game)
        trials.persist(self.output, files, self.root, self.game, check=True)
        self.assertEqual({p.suffix for p in self.output.iterdir()}, {'.md', '.json'})
        self.assertEqual(len(files), 4)
        self.assertNotIn(b'// invented fixture', b''.join(files.values()))
        self.assertIn(b'Retour arri', files['example-variant.md'])

    def test_existing_output_is_refused_without_overwrite(self):
        files = trials.documents(self.collect())
        trials.persist(self.output, files, self.root, self.game)
        marker = self.output / 'user-notes.md'
        marker.write_bytes(b'preserve me')
        with self.assertRaises(FileExistsError):
            trials.persist(self.output, files, self.root, self.game)
        self.assertEqual(marker.read_bytes(), b'preserve me')

    def test_study_or_executable_change_invalidates_prepared_pack(self):
        files = trials.documents(self.collect())
        trials.persist(self.output, files, self.root, self.game)
        self.study.write_text('Different instructions.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'differs from current'):
            trials.persist(self.output, trials.documents(self.collect()), self.root, self.game, check=True)
        self.study.write_text('Invented study.', encoding='utf-8')
        (self.game / 'HD2_SabreSquadron.exe').write_bytes(b'CHANGED INVENTED EXE')
        with self.assertRaisesRegex(ValueError, 'differs from current'):
            trials.persist(self.output, trials.documents(self.collect()), self.root, self.game, check=True)

    def test_modified_missing_and_extra_documents_are_refused(self):
        files = trials.documents(self.collect())
        trials.persist(self.output, files, self.root, self.game)
        path = self.output / 'example-variant.md'
        path.write_bytes(b'modified')
        with self.assertRaises(ValueError):
            trials.persist(self.output, files, self.root, self.game, check=True)
        path.unlink()
        with self.assertRaises(ValueError):
            trials.persist(self.output, files, self.root, self.game, check=True)
        path.write_bytes(files[path.name])
        (self.output / 'unexpected.md').write_bytes(b'extra')
        with self.assertRaises(ValueError):
            trials.persist(self.output, files, self.root, self.game, check=True)

    def test_outputs_outside_designated_area_and_inside_game_refused(self):
        for path in (self.root, self.game / 'trials', self.root / '.analysis/reconstruction-trials',
                     self.root / '.analysis/reconstruction-trials/nested/fixture'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                trials.safe_output(path, self.root, self.game)
        with self.assertRaises(ValueError):
            trials.safe_output(self.output, self.root, self.root / '.analysis')

    def test_output_symlink_rejected(self):
        other = self.root / 'elsewhere'
        other.mkdir()
        self.output.parent.mkdir(parents=True)
        try:
            self.output.symlink_to(other, target_is_directory=True)
        except OSError:
            self.skipTest('Host does not allow unprivileged symlinks')
        with self.assertRaises(ValueError):
            trials.safe_output(self.output, self.root, self.game)

    def test_metadata_path_traversal_and_payload_extensions_rejected(self):
        for name in ('../escape.md', 'C:escape.json', 'nested/escape.md', 'script.scr'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                trials.persist(self.output, {name: b'x'}, self.root, self.game)
        self.assertFalse(self.output.exists())

    def test_duplicate_bundles_refused_instead_of_picking_latest(self):
        duplicate = self.labs / 'another' / self.bundle.name
        duplicate.parent.mkdir()
        duplicate.write_bytes(self.bundle.read_bytes())
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            self.collect()

    def test_missing_lab_is_not_mistaken_for_missing_dependency(self):
        self.bundle.unlink()
        report = self.collect()
        row = report['profiles'][0]
        self.assertEqual(row['preparation_status'], 'complete_lab_bundle_missing')
        self.assertIsNone(row['payload_evidence'])
        self.assertIsNone(row['bundle'])

    def test_only_a_verified_missing_script_is_reported_as_a_dependency_obstacle(self):
        self.bundle.unlink()
        with patch.object(trials, 'plan_lab', side_effect=ValueError('Missing script dependencies: absent.scr')):
            row = self.collect()['profiles'][0]
        self.assertEqual(row['preparation_status'], 'missing_script_dependencies')
        self.assertIn('absent.scr', row['preparation_obstacles'][0])
        self.assertEqual(row['script_variant_proof']['static_status'], 'passed')
        with patch.object(trials, 'plan_lab', side_effect=ValueError('Source changed')):
            with self.assertRaisesRegex(ValueError, 'Source changed'):
                self.collect()

    def test_stale_register_and_corrupt_bundle_abort_preparation(self):
        self.entry['definition_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Invalid runtime register'):
            self.collect()
        self.entry['definition_sha256'] = self.expected[self.profile['id']]['definition_sha256']
        self.bundle.write_bytes(b'not a zip')
        with self.assertRaises(trials.zipfile.BadZipFile):
            self.collect()
        self.assertFalse(self.output.exists())

    def test_conflicts_are_derived_from_all_atomic_changes(self):
        first, second, third = (copy.deepcopy(self.profile) for _ in range(3))
        first['id'], second['id'], third['id'] = 'first', 'second', 'third'
        second['source'], second['actor'] = 'scripts/example/other.scr', 'Other'
        second['additional_changes'] = [{k: third[k] for k in ('source', 'actor', 'edits')}]
        third['source'], third['actor'] = 'scripts/example/independent.scr', 'Independent'
        self.assertEqual(trials.conflicts({p['id']: p for p in (first, second, third)}),
                         {'first': ['second'], 'second': ['first'], 'third': []})

    def test_scene_cards_keep_network_and_incomplete_deployment_visible(self):
        scene_id = 'co-burgundy3-ambience'
        self.entry.update(id=scene_id, kind='scene_registry', mode='cooperation', mission='co_burgundy3')
        self.entry['results']['network'] = {'state': 'pending', 'evidence': None}
        self.expected = {scene_id: {k: self.entry[k] for k in ('kind', 'mission', 'definition_sha256')}}
        with self.assertRaisesRegex(ValueError, 'Missing scene comparison'):
            self.collect()
        (self.scenes / (scene_id + '.scene-patch.zip.disabled')).write_bytes(b'invented comparison')
        with patch.object(trials, 'inspect_scene', return_value={'synthetic': True}):
            report = self.collect()
        row = report['profiles'][0]
        self.assertEqual(row['preparation_status'], 'source_verified_inert_scene_comparison')
        self.assertEqual(row['scenarios'][-1]['id'], 'network')
        self.assertEqual(row['deployment_status'], 'not_prepared')
        self.assertTrue(row['preparation_obstacles'])


if __name__ == '__main__':
    unittest.main()
