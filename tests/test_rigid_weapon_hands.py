"""Original inputs and invented poses only; no commercial skeleton fixtures."""
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_rigid_weapon_hand_bank as hands
from build_modern_equipment_hose import digest
from five_ds import parse_5ds
from hand_pose_ik import validate_basis
from rigid_weapon_hand_audit import suffix_checked,load_bank,audit


class RigidWeaponHandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled={c:hands.rigid_bank(c) for c in hands.CASES}
        cls.profile=json.loads(hands.PROFILE.read_text(encoding='utf-8'))
        cls.base=json.loads(hands.BASE_PROFILE.read_text(encoding='utf-8'))
        cls.spec=json.loads(hands.RECIPE.read_text(encoding='utf-8'))

    def test_profile_pins_modern_models_and_keeps_inputs_unchanged(self):
        before=deepcopy((self.profile,self.base,self.spec))
        for case in hands.CASES:
            grips,thumb,translation,sha=hands.configuration(self.profile,self.base,self.spec,case)
            self.assertEqual(sha,digest(self.compiled[case][1]));self.assertEqual(translation,[.07,-.13,.16])
            self.assertEqual(set(grips),{'L','R'})
            for g in grips.values():validate_basis(g['rest_to_equipment_rotation'])
            hands.turns(thumb)
        self.assertEqual((self.profile,self.base,self.spec),before)

    def test_invalid_profile_provenance_hash_fields_and_ranges_refused(self):
        mutations=(lambda p:p.update(schema_version=True),lambda p:p.update(provenance='OFFICIEL'),
            lambda p:p.update(source_grip_profile_sha256='0'*64),lambda p:p.update(cases=None),
            lambda p:p['cases'].update(FG42=[]),lambda p:p['cases']['FG42'].update(model_sha256='../'),
            lambda p:p['cases']['FG42'].update(translation=[0,math.inf,0]),
            lambda p:p['cases']['FG42'].update(translation=[0,.51,0]),
            lambda p:p['cases']['FG42']['hands']['L'].update(contact_offset_delta=[True,0,0]),
            lambda p:p['cases']['FG42']['hands']['R'].update(rotation_degrees=[91,0,0]),
            lambda p:p['cases']['FG42']['hands']['L'].update(bone_poses=[]))
        for mutate in mutations:
            bad=deepcopy(self.profile);mutate(bad)
            with self.assertRaises(ValueError):hands.configuration(bad,self.base,self.spec,'FG42')
        with self.assertRaises(ValueError):hands.configuration(self.profile,self.base,self.spec,'Other')

    def test_adjustment_affects_only_selected_modern_choices(self):
        grips,thumb,_,_=hands.configuration(self.profile,self.base,self.spec,'FG42');before=deepcopy((grips,thumb))
        choice={'contact_offset_delta':[.001,.002,-.003],'rotation_degrees':[3,4,5],
                'finger_curl_degrees':[60,40,20],'thumb':{'opposition_degrees':15,'curl_degrees':[10,20]}}
        actual,turned=hands.adjust(grips,thumb,'L',choice)
        self.assertEqual((grips,thumb),before);self.assertEqual(actual['R'],grips['R']);self.assertEqual(turned['R'],thumb['R'])
        self.assertEqual(actual['L']['contact_offset'],[a+b for a,b in zip(grips['L']['contact_offset'],choice['contact_offset_delta'])])
        self.assertEqual(actual['L']['finger_curl_degrees'],[60,40,20]);self.assertEqual(turned['L'],choice['thumb'])
        for key in ('wrist_to_contact_in_rest','elbow_pole'):self.assertEqual(actual['L'][key],grips['L'][key])
        validate_basis(actual['L']['rest_to_equipment_rotation'])
        for change in ({'finger_curl_degrees':[111,0,0]},{'thumb':{'opposition_degrees':True,'curl_degrees':[0,0]}}):
            bad=deepcopy(choice);bad.update(change)
            with self.assertRaises(ValueError):hands.adjust(grips,thumb,'L',bad)

    def test_placement_changes_only_root_positions_after_float32_roundtrip(self):
        for case,(_,rig,clips,_) in self.compiled.items():
            for stem,raw in clips.values():
                before=parse_5ds(raw)['tracks'];placed=hands.placed_tracks(raw,[.07,-.13,.16])
                for a,b in zip(before,placed):
                    self.assertEqual(a['name'],b['name']);expected=deepcopy(a['channels'])
                    if a['name']=='fpv_weapon':
                        expected['position']['values']=[hands.f32_row([x+y for x,y in zip(v,[.07,-.13,.16])],3)
                                                       for v in expected['position']['values']]
                    self.assertEqual(b['channels'],expected)
                self.assertEqual(parse_5ds(raw)['tracks'],before)
        for vector in ([math.nan,0,0],[True,0,0],[.51,0,0],[0,0]):
            with self.assertRaises(ValueError):hands.placed_tracks(raw,vector)

    def invented(self,case='FG42'):
        # Test serialization orchestration, not commercial IK: invented identity poses.
        names=sorted(hands.HAND_NAMES);identity=[[1,0,0],[0,1,0],[0,0,1]]
        skin={'nodes':[{'name':n,'index':i+1} for i,n in enumerate(names)],
              'rest_world':{i+1:(identity,[0,0,0]) for i in range(len(names))}}
        poses={n:{'position':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]} for n in names}
        cfg=hands.configuration(self.profile,self.base,self.spec,case);rig=self.compiled[case][1]
        with patch.object(hands,'pinned_skin',return_value=(hands.HAND_MODELS[0],skin)), \
             patch.object(hands,'author_pose',return_value=(poses,{'arms':{'L':{'wrist_error':0},'R':{'wrist_error':0}}})), \
             patch.object(hands,'apply',side_effect=lambda poses,bases,thumb:poses):
            return hands.compile_hand_bank(case,b'invented source marker',rig,self.compiled[case][2],*cfg[:3])

    def test_stow_translation_fades_to_zero_and_only_changes_root_position(self):
        for name in ('Arm','Disarm','Idle1','Rel'):
            raw=self.compiled['MG34'][2][name][1];end=parse_5ds(raw)['frame_end']
            normal=hands.placed_tracks(raw,[.07,-.13,.16]);placed=hands.placed_tracks(raw,[.07,-.13,.16],stow=[0,0,.12],clip_name=name)
            for a,b in zip(normal,placed):
                if a['name']!='fpv_weapon':self.assertEqual(a,b);continue
                for key in ('rotation','scale'):self.assertEqual(a['channels'][key],b['channels'][key])
                for frame,x,y in zip(a['channels']['position']['frames'],a['channels']['position']['values'],b['channels']['position']['values']):
                    factor=1-frame/end if name=='Arm' else (frame/end if name=='Disarm' else 0)
                    self.assertEqual(x[:2],y[:2]);self.assertAlmostEqual(y[2]-x[2],.12*factor,places=7)
        for value,clip in (([0,0,.21],'Arm'),([0,0,.12],None),([0,0,True],'Arm')):
            with self.assertRaises(ValueError):hands.placed_tracks(raw,[0,0,0],stow=value,clip_name=clip)

    def test_elbow_stow_curve_is_reversible_and_leaves_idle_aim_and_reload_unchanged(self):
        grip={'elbow_pole':[-.38,-.28,-.12],'stow_elbow_pole':[-.38,-.03,.13]}
        for time in range(0,961,20):
            for a,b in zip(hands.elbow_hint(grip,'Arm',time,24),hands.elbow_hint(grip,'Disarm',960-time,24)):
                self.assertAlmostEqual(a,b,places=14)
        for a,b in zip(hands.elbow_hint(grip,'Arm',0,24),grip['stow_elbow_pole']):self.assertAlmostEqual(a,b,places=14)
        self.assertEqual(hands.elbow_hint(grip,'Arm',960,24),grip['elbow_pole'])
        for name in ('Idle1','Aim','Daim','Rel'):
            self.assertEqual(hands.elbow_hint(grip,name,480,24),grip['elbow_pole'])
        for time in (-1,961,True,float('nan')):
            with self.assertRaises(ValueError):hands.elbow_hint(grip,'Arm',time,24)

    def test_private_merge_aliases_and_equipment_preservation_with_invented_poses(self):
        clips,report=self.invented()
        self.assertEqual(len(clips),9);self.assertEqual(report['hand_sha256'],digest(b'invented source marker'))
        self.assertFalse(report['finger_contact_qualified']);self.assertFalse(report['engine_validated'])
        for name,(stem,raw) in clips.items():
            self.assertLessEqual(len(stem),19);self.assertTrue(stem.startswith('PROTOTYPE_FG4PH'))
            parsed=parse_5ds(raw);tracks={t['name']:t['channels'] for t in parsed['tracks']}
            self.assertEqual(len(tracks),37+32);self.assertLessEqual(len(raw)-18,0xf000)
            expected=hands.placed_tracks(self.compiled['FG42'][2][name][1],[.07,-.13,.16])
            self.assertEqual({k:v for k,v in tracks.items() if k not in hands.HAND_NAMES},
                             {t['name']:t['channels'] for t in expected})

    def test_target_translation_is_additive_and_never_rotates_hands_by_reflection(self):
        for case,(_,rig,clips,_) in self.compiled.items():
            grips,_,shift,_=hands.configuration(self.profile,self.base,self.spec,case)
            zero=hands.placed_tracks(clips['Idle1'][1],[0,0,0]);placed=hands.placed_tracks(clips['Idle1'][1],shift)
            a=hands.targets(rig,zero,0,grips);b=hands.targets(rig,placed,0,grips)
            for side in ('L','R'):
                for i in range(3):self.assertAlmostEqual(b[side]['position'][i]-a[side]['position'][i],shift[i],places=7)
                self.assertEqual(a[side]['rotation'],b[side]['rotation']);validate_basis(b[side]['rotation'])

    def test_unreviewed_hand_source_rejected_before_model_or_directory_access(self):
        with self.assertRaises(ValueError):load_bank(None,'FG42',hands.HAND_MODELS[0],b'wrong',self.profile,None)
        with self.assertRaises(ValueError):load_bank(None,'Other',hands.HAND_MODELS[0],b'wrong',self.profile,None)
        for suffix in ('../HandFPV_v1','HandFPV_v0','HandFPV_v1/Other','Other',None):
            with self.assertRaises(ValueError):suffix_checked(suffix)
            with self.assertRaises(ValueError):audit(None,None,suffix,None)

    def test_build_exports_no_hand_model_or_active_clip_and_refuses_overwrite(self):
        compiled=self.compiled['FG42'];clips,row=self.invented()
        second={n:(stem.replace('PH','PR'),raw) for n,(stem,raw) in clips.items()}
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'fresh'
            with patch.object(hands,'rigid_bank',return_value=compiled), \
                 patch.object(hands,'compile_hand_bank',side_effect=[(clips,row),(second,row)]):
                report=hands.build('FG42',{s:b'invented' for s in hands.HAND_MODELS},self.profile,out)
                self.assertEqual(len(list(out.glob('*.4ds.disabled'))),1)
                self.assertEqual(len(list(out.glob('*.5ds.disabled'))),18)
                self.assertFalse(list(out.glob('*.4ds')));self.assertFalse(list(out.glob('*.5ds')))
                self.assertFalse(any('hands' in p.name.lower() for p in out.iterdir()))
                for name,sha in report['files'].items():self.assertEqual(digest((out/name).read_bytes()),sha)
                self.assertFalse(report['surface_contact_qualified']);self.assertFalse(report['game_modified'])
                with self.assertRaises(FileExistsError):hands.build('FG42',{s:b'invented' for s in hands.HAND_MODELS},self.profile,out)

    def test_loader_checks_manifest_and_clip_bytes_against_reproduced_modern_bank(self):
        import rigid_weapon_hand_audit as checks
        compiled=self.compiled['FG42'];clips,row=self.invented();raw_hand=b'invented source marker';source=hands.HAND_MODELS[0]
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'fresh'
            with patch.object(hands,'rigid_bank',return_value=compiled),patch.object(hands,'compile_hand_bank',return_value=(clips,row)):
                hands.build('FG42',{s:raw_hand for s in hands.HAND_MODELS},self.profile,out)
            with patch.object(checks,'HAND_PINS',{**checks.HAND_PINS,source:('unused',len(raw_hand),digest(raw_hand))}):
                rig,actual,grips=load_bank(out,'FG42',source,raw_hand,self.profile,compiled)
                self.assertEqual(rig,compiled[1]);self.assertEqual(actual,clips)
                bad=deepcopy(self.profile);bad['cases']['FG42']['translation'][0]+=.01
                with self.assertRaises(ValueError):load_bank(out,'FG42',source,raw_hand,bad,compiled)
                stem,raw=clips['Idle1'];path=out/(stem+'.5ds.disabled');path.write_bytes(raw+b'changed')
                with self.assertRaises(ValueError):load_bank(out,'FG42',source,raw_hand,self.profile,compiled)


if __name__=='__main__':unittest.main()
