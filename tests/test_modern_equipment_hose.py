"""Original visual hose: exact source geometry, two LODs, native binds and joins."""
from copy import deepcopy
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_modern_asset as asset
from build_modern_equipment_hose import inputs,compile_hose_bank,skin_mesh,build,CASES
from build_modern_equipment_animation import compile_equipment_bank
from four_ds_skin import read_reviewed
from menu_gui_audit import parse_4ds_nodes
from five_ds import parse_5ds
from model_transform import point,compose
import modern_animation as motion

HASHES={'F35':'acae0e6ded8dc4b74d3887d697ec5a5a6d47bc50d459d8d854853fc8b73c7715',
        'F2':'1451f7c7775c17e8a243674492955241aeee41d8bd05a30fc997e963ae0545ed'}


class ModernHoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={case:(inputs(case),compile_hose_bank(*inputs(case))) for case in CASES}

    def test_two_stable_two_lod_skins_and_eighteen_clips(self):
        for case,(_, (rig,clips,_,report)) in self.cases.items():
            self.assertEqual(hashlib.sha256(rig).hexdigest(),HASHES[case]);self.assertEqual(len(clips),9)
            self.assertEqual(report['lod_vertices'],[576,288]);self.assertEqual(report['lod_triangles'],[192,96])
            self.assertEqual(parse_4ds_nodes(rig)['node_count'],9)
            self.assertEqual(parse_4ds_nodes(rig)['has_animation'],0)
            for stem,clip in clips.values():
                self.assertLessEqual(len(stem),19);self.assertEqual(parse_5ds(clip)['track_count'],9)

    def test_original_geometry_payload_both_lods_is_exact(self):
        for _,(args,(rig,_,levels,_)) in self.cases.items():
            source=next(pair for pair in asset.build_meshes(args[0]) if pair[0].name=='MOD_hose')
            for lod in (0,1):
                skin=read_reviewed(rig,allow_multiple_lods=True,lod=lod)
                a=b''.join(struct.pack('<8f',*v) for v in source[lod].expanded())
                b=b''.join(struct.pack('<8f',*v) for v in skin['vertices'])
                self.assertEqual(a,b);self.assertEqual(levels[lod].triangles,source[lod].triangles)

    def test_independent_bone_frames_and_inverse_binds(self):
        for _,(_, (rig,_,_,report)) in self.cases.items():
            skin=read_reviewed(rig,allow_multiple_lods=True)
            self.assertEqual(skin['parents'],[0]*8)
            self.assertEqual({p[0] for p in skin['pairs']},set(range(1,9)))
            self.assertEqual({p[1] for p in skin['pairs']},{0})
            self.assertLess(skin['report']['inverse_bind_max_identity_error'],1e-7)
            self.assertEqual(report['influence_weights'][:2],[0,0]);self.assertEqual(report['influence_weights'][-2:],[1,1])
            self.assertEqual(report['influence_weights'],sorted(report['influence_weights']))

    def test_original_single_lod_reader_default_remains_strict(self):
        rig=self.cases['F35'][1][0]
        with self.assertRaises(ValueError):read_reviewed(rig)
        for selected in (-1,2,True,0.5):
            with self.assertRaises(ValueError):read_reviewed(rig,allow_multiple_lods=True,lod=selected)
        for allowed in (1,None,'yes'):
            with self.assertRaises(ValueError):read_reviewed(rig,allow_multiple_lods=allowed)

    def test_every_bound_track_is_transform_only_and_keeps_root_identity(self):
        for _,(_, (rig,clips,_,report)) in self.cases.items():
            names={node['name'] for node in parse_4ds_nodes(rig)['nodes']}
            for _,animation in clips.values():
                parsed=parse_5ds(animation)
                self.assertEqual({t['name'] for t in parsed['tracks']},names)
                self.assertTrue(all(t['flags']==6 for t in parsed['tracks']))
                root=next(t for t in parsed['tracks'] if t['name']==report['root'])
                self.assertEqual(root['channels']['position']['values'],[[0,0,0],[0,0,0]])

    def test_corrupt_second_lod_pair_is_rejected_even_when_reading_first(self):
        raw=self.cases['F35'][1][0];root=parse_4ds_nodes(raw)['nodes'][0]
        broken=bytearray(raw);broken[root['end']-2*288]=0
        for lod in (0,1):
            with self.assertRaises(ValueError):read_reviewed(bytes(broken),allow_multiple_lods=True,lod=lod)

    def test_continuous_endpoint_transforms_at_all_half_frames(self):
        samples=0
        for _,(args,(rig,clips,_,report)) in self.cases.items():
            held,held_clips,_,_=compile_equipment_bank(*args[:3])
            held_nodes={n['name']:n for n in parse_4ds_nodes(held)['nodes']}
            skin=read_reviewed(rig,allow_multiple_lods=True)
            path=next(p['path'] for p in args[0]['parts'] if p['name']=='MOD_hose')
            for name,(_,animation) in clips.items():
                end=parse_5ds(animation)['frame_end']
                for half in range(end*2+1):
                    frame=half/2;poses=motion.pose(rig,animation,frame)
                    held_poses=motion.pose(held,held_clips[name][1],frame)
                    for endpoint,bone in ((path[0],0),(path[-1],7)):
                        values=skin['inverse_binds'][bone]
                        inverse=([[values[i+j*4] for j in range(3)] for i in range(3)],values[12:15])
                        actual=point(compose(poses[skin['joint_node_indices'][bone]],inverse),endpoint)
                        if bone==0:expected=endpoint
                        else:
                            transform=held_poses[held_nodes['MOD_held_pivot']['index']]
                            moved=point(transform,[v-p for v,p in zip(endpoint,report['pivot'])])
                            expected=[v+p for v,p in zip(moved,report['pivot'])]
                        self.assertLess(max(abs(a-b) for a,b in zip(actual,expected)),2e-7)
                    samples+=1
        self.assertEqual(samples,1122)

    def test_rest_and_both_lod_deformations_are_nondegenerate(self):
        for _,(_, (rig,clips,levels,_)) in self.cases.items():
            for lod in (0,1):
                rest=skin_mesh(rig,clips['Idle1'][1],0,lod)
                expected=levels[lod].expanded()
                for actual,wanted in zip(rest.points,expected):
                    self.assertLess(max(abs(a-b) for a,b in zip(actual,wanted[:3])),1e-7)
                moved=skin_mesh(rig,clips['Arm'][1],0,lod)
                self.assertGreater(max(abs(a-b) for p,q in zip(rest.points,moved.points) for a,b in zip(p,q)),.01)
                for name,(_,animation) in clips.items():
                    end=parse_5ds(animation)['frame_end']
                    for frame in (0,end/2,end):skin_mesh(rig,animation,frame,lod).validate()

    def test_loops_and_cross_clip_joins(self):
        pairs=(('Aim',12,'AimShot',0),('AimShot',24,'Daim',0),('Daim',12,'Idle1',0),
               ('Arm',24,'Idle1',0),('Rel',64,'Idle1',0),('Jammed',32,'Idle1',0))
        for _,(_, (rig,clips,_,report)) in self.cases.items():
            checks=list(pairs)+[(name,0,name,desc['frame_end']) for name,desc in report['clips'].items() if desc['loop']]
            for a,fa,b,fb in checks:
                left=motion.pose(rig,clips[a][1],fa);right=motion.pose(rig,clips[b][1],fb)
                for index in left:
                    for x,y in zip((*left[index][0],left[index][1]),(*right[index][0],right[index][1])):
                        self.assertLess(max(abs(v-w) for v,w in zip(x,y)),1e-7)

    def test_sources_unchanged(self):
        args=inputs('F35');before=deepcopy(args);compile_hose_bank(*args);self.assertEqual(args,before)

    def test_changed_sources_or_functional_claims_refused(self):
        args=inputs('F35')
        for update in ({'held_rig_sha256':'0'*64},{'held_recipe_sha256':'0'*64},{'name':'F2'},
                       {'provenance':'OFFICIEL'},{'runtime_status':'passed'},{'method':'physical'}, {'ammo_id':207}):
            modified=deepcopy(args);modified[3].update(update)
            with self.assertRaises(ValueError):compile_hose_bank(*modified)

    def test_missing_gameplay_and_dynamic_solver_are_explicit(self):
        for _,(_, (_,_,_,report)) in self.cases.items():
            self.assertTrue(report['hose_deformation_implemented']);self.assertTrue(report['authored_synchronized_clips_only'])
            self.assertEqual(report['runtime_status'],'pending')
            for key in ('length_preserving','collision_solver','arbitrary_pose_solver','player_skeleton_bound',
                        'native_loader_executed','events_or_effects','functional_weapon_implemented',
                        'commercial_assets_read','game_modified','game_launched','engine_validated'):
                self.assertFalse(report[key])

    def test_native_endpoint_comparison_preserves_identity_snap(self):
        from equipment_hose_native_audit import held_endpoint
        from ls3d_palette_oracle import reference
        identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
        pose={'position':[0,0,0],'rotation':[-.00001745,0,-.00001454,1],
              'scale':[1,1,1],'parent':-1}
        matrix=reference([pose],[identity])['palette'][0]
        self.assertEqual(matrix,identity)
        source=[.157,.03,-.05];pivot=[0,-.047,-.025]
        actual=held_endpoint(matrix,source,pivot)
        for a,b in zip(actual,source):self.assertAlmostEqual(a,b,places=14)

    def test_fresh_output_only_and_all_native_files_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'fresh';report=build(*inputs('F2'),output)
            self.assertEqual(len(list(output.iterdir())),27)
            self.assertEqual(len(list(output.glob('*.4ds.disabled'))),10)
            self.assertEqual(len(list(output.glob('*.5ds.disabled'))),9)
            self.assertFalse(list(output.glob('*.4ds'))+list(output.glob('*.5ds')))
            self.assertFalse(report['companion_auto_load_engine_validated'])
            with self.assertRaises(FileExistsError):build(*inputs('F2'),output)


if __name__=='__main__':unittest.main()
