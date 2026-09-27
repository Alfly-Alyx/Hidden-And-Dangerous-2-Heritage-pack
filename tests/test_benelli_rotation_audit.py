"""Invented 5DS curves and a reference-only double, never native proof."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import benelli_rotation_audit as audit
from ls3d_math_oracle import rotation_sample,TIME_FACTOR
from test_five_ds import invented_clip


class ReferenceDouble:
    def __init__(self,mutate=None):self.mutate=mutate
    def sample_rotation(self,frames,values,time):
        result={**rotation_sample(frames,values,time),'native_channel_sample_match':True,
                'inputs_preserved':True,'max_error':0,'time_integer_units_per_frame':40,'time_factor_float32':TIME_FACTOR}
        result.update(dict.fromkeys(('blending_executed','whole_track_evaluated','time_unit_seconds_qualified',
                                     'library_loaded','game_started','scene_evaluated'),False))
        if self.mutate:self.mutate(result)
        return result


class BenelliRotationAuditTests(unittest.TestCase):
    def sources(self):
        raw=invented_clip([('Root',{'rotation':([0,5,10],[(0,0,0,1),(0,0,math.sin(.5),math.cos(.5)),(0,0,1,0)])})])
        return {'models/#fpvbeneli'+state+'.5ds':raw for state in audit.STATES}

    def test_sampling_includes_key_boundaries_midpoints_and_integer_wrap_limit(self):
        self.assertEqual(audit.sample_times([0,5,10]),[0,1,100,199,200,201,300,399,400,401])
        self.assertEqual(audit.sample_times([65535]),[0,65535*40-1,65535*40,65535*40+1])

    def test_report_contains_counts_and_hashes_but_no_key_values_or_runtime_claims(self):
        report=audit.audit(self.sources(),ReferenceDouble())
        self.assertEqual((report['rotation_channels'],report['rotation_keys'],report['samples']),(9,27,90))
        self.assertEqual(len(report['clips']),9)
        for row in report['clips'].values():self.assertNotIn('value',row);self.assertNotIn('values',row)
        for key in ('time_unit_seconds_qualified','partial_pose_inheritance_qualified','skin_evaluated',
                    'native_library_loaded','game_started','game_modified','commercial_geometry_or_keys_exported'):
            self.assertFalse(report[key])

    def test_incomplete_nonfinite_or_engine_claiming_receipts_are_rejected(self):
        for key,value in (('native_channel_sample_match',1),('inputs_preserved',1),('max_error',math.nan),
                          ('max_error',.1),('value',[0,0,0,math.inf]),('branch','unknown'),
                          ('blending_executed',True),('time_unit_seconds_qualified',True)):
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'receipt'):
                audit.audit(self.sources(),ReferenceDouble(lambda r:r.update({key:value})))

    def test_missing_source_and_rotationless_clip_are_not_silently_skipped(self):
        sources=self.sources();sources.pop(next(iter(sources)))
        with self.assertRaises(KeyError):audit.audit(sources,ReferenceDouble())
        raw=invented_clip([('Root',{'position':([0],[(0,0,0)])})])
        sources=self.sources();sources[next(iter(sources))]=raw
        with self.assertRaisesRegex(ValueError,'No Benelli rotation'):audit.audit(sources,ReferenceDouble())


if __name__=='__main__':unittest.main()
