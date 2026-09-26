import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import benelli_fpv_inspector as inspector
from test_benelli_fpv_static import source
from test_five_ds import invented_clip


class InspectorTests(unittest.TestCase):
    def fixture(self):
        return {'models/#fpvbeneliaim.4ds':source(),
                'models/#fpvbeneliaim.5ds':invented_clip(),
                'maps/fixture.bmp':b'invented bitmap', 'sounds/fixture.wav':b'invented audio'}

    def test_plain_geometry_and_raw_channels_remain_separate(self):
        data=inspector.inspection_data(self.fixture(),('aim',))
        self.assertFalse(data['animation_playback']); self.assertFalse(data['engine_validated'])
        self.assertEqual(data['key_mode'],'raw_samples_no_interpolation')
        self.assertEqual(len(data['pairs']['aim']['vertices']),12)
        self.assertEqual(len(data['pairs']['aim']['nodes']),8)
        self.assertEqual(data['pairs']['aim']['tracks'][0]['channels']['position']['values'][-1],[1,2,3])
        self.assertEqual(set(data['audio']),{'sounds/fixture.wav'})

    def test_self_contained_output_roundtrip_and_network_block(self):
        html=inspector.render(self.fixture(),('aim',))
        payload=json.loads(re.search(r'id="resource-data">(.*?)</script>',html,re.S).group(1))
        self.assertEqual(payload['pairs']['aim']['frame_end'],10)
        self.assertIn("connect-src 'none'",html); self.assertIn("default-src 'none'",html)
        self.assertNotIn('__FPV_DATA__',html); self.assertNotIn('https://',html)
        self.assertNotIn('fetch(',html); self.assertNotIn('.play()',html)

    def test_payload_cannot_end_the_data_script(self):
        unsafe={'name':'</script><script>alert(1)</script>&'}
        with patch.object(inspector,'inspection_data',return_value=unsafe): html=inspector.render({},())
        encoded=re.search(r'id="resource-data">(.*?)</script>',html,re.S).group(1)
        self.assertEqual(json.loads(encoded),unsafe); self.assertNotIn('<',encoded)

    def test_corrupt_pair_does_not_render_partial_inspector(self):
        data=self.fixture(); data['models/#fpvbeneliaim.5ds']=b'bad'
        with self.assertRaises(ValueError): inspector.render(data,('aim',))


if __name__=='__main__': unittest.main()
