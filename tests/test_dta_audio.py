"""Invented mono samples and archive blocks; no licensed WAV fixtures."""
import io
import hashlib
from pathlib import Path
import struct
import sys
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from dta_audio import DpcmMonoDecoder, DPCM_TYPES, WAV_DELTAS
from dta_archive import DtaArchive, Entry
from audit_audio_resources import pcm_metadata


def header(frames=3, channels=1, bits=16, rate=22050):
    size = frames * 2
    return (b'RIFF' + struct.pack('<I', size + 36) + b'WAVEfmt '
            + struct.pack('<IHHIIHH', 16, 1, channels, rate, rate * 2, 2, bits)
            + b'data' + struct.pack('<I', size))


def archive_fixture(version, block_lists):
    """Exercise DtaArchive.read for both layouts, without writing any files."""
    archive = DtaArchive.__new__(DtaArchive)
    archive.version = version
    archive.key = 0
    archive.records = []
    entries, raw = [], bytearray()
    for i, (decoded_size, blocks) in enumerate(block_lists):
        name = f'synthetic{i}.wav'
        offset = len(raw)
        raw.extend(b'\0' * 32 + name.encode())
        data_offset = len(raw)
        if version == 'ISD0':
            for kind, payload in blocks:
                raw.extend(struct.pack('<I', len(payload) + 1) + bytes([kind]) + payload)
        else:
            raw.extend(struct.pack('<' + 'I' * len(blocks), *(len(p) for _, p in blocks)))
            raw.extend(bytes(k for k, _ in blocks))
            for _, payload in blocks:
                raw.extend(payload)
        archive.records.append((0, len(name), offset, data_offset, b''))
        entries.append(Entry(i, name, decoded_size, len(blocks), False, offset, data_offset))
    archive.stream = io.BytesIO(raw)
    return archive, entries


class DtaAudioTests(unittest.TestCase):
    def test_all_seven_tables_and_signed_delta(self):
        self.assertEqual(len(WAV_DELTAS), 896)
        self.assertEqual(hashlib.sha256(struct.pack('<896H', *WAV_DELTAS)).hexdigest(),
                         'fcbd0350caeecc42d5373255b5335da50c2423259184a6526bb22d9edf01e2e2')
        self.assertEqual(DPCM_TYPES, {8, 12, 16, 20, 24, 28, 32})
        for kind, maximum in zip(sorted(DPCM_TYPES), [8192, 12288, 16384, 20480, 24576, 28672, 32767]):
            with self.subTest(kind=kind):
                decoder = DpcmMonoDecoder()
                raw = decoder.decode(kind, header() + struct.pack('<H', 100) + b'\x7f\xff')
                self.assertEqual(struct.unpack('<3H', raw[44:]), (100, (100 + maximum) & 65535, 100))
                decoder.finish(len(raw))

    def test_uint16_wrap_is_not_saturation(self):
        raw = DpcmMonoDecoder().decode(32, header() + b'\xff\xff\x01\x81')
        self.assertEqual(struct.unpack('<3H', raw[44:]), (65535, 1, 65535))

    def test_each_block_resets_sample_and_can_switch_table(self):
        decoder = DpcmMonoDecoder()
        first = decoder.decode(32, header(4) + struct.pack('<H', 10) + b'\x01')
        second = decoder.decode(8, struct.pack('<H', 100) + b'\x01')
        self.assertEqual(struct.unpack('<4H', (first + second)[44:]), (10, 12, 100, 101))
        decoder.finish(len(first + second))

    def test_zero_delta_keeps_sample(self):
        raw = DpcmMonoDecoder().decode(8, header() + struct.pack('<h', -7) + b'\x00\x80')
        self.assertEqual(struct.unpack('<3h', raw[44:]), (-7, -7, -7))

    def test_wave_reader_accepts_exact_pcm_frames(self):
        raw = DpcmMonoDecoder().decode(12, header() + b'\0\0\x01\x81')
        with wave.open(io.BytesIO(raw)) as wav:
            self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()), (1, 2, 22050, 3))
            self.assertEqual(len(wav.readframes(100)), 6)

    def test_truncated_header_and_seed_refuse(self):
        for raw in (b'', b'RIFF', header(), header() + b'\0'):
            with self.subTest(size=len(raw)), self.assertRaisesRegex(ValueError, 'Truncated'):
                DpcmMonoDecoder().decode(32, raw)
        decoder = DpcmMonoDecoder()
        decoder.decode(32, header(4) + b'\0\0')
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            decoder.decode(8, b'\0')

    def test_unsupported_types_refuse(self):
        for kind in (2, 7, 9, 31, 33, 36, 255):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'Unsupported'):
                DpcmMonoDecoder().decode(kind, header() + b'\0\0\0\0')

    def test_stereo_and_non_pcm16_refuse(self):
        for head in (header(channels=2), header(bits=8), header(rate=0)):
            with self.assertRaisesRegex(ValueError, 'mono PCM16'):
                DpcmMonoDecoder().decode(32, head + b'\0\0\0\0')

    def test_noncanonical_chunks_and_lengths_refuse(self):
        for offset, replacement in [(0, b'RIFX'), (12, b'JUNK'), (36, b'LIST'), (16, struct.pack('<I', 18)), (40, struct.pack('<I', 5)), (4, struct.pack('<I', 100))]:
            raw = bytearray(header() + b'\0\0\0\0')
            raw[offset:offset + len(replacement)] = replacement
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                DpcmMonoDecoder().decode(32, bytes(raw))

    def test_payload_overflow_refuses_before_state_change(self):
        decoder = DpcmMonoDecoder()
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            decoder.decode(32, header(1) + b'\0\0\0')
        self.assertIsNone(decoder.expected_size)
        self.assertEqual(decoder.decoded_size, 0)

    def test_payload_underflow_and_mixed_output_refuse(self):
        decoder = DpcmMonoDecoder()
        decoder.decode(32, header(3) + b'\0\0')
        with self.assertRaisesRegex(ValueError, 'Incomplete or mixed'):
            decoder.finish(46)
        decoder = DpcmMonoDecoder()
        decoder.decode(32, header(1) + b'\0\0')
        with self.assertRaisesRegex(ValueError, 'Incomplete or mixed'):
            decoder.finish(50)

    def test_both_archive_versions_decode_multiblock(self):
        for version in ('ISD0', 'ISD1'):
            with self.subTest(version=version):
                archive, entries = archive_fixture(version, [(52, [(32, header(4) + b'\x0a\0\x01'), (8, b'\x64\0\x01')])])
                with archive:
                    raw = archive.read(entries[0])
                self.assertEqual(struct.unpack('<4H', raw[44:]), (10, 12, 100, 101))

    def test_entry_state_does_not_leak_and_repeated_read_is_stable(self):
        archive, entries = archive_fixture('ISD0', [
            (50, [(32, header() + b'\0\0\x01\x01')]),
            (46, [(32, header(1) + b'\x7f\0')]),
        ])
        with archive:
            first = archive.read(entries[0])
            self.assertEqual(archive.read(entries[1])[44:], b'\x7f\0')
            self.assertEqual(archive.read(entries[0]), first)

    def test_archive_declared_size_is_still_enforced(self):
        archive, entries = archive_fixture('ISD0', [(49, [(32, header() + b'\0\0\x01\x01')])])
        with archive, self.assertRaisesRegex(ValueError, 'Decoded size mismatch'):
            archive.read(entries[0])

    def test_non_audio_decoding_unchanged(self):
        self.assertEqual(DtaArchive._decode_block(0, b'plain', 'test'), b'plain')
        self.assertEqual(DtaArchive._decode_block(1, b'\0\0literal', 'test'), b'literal')
        DpcmMonoDecoder().finish(100)  # Not an audio entry.

    def test_metadata_reports_duration_not_engine_success(self):
        result = pcm_metadata(header(3) + b'\0' * 6)
        self.assertEqual(result['sample_frames'], 3)
        self.assertEqual(result['duration_seconds'], 3 / 22050)
        self.assertEqual(len(result['sha256']), 64)
        self.assertFalse(result['listened'])
        self.assertFalse(result['runtime_validated'])

    def test_metadata_rejects_short_pcm_body(self):
        with self.assertRaisesRegex(ValueError, 'Truncated PCM'):
            pcm_metadata(header(3) + b'\0' * 4)


if __name__ == '__main__':
    unittest.main()
