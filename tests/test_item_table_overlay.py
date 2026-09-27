"""Invented current-table snapshots; originals and modified records stay private."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import item_table_overlay as overlay
from item_table_additive import restore
from items_sav import parse
from test_item_table_additive import fixture,group
from test_item_table_oracle import valid_records
from test_items_sav import table as item_table
from test_fpv_table import table as fpv_table


def sources():
    _,fpv,descriptor,fragment=fixture()
    return {'items':valid_records(),'fpv':fpv},descriptor,fragment


def record(raw,slot):
    entry=parse(raw)['slots'][slot]
    return raw[entry['offset']:entry['offset']+entry['size']] if entry['present'] else None


def replace_record(raw,slot,replacement):
    slots=parse(raw)['slots']
    return item_table([replacement if entry['slot']==slot else
                       raw[entry['offset']:entry['offset']+entry['size']] if entry['present'] else None
                       for entry in slots])


def edited_weight(raw,slot=23):
    current=bytearray(record(raw,slot));struct.pack_into('<f',current,112,3.25)
    return replace_record(raw,slot,bytes(current))


class CentralTableCompositionTests(unittest.TestCase):
    def test_personal_item_and_animation_changes_survive_addition_and_exact_rollback(self):
        archive,descriptor,fragment=sources()
        current={'items':edited_weight(archive['items']),
                 'fpv':fpv_table(group(123)+group(109).replace(b'Invented0',b'Custom___')+group(299))}
        before=copy.deepcopy((archive,current,descriptor,fragment))
        changed,proof=overlay.compose(archive,current,descriptor,fragment,slot=359)
        self.assertEqual(restore(changed,proof['transaction']),current)
        self.assertEqual(proof['preexisting_changes']['items'][0]['slot'],23)
        self.assertEqual(proof['preexisting_changes']['items'][0]['change'],'modified')
        self.assertEqual([(x['group_id'],x['change']) for x in proof['preexisting_changes']['fpv_groups']],[(109,'modified'),(299,'added')])
        self.assertTrue(proof['preexisting_changes']['existing_fpv_group_order_changed'])
        self.assertEqual(record(changed['items'],23),record(current['items'],23))
        self.assertEqual(changed['fpv'][6:len(current['fpv'])],current['fpv'][6:])
        self.assertEqual((archive,current,descriptor,fragment),before)
        for key in ('other_resource_overrides_merged','global_id_reservation','installation_allowed','game_started','game_modified'):
            self.assertFalse(proof[key])

    def test_custom_removals_and_added_items_are_not_silently_replaced_with_archive_content(self):
        archive,descriptor,fragment=sources();raw=replace_record(archive['items'],400,None)
        raw=replace_record(raw,401,record(archive['items'],400))
        current={'items':raw,'fpv':fpv_table(group(123))}
        changed,proof=overlay.compose(archive,current,descriptor,fragment,slot=359)
        self.assertIsNone(record(changed['items'],400));self.assertIsNotNone(record(changed['items'],401))
        self.assertEqual([(r['slot'],r['change']) for r in proof['preexisting_changes']['items']],[(400,'removed'),(401,'added')])
        self.assertEqual(proof['preexisting_changes']['fpv_groups'][0]['change'],'removed')
        self.assertEqual(restore(changed,proof['transaction']),current)

    def test_missing_override_uses_only_the_corresponding_archive_snapshot(self):
        archive,descriptor,fragment=sources()
        for current in ({},{'items':edited_weight(archive['items'])},{'fpv':fpv_table(group(123))}):
            changed,proof=overlay.compose(archive,current,descriptor,fragment,slot=359)
            self.assertEqual(restore(changed,proof['transaction']),{**archive,**current})
            self.assertEqual(proof['selected_source'],{k:'installed_snapshot' if k in current else 'reviewed_archive' for k in archive})

    def test_modified_removed_or_retyped_ammunition_is_a_conflict_not_an_adopted_parameter(self):
        archive,descriptor,fragment=sources();ammo=bytearray(record(archive['items'],179))
        altered=bytearray(ammo);altered[176]^=1
        retyped=bytearray(ammo);struct.pack_into('<I',retyped,4,2)
        for replacement in (None,bytes(altered),bytes(retyped)):
            with self.subTest(replacement=replacement is None),self.assertRaisesRegex(ValueError,'ammunition differs'):
                overlay.compose(archive,{'items':replace_record(archive['items'],179,replacement)},descriptor,fragment,slot=359)

    def test_candidate_slot_and_fpv_owner_conflicts_are_refused(self):
        archive,descriptor,fragment=sources()
        for current,error in (({'items':replace_record(archive['items'],359,record(archive['items'],23))},'occupied'),
                              ({'fpv':fpv_table(group(109)+group(459))},'FPV owner')):
            with self.assertRaisesRegex(ValueError,error):overlay.compose(archive,current,descriptor,fragment,slot=359)

    def test_name_and_text_collisions_in_personal_records_are_refused(self):
        archive,descriptor,fragment=sources()
        for source,target,size,error in ((88,88,20,'internal name'),(108,108,4,'text ID')):
            custom=bytearray(record(archive['items'],400));custom[target:target+size]=descriptor[source:source+size]
            with self.assertRaisesRegex(ValueError,error):
                overlay.compose(archive,{'items':replace_record(archive['items'],400,bytes(custom))},descriptor,fragment,slot=359)

    def test_unreviewed_native_record_shape_and_fpv_shape_are_refused(self):
        archive,descriptor,fragment=sources();bad=bytearray(record(archive['items'],400))
        struct.pack_into('<I',bad,136,99)
        for current in ({'items':replace_record(archive['items'],400,bytes(bad))},
                        {'items':item_table([None]*255)}, {'fpv':fpv_table(group(109)+group(109))}):
            with self.assertRaises(ValueError):overlay.compose(archive,current,descriptor,fragment,slot=359)

    def test_unknown_keys_mutable_buffers_or_incomplete_archive_are_refused(self):
        archive,descriptor,fragment=sources()
        for current in (None,{'models':b'x'},{'items':bytearray(archive['items'])},{'fpv':None}):
            with self.assertRaisesRegex(ValueError,'snapshots'):overlay.compose(archive,current,descriptor,fragment,slot=359)
        with self.assertRaisesRegex(ValueError,'snapshots'):overlay.compose({'items':archive['items']},{},descriptor,fragment,slot=359)

    def test_rollback_does_not_discard_a_later_personal_edit(self):
        archive,descriptor,fragment=sources()
        changed,proof=overlay.compose(archive,{'items':edited_weight(archive['items'])},descriptor,fragment,slot=359)
        changed['items']=edited_weight(changed['items'],400)
        with self.assertRaisesRegex(ValueError,'result changed'):restore(changed,proof['transaction'])


class CentralSnapshotReadTests(unittest.TestCase):
    def test_only_fixed_central_paths_are_read_and_disappearance_or_change_is_refused(self):
        from reconstruction_sandbox import write_new
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp);(game/'Tables').mkdir();(game/'Models').mkdir()
            write_new(game/'Tables/items.sav',b'invented items')
            write_new(game/'Models/unrelated.4ds',b'not read')
            snapshot=overlay.read_overlays(game);self.assertEqual(snapshot,{'items':b'invented items'})
            overlay.require_unchanged_overlays(game,snapshot)
            with self.assertRaisesRegex(ValueError,'changed during'):overlay.require_unchanged_overlays(game,{'items':b'older'})
            write_new(game/'Tables/FpvAnims.sav',b'newly appeared')
            with self.assertRaisesRegex(ValueError,'changed during'):overlay.require_unchanged_overlays(game,snapshot)

    def test_directories_and_linked_sources_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp);(game/'Tables/items.sav').mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'regular file'):overlay.read_overlays(game)
            with patch('reconstruction_sandbox.normal',side_effect=ValueError('Linked source refused')):
                with self.assertRaisesRegex(ValueError,'Linked source'):overlay.read_overlays(game)


if __name__=='__main__':unittest.main()
