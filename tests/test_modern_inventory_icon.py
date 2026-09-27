"""Original geometry and colours only; no commercial image fixtures."""
import copy
import io
import json
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import modern_inventory_icon as icon
from build_modern_asset import ROOT


class ModernInventoryIconTests(unittest.TestCase):
    def recipe(self):return json.loads((ROOT/'experimental/FG42/modern-world-model.json').read_text(encoding='utf-8'))

    def test_modern_mesh_render_is_deterministic_and_explicitly_unqualified(self):
        recipe=self.recipe();before=copy.deepcopy(recipe)
        a,report=icon.prepare(recipe);b,_=icon.prepare(recipe)
        self.assertEqual(a,b);self.assertEqual(recipe,before);self.assertEqual(len(a),3126)
        self.assertEqual(report['sha256'],icon.digest(a))
        for flag in ('transparent_background','commercial_bitmap_or_palette_used','native_ui_load_qualified',
                     'engine_background_or_transparency_qualified'):self.assertFalse(report[flag])

    def test_bmp_header_dimensions_palette_and_bottom_up_rows(self):
        from PIL import Image
        image=Image.new('RGB',(64,32),(255,0,0));image.putpixel((1,0),(0,255,0));image.putpixel((2,31),(0,0,255))
        raw=icon.encode_bitmap(image);magic,size,a,b,offset=struct.unpack_from('<2sIHHI',raw)
        self.assertEqual((magic,size,a,b,offset),(b'BM',len(raw),0,0,1078))
        self.assertEqual(struct.unpack_from('<IiiHHII',raw,14),(40,64,32,1,8,0,2048))
        self.assertEqual(raw[offset+2],5);self.assertEqual(raw[offset+31*64+1],30)
        with Image.open(io.BytesIO(raw)) as decoded:self.assertEqual(decoded.convert('RGB').tobytes(),image.tobytes())

    def test_wrong_image_mode_or_dimensions_are_refused(self):
        from PIL import Image
        for mode,size in (('RGBA',(64,32)),('RGB',(32,64)),('P',(64,32))):
            with self.assertRaises(ValueError):icon.encode_bitmap(Image.new(mode,size))

    def test_face_order_does_not_control_occlusion(self):
        from PIL import Image
        triangles=[([(2,2,0),(60,2,0),(2,30,0)],(255,0,0)),
                   ([(2,2,1),(60,2,1),(2,30,1)],(0,255,0))]
        images=[]
        for rows in (triangles,list(reversed(triangles))):
            image=Image.new('RGB',(64,32));icon.draw_triangles(image,rows,(0,0,64,32));images.append(image.tobytes())
        self.assertEqual(*images)


if __name__=='__main__':unittest.main()
