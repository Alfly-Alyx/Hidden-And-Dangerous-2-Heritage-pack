"""Synthetic/original animation tests, never commercial poses or keyframes."""
import copy
import json
import math
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_modern_asset as asset
import modern_animation as motion
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from model_transform import point, world_transforms
from test_five_ds import invented_clip


def clip(tracks=None,end=10):
    if tracks is None:
        tracks=[{'name':'Root','channels':{'position':{'frames':[0,end],'values':[[0,0,0],[1,2,3]]}}}]
    return {'provenance':'MODERNE','runtime_status':'pending','frame_end':end,'tracks':tracks}


def channel(kind,frames,values,name='Root'):
    return {'name':name,'channels':{kind:{'frames':frames,'values':values}}}


class ModernAnimationCodecTests(unittest.TestCase):
    def test_minimal_position_file_matches_hand_calculated_layout(self):
        data=motion.encode_5ds(clip([channel('position',[0],[[1,2,3]],'root')],1))
        expected=(b'5DS\0'+struct.pack('<HQI',122,0,41)
                  +struct.pack('<HHII',1,1,36,16)+bytes(4)
                  +struct.pack('<IHH3f',2,1,0,1,2,3)+b'root\0')
        self.assertEqual(data,expected)

    def test_all_channels_match_independent_existing_fixture_encoder(self):
        tracks=[('Root',{'rotation':([0,10],[(0,0,0,1),(0,1,0,0)]),
                        'position':([0,4,10],[(0,0,0),(1,2,3),(2,3,4)]),
                        'scale':([0,10],[(1,1,1),(2,2,2)])}),
                ('Part',{'position':([0],[(0,1,0)])})]
        description=[{'name':n,'channels':{k:{'frames':f,'values':[list(row) for row in v]}
                                           for k,(f,v) in channels.items()}} for n,channels in tracks]
        data=motion.encode_5ds(clip(description))
        self.assertEqual(data,invented_clip(tracks))
        parsed=parse_5ds(data)
        self.assertIsNone(parsed['frame_rate'])
        self.assertFalse(parsed['engine_validated'])

    def test_invalid_provenance_unknown_events_and_duplicate_names_are_refused(self):
        bad=[]
        for updates in ({'provenance':'OFFICIEL'},{'runtime_status':'passed'},{'events':[]},
                        {'frame_end':True},{'frame_end':0},{'tracks':[]}):
            value=clip();value.update(updates);bad.append(value)
        bad.append(clip([channel('note',[0],[[1,2,3]])]))
        bad.append(clip([channel('position',[0],[[0,0,0]],'../Root')]))
        bad.append(clip([channel('position',[0],[[0,0,0]],'Root'),
                         channel('position',[0],[[0,0,0]],'root')]))
        for value in bad:
            with self.subTest(value=value),self.assertRaises(ValueError):motion.encode_5ds(value)

    def test_bad_frames_and_transforms_are_refused(self):
        bad=[channel('position',f,[[0,0,0]]*len(f)) for f in ([True],[11],[2,1],[0,0],[])]
        bad.extend((channel('position',[0],[[math.inf,0,0]]),channel('position',[0],[[11,0,0]]),
                    channel('scale',[0],[[1,0,1]]),channel('scale',[0],[[-1,1,1]]),
                    channel('rotation',[0],[[0,0,0,0]]),channel('rotation',[0],[[0,0,0,2]]),
                    channel('position',[0,10],[[0,0,0]])))
        for track in bad:
            with self.subTest(track=track),self.assertRaises(ValueError):motion.encode_5ds(clip([track]))

    def test_shortest_arc_quaternion_interpolation_and_antipodes(self):
        middle=motion.slerp([0,0,0,1],[0,0,1,0],.5)
        self.assertAlmostEqual(middle[2],math.sqrt(.5))
        self.assertAlmostEqual(middle[3],math.sqrt(.5))
        self.assertEqual(motion.slerp([0,0,0,1],[0,0,0,-1],.5),[0,0,0,1])
        nearly=motion.slerp([0,0,0,1],[0,0,math.sin(.001),math.cos(.001)],.5)
        self.assertAlmostEqual(sum(v*v for v in nearly),1)

    def test_linear_sampling_uses_keys_and_holds_endpoints(self):
        value={'frames':[2,4,10],'values':[[0,0,0],[2,4,6],[8,10,12]]}
        self.assertEqual(motion.sample_channel(value,0),[0,0,0])
        self.assertEqual(motion.sample_channel(value,3),[1,2,3])
        self.assertEqual(motion.sample_channel(value,4),[2,4,6])
        self.assertEqual(motion.sample_channel(value,20),[8,10,12])


class ModernRigidPivotTests(unittest.TestCase):
    def setUp(self):
        self.recipe=json.loads((ROOT/'experimental/FG42/modern-world-model.json').read_text(encoding='utf-8'))
        self.meshes=asset.build_meshes(self.recipe)
        self.base=asset.encode_4ds(self.recipe,self.meshes)
        self.groups=[{'name':'MOD_magazine_pivot','pivot':[-.02,.072,.036],
                      'members':['MOD_side_magazine','MOD_magazine_endplate','MOD_magazine_anchor']}]
        self.rig,self.report=motion.rig_model(self.base,self.groups)

    def test_pivots_preserve_every_world_transform_and_geometry_payload_at_rest(self):
        original=parse_4ds_nodes(self.base);rebuilt=parse_4ds_nodes(self.rig)
        before=world_transforms(self.base,original['nodes'])
        after=world_transforms(self.rig,rebuilt['nodes'])
        by_name={n['name']:n for n in rebuilt['nodes']}
        self.assertEqual(rebuilt['node_count'],original['node_count']+1)
        self.assertFalse(rebuilt['has_animation'])
        self.assertFalse(self.report['vertices_rewritten'])
        for old in original['nodes']:
            new=by_name[old['name']]
            for value in ((0,0,0),(.3,.2,.1),(-.2,.5,-.4)):
                for a,b in zip(point(before[old['index']],value),point(after[new['index']],value)):
                    self.assertAlmostEqual(a,b,places=7)
            if old['frame_type']==1:
                left=self.base[old['position_offset']+12:old['end']]
                right=self.rig[new['position_offset']+12:new['end']]
                self.assertEqual(left,right)

    def test_rotating_pivot_moves_owned_parts_and_anchors_only(self):
        pivot=self.groups[0]['pivot']
        description=clip([{'name':'MOD_magazine_pivot','channels':{
            'position':{'frames':[0,10],'values':[pivot,pivot]},
            'rotation':{'frames':[0,10],'values':[[0,0,0,1],[0,0,1,0]]}}}])
        animation=motion.encode_5ds(description)
        transforms=motion.pose(self.rig,animation,5)
        nodes={n['name']:n for n in parse_4ds_nodes(self.rig)['nodes']}
        vertex=(-.1,.072,.036)
        actual=point(transforms[nodes['MOD_side_magazine']['index']],vertex)
        expected=[pivot[0],pivot[1]+vertex[0]-pivot[0],pivot[2]]
        for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,places=7)
        for a,b in zip(point(transforms[nodes['MOD_receiver']['index']],vertex),vertex):
            self.assertAlmostEqual(a,b)
        posed=motion.animated_meshes(self.recipe,self.meshes,self.rig,animation,0)
        for old,new in zip(self.meshes,posed):
            for a,b in zip(old[0].points,new[0].points):
                for left,right in zip(a,b):self.assertAlmostEqual(left,right,places=7)

    def test_missing_duplicate_reserved_and_invalid_pivots_are_refused(self):
        invalid=[[],[{'name':'MOD_x','pivot':[0,0,0],'members':[]}]]
        for updates in ({'name':self.recipe['name']},{'name':'../bad'},
                        {'pivot':[math.nan,0,0]},{'members':['missing']},
                        {'members':['MOD_receiver','MOD_receiver']}):
            group=copy.deepcopy(self.groups[0]);group.update(updates);invalid.append([group])
        invalid.append(self.groups*2)
        for groups in invalid:
            with self.subTest(groups=groups),self.assertRaises(ValueError):motion.rig_model(self.base,groups)

    def test_unbound_tracks_and_out_of_range_frames_are_refused(self):
        animation=motion.encode_5ds(clip())
        with self.assertRaisesRegex(ValueError,'Unbound'):motion.pose(self.rig,animation,0)
        animation=motion.encode_5ds(clip([channel('position',[0],[[0,0,0]],self.report['root'])]))
        for frame in (-1,11,math.nan,True):
            with self.subTest(frame=frame),self.assertRaises(ValueError):motion.pose(self.rig,animation,frame)


if __name__=='__main__':unittest.main()

