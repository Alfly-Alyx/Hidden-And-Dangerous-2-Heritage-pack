"""Offline route regression tests. Does NOT load the ASI or launch the game.

The compiled x86 adapters execute in Unicorn with fake game objects/functions.
These tests cannot validate rendering, ASI startup timing, or real game input.
"""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".research" / "binary-patch-deps"))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *


class Machine:
    def __init__(self, view=0):
        self.pe = pefile.PE(str(ROOT / "build" / "HD2.CustomMenu.experimental.asi"))
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.raw = self.pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(self.base, (len(self.raw) + 4095) & ~4095)
        self.uc.mem_write(self.base, self.raw)
        self.uc.mem_map(0x400000, 0x800000)
        self.uc.mem_map(0x2000000, 0x10000)
        self.uc.mem_map(0x2100000, 0x10000)
        self.uc.mem_map(0x3000000, 0x10000)
        self.uc.mem_map(0x3100000, 0x10000)
        self.exports = {s.name.decode(): self.base + s.address
                        for s in self.pe.DIRECTORY_ENTRY_EXPORT.symbols}
        self.counts = [24, 9, 3, 1, 2, 4]
        self.manager, self.screen, self.control = 0x2000000, 0x2001000, 0x2002000
        self.stop, self.stack = 0x3100000, 0x2108000
        self.put(0x8aea10, self.manager)
        self.put(0x8aea34, 0x2003000)
        self.put(self.manager + 8, 0x2004000)
        self.put(self.manager + 12, 0x2004000 + 4 * len(self.counts))
        self.put(self.manager + 0xe8, view)
        self.put(self.exports["MenuView"], view)
        self.imports = {}
        slot = 0
        for dll in self.pe.DIRECTORY_ENTRY_IMPORT:
            for item in dll.imports:
                target = 0x3000000 + 16 * slot
                slot += 1
                self.put(item.address, target)
                self.imports[target] = item.name.decode()
        self.hooks = {}
        for index in range(self.get(self.exports["MenuHookCount"])):
            fields = struct.unpack("<IIII", self.uc.mem_read(self.exports["MenuHooks"] + index * 48, 16))
            address, length, expected, replacement = fields
            self.hooks[address] = (length, bytes(self.uc.mem_read(expected, length)), replacement)
        self.calls = []
        self.visibility_calls = []
        self.next_control = self.control
        self.uc.hook_add(UC_HOOK_CODE, self.on_code)

    def install_category_controls(self):
        base = self.exports["MenuCategoryControls"]
        controls = [self.control + index * 0x100 for index in range(4)]
        for index, control in enumerate(controls):
            self.put(base + index * 4, control)
        self.put(self.exports["MenuBackControl"], controls[3])
        self.put(self.exports["MenuMissionScreen"], self.screen)
        self.put(self.exports["MenuMissionScene"], 0)
        return controls

    def put(self, address, value):
        self.uc.mem_write(address, struct.pack("<I", value & 0xffffffff))

    def get(self, address):
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def reg(self, register):
        return self.uc.reg_read(register)

    def string(self, address):
        data = bytearray()
        while address and len(data) < 2048:
            value = self.uc.mem_read(address + len(data), 1)[0]
            if not value:
                break
            data.append(value)
        return bytes(data)

    def return_call(self, value=0, arguments=0):
        esp = self.reg(UC_X86_REG_ESP)
        self.uc.reg_write(UC_X86_REG_EAX, value & 0xffffffff)
        self.uc.reg_write(UC_X86_REG_EIP, self.get(esp))
        self.uc.reg_write(UC_X86_REG_ESP, esp + 4 + arguments * 4)

    def on_code(self, uc, address, size, _):
        esp = self.reg(UC_X86_REG_ESP)
        if address == 0x6b9350:
            catalogue = self.get(esp + 4)
            self.return_call(self.counts[catalogue], 1)
        elif address == 0x63ab60:
            self.calls.append(("reload", self.reg(UC_X86_REG_ECX), self.get(self.exports["MenuView"])))
            self.return_call(1)
        elif address == self.exports["MenuSetControlVisible"]:
            self.visibility_calls.append((self.get(esp + 4), self.get(esp + 8)))
            self.return_call()
        elif address == 0x615360:
            self.calls.append(("control", self.string(self.get(esp + 8))))
            control = self.next_control
            self.next_control += 0x100
            self.return_call(control, 2)
        elif address in (0x614e80, 0x614f10, 0x61e100):
            args = tuple(self.get(esp + offset) for offset in range(4, 28, 4))
            self.calls.append((address, args))
            self.return_call()
        elif address in self.imports:
            name = self.imports[address]
            if name == "CreateFileA":
                self.return_call(0xffffffff, 7)  # no real files, ever
            elif name == "sprintf":
                self.uc.mem_write(self.get(esp + 4), b"test\0")
                self.return_call(4)
            elif name == "strlen":
                self.return_call(len(self.string(self.get(esp + 4))))
            else:
                raise AssertionError("Unexpected OS/CRT function: " + name)

    def run(self, entry, args=(), registers=None, until=None):
        for reg in (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
                    UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP):
            self.uc.reg_write(reg, 0)
        self.uc.reg_write(UC_X86_REG_ESP, self.stack)
        self.put(self.stack, self.stop)
        for i, arg in enumerate(args, start=1):
            self.put(self.stack + 4 * i, arg)
        for register, value in (registers or {}).items():
            self.uc.reg_write(register, value)
        if isinstance(entry, str):
            target = self.exports[entry]
        elif entry in self.hooks:
            target = self.hooks[entry][2]
        else:
            target = entry
        self.uc.emu_start(target, until or self.stop, count=10000)
        if self.reg(UC_X86_REG_EIP) != (until or self.stop):
            raise AssertionError("Route did not reach the expected destination")
        return self.reg(UC_X86_REG_EAX)


class NativeMenuTests(unittest.TestCase):
    def test_signatures_match_stock_client(self):
        stock = (ROOT / "tmp" / "stock-menu-analysis.bin").read_bytes()
        for address, (length, expected, _) in Machine().hooks.items():
            with self.subTest(address=hex(address)):
                self.assertEqual(stock[address - 0x401000:address - 0x401000 + length], expected)

    def test_cumulative_offsets_not_just_original_count(self):
        m = Machine()
        for catalogue, expected in enumerate((0, 24, 33, 36, 37, 39)):
            self.assertEqual(m.run("MenuOffset", (catalogue,)), expected)

    def test_decode_every_row_including_official_boundaries(self):
        m = Machine()
        for catalogue, size in enumerate(m.counts):
            for row in range(size):
                encoded = sum(m.counts[:catalogue]) + row
                self.assertEqual(m.run("MenuDecode", (encoded,)), catalogue)
                self.assertEqual(m.reg(UC_X86_REG_EDX), row)

    def test_visibility_points_to_custom_ids(self):
        for catalogue, expected in ((1, 24), (2, 33), (3, 36), (4, 37), (5, 39)):
            m = Machine(catalogue)
            m.put(m.stack + 0x10, catalogue)
            self.assertEqual(m.run(0x63ae61, until=0x63ae6b), expected)

    def test_flat_list_labels_use_the_same_unique_offsets_as_visibility(self):
        for catalogue, expected in ((1, 24), (2, 33), (3, 36), (4, 37), (5, 39)):
            m = Machine(catalogue)
            self.assertEqual(m.run(0x63a3de, registers={UC_X86_REG_EBX: catalogue}, until=0x63a3e7), expected)

    def test_official_browser_excludes_custom_catalogues(self):
        m = Machine()
        m.run(0x63aefa, registers={UC_X86_REG_EAX: 0}, until=0x63aeff)
        m.run(0x63aefa, registers={UC_X86_REG_EAX: 1}, until=0x63af06)
        for view in range(2, 6):
            m = Machine(view)
            m.run(0x63aefa, registers={UC_X86_REG_EAX: view}, until=0x63af06)

    def test_campaign_groups_do_not_create_duplicate_custom_controls(self):
        m = Machine()
        m.run(0x639d68, registers={UC_X86_REG_EAX: 6, UC_X86_REG_EBP: 1}, until=0x639d70)
        m.run(0x639d68, registers={UC_X86_REG_EAX: 6, UC_X86_REG_EBP: 2}, until=0x63a166)
        m.run(0x639d68, registers={UC_X86_REG_EAX: 0, UC_X86_REG_EBP: 0}, until=0x63a166)

    def test_custom_visibility_does_not_unlock_official_missions(self):
        m = Machine(2)
        m.put(m.screen + 0x20c, 7)
        m.run(0x63ae00, registers={UC_X86_REG_EBP: m.screen}, until=0x63af06)
        self.assertEqual(m.reg(UC_X86_REG_EDI), 2)
        self.assertEqual(m.get(m.screen + 0x20c), 100)
        m.put(m.exports["MenuView"], 4)
        m.run(0x63ae00, registers={UC_X86_REG_EBP: m.screen}, until=0x63ae08)
        m.put(m.exports["MenuView"], 0)
        m.run(0x63ae00, registers={UC_X86_REG_EBP: m.screen}, until=0x63ae08)
        self.assertEqual(m.reg(UC_X86_REG_EDI), 0)
        self.assertEqual(m.get(m.screen + 0x20c), 7)

    def test_row_lookup_uses_correct_catalogue_and_local_index(self):
        for row, catalogue, local in ((24, 1, 0), (33, 2, 0), (35, 2, 2), (36, 3, 0), (38, 4, 1), (42, 5, 3)):
            m = Machine(catalogue)
            m.run(0x63b359, registers={UC_X86_REG_ESI: row}, until=0x63b378)
            self.assertEqual(m.get(m.stack + 0x14), catalogue)
            self.assertEqual(m.get(m.stack + 0x48), local)

    def test_three_menu_buttons_open_their_native_mission_lists(self):
        for button, action, expected_view in (
            (0, 0x0CD10000, 4), (1, 0x0CD20000, 3), (2, 0x0CD30000, 5)
        ):
            m = Machine(2)
            controls = m.install_category_controls()
            m.run(
                0x63c090,
                registers={UC_X86_REG_EAX: action, UC_X86_REG_EDI: controls[button]},
                until=0x63be31,
            )
            self.assertEqual(m.get(m.exports["MenuView"]), expected_view)
            self.assertEqual(m.get(m.manager + 0xe8), expected_view)
            self.assertEqual(m.calls, [])

    def test_stale_list_row_is_blocked_on_category_menu(self):
        m = Machine(2)
        m.put(m.control + 0x5c, 24)
        m.run(0x63b310, (0, m.control, 0x4001000, 0), {UC_X86_REG_ECX: m.screen})
        self.assertEqual(m.get(m.exports["MenuView"]), 2)
        self.assertEqual(m.calls, [])

    def test_start_blocked_on_categories_and_detail_offset_preserved(self):
        m = Machine(2)
        m.run(0x6390c9, until=0x6391d4)
        for view, offset in ((3, 36), (4, 37), (5, 39)):
            m = Machine(view)
            self.assertEqual(m.run(0x6390c9, until=0x6390cf), offset)
            self.assertEqual(m.get(m.manager + 0xe8), view)

    def test_stock_button_actions_are_blocked_on_category_menu(self):
        m = Machine(2)
        m.run(0x63c090, registers={UC_X86_REG_EAX: 0x0CE00000}, until=0x63c270)
        self.assertEqual(m.get(m.exports["MenuView"]), 2)
        self.assertEqual(m.calls, [])

    def test_custom_back_returns_each_detail_list_to_category_menu(self):
        for view in range(3, 6):
            m = Machine(view)
            controls = m.install_category_controls()
            m.run(
                0x63c090,
                registers={UC_X86_REG_EAX: 0, UC_X86_REG_EDI: controls[3]},
                until=0x63be31,
            )
            self.assertEqual(m.get(m.exports["MenuView"]), 2)
            self.assertEqual(m.calls, [])

    def test_stock_back_returns_each_detail_list_to_category_menu(self):
        for view in range(3, 6):
            m = Machine(view)
            m.install_category_controls()
            m.run(
                0x63c090,
                registers={UC_X86_REG_EAX: 0x0CC00000},
                until=0x63be31,
            )
            self.assertEqual(m.get(m.exports["MenuView"]), 2)
            self.assertEqual(m.get(m.manager + 0xe8), 2)
            self.assertEqual(m.calls, [])

    def test_mission_browser_local_back_event_returns_to_category_menu(self):
        event = 0x2008000
        for view in range(3, 6):
            m = Machine(view)
            m.install_category_controls()
            m.put(event + 4, 0x02000003)
            m.run(
                0x638e21,
                registers={UC_X86_REG_ECX: event, UC_X86_REG_ESI: m.screen},
                until=0x6391d4,
            )
            self.assertEqual(m.get(m.exports["MenuView"]), 2)
            self.assertEqual(m.get(m.manager + 0xe8), 2)
            self.assertEqual(m.calls, [("reload", m.screen, 2)])

    def test_native_parent_back_event_is_not_consumed_by_mission_dispatch(self):
        event = 0x2008000
        m = Machine(2)
        m.put(event + 4, 0x01000004)
        self.assertEqual(
            m.run(
                0x638e21,
                registers={UC_X86_REG_ECX: event, UC_X86_REG_ESI: m.screen},
                until=0x638e29,
            ),
            0x01000004,
        )
        self.assertEqual(m.get(m.exports["MenuView"]), 2)

    def test_non_back_mission_event_keeps_native_dispatch(self):
        event = 0x2008000
        m = Machine(4)
        m.put(event + 4, 0x02000008)
        result = m.run(
            0x638e21,
            registers={UC_X86_REG_ECX: event, UC_X86_REG_ESI: m.screen},
            until=0x638e29,
        )
        self.assertEqual(result, 0x02000008)
        self.assertEqual(m.get(m.exports["MenuView"]), 4)
        self.assertEqual(m.calls, [])

    def test_custom_back_leaves_category_menu_through_native_back_action(self):
        m = Machine(2)
        controls = m.install_category_controls()
        m.run(
            0x63c090,
            registers={UC_X86_REG_EAX: 0x0CD40000, UC_X86_REG_EDI: controls[3]},
            until=0x63c095,
        )
        self.assertEqual(m.get(m.exports["MenuView"]), 0)
        self.assertEqual(m.get(m.manager + 0xe8), 0)
        self.assertEqual(m.reg(UC_X86_REG_EAX), 0x0CC00000)

    def test_main_custom_button_enters_category_menu(self):
        m = Machine(0)
        m.install_category_controls()
        m.run(
            0x63c090,
            registers={UC_X86_REG_EAX: 0x0CD00000, UC_X86_REG_EDI: 0x2009000},
            until=0x63be31,
        )
        self.assertEqual(m.get(m.exports["MenuView"]), 2)
        self.assertEqual(m.get(m.manager + 0xe8), 2)

    def test_localized_title_ids(self):
        for view, text_id in ((0, 2251), (2, 20402), (3, 20410), (4, 20411), (5, 20412)):
            m = Machine(view)
            m.run(0x63abec, registers={UC_X86_REG_ECX: 2251}, until=0x63abf8)
            self.assertEqual(m.reg(UC_X86_REG_ECX), text_id)

    def test_layout_is_reapplied_after_native_screen_refresh(self):
        for view in range(2, 6):
            m = Machine(view)
            m.put(m.exports["MenuMissionScene"], 0)
            m.put(m.stack + 0x34, 0x12345678)
            m.run(0x63af06, until=0x63af0b)
            self.assertEqual(m.reg(UC_X86_REG_ECX), 0x12345678)
            self.assertEqual(m.reg(UC_X86_REG_EDI), m.stop)

    def test_original_buttons_reset_custom_state(self):
        for entry, end in ((0x63be2c, 0x63be31), (0x63be73, 0x63be78)):
            m = Machine(5)
            m.run(entry, until=end)
            self.assertEqual(m.get(m.exports["MenuView"]), 0)
            self.assertEqual(m.get(m.manager + 0xe8), 0)

    def test_builder_registers_button_and_balances_stack(self):
        m = Machine()
        m.run(0x625c81, registers={UC_X86_REG_ESI: m.screen}, until=0x625c88)
        self.assertEqual(m.calls[0], ("control", b"bcampaign02"))
        self.assertEqual(m.calls[1][1][4], 20402)
        self.assertEqual(m.calls[2][1][3], 0x4003000)
        self.assertEqual(m.calls[3][1][3], 0x4001000)
        self.assertEqual(m.reg(UC_X86_REG_ESP), m.stack - 4)
        self.assertEqual(m.get(m.stack - 4), 0x83ebc0)

    def test_mission_builder_registers_three_menu_buttons(self):
        m = Machine(2)
        frame = m.stack + 0x400
        m.put(frame + 8, m.screen)
        m.put(frame + 12, 0)
        m.run(0x639afe, registers={UC_X86_REG_EBP: frame, UC_X86_REG_ESI: m.control}, until=0x639b06)
        created = [call[1] for call in m.calls if call[0] == "control"]
        self.assertEqual(created, [
            b"bcustom user", b"bcustom multi", b"bcustom explore"
        ])
        configured = [call[1][4] for call in m.calls if call[0] == 0x614f10]
        self.assertEqual(configured, [20411, 20410, 20412])
        self.assertEqual(m.get(m.exports["MenuMissionScreen"]), m.screen)

    def test_detail_builder_does_not_recreate_category_controls(self):
        m = Machine(4)
        frame = m.stack + 0x400
        m.put(frame + 8, m.screen)
        m.put(frame + 12, 0)
        m.run(0x639afe, registers={UC_X86_REG_EBP: frame, UC_X86_REG_ESI: m.control}, until=0x639b06)
        created = [call[1] for call in m.calls if call[0] == "control"]
        self.assertEqual(created, [])
        self.assertEqual(m.get(m.exports["MenuCategoryControls"]), 0)
        self.assertEqual(m.get(m.exports["MenuCategoryControls"] + 4), 0)
        self.assertEqual(m.get(m.exports["MenuCategoryControls"] + 8), 0)

    def test_official_builder_does_not_recreate_category_controls(self):
        m = Machine(0)
        frame = m.stack + 0x400
        m.put(frame + 8, m.screen)
        m.put(frame + 12, 0)
        m.run(0x639afe, registers={UC_X86_REG_EBP: frame, UC_X86_REG_ESI: m.control}, until=0x639b06)
        created = [call[1] for call in m.calls if call[0] == "control"]
        self.assertEqual(created, [])

    def test_category_controls_normalize_action_for_native_dispatch(self):
        m = Machine(2)
        controls = m.install_category_controls()
        m.run("MenuPrepareControl", (controls[1],))
        self.assertEqual(m.get(controls[1] + 0x60), 0x0CD00000)

    def test_each_category_callback_posts_the_native_custom_action(self):
        probe = Machine(2)
        frame = probe.stack + 0x400
        probe.put(frame + 8, probe.screen)
        probe.put(frame + 12, 0)
        probe.run(0x639AFE, registers={UC_X86_REG_EBP: frame}, until=0x639B06)
        callbacks = [call[1][5] for call in probe.calls if call[0] == 0x61E100][::2]
        self.assertEqual(len(callbacks), 3)
        for callback in callbacks:
            with self.subTest(callback=hex(callback)):
                m = Machine(2)
                event = m.control + 0x400
                m.run(callback, (0, event), until=0x63B9A0)
                self.assertEqual(m.get(event + 0x60), 0x0CD00000)

    def test_mission_builder_keeps_the_native_back_control(self):
        m = Machine(4)
        frame = m.stack + 0x400
        m.put(frame + 8, m.screen)
        m.put(frame + 12, 0)
        m.run(
            0x639afe,
            registers={UC_X86_REG_EBP: frame, UC_X86_REG_ESI: m.control},
            until=0x639b06,
        )
        back = m.control
        self.assertEqual(m.get(m.exports["MenuCategoryControls"] + 12), back)
        self.assertEqual(m.get(m.exports["MenuBackControl"]), back)

    def test_category_layout_keeps_native_labels_for_hidden_controls(self):
        for view in (2, 4):
            with self.subTest(view=view, control="start"):
                m = Machine(view)
                m.put(m.stack + 0x10, m.control)
                m.run(0x6396fe, until=0x639703)
                self.assertEqual(m.get(m.exports["MenuStartControl"]), m.control)
                self.assertEqual(m.get(m.reg(UC_X86_REG_ESP)), 0x935)
            with self.subTest(view=view, control="caption"):
                m = Machine(view)
                m.put(m.stack + 0x24, m.control)
                m.run(0x639a17, until=0x639a1c)
                self.assertEqual(m.get(m.exports["MenuCaptionControl"]), m.control)
                self.assertEqual(m.get(m.reg(UC_X86_REG_ESP)), 0x8D2)
            with self.subTest(view=view, control="resume"):
                m = Machine(view)
                m.run(0x639a94, registers={UC_X86_REG_EAX: m.control}, until=0x639a99)
                self.assertEqual(m.get(m.exports["MenuResumeControl"]), m.control)
                self.assertEqual(m.get(m.reg(UC_X86_REG_ESP)), 0x839)

    def test_category_layout_shows_only_categories_and_real_back_control(self):
        m = Machine(2)
        categories = m.install_category_controls()
        start, caption, resume = 0x2005000, 0x2005100, 0x2005200
        m.put(m.exports["MenuStartControl"], start)
        m.put(m.exports["MenuCaptionControl"], caption)
        m.put(m.exports["MenuResumeControl"], resume)

        m.run("MenuApplyLayout", (2,))

        self.assertEqual(m.visibility_calls, [
            (categories[0], 1),
            (categories[1], 1),
            (categories[2], 1),
            (start, 0),
            (caption, 0),
            (resume, 0),
            (categories[3], 1),
        ])

    def test_detail_layout_hides_categories_without_hiding_native_browser(self):
        m = Machine(4)
        categories = m.install_category_controls()
        start, caption, resume = 0x2005000, 0x2005100, 0x2005200
        m.put(m.exports["MenuStartControl"], start)
        m.put(m.exports["MenuCaptionControl"], caption)
        m.put(m.exports["MenuResumeControl"], resume)

        m.run("MenuApplyLayout", (4,))

        self.assertEqual(m.visibility_calls, [
            (categories[0], 0),
            (categories[1], 0),
            (categories[2], 0),
            (start, 1),
            (caption, 1),
            (resume, 1),
            (categories[3], 1),
        ])

    def test_native_back_always_posts_a_screen_local_event(self):
        for view in range(6):
            m = Machine(view)
            m.run(0x639aef, until=0x639af6)
            self.assertEqual(m.get(m.reg(UC_X86_REG_ESP)), 0x02000003)
            self.assertEqual(m.get(m.reg(UC_X86_REG_ESP) + 4), 0)

    def test_category_back_is_rewritten_for_the_parent_screen(self):
        event = 0x2008000
        m = Machine(2)
        m.put(event + 4, 0x02000003)
        m.run(
            0x638e21,
            registers={UC_X86_REG_ECX: event, UC_X86_REG_ESI: m.screen},
            until=0x6391ea,
        )
        self.assertEqual(m.get(event + 4), 0x01000004)
        self.assertEqual(m.get(m.exports["MenuView"]), 0)
        self.assertEqual(m.get(m.manager + 0xe8), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
