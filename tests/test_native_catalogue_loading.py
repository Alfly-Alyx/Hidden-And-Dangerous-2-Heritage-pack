"""Exercise the stock GDT loader/counters using local commercial data only.

File and allocation operations are test doubles; parsing and mission counting
execute the real game code. No commercial bytes are stored in this test file.
"""
from pathlib import Path
import io
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.research/binary-patch-deps'))
sys.path.insert(0, str(ROOT / 'tools'))
from dta_archive import DtaArchive
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *


class CatalogueMachine:
    def __init__(self, files):
        self.files = files
        self.opened = []
        self.handles = {}
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(0, 0x1000)
        self.uc.mem_map(0x400000, 0x800000)
        self.uc.mem_write(0x401000, (ROOT / 'tmp/stock-menu-analysis.bin').read_bytes())
        self.uc.mem_map(0x2000000, 0x200000)
        self.uc.mem_map(0x3000000, 0x1000000)
        self.stack, self.stop, self.manager = 0x2010000, 0x201f000, 0x2001000
        self.heap = 0x3000000
        self.put(self.manager + 0xec, 2)
        self.uc.hook_add(UC_HOOK_CODE, self.on_code)

    def put(self, at, value): self.uc.mem_write(at, struct.pack('<I', value & 0xffffffff))
    def get(self, at): return struct.unpack('<I', self.uc.mem_read(at, 4))[0]
    def string(self, at):
        data = bytearray()
        while len(data) < 1024:
            ch = self.uc.mem_read(at + len(data), 1)[0]
            if not ch: break
            data.append(ch)
        return data.decode('cp1252')
    def ret(self, args=0, value=0):
        sp = self.uc.reg_read(UC_X86_REG_ESP)
        self.uc.reg_write(UC_X86_REG_EAX, value & 0xffffffff)
        self.uc.reg_write(UC_X86_REG_ESP, sp + 4 + args*4)
        self.uc.reg_write(UC_X86_REG_EIP, self.get(sp))
    def on_code(self, uc, address, size, unused):
        sp = uc.reg_read(UC_X86_REG_ESP)
        if address == 0x7e566f:
            n = self.get(sp + 4)
            result = self.heap
            self.heap += (max(n, 16) + 15) & ~15
            if self.heap >= 0x4000000: raise MemoryError('test allocation limit')
            self.ret(value=result)
        elif address == 0x7e2120:
            self.ret()
        elif address == 0x405620:
            obj = uc.reg_read(UC_X86_REG_ECX)
            name = self.string(self.get(sp + 4)).replace('\\', '/').lower()
            self.opened.append(name)
            data = self.files.get(name)
            if data is None:
                uc.mem_write(obj, b'\0')
                self.ret(2, 0)
            else:
                handle = len(self.handles) + 1
                self.handles[handle] = io.BytesIO(data)
                uc.mem_write(obj, b'\x01')
                self.put(obj + 4, handle)
                uc.mem_write(obj + 8, b'\0')
                self.put(obj + 0x410, 0)
                self.ret(2, 1)
        elif address == 0x7e539e:
            stream = self.handles[self.get(sp + 4)]
            data = stream.read(self.get(sp + 12))
            if data: uc.mem_write(self.get(sp + 8), data)
            self.ret(3, len(data))
        elif address == 0x7e5398:
            stream = self.handles[self.get(sp + 4)]
            offset = struct.unpack('<i', uc.mem_read(sp + 8, 4))[0]
            self.ret(3, stream.seek(offset, self.get(sp + 12)))
        elif address == 0x7e53b0:
            self.ret(1)
        elif address == 0x7e5392:
            raise AssertionError('Stock loader unexpectedly attempted to write a catalogue')

    def call(self, address, ecx, *args):
        self.uc.reg_write(UC_X86_REG_ESP, self.stack)
        self.uc.reg_write(UC_X86_REG_ECX, ecx)
        self.put(self.stack, self.stop)
        for i, value in enumerate(args): self.put(self.stack + 4 + i*4, value)
        try:
            self.uc.emu_start(address, self.stop, count=5000000)
        except Exception as error:
            raise RuntimeError('native catalogue error at %08X' % self.uc.reg_read(UC_X86_REG_EIP)) from error
        if self.uc.reg_read(UC_X86_REG_EIP) != self.stop:
            raise RuntimeError('native catalogue did not return')
        return self.uc.reg_read(UC_X86_REG_EAX)


class NativeCatalogueLoadingTests(unittest.TestCase):
    def test_real_catalogue_loader_sees_installed_test_missions(self):
        game = Path(r'D:\Games\Hidden and Dangerous 2 - Test Menu Personnalise')
        if not (game / 'SabreSquadron.dta').is_file():
            self.skipTest('local test installation not available')
        files = {}
        with DtaArchive(game / 'SabreSquadron.dta') as archive:
            for entry in archive.entries:
                name = entry.name.replace('\\', '/').lower()
                if name in ('gamedata/gamedata00.gdt', 'gamedata/gamedata01.gdt'):
                    files[name] = archive.read(entry)
        for path in (game / 'GameData').glob('*.gdt'):
            files['gamedata/' + path.name.lower()] = path.read_bytes()
        machine = CatalogueMachine(files)
        self.assertEqual(machine.call(0x6bb860, machine.manager) & 255, 1)
        loaded = (machine.get(machine.manager + 12) - machine.get(machine.manager + 8)) // 4
        self.assertEqual(loaded, 6, machine.opened)
        counts = [machine.call(0x6b9350, machine.manager, i) for i in range(loaded)]
        self.assertEqual(counts, [24, 9, 3, 1, 1, 1])


if __name__ == '__main__': unittest.main(verbosity=2)
