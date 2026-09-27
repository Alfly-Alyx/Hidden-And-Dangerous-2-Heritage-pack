"""Original synthetic tables/models/texts, never installed or executed."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import benelli_trial_payload as trial
from item_table_additive import build,fingerprint
from texty_additive import append_labels,ENCODINGS
from reconstruction_sandbox import write_new
from test_item_table_overlay import sources


def fixture():
    archive,descriptor,fragment=sources()
    result,proof=build(archive['items'],archive['fpv'],descriptor,fragment,slot=359)
    files={'PROTOTYPE_Benelli.item.disabled':descriptor,'PROTOTYPE_Benelli.fpvgroup.disabled':fragment,
           'Tables/items.sav.disabled':result['items'],'Tables/FpvAnims.sav.disabled':result['fpv']}
    before={'Tables/items.sav':archive['items'],'Tables/FpvAnims.sav':archive['fpv']};pins={};text_proofs={}
    for stem in trial.MODEL_PINS:
        raw=b'Invented geometry '+stem.encode();files[stem+'.4ds.disabled']=raw
        pins[stem]=(len(raw),fingerprint(raw)['sha256']);before['Models/'+stem+'.4ds']=None
    labels=[{'key':'benelli_m4','text_id':21500,'values':{lang:'Invented [MODERN]' for lang in ENCODINGS}}]
    for lang in ENCODINGS:
        target='Text/'+lang+'/TEXTY_DD.txt';original=b'1000 "Existing text"\r\n'
        changed,receipt=append_labels(original,labels,lang)
        files[target+'.disabled']=changed;before[target]=original;text_proofs[target]=receipt
    manifest={'scope':'private_disabled_benelli_full_table_lab','installation_allowed':False,'game_modified':False,
              'reverse_verified_in_memory':True,'files':{name:fingerprint(raw) for name,raw in files.items()},
              'transaction':proof,'descriptor_lab':{'inventory_texts':{'proofs':text_proofs}},
              'pending_requirements':['native_hands','global_slot_freedom','isolated_transaction']}
    return files,manifest,before,pins


class TrialPayloadTests(unittest.TestCase):
    def test_exact_twelve_targets_exclude_audit_fragments_and_preserve_all_sources(self):
        files,manifest,before,pins=fixture();original=copy.deepcopy((files,manifest,before))
        with patch.object(trial,'MODEL_PINS',pins):after,report=trial.prepare(files,manifest,before)
        self.assertEqual(len(after),12);self.assertEqual(len(report['files']),12)
        self.assertTrue(all(not path.endswith('.disabled') for path in after))
        self.assertEqual(report['audit_only_files'],sorted(trial.AUDIT_FILES))
        self.assertEqual(sum(row['operation']=='create' for row in report['files']),2)
        self.assertEqual(report['pending_requirements'],manifest['pending_requirements'])
        self.assertEqual((files,manifest,before),original)
        for key in ('installation_allowed','game_started','game_modified','playable_weapon',
                    'isolated_filesystem_transaction_performed','native_resource_search_qualified'):
            self.assertFalse(report[key])

    def test_missing_languages_audit_fragments_and_duplicate_targets_are_refused(self):
        files,_,_,_=fixture()
        for name in ('PROTOTYPE_Benelli.item.disabled','Text/french/TEXTY_DD.txt.disabled','Tables/items.sav.disabled'):
            incomplete=dict(files);incomplete.pop(name)
            with self.assertRaisesRegex(ValueError,'Incomplete'):trial.target_map(incomplete)
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            trial.target_map([*files,'text/FRENCH/texty_dd.TXT.disabled'])

    def test_executable_save_unknown_or_traversing_payloads_never_become_targets(self):
        files,_,_,_=fixture()
        for name in ('HD2_SabreSquadron.exe.disabled','Players/save.sav.disabled','../escape.disabled',
                     'Text/french/../../items.sav.disabled','Models/PROTOTYPE_BenFPV.4ds.disabled',
                     'Text/french/TEXTY_DD.txt','Tables/item_shoot.tbl.disabled'):
            with self.subTest(name=name),self.assertRaises(ValueError):trial.target_map({**files,name:b'x'})

    def test_existing_modern_models_are_never_overwritten_even_when_identical(self):
        files,manifest,before,pins=fixture()
        before['Models/PROTOTYPE_BenFPV.4ds']=files['PROTOTYPE_BenFPV.4ds.disabled']
        with patch.object(trial,'MODEL_PINS',pins),self.assertRaisesRegex(ValueError,'already exists'):
            trial.prepare(files,manifest,before)

    def test_archive_table_absence_is_preserved_but_missing_personal_snapshot_is_a_conflict(self):
        files,manifest,before,pins=fixture();before['Tables/items.sav']=None
        with patch.object(trial,'MODEL_PINS',pins):
            _,report=trial.prepare(files,manifest,before)
            self.assertEqual(sum(row['operation']=='create' for row in report['files']),3)
            manifest['central_table_overlay_composition']={'selected_source':{'items':'installed_snapshot','fpv':'reviewed_archive'}}
            with self.assertRaisesRegex(ValueError,'Current central table'):trial.prepare(files,manifest,before)

    def test_changed_current_table_or_text_refuses_plan_without_normalization(self):
        for target in ('Tables/items.sav','Tables/FpvAnims.sav','Text/french/TEXTY_DD.txt'):
            files,manifest,before,pins=fixture();before[target]+=b'personal later edit'
            with patch.object(trial,'MODEL_PINS',pins),self.assertRaisesRegex(ValueError,'Current'):
                trial.prepare(files,manifest,before)

    def test_payload_hash_native_model_and_fragment_mismatches_are_all_refused(self):
        for name,refresh in (('Tables/items.sav.disabled',False),('PROTOTYPE_BenFPV.4ds.disabled',True),
                             ('PROTOTYPE_Benelli.item.disabled',True),('PROTOTYPE_Benelli.fpvgroup.disabled',True)):
            files,manifest,before,pins=fixture();files[name]+=b'changed'
            if refresh:manifest['files'][name]=fingerprint(files[name])
            with patch.object(trial,'MODEL_PINS',pins),self.assertRaises(ValueError):trial.prepare(files,manifest,before)

    def test_approval_claims_boolean_aliases_and_incomplete_snapshots_are_not_accepted(self):
        for key,value in (('installation_allowed',True),('game_modified',0),('reverse_verified_in_memory',1),('scope','unrelated')):
            files,manifest,before,pins=fixture();manifest[key]=value
            with patch.object(trial,'MODEL_PINS',pins),self.assertRaisesRegex(ValueError,'manifest'):
                trial.prepare(files,manifest,before)
        files,manifest,before,pins=fixture();before.pop('Models/PROTOTYPE_BenFPV.4ds')
        with patch.object(trial,'MODEL_PINS',pins),self.assertRaisesRegex(ValueError,'snapshots'):
            trial.prepare(files,manifest,before)

    def test_lab_loader_validates_names_before_reading_and_reads_only_expected_files(self):
        files,manifest,_,_=fixture()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name,raw in files.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);write_new(path,raw)
            write_new(root/'MANIFEST.json',json.dumps(manifest).encode())
            actual,loaded,mapping=trial.load_lab(root)
            self.assertEqual(actual,files);self.assertEqual(loaded,manifest);self.assertEqual(len(mapping),12)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);write_new(root/'MANIFEST.json',json.dumps({'files':{'../escape':{}}}).encode())
            with self.assertRaisesRegex(ValueError,'unsafe'):trial.load_lab(root)

    def test_target_reader_captures_absence_and_refuses_directories(self):
        files,_,_,_=fixture();mapping=trial.target_map(files)
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp);before=trial.read_targets(game,mapping)
            self.assertEqual(set(before.values()),{None})
            (game/'Tables/items.sav').mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'regular file'):trial.read_targets(game,mapping)


if __name__=='__main__':unittest.main()
