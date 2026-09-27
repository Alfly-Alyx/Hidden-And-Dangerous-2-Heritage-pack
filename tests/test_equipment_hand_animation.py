"""Native derived authoring contracts on synthetic poses; no commercial data."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import modern_animation as motion
from build_equipment_hand_animation import (PROVENANCE,HAND_NAMES,encode_derived_clip,
    bake_tracks,combine_tracks,compile_hand_bank)
from five_ds import parse_5ds
from test_modern_animation import clip,channel


def invented_samples(end=4):
    samples=[]
    for frame in range(end+1):
        row={name:{'position':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]} for name in HAND_NAMES}
        row['Bip01 L Hand']['rotation']=[0,math.sin(frame*.01),0,math.cos(frame*.01)]
        samples.append(row)
    return samples


def derived(tracks,end=4):
    return {'provenance':PROVENANCE,'runtime_status':'pending','frame_end':end,'tracks':tracks}


class DerivedHandAnimationTests(unittest.TestCase):
    def test_namespace_and_provenance_are_separate_from_original_authoring(self):
        track=channel('rotation',[0,4],[[0,0,0,1]]*2,'Bip01 L Hand')
        self.assertEqual(parse_5ds(encode_derived_clip(derived([track])))['tracks'][0]['name'],'Bip01 L Hand')
        with self.assertRaises(ValueError):motion.encode_5ds(clip([track],4))
        with self.assertRaises(ValueError):motion.encode_5ds(derived([track]))
        for change in ({'provenance':'MODERNE'},{'runtime_status':'passed'},{'events':[]}):
            value=derived([track]);value.update(change)
            with self.assertRaises(ValueError):encode_derived_clip(value)

    def test_unknown_bones_paths_events_and_duplicate_names_are_refused(self):
        for name in ('Bip01 L Unknown','../a','Bip01 L Hand\0','Root'):
            with self.assertRaises(ValueError):
                encode_derived_clip(derived([channel('position',[0],[[0,0,0]],name)]))
        track=channel('position',[0],[[0,0,0]],'a')
        with self.assertRaises(ValueError):encode_derived_clip(derived([track,track]))
        with self.assertRaises(ValueError):encode_derived_clip(derived([channel('callback',[0],[[0,0,0]],'a')]))

    def test_dense_rotations_and_constant_channels_are_baked_without_mutating_input(self):
        samples=invented_samples();before=deepcopy(samples);names=sorted(HAND_NAMES)
        tracks=bake_tracks(samples,names,4);self.assertEqual(samples,before)
        parsed=parse_5ds(encode_derived_clip(derived(tracks)))
        self.assertEqual(parsed['track_count'],37)
        by_name={t['name']:t['channels'] for t in parsed['tracks']}
        self.assertEqual(by_name['Bip01 L Hand']['rotation']['frames'],[0,1,2,3,4])
        self.assertEqual(by_name['Bip01 R Hand']['rotation']['frames'],[0,4])
        self.assertEqual(by_name['a']['position']['values'],[[0,0,0]]*2)

    def test_missing_frames_nodes_fields_and_stretch_are_refused(self):
        for mode in ('frame','node','channel','position','scale'):
            samples=invented_samples()
            if mode=='frame':samples.pop()
            elif mode=='node':del samples[1]['a']
            elif mode=='channel':del samples[1]['a']['rotation']
            else:samples[1]['Bip01 L Hand'][mode][0]=.5
            with self.subTest(mode=mode),self.assertRaises(ValueError):bake_tracks(samples,sorted(HAND_NAMES),4)

    def test_existing_native_equipment_keys_survive_merge_exactly(self):
        q=[-.00001745,0,-.00001454,1]
        raw=motion.encode_5ds(clip([channel('rotation',[0,4],[q,q],'MOD_held_pivot')],4),
            preserve_native_rotations=True)
        tracks=bake_tracks(invented_samples(),sorted(HAND_NAMES),4)
        result=combine_tracks(tracks,raw,'PROTOTYPE_Assembly',[0,.14,-.16])
        parsed=parse_5ds(result);by_name={t['name']:t['channels'] for t in parsed['tracks']}
        self.assertEqual(parsed['track_count'],39)
        self.assertEqual(by_name['MOD_held_pivot'],parse_5ds(raw)['tracks'][0]['channels'])
        self.assertEqual(by_name['PROTOTYPE_Assembly']['position']['frames'],[0,4])

    def test_native_key_limit_and_unpinned_sources_are_refused(self):
        track=channel('position',list(range(181)),[[0,0,0]]*181,'a')
        with self.assertRaisesRegex(ValueError,'key count'):encode_derived_clip(derived([track],180))
        with self.assertRaisesRegex(ValueError,'Unreviewed commercial'):compile_hand_bank('F35',b'unknown',{})

    def test_wrist_offset_uses_native_basis_and_already_translated_anchor(self):
        from build_equipment_hand_animation import wrist_from_native,IDENTITY
        hand={'contact_offset':[.02,0,0],'rest_to_equipment_rotation':[[1,0,0],[0,1,0],[0,0,1]],
              'wrist_to_contact_in_rest':[.06,0,0]}
        anchor=IDENTITY[:];anchor[12:15]=[.1,.2,.3]
        self.assertEqual(wrist_from_native(IDENTITY,anchor,hand),[.06000000000000001,.2,.3])
        held=[0,1,0,0,-1,0,0,0,0,0,1,0,0,0,0,1]
        result=wrist_from_native(held,anchor,hand)
        for a,b in zip(result,[.1,.16,.3]):self.assertAlmostEqual(a,b)

    def test_tiny_rotations_follow_native_identity_rule_in_bake_targets(self):
        import json
        from build_equipment_hand_animation import native_grip_targets
        from build_equipment_hand_grips import RECIPE,targets,effective_hands
        from build_modern_equipment_assembly import inputs,compile_assembly
        spec=json.loads(RECIPE.read_text(encoding='utf-8'));rig,clips,_=compile_assembly(*inputs('F35'))
        native=native_grip_targets(rig,clips['Idle1'][1],1,spec,'F35')
        ideal=targets(rig,clips['Idle1'][1],1,spec,'F35')
        hands=effective_hands(spec,'F35')
        for side in ('L','R'):
            self.assertEqual(native[side]['rotation'],hands[side]['rest_to_equipment_rotation'])
        self.assertGreater(max(abs(a-b) for a,b in zip(native['L']['position'],ideal['L']['position'])),1e-5)


if __name__=='__main__':unittest.main()
