"""Invented two-bone fixture; inverse binds are hand-calculated constants."""
import math
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from four_ds_skin import audit_rest,read_reviewed
from menu_gui_audit import parse_4ds_nodes
from test_model_instance import mesh,model


def fixture():
    # Bone 1 appears first in node order: native Z+90 means active Z-90.
    root=bytearray(mesh('Skin'));root[1]=2
    bbox=bytes(32)
    # Joint A: Rz(-90), translation (1,0,0). Joint B: same R, t=(1,-1,0).
    # Stored column-major inverse: Rz(+90), t=(0,-1,0) / (-1,-1,0).
    def inverse(tx):return struct.pack('<16f',0,1,0,0,-1,0,0,0,0,0,1,0,tx,-1,0,1)
    # Inverse B translation is (-R^-1 * (1,-1,0)) = (-1,-1,0).
    skin=bytes([2])+bbox+bytes([2,0])+inverse(-1)+bbox+inverse(0)+bbox
    skin+=struct.pack('<I',3)+bytes([1,0,2,128,1,255])
    def joint(name,parent,position,q,bone):
        return (struct.pack('<BH3f4f3f',10,parent,*position,*q,1,1,1)+bytes(5)
                +bytes([len(name)])+name.encode()+b'\0'+struct.pack('<I',bone))
    return model(bytes(root)+skin,
                 joint('A',1,[1,0,0],[0,0,math.sqrt(.5),math.sqrt(.5)],1),
                 joint('B',2,[1,0,0],[0,0,0,1],0))


class SkinRestTests(unittest.TestCase):
    def test_independent_inverse_binds_and_nonordinal_bone_ids(self):
        report=audit_rest(fixture())
        self.assertEqual((report['bones'],report['vertices'],report['triangles']),(2,3,1))
        self.assertLess(report['inverse_bind_max_identity_error'],1e-6)
        self.assertTrue(report['parent_bytes_verified'])
        for key in ('weight_byte_semantics_qualified','skin_deformation_qualified','engine_validated','geometry_exported'):
            self.assertFalse(report[key])

    def test_opposite_quaternion_fails_independent_matrix_proof(self):
        data=bytearray(fixture());node=parse_4ds_nodes(data)['nodes'][1]
        struct.pack_into('<f',data,node['position_offset']+20,-math.sqrt(.5))
        with self.assertRaisesRegex(ValueError,'Inverse bind'):audit_rest(bytes(data))

    def test_duplicate_bone_and_wrong_parent_bytes_are_rejected(self):
        original=fixture();nodes=parse_4ds_nodes(original)['nodes']
        data=bytearray(original);struct.pack_into('<I',data,nodes[2]['end']-4,1)
        with self.assertRaisesRegex(ValueError,'bone ID'):audit_rest(bytes(data))
        data=bytearray(original);skin_start=len(mesh('Skin'))+nodes[0]['start']
        data[skin_start+33]=0
        with self.assertRaisesRegex(ValueError,'parent byte'):audit_rest(bytes(data))

    def test_weight_index_nonfinite_and_mismatched_inverse_are_rejected(self):
        original=fixture();root=parse_4ds_nodes(original)['nodes'][0]
        start=len(mesh('Skin'))+root['start'];matrix=start+35
        changes=[(root['end']-6,b'\x03','weight bone'),
                 (root['end']-6,b'\x00','weight bone'),
                 (matrix,struct.pack('<f',math.nan),'Nonfinite'),
                 (matrix+12,struct.pack('<f',1),'homogeneous'),
                 (matrix+48,struct.pack('<f',2),'Inverse bind')]
        for at,raw,message in changes:
            data=bytearray(original);data[at:at+len(raw)]=raw
            with self.subTest(message=message),self.assertRaisesRegex(ValueError,message):audit_rest(bytes(data))

    def test_unreviewed_domain_and_truncation_refused(self):
        original=fixture();node=parse_4ds_nodes(original)['nodes'][0]
        data=bytearray(original);struct.pack_into('<f',data,node['position_offset'],1)
        with self.assertRaisesRegex(ValueError,'identity skin root'):audit_rest(bytes(data))
        with self.assertRaises(ValueError):audit_rest(original[:-1])

    def test_face_groups_are_opt_in_and_do_not_change_default_data(self):
        normal=read_reviewed(fixture());with_faces=read_reviewed(fixture(),include_faces=True)
        self.assertNotIn('face_groups',normal)
        faces=with_faces.pop('face_groups');self.assertEqual(with_faces,normal)
        self.assertEqual(faces,[{'material':1,'triangles':[[0,1,2]]}])
        for option in (None,1,'yes'):
            with self.assertRaises(ValueError):read_reviewed(fixture(),include_faces=option)


if __name__=='__main__':unittest.main()
