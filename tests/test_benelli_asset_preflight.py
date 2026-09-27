"""Invented archive indices and loose files; no commercial assets distributed."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import benelli_asset_preflight as preflight
from reconstruction_sandbox import write_new

SOURCES={'models/#clip.4ds','models/#clip.5ds','maps/weapon.bmp','maps_u/sleeve.bmp',
         'sounds/fire.wav','tables/ingamesounds.def','tables/fpvanims.sav','tables/item_shoot.tbl'}


class Archive:
    def __init__(self,rows):
        self.rows=rows;self.entries=[SimpleNamespace(name=name,size=len(raw),index=i) for i,(name,raw) in enumerate(rows)]
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,entry):return self.rows[entry.index][1]


class AssetClassificationTests(unittest.TestCase):
    def test_modern_aliases_cover_case_slashes_and_three_loader_extensions(self):
        for name in ('Models/PROTOTYPE_BenFPV.4ds','models\\prototype_benm4.I3D','models/PROTOTYPE_BenFPV.5ds'):
            self.assertEqual(preflight.classify(name,SOURCES),'modern_model_alias_collision')
        for name in ('models/PROTOTYPE_BenFPV_extra.4ds','models/PROTOTYPE_BenFPV.txt','backup/models/PROTOTYPE_BenFPV.4ds'):
            self.assertIsNone(preflight.classify(name,SOURCES))

    def test_compressed_variants_and_cross_namespace_texture_candidates_are_not_silently_selected(self):
        for name in ('maps/weapon_1.dx1','Maps_C/weapon_8.DX1','maps_u/weapon.bmp','maps/sleeve_1l.dx1'):
            self.assertEqual(preflight.classify(name,SOURCES),'texture_resolution_neighbor')
        self.assertEqual(preflight.classify('models/#clip.I3D',SOURCES),'model_resolution_neighbor')
        self.assertIsNone(preflight.classify('maps/weaponized.bmp',SOURCES))

    def test_current_central_tables_are_handled_elsewhere_but_sound_definitions_remain_protected(self):
        for name in ('Tables/items.sav','Tables/FpvAnims.sav','Tables/item_shoot.tbl'):
            self.assertIsNone(preflight.classify(name,SOURCES))
        for name in ('tables/ingamesounds.def','sounds/fire.wav','models/#clip.4ds'):
            self.assertEqual(preflight.classify(name,SOURCES),'pinned_resource_path')


class AssetInventoryTests(unittest.TestCase):
    def inspect(self,archives,loose=None):
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp)
            for name in archives:write_new(game/name,b'Invented archive index')
            for name,raw in (loose or {}).items():
                path=game/name;path.parent.mkdir(parents=True,exist_ok=True);write_new(path,raw)
            with patch.object(preflight,'DtaArchive',side_effect=lambda path:Archive(archives[path.name])):
                return preflight.inventory(game,SOURCES)

    def test_reviewed_archives_are_indexed_and_neighbors_reported_without_qualifying_native_resolution(self):
        report=self.inspect({'models.dta':[('models/#clip.4ds',b'model'),('models/#clip.5ds',b'motion')],
                             'Maps.dta':[('maps/weapon.bmp',b'bmp'),('maps/weapon_1.dx1',b'dx1')]},
                            {'Tables/items.sav':b'current table','Models/unrelated.4ds':b'ignored'})
        self.assertTrue(report['no_candidate_collisions']);self.assertEqual(len(report['archives']),2)
        self.assertEqual(len(report['archive_resources']),4)
        for key in ('native_search_order_qualified','compressed_texture_choice_qualified',
                    'global_id_reservation','installation_allowed','game_started','game_modified'):
            self.assertFalse(report[key])
        self.assertFalse(report['archives'][0]['index_hash_is_full_archive_hash'])

    def test_modern_alias_in_any_archive_is_a_collision_even_when_geometry_is_identical(self):
        report=self.inspect({'models.dta':[('models/PROTOTYPE_BenFPV.5ds',b'invented')]})
        self.assertFalse(report['no_candidate_collisions']);self.assertEqual(len(report['archive_modern_alias_collisions']),1)

    def test_loose_exact_and_neighbor_resources_are_recorded_with_hashes_and_not_overwritten(self):
        for name in ('Models/PROTOTYPE_BenM4.4ds','Models/#clip.I3D','Maps_U/weapon_8.dx1','Sounds/fire.wav'):
            with self.subTest(name=name):
                report=self.inspect({'models.dta':[]},{name:b'personal bytes'})
                self.assertFalse(report['no_candidate_collisions'])
                self.assertEqual(report['loose_asset_candidates'][0]['sha256'],preflight.fingerprint(b'personal bytes')['sha256'])

    def test_related_resource_in_an_unreviewed_archive_is_not_ignored(self):
        report=self.inspect({'extra.dta':[('models/#clip.4ds',b'shadow')]})
        self.assertFalse(report['no_candidate_collisions']);self.assertEqual(len(report['unexpected_archive_providers']),1)

    def test_duplicate_relevant_entries_no_archive_and_unreadable_archive_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'Duplicate relevant'):
            self.inspect({'models.dta':[('models/#clip.4ds',b'a'),('MODELS/#CLIP.4DS',b'b')]})
        with self.assertRaisesRegex(ValueError,'No root'):self.inspect({})
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp);write_new(game/'models.dta',b'invented')
            with patch.object(preflight,'DtaArchive',side_effect=ValueError('unreadable')):
                with self.assertRaisesRegex(ValueError,'unreadable'):preflight.inventory(game,SOURCES)


if __name__=='__main__':unittest.main()
