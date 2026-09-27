"""Flat original visual hierarchy, no commercial models or game invocation."""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_modern_equipment_fpv_rig import compile_flat_rig,flatten_original
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms,point
from ls3d_frame_find_oracle import reference


class ModernFPVRigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases={case:compile_flat_rig(case) for case in ('F35','F2')}

    def test_real_existing_visual_root_and_all_children_are_directly_addressable(self):
        for case,(raw,_,report) in self.cases.items():
            nodes=parse_4ds_nodes(raw)['nodes']
            self.assertEqual(len(nodes),38 if case=='F35' else 36)
            self.assertEqual((nodes[0]['name'],nodes[0]['frame_type'],nodes[0]['visual_type']),('fpv_weapon',1,2))
            self.assertEqual(nodes[0]['parent_id'],0)
            self.assertTrue(all(n['parent_id']==1 for n in nodes[1:]))
            self.assertFalse(report['old_animation_banks_compatible'])
            self.assertFalse(report['engine_validated'])

    def test_payloads_and_every_rest_world_transform_are_preserved(self):
        for flat,original,report in self.cases.values():
            before=parse_4ds_nodes(original)['nodes'];after=parse_4ds_nodes(flat)['nodes']
            source_world=world_transforms(original,before);flat_world=world_transforms(flat,after)
            by_name={n['name']:n for n in after}
            for old in before[1:]:
                new=by_name[report['source_to_fpv_names'][old['name']]]
                self.assertEqual(original[old['name_offset']+old['name_length']:old['end']],
                    flat[new['name_offset']+new['name_length']:new['end']])
                for vertex in ((0,0,0),(.2,.5,-.3),(-.1,.07,.4)):
                    for a,b in zip(point(source_world[old['index']],vertex),point(flat_world[new['index']],vertex)):
                        self.assertAlmostEqual(a,b,places=7)

    def test_visual_query_matches_without_adding_fake_magazine(self):
        for flat,_,_ in self.cases.values():
            nodes=parse_4ds_nodes(flat)['nodes']
            tree=[{'name':n['name'],'frame_type':n['frame_type'],'parent':n['parent_id']-1} for n in nodes]
            self.assertEqual(reference(tree,'fpv_weapon')['direct_children'],list(range(1,len(nodes))))
            self.assertIsNone(reference(tree,'magazine',0x21)['index'])

    def test_altered_rotation_origin_scale_and_non_original_names_are_refused(self):
        original=self.cases['F35'][1];nodes=parse_4ds_nodes(original)['nodes']
        mutations=[]
        for offset,values in ((nodes[1]['position_offset']+12,[0,0,1,0]),
                              (nodes[0]['position_offset'],[1,0,0]),
                              (nodes[1]['position_offset']+28,[2,1,1])):
            raw=bytearray(original);struct.pack_into('<'+'f'*len(values),raw,offset,*values);mutations.append(bytes(raw))
        raw=bytearray(original);raw[nodes[1]['name_offset']]=ord('X');mutations.append(bytes(raw))
        for raw in mutations:
            with self.assertRaises(ValueError):flatten_original(raw)


if __name__=='__main__':unittest.main()
