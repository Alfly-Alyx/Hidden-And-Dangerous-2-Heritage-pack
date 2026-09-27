"""Invented definition bytes and mock native receipts; no commercial fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_modern_audio_lab as lab
from sound_definition import parse,VARIANT_FIELDS
from sound_definition_additive import restore
from test_sound_definition import chunk,string,bank,entry


def template(kind):
    _,_,label,filename,parameters=lab.TEMPLATES[kind]
    variant=chunk(1300,string(1400,filename)+b''.join(chunk(k,struct.pack('<I',parameters[str(k)])) for k in VARIANT_FIELDS[1:]))
    return chunk(1200,string(1210,label)+chunk(1310,b'\0')+variant)


def definition():
    return chunk(1000,bank('First',entry('Invented',0))+bank('Empty',b'')+
        bank('Weapon Shooting',template('shot'))+
        bank('Weapon Manipulation',entry('Reserved A',0)+entry('Reserved B',0)+template('reload'))+
        chunk(1050,struct.pack('<II',123,456)))


class Machine:
    def lookup(self,bank,index,counts):
        return {'bank':bank,'index':index,'entry_present':0<=index<counts[bank],
                'native_synthetic_lookup_matches':True,'entry_sentinel_dereferenced':False}
    def append_order(self):return {'checks':[{'native_append_matches':True} for _ in range(12)]}


class ModernAudioLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=definition();cls.pin=('Patch.dta',len(cls.raw),lab.digest(cls.raw))
        cls.recipes={case:json.loads(path.read_text(encoding='utf-8')) for case,path in lab.RECIPES.items()}

    def prepare(self,*,recipes=None,machine=None):
        with patch.object(lab,'PIN',self.pin):
            return lab.prepare(self.raw,self.recipes if recipes is None else recipes,Machine() if machine is None else machine)

    def test_original_audio_and_reversible_table_are_separate_from_historical_symbols(self):
        files,report=self.prepare();self.assertEqual(len(files),5)
        self.assertTrue(all(name.endswith('.disabled') for name in files))
        self.assertEqual(restore(files['Tables/IngameSounds.def.disabled'],report['transaction']),self.raw)
        self.assertEqual([(r['bank'],r['index']) for r in report['transaction']['additions']],[(2,1),(3,3),(2,2),(3,4)])
        self.assertEqual(report['after_bank_counts'],[1,0,3,5]);self.assertEqual(len(report['native_numeric_lookup']),4)
        self.assertFalse(report['historic_fg42_symbols_resolved']);self.assertFalse(report['playback_executed'])
        self.assertFalse(report['native_complete_definition_loader_executed']);self.assertFalse(report['installation_allowed'])
        self.assertFalse(report['commercial_audio_exported']);self.assertTrue(report['source_definition_is_commercial_private_only'])
        for name,raw in files.items():self.assertEqual(report['files'][name],lab.fingerprint(raw))

    def test_changed_source_and_missing_or_swapped_recipes_refused(self):
        with self.assertRaises(ValueError):lab.prepare(self.raw, self.recipes,Machine())
        with self.assertRaises(ValueError):self.prepare(recipes={'FG42':self.recipes['FG42']})
        bad=deepcopy(self.recipes);bad['FG42']=bad['ZK383']
        with self.assertRaises(ValueError):self.prepare(recipes=bad)

    def test_category_parameters_are_pinned_even_with_matching_source_fingerprint(self):
        raw=self.raw.replace(b'G MP40\0',b'X MP40\0')
        with patch.object(lab,'PIN',('Patch.dta',len(raw),lab.digest(raw))):
            with self.assertRaisesRegex(ValueError,'category baseline'):lab.prepare(raw,self.recipes,Machine())

    def test_incomplete_native_receipts_are_refused(self):
        for receipt in ({'native_synthetic_lookup_matches':False,'entry_present':True},
                        {'native_synthetic_lookup_matches':True,'entry_present':False},{}):
            machine=Machine()
            with patch.object(machine,'lookup',return_value=receipt):
                with self.assertRaisesRegex(ValueError,'lookup receipt'):self.prepare(machine=machine)
        machine=Machine()
        with patch.object(machine,'append_order',return_value={'checks':[{'native_append_matches':True}]}):
            with self.assertRaisesRegex(ValueError,'append receipt'):self.prepare(machine=machine)

    def inventory(self,game,resources,**kwargs):
        class Archive:
            def __init__(self,path):
                self.rows=resources[path.name]
                self.entries=[SimpleNamespace(name=name,size=len(raw)) for name,raw in self.rows.items()]
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,entry):return self.rows[entry.name]
        with patch.object(lab,'PIN',self.pin),patch.object(lab,'DtaArchive',Archive):
            return lab.read_sources(game,**kwargs)

    def test_inventory_checks_all_root_archives_and_loose_definition_requires_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            game=Path(directory);(game/'Patch.dta').write_bytes(b'invented');(game/'missions.dta').write_bytes(b'invented')
            resources={'Patch.dta':{'Tables/IngameSounds.def':self.raw},'missions.dta':{'other/file.bin':b'data'}}
            raw,report=self.inventory(game,resources)
            self.assertEqual(raw,self.raw);self.assertEqual(len(report['archives']),2)
            self.assertEqual(report['archive_and_direct_loose_alias_conflicts'],[])
            (game/'Tables').mkdir();(game/'Tables/IngameSounds.def').write_bytes(b'personal override')
            with self.assertRaisesRegex(ValueError,'archive-only'):self.inventory(game,resources)
            _,report=self.inventory(game,resources,archives_only=True)
            self.assertEqual(report['excluded_loose_definition'],lab.fingerprint(b'personal override'))

    def test_archive_or_loose_alias_and_unreviewed_definition_provider_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            game=Path(directory);(game/'Patch.dta').write_bytes(b'invented')
            resources={'Patch.dta':{'Tables/IngameSounds.def':self.raw,'Sounds/mod_fg42_f.ogg':b'collision'}}
            with self.assertRaisesRegex(ValueError,'collision'):self.inventory(game,resources)
            resources['Patch.dta'].pop('Sounds/mod_fg42_f.ogg')
            (game/'Sounds').mkdir();(game/'Sounds/mod_zk383_r.WAV').write_bytes(b'collision')
            with self.assertRaisesRegex(ValueError,'collision'):self.inventory(game,resources)
        with tempfile.TemporaryDirectory() as directory:
            game=Path(directory);(game/'unknown.dta').write_bytes(b'invented')
            with self.assertRaisesRegex(ValueError,'provider'):
                self.inventory(game,{'unknown.dta':{'Tables/IngameSounds.def':self.raw}})


if __name__=='__main__':unittest.main()
