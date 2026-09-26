from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from benelli_fpv_static import derive,geometry,NAMES
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms,compose,invert,node_transform
from test_model_instance import mesh,model


def anchor(name,parent=1):
    return (struct.pack('<BH',6,parent)+struct.pack('<3f4f3f',0,0,0,0,0,0,1,1,1,1)
            +bytes(5)+bytes([len(name)])+name.encode()+b'\0'+bytes(32))


def source():
    data=model(mesh('fpv_weapon'),mesh('gunlock',parent=1),mesh('cock',parent=1),
               anchor('blsdum'),anchor('cardum'),anchor('shdum'),mesh('shell01',parent=1),anchor('magazine',0))
    nodes=parse_4ds_nodes(data)['nodes']
    data=bytearray(data)
    struct.pack_into('<3f4f3f',data,nodes[0]['position_offset'],3,4,5,0,1,0,0,1,1,1)
    struct.pack_into('<3f',data,nodes[-1]['position_offset'],3.1,4.2,5.3)
    data[-1]=1
    return bytes(data)


class StaticFpvTests(unittest.TestCase):
    def test_eight_nodes_materials_and_geometry_kept_but_not_companion_animation(self):
        raw=source(); out,proof=derive(raw)
        old,new=parse_4ds_nodes(raw),parse_4ds_nodes(out)
        self.assertTrue(proof['material_bytes_preserved'])
        self.assertFalse(proof['playable_weapon'])
        self.assertEqual(proof['provenance'],'DERIVE_DU_JEU')
        self.assertEqual(new['has_animation'],0)
        for a,b in zip(old['nodes'],new['nodes']):
            self.assertEqual(a['name'],b['name'])
            start1=a['name_offset']+a['name_length']; start2=b['name_offset']+b['name_length']
            self.assertEqual(raw[start1:a['end']],out[start2:b['end']])
        self.assertEqual(new['nodes'][0]['position'],[0,0,0])
        self.assertEqual(new['nodes'][0]['scale'],[1,1,1])

    def test_root_rebase_preserves_relative_world_placements(self):
        raw=source(); out,_=derive(raw)
        old,new=parse_4ds_nodes(raw)['nodes'],parse_4ds_nodes(out)['nodes']
        old_world=world_transforms(raw,old); new_world=world_transforms(out,new)
        inv=invert(node_transform(raw,old[0]))
        for before,after in zip(old,new):
            expected=compose(inv,old_world[before['index']]); actual=new_world[after['index']]
            for a,b in zip(expected[1],actual[1]): self.assertAlmostEqual(a,b,places=6)
            for row_a,row_b in zip(expected[0],actual[0]):
                for a,b in zip(row_a,row_b): self.assertAlmostEqual(a,b,places=6)

    def test_geometry_composes_hierarchy_and_has_no_removed_arm_vertices(self):
        out,_=derive(source()); v,f,n=geometry(out)
        self.assertEqual(len(v),12); self.assertEqual(len(f),4)
        self.assertEqual(set(n),NAMES)

    def test_missing_duplicate_or_wrong_owner_refused(self):
        raw=source(); nodes=parse_4ds_nodes(raw)['nodes']
        for changed in (raw.replace(b'gunlock',b'missing'),raw.replace(b'gunlock',b'shell01')):
            with self.assertRaises(ValueError): derive(changed)
        damaged=bytearray(raw)
        struct.pack_into('<H',damaged,nodes[1]['parent_offset'],8)
        with self.assertRaisesRegex(ValueError,'child ownership'): derive(bytes(damaged))

    def test_deterministic_derived_asset(self):
        self.assertEqual(derive(source()),derive(source()))


if __name__=='__main__': unittest.main()
