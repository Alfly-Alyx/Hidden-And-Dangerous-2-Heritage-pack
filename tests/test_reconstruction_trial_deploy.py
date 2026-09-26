"""Native mission deployment/rollback with fabricated bytes, never HD2 execution."""
import copy
from contextlib import ExitStack, nullcontext
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import reconstruction_sandbox as sandbox
import reconstruction_trial_deploy as deploy
from reconstruction_runtime_audit import fingerprint
from test_reconstruction_labs import LabSources
from test_reconstruction_variants import fixture


class NativeTrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'personal-game'
        self.source.mkdir()
        for name in ('HD2_SabreSquadron.exe', 'SabreSquadron.dta', 'missions.dta', 'Scripts.dta'):
            (self.source / name).write_bytes(b'INVENTED, NOT EXECUTABLE: ' + name.encode())
        self.original_script = self.source / 'Scripts/example/source.scr'
        self.original_script.parent.mkdir(parents=True)
        self.original_script.write_bytes(b'Original user override - must survive')
        (self.original_script.parent / 'legacy-missing.scr').write_bytes(b'Installed extra, not in archives')
        self.session = self.root / '.analysis/reconstruction-sandboxes/fixture'
        self.addCleanup(patch.stopall)
        patch.object(sandbox, 'idle_game').start()
        patch.object(deploy, 'idle_game').start()
        sandbox.clone(self.source, self.session, root=self.root, build=True)
        self.profile, self.files = fixture()
        for name in ('tree.klz', 'scene.4ds', 'scene2.bin'):
            self.files[f'missions/example/{name}'] = ('missions.dta', b'INVENTED ' + name.encode())
        self.sources = LabSources(self.files)
        self.sources.excluded_loose_overrides = {}
        self.runtime = {'test_plan_sha256': {self.profile['id']: 'a' * 64}}
        snapshots, self.preset = deploy.native_plan(self.profile['id'],
            {self.profile['id']: self.profile}, self.sources, self.runtime)
        for snapshot in snapshots.values():
            for raw in snapshot.values():
                deploy.put_blob(self.session, raw)
        self.preset['environment_sha256'] = sandbox.load_session(self.session, self.root)[1]['manifest_sha256']
        self.persist_preset()

    def persist_preset(self):
        folder = self.session / 'presets'
        folder.mkdir(exist_ok=True)
        (folder / (self.profile['id'] + '.json')).write_bytes(sandbox.json_data(self.preset))
        (self.session / 'PRESETS.json').write_bytes(sandbox.json_data({
            'profiles': [{'profile': self.profile['id'], 'sha256': fingerprint(self.preset)}]}))

    def extension_context(self):
        index_path = self.session / 'PRESETS.json'
        index = json.loads(index_path.read_text())
        index.update(schema_version=1, kind='native_trial_presets', game_launched=False,
                     environment_sha256=self.preset['environment_sha256'])
        index_path.write_bytes(sandbox.json_data(index))
        second = {**copy.deepcopy(self.profile), 'id': 'example-second'}
        catalog = {self.profile['id']: self.profile, second['id']: second}
        expected = {key: {'definition_sha256': fingerprint(value)} for key, value in catalog.items()}
        runtime = {'ok': True, 'test_plan_sha256': {key: 'a' * 64 for key in catalog}}
        context = ExitStack()
        context.enter_context(patch.object(deploy, 'supported_client'))
        context.enter_context(patch.object(deploy, 'audit', return_value=runtime))
        context.enter_context(patch.object(deploy, 'definitions', return_value=expected))
        context.enter_context(patch.object(deploy, 'load_catalog', return_value=catalog))
        context.enter_context(patch.object(deploy, 'ArchiveSources', side_effect=lambda *a, **kw: nullcontext(self.sources)))
        return context, runtime

    def test_extension_preserves_old_preset_game_and_recovery_index(self):
        context, _ = self.extension_context()
        old_bytes = (self.session / 'presets' / (self.profile['id'] + '.json')).read_bytes()
        old_index = (self.session / 'PRESETS.json').read_bytes()
        with context:
            report = deploy.extend_all(self.session, root=self.root)
            self.assertEqual(report['added'], ['example-second'])
            self.assertEqual(deploy.extend_all(self.session, root=self.root)['added'], [])
        self.assertEqual((self.session / 'presets' / (self.profile['id'] + '.json')).read_bytes(), old_bytes)
        self.assertEqual(next((self.session / 'preset-history').iterdir()).read_bytes(), old_index)
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])
        self.assertEqual(deploy.load_preset(self.session, 'example-second')['profile'], 'example-second')

    def test_extension_refuses_changed_existing_protocol(self):
        context, runtime = self.extension_context()
        old_index = (self.session / 'PRESETS.json').read_bytes()
        runtime['test_plan_sha256'][self.profile['id']] = 'b' * 64
        with context, self.assertRaisesRegex(ValueError, 'protocol changed'):
            deploy.extend_all(self.session, root=self.root)
        self.assertEqual((self.session / 'PRESETS.json').read_bytes(), old_index)
        self.assertFalse((self.session / 'presets/example-second.json').exists())

    def test_interrupted_extension_preserves_index_and_resumes_identical_presets(self):
        context, _ = self.extension_context()
        old_index = (self.session / 'PRESETS.json').read_bytes()
        with context:
            with patch.object(deploy, 'atomic_json', side_effect=OSError('invented interruption')):
                with self.assertRaises(OSError):
                    deploy.extend_all(self.session, root=self.root)
            self.assertEqual((self.session / 'PRESETS.json').read_bytes(), old_index)
            report = deploy.extend_all(self.session, root=self.root)
            self.assertEqual(report['added'], ['example-second'])
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])

    def test_extension_refuses_active_trial_without_changing_files(self):
        context, _ = self.extension_context()
        with context:
            self.apply()
            with self.assertRaisesRegex(ValueError, 'active trial'):
                deploy.extend_all(self.session, root=self.root)
        self.assertEqual(deploy.status(self.session, root=self.root)['modified_targets'], [])

    def test_selected_rehearsal_requires_safe_separate_report_name(self):
        for options in ({'profiles': [self.profile['id']]}, {'report_name': '../escape'}):
            with self.assertRaises(ValueError):
                deploy.rehearse(self.session, root=self.root, **options)

    def test_apply_rechecks_dialogue_assets_before_any_game_write(self):
        raw = b'INVENTED AUDIO'
        self.preset['asset_evidence'] = [{'path': 'sounds/12345678.wav', 'archive': 'LangEnglish.dta',
                                         'size': len(raw), 'sha256': fingerprint({'not': 'actual bytes'})}]
        self.persist_preset()
        self.sources.read_asset = lambda *args: raw
        with patch.object(deploy, 'ArchiveSources', side_effect=lambda *a, **kw: nullcontext(self.sources)):
            with self.assertRaisesRegex(ValueError, 'asset changed before application'):
                self.apply()
        self.assertFalse((self.session / 'active.json').exists())
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])

    def apply(self, mode='variant'):
        return deploy.apply(self.session, self.profile['id'], mode, root=self.root)

    def test_native_paths_and_only_approved_script_changes(self):
        rows = self.preset['payloads']['baseline']['files']
        self.assertTrue(all(r['path'].split('/')[1] == 'example' for r in rows))
        self.assertEqual(self.preset['changed_entries'], ['scripts/example/source.scr'])
        self.assertFalse(self.preset['variant_requires_observed_baseline'])
        self.assertFalse(self.preset['game_launched'])

    def test_apply_and_restore_preserve_source_and_original_override(self):
        result = self.apply()
        self.assertEqual(result['status'], 'applied_not_run')
        target = self.session / 'game/Scripts/example/source.scr'
        self.assertIn(b'\r\nMove("P1");', target.read_bytes())
        self.assertEqual(self.original_script.read_bytes(), b'Original user override - must survive')
        self.assertEqual(deploy.status(self.session, root=self.root)['modified_targets'], [])
        report = deploy.restore(self.session, root=self.root)
        self.assertEqual(report['status'], 'restored')
        self.assertGreater(report['retired_files'], 0)
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])
        self.assertTrue((self.session / 'retired').is_dir())
        self.assertFalse((self.session / 'active.json').exists())

    def test_baseline_and_variant_can_be_repeated_with_restoration_between(self):
        for mode in ('baseline', 'variant', 'baseline'):
            self.apply(mode)
            deploy.restore(self.session, root=self.root)
            self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])
        self.assertEqual(len(list((self.session / 'history').glob('*.json'))), 3)

    def test_second_experiment_is_refused_until_restored(self):
        self.apply('baseline')
        with self.assertRaisesRegex(ValueError, 'Restore the current'):
            self.apply('variant')

    def test_later_edit_blocks_restore_without_overwriting_any_file(self):
        self.apply()
        edited = self.session / 'game/Scripts/example/source.scr'
        edited.write_bytes(b'User edited after deployment')
        before = {p['path']: deploy.current_proof(self.session, p['path'])
                  for p in self.preset['payloads']['variant']['files']}
        with self.assertRaisesRegex(ValueError, 'Later edits preserved'):
            deploy.restore(self.session, root=self.root)
        self.assertEqual(edited.read_bytes(), b'User edited after deployment')
        self.assertEqual(before, {name: deploy.current_proof(self.session, name) for name in before})
        self.assertTrue((self.session / 'active.json').exists())

    def test_user_deletion_of_preexisting_file_is_preserved(self):
        self.apply()
        (self.session / 'game/Scripts/example/source.scr').unlink()
        with self.assertRaisesRegex(ValueError, 'Later edits preserved'):
            deploy.restore(self.session, root=self.root)

    def test_interrupted_apply_is_recovered_to_original_bytes(self):
        replace = deploy.replace_payload
        count = 0
        def interrupted(*args):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError('Simulated write interruption')
            return replace(*args)
        with patch.object(deploy, 'replace_payload', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'Simulated'):
                self.apply()
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])

    def test_recovery_handles_mixed_already_restored_and_installed_files(self):
        self.apply()
        journal = json.loads((self.session / 'active.json').read_text(encoding='utf-8'))
        item = next(i for i in journal['files'] if i['before'] is not None)
        deploy.replace_payload(self.session, item['path'], item['before'])
        deploy.restore(self.session, root=self.root)
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])

    def test_missing_backup_or_corrupt_payload_aborts_before_changes(self):
        self.apply()
        journal = json.loads((self.session / 'active.json').read_text(encoding='utf-8'))
        proof = next(i['before'] for i in journal['files'] if i['before'] is not None)
        (self.session / 'objects' / (proof['sha256'] + '.disabled')).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            deploy.restore(self.session, root=self.root)

    def test_frozen_archive_change_refused_before_overlay(self):
        (self.session / 'game/SabreSquadron.dta').write_bytes(b'changed archive')
        with self.assertRaisesRegex(ValueError, 'Frozen game'):
            self.apply()
        self.assertFalse((self.session / 'active.json').exists())

    def test_shared_target_or_shared_control_file_refused(self):
        target = self.session / 'game/Scripts/example/source.scr'
        os.link(target, self.root / 'shared-target')
        with self.assertRaisesRegex(ValueError, 'hard-linked'):
            self.apply()
        (self.root / 'shared-target').unlink()
        os.link(self.session / 'PRESETS.json', self.root / 'shared-control')
        with self.assertRaisesRegex(ValueError, 'hard-linked'):
            self.apply()

    def test_tampered_preset_path_cannot_escape_mission_or_sandbox(self):
        row = self.preset['payloads']['variant']['files'][0]
        for name in ('../escape', 'Missions/elsewhere/file.scr', 'PlayersProfiles/test/save.sav'):
            with self.subTest(name=name):
                row['path'] = name
                self.persist_preset()
                with self.assertRaises(ValueError):
                    self.apply()
        self.assertFalse((self.session / 'active.json').exists())

    def test_present_and_absent_cannot_target_the_same_file(self):
        self.preset['required_absent'] = ['Scripts/example/source.scr']
        self.persist_preset()
        with self.assertRaisesRegex(ValueError, 'both required and absent'):
            self.apply('baseline')

    def test_loose_replacement_is_preserved_outside_game_then_restored(self):
        name = 'Scripts/example/legacy-missing.scr'
        self.preset['required_absent'] = [name]
        self.persist_preset()
        self.apply('baseline')
        self.assertFalse((self.session / 'game' / name).exists())
        self.assertEqual((self.source / name).read_bytes(), b'Installed extra, not in archives')
        self.assertEqual(deploy.status(self.session, root=self.root)['preserved_commercial_absences'], [name])
        self.assertEqual(len(list((self.session / 'retired').rglob('legacy-missing.scr.disabled'))), 1)
        deploy.restore(self.session, root=self.root)
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])

    def test_africa5_gate_requires_real_evidence_not_a_flag(self):
        self.preset['variant_requires_observed_baseline'] = True
        self.persist_preset()
        register = self.root / 'validation/reconstruction-runtime.json'
        register.parent.mkdir()
        register.write_text(json.dumps({'profiles': [{
            'id': self.profile['id'], 'results': {'baseline': {'state': 'pending', 'evidence': None}}
        }]}), encoding='utf-8')
        with patch.object(deploy, 'audit', return_value={'ok': True}):
            with self.assertRaisesRegex(ValueError, 'real, evidenced'):
                self.apply('variant')
        self.apply('baseline')
        deploy.restore(self.session, root=self.root)
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])

    def test_unreviewed_missing_dependency_is_never_waived(self):
        with patch.object(deploy, 'script_closure', side_effect=ValueError(
                'Missing script dependencies: other.scr')):
            with self.assertRaises(ValueError):
                deploy.closure({}, 'africa5', 'scripts.dta')
        with patch.object(deploy, 'script_closure', side_effect=ValueError(
                'Missing script dependencies: ' + deploy.AFRICA5_MISSING)):
            with self.assertRaises(ValueError):
                deploy.closure({'missions/africa5/scripts.dta': b'wrong registry'}, 'africa5', 'scripts.dta')

    def test_changed_recipe_or_protocol_refused(self):
        expected = {self.profile['id']: {'definition_sha256': '0' * 64}}
        with self.assertRaisesRegex(ValueError, 'Recipe changed'):
            deploy.apply(self.session, self.profile['id'], 'baseline', root=self.root, expected=expected)
        expected[self.profile['id']]['definition_sha256'] = self.preset['definition_sha256']
        with patch.object(deploy, 'audit', return_value={'ok': True,
                'test_plan_sha256': {self.profile['id']: 'b' * 64}}):
            with self.assertRaisesRegex(ValueError, 'protocol changed'):
                deploy.apply(self.session, self.profile['id'], 'baseline', root=self.root, expected=expected)

    def test_resume_only_accepts_identical_recomputed_metadata(self):
        path = self.root / 'partial.json'
        deploy.save_preset(path, self.preset)
        deploy.save_preset(path, self.preset, resume=True)
        with self.assertRaises(FileExistsError):
            deploy.save_preset(path, self.preset)
        changed = {**self.preset, 'mission': 'different'}
        with self.assertRaisesRegex(ValueError, 'not overwritten'):
            deploy.save_preset(path, changed, resume=True)
        self.assertEqual(path.read_bytes(), sandbox.json_data(self.preset))

    def test_native_client_version_is_pinned(self):
        with self.assertRaisesRegex(ValueError, 'verified original'):
            deploy.supported_client(self.session)
        with patch.object(deploy, 'file_hash', return_value=deploy.SUPPORTED_CLIENT_SHA):
            deploy.supported_client(self.session)

    def test_native_missing_contract_is_exact_and_still_requires_engine_observation(self):
        registry, expected_sha, missing = deploy.NATIVE_MISSING['co_burgundy1']
        error = ValueError('Missing script dependencies: ' + ', '.join(missing))
        with patch.object(deploy, 'script_closure', side_effect=error), \
                patch.object(deploy, 'digest', return_value=expected_sha):
            result = deploy.closure({'missions/co_burgundy1/mpscripts.dta': b'invented'},
                                    'co_burgundy1', registry)
        self.assertEqual(result['missing_scripts'], missing)
        self.assertFalse(result['complete_lab'])
        self.assertEqual(result['runtime_resolution'], 'original_baseline_must_be_observed')
        with patch.object(deploy, 'script_closure', side_effect=ValueError(
                'Missing script dependencies: ' + ', '.join(missing + ['new.scr']))):
            with self.assertRaises(ValueError):
                deploy.closure({'missions/co_burgundy1/mpscripts.dta': b'invented'},
                               'co_burgundy1', registry)


if __name__ == '__main__':
    unittest.main()
