"""Strict read-only 5DS v122 transform tracks (HD2), no animation execution.

Original implementation checked against the public RoadTrain/mafia-formats
5ds.bt layout and licensed local files. Notes/unknown flags are deliberately
unsupported, not skipped. A frame count does not establish a frame rate.
"""
from __future__ import annotations

import math
import struct

HEADER = 18
FLAGS = {'rotation': 4, 'position': 2, 'scale': 8}


class Reader:
    def __init__(self, data, start, end):
        self.data, self.position, self.end = data, start, end

    def take(self, count):
        if count < 0 or self.position + count > self.end:
            raise ValueError('5DS read outside selected structure')
        raw = self.data[self.position:self.position+count]
        self.position += count
        return raw

    def values(self, fmt):
        return struct.unpack('<'+fmt, self.take(struct.calcsize('<'+fmt)))

    def align(self, boundary):
        # 5DS offsets and alignment are relative to the data after its header.
        self.take((-(self.position-HEADER)) % boundary)


def parse_5ds(data: bytes) -> dict:
    if len(data) < HEADER+4 or data[:4] != b'5DS\0':
        raise ValueError('Invalid 5DS signature or truncated header')
    version = struct.unpack_from('<H', data, 4)[0]
    if version != 122:
        raise ValueError('Only HD2 5DS version 122 is supported')
    size = struct.unpack_from('<I', data, 14)[0]
    if size != len(data)-HEADER:
        raise ValueError('5DS declared size differs from file')
    reader = Reader(data, HEADER, len(data))
    count, frames = reader.values('HH')
    if not count or not frames or count > 4096:
        raise ValueError('Invalid 5DS track/frame count')
    links = [reader.values('II') for _ in range(count)]
    reader.align(16)
    start = reader.position
    name_offsets = [HEADER+n for n,_ in links]
    key_offsets = [HEADER+k for _,k in links]
    if (len(set(name_offsets)) != count or len(set(key_offsets)) != count
            or min(key_offsets) != start
            or not start <= max(key_offsets) < min(name_offsets) < len(data)
            or max(name_offsets) >= len(data)):
        raise ValueError('Invalid, aliased or overlapping 5DS offsets')
    names = {}
    name_ends = sorted(name_offsets)[1:] + [len(data)]
    for offset,end in zip(sorted(name_offsets),name_ends):
        raw = data[offset:end]
        if not 2 <= len(raw) <= 256 or raw[-1] != 0 or b'\0' in raw[:-1]:
            raise ValueError('Invalid 5DS track name or unparsed name tail')
        name = raw[:-1].decode('cp1252')
        if name.casefold() in {n.casefold() for n in names.values()}:
            raise ValueError('Ambiguous 5DS track name')
        names[offset] = name
    ordered = sorted(key_offsets)
    ends = dict(zip(ordered,ordered[1:]+[min(name_offsets)]))
    tracks = []
    for name_offset,key_offset in zip(name_offsets,key_offsets):
        reader = Reader(data,key_offset,ends[key_offset])
        flags, = reader.values('I')
        if not flags or flags & ~14:
            raise ValueError('Unsupported 5DS flags, including note/event tracks')
        channels = {}
        for channel,flag in FLAGS.items():
            if not flags & flag:
                continue
            n, = reader.values('H')
            if not n:
                raise ValueError('Empty flagged 5DS channel')
            key_frames = list(reader.values('H'*n))
            # All nine commercial Benelli clips include keys at the header's
            # terminal frame (e.g. Arm: 0..60 inclusive), not just 0..59.
            if any(f > frames for f in key_frames) or any(a >= b for a,b in zip(key_frames,key_frames[1:])):
                raise ValueError('5DS key frames are unordered or outside the declared clip')
            if channel == 'rotation':
                reader.align(16)
            elif n % 2 == 0:
                reader.take(2)
            width = 4 if channel == 'rotation' else 3
            values = [list(reader.values('f'*width)) for _ in range(n)]
            if not all(math.isfinite(v) for row in values for v in row):
                raise ValueError('Nonfinite 5DS transform key')
            if channel == 'rotation' and any(sum(v*v for v in row) < 1e-12 for row in values):
                raise ValueError('Zero 5DS quaternion')
            channels[channel] = {'frames':key_frames,'values':values}
        if reader.position != reader.end:
            raise ValueError(f'Unparsed 5DS track tail: {reader.end-reader.position} bytes ({names[name_offset]})')
        tracks.append({'name':names[name_offset],'flags':flags,'channels':channels,
                       'offset':key_offset,'end':reader.end})
    return {'version':version,'frame_end':frames,'track_count':count,'tracks':tracks,
            'frame_rate':None,'duration_seconds':None,'engine_validated':False}
