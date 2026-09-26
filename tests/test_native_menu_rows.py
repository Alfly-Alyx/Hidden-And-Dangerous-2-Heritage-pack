"""Native flat-list construction tests. Scene cloning/text lookup are doubles;
the actual stock row definitions, IDs and vectors execute in the x86 emulator.
"""
import struct
import unittest
from test_native_custom_menu import Machine
from unicorn.x86_const import *


class RowMachine(Machine):
    def __init__(self):
        super().__init__()
        self.counts = [24, 9, 3, 1, 1, 1]
        self.owner = 0x2007000
        self.put(self.owner + 0x40, 0x14000000)
        self.put(self.owner + 0x28, 0x2007800)
        self.put(self.owner + 0x2c, 0x2007800 + 7*4)
        self.put(self.owner + 0x30, 0x2007800 + 7*4)
        self.uc.mem_write(0x2007900, struct.pack('<II', 100, 4) + b'Name\0')

    def on_code(self, uc, address, size, unused):
        sp = self.reg(UC_X86_REG_ESP)
        if address == 0x7e53c2:  # aligned allocation
            allocated = self.heap
            self.heap += (self.get(sp + 4) + 15) & ~15
            self.return_call(allocated)
        elif address == 0x7e2120:
            self.return_call()
        elif address == 0x66dcf0:  # clone geometry is outside the row-ID test
            self.return_call(1, 3)
        elif address == 0x6b9040:
            self.return_call(0x2007900, 2)
        elif address == 0x644da0:  # font/scene projection, not visibility
            self.return_call(1, 2)
        elif address == 0x405100:  # native formatted string output object
            value = ('row%d' % self.get(sp + 12)).encode('ascii')
            target = self.heap
            self.heap += 64
            self.uc.mem_write(target, struct.pack('<II', 1, len(value)) + value + b'\0')
            self.put(self.get(sp + 4), target)
            self.return_call()
        else:
            super().on_code(uc, address, size, unused)

    def build(self):
        self.put(self.stack, self.stop)
        for i, value in enumerate((self.owner, 0, 0, 0x2008000), 1):
            self.put(self.stack + i*4, value)
        self.uc.reg_write(UC_X86_REG_ESP, self.stack)
        self.uc.reg_write(UC_X86_REG_ECX, self.screen)
        try:
            self.uc.emu_start(0x63a1a0, self.stop, count=1000000)
        except Exception as error:
            raise RuntimeError('row builder failed at %08X' % self.reg(UC_X86_REG_EIP)) from error
        if self.reg(UC_X86_REG_EIP) != self.stop:
            raise AssertionError('row builder did not return: %08X' % self.reg(UC_X86_REG_EIP))
        self.group = self.get(self.get(self.owner + 0x2c) - 4)
        return [self.get(slot) for slot in range(self.get(self.group + 0x34),
                                                self.get(self.group + 0x38), 4)]


class NativeRowTests(unittest.TestCase):
    def test_actual_builder_creates_custom_rows_with_refresh_target_ids(self):
        m = RowMachine()
        rows = m.build()
        self.assertEqual(m.get(m.group + 8), 0x14800000)
        ids = [m.get(row + 8) for row in rows]
        self.assertEqual(len(rows), sum(m.counts) - 1)  # tutorial is excluded
        self.assertEqual(ids, [0x14800000 | (n << 12) for n in range(1, 39)])
        m.run_stock_refresh = True
        for view in (3, 4, 5):
            m.put(m.exports['MenuView'], view)
            m.messages.clear()
            m.reload()
            visible = [message[2] for message in m.messages if message[1] == 0x2000083]
            self.assertEqual(visible, [0x14800000 | (sum(m.counts[:view]) << 12)])
            self.assertIn(visible[0], ids)

    def test_hidden_native_list_reveals_rows_after_category_change(self):
        m = RowMachine()
        definitions = m.build()
        m.preload()
        m.install_runtime_controls()
        group = m.runtime_controls[0x14800000]
        m.put(group, 0x814a08)  # real list-group vtable, not a text-button double
        m.put(group + 0x6c, 0xffffffff)
        for offset in (8, 12, 16, 0x74, 0x7c, 0x88): m.put(group + offset, 0)
        m.put(group + 0x94, 17)
        m.put(group + 0x98, 0)
        m.put(group + 0x9c, 16)
        rows = {}
        vector = 0x2009000
        for index, definition in enumerate(definitions):
            row = m.heap
            m.heap += 0x200
            scene = row + 0x100
            target = m.get(definition + 8)
            rows[target] = row
            m.put(row, 0x813cc0)
            m.put(row + 0x60, target)
            m.put(row + 0x50, scene)
            m.put(scene, 0x3001000)
            m.put(vector + index*4, row)
        m.put(group + 0xa4, vector)
        m.put(group + 0xa8, vector + len(rows)*4)
        m.put(group + 0xac, vector + len(rows)*4)

        def flush():
            while m.pending_messages:
                pending, m.pending_messages = m.pending_messages, []
                for message in pending:
                    target = message[0]
                    if target == 0x14800000:
                        packet = 0x200E000
                        m.uc.mem_write(packet, struct.pack('<6I', *message))
                        try:
                            m.run(0x659d50, (packet,), {UC_X86_REG_ECX: group})
                        except Exception as error:
                            raise RuntimeError('message %s failed at %08X, return %08X' % (
                                [hex(x) for x in message], m.reg(UC_X86_REG_EIP),
                                m.get(m.reg(UC_X86_REG_ESP)))) from error
                    else:
                        m.pending_messages = [message]
                        m.flush_visibility()

        m.run_stock_refresh = True
        for view in (2, 3, 2, 4, 2, 5, 2, 3):
            m.put(m.exports['MenuView'], view)
            m.reload()
            flush()
            if view >= 3:
                target = 0x14800000 | (sum(m.counts[:view]) << 12)
                self.assertEqual(m.uc.mem_read(group + 0x65, 1)[0], 1)
                self.assertEqual(m.uc.mem_read(rows[target] + 0x65, 1)[0], 1,
                                 'List parent visible but mission row remains hidden')
                self.assertEqual(m.get(group + 12) - m.get(group + 8), 4)


if __name__ == '__main__': unittest.main(verbosity=2)
