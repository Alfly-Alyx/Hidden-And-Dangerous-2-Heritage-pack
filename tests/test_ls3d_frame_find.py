"""Synthetic scene-name/type/tree contract, no commercial frame data."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_frame_find_oracle import reference


def node(name,kind=1,parent=-1):return {'name':name,'frame_type':kind,'parent':parent}


class FrameFindReferenceTests(unittest.TestCase):
    def test_visual_filter_skips_dummy_alias_and_finds_nested_visual(self):
        tree=[node('fpv_weapon',6),node('fpv_weapon',1,0),node('child',1,1)]
        self.assertEqual(reference(tree,'fpv_weapon',1),{'index':1,'direct_children':[2]})
        self.assertEqual(reference(tree,'fpv_weapon',0x21),{'index':0,'direct_children':[1]})

    def test_visual_only_lookup_does_not_accept_same_named_dummy(self):
        self.assertIsNone(reference([node('fpv_weapon',6)],'fpv_weapon',1)['index'])
        self.assertEqual(reference([node('magazine',6)],'magazine',0x21)['index'],0)

    def test_depth_first_match_and_direct_children_are_distinct(self):
        tree=[node('root'),node('branch',6,0),node('target',1,1),node('target',1,0),node('leaf',10,2)]
        self.assertEqual(reference(tree,'target'),{'index':2,'direct_children':[4]})
        self.assertEqual(reference(tree,'root')['direct_children'],[1,3])

    def test_default_ascii_lookup_is_case_insensitive_unlike_clip_binding(self):
        tree=[node('FPV_Weapon')]
        self.assertEqual(reference(tree,'fpv_weapon')['index'],0)
        self.assertIsNone(reference(tree,'fpv_weapon',0x20001)['index'])
        self.assertEqual(reference(tree,'FPV_Weapon',0x20001)['index'],0)

    def test_unsupported_flags_wildcards_kinds_and_bad_parent_refused(self):
        for flags in (True,0,2,0x10001):
            with self.assertRaises(ValueError):reference([node('x')],'x',flags)
        for name in ('*','x?','x\0','é'):
            with self.assertRaises(ValueError):reference([node('x')],name)
        for tree in ([node('x',1,0)],[node('x',True)],[node('x',2)],[]):
            with self.assertRaises(ValueError):reference(tree,'x')


if __name__=='__main__':unittest.main()
