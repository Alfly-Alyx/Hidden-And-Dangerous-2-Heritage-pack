"""Offline x86 regressions; never loads the ASI or launches the game.

Definitions and runtime controls deliberately occupy different addresses.
The stock refresh and visibility handlers execute in Unicorn; allocation,
the message queue, scene methods and text drawing have explicit test doubles.
This validates state/ABI behavior, not pixels, startup timing or game input.
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

SHOW, HIDE = 0x01000003, 0x01000004
CATEGORY_IDS = (0x14D00000, 0x14E00000, 0x14F00000)
BROWSER_IDS = (0x14200000, 0x14300000, 0x14400000, 0x14600000,
               0x14700000, 0x14800000, 0x14900000, 0x14B00000)
BACK_ID, SECONDARY_BACK_ID = 0x14500000, 0x14C00000


class Machine:
    def __init__(self, view=0):
        self.pe = pefile.PE(str(ROOT / "build" / "HD2.CustomMenu.experimental.asi"))
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.raw = self.pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(0, 0x1000)  # isolated x86 SEH chain used by stock handlers
        self.uc.mem_map(self.base, (len(self.raw) + 4095) & ~4095)
        self.uc.mem_write(self.base, self.raw)
        self.uc.mem_map(0x400000, 0x800000)
        self.stock = (ROOT / "tmp" / "stock-menu-analysis.bin").read_bytes()
        self.uc.mem_write(0x401000, self.stock)
        self.uc.mem_map(0x2000000, 0x10000)
        self.uc.mem_map(0x2100000, 0x10000)
        self.uc.mem_map(0x3000000, 0x10000)
        self.uc.mem_map(0x3100000, 0x10000)
        self.uc.mem_map(0x3200000, 0x100000)
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
        self.top_control = 0x2005000
        self.top_cell = 0x2005100
        self.put(self.top_control + 0x60, 0x14000000)
        self.put(self.top_cell, self.top_control)
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
            self.uc.mem_write(address, b"\xe9" + struct.pack("<I", (replacement - address - 5) & 0xffffffff)
                              + b"\x90" * (length - 5))
        self.calls = []
        self.next_definition = 0x2006000
        self.next_definition_id = 0x14D00000
        self.definitions = {}
        self.messages = []
        self.pending_messages = []
        self.runtime_controls = {}
        self.scene_calls = []
        self.draw_calls = []
        self.run_stock_refresh = False
        self.heap = 0x3200000
        self.uc.hook_add(UC_HOOK_CODE, self.on_code)

    def preload(self):
        frame = self.stack + 0x400
        self.put(frame + 8, 0x2007000)  # definition owner, not the runtime screen
        self.put(frame + 12, 0)
        self.run(0x639afe, registers={UC_X86_REG_EBP: frame}, until=0x639b06)
        return [self.get(self.exports["MenuCategoryControls"] + i * 4) for i in range(3)]

    def category_callbacks(self):
        return [call[1][5] for call in self.calls if call[0] == 0x61e100][::2]

    def reload(self):
        self.run(0x63ab60, registers={UC_X86_REG_ECX: self.screen})

    def install_runtime_controls(self):
        for index, target in enumerate(BROWSER_IDS + (BACK_ID, SECONDARY_BACK_ID) + CATEGORY_IDS):
            control = self.control + index * 0x100
            scene = 0x200A000 + index * 0x100
            text = 0x200C000 + index * 0x40
            self.runtime_controls[target] = control
            self.put(control, 0x814CB0)  # native text button vtable
            self.put(control + 0x50, scene)
            self.put(control + 0x60, target)
            self.uc.mem_write(control + 0x64, bytes((0, 1, 1)))
            self.put(control + 0x6c, text)
            self.put(scene, 0x3001000)
            self.put(text, 0x3001100)
            self.put(0x3001000 + 0x30, 0x3002000)
            self.put(0x3001000 + 0x24, 0x3002010)
            self.put(0x3001100 + 4, 0x3002020)

    def flush_visibility(self):
        pending, self.pending_messages = self.pending_messages, []
        for message in pending:
            target, event, *_ = message
            if target not in self.runtime_controls or event not in (SHOW, HIDE, 0x1000001, 0x1000002):
                continue
            packet = 0x200E000
            self.uc.mem_write(packet, struct.pack("<6I", *message))
            self.run(0x6554f0, (packet,), {UC_X86_REG_ECX: self.runtime_controls[target]})

    def visibility(self, target):
        return self.uc.mem_read(self.runtime_controls[target] + 0x65, 1)[0]

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
            if not self.run_stock_refresh:
                self.return_call(1)
        elif address == 0x615360:
            name = self.string(self.get(esp + 8))
            self.calls.append(("control", name))
            definition = self.next_definition
            self.next_definition += 0x40
            self.put(definition, 0x813ab0)
            self.put(definition + 8, self.next_definition_id)
            self.next_definition_id += 0x100000
            self.definitions[definition] = name
            self.return_call(definition, 2)
        elif address in (0x614e80, 0x614f10, 0x61e100):
            args = tuple(self.get(esp + offset) for offset in range(4, 28, 4))
            self.calls.append((address, args))
            self.return_call()
        elif address == 0x615a90:
            if self.reg(UC_X86_REG_ECX) != 0x8ae590:
                raise AssertionError("Wrong native message queue this pointer")
            message = struct.unpack("<6I", self.uc.mem_read(self.get(esp + 4), 24))
            self.messages.append(message)
            self.pending_messages.append(message)
            self.return_call(1, 1)
        elif address == 0x628230:
            self.return_call(self.top_cell)
        elif address == 0x7e566f:
            allocated = self.heap
            self.heap += (self.get(esp + 4) + 15) & ~15
            self.return_call(allocated)
        elif address == 0x4050a0:
            target = self.reg(UC_X86_REG_ECX)
            self.put(target, 1)
            self.put(target + 4, self.get(esp + 8))
            self.uc.mem_write(target + 8, self.string(self.get(esp + 4)) + b"\0")
            self.return_call(target, 2)
        elif address == 0x4050e0:
            self.return_call()
        elif address == 0x6b16c0:
            self.return_call(7, 1)
        elif address == 0x65d270:
            self.return_call(1, 2)  # visibility notifications; no game/UI side effects
        elif address == 0x3002000:
            self.scene_calls.append((self.get(esp + 4), self.get(esp + 8)))
            self.return_call(1, 2)
        elif address == 0x3002010:
            self.return_call(1, 1)
        elif address == 0x3002020:
            self.draw_calls.append(self.reg(UC_X86_REG_ECX))
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

    def test_unrelated_stock_actions_keep_native_dispatch(self):
        m = Machine(2)
        m.run(0x63c090, registers={UC_X86_REG_EAX: 0x0CE00000}, until=0x63c095)
        self.assertEqual(m.get(m.exports["MenuView"]), 2)
        self.assertEqual(m.calls, [])

    def test_unrelated_mission_events_keep_native_dispatch(self):
        for event_id in (0x01000004, 0x02000003, 0x02000008):
            m = Machine(4)
            event = 0x200E000
            m.put(event + 4, event_id)
            result = m.run(0x638e21,
                           registers={UC_X86_REG_ECX: event, UC_X86_REG_ESI: m.screen},
                           until=0x638e29)
            self.assertEqual(result, event_id)
            self.assertEqual(m.get(m.exports["MenuView"]), 4)
            self.assertEqual(m.calls, [])

    def test_main_custom_button_enters_category_menu(self):
        m = Machine()
        m.run(0x63c090, registers={UC_X86_REG_EAX: 0x0CD00000}, until=0x63be31)
        self.assertEqual(m.get(m.exports["MenuView"]), 2)
        self.assertEqual(m.get(m.manager + 0xe8), 2)

    def test_localized_title_ids(self):
        for view, text_id in ((0, 2251), (2, 20402), (3, 20410), (4, 20411), (5, 20412)):
            m = Machine(view)
            m.run(0x63abec, registers={UC_X86_REG_ECX: 2251}, until=0x63abf8)
            self.assertEqual(m.reg(UC_X86_REG_ECX), text_id)

    def test_layout_refresh_preserves_native_registers_and_stack(self):
        m = Machine(2)
        m.preload()
        m.put(m.stack + 0x34, 0x12345678)
        m.run(0x63af06, until=0x63af0b)
        self.assertEqual(m.reg(UC_X86_REG_ECX), 0x12345678)
        self.assertEqual(m.reg(UC_X86_REG_EDI), m.stop)
        self.assertEqual(m.reg(UC_X86_REG_ESP), m.stack + 4)
        self.assertEqual(len(m.messages), 13)

    def test_original_buttons_reset_custom_state(self):
        for entry, end in ((0x63be2c, 0x63be31), (0x63be73, 0x63be78)):
            m = Machine(5)
            m.run(entry, until=end)
            self.assertEqual(m.get(m.exports["MenuView"]), 0)
            self.assertEqual(m.get(m.manager + 0xe8), 0)

    def test_main_builder_registers_button_and_balances_stack(self):
        m = Machine()
        m.run(0x625c81, registers={UC_X86_REG_ESI: m.screen}, until=0x625c88)
        self.assertEqual(m.calls[0], ("control", b"bcampaign02"))
        self.assertEqual(m.calls[1][1][4], 20402)
        self.assertEqual(m.calls[2][1][3], 0x4003000)
        self.assertEqual(m.calls[3][1][3], 0x4001000)
        self.assertEqual(m.reg(UC_X86_REG_ESP), m.stack - 4)
        self.assertEqual(m.get(m.stack - 4), 0x83ebc0)

    def test_preload_zero_builds_hidden_labeled_category_definitions(self):
        m = Machine(0)
        definitions = m.preload()
        self.assertEqual([m.definitions[d] for d in definitions],
                         [b"bcustom user", b"bcustom multi", b"bcustom explore"])
        self.assertEqual([m.get(d + 8) for d in definitions], list(CATEGORY_IDS))
        labels = [call[1][4] for call in m.calls if call[0] == 0x614f10]
        self.assertEqual(labels, [20411, 20410, 20412])
        hides = [call[1][:4] for call in m.calls if call[0] == 0x614e80]
        self.assertEqual(hides, [(d, 0, HIDE, 0) for d in definitions])
        self.assertEqual(m.messages, [])  # definitions are not live yet
        self.assertEqual(m.reg(UC_X86_REG_ESP), m.stack + 0x24)

    def test_category_definitions_exist_independently_of_current_view(self):
        for view in (2, 3, 4, 5):
            with self.subTest(view=view):
                m = Machine(view)
                self.assertEqual(len(m.preload()), 3)
                self.assertEqual(len(m.definitions), 3)

    def test_each_callback_queues_private_event_without_corrupting_runtime_id(self):
        for index in range(3):
            m = Machine(2)
            definitions = m.preload()
            m.install_runtime_controls()
            runtime = m.runtime_controls[CATEGORY_IDS[index]]
            self.assertNotEqual(definitions[index], runtime)
            m.messages.clear()
            callback = m.category_callbacks()[index]
            m.run(callback, (0, runtime, 0x04001000, 0))
            self.assertEqual(m.messages, [(0, 0x02000FF1 + index, 0, 0, 0, 0)])
            self.assertEqual(m.get(runtime + 0x60), CATEGORY_IDS[index])
            self.assertEqual(m.get(definitions[index] + 8), CATEGORY_IDS[index])
            self.assertEqual(m.reg(UC_X86_REG_ESP), m.stack + 20)
            self.assertEqual(m.reg(UC_X86_REG_EAX) & 0xff, 1)
            m.messages.clear()
            m.run(callback, (0, runtime, 0x04003000, 0))
            self.assertEqual(m.messages, [])  # focus does not navigate

    def test_category_click_ignored_outside_selector(self):
        for view in (0, 3, 4, 5):
            m = Machine(view)
            m.run("MenuCategoryClick", (0,))
            self.assertEqual(m.messages, [])

    def test_private_events_cannot_navigate_nested_or_inactive_screens(self):
        for view, top_id in ((0, 0x14000000), (4, 0x14000000), (2, 0x20000000)):
            m = Machine(view)
            m.put(m.top_control + 0x60, top_id)
            m.put(0x8ae5f0, 1)
            m.run("MenuHandleCategoryEvent", (0x02000FF1, m.screen))
            self.assertEqual(m.get(m.exports["MenuView"]), view)
            self.assertEqual(m.calls, [])

    def test_global_back_consumes_detail_only_and_respects_nested_screens(self):
        for view in (3, 4, 5):
            m = Machine(view)
            m.put(0x8ae5f0, 1)
            m.run(0x66cd70, registers={UC_X86_REG_EAX: 0x02000003, UC_X86_REG_EBX: m.screen},
                  until=0x66d96f)
            self.assertEqual(m.get(m.exports["MenuView"]), 2)
            self.assertEqual(m.calls, [("reload", m.screen, 2)])
        for view, top_id, expected_view in ((2, 0x14000000, 0), (4, 0x20000000, 4),
                                           (0, 0x14000000, 0)):
            m = Machine(view)
            m.put(0x8ae5f0, 1)
            m.put(m.top_control + 0x60, top_id)
            m.run(0x66cd70, registers={UC_X86_REG_EAX: 0x02000003, UC_X86_REG_EBX: m.screen},
                  until=0x66cd75)
            self.assertEqual(m.get(m.exports["MenuView"]), expected_view)
            self.assertEqual(m.calls, [])
            self.assertEqual(m.reg(UC_X86_REG_EAX), 0x02000003)
            self.assertTrue(m.reg(UC_X86_REG_EFLAGS) & 0x40)  # replayed native CMP

    def test_global_back_hook_preserves_non_back_native_comparison(self):
        m = Machine(4)
        m.run(0x66cd70, registers={UC_X86_REG_EAX: 0x02000004, UC_X86_REG_EBX: m.screen},
              until=0x66cd75)
        self.assertEqual(m.get(m.exports["MenuView"]), 4)
        self.assertEqual(m.calls, [])
        self.assertFalse(m.reg(UC_X86_REG_EFLAGS) & 0x40)

    def assert_layout(self, m, categories):
        visible = {target for target in m.runtime_controls if m.visibility(target)}
        expected = set(CATEGORY_IDS if categories else BROWSER_IDS) | {BACK_ID}
        self.assertEqual(visible, expected)
        self.assertEqual(m.visibility(SECONDARY_BACK_ID), 0)
        for target, runtime in m.runtime_controls.items():
            self.assertEqual(m.get(runtime + 0x60), target)

    def test_real_preload_refresh_category_list_back_cycle(self):
        for index, view in enumerate((4, 3, 5)):
            with self.subTest(category=index):
                m = Machine(0)
                definitions = m.preload()  # happens once, while MenuView is zero
                m.install_runtime_controls()
                self.assertTrue(set(definitions).isdisjoint(m.runtime_controls.values()))
                m.put(0x8ae5f0, 1)
                m.put(m.screen + 0x20c, 7)
                m.run_stock_refresh = True
                m.reload()
                m.flush_visibility()
                self.assert_layout(m, False)
                m.run(0x63c090, registers={UC_X86_REG_EAX: 0x0CD00000}, until=0x63be31)
                m.reload()
                m.flush_visibility()
                self.assert_layout(m, True)
                callback = m.category_callbacks()[index]
                m.run(callback, (0, m.runtime_controls[CATEGORY_IDS[index]], 0x04001000, 0))
                packet = 0x200E000
                m.uc.mem_write(packet, struct.pack("<6I", *m.messages[-1]))
                m.run(0x638e21, registers={UC_X86_REG_ECX: packet, UC_X86_REG_ESI: m.screen},
                      until=0x6391d4)
                self.assertEqual(m.get(m.exports["MenuView"]), view)
                self.assertEqual(m.get(m.manager + 0xe8), view)
                m.flush_visibility()
                self.assert_layout(m, False)
                m.run(0x66cd70, registers={UC_X86_REG_EAX: 0x02000003, UC_X86_REG_EBX: m.screen},
                      until=0x66d96f)
                m.flush_visibility()
                self.assert_layout(m, True)
                m.run(0x66cd70, registers={UC_X86_REG_EAX: 0x02000003, UC_X86_REG_EBX: m.screen},
                      until=0x66cd75)
                self.assertEqual(m.get(m.exports["MenuView"]), 0)
                self.assertEqual(m.get(m.manager + 0xe8), 0)
                # Reentering the official browser restores its saved unlock bound.
                m.reload()
                m.flush_visibility()
                self.assert_layout(m, False)
                self.assertEqual(m.get(m.screen + 0x20c), 7)
                self.assertEqual(len(m.definitions), 3)

    def test_native_hide_suppresses_text_draw_and_show_restores_it(self):
        m = Machine()
        m.install_runtime_controls()
        runtime = m.runtime_controls[0x14900000]
        for event, expected_visible in ((HIDE, 0), (SHOW, 1)):
            m.pending_messages = [(0x14900000, event, 0, 0, 0, 0)]
            m.flush_visibility()
            self.assertEqual(m.visibility(0x14900000), expected_visible)
            self.assertEqual(m.scene_calls[-1][1], expected_visible)
            m.draw_calls.clear()
            m.run(0x661fa0, registers={UC_X86_REG_ECX: runtime})
            self.assertEqual(len(m.draw_calls), expected_visible)
        self.assertEqual(m.get(runtime + 0x60), 0x14900000)

    def test_stock_labels_and_secondary_back_initial_hide_are_not_patched(self):
        m = Machine()
        for address in (0x6396fe, 0x639a17, 0x639a94, 0x639aef):
            self.assertNotIn(address, m.hooks)
        self.assertEqual(m.stock[0x639aef - 0x401000:0x639af6 - 0x401000],
                         bytes.fromhex("6a006804000001"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
