"""Filesystem isolation tests with invented files; never a game launch."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import reconstruction_sandbox as sandbox


class SandboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        for name in ('HD2_SabreSquadron.exe', 'SabreSquadron.dta', 'missions.dta', 'Scripts.dta'):
            (self.source / name).write_bytes(b'INVENTED NOT EXECUTABLE: ' + name.encode())
        personal = self.source / 'PlayersProfiles/test/save.sav'
        personal.parent.mkdir(parents=True)
        personal.write_bytes(b'invented saved progress')
        self.session = self.root / '.analysis/reconstruction-sandboxes/fixture'
        self.addCleanup(patch.stopall)
        patch.object(sandbox, 'idle_game').start()

    def clone(self):
        return sandbox.clone(self.source, self.session, root=self.root, build=True)

    def test_readonly_plan_writes_nothing(self):
        result = sandbox.clone(self.source, self.session, root=self.root)
        self.assertEqual(result['files'], 5)
        self.assertEqual(result['status'], 'read_only_plan')
        self.assertFalse(self.session.exists())

    def test_independent_copy_preserves_source_and_saved_progress(self):
        result = self.clone()
        self.assertEqual(result['status'], 'independent_copy_verified')
        self.assertFalse(result['game_launched'])
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])
        name = 'PlayersProfiles/test/save.sav'
        copied = self.session / 'game' / name
        self.assertFalse(copied.samefile(self.source / name))
        copied.write_bytes(b'changed only in test copy')
        self.assertEqual((self.source / name).read_bytes(), b'invented saved progress')
        self.assertEqual(sandbox.verify(self.session, root=self.root)['changed'], [name])

    def test_hardlinked_source_becomes_independent_destination(self):
        original = self.source / 'SabreSquadron.dta'
        os.link(original, self.root / 'external-archive-link')
        self.clone()
        copied = self.session / 'game/SabreSquadron.dta'
        self.assertEqual(copied.stat().st_nlink, 1)
        self.assertFalse(copied.samefile(original))

    def test_new_hardlink_in_destination_is_refused(self):
        self.clone()
        os.link(self.session / 'game/SabreSquadron.dta', self.root / 'shared-copy')
        with self.assertRaisesRegex(ValueError, 'hard-linked'):
            sandbox.verify(self.session, root=self.root)

    def test_existing_session_is_never_replaced(self):
        self.clone()
        with self.assertRaises(FileExistsError):
            self.clone()
        self.assertTrue(sandbox.verify(self.session, root=self.root)['ok'])

    def test_unrelated_output_and_source_overlap_refused(self):
        for target in (self.source, self.root, self.root / '.analysis/elsewhere'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                sandbox.clone(self.source, target, root=self.root, build=True)
        with self.assertRaises(ValueError):
            sandbox.clone(self.root, self.session, root=self.root, build=True)

    def test_case_resolution_and_path_validation(self):
        folder = self.source / 'Missions/Example'
        folder.mkdir(parents=True)
        (folder / 'File.scr').write_bytes(b'fixture')
        self.assertEqual(sandbox.destination(self.source, 'missions/example/file.scr'), folder / 'File.scr')
        for name in ('../x', '/x', 'C:/x', 'x\\y', 'x/../y', 'x/con.txt', 'x/trailing.', 'x//y'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                sandbox.destination(self.source, name)

    def test_changed_source_prevents_ready_marker(self):
        original = sandbox.tree
        calls = 0
        def unstable(*args, **kwargs):
            nonlocal calls
            calls += 1
            result = original(*args, **kwargs)
            if calls == 2:
                result['Scripts.dta']['mtime_ns'] += 1
            return result
        with patch.object(sandbox, 'tree', side_effect=unstable):
            with self.assertRaisesRegex(ValueError, 'Source changed during'):
                self.clone()
        self.assertFalse((self.session / 'READY.json').exists())

    def test_running_game_refused_before_copy(self):
        with patch.object(sandbox, 'idle_game', side_effect=ValueError('Close all HD2')):
            with self.assertRaisesRegex(ValueError, 'Close all'):
                self.clone()
        self.assertFalse(self.session.exists())

    def test_manifest_tampering_or_active_experiment_refused(self):
        self.clone()
        (self.session / 'active.json').write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Restore the active'):
            sandbox.verify(self.session, root=self.root)
        (self.session / 'active.json').unlink()
        manifest = self.session / 'clone-manifest.json'
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['files'][0]['size'] += 1
        manifest.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'identity or manifest'):
            sandbox.load_session(self.session, self.root)

    def test_only_one_mutating_operation_at_a_time(self):
        self.clone()
        with sandbox.operation(self.session):
            with self.assertRaises(FileExistsError):
                with sandbox.operation(self.session):
                    self.fail('Second operation must never start')
        self.assertFalse((self.session / '.operation.lock').exists())


if __name__ == '__main__':
    unittest.main()
