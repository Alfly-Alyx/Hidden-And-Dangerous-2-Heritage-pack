"""Invented FPV prior lists, indices and expected native call arguments."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fpv_transition_oracle import reference,TransitionOracle,BLENDED,IMMEDIATE,END
from fpv_transition_audit import cases,audit


class TransitionTests(unittest.TestCase):
    def test_three_candidates_then_unchecked_fourth_slot(self):
        for previous,selected in (([],0),([0],1),([0,1],2),([0,1,2],3),([0,1,2,3],3),([1,2,3],0)):
            row=reference(359,0,0,previous,True)
            self.assertEqual(row['selected_slot'],selected)
            self.assertEqual(row['selected_slot_already_present'],selected in previous)

    def test_prior_order_does_not_change_choice(self):
        self.assertEqual(reference(359,0,0,[2,0,1],True),reference(359,0,0,[0,1,2],True))

    def test_high_prior_slots_do_not_consume_candidate_zero(self):
        self.assertEqual(reference(359,0,0,[3,4,5,6,7],True)['selected_slot'],0)

    def test_supplied_branch_initializes_distinct_weight_and_rate(self):
        for blended,weight,rate in ((True,0,5),(False,1,0)):
            row=reference(0,0,0,[],blended)
            self.assertEqual((row['weight'],row['rate'],row['mode_argument']),(weight,rate,0))

    def test_loaded_pointer_is_sixteen_bytes_before_resource_name(self):
        from item_native_layout import fpv_loaded_cell
        row=reference(499,12,3,[],False)
        self.assertEqual(row['clip_cache_member'],0xa0+499*624+12*48+3*4)
        self.assertEqual(row['clip_cache_member']+16,fpv_loaded_cell(599,2012,3)['name_member_offset'])

    def test_prior_list_not_modified(self):
        previous=[0,2,5];before=deepcopy(previous);reference(359,0,0,previous,True)
        self.assertEqual(previous,before)

    def test_invalid_domains_fail_closed(self):
        for args in ((-1,0,0,[],True),(500,0,0,[],True),(0,13,0,[],True),(0,0,4,[],True),
                     (True,0,0,[],True),(None,0,0,[],True),(0,0,0,[0,0],True),
                     (0,0,0,[8],True),(0,0,0,[True],True),(0,0,0,[],1)):
            with self.subTest(args=args),self.assertRaises(ValueError):reference(*args)

    def test_instruction_allowlist_excludes_prior_allocation_and_epilogue(self):
        machine=object.__new__(TransitionOracle);machine.active=True
        machine.on_code(None,BLENDED,4,None);machine.on_code(None,IMMEDIATE,4,None)
        for address,size in ((0x49319a,1),(0x41fc10,1),(END,1),(END-1,2),(BLENDED-1,1)):
            with self.assertRaises(ValueError):machine.on_code(None,address,size,None)

    def test_write_guard_keeps_prior_list_and_cache_immutable(self):
        machine=object.__new__(TransitionOracle);machine.active=True
        machine.writes=((machine.FPV+0x70,machine.FPV+0x80),)
        machine.on_write(None,None,machine.FPV+0x70,4,0,None)
        for address in (machine.HEAP,machine.INPUT,machine.FPV+0xa0):
            with self.assertRaises(ValueError):machine.on_write(None,None,address,4,0,None)

    def test_corpus_covers_all_256_prior_subsets_and_cache_boundaries(self):
        rows=list(cases());self.assertEqual(len(rows),848)
        self.assertEqual({tuple(row[3]) for row in rows[312:824]},
                         {tuple(i for i in range(8) if mask&(1<<i)) for mask in range(256)})
        for args in rows:reference(*args)

    def test_incomplete_receipts_are_not_native_proof(self):
        class Invalid:
            def prepare(self,*args):return reference(*args)
        with self.assertRaisesRegex(ValueError,'receipt'):audit(Invalid())

    def test_image_pin_checked_before_emulator_import(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed decompressed'):TransitionOracle(b'')


if __name__=='__main__':unittest.main()
