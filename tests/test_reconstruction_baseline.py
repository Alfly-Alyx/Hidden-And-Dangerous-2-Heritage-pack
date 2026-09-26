"""Composed native baselines with invented scripts, never engine evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_reconstruction_variant as builder
import build_reconstruction_lab as lab
import reconstruction_baseline as composition
import reconstruction_trial_deploy as deploy
import reconstruction_runtime_audit as runtime
import test_reconstruction_runtime as runtime_tests
from test_reconstruction_variants import fixture, field, MemorySources


def composed_fixture():
    p, files = fixture()
    def remap(name):
        return name.replace('/example/', '/africa4/').replace('/source.scr', '/af3b_organizer.scr')
    files = {remap(n): v for n,v in files.items()}
    p['source'] = composition.SOURCE
    p['checks'][0]['entry'] = remap(p['checks'][0]['entry'])
    files['missions/africa4/scripts.dta'] = ('missions.dta', b'\0'*6 + field(1,'Owner') + field(1,'af3b_organizer.scr'))
    source = (b'// fabricated contract, not a commercial script\n'
              b'INTEGER odvysilali = _LoadGameValue(20);\n   odvysilali = 1;\n'
              b'if(odvysilali){signal1=20;signal2=1;}else{signal1=21;signal2=2;}\n'
              b'if(odvysilali){zpozdeni=30000;}else{zpozdeni=20000;}\n'
              b'//Move("P1");\nEnd();\n')
    files[p['source']] = ('Patch.dta', source)
    for name in ('tree.klz', 'scene.4ds', 'scene2.bin'):
        files[f'missions/africa4/{name}'] = ('missions.dta', b'FABRICATED STRUCTURE')
    for actor in composition.CAMPAIGN:
        raw = (b'// invented receiver\nOnSignal(1){} OnSignal(2){} OnSignal(20){} OnSignal(21){}\n'
               b'INTEGER odvysilali=_LoadGameValue(20); if(!odvysilali){}\n')
        if actor == 'af3b_dummy_diary':
            raw += b'if(odvisilali){AddDiaryText(4153);}else{AddDiaryText(4154);}\n'
        files[f'scripts/africa4/{actor}.scr'] = ('Scripts.dta', raw)
    p['evidence'] = {n: {'archive':a,'size':len(raw),'sha256':builder.digest(raw)} for n,(a,raw) in files.items()}
    files['missions/africa3/scripts.dta'] = ('missions.dta', b'\0'*6 + field(1,'AF3a_19') + field(1,'AF3a_19.scr'))
    files['missions/africa3/actors.bin'] = ('missions.dta', field(0x10,'AF3a_19'))
    files['scripts/africa3/af3a_19.scr'] = ('Patch.dta', b'// invented operator\nSaveGameValue(20,0);\nSaveGameValue(20,1);')
    baseline = builder.apply_edits(source, [composition.EDIT])
    p['comparison_baseline'] = {
        'id':composition.IDENTIFIER, 'source':p['source'], 'edits':[composition.EDIT],
        'module':{'path':composition.MODULE,'text_sha256':composition.MODULE_SHA},
        'size':len(baseline),'sha256':builder.digest(baseline),
        'external_evidence':{n:{'archive':files[n][0],'size':len(files[n][1]),'sha256':builder.digest(files[n][1])}
                             for n in composition.EXTERNAL}}
    sources = MemorySources(files)
    sources.excluded_loose_overrides = {}
    sources.mission_entries = lambda mission: sorted(n for n in files if n.split('/')[1] == mission)
    return p, sources, baseline


class ComposedBaselineTests(unittest.TestCase):
    def setUp(self):
        self.profile, self.sources, self.baseline = composed_fixture()

    def plan(self):
        p = self.profile
        return deploy.native_plan(p['id'], {p['id']:p}, self.sources,
                                  {'test_plan_sha256':{p['id']:'a'*64}})

    def test_variant_changes_only_experiment_relative_to_same_shared_baseline(self):
        self.sources.excluded_loose_overrides = {'missions/africa3/scripts.dta': {'size':12,'sha256':'a'*64},
                                                 'unrelated': {'size':5,'sha256':'b'*64}}
        result, proof = builder.prepare_changes(self.profile, self.sources)
        self.assertEqual(result[self.profile['source']], builder.apply_edits(self.baseline, self.profile['edits']))
        self.assertNotIn(b'   odvysilali = 1;', result[self.profile['source']])
        self.assertEqual(proof['comparison_baseline']['sha256'], builder.digest(self.baseline))
        self.assertNotEqual(proof['source_sha256'], proof['comparison_baseline']['sha256'])
        self.assertFalse(proof['comparison_baseline']['complete_heritage_installation_qualified'])
        self.assertEqual(set(proof['comparison_baseline']['excluded_external_loose_overrides']),
                         {'missions/africa3/scripts.dta'})

    def test_native_pair_keeps_commercial_provenance_but_composed_baseline(self):
        snapshots, preset = self.plan()
        name = 'Scripts/africa4/af3b_organizer.scr'
        self.assertEqual(snapshots['baseline'][name], self.baseline)
        self.assertEqual(snapshots['variant'][name], builder.apply_edits(self.baseline, self.profile['edits']))
        original = self.sources.files[self.profile['source']][1]
        self.assertEqual(preset['source_files'][self.profile['source']]['sha256'], builder.digest(original))
        self.assertEqual(preset['changed_entries'], [self.profile['source']])
        self.assertEqual(preset['closure']['baseline'], preset['closure']['variant'])
        self.assertTrue(all('/africa3/' not in n for branch in snapshots.values() for n in branch))

    def test_renamed_lab_refuses_composition_before_reading_any_source(self):
        with self.assertRaisesRegex(ValueError, 'Native-only comparison baseline'):
            lab.plan_lab(self.profile, None)

    def test_external_source_change_and_wrong_radio_binding_refused(self):
        name = 'missions/africa3/scripts.dta'
        self.sources.files[name] = ('missions.dta', b'\0'*6 + field(1,'AF3a_19') + field(1,'different.scr'))
        with self.assertRaisesRegex(ValueError, 'External campaign source changed'):
            builder.prepare_changes(self.profile, self.sources)
        raw = self.sources.files[name][1]
        self.profile['comparison_baseline']['external_evidence'][name].update(size=len(raw),sha256=builder.digest(raw))
        with self.assertRaisesRegex(ValueError, 'radio-operator ownership'):
            builder.prepare_changes(self.profile, self.sources)

    def test_commented_campaign_write_is_not_active_evidence(self):
        name = 'scripts/africa3/af3a_19.scr'
        raw = b'SaveGameValue(20,0);\n//SaveGameValue(20,1);'
        self.sources.files[name] = ('Patch.dta',raw)
        self.profile['comparison_baseline']['external_evidence'][name].update(size=len(raw),sha256=builder.digest(raw))
        with self.assertRaisesRegex(ValueError, 'campaign contract'):
            builder.prepare_changes(self.profile, self.sources)

    def test_changed_module_or_declared_fingerprint_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            module = root / composition.MODULE
            module.parent.mkdir()
            module.write_text('fabricated modified module',encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'module changed'):
                composition.baseline_spec(self.profile, root=root)
        self.profile['comparison_baseline']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'baseline fingerprint'):
            builder.prepare_changes(self.profile, self.sources)

    def test_baseline_cannot_escape_scope_or_be_silently_applied_to_atomic_members(self):
        for key,value in [('source','scripts/other/source.scr'), ('id','invented'), ('size',True),
                          ('edits',[{'before':'End();','after':'Alter();'}]),
                          ('external_evidence',{}), ('module',{'path':'../secret','text_sha256':'0'*64})]:
            p = copy.deepcopy(self.profile)
            p['comparison_baseline'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                composition.baseline_spec(p)
        for key,value in [('additional_changes',[{'invented':True}]), ('qualification_mode','cooperation')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                composition.baseline_spec({**self.profile,key:value})

    def test_receiver_contract_and_diary_are_checked_not_only_pinned(self):
        for name in ('af3b_01','af3b_11','af3b_tankista01','af3b_26','af3b_dummy_diary'):
            p,s,_ = composed_fixture()
            path = f'scripts/africa4/{name}.scr'
            raw = b'// OnSignal(1){} OnSignal(2){} OnSignal(20){} OnSignal(21){}'
            s.files[path] = ('Scripts.dta',raw)
            p['evidence'][path].update(size=len(raw),sha256=builder.digest(raw))
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'campaign contract'):
                builder.prepare_changes(p,s)

    def test_double_application_refused_not_presented_as_fresh_baseline(self):
        self.sources.files[self.profile['source']] = ('Patch.dta',self.baseline)
        self.profile['evidence'][self.profile['source']].update(size=len(self.baseline),sha256=builder.digest(self.baseline))
        with self.assertRaisesRegex(ValueError, 'match exactly once'):
            builder.prepare_changes(self.profile,self.sources)

    def test_native_preset_baseline_identity_cannot_be_swapped(self):
        snapshots,preset = self.plan()
        with tempfile.TemporaryDirectory() as folder:
            session=Path(folder)
            (session/'presets').mkdir()
            for branch in snapshots.values():
                for raw in branch.values(): deploy.put_blob(session,raw)
            expected={self.profile['id']:{'definition_sha256':runtime.fingerprint(self.profile),
                      'mode':'solo','comparison_baseline':composition.IDENTIFIER}}
            def persist():
                (session/'presets'/(self.profile['id']+'.json')).write_text(json.dumps(preset))
                (session/'PRESETS.json').write_text(json.dumps({'profiles':[{'profile':self.profile['id'],
                                                         'sha256':runtime.fingerprint(preset)}]}))
            persist()
            deploy.load_preset(session,self.profile['id'],expected=expected)
            preset['comparison_baseline']['id']='commercial'
            persist()
            with self.assertRaisesRegex(ValueError, 'Comparison baseline differs'):
                deploy.load_preset(session,self.profile['id'],expected=expected)

    def test_runtime_register_refuses_wrong_or_missing_baseline_identity(self):
        case=runtime_tests.RuntimeRegisterTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.expected['example']['comparison_baseline']=composition.IDENTIFIER
        self.assertFalse(case.run_audit()['ok'])
        case.profile['comparison_baseline']=composition.IDENTIFIER
        self.assertTrue(case.run_audit()['ok'])
        case.profile['comparison_baseline']='commercial'
        self.assertFalse(case.run_audit()['ok'])

    def test_real_profile_keeps_exact_transition_delta_from_commercial_pair(self):
        cat=builder.load_catalog()
        p=cat['africa4-invasion-transition-heritage-radio']
        self.assertEqual(p['edits'],cat['africa4-invasion-transition']['edits'])
        self.assertEqual(p['comparison_baseline']['size'],3978)
        self.assertEqual(len(p['evidence']),32)
        self.assertEqual(len(composition.SOLDIERS),18)
        self.assertEqual(len(set(composition.CAMPAIGN)),28)


if __name__ == '__main__':
    unittest.main()
