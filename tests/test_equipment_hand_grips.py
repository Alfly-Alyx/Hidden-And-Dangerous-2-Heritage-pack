"""Modern targets and preview provenance; no commercial hand payloads."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_equipment_hand_grips import RECIPE,validate_spec,effective_hands,targets,compile_grips,posed_hand_mesh
from build_modern_equipment_assembly import inputs,compile_assembly
from hand_pose_ik import two_bone,norm,sub
from four_ds_skin import read_reviewed
from benelli_pose_chain_audit import initial_poses
import build_modern_asset as asset
from test_four_ds_skin import fixture


class GripTargetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads(RECIPE.read_text(encoding='utf-8'))
        cls.cases={case:compile_assembly(*inputs(case)) for case in ('F35','F2')}

    def test_case_specific_left_grip_and_unchanged_recipe(self):
        before=deepcopy(self.spec);a=effective_hands(self.spec,'F35');b=effective_hands(self.spec,'F2')
        self.assertEqual(a['R'],b['R']);self.assertNotEqual(a['L']['rest_to_equipment_rotation'],b['L']['rest_to_equipment_rotation'])
        a['L']['contact_offset'][0]=99;self.assertEqual(self.spec,before)

    def test_source_provenance_and_functional_fields_rejected(self):
        rig=self.cases['F35'][0]
        for changes in ({'provenance':'MODERNE'},{'runtime_status':'passed'},{'damage':1},
                        {'assembly_sha256':{'F35':'0'*64,'F2':'0'*64}}):
            spec=deepcopy(self.spec);spec.update(changes)
            with self.assertRaises(ValueError):validate_spec(spec,'F35',rig)
        spec=deepcopy(self.spec);spec['case_overrides']['F2']['L']['native_callback']=1
        with self.assertRaises(ValueError):validate_spec(spec,'F2',self.cases['F2'][0])

    def test_all_authored_targets_are_reachable_with_explicit_synthetic_arm_lengths(self):
        count=0
        for case,(rig,clips,report) in self.cases.items():
            validate_spec(self.spec,case,rig)
            for name,(_,raw) in clips.items():
                for frame in range(report['clips'][name]['frame_end']+1):
                    rows=targets(rig,raw,frame,self.spec,case)
                    for side,row in rows.items():
                        shoulder=[-.16 if side=='L' else .16,0,0]
                        elbow=two_bone(shoulder,row['position'],row['pole'],.28,.24)
                        self.assertAlmostEqual(norm(sub(elbow,shoulder)),.28)
                        self.assertAlmostEqual(norm(sub(row['position'],elbow)),.24);count+=1
        self.assertEqual(count,1140)

    def test_incomplete_sources_rejected_without_commercial_reads(self):
        with self.assertRaisesRegex(ValueError,'Incomplete'):compile_grips('F35',{},self.spec)

    def test_private_preview_uses_serialized_synthetic_faces(self):
        raw=fixture();skin=read_reviewed(raw);poses=initial_poses(raw,skin)
        mesh=posed_hand_mesh(raw,poses,3)
        self.assertEqual(mesh.triangles,[(0,1,2)]);self.assertEqual(mesh.material,3)
        for a,b in zip(mesh.points,skin['vertices']):
            self.assertLess(max(abs(x-y) for x,y in zip(a,b[:3])),1e-6)

    def test_preview_provenance_is_explicit_and_old_default_is_unchanged(self):
        from PIL import ImageDraw
        recipe={'materials':[{'diffuse':[.3,.4,.5]}]};mesh=asset.Mesh('Example',1,[(0,0,0),(1,0,0),(0,1,1)],[(0,1,2)])
        labels=('PRIVE / MAINS DERIVEES','Pose moderne, geometrie commerciale')
        seen=[];original=ImageDraw.ImageDraw.text
        def text(draw,xy,value,*args,**kwargs):seen.append(value);return original(draw,xy,value,*args,**kwargs)
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(ImageDraw.ImageDraw,'text',text):
                asset.preview(recipe,[(mesh,mesh)],Path(directory)/'private.png',labels=labels)
            self.assertEqual(seen[:2],list(labels))
            asset.preview(recipe,[(mesh,mesh)],Path(directory)/'default.png')
            asset.preview(recipe,[(mesh,mesh)],Path(directory)/'explicit.png',labels=(
                'HERITAGE / MODERNE / MODELE EXTERIEUR EXPERIMENTAL',
                'Geometrie originale - rendu hors moteur - ni arme jouable, ni animation FPV'))
            self.assertEqual((Path(directory)/'default.png').read_bytes(),(Path(directory)/'explicit.png').read_bytes())


if __name__=='__main__':unittest.main()
