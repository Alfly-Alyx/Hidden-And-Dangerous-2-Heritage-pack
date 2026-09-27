import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fpv_rig_binding import bind,hierarchy


def rigs(bones=2):
    hands=[{'index':1,'name':'a','parent_id':0,'frame_type':1,'visual_type':2}]
    hands.extend({'index':n+1,'name':'bone'+str(n),'parent_id':n,'frame_type':10,'visual_type':None}
                 for n in range(1,bones+1))
    names=('fpv_weapon','gunlock','cock','blsdum','cardum','shdum','shell01','magazine')
    weapon=[{'index':i,'name':name,'parent_id':0 if name in ('fpv_weapon','magazine') else 1,
             'frame_type':1 if name in ('fpv_weapon','gunlock','cock','shell01') else 6,'visual_type':None}
            for i,name in enumerate(names,1)]
    animation=copy.deepcopy(hands);animation[0]['frame_type']=10;animation[0]['visual_type']=None
    for node in weapon:
        animation.append({**node,'index':node['index']+len(hands),
                          'parent_id':node['parent_id']+len(hands) if node['parent_id'] else 0})
    return hands,weapon,animation


class FpvRigBindingTests(unittest.TestCase):
    def test_separate_owners_and_parent_names_match_despite_different_node_ordinals(self):
        hands,weapon,animation=rigs();tracks=[{'name':n['name']} for n in animation]
        originals=copy.deepcopy((hands,weapon,animation,tracks))
        result=bind(hands,weapon,animation,tracks)
        self.assertEqual(result['assembled_target_count'],11)
        self.assertEqual((result['hand_track_count'],result['weapon_track_count']),(3,8))
        root=next(b for b in result['bindings'] if b['track']=='fpv_weapon')
        self.assertEqual(root['target_node_index'],1);self.assertEqual(root['target_owner'],'weapon')
        self.assertEqual(result['targets_without_track'],[])
        self.assertEqual((hands,weapon,animation,tracks),originals)
        for key in ('native_name_binding_executed','skin_weights_evaluated','camera_or_events_qualified',
                    'partial_track_state_inheritance_qualified','engine_validated'):
            self.assertFalse(result[key])

    def test_partial_tracks_remain_partial_without_invented_default_poses(self):
        result=bind(*rigs(),[{'name':'a'},{'name':'gunlock'}])
        self.assertEqual((result['hand_track_count'],result['weapon_track_count']),(1,1))
        self.assertEqual(len(result['targets_without_track']),9)
        self.assertFalse(result['partial_track_state_inheritance_qualified'])

    def test_cross_model_name_collision_is_refused(self):
        hands,weapon,animation=rigs();hands[1]['name']='GUNLOCK'
        with self.assertRaisesRegex(ValueError,'colliding'):bind(hands,weapon,animation,[{'name':'a'}])

    def test_unknown_and_duplicate_track_names_are_refused_not_case_corrected(self):
        for tracks in ([{'name':'unknown'}],[{'name':'A'}],[{'name':'a'},{'name':'a'}],[],None):
            with self.subTest(tracks=tracks),self.assertRaises(ValueError):bind(*rigs(),tracks)

    def test_root_kind_exception_is_explicit_and_not_applied_to_other_joints(self):
        hands,weapon,animation=rigs();animation[1]['frame_type']=6
        with self.assertRaisesRegex(ValueError,'frame kind'):bind(hands,weapon,animation,[{'name':'a'}])
        hands,weapon,animation=rigs();animation[0]['frame_type']=1
        with self.assertRaisesRegex(ValueError,'frame kind'):bind(hands,weapon,animation,[{'name':'a'}])
        hands,weapon,animation=rigs();hands[0]['visual_type']=0
        with self.assertRaisesRegex(ValueError,'skinned hands'):bind(hands,weapon,animation,[{'name':'a'}])

    def test_changed_animation_parent_or_missing_target_is_refused(self):
        hands,weapon,animation=rigs();animation[2]['parent_id']=1
        with self.assertRaisesRegex(ValueError,'parent names'):bind(hands,weapon,animation,[{'name':'a'}])
        hands,weapon,animation=rigs();animation.pop()
        with self.assertRaisesRegex(ValueError,'target names'):bind(hands,weapon,animation,[{'name':'a'}])
        hands,weapon,animation=rigs();weapon.pop()
        with self.assertRaisesRegex(ValueError,'static Benelli'):bind(hands,weapon,animation,[{'name':'a'}])

    def test_hierarchy_rejects_cycles_missing_parents_duplicate_ids_and_case_aliases(self):
        for mutate in (lambda nodes:nodes[0].update(parent_id=3),lambda nodes:nodes[2].update(parent_id=99),
                       lambda nodes:nodes[2].update(index=1),lambda nodes:nodes[2].update(name='A'),
                       lambda nodes:nodes[0].update(index=True),lambda nodes:nodes[0].update(parent_id=False)):
            nodes=rigs()[0];mutate(nodes)
            with self.assertRaises(ValueError):hierarchy(nodes)


if __name__=='__main__':unittest.main()
