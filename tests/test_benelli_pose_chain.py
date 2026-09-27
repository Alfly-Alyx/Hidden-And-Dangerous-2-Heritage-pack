"""Synthetic channel windows/chain wiring; no commercial asset required."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from benelli_pose_chain_audit import key_window,times,initial_poses,check_pose,evaluate,audit
from ls3d_math_oracle import rotation_sample,vector_sample
from ls3d_pose_oracle import reference
from four_ds_skin import read_reviewed
from test_four_ds_skin import fixture


class PoseChainTests(unittest.TestCase):
    def test_vector_window_keeps_original_irregular_key_times_and_values(self):
        channel={'frames':[0,3,7,13],'values':[[i,i*.1,-i] for i in range(4)]}
        for time in (0,1,119,120,121,239,279,280,281,519,520,521):
            window=key_window(channel,time)
            self.assertLessEqual(len(window['frames']),2)
            self.assertEqual(vector_sample(**channel,time=time)['value'],vector_sample(**window,time=time)['value'])

    def test_rotation_window_matches_full_180_key_reference(self):
        channel={'frames':[i*3 for i in range(180)],
                 'values':[[0,0,math.sin(i*.01),math.cos(i*.01)] for i in range(180)]}
        for time in (0,1,119,120,121,3481,17003,537*40,65535*40+39):
            window=key_window(channel,time)
            self.assertEqual(rotation_sample(**channel,time=time)['value'],rotation_sample(**window,time=time)['value'])

    def test_held_first_last_and_single_key_windows(self):
        channel={'frames':[2,5],'values':[[0,0,0],[1,2,3]]}
        self.assertEqual(key_window(channel,0)['frames'],[2])
        self.assertEqual(key_window(channel,200)['frames'],[5])
        single={'frames':[12],'values':[[1,1,1]]}
        for time in (0,480,999):self.assertEqual(key_window(single,time),single)

    def test_windows_do_not_mutate_or_alias_original_values(self):
        channel={'frames':[0,2],'values':[[0,0,0],[1,1,1]]};before=deepcopy(channel)
        window=key_window(channel,40);window['frames'][0]=99;window['values'][0][0]=99
        self.assertEqual(channel,before)

    def test_invalid_window_time_empty_or_unsorted_keys_rejected(self):
        for channel,time in (({'frames':[],'values':[]},0),({'frames':[2,1],'values':[[0]*3]*2},0),
                             ({'frames':[0],'values':[[0]*3]},-1)):
            with self.assertRaises(ValueError):key_window(channel,time)

    def test_sample_policies_include_exact_end_without_claiming_seconds(self):
        self.assertEqual(times(10,'boundaries'),[0,1,200,399,400])
        self.assertEqual(times(1,'half-frames'),[0,20,40])
        with self.assertRaises(ValueError):times(0,'boundaries')
        with self.assertRaises(ValueError):times(1,'seconds')

    def test_missing_track_channels_keep_explicit_seed(self):
        raw=fixture();skin=read_reviewed(raw);seeds=initial_poses(raw,skin)
        self.assertEqual(len(seeds),3)
        for seed in seeds.values():self.assertEqual(reference(seed,[])['pose'],seed)
        seed=seeds['B'];changed=reference(seed,[{'active':True,'weight':1,'time':40,
            'channels':{'position':{'frames':[0,2],'values':[[0,0,0],[2,0,0]]}}}])['pose']
        self.assertEqual(changed['position'],[1,0,0]);self.assertEqual(changed['rotation'],seed['rotation'])
        self.assertEqual(changed['scale'],seed['scale'])

    def test_incomplete_pose_is_rejected_before_palette_or_skin(self):
        class Invalid:
            def apply(self,*args):return {'native_synthetic_pose_match':True}
        raw=fixture();skin=read_reviewed(raw)
        with self.assertRaisesRegex(ValueError,'receipt'):
            evaluate(skin,initial_poses(raw,skin),{},0,Invalid(),None,None)

    def test_pose_receipt_shape_nonfinite_and_flags_are_checked(self):
        row={'native_synthetic_pose_match':True,'inputs_preserved':True,
             'extra_pose_evaluated':False,'matrix_rotation_fallback_evaluated':False,
             'event_or_scene_called':False,'skin_evaluated':False,'model_loading_qualified':False,
             'game_started':False,'library_loaded':False,'max_error':0,
             'pose':{'position':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]}}
        check_pose(row)
        for key,value in (('max_error',math.nan),('event_or_scene_called',True),('pose',{}),
                          ('pose',{'position':[math.inf,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]})):
            with self.assertRaises(ValueError):check_pose({**row,key:value})

    def test_unpinned_inputs_cannot_reach_any_native_phase(self):
        with self.assertRaisesRegex(ValueError,'Incomplete pinned'):audit({}, {},None,None,None)


if __name__=='__main__':unittest.main()
