import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from custom_mission_packages import TEXT_ID_START,TEXT_ID_END
import texty_additive as codec
import build_modern_inventory_text_lab as lab


def catalogue():return json.loads(lab.CATALOGUE.read_text(encoding='utf-8'))
def labels():return codec.validate(catalogue(),mission_range=(TEXT_ID_START,TEXT_ID_END))


class ModernInventoryTextTests(unittest.TestCase):
    def test_actual_catalogue_is_outside_creator_and_menu_reservations(self):
        rows=labels();self.assertEqual([r['text_id'] for r in rows],[21500,21501])
        tree=ast.parse((ROOT/'tools/build_static_custom_menu.py').read_text(encoding='utf-8'))
        values=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
                    and any(isinstance(t,ast.Name) and t.id=='CUSTOM_TEXT_IDS' for t in node.targets))
        self.assertFalse(set(values)&set(range(21500,21532)))
        self.assertEqual(set(rows[0]['values']),set(codec.ENCODINGS))

    def test_original_bytes_duplicates_comments_and_newlines_are_preserved(self):
        raw=b'; existing user content\r\n1\t"Original"\r\n1\t"Duplicate retained"\r\n'
        result,proof=codec.append_labels(raw,labels(),'french')
        self.assertTrue(result.startswith(raw))
        self.assertIn(b'21500\t"Benelli M4 [MODERNE]"\r\n',result)
        self.assertEqual(codec.remove_append(result,proof),raw)
        self.assertEqual(proof['newline_hex'],'0d0a')
        self.assertFalse(proof['native_text_loader_qualified'])

    def test_single_line_lf_cr_and_bom_are_not_normalized(self):
        for raw in (b'1 "Old"',b'1 "Old"\n',b'1 "Old"\r',b'\xef\xbb\xbf1 "Old"\n',b''):
            result,proof=codec.append_labels(raw,labels(),'english')
            self.assertTrue(result.startswith(raw))
            self.assertEqual(codec.remove_append(result,proof),raw)
        raw=b'\xef\xbb\xbf1 "Old"\n';result,_=codec.append_labels(raw,labels(),'japan')
        self.assertEqual(result.count(b'\xef\xbb\xbf'),1)

    def test_czech_encoding_is_explicit_and_existing_bytes_are_opaque(self):
        raw=b'; private legacy byte \x81\r\n'
        result,proof=codec.append_labels(raw,labels(),'czech')
        self.assertIn('Benelli M4 [MODERNÍ]'.encode('cp1250'),result)
        self.assertEqual(proof['encoding'],'cp1250')
        self.assertEqual(result[:len(raw)],raw)

    def test_conservative_collision_scan_includes_other_languages_and_comments(self):
        for raw in (b'21500 "Existing"',b'; future 21500 reservation',b'text X21500Y'):
            with self.assertRaises(ValueError):codec.collision_check({'OtherLanguage':raw},[21500])
        codec.collision_check({'No collision':b'121500 215001'},[21500])
        with self.assertRaises(ValueError):codec.collision_check({},[21500])
        with self.assertRaises(ValueError):codec.collision_check({'binary':b'\0'},[21500])

    def test_invalid_catalogues_and_encoding_or_quote_injection_are_refused(self):
        for key,value in (('status','active'),('provenance','ORIGINAL'),('schema_version',True),
                          ('project_reservation',[21500.0,21531.0])):
            data=catalogue();data[key]=value
            with self.assertRaises(ValueError):codec.validate(data,mission_range=(22000,65000))
        for value in ('No modern marker','Bad "quote [MODERN]','Bad\\escape [MODERN]',
                      'Bad\nline [MODERN]','☃ [MODERN]','x'*80+' [MODERN]'):
            data=catalogue();data['labels'][0]['values']['french']=value
            with self.subTest(value=value),self.assertRaises(ValueError):codec.validate(data,mission_range=(22000,65000))
        for number in (True,21499,22000):
            data=catalogue();data['labels'][0]['text_id']=number
            with self.assertRaises(ValueError):codec.validate(data,mission_range=(22000,65000))
        data=catalogue();data['labels']*=2
        with self.assertRaises(ValueError):codec.validate(data,mission_range=(22000,65000))

    def test_changed_creator_reservation_blocks_modern_range(self):
        for reserved in ((21000,65000),(21531,65000),(0,21500)):
            with self.assertRaisesRegex(ValueError,'overlaps'):codec.validate(catalogue(),mission_range=reserved)

    def test_unclear_final_boundary_and_binary_input_are_refused(self):
        for raw in (b'1 "unfinished',b'continuation"',b'\xff\xfe1\0',bytearray(b'1 "Old"')):
            with self.assertRaises(ValueError):codec.append_labels(raw,labels(),'english')
        with self.assertRaises(ValueError):codec.append_labels(b'',labels()*2,'english')
        with self.assertRaises(ValueError):codec.append_labels(b'',labels(),'unknown')

    def test_reversal_does_not_erase_later_edits_or_accept_broken_proof(self):
        raw=b'1 "Original"\n';result,proof=codec.append_labels(raw,labels(),'english')
        for changed in (result+b'2 "Later"\n',result.replace(b'Original',b'Modified')):
            with self.assertRaises(ValueError):codec.remove_append(changed,proof)
        for key,value in (('original_size',-1),('original_size',True),('addition_size',0),('original_sha256','wrong')):
            broken={**proof,key:value}
            with self.assertRaises(ValueError):codec.remove_append(result,broken)

    def test_all_installed_languages_prepare_disabled_outputs_with_exact_reverse(self):
        sources={f'Text/{language}/TEXTY_DD.txt':b'1 "Existing"\n' for language in codec.ENCODINGS}
        sources['Text/english/TEXTY.txt']=b'1009 "Compass"\n'
        before=copy.deepcopy(sources)
        outputs,report=lab.prepare(catalogue(),sources,occupied_item_text_ids={1009,1179},mission_range=(22000,65000))
        self.assertEqual(len(outputs),8)
        self.assertEqual(report['source_tables_checked'],9)
        self.assertFalse(report['game_modified']);self.assertFalse(report['global_text_id_freedom_qualified'])
        for name,data in outputs.items():
            self.assertTrue(name.endswith('.disabled'));source=name.removesuffix('.disabled')
            self.assertEqual(codec.remove_append(data,report['proofs'][source]),sources[source])
        self.assertEqual(sources,before)

    def test_item_reference_and_unreviewed_languages_or_paths_block_preparation(self):
        sources={'Text/french/TEXTY_DD.txt':b'1 "Old"\n'}
        with self.assertRaisesRegex(ValueError,'referenced by an item'):
            lab.prepare(catalogue(),sources,occupied_item_text_ids={21500},mission_range=(22000,65000))
        for path in ('Text/unknown/TEXTY_DD.txt','Text/../TEXTY_DD.txt','Text/french/deep/TEXTY_DD.txt'):
            with self.assertRaises(ValueError):lab.prepare(catalogue(),{path:b''},occupied_item_text_ids=set(),mission_range=(22000,65000))

    def test_reader_and_output_paths_do_not_follow_links_or_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaises(ValueError):lab.read_text_sources(root)
            folder=root/'Text/english';folder.mkdir(parents=True)
            (folder/'TEXTY_DD.txt').write_bytes(b'1 "Fixture"\n')
            self.assertEqual(lab.read_text_sources(root),{'Text/english/TEXTY_DD.txt':b'1 "Fixture"\n'})
            output=lab.output_directory('Fixture_v1',root);self.assertFalse(output.exists())
            output.mkdir(parents=True)
            with self.assertRaises(ValueError):lab.output_directory('Fixture_v1',root)
            for name in ('../escape','NUL','',None,'a/b'):
                with self.assertRaises(ValueError):lab.output_directory(name,root)
            with patch.object(lab,'linked',return_value=True):
                with self.assertRaises(ValueError):lab.read_text_sources(root)
                with self.assertRaises(ValueError):lab.output_directory('Other',root)


if __name__=='__main__':unittest.main()
