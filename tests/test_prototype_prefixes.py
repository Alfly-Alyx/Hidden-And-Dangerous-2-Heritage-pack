"""Prefix diagnostics must never imply recovery of a historical mission."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from prototype_deployment_audit import prefix_comparison


def container(data):
    child = struct.pack('<HI', 0x10, len(data) + 6) + data
    return struct.pack('<HI', 0x4C53, len(child) + 6) + child


class PrefixTests(unittest.TestCase):
    def test_identical_complete_containers_are_not_a_playability_proof(self):
        data = container(b'fixture\0')
        report = prefix_comparison(data, data)
        self.assertTrue(report['fragment_structurally_complete'])
        self.assertTrue(report['reference_structurally_complete'])
        self.assertTrue(report['payload_is_prefix'])
        self.assertFalse(report['automatic_splice_authorized'])
        self.assertEqual(report['runtime_status'], 'pending')

    def test_real_tail_truncation_is_identified_without_authorizing_a_splice(self):
        data = container(b'fixture\0')
        report = prefix_comparison(data[:-3], data)
        self.assertTrue(report['payload_is_prefix'])
        self.assertTrue(report['same_declared_length'])
        self.assertFalse(report['fragment_structurally_complete'])
        self.assertFalse(report['automatic_splice_authorized'])

    def test_header_lengths_are_not_hidden_by_a_matching_payload(self):
        data = container(b'fixture\0')
        other = data[:2] + struct.pack('<I', 9999) + data[6:-1]
        report = prefix_comparison(other, data)
        self.assertTrue(report['payload_is_prefix'])
        self.assertFalse(report['same_declared_length'])
        self.assertEqual(report['fragment_declared_bytes'], 9999)

    def test_first_payload_difference_and_different_kind_are_explicit(self):
        data = container(b'fixture\0')
        other = bytearray(data[:-2])
        other[0] ^= 1
        other[8] ^= 1
        report = prefix_comparison(bytes(other), data)
        self.assertFalse(report['same_container_kind'])
        self.assertFalse(report['payload_is_prefix'])
        self.assertEqual(report['first_payload_mismatch_offset'], 8)

    def test_longer_fragment_is_not_a_prefix_and_short_headers_are_refused(self):
        data = container(b'fixture\0')
        self.assertFalse(prefix_comparison(data, data[:-2])['payload_is_prefix'])
        with self.assertRaises(ValueError):
            prefix_comparison(b'bad', data)


if __name__ == '__main__':
    unittest.main()
