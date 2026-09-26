"""Synthetic raster tests; no external or commercial images."""
from pathlib import Path
import sys
import unittest
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from software_depth import draw_triangles


class SoftwareDepthTests(unittest.TestCase):
    def test_per_pixel_depth_crossing_is_independent_of_face_order(self):
        tilted=([(1,1,9),(9,1,1),(1,9,9)],(255,0,0))
        flat=([(1,1,5),(9,1,5),(1,9,5)],(0,0,255))
        results=[]
        for triangles in ([tilted,flat],[flat,tilted]):
            image=Image.new('RGB',(12,12))
            draw_triangles(image,triangles,(0,0,12,12))
            self.assertEqual(image.getpixel((2,2)),(255,0,0))
            self.assertEqual(image.getpixel((7,1)),(0,0,255))
            results.append(image.tobytes())
        self.assertEqual(results[0],results[1])

    def test_winding_and_clipping_preserve_visible_pixels(self):
        vertices=[(-10,-10,1),(20,0,2),(0,20,3)]
        results=[]
        for points in (vertices,list(reversed(vertices))):
            image=Image.new('RGB',(10,10))
            draw_triangles(image,[(points,(255,255,255))],(2,2,5,5))
            self.assertEqual(image.getpixel((1,3)),(0,0,0))
            self.assertEqual(image.getpixel((4,4)),(255,255,255))
            self.assertEqual(image.getpixel((7,4)),(0,0,0))
            results.append(image.tobytes())
        self.assertEqual(results[0],results[1])

    def test_adjacent_triangles_have_no_cracks_and_degenerate_faces_do_nothing(self):
        image=Image.new('RGB',(8,8))
        triangles=[([(0,0,1),(8,0,1),(8,8,1)],(255,0,0)),
                   ([(0,0,1),(8,8,1),(0,8,1)],(255,0,0)),
                   ([(0,0,5),(4,4,5),(8,8,5)],(0,255,0))]
        draw_triangles(image,triangles,(0,0,8,8))
        self.assertEqual(image.tobytes(),bytes([255,0,0])*64)

    def test_nonfinite_coordinates_and_invalid_regions_are_refused(self):
        image=Image.new('RGB',(8,8))
        with self.assertRaises(ValueError):
            draw_triangles(image,[([(0,0,0),(1,1,1),(2,float('nan'),2)],(255,0,0))],(0,0,8,8))
        with self.assertRaises(ValueError):draw_triangles(image,[],(0,0,-1,8))


if __name__=='__main__':unittest.main()
