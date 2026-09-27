"""Invented channel fixtures and reference double; not proof of engine behavior."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import benelli_vector_audit as audit
from ls3d_math_oracle import vector_sample,TIME_FACTOR
from test_five_ds import invented_clip


class ReferenceDouble:
    def __init__(self,mutate=None):self.mutate=mutate
    def sample_vector(self,kind,frames,values,time):
        result={**vector_sample(frames,values,time),'native_channel_sample_match':True,'channel_kind':kind,
                'inputs_preserved':True,'max_error':0,'time_integer_units_per_frame':40,'time_factor_float32':TIME_FACTOR}
        result.update(dict.fromkeys(('blending_executed','whole_track_evaluated','time_unit_seconds_qualified',
                                     'library_loaded','game_started','scene_evaluated'),False))
        if self.mutate:self.mutate(result)
        return result


class BenelliVectorAuditTests(unittest.TestCase):
    def sources(self,scale=True):
        channels={'position':([0,5,10],[(0,0,0),(1,2,3),(-1,-2,-3)])}
        if scale:channels['scale']=([0,10],[(1,1,1),(2,1,.5)])
        raw=invented_clip([('Root',channels)])
        return {'models/#fpvbeneli'+state+'.5ds':raw for state in audit.STATES}

    def test_counts_are_separate_and_report_does_not_export_values(self):
        progress=[];report=audit.audit(self.sources(),ReferenceDouble(),lambda state,row:progress.append(state))
        self.assertEqual(report['totals']['position'],{'channels':9,'keys':27,'samples':90})
        self.assertEqual(report['totals']['scale'],{'channels':9,'keys':18,'samples':54})
        self.assertEqual(len(progress),9)
        for row in report['clips'].values():self.assertNotIn('values',row)
        for key in ('skin_evaluated','blending_executed','time_unit_seconds_qualified','native_library_loaded',
                    'game_started','game_modified','commercial_geometry_or_keys_exported'):self.assertFalse(report[key])

    def test_absent_scale_is_reported_as_zero_not_fabricated(self):
        report=audit.audit(self.sources(False),ReferenceDouble())
        self.assertEqual(report['totals']['scale'],{'channels':0,'keys':0,'samples':0})

    def test_invalid_receipts_cannot_become_native_proofs(self):
        for key,value in (('native_channel_sample_match',1),('channel_kind','rotation'),('max_error',math.nan),
                          ('value',[1,2,math.inf]),('value',[1,2]),('blending_executed',True),
                          ('time_integer_units_per_frame',25),('branch','spherical')):
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'receipt'):
                audit.audit(self.sources(),ReferenceDouble(lambda r:r.update({key:value})))

    def test_missing_source_and_positionless_corpus_fail_closed(self):
        with self.assertRaises(KeyError):audit.audit({},ReferenceDouble())
        raw=invented_clip([('Root',{'rotation':([0],[(0,0,0,1)])})])
        with self.assertRaisesRegex(ValueError,'No Benelli position'):
            audit.audit({'models/#fpvbeneli'+s+'.5ds':raw for s in audit.STATES},ReferenceDouble())


if __name__=='__main__':unittest.main()
