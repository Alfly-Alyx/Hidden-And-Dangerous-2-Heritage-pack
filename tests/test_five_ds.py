"""Fabricated 5DS tracks; no commercial keyframes or engine assumptions."""
import math
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from five_ds import parse_5ds


def invented_clip(tracks=None, end=10):
    if tracks is None:
        tracks = [('root', {'rotation':([0,end],[(0,0,0,1),(0,1,0,0)]),
                            'position':([0,end],[(0,0,0),(1,2,3)]),
                            'scale':([0,end],[(1,1,1),(0,0,0)])})]
    data=bytearray(struct.pack('<HH',len(tracks),end) + bytes(8*len(tracks)))
    data.extend(bytes((-len(data))%16))
    offsets=[]
    for name,channels in tracks:
        offset=len(data)
        data.extend(struct.pack('<I',sum({'rotation':4,'position':2,'scale':8}[k] for k in channels)))
        for kind in ('rotation','position','scale'):
            if kind not in channels: continue
            frames,values=channels[kind]
            data.extend(struct.pack('<H',len(frames)))
            data.extend(struct.pack('<'+'H'*len(frames),*frames))
            if kind=='rotation': data.extend(bytes((-len(data))%16))
            elif len(frames)%2==0: data.extend(bytes(2))
            for row in values: data.extend(struct.pack('<'+'f'*len(row),*row))
        offsets.append(offset)
    for i,((name,_),offset) in enumerate(zip(tracks,offsets)):
        struct.pack_into('<II',data,4+i*8,len(data),offset)
        data.extend(name.encode('cp1252')+b'\0')
    return b'5DS\0'+struct.pack('<H',122)+bytes(8)+struct.pack('<I',len(data))+data


def modified(raw, offset, fmt, *values):
    data=bytearray(raw)
    struct.pack_into('<'+fmt,data,offset,*values)
    return bytes(data)


class FiveDsTests(unittest.TestCase):
    def test_three_channels_and_terminal_key_are_preserved_without_invented_fps(self):
        p=parse_5ds(invented_clip())
        self.assertEqual(p['frame_end'],10)
        self.assertEqual(p['track_count'],1)
        self.assertEqual(p['tracks'][0]['channels']['position']['frames'],[0,10])
        self.assertEqual(p['tracks'][0]['channels']['scale']['values'][-1],[0,0,0])
        self.assertIsNone(p['frame_rate'])
        self.assertIsNone(p['duration_seconds'])
        self.assertFalse(p['engine_validated'])

    def test_sparse_tracks_and_odd_position_keys_decode_exactly(self):
        p=parse_5ds(invented_clip([('root',{'rotation':([0],[(0,0,0,1)])}),
                                  ('prop',{'position':([0,5,10],[(0,1,2),(3,4,5),(6,7,8)])})]))
        self.assertEqual(p['tracks'][1]['channels']['position']['values'],[[0,1,2],[3,4,5],[6,7,8]])
        self.assertEqual(set(p['tracks'][0]['channels']),{'rotation'})

    def test_header_and_bounds_corruption_refused(self):
        d=invented_clip()
        for raw in (b'',d[:20],b'4DS\0'+d[4:],modified(d,4,'H',20),
                    modified(d,14,'I',len(d)),d+b'x',modified(d,18,'H',0),modified(d,20,'H',0)):
            with self.subTest(raw=raw[:22]),self.assertRaises(ValueError): parse_5ds(raw)

    def test_key_frame_order_duplicates_and_outside_clip_refused(self):
        for frames in ([10,0],[0,0],[0,11]):
            with self.subTest(frames=frames),self.assertRaisesRegex(ValueError,'key frames'):
                parse_5ds(invented_clip([('x',{'position':(frames,[(0,0,0),(1,1,1)])})]))

    def test_unsupported_flags_and_empty_flagged_channel_refused(self):
        d=invented_clip()
        at=18+struct.unpack_from('<I',d,26)[0]
        for flags in (0,1,32,46):
            with self.subTest(flags=flags),self.assertRaisesRegex(ValueError,'flags'):
                parse_5ds(modified(d,at,'I',flags))
        with self.assertRaisesRegex(ValueError,'Empty'):
            parse_5ds(modified(d,at+4,'H',0))

    def test_nonfinite_keys_and_zero_quaternions_refused(self):
        for value in (math.inf,math.nan):
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'Nonfinite'):
                parse_5ds(invented_clip([('x',{'position':([0],[(value,0,0)])})]))
        with self.assertRaisesRegex(ValueError,'quaternion'):
            parse_5ds(invented_clip([('x',{'rotation':([0],[(0,0,0,0)])})]))

    def test_aliases_names_outside_and_unknown_tail_refused(self):
        d=invented_clip([('root',{'rotation':([0],[(0,0,0,1)])}),
                         ('prop',{'position':([0],[(0,0,0)])})])
        n1,k1=struct.unpack_from('<II',d,22)
        for raw in (modified(d,30,'I',n1),modified(d,34,'I',k1),modified(d,22,'I',len(d)),
                    modified(d,26,'I',4),d[:-1]+b'X'):
            with self.subTest(raw=raw[:38]),self.assertRaises(ValueError): parse_5ds(raw)
        with self.assertRaisesRegex(ValueError,'Ambiguous'):
            parse_5ds(invented_clip([('Root',{'position':([0],[(0,0,0)])}),
                                     ('root',{'position':([0],[(0,0,0)])})]))


if __name__=='__main__':
    unittest.main()
