"""Invented chunk fixtures only; no commercial sound definition or recording."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from sound_definition import parse,VARIANT_FIELDS
from sound_definition_additive import build,restore,encode_entry
from test_sound_definition import fixture,chunk,bank,entry


def modern(which=0):
    return {'bank':2+which,'label':'MODERN INVENTED '+str(which),'flag_raw':0,
            'variant':{'filename':'MOD_INVENTED_'+str(which)+'.wav',
                       'parameters_raw':{str(k):k for k in VARIANT_FIELDS[1:]}}}


class AdditiveSoundTests(unittest.TestCase):
    def test_append_preserves_original_ordinals_variants_empty_entries_and_lookup(self):
        source=fixture();before=parse(source);additions=[modern(),modern(1)];copy=deepcopy(additions)
        current,proof=build(source,additions);after=parse(current)
        self.assertEqual(additions,copy);self.assertEqual(restore(current,proof),source)
        self.assertEqual([(r['bank'],r['index']) for r in proof['additions']],[(2,1),(3,1)])
        self.assertEqual(after['entry_count'],before['entry_count']+2)
        for a,b in zip(before['banks'],after['banks']):
            self.assertEqual([e['sha256'] for e in a['entries']],[e['sha256'] for e in b['entries'][:len(a['entries'])]])
        a,b=before['opaque_lookup'],after['opaque_lookup']
        self.assertEqual(source[a['offset']:a['offset']+a['size']],current[b['offset']:b['offset']+b['size']])

    def test_multiple_same_bank_appends_keep_requested_relative_order(self):
        first=modern();second=modern(1);second['bank']=2
        current,proof=build(fixture(),[first,second])
        self.assertEqual([r['index'] for r in proof['additions']],[1,2]);self.assertEqual(restore(current,proof),fixture())
        self.assertEqual(parse(current)['banks'][2]['entries'][2]['label'],second['label'])

    def test_collision_in_names_or_filenames_is_case_insensitively_refused(self):
        current,_=build(fixture(),[modern()])
        with self.assertRaisesRegex(ValueError,'collision'):build(current,[modern()])
        first=modern();second=modern(1);second['variant']['filename']=first['variant']['filename']
        with self.assertRaisesRegex(ValueError,'collision'):build(fixture(),[first,second])
        second=modern(1);second['label']=first['label']
        with self.assertRaisesRegex(ValueError,'collision'):build(fixture(),[first,second])

    def test_bank_owner_bounds_and_entry_shape_are_strict(self):
        for key,value in (('bank',True),('bank',4),('label','Old identity'),('flag_raw',True),('flag_raw',2)):
            bad=modern();bad[key]=value
            with self.assertRaises(ValueError):encode_entry(bad)
        for filename in ('../test.wav','MOD_ok.wav','MOD_BAD.WAV','MOD_BAD.wav.disabled','MOD_A.wav/../B'):
            bad=modern();bad['variant']['filename']=filename
            with self.assertRaises(ValueError):encode_entry(bad)
        for value in (True,-1,2**32):
            bad=modern();bad['variant']['parameters_raw']['1410']=value
            with self.assertRaises(ValueError):encode_entry(bad)
        wrong=chunk(1000,bank()+bank()+bank('Wrong owner'))
        with self.assertRaisesRegex(ValueError,'owner'):build(wrong,[modern()])
        full=chunk(1000,bank()+bank()+bank('Weapon Shooting',entry()*256))
        with self.assertRaisesRegex(ValueError,'capacity'):build(full,[modern()])

    def test_modified_output_or_receipt_refuses_reversal(self):
        current,proof=build(fixture(),[modern(),modern(1)])
        with self.assertRaises(ValueError):restore(current+b'changed',proof)
        for mutate in (lambda p:p.update(schema_version=True),lambda p:p['before'].update(sha256='0'*64),
                       lambda p:p['additions'][0].update(index=0),lambda p:p['additions'][0].update(size=1),
                       lambda p:p['additions'][0].update(bank=True),lambda p:p.update(global_indices_reserved=True),
                       lambda p:p.update(additions=[])):
            bad=deepcopy(proof);mutate(bad)
            with self.assertRaises(ValueError):restore(current,bad)

    def test_no_lookup_or_empty_target_bank_remains_reversible(self):
        source=chunk(1000,bank()+bank()+bank('Weapon Shooting',b'')+bank('Weapon Manipulation',b''))
        current,proof=build(source,[modern()])
        self.assertIsNone(parse(current)['opaque_lookup']);self.assertEqual(restore(current,proof),source)
        self.assertEqual(proof['additions'][0]['index'],0)
        for additions in ([],[modern()]*9,None):
            with self.assertRaises(ValueError):build(source,additions)


if __name__=='__main__':unittest.main()
