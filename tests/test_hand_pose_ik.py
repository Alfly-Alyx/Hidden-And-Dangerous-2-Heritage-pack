"""Modern analytic hand targeting: synthetic numbers, no commercial geometry."""
import math
from copy import deepcopy
import struct
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from hand_pose_ik import two_bone,shortest_rotation,bend_plane_rotation,norm,sub,validate_basis,pinned_skin,finger_curls,finger_splay
from model_transform import matvec,determinant
import hand_pose_ik as ik


class HandIKTests(unittest.TestCase):
    def test_optional_digit_choices_are_absolute_and_detached(self):
        source={'finger_curl_degrees':[60,45,20],'finger_curl_overrides':{'1':[10,15,5],'4':[55,30,10]}}
        result=finger_curls(source)
        self.assertEqual(result,{'1':[10,15,5],'2':[60,45,20],'3':[60,45,20],'4':[55,30,10]})
        result['1'][0]=90;result['2'][0]=90
        self.assertEqual(source['finger_curl_overrides']['1'],[10,15,5])
        self.assertEqual(source['finger_curl_degrees'],[60,45,20]);self.assertEqual(result['3'],[60,45,20])
        self.assertEqual(finger_curls({'finger_curl_degrees':[-60,-45,-20]}),{str(i):[-60,-45,-20] for i in range(1,5)})

    def test_digit_choice_refuses_thumb_unknown_keys_and_invalid_angles(self):
        for overrides in ({},{'0':[1,2,3]},{'5':[1,2,3]},{1:[1,2,3]},[],
                          {'1':[True,0,0]},{'1':[float('nan'),0,0]},{'4':[111,0,0]},{'1':[1,2]}):
            with self.assertRaises(ValueError):finger_curls({'finger_curl_degrees':[0,0,0],'finger_curl_overrides':overrides})
        for value in ({},None,{'finger_curl_degrees':[0,0,0],'other':0},{'finger_curl_degrees':[0,float('inf'),0]}):
            with self.assertRaises(ValueError):finger_curls(value)

    def test_optional_splay_refuses_thumb_overrotation_and_nonfinite_values(self):
        self.assertEqual(finger_splay({}),{str(i):0 for i in range(1,5)})
        self.assertEqual(finger_splay({'finger_splay_degrees':{'1':15,'4':-20}}),{'1':15,'2':0,'3':0,'4':-20})
        for value in ({},{'0':10},{'5':10},{1:10},[],{'1':31},{'1':True},{'4':float('nan')}):
            with self.assertRaises(ValueError):finger_splay({'finger_splay_degrees':value})
        with self.assertRaises(ValueError):finger_splay(None)

    def test_authored_digit_changes_only_its_three_local_rotations_on_invented_skeleton(self):
        from model_transform import world_transforms
        raw=bytes(12)+struct.pack('<4f',0,0,0,1);nodes=[]
        def add(name,parent,position):
            index=len(nodes)+1
            nodes.append({'name':name,'index':index,'parent_id':parent,'position':position,
                          'position_offset':0,'scale':[1,1,1]})
            return index
        root=add('a',0,[0,0,0])
        for side,sign in (('L',-1),('R',1)):
            upper=add('Bip01 '+side+' UpperArm',root,[sign*.15,0,0])
            fore=add('Bip01 '+side+' Forearm',upper,[sign*.2,0,0])
            hand=add('Bip01 '+side+' Hand',fore,[sign*.2,0,0])
            for digit in range(5):
                parent=hand
                for segment in range(2 if digit==0 else 3):
                    name=f'Bip01 {side} Finger{digit}'+('' if segment==0 else str(segment))
                    parent=add(name,parent,[sign*.025,.01*digit if segment==0 else 0,0])
        skin={'nodes':nodes,'rest_world':world_transforms(raw,nodes)}
        targets={s:{'position':[sign*.4,.1,.08],'rotation':[[1,0,0],[0,1,0],[0,0,1]],
                    'pole':[sign*.3,-.25,0]} for s,sign in (('L',-1),('R',1))}
        normal={s:{'finger_curl_degrees':[25,20,10]} for s in ('L','R')}
        changed=deepcopy(normal);changed['R']['finger_curl_overrides']={'4':[35,40,15]}
        spread=deepcopy(normal);spread['R']['finger_splay_degrees']={'1':15}
        zero=deepcopy(normal);zero['R']['finger_splay_degrees']={'1':0}
        with patch.object(ik,'pinned_skin',return_value=('invented',skin)):
            a,_=ik.author_pose(raw,targets,normal,arm_rotation_policy='bend_plane')
            b,_=ik.author_pose(raw,targets,changed,arm_rotation_policy='bend_plane')
            c,_=ik.author_pose(raw,targets,spread,arm_rotation_policy='bend_plane')
            d,_=ik.author_pose(raw,targets,zero,arm_rotation_policy='bend_plane')
        expected={'Bip01 R Finger4','Bip01 R Finger41','Bip01 R Finger42'}
        self.assertEqual({name for name in a if a[name]!=b[name]},expected)
        self.assertEqual({name for name in a if a[name]!=c[name]},{'Bip01 R Finger1'})
        self.assertEqual(a,d)
        for name in a:
            for key in ('position','scale'):
                self.assertEqual(a[name][key],b[name][key]);self.assertEqual(a[name][key],c[name][key])

    def test_both_lengths_and_pole_side_are_preserved(self):
        elbow=two_bone([0,0,0],[0,.4,0],[1,0,0],.3,.25)
        self.assertAlmostEqual(norm(elbow),.3)
        self.assertAlmostEqual(norm(sub(elbow,[0,.4,0])),.25);self.assertGreater(elbow[0],0)

    def test_mirrored_poles_produce_mirrored_elbows(self):
        a=two_bone([0,0,0],[0,.4,0],[1,0,0],.3,.25)
        b=two_bone([0,0,0],[0,.4,0],[-1,0,0],.3,.25)
        self.assertAlmostEqual(a[0],-b[0]);self.assertEqual(a[1:],b[1:])

    def test_unreachable_or_singular_targets_never_stretch(self):
        for target in ([0,1,0],[0,.55,0],[0,0,0],[0,.01,0]):
            with self.assertRaises(ValueError):two_bone([0,0,0],target,[1,0,0],.3,.25)
        with self.assertRaises(ValueError):two_bone([0,0,0],[0,.4,0],[0,1,0],.3,.25)

    def test_invalid_vectors_lengths_and_booleans_refused(self):
        for length in (True,0,3,float('nan')):
            with self.assertRaises(ValueError):two_bone([0,0,0],[0,.4,0],[1,0,0],length,.25)
        for target in ([0,math.inf,0],[True,.4,0],[0,.4]):
            with self.assertRaises(ValueError):two_bone([0,0,0],target,[1,0,0],.3,.25)

    def test_shortest_rotation_regular_parallel_and_antiparallel(self):
        for target in ([0,1,0],[1,0,0],[-1,0,0],[0,0,-1]):
            matrix=shortest_rotation([1,0,0],target);actual=matvec(matrix,[1,0,0])
            for a,b in zip(actual,target):self.assertAlmostEqual(a,b)
            self.assertAlmostEqual(determinant(matrix),1)

    def test_orientation_rejects_scale_reflection_and_bad_shape(self):
        for matrix in ([[2,0,0],[0,1,0],[0,0,1]],[[-1,0,0],[0,1,0],[0,0,1]],[[1,0,0]]):
            with self.assertRaises(ValueError):validate_basis(matrix)

    def test_unreviewed_commercial_input_refused_before_parsing(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed'):pinned_skin(b'not a commercial model')

    def test_bend_plane_rotation_maps_bone_and_resolves_antipodal_twist(self):
        for target in ([1,0,0],[-1,0,0],[0,1,0],[.6,.8,0]):
            matrix=bend_plane_rotation([1,0,0],target,[0,0,1])
            validate_basis(matrix)
            for a,b in zip(matvec(matrix,[1,0,0]),target):self.assertAlmostEqual(a,b)
            self.assertEqual(matvec(matrix,[0,0,1]),[0,0,1])

    def test_bend_plane_rotation_refuses_collinear_hint(self):
        with self.assertRaises(ValueError):bend_plane_rotation([1,0,0],[0,1,0],[0,1,0])


if __name__=='__main__':unittest.main()
