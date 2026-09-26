"""Recipe invariants using invented data; these are not engine validations."""
import copy
import itertools
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_reconstruction_variant as builder
from test_reconstruction_variants import MemorySources, fixture


class ExpansionRecipeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = builder.load_catalog()

    def test_cistern_probes_change_one_independent_effect_only(self):
        for effect, call in [('particle', 'FRM_CreateParticle(53, MyFRM);'),
                             ('sound', 'PlaySound(6, 2);')]:
            profile = self.catalog['arctic1-cistern1-' + effect]
            self.assertEqual(profile['actor'], 'm_nadrz_')
            self.assertEqual(profile['source'], 'scripts/arctic1/r_arc1a_cisterna1.scr')
            self.assertEqual(profile['edits'], [{'before': '//  ' + call, 'after': '  ' + call}])
            self.assertFalse(profile.get('additional_changes'))
            raw = ('// fabricated test\r\n//  ' + call + '\r\nKeepExplosion();\r\nSave(101);').encode()
            self.assertEqual(builder.apply_edits(raw, profile['edits']), raw.replace(b'//  ', b'  '))

    def test_cistern_probe_rejects_already_active_or_ambiguous_effect(self):
        profile = self.catalog['arctic1-cistern1-sound']
        for source in (b'  PlaySound(6, 2);', b'//  PlaySound(6, 2);\n//  PlaySound(6, 2);'):
            with self.assertRaises(ValueError):
                builder.apply_edits(source, profile['edits'])

    def test_invasion_only_uncomments_four_unique_calls(self):
        profile = self.catalog['africa4-invasion-transition']
        self.assertEqual(len(profile['edits']), 4)
        for spec in profile['edits']:
            self.assertEqual(spec['before'][2:], spec['after'])
        unchanged = b'odvysilali = 1;\r\nSendSignal(driver, signal1);\r\nDelay(20000);'
        raw = '\n'.join(e['before'] for e in profile['edits']).encode() + b'\r\n' + unchanged
        result = builder.apply_edits(raw, profile['edits'])
        self.assertTrue(result.endswith(unchanged))
        self.assertEqual(result.count(b'Delay(20000);'), 2)

    def test_park_condition_uses_eight_states_not_jeep_or_aggregate(self):
        profile = self.catalog['libye2-destroyed-park-dialogue']
        phrase = next(e['after'] for e in profile['edits'] if '53990023' in e['before'])
        names = re.findall(r'_ACTOR_GetState\((\w+)\)==0', phrase)
        self.assertEqual(names, ['opel1', 'opel2', 'opel3', 'opel4', 'opel5', 'opelflak1', 'opelflak2', 'kubel'])
        # Every binary state combination: exactly all eight destroyed qualifies.
        for states in itertools.product((0, 1), repeat=8):
            values = dict(zip(names, states))
            self.assertEqual(all(values[n] == 0 for n in names), not any(states))
        self.assertNotIn('jeep', phrase.lower())
        self.assertIn('(_ACTOR_GetState(af2_24) != 0)', phrase)
        self.assertIn('(_ACTOR_GetState(af2_25) != 0)', phrase)
        self.assertLess(phrase.index('heritage_phrase_used = 1;'), phrase.index('FRM_MorphSpeechDelayed'))

    def test_dialogue_latches_before_signals_and_keeps_cancellation(self):
        specs = self.catalog['libye2-destroyed-park-dialogue']['edits']
        dispatch = next(e['after'] for e in specs if e['before'] == '\tSendSignal(af2_24, 2);')
        self.assertLess(dispatch.index('heritage_dialogue_state = 1;'), dispatch.index('SendSignal'))
        self.assertLess(dispatch.index('SetWhenever(start, false);'), dispatch.index('SendSignal'))
        reply = next(e['after'] for e in specs if e['before'] == '\tGoTo start;')
        self.assertIn('heritage_dialogue_state == 1', reply)
        self.assertLess(reply.index('heritage_dialogue_state = 2;'), reply.index('GoTo start;'))
        cancel = next(e['after'] for e in specs if 'af2_24, 0, 0, 0' in e['before'])
        self.assertIn('heritage_dialogue_state = 3;', cancel)
        self.assertNotIn('DisableSignals', '\n'.join(e['after'] for e in specs))

    def test_dialogue_does_not_change_speakers_objectives_or_vehicle_scripts(self):
        profile = self.catalog['libye2-destroyed-park-dialogue']
        self.assertFalse(profile.get('additional_changes'))
        self.assertEqual(profile['source'], 'scripts/libye2/af2_24_25_speech.scr')
        after = '\n'.join(e['after'] for e in profile['edits'])
        self.assertNotRegex(after, r'\b(?:AddObjective|SetObjective|HUMAN_BoardVehicle|SaveGameValue)\s*\(')
        self.assertEqual({a['path'] for a in profile['asset_evidence']},
                         {'sounds/53990023.wav', 'tables/dabing/53990023.dat'})

    def test_alps_profiles_only_remove_selected_comment_markers(self):
        profiles = [p for key, p in self.catalog.items() if key.startswith('alps1-')]
        self.assertEqual(len(profiles), 9)
        for p in profiles:
            for spec in p['edits']:
                self.assertEqual(spec['before'][2:], spec['after'])
                self.assertNotRegex(spec['after'], r'(?:PlaySound|MorphSpeech|SendSignal)')
            self.assertFalse(p.get('additional_changes'))

    def test_ge31_pair_cannot_build_with_only_one_dormant_stance(self):
        profile = self.catalog['alps1-ge31-range-stance-pair']
        self.assertEqual(len(profile['edits']), 2)
        with self.assertRaises(ValueError):
            builder.apply_edits(profile['edits'][0]['before'].encode(), profile['edits'])

    def test_ge17_keeps_teleport_disabled_and_final_route(self):
        profile = self.catalog['alps1-ge17-move-before-final-post']
        tail = b'\r\n//FRM_TeleportNearCheckpoint(me, "ge17_03", "ge16_sniper");\r\nHUMAN_Move("ge17_04");'
        raw = profile['edits'][0]['before'].encode() + tail
        self.assertEqual(builder.apply_edits(raw, profile['edits']), raw[2:])
        self.assertTrue(builder.apply_edits(raw, profile['edits']).endswith(tail))

    def test_card_pair_is_atomic_and_cleans_before_existing_handlers(self):
        profile = self.catalog['africa1-card-players-pair']
        changes = builder.change_specs(profile)
        self.assertEqual([p['actor'] for p in changes], ['AF1_24', 'AF1_25'])
        for change in changes:
            handlers = [e for e in change['edits'] if e['before'].startswith(('OnDeath', 'OnAlarm', 'OnSignal'))]
            self.assertEqual(len(handlers), 3)
            for spec in handlers:
                self.assertTrue(spec['after'].startswith(spec['before']))
                self.assertLess(spec['after'].index('heritage_cards_active = 0;'),
                                spec['after'].index('HUMAN_ACTIVITY_Card(0);'))
                self.assertIn('SetWhenever(player, false);', spec['after'])
            loop = next(e['after'] for e in change['edits'] if 'Card(1)' in e['before'])
            self.assertLess(loop.index('heritage_cards_active = 1;'), loop.index('Card(1)'))
            self.assertLess(loop.index('Delay(1500);'), loop.index('goto LOOP;'))
            self.assertNotIn('SendSignal', loop)


class PinnedAssetTests(unittest.TestCase):
    def setUp(self):
        self.profile, files = fixture()
        self.raw = b'FABRICATED AUDIO FOR TESTS'
        self.spec = {'path': 'sounds/12345678.wav', 'archive': 'LangEnglish.dta',
                     'size': len(self.raw), 'sha256': builder.digest(self.raw)}
        self.profile['asset_evidence'] = [self.spec]
        self.sources = MemorySources(files)
        self.sources.read_asset = lambda name, archive: self.raw

    def test_matching_asset_allows_recipe_without_export(self):
        variant, report = builder.prepare(self.profile, self.sources)
        self.assertNotIn(self.raw, variant)
        self.assertEqual(report['runtime_status'], 'pending')

    def test_changed_asset_refuses_entire_recipe(self):
        self.raw += b'changed'
        with self.assertRaisesRegex(ValueError, 'asset changed'):
            builder.prepare(self.profile, self.sources)

    def test_asset_paths_archives_and_duplicates_are_restricted(self):
        for key, value in [('path', '../secret'), ('path', 'scripts/example/a.scr'),
                           ('path', 'sounds/12345678.WAV'), ('archive', '../LangEnglish.dta'),
                           ('size', True), ('sha256', 'invalid')]:
            spec = {**self.spec, key: value}
            with self.assertRaises(ValueError):
                builder.asset_specs({'asset_evidence': [spec]})
        with self.assertRaises(ValueError):
            builder.asset_specs({'asset_evidence': [self.spec, self.spec]})

    def test_asset_reader_refuses_conflicting_loose_audio_even_archives_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            loose = root / self.spec['path']
            loose.parent.mkdir()
            loose.write_bytes(b'OTHER AUDIO')
            source = builder.ArchiveSources(root, archives_only=True)
            class Archive:
                def read(inner, entry):
                    return self.raw
            source.index['LangEnglish.dta'] = (Archive(), {self.spec['path']: [object()]})
            with self.assertRaisesRegex(ValueError, 'Conflicting loose'):
                source.read_asset(self.spec['path'], 'LangEnglish.dta')
            loose.write_bytes(self.raw)
            self.assertEqual(source.read_asset(self.spec['path'], 'LangEnglish.dta'), self.raw)

    def test_loading_asset_archive_does_not_expand_mission_inventory(self):
        source = builder.ArchiveSources(Path('.'))
        source.index = {'missions.dta': (None, {'scripts/example/original.scr': []}),
                        'LangEnglish.dta': (None, {'scripts/example/other.scr': []})}
        self.assertEqual(source.mission_entries('example'), ['scripts/example/original.scr'])
