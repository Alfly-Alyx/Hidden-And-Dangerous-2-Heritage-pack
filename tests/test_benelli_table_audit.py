import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import benelli_table_audit as audit
from test_benelli_fpv_lab import MemoryArchive
from test_items_sav import invented_slot,table as item_table
from test_fpv_table import chunk,variant,state,table as fpv_table
from fpv_table import parse as parse_fpv


def benelli_table():
    return fpv_table(chunk(109,b''.join(state(2000+i,variant('#FPVBeneli'+name+'.I3D'))
                                     for i,name in enumerate(audit.EXPECTED_STATES)))
                     +chunk(359,state(2000,variant('fixture_other.I3D'))))


def fixture():
    tables={}
    for archive in ('others.DTA','Patch.dta','SabreSquadron.dta','PatchX01.dta'):
        slots=[None]*(255 if archive in ('others.DTA','Patch.dta') else 500)
        for n,kind,name in ((9,2,'KOMPAS'),(10,1,'M1 Garand'),(23,1,'Side by Side'),(179,0,'AMMO Beneli')):
            slots[n]=invented_slot(name=name,text_id=1000+n,kind=kind)
        tables[(archive,'tables/items.sav')]=item_table(slots)
    for archive in ('others.DTA','SabreSquadron.dta'):
        tables[(archive,'tables/fpvanims.sav')]=benelli_table()
    tables[('others.DTA','tables/item_shoot.tbl')]=b'fictional shoot record'
    tables[('SabreSquadron.dta','tables/item_base_items.tbl')]=b'fictional base item table'
    return tables


class CentralTableTests(unittest.TestCase):
    def inspect(self,tables,candidate=359):
        with patch.object(audit,'benelli_shoot_evidence',return_value={'header_ok':True,'sha256':audit.BENELLI_SHOOT_SHA256}),\
             patch.object(audit,'benelli_compass_evidence',return_value={'sha256':audit.BENELLI_COMPASS_SHA256}):
            return audit.inspect(tables,candidate,{})

    def test_base_limit_and_empty_sabre_slot_do_not_grant_allocation(self):
        report=self.inspect(fixture())
        self.assertEqual(report['item_tables']['others.DTA']['candidate']['status'],'outside_serialized_capacity')
        self.assertEqual(report['item_tables']['PatchX01.dta']['candidate']['status'],'serialized_empty')
        self.assertFalse(report['allocation_allowed']);self.assertFalse(report['saved_game_audit_included'])
        self.assertFalse(report['tables_modified']);self.assertEqual(report['last_reviewed_item_layer'],'PatchX01.dta')
        fpv=report['fpv_tables']['SabreSquadron.dta']
        self.assertTrue(fpv['same_numeric_group_as_candidate_present'])
        self.assertFalse(fpv['candidate_plus_100_group_present'])
        self.assertTrue(fpv['candidate_plus_100_is_binding_hypothesis_only'])

    def test_occupied_and_compass_slots_never_allocated(self):
        report=self.inspect(fixture(),9)
        self.assertEqual(report['item_tables']['PatchX01.dta']['candidate']['status'],'occupied')
        self.assertFalse(report['allocation_allowed'])
        for value in (True,-1,2**32):
            with self.assertRaises(ValueError):self.inspect(fixture(),value)

    def test_changed_reference_or_missing_benelli_group_refused(self):
        tables=fixture();key=('others.DTA','tables/items.sav')
        tables[key]=tables[key].replace(b'KOMPAS',b'WRONG!')
        with self.assertRaisesRegex(ValueError,'control changed'):self.inspect(tables)
        with self.assertRaisesRegex(ValueError,'Ambiguous'):audit.benelli_group(parse_fpv(fpv_table()))
        with self.assertRaisesRegex(ValueError,'associations'):
            audit.benelli_group(parse_fpv(benelli_table().replace(b'#FPVBeneliRel.I3D',b'#FPVBeneliXXX.I3D')))

    def test_fpv_duplicate_or_wrong_state_ids_refused(self):
        parsed=parse_fpv(benelli_table());parsed['groups'][0]['states'][0]['id']=2001
        with self.assertRaisesRegex(ValueError,'state IDs'):audit.benelli_group(parsed)
        parsed=parse_fpv(benelli_table());parsed['groups'].append(copy.deepcopy(parsed['groups'][0]))
        with self.assertRaisesRegex(ValueError,'Ambiguous'):audit.benelli_group(parsed)

    def read(self,game,tables,mutate=None,**kwargs):
        archives={a:[] for a in ('others.DTA','Patch.dta','SabreSquadron.dta','PatchX01.dta')}
        pins={}
        for (a,name),raw in tables.items():archives[a].append((name,raw));pins[(a,name)]=(len(raw),audit.sha(raw))
        if mutate:mutate(archives)
        with patch.object(audit,'TABLE_PINS',pins),\
             patch.object(audit,'DtaArchive',side_effect=lambda path:MemoryArchive(path,archives)):
            return audit.read_tables(game,**kwargs)

    def test_all_layers_including_patchx_are_read_without_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp);(game/'PatchX01.dta').touch()
            data,excluded=self.read(game,fixture())
            self.assertEqual(len(data),8);self.assertEqual(excluded,{})
            self.assertEqual(len(list(game.iterdir())),1)

    def test_loose_overrides_explicitly_excluded_not_called_effective(self):
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp);(game/'tables').mkdir();(game/'tables/items.sav').write_bytes(b'user data')
            with self.assertRaisesRegex(ValueError,'Loose'):self.read(game,fixture())
            data,excluded=self.read(game,fixture(),archives_only=True)
            self.assertEqual(len(data),7);self.assertIn('tables/items.sav',excluded)
            self.assertEqual((game/'tables/items.sav').read_bytes(),b'user data')

    def test_duplicate_unreviewed_and_modified_archive_tables_refused(self):
        def duplicate(arcs):arcs['Patch.dta'].append(('TABLES\\ITEMS.SAV',arcs['Patch.dta'][0][1]))
        def unreviewed(arcs):arcs['PatchX01.dta'].append(('tables/item_shoot.tbl',b'unknown'))
        def modified(arcs):arcs['Patch.dta'][0]=('tables/items.sav',b'changed')
        def missing(arcs):arcs['Patch.dta'].clear()
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp);(game/'PatchX01.dta').touch()
            for mutation in (duplicate,unreviewed,modified,missing):
                with self.subTest(mutation=mutation.__name__),self.assertRaises(ValueError):
                    self.read(game,fixture(),mutate=mutation)


if __name__=='__main__':unittest.main()
