"""Synthetic relay boundaries and recursive-refresh contract, no game files."""
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_relay as relay
from native_hand_hook import ENTRY
from ls3d_animation_stream_oracle import validate


class NativeHandRelayTests(unittest.TestCase):
    def test_patch_is_one_exact_call_and_nop_at_reviewed_boundary(self):
        data=relay.relay_patch(relay.HOOK_ORIGINAL)
        self.assertEqual(len(data),6);self.assertEqual(data[0],0xe8);self.assertEqual(data[-1],0x90)
        self.assertEqual(relay.HOOK_SITE+5+struct.unpack_from('<i',data,1)[0],ENTRY)

    def test_unreviewed_bytes_addresses_or_scalar_types_refused(self):
        for original,site,target in ((b'',relay.HOOK_SITE,ENTRY),(bytearray(relay.HOOK_ORIGINAL),relay.HOOK_SITE,ENTRY),
                (relay.HOOK_ORIGINAL,relay.HOOK_SITE+1,ENTRY),(relay.HOOK_ORIGINAL,relay.HOOK_SITE,ENTRY+1),
                (relay.HOOK_ORIGINAL,True,ENTRY),(relay.HOOK_ORIGINAL,relay.HOOK_SITE,False)):
            with self.assertRaisesRegex(ValueError,'patch contract'):relay.relay_patch(original,site,target)

    def test_patch_change_checks_phase_and_exact_current_bytes(self):
        m=object.__new__(relay.HandRelayOracle);m.phase=None;m.adapter=SimpleNamespace(mode=None)
        m.uc=Mock();m.patched=False;m.patch=relay.relay_patch(relay.HOOK_ORIGINAL)
        m.uc.mem_read.return_value=b'changed'
        with self.assertRaisesRegex(ValueError,'lifecycle'):m.set_patch(True)
        m.uc.mem_write.assert_not_called()
        m.uc.mem_read.return_value=relay.HOOK_ORIGINAL;m.set_patch(True)
        m.uc.mem_write.assert_called_once_with(relay.HOOK_SITE,m.patch)
        m.uc.ctl_remove_cache.assert_called_once_with(relay.MODEL_TICK,relay.RELAY_END)
        self.assertTrue(m.patched)
        m.uc.reset_mock();m.phase='tick'
        with self.assertRaisesRegex(ValueError,'active'):m.set_patch(False)
        m.uc.mem_read.assert_not_called()

    def test_fixture_steps_include_empty_pause_zero_weight_detach_and_reattach(self):
        for turned in (False,True):
            data,arena,offsets,roles,names,clips,poses=relay.fixture(turned)
            _,_,steps=validate(names,clips,poses,relay.sequence_steps(),9)
            self.assertEqual(len(arena),65536);self.assertEqual(len(roles),11)
            self.assertEqual(sum(s['kind']=='tick' for s in steps),13)
            self.assertEqual(steps[0],{'kind':'tick','delta':40})
            self.assertEqual(sum(s['kind']=='attach' and s['clip']=='A' for s in steps),2)
            self.assertEqual(sum(s['kind']=='attach' and s['clip'] is None for s in steps),2)

    def test_recursive_refresh_clears_dirty_state_and_updates_owning_visual(self):
        data,arena,offsets,*_=relay.fixture();mutable=bytearray(arena);model=bytearray(0x170)
        struct.pack_into('<I',mutable,offsets[4]+0xe0,0x40000008)
        for at in offsets:struct.pack_into('<I',mutable,at+0x164,0x18)
        struct.pack_into('<I',mutable,0xf0e0,0x11c);struct.pack_into('<I',mutable,0xf1d0,0x60000)
        after,updated=relay.reference_model_refresh(bytes(mutable),data['parents'],bytes(model))
        read=lambda at:struct.unpack_from('<I',after,at)[0]
        self.assertEqual(read(0xf218),1);self.assertEqual(read(0xf1d0),0)
        self.assertEqual(read(0xf0e0),0x4000001c)
        for i in (4,5,6):self.assertEqual(read(offsets[i]+0x104),1);self.assertEqual(read(offsets[i]+0x164),0)
        for at in offsets:self.assertFalse(read(at+0xe0)&0x40002000)
        self.assertEqual(struct.unpack_from('<I',updated,0xe0)[0],0)
        again=relay.reference_model_refresh(after,data['parents'],updated)
        self.assertEqual(again,(after,updated))

    def test_failure_restores_patch_and_checks_whole_native_image(self):
        m=object.__new__(relay.HandRelayOracle);m.uc=Mock();m.native_size=3;m.native_image=b'abc'
        m.uc.mem_read.return_value=b'abc'
        with patch.object(m,'_run',side_effect=ValueError('fixture failed')),patch.object(m,'set_patch') as restore:
            with self.assertRaisesRegex(ValueError,'fixture failed'):m.run()
            restore.assert_called_once_with(False)
        m.uc.mem_read.return_value=b'abx'
        with patch.object(m,'_run',return_value={}),patch.object(m,'set_patch'):
            with self.assertRaisesRegex(ValueError,'fully restored'):m.run()

    def test_native_refresh_write_guard_excludes_poses_and_overflow(self):
        m=object.__new__(relay.HandRelayOracle);m.refresh_active=True;m.refresh_writes=[(0x1000,0x1004)]
        m.on_write(None,None,0x1000,4,0,None)
        for at,size in ((0x1003,2),(0x2000,16)):
            with self.assertRaisesRegex(ValueError,'flags/counters'):m.on_write(None,None,at,size,0,None)


if __name__=='__main__':unittest.main()
