"""Original fitting parameters and invented vertices; no private skeleton fixture."""
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fit_modern_grip_candidates import PARAMETERS, recipe, digit_indices, objective, probe_penalty, surface_witnesses
from build_fitted_fpv_bank import fitted_grips, profile_report
from build_equipment_fpv_view_bank import view_grips
from build_equipment_hand_grips import RECIPE
from build_modern_equipment_hose import digest
from benelli_fpv_rig_audit import HAND_MODELS, HAND_PINS
from hand_pose_ik import validate_basis
from fitted_grip_native_audit import audit as native_audit
from fitted_grip_surface_audit import audit as surface_audit


class FittedGripsTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads(RECIPE.read_text(encoding='utf-8'))

    def test_modern_parameters_adjust_only_selected_hand_and_proper_basis(self):
        values=[.02,.01,15,75,60,30,-30,-45,-20]
        for case in ('F35','F2'):
            for side in ('L','R'):
                base=view_grips(self.spec,case);before=deepcopy(base)
                result,thumb=recipe(base,case,side,values)
                other='R' if side=='L' else 'L'
                self.assertEqual(result[other],base[other])
                validate_basis(result[side]['rest_to_equipment_rotation'])
                self.assertEqual(result[side]['wrist_to_contact_in_rest'],base[side]['wrist_to_contact_in_rest'])
                self.assertEqual(result[side]['elbow_pole'],base[side]['elbow_pole'])
                self.assertEqual(result[side]['finger_curl_degrees'],[v*(1 if side=='L' else -1) for v in values[3:6]])
                self.assertEqual(thumb[side],{'opposition_degrees':-30,'curl_degrees':[-45,-20]})
                self.assertEqual(base,before)

    def test_parameter_range_nonfinite_and_bool_refused(self):
        base=view_grips(self.spec,'F35');values=[0,0,0,90,45,25,0,0,0]
        for axis,value in ((0,-.01),(1,.06),(2,31),(3,111),(4,-1),(6,66),(7,math.nan),(8,True)):
            bad=values[:];bad[axis]=value
            with self.assertRaises(ValueError): recipe(base,'F35','L',bad)
        with self.assertRaises(ValueError): recipe(base,'Unknown','L',values)

    def report(self):
        report={'schema_version':1,'provenance':'MODERNE','runtime_status':'pending',
                'source_hand_sha256':HAND_PINS[HAND_MODELS[0]][2],
                'source_recipe_sha256':digest(RECIPE.read_bytes()),'cases':{}}
        values=[0,0,0,90,45,25,0,0,0]
        for case in ('F35','F2'):
            report['cases'][case]={};base=view_grips(self.spec,case)
            for side in ('L','R'):
                chosen,thumb=recipe(base,case,side,values)
                report['cases'][case][side]={'parameters':dict(zip(PARAMETERS,values)),
                    'grip':chosen[side],'thumb':thumb[side],'auto_promoted':False,'contact_qualified':False}
        return report

    def test_report_reconstructs_choices_instead_of_trusting_transforms(self):
        report=self.report()
        for case in ('F35','F2'):
            grips,thumb=fitted_grips(report,self.spec,case)
            self.assertEqual(grips['L'],report['cases'][case]['L']['grip'])
            self.assertEqual(thumb['R'],report['cases'][case]['R']['thumb'])
        for mutate in (lambda r:r.update(provenance='OFFICIEL'),
                       lambda r:r.update(source_recipe_sha256='0'*64),
                       lambda r:r['cases']['F35']['L'].update(auto_promoted=True),
                       lambda r:r['cases']['F35']['L']['grip']['contact_offset'].__setitem__(0,.01),
                       lambda r:r['cases']['F35']['R']['thumb'].update(opposition_degrees=10)):
            bad=deepcopy(report);mutate(bad)
            with self.assertRaises(ValueError): fitted_grips(bad,self.spec,'F35')

    def test_objective_penalizes_penetration_and_separated_digits(self):
        support=[((1,0,0),1),((-1,0,0),1),((0,1,0),1),((0,-1,0),1),((0,0,1),1),((0,0,-1),1)]
        indices=list(range(5));digits={i:[i] for i in indices}
        score,stats=objective([(1,0,0)]*5,support,indices,digits)
        self.assertEqual(score,0);self.assertEqual(stats['inside'],0)
        self.assertGreater(objective([(0,0,0)]*5,support,indices,digits)[0],score)
        self.assertGreater(objective([(1.1,0,0)]*5,support,indices,digits)[0],score)

    def test_five_digits_are_distinguished_without_exporting_skin(self):
        skin={'nodes':[{'index':i+1,'name':f'Bip01 L Finger{i}'} for i in range(5)],
              'joint_node_indices':list(range(1,6)),'parents':[0]*5,'pairs':[[i,0] for i in range(1,6)]}
        indices,digits=digit_indices(skin,'L')
        self.assertEqual(indices,list(range(5)));self.assertEqual(digits,{i:[i] for i in range(5)})
        with self.assertRaises(ValueError):digit_indices(skin,'R')

    def test_surface_probes_find_crossings_missed_by_vertices(self):
        support=[((1,0,0),1),((-1,0,0),1),((0,1,0),1),((0,-1,0),1),((0,0,1),1),((0,0,-1),1)]
        volumes=[((-1,-1,-1),(1,1,1),support)]
        points=[(-3,-2,0),(3,-2,0),(0,4,0)]
        plain,_=probe_penalty(points,[0,1,2],[],volumes)
        sampled,metrics=probe_penalty(points,[0,1,2],[(0,1,2)],volumes)
        self.assertEqual(plain,0);self.assertGreater(sampled,0)
        self.assertEqual(metrics['probe_count'],7)
        self.assertEqual(metrics['convex_volumes'],1)
        self.assertEqual(metrics['probe_max_depth'],1)

    def test_clipped_surface_witness_stays_on_its_private_triangle(self):
        support=[((1,0,0),1),((-1,0,0),1),((0,1,0),1),((0,-1,0),1),((0,0,1),1),((0,0,-1),1)]
        volumes=[((-1,-1,-1),(1,1,1),support)]
        points=[(-3,-2,0),(3,-2,0),(0,4,0)]
        witnesses=surface_witnesses(points,[(0,1,2)],volumes)
        self.assertEqual(len(witnesses),1)
        face,weights=witnesses[0]
        self.assertEqual(face,(0,1,2));self.assertAlmostEqual(sum(weights),1)
        self.assertGreaterEqual(min(weights),0)
        point=[sum(points[i][j]*w for i,w in zip(face,weights)) for j in range(3)]
        self.assertTrue(all(-1<v<1 for v in point))
        score,metrics=probe_penalty(points,[],[],volumes,witnesses)
        self.assertGreater(score,0);self.assertEqual(metrics['probe_count'],1)
        outside=[(x,y,z+3) for x,y,z in points]
        self.assertEqual(surface_witnesses(outside,[(0,1,2)],volumes),[])

    def test_native_bank_suffix_rejects_path_escape_before_any_game_read(self):
        for suffix in ('../FittedGrips_v3','FittedGrips_v0','FittedGrips_v1/Other','Other'):
            with self.assertRaises(ValueError):native_audit(None,None,suffix,None)

    def test_surface_bank_suffix_rejects_path_escape_before_any_game_read(self):
        for suffix in ('../FittedGrips_v3','FittedGrips_v0','FittedGrips_v1/Other','Other'):
            with self.assertRaises(ValueError):surface_audit(None,None,bank_suffix=suffix)

    def test_portable_modern_profile_reproduces_grips_without_private_fit_report(self):
        profile=json.loads((RECIPE.parent/'modern-fitted-hand-grips.json').read_text(encoding='utf-8'))
        expanded=profile_report(profile,self.spec)
        for case in ('F35','F2'):
            self.assertEqual(fitted_grips(profile,self.spec,case),fitted_grips(expanded,self.spec,case))
        reformatted=json.loads(json.dumps(profile,indent=4,sort_keys=True))
        self.assertEqual(profile_report(reformatted,self.spec),expanded)
        for mutate in (lambda p:p.update(source_recipe_sha256='0'*64),
                       lambda p:p.update(runtime_status='validated'),
                       lambda p:p['cases']['F35']['L'].update(bone_poses=[]),
                       lambda p:p['cases']['F2']['R']['parameters'].update(normal_shift=True)):
            bad=deepcopy(profile);mutate(bad)
            with self.assertRaises(ValueError):profile_report(bad,self.spec)


if __name__=='__main__':unittest.main()
