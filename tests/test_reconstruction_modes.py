"""Mode-specific qualification is explicit and cannot silently become solo."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_reconstruction_variant as builder
import build_reconstruction_lab as lab
import reconstruction_runtime_audit as runtime
from test_reconstruction_variants import fixture, MemorySources, field
import test_reconstruction_runtime as runtime_tests


class ScriptModeTests(unittest.TestCase):
    def test_default_mode_remains_solo(self):
        profile, files = fixture()
        self.assertEqual(builder.qualification_mode(profile), 'solo')
        self.assertEqual(builder.registry_name(profile), 'scripts.dta')
        builder.prepare(profile, MemorySources(files))

    def test_coop_uses_only_its_registry(self):
        profile, files = fixture()
        profile['qualification_mode'] = 'cooperation'
        name = 'missions/example/scripts.dta'
        coop_name = 'missions/example/mpscripts.dta'
        files[coop_name] = files[name]
        profile['evidence'][coop_name] = profile['evidence'].pop(name)
        # Contradictory solo register must not contaminate the cooperative root.
        files[name] = ('missions.dta', b'\0'*6 + field(1, 'Owner') + field(1, 'Wrong.scr'))
        result, _ = builder.prepare(profile, MemorySources(files))
        self.assertIn(b'Move("P1")', result)
        self.assertEqual(builder.registry_name(profile), 'mpscripts.dta')
        del files[coop_name]
        with self.assertRaises(KeyError):
            builder.prepare(profile, MemorySources(files))

    def test_coop_catalog_requires_pinned_coop_root(self):
        profile, _ = fixture()
        profile['qualification_mode'] = 'cooperation'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'catalog.json'
            path.write_text(json.dumps({'schema_version':1,'profiles':[profile]}),encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Missing script, registry'):
                builder.load_catalog(path)

    def test_carnage_uses_original_solo_registry_not_renamed_wrapper(self):
        profile, files = fixture()
        profile['qualification_mode'] = 'carnage'
        self.assertEqual(builder.registry_name(profile), 'scripts.dta')
        builder.prepare(profile, MemorySources(files))
        with self.assertRaisesRegex(ValueError, 'Native-only qualification'):
            lab.plan_lab(profile, MemorySources(files))

    def test_no_coop_profile_can_be_exported_as_solo_lab(self):
        profile, files = fixture()
        profile['qualification_mode'] = 'cooperation'
        with self.assertRaisesRegex(ValueError, 'Native-only qualification'):
            lab.plan_lab(profile, MemorySources(files))

    def test_invalid_modes_refused(self):
        for mode in ('Solo', 'network', '', None, 3):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                builder.qualification_mode({'qualification_mode':mode})

    def test_real_carnage_recipes_are_exclusive_and_guarded(self):
        catalog = builder.load_catalog()
        for order in ('after', 'before'):
            profile = catalog['arctic1-carnage-sit-'+order+'-smoke']
            self.assertEqual(builder.qualification_mode(profile), 'carnage')
            self.assertEqual(profile['source'], 'scripts/arctic1/r_arc1a_kanisternik.scr')
            added = '\n'.join(e['after'] for e in profile['edits'])
            self.assertIn('(_SPGetGameType()==3) OR (_SPGetGameType()==7)', added)
            self.assertNotIn('kourimsed2', added)
            self.assertNotIn('OnSignal(5)', added)
            self.assertNotIn('FRM_CreatePhysicalObject', added)
            self.assertNotIn('HUMAN_Move', added)

    def test_carnage_cleanup_latches_before_calls_and_does_not_stand_dead_actor(self):
        catalog = builder.load_catalog()
        for order in ('after', 'before'):
            p = catalog['arctic1-carnage-sit-'+order+'-smoke']
            for prefix in ('OnAlarm()\n{','OnDeath()\n{'):
                after = next(e['after'] for e in p['edits'] if e['before'] == prefix)
                self.assertLess(after.index('heritage_idle_active = 0;'), after.index('HUMAN_ACTIVITY_Smoke(false)'))
                if prefix.startswith('OnDeath'):
                    self.assertNotIn('HUMAN_SETMODE_Stand', after)
            cutscene = next(e['after'] for e in p['edits'] if e['before'] == 'OnCutscene(4){}')
            self.assertIn('heritage_idle_blocked = 1;', cutscene)
            self.assertTrue(cutscene.endswith('OnCutsceneDone(4){}'))

    def test_carnage_order_alternatives_cannot_both_be_applied(self):
        catalog = builder.load_catalog()
        after = catalog['arctic1-carnage-sit-after-smoke']
        before = catalog['arctic1-carnage-sit-before-smoke']
        smoke_after = next(e['after'] for e in after['edits'] if e['before'] == '  HUMAN_ACTIVITY_Smoke(true);')
        smoke_before = next(e['after'] for e in before['edits'] if e['before'] == '  HUMAN_ACTIVITY_Smoke(true);')
        self.assertNotIn('HUMAN_ACTIVITY_Sit(sit);', smoke_after)
        self.assertLess(smoke_before.index('HUMAN_ACTIVITY_Sit(sit);'), smoke_before.index('HUMAN_ACTIVITY_Smoke(true);'))
        from prepare_reconstruction_trials import conflicts
        self.assertIn(before['id'], conflicts(catalog)[after['id']])

    def test_coop_interrogation_has_distinct_source_and_controller(self):
        p = builder.load_catalog()['co-burgundy3-interrogation-visual-phases']
        changes = builder.change_specs(p)
        self.assertEqual(builder.qualification_mode(p), 'cooperation')
        self.assertEqual(len(changes), 3)
        self.assertTrue(all(c['source'].startswith('scripts/co_burgundy3/') for c in changes))
        self.assertEqual(changes[2]['actor'], 'dummy_rozhovor_sas')
        self.assertIn('missions/co_burgundy3/mpscripts.dta', p['evidence'])
        self.assertNotIn('missions/co_burgundy3/scripts.dta', p['evidence'])
        self.assertNotIn('scripts/co_burgundy3/bur3_06.scr', p['evidence'])

    def test_coop_interruption_and_objectives_preserved_by_prefix_only_edits(self):
        p = builder.load_catalog()['co-burgundy3-interrogation-visual-phases']
        changes = builder.change_specs(p)
        for e in changes[2]['edits']:
            self.assertTrue(e['after'].startswith(e['before']))
            self.assertEqual(e['after'].count('SendSignal('), 2)
        interrupted = [e for e in changes[2]['edits'] if e['before'].startswith('OnSignal(1)')]
        self.assertEqual(len(interrupted), 1)
        for c in changes:
            text = '\n'.join(e['after'] for e in c['edits'])
            self.assertNotIn('goto ACTIVITY', text)
            self.assertNotIn('SendSignal(obj', text)
            self.assertNotIn('SendSignal(texty', text)
            self.assertNotIn('SaveGameValue', text)

    def test_runtime_carnage_cannot_claim_solo_proof(self):
        # Reuse fixture setup, not its test class in discovery.
        case = runtime_tests.RuntimeRegisterTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.expected['example']['mode'] = 'carnage'
        self.assertFalse(case.run_audit()['ok'])
        case.profile['mode'] = 'carnage'
        self.assertTrue(case.run_audit()['ok'])
        evidence = case.record()
        self.assertFalse(case.run_audit()['ok'])
        evidence['mode'] = 'carnage'
        self.assertTrue(case.run_audit()['ok'])

    def test_cooperative_script_requires_network_scenario(self):
        case = runtime_tests.RuntimeRegisterTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.expected['example']['mode'] = 'cooperation'
        case.profile['mode'] = 'cooperation'
        self.assertFalse(case.run_audit()['ok'])
        case.profile['results']['network'] = {'state':'pending','evidence':None}
        self.assertTrue(case.run_audit()['ok'])


if __name__ == '__main__':
    unittest.main()
