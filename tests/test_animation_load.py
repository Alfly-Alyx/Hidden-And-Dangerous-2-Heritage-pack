"""Synthetic loader input/domain tests without any commercial binary."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_animation_load_oracle import resource_paths,validate
from modern_animation import encode_5ds


class AnimationLoadTests(unittest.TestCase):
    def test_resource_extension_rewrite_preserves_case_and_directory(self):
        for name in ('PROTOTYPE_Demo.I3D','PROTOTYPE_Demo.4ds','Models\\PROTOTYPE_Demo.5ds'):
            requested,cached=resource_paths(name)
            self.assertEqual(requested,name.rsplit('.',1)[0]+'.5ds')
            self.assertEqual(cached,'PROTOTYPE_Demo')

    def test_unreviewed_or_traversing_resource_names_refused(self):
        for name in ('','Demo.I3D','../PROTOTYPE_Demo.I3D','C:\\PROTOTYPE_Demo.I3D',
                     'Models/PROTOTYPE_Demo.I3D','PROTOTYPE_Demo.I3D\0',True,'PROTOTYPE_'+('x'*33)+'.I3D'):
            with self.assertRaises(ValueError):resource_paths(name)

    def test_transform_only_original_fixture_accepted_and_bad_header_refused(self):
        raw=encode_5ds({'provenance':'MODERNE','runtime_status':'pending','frame_end':1,
            'tracks':[{'name':'MOD_demo','channels':{'position':{'frames':[0,1],'values':[[0,0,0],[1,0,0]]}}}]})
        parsed,path,name=validate(raw,'PROTOTYPE_Demo.I3D')
        self.assertEqual((parsed['track_count'],path,name),(1,'PROTOTYPE_Demo.5ds','PROTOTYPE_Demo'))
        for bad in (b'',raw[:-1],b'4DS'+raw[3:],raw+bytes(0xf000)):
            with self.assertRaises(ValueError):validate(bad,'PROTOTYPE_Demo.I3D')


if __name__=='__main__':unittest.main()
