from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from equipment_hand_contact import vertex_groups


class HandContactGroupingTests(unittest.TestCase):
    def test_dominant_native_influence_and_thumb_prefix(self):
        skin={'nodes':[{'index':1,'name':'Bip01 L Hand'},
                       {'index':2,'name':'Bip01 L Finger01'},
                       {'index':3,'name':'Bip01 R Finger12'}],
              'joint_node_indices':[1,2,3], 'parents':[0,1,0],
              'pairs':[[2,0],[2,128],[2,129],[3,0]]}
        result=vertex_groups(skin)
        self.assertEqual(result['L']['thumb'],[0,1])
        self.assertEqual(result['L']['palm_or_arm'],[2])
        self.assertEqual(result['R']['fingers'],[3])
        self.assertEqual(sum(len(v) for side in result.values() for v in side.values()),4)

    def test_unknown_or_model_root_dominant_influence_is_refused(self):
        skin={'nodes':[{'index':1,'name':'Other'}], 'joint_node_indices':[1],
              'parents':[0], 'pairs':[[1,0]]}
        with self.assertRaises(ValueError): vertex_groups(skin)
        skin['nodes'][0]['name']='Bip01 L Hand';skin['pairs'][0][1]=255
        with self.assertRaises(ValueError): vertex_groups(skin)


if __name__=='__main__': unittest.main()
