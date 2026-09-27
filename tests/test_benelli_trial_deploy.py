"""Actual file transactions on invented independent copies, never HD2 execution."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import benelli_trial_deploy as deploy
import benelli_trial_payload as payload
import reconstruction_sandbox as sandbox
import reconstruction_trial_deploy as missions
from test_benelli_trial_payload import fixture


class BenelliDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'personal-game';self.source.mkdir()
        self.files,self.manifest,self.before,pins=fixture();self.lab=self.root/'disabled-lab';self.lab.mkdir()
        for name,raw in self.files.items():
            path=self.lab/name;path.parent.mkdir(parents=True,exist_ok=True);sandbox.write_new(path,raw)
        sandbox.write_new(self.lab/'MANIFEST.json',json.dumps(self.manifest).encode())
        for name in ('HD2_SabreSquadron.exe','SabreSquadron.dta','missions.dta','Scripts.dta','PrivateSave.bin'):
            sandbox.write_new(self.source/name,b'INVENTED NOT EXECUTABLE '+name.encode())
        for name,raw in self.before.items():
            if raw is None:continue
            path=self.source/name;path.parent.mkdir(parents=True,exist_ok=True);sandbox.write_new(path,raw)
        for context in (patch.object(payload,'MODEL_PINS',pins),patch.object(sandbox,'idle_game'),
                        patch.object(deploy,'idle_game'),patch.object(missions,'idle_game'),
                        patch.object(deploy,'supported_client'),
                        patch.object(deploy,'asset_audit',return_value={'no_candidate_collisions':True,'invented_sources':1})):
            context.start();self.addCleanup(context.stop)
        self.session=self.root/'.analysis/reconstruction-sandboxes/benelli-fixture'
        sandbox.clone(self.source,self.session,root=self.root,build=True)

    def prepare(self):return deploy.prepare(self.session,self.lab,root=self.root)
    def apply(self):return deploy.apply(self.session,root=self.root)
    def restore(self):return deploy.restore(self.session,root=self.root)
    def verified(self):return sandbox.verify(self.session,root=self.root)['ok']

    def test_preparation_is_inert_and_apply_restore_recovers_every_original_file(self):
        result=self.prepare();self.assertEqual(result['files'],12);self.assertTrue(self.verified())
        self.assertFalse((self.session/'active.json').exists())
        self.assertEqual(self.apply()['status'],'applied_not_run')
        for name,raw in self.files.items():
            target=payload.target_map(self.files).get(name)
            if target:self.assertEqual((self.session/'game'/target).read_bytes(),raw)
        self.assertEqual((self.source/'Tables/items.sav').read_bytes(),self.before['Tables/items.sav'])
        restored=self.restore();self.assertEqual(len(restored['retired_files']),2)
        self.assertTrue(self.verified());self.assertFalse((self.session/'active.json').exists())
        self.assertEqual(len(list((self.session/'retired').rglob('*.disabled'))),2)
        self.assertFalse((self.session/'game/Models').exists())

    def test_rehearsal_records_zero_runtime_tests_and_never_overwrites_its_report(self):
        self.prepare();result=deploy.rehearse(self.session,root=self.root)
        self.assertTrue(result['initial_copy_restored']);self.assertEqual(result['runtime_tests_performed'],0)
        self.assertFalse(result['game_launched']);self.assertTrue(self.verified())
        with self.assertRaises(FileExistsError):deploy.rehearse(self.session,root=self.root)

    def test_personal_installation_cannot_be_used_as_a_session(self):
        with self.assertRaisesRegex(ValueError,'Session must'):
            deploy.prepare(self.source,self.lab,root=self.root)
        self.assertFalse((self.source/deploy.PRESET).exists())

    def test_single_active_marker_blocks_both_benelli_and_mission_operations(self):
        self.prepare();self.apply()
        with self.assertRaisesRegex(ValueError,'active experiment'):self.apply()
        with self.assertRaisesRegex(ValueError,'active experiment'):self.prepare()
        with self.assertRaisesRegex(ValueError,'current experiment'):
            missions.apply(self.session,'invented','baseline',root=self.root)
        self.restore();self.assertTrue(self.verified())

    def test_changed_target_or_frozen_archive_refuses_before_any_activation(self):
        self.prepare();target=self.session/'game/Tables/items.sav';old=target.read_bytes()
        target.write_bytes(old+b'later edit')
        with self.assertRaisesRegex(ValueError,'target changed'):self.apply()
        self.assertFalse((self.session/'active.json').exists());self.assertEqual(target.read_bytes(),old+b'later edit')
        target.write_bytes(old)
        archive=self.session/'game/SabreSquadron.dta';archive.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Frozen'):self.apply()
        self.assertFalse((self.session/'active.json').exists())

    def test_new_asset_provider_refuses_before_any_activation(self):
        self.prepare()
        with patch.object(deploy,'asset_audit',return_value={'no_candidate_collisions':True,'invented_sources':2}):
            with self.assertRaisesRegex(ValueError,'Asset environment'):self.apply()
        self.assertTrue(self.verified());self.assertFalse((self.session/'active.json').exists())

    def test_interrupted_application_restores_partial_model_without_deleting_its_recoverable_copy(self):
        self.prepare();original=deploy.replace_file;calls=[]
        def interrupted(*args):
            calls.append(args[1])
            if len(calls)==2:raise OSError('invented interrupted second write')
            return original(*args)
        with patch.object(deploy,'replace_file',side_effect=interrupted):
            with self.assertRaisesRegex(OSError,'interrupted'):self.apply()
        self.assertTrue(self.verified());self.assertFalse((self.session/'active.json').exists())
        self.assertEqual(len(list((self.session/'retired').rglob('*.disabled'))),1)

    def test_later_edit_refuses_all_restoration_until_user_content_is_accounted_for(self):
        self.prepare();self.apply();path=self.session/'game/Text/french/TEXTY_DD.txt';after=path.read_bytes()
        path.write_bytes(after+b'later user edit')
        with self.assertRaisesRegex(ValueError,'Later edit preserved'):self.restore()
        self.assertEqual(path.read_bytes(),after+b'later user edit')
        self.assertTrue((self.session/'game/Models/PROTOTYPE_BenFPV.4ds').exists())
        self.assertTrue((self.session/'active.json').exists())
        path.write_bytes(after);self.restore();self.assertTrue(self.verified())

    def test_missing_original_backup_refuses_restoration_before_touching_any_target(self):
        self.prepare();self.apply()
        preset=json.loads((self.session/deploy.PRESET).read_text())
        original=next(row['before'] for row in preset['plan']['files'] if row['before'] is not None)
        backup=self.session/'objects'/(original['sha256']+'.disabled');backup.write_bytes(b'corrupted fixture backup')
        with self.assertRaisesRegex(ValueError,'Stored payload/backup'):self.restore()
        self.assertTrue((self.session/'active.json').exists())
        self.assertTrue((self.session/'game/Models/PROTOTYPE_BenFPV.4ds').exists())

    def test_altered_journal_paths_and_directory_cleanup_cannot_escape_trial_targets(self):
        self.prepare();self.apply();journal_path=self.session/'active.json';original=journal_path.read_bytes()
        for key,value in (('created_directories',['../escape']),('kind','native_trial_transaction'),('files',[])):
            journal=json.loads(original);journal[key]=value;journal_path.write_bytes(sandbox.json_data(journal))
            with self.subTest(key=key),self.assertRaises(ValueError):self.restore()
            self.assertTrue((self.session/'game/Models/PROTOTYPE_BenFPV.4ds').exists())
        journal_path.write_bytes(original);self.restore();self.assertTrue(self.verified())

    def test_changed_preset_and_duplicate_preparation_are_not_silently_accepted(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError,'already exists'):self.prepare()
        path=self.session/deploy.PRESET;data=json.loads(path.read_text())
        data['plan']['files'][0]['after']['size']+=1;path.write_bytes(sandbox.json_data(data))
        with self.assertRaisesRegex(ValueError,'plan no longer matches'):self.apply()
        self.assertFalse((self.session/'active.json').exists());self.assertTrue(self.verified())


if __name__=='__main__':unittest.main()
