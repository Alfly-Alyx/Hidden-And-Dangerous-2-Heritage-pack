"""Synthetic scene/registry fixtures only; no commercial game required."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_burgundy_ambient_patch import (
    MEMBERS, RECIPES, append_bindings, append_owners, check_script_pair, record_name, registry_pairs,
    scene_group, write_comparison,
)
from build_reconstruction_variant import digest


def block(kind, payload):
    return struct.pack('<HI', kind, len(payload) + 6) + payload


def string(kind, value):
    return block(kind, value.encode('ascii') + b'\0')


def dummy(name, kind=6, parent='Primary sector', world=1.25, local=1.25):
    return block(0x4010, b''.join([
        block(0x4011, struct.pack('<I', kind)), string(0x10, name),
        block(0x20, struct.pack('<3f', local, 2.5, -3.75)),
        block(0x22, struct.pack('<4f', 1, 0, 0, 0)),
        block(0x2D, struct.pack('<3f', 1, 1, 1)),
        block(0x2C, struct.pack('<3f', world, 2.5, -3.75)),
        block(0x4020, string(0x10, parent)),
        block(0x4050, struct.pack('<6f', -.5, -.5, -.5, .5, .5, .5)),
    ]))


def scene(records):
    return block(0x4C53, block(0x3001, b'prefix') + block(0x4000, b''.join(records))
                 + block(0xAE20, b'untouched-tail'))


def registry(pairs):
    return block(0, b''.join(string(1, owner) + string(1, script) for owner, script in pairs))


class AmbientSceneTests(unittest.TestCase):
    def setUp(self):
        self.owners = {'bird_a': 'bird.scr', 'bird_b': 'door.scr'}
        self.solo = scene([dummy('bird_b'), dummy('unrelated'), dummy('bird_a')])
        self.coop = scene([dummy('existing')])

    def test_exact_records_and_all_existing_scene_bytes_are_preserved(self):
        result, records = append_owners(self.solo, self.coop, self.owners)
        before, after = scene_group(self.coop), scene_group(result)
        self.assertEqual([record_name(n) for n in after.children], ['existing', 'bird_b', 'bird_a'])
        self.assertEqual(result[after.children[0].start:after.children[0].end], dummy('existing'))
        self.assertEqual(result[after.end:], self.coop[before.end:])
        self.assertEqual(len(result) - len(self.coop), len(dummy('bird_a')) + len(dummy('bird_b')))
        self.assertEqual(records, {name: digest(dummy(name)) for name in ('bird_a', 'bird_b')})

    def test_second_application_is_refused_not_duplicated(self):
        variant, _ = append_owners(self.solo, self.coop, self.owners)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            append_owners(self.solo, variant, self.owners)

    def test_missing_or_duplicate_source_owner_is_refused(self):
        for source in [scene([dummy('bird_a')]), scene([dummy('bird_a'), dummy('bird_a'), dummy('bird_b')])]:
            with self.assertRaises(ValueError):
                append_owners(source, self.coop, self.owners)

    def test_non_dummy_unknown_parent_or_parent_transform_is_refused(self):
        for record in [dummy('bird_a', kind=7), dummy('bird_a', parent='unknown'),
                       dummy('bird_a', world=2.75), dummy('bird_a', local=float('nan'))]:
            with self.assertRaises(ValueError):
                append_owners(scene([record, dummy('bird_b')]), self.coop, self.owners)

    def test_truncated_scene_or_duplicate_frame_group_is_refused(self):
        for raw in [self.coop[:-1], block(0x4C53, block(0x4000, dummy('a')) + block(0x4000, dummy('b')))]:
            with self.assertRaises(ValueError):
                append_owners(self.solo, raw, self.owners)

    def test_empty_source_owner_set_cannot_mask_missing_evidence(self):
        with self.assertRaises(ValueError):
            append_owners(scene([]), self.coop, self.owners)


class AmbientRegistryTests(unittest.TestCase):
    def setUp(self):
        self.owners = {'bird_a': 'bird.scr', 'bird_b': 'door.scr'}
        self.solo = registry([('BIRD_A', 'Bird.scr'), ('bird_b', 'door.scr')])
        self.coop = registry([('guard', 'guard.scr')])

    def test_appended_pairs_are_copied_raw_and_old_payload_is_unchanged(self):
        result = append_bindings(self.solo, self.coop, self.owners)
        self.assertEqual(result[6:], self.coop[6:] + self.solo[6:])
        self.assertEqual(len(registry_pairs(result)), 3)
        self.assertIn(b'BIRD_A\0', result)

    def test_existing_owner_or_script_on_another_owner_is_refused(self):
        for pairs in [[('bird_a', 'other.scr')], [('another', 'bird.scr')]]:
            with self.assertRaises(ValueError):
                append_bindings(self.solo, registry(pairs), self.owners)

    def test_wrong_or_duplicate_source_binding_is_refused(self):
        for pairs in [[('bird_a', 'wrong.scr'), ('bird_b', 'door.scr')],
                      [('bird_a', 'bird.scr'), ('bird_a', 'other.scr'), ('bird_b', 'door.scr')]]:
            with self.assertRaises(ValueError):
                append_bindings(registry(pairs), self.coop, self.owners)

    def test_bad_header_length_and_embedded_zero_are_refused(self):
        for raw in [self.coop[:-1], self.coop[:2] + b'\0'*4 + self.coop[6:], registry([('a\0b', 'x.scr')])]:
            with self.assertRaises(ValueError):
                registry_pairs(raw)


class AmbientRecipeTests(unittest.TestCase):
    def test_identical_scripts_need_no_exception(self):
        self.assertEqual(check_script_pair(b'unchanged', b'unchanged', 'test.scr', {}), 'identical')

    def test_exception_requires_both_exact_hashes_and_filename(self):
        allowed = {'horse.scr': (digest(b'solo'), digest(b'coop'))}
        self.assertEqual(check_script_pair(b'solo', b'coop', 'horse.scr', allowed),
                         'reviewed_difference_coop_preserved')
        for solo, coop, name in [(b'changed', b'coop', 'horse.scr'),
                                 (b'solo', b'changed', 'horse.scr'),
                                 (b'solo', b'coop', 'other.scr')]:
            with self.assertRaises(ValueError):
                check_script_pair(solo, coop, name, allowed)

    def test_burgundy_two_has_two_dummy_owners_not_a_horse_actor(self):
        recipe = RECIPES['co-burgundy2-animal-ambience']
        self.assertEqual(set(recipe['owners']), {'zwukkun', 'zwukprase'})
        self.assertEqual(recipe['sound_count'], 3)
        self.assertEqual(set(recipe['reviewed_script_differences']), {'br2_snd_kun.scr'})
        self.assertFalse(recipe['sounds_identical'])

    def test_burgundy_three_still_requires_ten_identical_scripts_and_sound_file(self):
        recipe = RECIPES['co-burgundy3-ambience']
        self.assertEqual(len(recipe['owners']), 10)
        self.assertEqual(recipe['sound_count'], 24)
        self.assertEqual(recipe['reviewed_script_differences'], {})
        self.assertTrue(recipe['sounds_identical'])


class AmbientOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'game'
        self.output = self.root / '.analysis/test.scene-patch.zip.disabled'
        self.payload = {name: name.encode('ascii') for name in MEMBERS}
        self.report = {'kind': 'inert_scene_registry_comparison', 'runtime_status': 'pending',
                       'installed_into_game': False, 'playable_mission': False,
                       'payloads': {name: {'size': len(data), 'sha256': digest(data)}
                                    for name, data in self.payload.items()}}

    def write(self, output=None, payload=None, report=None):
        return write_comparison(output or self.output, payload or self.payload,
                                report or self.report, self.game, self.root)

    def test_bundle_contains_only_two_disabled_pairs_and_a_disabled_report(self):
        self.write()
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(len(archive.namelist()), 5)
            self.assertTrue(all(name.endswith('.disabled') for name in archive.namelist()))
            self.assertNotIn('mission.json', archive.namelist())

    def test_overwrite_is_refused(self):
        self.write()
        original = self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            self.write()
        self.assertEqual(self.output.read_bytes(), original)

    def test_active_external_or_game_output_is_refused(self):
        for output in [self.root / '.analysis/active.zip', self.root / 'outside.scene-patch.zip.disabled']:
            with self.assertRaises(ValueError):
                self.write(output=output)
        self.game = self.root / '.analysis/game'
        with self.assertRaises(ValueError):
            self.write(output=self.game / 'test.scene-patch.zip.disabled')

    def test_missing_pair_or_hash_mismatch_is_refused_before_creation(self):
        partial = dict(self.payload)
        partial.pop('variant/mpscripts.dta.disabled')
        with self.assertRaises(ValueError):
            self.write(payload=partial)
        changed = dict(self.payload)
        changed['variant/scene2.bin.disabled'] = b'changed'
        with self.assertRaises(ValueError):
            self.write(payload=changed)
        self.assertFalse(self.output.exists())

    def test_false_playability_or_runtime_pass_claim_is_refused(self):
        for key, value in [('playable_mission', True), ('installed_into_game', True), ('runtime_status', 'passed')]:
            report = dict(self.report, **{key: value})
            with self.assertRaises(ValueError):
                self.write(report=report)


if __name__ == '__main__':
    unittest.main()
