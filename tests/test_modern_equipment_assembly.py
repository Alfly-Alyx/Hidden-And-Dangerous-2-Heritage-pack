"""One modern rig/clock for held piece, fixed pack and two-LOD hose skin."""
from copy import deepcopy
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_modern_equipment_assembly import inputs,compile_assembly,assemble_models,assembly_preview,build,CASES
from build_modern_equipment_hose import compile_hose_bank
from build_modern_equipment_animation import compile_equipment_bank
from build_modern_equipment_components import compile_components
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms
import build_modern_asset as asset
import modern_animation as motion

HASHES={'F35':'ed213eee76c286aa9858f7d0f6e6210950fa0f0cd6566e253058d6dc40c73751',
        'F2':'c64d8b70809d7a760603c84cdffd6487199b27d5beb3f140d08e9a6226612055'}


class ModernAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={case:(inputs(case),compile_assembly(*inputs(case))) for case in CASES}

    def test_two_native_rigs_and_eighteen_unified_clips(self):
        for case,(_, (rig,clips,report)) in self.cases.items():
            self.assertEqual(hashlib.sha256(rig).hexdigest(),HASHES[case])
            parsed=parse_4ds_nodes(rig);self.assertEqual(parsed['node_count'],39 if case=='F35' else 37)
            self.assertEqual(len(clips),9);self.assertEqual(parsed['has_animation'],0)
            names={n['name'] for n in parsed['nodes']};self.assertEqual(len(names),parsed['node_count'])
            for stem,raw in clips.values():
                self.assertLessEqual(len(stem),19);clip=parse_5ds(raw)
                self.assertEqual(clip['track_count'],11)
                self.assertTrue(all(t['flags']==6 and t['name'] in names for t in clip['tracks']))

    def test_both_component_key_sets_are_preserved_without_quaternion_roundtrip(self):
        for _,(args,(rig,clips,report)) in self.cases.items():
            held,held_clips,_,held_report=compile_equipment_bank(*args[:3])
            _,hose_clips,_,_=compile_hose_bank(*args)
            for name,(_,raw) in clips.items():
                actual={t['name']:t['channels'] for t in parse_5ds(raw)['tracks']}
                for data in (held_clips[name][1],hose_clips[name][1]):
                    for track in parse_5ds(data)['tracks']:
                        expected=deepcopy(track['channels'])
                        if track['name']==held_report['rig']['root']:
                            origin=[struct.unpack('<f',struct.pack('<f',v))[0] for v in report['component_origins']['held']]
                            expected['position']['values']=[origin[:] for _ in expected['position']['values']]
                        self.assertEqual(actual[track['name']],expected)

    def test_component_blocks_preserve_skin_and_mesh_bytes(self):
        for _,(args,(rig,_,report)) in self.cases.items():
            components,_=compile_components(*args[:2]);sources={'held':compile_equipment_bank(*args[:3])[0],
                'backpack':components['backpack']['data'],'hose':compile_hose_bank(*args)[0]}
            combined={n['index']:n for n in parse_4ds_nodes(rig)['nodes']}
            for role,data in sources.items():
                for node in parse_4ds_nodes(data)['nodes']:
                    target=combined[report['source_index_maps'][role][node['index']]]
                    before=data[node['start']:node['end']];after=bytearray(rig[target['start']:target['end']])
                    p=node['parent_offset']-node['start'];after[p:p+2]=before[p:p+2]
                    if node['index']==1:
                        p=node['position_offset']-node['start'];after[p:p+12]=before[p:p+12]
                    self.assertEqual(bytes(after),before)

    def test_rest_rigid_geometry_matches_the_original_whole_model(self):
        for _,(args,(rig,clips,_)) in self.cases.items():
            source={pair[0].name:pair for pair in asset.build_meshes(args[0])}
            previews=assembly_preview(args[0],rig,clips['Idle1'][1],0,compile_hose_bank(*args)[0])
            for pair in previews:
                if pair[0].name=='MOD_hose':continue
                for lod in (0,1):
                    for a,b in zip(pair[lod].points,source[pair[lod].name][lod].points):
                        self.assertLess(max(abs(x-y) for x,y in zip(a,b)),1e-7)

    def test_single_clock_preserves_all_half_frame_component_poses(self):
        count=0
        for _,(args,(rig,clips,report)) in self.cases.items():
            held,held_clips,_,_=compile_equipment_bank(*args[:3]);hose,hose_clips,_,_=compile_hose_bank(*args)
            for name,(_,data) in clips.items():
                end=parse_5ds(data)['frame_end']
                for half in range(end*2+1):
                    actual=motion.pose(rig,data,half/2)
                    for role,source,animations in (('held',held,held_clips),('hose',hose,hose_clips)):
                        expected=motion.pose(source,animations[name][1],half/2)
                        for index,(matrix,position) in expected.items():
                            result=actual[report['source_index_maps'][role][index]]
                            for a,b in zip(matrix,result[0]):
                                self.assertLess(max(abs(x-y) for x,y in zip(a,b)),1e-7)
                            shifted=[a+b for a,b in zip(position,report['component_origins'][role])]
                            self.assertLess(max(abs(x-y) for x,y in zip(shifted,result[1])),1e-7)
                    count+=1
        self.assertEqual(count,1122)

    def test_backpack_is_not_accidentally_animated_or_double_translated(self):
        for _,(args,(rig,clips,report)) in self.cases.items():
            nodes=parse_4ds_nodes(rig)['nodes'];rest=world_transforms(rig,nodes)
            pack_indices=set(report['source_index_maps']['backpack'].values())
            pack_names={n['name'] for n in nodes if n['index'] in pack_indices}
            for _,raw in clips.values():
                parsed=parse_5ds(raw);self.assertFalse(pack_names&{t['name'] for t in parsed['tracks']})
                actual=motion.pose(rig,raw,parsed['frame_end']/2)
                self.assertEqual({i:actual[i] for i in pack_indices},{i:rest[i] for i in pack_indices})

    def test_skin_visual_root_and_joint_parents_are_correctly_remapped(self):
        for _,(_, (rig,_,report)) in self.cases.items():
            nodes={n['index']:n for n in parse_4ds_nodes(rig)['nodes']};mapping=report['source_index_maps']['hose']
            root=nodes[mapping[1]];self.assertEqual(root['visual_type'],2);self.assertEqual(root['parent_id'],1)
            for i in range(2,10):
                joint=nodes[mapping[i]];self.assertEqual(joint['parent_id'],mapping[1]);self.assertEqual(joint['frame_type'],10)
                self.assertEqual(struct.unpack_from('<I',rig,joint['end']-4)[0],i-2)

    def test_ambiguous_or_different_material_sources_are_rejected(self):
        args=inputs('F35');components,_=compile_components(*args[:2])
        held=compile_equipment_bank(*args[:3])[0];hose=compile_hose_bank(*args)[0]
        source={'held':held,'backpack':components['backpack']['data'],'hose':hose}
        origins={role:[0,0,0] for role in source}
        bad=dict(source);bad['backpack']=held
        with self.assertRaises(ValueError):assemble_models(bad,origins,'PROTOTYPE_HERITAGE_Test',[[0,0,0],[1,1,1]])
        changed=bytearray(hose);changed[20]^=1;bad=dict(source);bad['hose']=bytes(changed)
        with self.assertRaises(ValueError):assemble_models(bad,origins,'PROTOTYPE_HERITAGE_Test',[[0,0,0],[1,1,1]])

    def test_inputs_unchanged_and_pending_flags_explicit(self):
        args=inputs('F2');before=deepcopy(args);_,_,report=compile_assembly(*args);self.assertEqual(args,before)
        self.assertTrue(report['rigid_and_skin_share_one_clip']);self.assertEqual(report['runtime_status'],'pending')
        for key in ('player_skeleton_bound','fpv_camera_calibrated','native_loader_executed','arbitrary_pose_solver',
                    'collision_solver','functional_weapon_implemented','events_or_effects','game_modified','game_launched'):
            self.assertFalse(report[key])

    def test_fresh_disabled_outputs_and_companion_names(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'fresh';report=build(*inputs('F35'),output)
            self.assertEqual(len(list(output.iterdir())),27)
            self.assertEqual(len(list(output.glob('*.4ds.disabled'))),10)
            self.assertEqual(len(list(output.glob('*.5ds.disabled'))),9)
            self.assertFalse(list(output.glob('*.4ds'))+list(output.glob('*.5ds')))
            for desc in report['clips'].values():
                companion=(output/(desc['stem']+'.4ds.disabled')).read_bytes()
                self.assertEqual(parse_4ds_nodes(companion)['has_animation'],1)
            self.assertFalse(report['companion_auto_load_engine_validated'])
            with self.assertRaises(FileExistsError):build(*inputs('F35'),output)


if __name__=='__main__':unittest.main()
