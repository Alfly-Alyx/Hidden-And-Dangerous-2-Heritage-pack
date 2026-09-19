#!/usr/bin/env python3
"""Archived experiment that rewrites the H&D2 executable.

This route is intentionally absent from the supported custom-mission workflow
because antivirus products correctly treat its added executable section and
control-flow hooks as code-injection indicators. The supported manager never
calls this script and leaves HD2_SabreSquadron.exe unchanged.

The packed client is decompressed and its import table is reconstructed offline.
Only a separate test installation may be targeted. The original installation is
never modified and the resulting commercial derivative must not be distributed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import sys
from collections import OrderedDict
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
DEPENDENCIES = PROJECT / ".research" / "binary-patch-deps"
sys.path.insert(0, str(DEPENDENCIES))

from unicorn import (
    Uc,
    UcError,
    UC_ARCH_X86,
    UC_HOOK_CODE,
    UC_HOOK_MEM_INVALID,
    UC_MODE_32,
    UC_PROT_ALL,
)
from unicorn.x86_const import (
    UC_X86_REG_EAX,
    UC_X86_REG_EBX,
    UC_X86_REG_EBP,
    UC_X86_REG_ECX,
    UC_X86_REG_EDX,
    UC_X86_REG_EDI,
    UC_X86_REG_EIP,
    UC_X86_REG_ESI,
    UC_X86_REG_ESP,
)

sys.path.insert(0, str(PROJECT / "tools"))
from dta_archive import DtaArchive
from menu_gui_audit import parse_4ds_nodes
from objective_audit import blocks, direct, walk
from custom_mission_packages import (
    CATEGORIES,
    CATEGORY_ORDER,
    load_library,
    localized_values,
    package_summary,
)


EXPECTED_SOURCE_SHA256 = "1EEBDE4710F800F712A05B1ECEE2BA862C144F478DF89B58E54C912E857EE78C"
IMAGE_BASE = 0x400000
OUTPUT_RVA = 0x1000
RESOURCE_RVA = 0x7BB000
RESOURCE_SIZE = 0x1800
TLS_RVA = 0x7BAB04
OEP_RVA = 0x596A05
BUILDER_SOURCE = 0x00625B25
BUILDER_HOOK = 0x00625C81
BUILDER_RETURN = 0x00625C88
HANDLER_HOOK = 0x0063C090
MENU_CONTROL_HANDLER = 0x0063B9A0
HANDLER_ORIGINAL_CC = 0x0063C09B
HANDLER_REJECT = 0x0063C274
HANDLER_SINGLE_MISSION_TAIL = 0x0063BE31
LIST_BUILD_HOOK = 0x0063AE00
LIST_BUILD_RETURN = 0x0063AE08
LIST_SELECT_HOOK = 0x006390C9
LIST_SELECT_RETURN = 0x006390CF
EVENT_DISPATCH_HOOK = 0x00638E21
EVENT_DISPATCH_RETURN = 0x00638E29
EVENT_HANDLED_RETURN = 0x006391D4
LIST_NEXT_HOOK = 0x0063AEFA
LIST_NEXT_RETURN = 0x0063AEFF
LIST_EXIT = 0x0063AF06
NATIVE_SINGLE_HOOK = 0x0063BE2C
NATIVE_SINGLE_RETURN = 0x0063BE31
NATIVE_CARNAGE_HOOK = 0x0063BE73
NATIVE_CARNAGE_RETURN = 0x0063BE78
CATALOGUE_RESET_HOOK = 0x006B6912
CATALOGUE_RESET_RETURN = 0x006B691C
CUSTOM_TEXT_IDS = {
    20499: " ",
    20402: "CUSTOM MISSIONS",
    20410: "MULTIPLAYER MISSIONS - SOLO",
    20411: "USER MISSIONS",
    20412: "FREE EXPLORATION",
    20413: "BACK",
    20420: "MULTIPLAYER ADAPTATION TEST - BREST",
    20421: "USER MISSION TEST - LIBYA 1",
    20422: "FREE EXPLORATION / WEAPON TEST - SICILY 1",
}
CUSTOM_TEXT_BY_LANGUAGE = {
    "czech": {
        20499: " ",
        20402: "VLASTNÍ MISE",
        20410: "ÚPRAVY PRO VÍCE HRÁČŮ",
        20411: "UŽIVATELSKÉ MISE",
        20412: "VOLNÝ PRŮZKUM / TESTY ZBRANÍ",
        20413: "ZPĚT",
        20420: "TEST ÚPRAVY PRO VÍCE HRÁČŮ - BREST",
        20421: "TEST UŽIVATELSKÉ MISE - LIBYE 1",
        20422: "PRŮZKUM / TEST ZBRANÍ - SICÍLIE 1",
    },
    "french": {
        20499: " ",
        20402: "MISSIONS PERSONNALISÉES",
        20410: "MISSIONS MULTI EN SOLO",
        20411: "MISSIONS UTILISATEUR",
        20412: "EXPLORATION LIBRE",
        20413: "RETOUR",
        20420: "TEST ADAPTATION MULTIJOUEUR - BREST",
        20421: "TEST MISSION UTILISATEUR - LIBYE 1",
        20422: "EXPLORATION / TEST D'ARMES - SICILE 1",
    },
    "german": {
        20499: " ",
        20402: "EIGENE MISSIONEN",
        20410: "MEHRSPIELER-ANPASSUNGEN",
        20411: "BENUTZERMISSIONEN",
        20412: "FREIE ERKUNDUNG / WAFFENTESTS",
        20413: "ZURÜCK",
        20420: "MEHRSPIELER-TEST - BREST",
        20421: "BENUTZERMISSION-TEST - LIBYEN 1",
        20422: "ERKUNDUNG / WAFFENTEST - SIZILIEN 1",
    },
    "italian": {
        20499: " ",
        20402: "MISSIONI PERSONALIZZATE",
        20410: "ADATTAMENTI MULTIGIOCATORE",
        20411: "MISSIONI UTENTE",
        20412: "ESPLORAZIONE LIBERA / TEST ARMI",
        20413: "INDIETRO",
        20420: "TEST ADATTAMENTO MULTIGIOCATORE - BREST",
        20421: "TEST MISSIONE UTENTE - LIBIA 1",
        20422: "ESPLORAZIONE / TEST ARMI - SICILIA 1",
    },
    "japan": {
        20499: " ",
        20402: "カスタムミッション",
        20410: "マルチプレイ改作",
        20411: "ユーザーミッション",
        20412: "フリー探索 / 武器テスト",
        20413: "戻る",
        20420: "マルチプレイ改作テスト - BREST",
        20421: "ユーザーミッションテスト - LIBYA 1",
        20422: "探索 / 武器テスト - SICILY 1",
    },
    "spanish": {
        20499: " ",
        20402: "MISIONES PERSONALIZADAS",
        20410: "ADAPTACIONES MULTIJUGADOR",
        20411: "MISIONES DE USUARIO",
        20412: "EXPLORACIÓN LIBRE / PRUEBAS DE ARMAS",
        20413: "ATRÁS",
        20420: "PRUEBA MULTIJUGADOR - BREST",
        20421: "PRUEBA DE MISIÓN - LIBIA 1",
        20422: "EXPLORACIÓN / PRUEBA DE ARMAS - SICILIA 1",
    },
}
CUSTOM_TEXT_ENCODINGS = {
    "czech": "cp1250",
    "japan": "utf-8",
}


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def c_string(machine: Uc, address: int) -> str:
    data = bytearray()
    for offset in range(1024):
        value = bytes(machine.mem_read(address + offset, 1))[0]
        if not value:
            return data.decode("ascii", errors="replace")
        data.append(value)
    raise ValueError("Chaîne d'importation sans terminaison")


def packed_layout(data: bytes) -> tuple[int, int, int, list[dict[str, int]]]:
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("Signature PE absente")
    section_count = struct.unpack_from("<H", data, pe + 6)[0]
    optional_size = struct.unpack_from("<H", data, pe + 20)[0]
    optional = pe + 24
    image_base = struct.unpack_from("<I", data, optional + 28)[0]
    entry_rva = struct.unpack_from("<I", data, optional + 16)[0]
    image_size = struct.unpack_from("<I", data, optional + 56)[0]
    sections = []
    table = optional + optional_size
    for index in range(section_count):
        offset = table + index * 40
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", data, offset + 8
        )
        sections.append({
            "virtual_size": virtual_size,
            "virtual_address": virtual_address,
            "raw_size": raw_size,
            "raw_offset": raw_offset,
        })
    return image_base, entry_rva, image_size, sections


def emulate_unpack(data: bytes) -> tuple[bytearray, list[dict[str, object]]]:
    image_base, entry_rva, image_size, sections = packed_layout(data)
    if image_base != IMAGE_BASE:
        raise ValueError("Base PE inattendue")
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    machine.mem_map(image_base, align(image_size, 0x1000), UC_PROT_ALL)
    first_raw = min(item["raw_offset"] for item in sections if item["raw_size"])
    machine.mem_write(image_base, data[:first_raw])
    for item in sections:
        if item["raw_size"]:
            machine.mem_write(
                image_base + item["virtual_address"],
                data[item["raw_offset"]:item["raw_offset"] + item["raw_size"]],
            )
    stack_base, stack_size = 0x10000000, 0x100000
    machine.mem_map(stack_base, stack_size, UC_PROT_ALL)
    machine.reg_write(UC_X86_REG_ESP, stack_base + stack_size - 0x100)

    fake_base = 0xF0000000
    machine.mem_map(fake_base, 0x1000, UC_PROT_ALL)
    load_library, get_proc, virtual_protect, exit_process = (
        fake_base,
        fake_base + 0x10,
        fake_base + 0x20,
        fake_base + 0x30,
    )
    # Slots used by the original UPX loader in the packed import directory.
    machine.mem_write(0x00BBC444, struct.pack("<I", load_library))
    machine.mem_write(0x00BBC448, struct.pack("<I", get_proc))
    machine.mem_write(0x00BBC44C, struct.pack("<I", virtual_protect))
    machine.mem_write(0x00BBC458, struct.pack("<I", exit_process))

    modules: dict[int, str] = {}
    imports: list[dict[str, object]] = []
    output_end = {"value": 0}
    memory_fault: dict[str, int] = {}

    def stack_u32(offset: int) -> int:
        esp = machine.reg_read(UC_X86_REG_ESP)
        return struct.unpack("<I", bytes(machine.mem_read(esp + offset, 4)))[0]

    def return_stdcall(arguments: int, eax: int) -> None:
        esp = machine.reg_read(UC_X86_REG_ESP)
        target = stack_u32(0)
        machine.reg_write(UC_X86_REG_EAX, eax)
        machine.reg_write(UC_X86_REG_ESP, esp + 4 + arguments * 4)
        machine.reg_write(UC_X86_REG_EIP, target)

    def on_load_library(_machine, _address, _size, _user) -> None:
        name = c_string(machine, stack_u32(4))
        handle = 0x10000 + len(modules) * 0x1000
        modules[handle] = name
        return_stdcall(1, handle)

    def on_get_proc(_machine, _address, _size, _user) -> None:
        handle, value = stack_u32(4), stack_u32(8)
        if handle not in modules:
            raise ValueError("Module d'importation inconnu")
        symbol: object = value if value <= 0xFFFF else c_string(machine, value)
        imports.append({
            "dll": modules[handle],
            "symbol": symbol,
            "iat_va": machine.reg_read(UC_X86_REG_EBX),
        })
        return_stdcall(2, 0x70000000 + len(imports) * 0x10)

    def on_virtual_protect(_machine, _address, _size, _user) -> None:
        return_stdcall(4, 1)

    def on_exit(_machine, _address, _size, _user) -> None:
        raise RuntimeError("Le chargeur compacté a demandé l'arrêt")

    def on_decompression_end(_machine, _address, _size, _user) -> None:
        output_end["value"] = machine.reg_read(UC_X86_REG_EDI)

    def on_invalid_memory(_machine, access, address, size, value, _user) -> bool:
        memory_fault.update({
            "access": access,
            "address": address,
            "size": size,
            "value": value,
            "eip": machine.reg_read(UC_X86_REG_EIP),
            "eax": machine.reg_read(UC_X86_REG_EAX),
            "ebx": machine.reg_read(UC_X86_REG_EBX),
            "ecx": machine.reg_read(UC_X86_REG_ECX),
            "edx": machine.reg_read(UC_X86_REG_EDX),
            "esi": machine.reg_read(UC_X86_REG_ESI),
            "edi": machine.reg_read(UC_X86_REG_EDI),
            "ebp": machine.reg_read(UC_X86_REG_EBP),
            "esp": machine.reg_read(UC_X86_REG_ESP),
        })
        return False

    machine.hook_add(UC_HOOK_CODE, on_load_library, begin=load_library, end=load_library)
    machine.hook_add(UC_HOOK_CODE, on_get_proc, begin=get_proc, end=get_proc)
    machine.hook_add(UC_HOOK_CODE, on_virtual_protect, begin=virtual_protect, end=virtual_protect)
    machine.hook_add(UC_HOOK_CODE, on_exit, begin=exit_process, end=exit_process)
    machine.hook_add(UC_HOOK_CODE, on_decompression_end, begin=0x00BBAA3A, end=0x00BBAA3A)
    machine.hook_add(UC_HOOK_MEM_INVALID, on_invalid_memory)
    try:
        machine.emu_start(
            image_base + entry_rva,
            image_base + OEP_RVA,
            timeout=60_000_000,
            count=400_000_000,
        )
    except UcError as error:
        if memory_fault:
            fault_eip = memory_fault["eip"]
            context = bytes(machine.mem_read(fault_eip - 32, 96)).hex()
            stack = bytes(machine.mem_read(memory_fault["esp"], 64)).hex()
            raise ValueError(
                "Accès mémoire imprévu pendant le décompactage hors ligne : "
                f"EIP=0x{fault_eip:08X}, adresse=0x{memory_fault['address']:08X}, "
                f"type={memory_fault['access']}, taille={memory_fault['size']}, "
                f"registres=" + ",".join(
                    f"{name.upper()}=0x{memory_fault[name]:08X}"
                    for name in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")
                ) + f", pile={stack}, contexte={context}"
            ) from error
        raise
    if output_end["value"] <= image_base + OUTPUT_RVA:
        raise ValueError("Décompression incomplète")
    image = bytearray(machine.mem_read(image_base + OUTPUT_RVA, RESOURCE_RVA - OUTPUT_RVA))
    return image, imports


def build_import_section(
    image: bytearray, imports: list[dict[str, object]], section_rva: int
) -> tuple[bytes, int, int, int, int]:
    grouped: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
    for item in imports:
        grouped.setdefault(str(item["dll"]), []).append(item)
    for dll, items in grouped.items():
        slots = [int(item["iat_va"]) for item in items]
        if slots != list(range(slots[0], slots[0] + len(slots) * 4, 4)):
            raise ValueError(f"IAT non contiguë pour {dll}")

    descriptors_size = (len(grouped) + 1) * 20
    section = bytearray(b"\0" * descriptors_size)

    def reserve(payload: bytes, alignment: int = 1) -> int:
        while len(section) % alignment:
            section.append(0)
        offset = len(section)
        section.extend(payload)
        return section_rva + offset

    descriptors = []
    iat_min, iat_max = 0xFFFFFFFF, 0
    for dll, items in grouped.items():
        dll_rva = reserve(dll.encode("ascii") + b"\0")
        thunk_values = []
        iat_rvas = []
        for item in items:
            symbol = item["symbol"]
            if isinstance(symbol, int):
                thunk_values.append(0x80000000 | symbol)
            else:
                thunk_values.append(reserve(b"\0\0" + str(symbol).encode("ascii") + b"\0", 2))
            iat_rva = int(item["iat_va"]) - IMAGE_BASE
            iat_rvas.append(iat_rva)
            iat_min = min(iat_min, iat_rva)
            iat_max = max(iat_max, iat_rva + 4)
        # A normal PE keeps the IAT identical to the lookup table on disk.
        # Leaving these entries at zero makes this 2003 startup stub call a
        # null pointer before Windows has a usable target.
        for iat_rva, thunk_value in zip(iat_rvas, thunk_values):
            struct.pack_into("<I", image, iat_rva - OUTPUT_RVA, thunk_value)
        struct.pack_into(
            "<I", image, iat_rvas[-1] + 4 - OUTPUT_RVA, 0
        )
        int_rva = reserve(
            b"".join(struct.pack("<I", value) for value in thunk_values) + b"\0\0\0\0",
            4,
        )
        first_thunk = int(items[0]["iat_va"]) - IMAGE_BASE
        descriptors.append((int_rva, 0, 0, dll_rva, first_thunk))
    for index, descriptor in enumerate(descriptors):
        struct.pack_into("<IIIII", section, index * 20, *descriptor)
    return bytes(section), section_rva, descriptors_size, iat_min, iat_max - iat_min


def rel32(from_next: int, target: int) -> bytes:
    return struct.pack("<i", target - from_next)


def install_menu_code(image: bytearray, patch_rva: int) -> bytes:
    def read_va(address: int, count: int) -> bytes:
        offset = address - IMAGE_BASE - OUTPUT_RVA
        return bytes(image[offset:offset + count])

    def write_va(address: int, value: bytes) -> None:
        offset = address - IMAGE_BASE - OUTPUT_RVA
        image[offset:offset + len(value)] = value

    expected = {
        BUILDER_SOURCE: bytes.fromhex("8BCE68C8F583006A14E8"),
        BUILDER_HOOK: bytes.fromhex("8BCE68C0EB8300"),
        HANDLER_HOOK: bytes.fromhex("3D0000C00C"),
        LIST_BUILD_HOOK: bytes.fromhex("8B3510EA8A0033FF"),
        LIST_SELECT_HOOK: bytes.fromhex("8991E8000000"),
        EVENT_DISPATCH_HOOK: bytes.fromhex("8B410425FF0F0003"),
        LIST_NEXT_HOOK: bytes.fromhex("4089442410"),
        NATIVE_SINGLE_HOOK: bytes.fromhex("A134EA8A00"),
        NATIVE_CARNAGE_HOOK: bytes.fromhex("A134EA8A00"),
        CATALOGUE_RESET_HOOK: bytes.fromhex("C780E800000001000000"),
    }
    for address, signature in expected.items():
        if read_va(address, len(signature)) != signature:
            raise ValueError(f"Signature client incompatible à 0x{address:08X}")

    patch_va = IMAGE_BASE + patch_rva
    builder_va = patch_va
    handler_va = patch_va + 0x200
    custom_callback_va = patch_va + 0x4A0
    control_name_va = patch_va + 0x420
    registration = bytearray(read_va(BUILDER_SOURCE, 0x57))
    struct.pack_into("<I", registration, 3, control_name_va)
    if registration[14] != 0x68 or struct.unpack_from("<I", registration, 15)[0] != 0x89A:
        raise ValueError("Identifiant de texte Campagne inattendu")
    struct.pack_into("<I", registration, 15, 20402)
    for offset in (37, 61):
        if registration[offset - 1] != 0x68 or struct.unpack_from(
            "<I", registration, offset
        )[0] != MENU_CONTROL_HANDLER:
            raise ValueError("Rappel du contrôle modèle inattendu")
        struct.pack_into("<I", registration, offset, custom_callback_va)
    for offset in (0x09, 0x1F, 0x37, 0x4F):
        if registration[offset] != 0xE8:
            raise ValueError("CALL de construction absent")
        old = struct.unpack_from("<i", registration, offset + 1)[0]
        target = BUILDER_SOURCE + offset + 5 + old
        struct.pack_into("<i", registration, offset + 1, target - (builder_va + offset + 5))
    builder = bytearray(registration)

    overwritten = read_va(BUILDER_HOOK, 7)
    builder.extend(overwritten)
    builder.extend(b"\xE9" + rel32(builder_va + len(builder) + 5, BUILDER_RETURN))

    handler = bytearray(bytes.fromhex(
        "3D0000D00C" "0F8400000000" "3D0000C00C" "0F8500000000" "E900000000"
        "A110EA8A00" "C780E800000002000000" "A134EA8A00" "E900000000"
    ))
    custom_offset = 27
    struct.pack_into("<i", handler, 7, handler_va + custom_offset - (handler_va + 11))
    struct.pack_into("<i", handler, 18, HANDLER_REJECT - (handler_va + 22))
    struct.pack_into("<i", handler, 23, HANDLER_ORIGINAL_CC - (handler_va + 27))
    # Keep catalogue selector 2, then enter the native Single Mission browser.
    # Its catalogue hierarchy supplies the three custom category groups.
    struct.pack_into(
        "<i", handler, 48,
        HANDLER_SINGLE_MISSION_TAIL - (handler_va + 52),
    )

    list_filter_va = patch_va + 0x300
    list_filter = bytearray(bytes.fromhex(
        "8B3510EA8A00"          # mov esi,[catalogue manager]
        "33FF"                  # xor edi,edi
        "8B86E8000000"          # mov eax,[esi+E8]
        "83F802"                # cmp eax,2
        "7C0C"                  # jl normal return
        "8BF8"                  # mov edi,eax
        "C7850C02000064000000"  # native sentinel: show every custom entry
        "E900000000"
    ))
    struct.pack_into(
        "<i", list_filter, 32,
        LIST_BUILD_RETURN - (list_filter_va + 36),
    )

    list_select_va = patch_va + 0x340
    list_select = bytearray(bytes.fromhex(
        "83B9E800000002"      # cmp dword [ecx+E8],2
        "7C2E"                # official catalogue
        "7532"                # detail catalogue: keep selector
        "8B9608020000"        # category row selected by the player
        "2BD0"                # convert the encoded row to 0..2
        "83FA02"
        "7709"                # invalid row: refresh safely
        "83C203"              # category 0..2 -> Gamedata03..05
        "8991E8000000"
        "C78608020000FFFFFFFF"
        "8BCE"
        "E800000000"          # rebuild this screen with the chosen catalogue
        "E900000000"          # handled without launching the placeholder
        "8991E8000000"        # native official selector
        "E900000000"
    ))
    struct.pack_into(
        "<i", list_select, 46,
        0x0063AB60 - (list_select_va + 50),
    )
    struct.pack_into(
        "<i", list_select, 51,
        EVENT_HANDLED_RETURN - (list_select_va + 55),
    )
    struct.pack_into(
        "<i", list_select, 62,
        LIST_SELECT_RETURN - (list_select_va + 66),
    )

    catalogue_reset_va = patch_va + 0x3D0
    catalogue_reset = bytearray(bytes.fromhex(
        "83B8E800000002"      # cmp dword [eax+E8],2
        "7D0A"                # preserve every custom catalogue
        "C780E800000001000000"
        "E900000000"
    ))
    struct.pack_into(
        "<i", catalogue_reset, 20,
        CATALOGUE_RESET_RETURN - (catalogue_reset_va + 24),
    )

    list_next_va = patch_va + 0x3F0
    list_next = bytearray(bytes.fromhex(
        "8B0D10EA8A00"
        "83B9E800000002"
        "7D0A"                # custom: stop after the selected catalogue
        "40"
        "89442410"
        "E900000000"
        "E900000000"
    ))
    struct.pack_into(
        "<i", list_next, 21,
        LIST_NEXT_RETURN - (list_next_va + 25),
    )
    struct.pack_into(
        "<i", list_next, 26,
        LIST_EXIT - (list_next_va + 30),
    )

    def native_selector_reset(code_va: int, return_va: int) -> bytes:
        code = bytearray(bytes.fromhex(
            "A110EA8A00" "C780E800000000000000" "A134EA8A00" "E900000000"
        ))
        struct.pack_into("<i", code, 21, return_va - (code_va + 25))
        return bytes(code)

    native_single_va = patch_va + 0x390
    native_carnage_va = patch_va + 0x3B0
    native_single = native_selector_reset(native_single_va, NATIVE_SINGLE_RETURN)
    native_carnage = native_selector_reset(native_carnage_va, NATIVE_CARNAGE_RETURN)

    event_dispatch_va = patch_va + 0x440
    event_dispatch = bytearray(bytes.fromhex(
        "8B4104"                  # original event code
        "8B1510EA8A00"
        "83BAE800000003"          # only inside a detail catalogue
        "7C3E"
        "8BD0"
        "81E2FF0F0003"
        "81FA03000002"            # bexit
        "7408"
        "81FA04000001"            # bexit01
        "7526"
        "8B1510EA8A00"
        "C782E800000002000000"    # return to category catalogue
        "C78608020000FFFFFFFF"
        "8BCE"
        "E800000000"
        "E900000000"
        "25FF0F0003"              # original dispatch operation
        "E900000000"
    ))
    struct.pack_into(
        "<i", event_dispatch, 71,
        0x0063AB60 - (event_dispatch_va + 75),
    )
    struct.pack_into(
        "<i", event_dispatch, 76,
        EVENT_HANDLED_RETURN - (event_dispatch_va + 80),
    )
    struct.pack_into(
        "<i", event_dispatch, 86,
        EVENT_DISPATCH_RETURN - (event_dispatch_va + 90),
    )

    custom_callback = bytearray(bytes.fromhex(
        "8B442408"              # event/control object
        "85C0"
        "7407"
        "C740600000D00C"        # force the dedicated Custom Missions action
        "E900000000"
    ))
    struct.pack_into(
        "<i", custom_callback, 16,
        MENU_CONTROL_HANDLER - (custom_callback_va + 20),
    )

    patch = bytearray(b"\xCC" * 0x500)
    patch[0:len(builder)] = builder
    patch[0x200:0x200 + len(handler)] = handler
    patch[0x300:0x300 + len(list_filter)] = list_filter
    patch[0x340:0x340 + len(list_select)] = list_select
    patch[0x390:0x390 + len(native_single)] = native_single
    patch[0x3B0:0x3B0 + len(native_carnage)] = native_carnage
    patch[0x3D0:0x3D0 + len(catalogue_reset)] = catalogue_reset
    patch[0x3F0:0x3F0 + len(list_next)] = list_next
    patch[0x420:0x42C] = b"bcampaign02\0"
    patch[0x440:0x440 + len(event_dispatch)] = event_dispatch
    patch[0x4A0:0x4A0 + len(custom_callback)] = custom_callback
    write_va(BUILDER_HOOK, b"\xE9" + rel32(BUILDER_HOOK + 5, builder_va) + b"\x90\x90")
    write_va(HANDLER_HOOK, b"\xE9" + rel32(HANDLER_HOOK + 5, handler_va))
    write_va(
        LIST_BUILD_HOOK,
        b"\xE9" + rel32(LIST_BUILD_HOOK + 5, list_filter_va) + b"\x90" * 3,
    )
    write_va(
        LIST_SELECT_HOOK,
        b"\xE9" + rel32(LIST_SELECT_HOOK + 5, list_select_va) + b"\x90",
    )
    write_va(
        EVENT_DISPATCH_HOOK,
        b"\xE9" + rel32(EVENT_DISPATCH_HOOK + 5, event_dispatch_va) + b"\x90" * 3,
    )
    write_va(
        LIST_NEXT_HOOK,
        b"\xE9" + rel32(LIST_NEXT_HOOK + 5, list_next_va),
    )
    write_va(
        NATIVE_SINGLE_HOOK,
        b"\xE9" + rel32(NATIVE_SINGLE_HOOK + 5, native_single_va),
    )
    write_va(
        NATIVE_CARNAGE_HOOK,
        b"\xE9" + rel32(NATIVE_CARNAGE_HOOK + 5, native_carnage_va),
    )
    write_va(
        CATALOGUE_RESET_HOOK,
        b"\xE9" + rel32(CATALOGUE_RESET_HOOK + 5, catalogue_reset_va) + b"\x90" * 5,
    )
    return bytes(patch)


def section_header(
    name: bytes, virtual_size: int, virtual_address: int, raw_size: int,
    raw_offset: int, characteristics: int
) -> bytes:
    return struct.pack(
        "<8sIIIIIIHHI",
        name.ljust(8, b"\0"), virtual_size, virtual_address, raw_size,
        raw_offset, 0, 0, 0, 0, characteristics,
    )


def rebuild_executable(packed: bytes) -> tuple[bytes, dict[str, object]]:
    image, imports = emulate_unpack(packed)
    pe = struct.unpack_from("<I", packed, 0x3C)[0]
    optional = pe + 24
    optional_size = struct.unpack_from("<H", packed, pe + 20)[0]
    section_alignment = struct.unpack_from("<I", packed, optional + 32)[0]
    file_alignment = struct.unpack_from("<I", packed, optional + 36)[0]
    header_size = struct.unpack_from("<I", packed, optional + 60)[0]
    idata_rva = 0x7BD000
    idata, import_rva, import_size, iat_rva, iat_size = build_import_section(
        image, imports, idata_rva
    )
    patch_rva = align(idata_rva + len(idata), 0x1000)
    patch = install_menu_code(image, patch_rva)

    image_raw_size = align(len(image), file_alignment)
    resource_raw_size = RESOURCE_SIZE
    idata_raw_size = align(len(idata), file_alignment)
    patch_raw_size = align(len(patch), file_alignment)
    image_raw = header_size
    resource_raw = image_raw + image_raw_size
    idata_raw = resource_raw + resource_raw_size
    patch_raw = idata_raw + idata_raw_size
    size_of_image = align(patch_rva + len(patch), section_alignment)

    headers = bytearray(packed[:header_size])
    struct.pack_into("<H", headers, pe + 6, 4)
    struct.pack_into("<III", headers, optional + 4, image_raw_size, resource_raw_size + idata_raw_size, 0)
    struct.pack_into("<III", headers, optional + 16, OEP_RVA, OUTPUT_RVA, OUTPUT_RVA)
    struct.pack_into("<II", headers, optional + 56, size_of_image, header_size)
    struct.pack_into("<I", headers, optional + 64, 0)
    directory = optional + 96
    for index in range(16):
        struct.pack_into("<II", headers, directory + index * 8, 0, 0)
    struct.pack_into("<II", headers, directory + 1 * 8, import_rva, import_size)
    struct.pack_into("<II", headers, directory + 2 * 8, RESOURCE_RVA, 0x132C)
    struct.pack_into("<II", headers, directory + 9 * 8, TLS_RVA, 0x18)
    struct.pack_into("<II", headers, directory + 12 * 8, iat_rva, iat_size)
    table = optional + optional_size
    section_headers = (
        section_header(b".hd2", len(image), OUTPUT_RVA, image_raw_size, image_raw, 0xE0000020)
        + section_header(b".rsrc", 0x2000, RESOURCE_RVA, resource_raw_size, resource_raw, 0x40000040)
        + section_header(b".idata", len(idata), idata_rva, idata_raw_size, idata_raw, 0xC0000040)
        + section_header(b".patch", len(patch), patch_rva, patch_raw_size, patch_raw, 0x60000020)
    )
    headers[table:table + len(section_headers)] = section_headers
    resource = packed[0x22A800:0x22A800 + RESOURCE_SIZE]
    result = (
        bytes(headers)
        + bytes(image).ljust(image_raw_size, b"\0")
        + resource.ljust(resource_raw_size, b"\0")
        + idata.ljust(idata_raw_size, b"\0")
        + patch.ljust(patch_raw_size, b"\0")
    )
    return result, {
        "imports": len(imports),
        "dlls": list(OrderedDict.fromkeys(str(item["dll"]) for item in imports)),
        "entry_rva": OEP_RVA,
        "patch_rva": patch_rva,
        "size": len(result),
        "sha256": digest(result),
    }


def validate_rebuilt_executable(data: bytes, report: dict[str, object]) -> None:
    import pefile

    executable = pefile.PE(data=data, fast_load=False)
    names = [section.Name.rstrip(b"\0").decode("ascii") for section in executable.sections]
    if names != [".hd2", ".rsrc", ".idata", ".patch"]:
        raise ValueError(f"Sections PE inattendues : {names}")
    if executable.OPTIONAL_HEADER.ImageBase != IMAGE_BASE:
        raise ValueError("Base du fichier reconstruit incorrecte")
    if executable.OPTIONAL_HEADER.AddressOfEntryPoint != OEP_RVA:
        raise ValueError("Point d'entrée reconstruit incorrect")
    if not hasattr(executable, "DIRECTORY_ENTRY_IMPORT"):
        raise ValueError("Table d'importation reconstruite absente")
    import_count = sum(len(module.imports) for module in executable.DIRECTORY_ENTRY_IMPORT)
    if import_count != report["imports"]:
        raise ValueError(
            f"Nombre d'importations incohérent ({import_count} au lieu de {report['imports']})"
        )
    for module in executable.DIRECTORY_ENTRY_IMPORT:
        thunk_size = (len(module.imports) + 1) * 4
        lookup = executable.get_data(module.struct.OriginalFirstThunk, thunk_size)
        iat = executable.get_data(module.struct.FirstThunk, thunk_size)
        if lookup != iat:
            raise ValueError(
                f"IAT non initialisée pour {module.dll.decode('ascii', errors='replace')}"
            )
    patch_section = executable.sections[-1]
    patch_data = patch_section.get_data()
    if b"bcampaign02\0" not in patch_data:
        raise ValueError("Identifiant du menu personnalisé absent du correctif")
    if patch_data[14:19] != b"\x68" + struct.pack("<I", 20402):
        raise ValueError("Libellé localisé du bouton personnalisé absent")
    def patch_jump_target(displacement_offset: int) -> int:
        displacement = struct.unpack_from("<i", patch_data, displacement_offset)[0]
        next_address = IMAGE_BASE + report["patch_rva"] + displacement_offset + 4
        return next_address + displacement

    expected_patch_jumps = {
        0x200 + 48: HANDLER_SINGLE_MISSION_TAIL,
        0x300 + 32: LIST_BUILD_RETURN,
        0x340 + 46: 0x0063AB60,
        0x340 + 51: EVENT_HANDLED_RETURN,
        0x340 + 62: LIST_SELECT_RETURN,
        0x390 + 21: NATIVE_SINGLE_RETURN,
        0x3B0 + 21: NATIVE_CARNAGE_RETURN,
        0x3D0 + 20: CATALOGUE_RESET_RETURN,
        0x3F0 + 21: LIST_NEXT_RETURN,
        0x3F0 + 26: LIST_EXIT,
        0x440 + 71: 0x0063AB60,
        0x440 + 76: EVENT_HANDLED_RETURN,
        0x440 + 86: EVENT_DISPATCH_RETURN,
        0x4A0 + 16: MENU_CONTROL_HANDLER,
    }
    for displacement_offset, expected_target in expected_patch_jumps.items():
        if patch_jump_target(displacement_offset) != expected_target:
            raise ValueError(
                f"Destination de correctif incorrecte à +0x{displacement_offset:X}"
            )
    if patch_data[0x308:0x31F] != bytes.fromhex(
        "8B86E800000083F8027C0C8BF8C7850C02000064000000"
    ):
        raise ValueError("Filtrage du catalogue personnalisé absent")
    if patch_data[0x340:0x36D] != bytes.fromhex(
        "83B9E8000000027C2E75328B96080200002BD083FA02770983C2038991E8000000C78608020000FFFFFFFF8BCE"
    ):
        raise ValueError("Navigation des catégories personnalisées absente")
    custom_callback_va = IMAGE_BASE + report["patch_rva"] + 0x4A0
    if (
        struct.unpack_from("<I", patch_data, 37)[0] != custom_callback_va
        or struct.unpack_from("<I", patch_data, 61)[0] != custom_callback_va
    ):
        raise ValueError("Rappel dédié du bouton personnalisé absent")
    if patch_data[0x4A0:0x4AF] != bytes.fromhex(
        "8B44240885C07407C740600000D00C"
    ):
        raise ValueError("Action dédiée du bouton personnalisé absente")

    # Execute the two small trampolines outside the game. This proves both the
    # callback calling convention ([esp+8] is the originating control) and the
    # effective 0x0CD00000 -> catalogue selector 2 route instead of merely
    # checking that the expected bytes happen to be present.
    stack_base = 0x00200000
    object_base = 0x00300000
    callback_machine = Uc(UC_ARCH_X86, UC_MODE_32)
    callback_machine.mem_map(IMAGE_BASE + report["patch_rva"], 0x1000, UC_PROT_ALL)
    callback_machine.mem_write(IMAGE_BASE + report["patch_rva"], patch_data[:0x500])
    callback_machine.mem_map(stack_base, 0x1000, UC_PROT_ALL)
    callback_machine.mem_map(object_base, 0x1000, UC_PROT_ALL)
    callback_esp = stack_base + 0x800
    callback_machine.mem_write(
        callback_esp,
        struct.pack("<IIIII", 0, 0, object_base, 0x04001000, 0),
    )
    callback_machine.reg_write(UC_X86_REG_ESP, callback_esp)
    callback_machine.emu_start(
        custom_callback_va, MENU_CONTROL_HANDLER, count=16
    )
    if struct.unpack(
        "<I", callback_machine.mem_read(object_base + 0x60, 4)
    )[0] != 0x0CD00000:
        raise ValueError("Le rappel personnalisé ne produit pas réellement l'action 0x0CD00000")

    handler_va = IMAGE_BASE + report["patch_rva"] + 0x200
    handler_machine = Uc(UC_ARCH_X86, UC_MODE_32)
    handler_machine.mem_map(IMAGE_BASE + report["patch_rva"], 0x1000, UC_PROT_ALL)
    handler_machine.mem_write(IMAGE_BASE + report["patch_rva"], patch_data[:0x500])
    handler_machine.mem_map(0x008AE000, 0x1000, UC_PROT_ALL)
    handler_machine.mem_map(object_base, 0x2000, UC_PROT_ALL)
    catalogue_manager = object_base
    menu_state = object_base + 0x1000
    handler_machine.mem_write(
        0x008AEA10, struct.pack("<I", catalogue_manager)
    )
    handler_machine.mem_write(0x008AEA34, struct.pack("<I", menu_state))
    handler_machine.reg_write(UC_X86_REG_EAX, 0x0CD00000)
    handler_machine.emu_start(
        handler_va, HANDLER_SINGLE_MISSION_TAIL, count=32
    )
    if struct.unpack(
        "<I", handler_machine.mem_read(catalogue_manager + 0xE8, 4)
    )[0] != 2:
        raise ValueError("L'action personnalisée n'ouvre pas réellement le catalogue de catégories")


def archive_entry(game: Path, name: str) -> bytes:
    wanted = name.replace("/", "\\").casefold()
    with DtaArchive(game / "SabreSquadron.dta") as archive:
        for entry in archive.entries:
            if entry.name.casefold() == wanted:
                return archive.read(entry)
    raise FileNotFoundError(name)


def encode_block(kind: int, payload: bytes) -> bytes:
    return struct.pack("<HI", kind, len(payload) + 6) + payload


def encode_existing_block(node) -> bytes:
    payload = (
        b"".join(encode_existing_block(child) for child in node.children)
        if node.children else node.payload
    )
    return encode_block(node.kind, payload)


def encode_integer_block(kind: int, value: int) -> bytes:
    return encode_block(kind, struct.pack("<I", value))


def encode_string_block(kind: int, value: str, model_payload: bytes) -> bytes:
    suffix = b"\0" if model_payload.endswith(b"\0") else b""
    return encode_block(kind, value.encode("ascii") + suffix)


def rewrite_objective(node, text_id: int) -> bytes:
    payload = bytearray()
    replaced = False
    for child in node.children:
        if child.kind == 0x29 and not replaced:
            payload.extend(encode_integer_block(0x29, text_id))
            replaced = True
        else:
            payload.extend(encode_existing_block(child))
    if not replaced:
        raise ValueError("Identifiant d'objectif absent du catalogue modèle")
    return encode_block(node.kind, bytes(payload))


def rewrite_mission(node, mission: dict) -> bytes:
    payload = bytearray()
    title_replaced = False
    directory_replaced = False
    loading_replaced = mission["loading_screen"] is None
    objectives_replaced = mission.get("objective_ids") is None
    objective_model = next((child for child in node.children if child.kind == 0x28), None)
    for child in node.children:
        if child.kind == 0x33 and not title_replaced:
            payload.extend(encode_integer_block(0x33, mission["title_id"]))
            title_replaced = True
        elif child.kind == 0x35 and not loading_replaced:
            payload.extend(encode_string_block(0x35, mission["loading_screen"], child.payload))
            loading_replaced = True
        elif child.kind == 0x36 and not directory_replaced:
            payload.extend(encode_string_block(0x36, mission["mission_directory"], child.payload))
            directory_replaced = True
        elif child.kind == 0x28 and mission.get("objective_ids") is not None:
            if not objectives_replaced:
                if objective_model is None and mission["objective_ids"]:
                    raise ValueError("Le gabarit ne contient aucun objectif clonable")
                for text_id in mission["objective_ids"]:
                    payload.extend(rewrite_objective(objective_model, text_id))
                objectives_replaced = True
        else:
            payload.extend(encode_existing_block(child))
    if not title_replaced or not directory_replaced or not loading_replaced:
        raise ValueError("Champs de mission absents du catalogue modèle")
    return encode_block(node.kind, bytes(payload))


def rewrite_campaign(node, header_id: int, missions: list[dict], templates: dict) -> bytes:
    payload = bytearray()
    header_replaced = False
    missions_written = False
    default_template = next(
        (item for item in walk(node.children) if item.kind == 0x32), None
    )
    if default_template is None:
        raise ValueError("Campagne modèle sans mission")
    for child in node.children:
        if child.kind == 0x3D and not header_replaced:
            payload.extend(encode_integer_block(0x3D, header_id))
            header_replaced = True
        elif child.kind == 0x05:
            content = bytearray()
            for item in child.children:
                if item.kind == 0x32:
                    if not missions_written:
                        for mission in missions:
                            template_name = mission.get("template_mission")
                            template = templates.get(template_name.casefold()) if template_name else default_template
                            if template is None:
                                raise ValueError(
                                    f"Mission modèle inconnue : {template_name}"
                                )
                            content.extend(rewrite_mission(template, mission))
                        missions_written = True
                else:
                    content.extend(encode_existing_block(item))
            payload.extend(encode_block(0x05, bytes(content)))
        else:
            payload.extend(encode_existing_block(child))
    if not header_replaced or not missions_written:
        raise ValueError("Campagne modèle incomplète")
    return encode_block(node.kind, bytes(payload))


def custom_catalogue(data: bytes, packages: list[dict] | None = None) -> bytes:
    root = blocks(data, 0, len(data))
    if root is None:
        raise ValueError("Catalogue Sabre modèle illisible")
    top_container = next((node for node in root if node.kind == 0x01), None)
    if top_container is None:
        raise ValueError("Conteneur principal du catalogue absent")
    main_container = next(iter(direct(top_container, 0x05)), None)
    if main_container is None:
        raise ValueError("Liste des campagnes absente")
    source_campaigns = [node for node in main_container.children if node.kind == 0x3C]
    if len(source_campaigns) < 3:
        raise ValueError("Catalogue Sabre insuffisant pour les trois gabarits")
    template_missions = {
        item_value.casefold(): item
        for item in (node for node in walk(main_container.children) if node.kind == 0x32)
        for item_value in [
            next(
                (
                    child.payload.rstrip(b"\0").decode("cp1252")
                    for child in item.children if child.kind == 0x36
                ),
                "",
            )
        ]
        if item_value
    }
    if packages is None:
        packages = technical_packages()
    grouped = {
        category: [item for item in packages if item["category"] == category]
        for category in CATEGORY_ORDER
    }
    campaign_specs = {
        index: (CATEGORIES[category], grouped[category])
        for index, category in enumerate(CATEGORY_ORDER)
        if grouped[category]
    }

    main_payload = bytearray()
    campaign_index = 0
    for node in main_container.children:
        if node.kind == 0x3C:
            if campaign_index in campaign_specs:
                header_id, missions = campaign_specs[campaign_index]
                main_payload.extend(
                    rewrite_campaign(node, header_id, missions, template_missions)
                )
            campaign_index += 1
        else:
            main_payload.extend(encode_existing_block(node))
    main_bytes = encode_block(0x05, bytes(main_payload))

    top_payload = bytearray()
    replaced_main = False
    for node in top_container.children:
        if node is main_container:
            top_payload.extend(main_bytes)
            replaced_main = True
        else:
            top_payload.extend(encode_existing_block(node))
    if not replaced_main:
        raise ValueError("Remplacement du catalogue principal impossible")
    rebuilt_top = encode_block(0x01, bytes(top_payload))
    result = b"".join(
        rebuilt_top if node is top_container else encode_existing_block(node)
        for node in root
    )

    from menu_gui_audit import catalogue
    decoded = catalogue(result, "Gamedata02.gdt")
    decoded_directories = [
        mission["directory"]
        for campaign in decoded["campaigns"]
        for mission in campaign["missions"]
    ]
    expected_directories = [
        item["mission_directory"]
        for category in CATEGORY_ORDER
        for item in grouped[category]
    ]
    if (
        decoded["campaign_count"] != len(campaign_specs)
        or decoded["mission_count"] != len(packages)
    ):
        raise ValueError("Validation du catalogue personnalisé impossible")
    if decoded_directories != expected_directories:
        raise ValueError(f"Missions personnalisées inattendues : {decoded_directories}")
    return result


def technical_packages() -> list[dict]:
    technical = (
        ("multiplayer-adaptation", 20420, "Brest"),
        ("user-mission", 20421, "Libye1"),
        ("free-exploration", 20422, "Sicily1"),
    )
    return [
        {
            "category": category,
            "title_id": text_id,
            "mission_directory": directory,
            "loading_screen": None,
            "template_mission": directory,
            "objective_ids": None,
        }
        for category, text_id, directory in technical
    ]


def split_custom_catalogues(
    data: bytes, packages: list[dict] | None = None
) -> dict[str, bytes]:
    technical = technical_packages()
    category_entries = [
        {
            **item,
            "title_id": CATEGORIES[item["category"]],
        }
        for item in technical
    ]
    detail_packages = technical if packages is None else packages
    result = {"Gamedata02.gdt": custom_catalogue(data, category_entries)}
    for index, category in enumerate(CATEGORY_ORDER, start=3):
        result[f"Gamedata{index:02d}.gdt"] = custom_catalogue(
            data,
            [item for item in detail_packages if item["category"] == category],
        )
    return result


def custom_text_tables(game: Path, packages: list[dict] | None = None) -> dict[Path, bytes]:
    text_root = game / "Text"
    if not text_root.is_dir():
        raise FileNotFoundError(text_root)
    updates: dict[Path, bytes] = {}
    for language in sorted((path for path in text_root.iterdir() if path.is_dir()), key=lambda p: p.name.casefold()):
        path = language / "TEXTY_DD.txt"
        if not path.is_file():
            continue
        data = path.read_bytes()
        separator = b"\r\n" if b"\r\n" in data else b"\n"
        language_key = language.name.casefold()
        values = dict(CUSTOM_TEXT_IDS)
        values.update(CUSTOM_TEXT_BY_LANGUAGE.get(language_key, {}))
        if packages:
            values.update(localized_values(packages, language_key))
        encoding = CUSTOM_TEXT_ENCODINGS.get(language_key, "cp1252")
        for text_id, value in values.items():
            encoded = f'{text_id}\t"{value}"'.encode(encoding)
            pattern = re.compile(
                rb"(?m)^[ \t]*" + str(text_id).encode("ascii") + rb"\b[^\r\n]*"
            )
            if pattern.search(data):
                data = pattern.sub(lambda _match, line=encoded: line, data)
            else:
                if data and not data.endswith((b"\r", b"\n")):
                    data += separator
                data += encoded + separator
        updates[path] = data
    if not updates:
        raise ValueError("Aucune table TEXTY_DD.txt installée")
    return updates


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".static-menu.tmp")
    try:
        temporary.write_bytes(data)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def safe_game_target(game: Path, relative: Path) -> Path:
    target = (game / relative).resolve()
    if target != game and game not in target.parents:
        raise ValueError(f"Chemin de paquet hors du jeu : {relative}")
    return target


def custom_menu_scene(data: bytes) -> bytes:
    scene = parse_4ds_nodes(data)
    nodes = scene["nodes"]
    by_name = {node["name"]: node for node in nodes}
    if "bcampaign02" in by_name:
        raise ValueError("Le nom technique réservé au bouton personnalisé existe déjà")
    # Clone the native Single Mission control so the button artwork and its
    # behaviour agree. Registration occurs after native Back (0x0CC00000), so
    # bcampaign02 is the next action (0x0CD00000); its dedicated callback also
    # normalizes the value before entering the native handler.
    root = by_name["bsingle mission"]
    children = sorted(
        (node for node in nodes if node["parent_id"] == root["index"]),
        key=lambda node: node["index"],
    )
    if [node["name"] for node in children] != ["actived03", "normal03"]:
        raise ValueError("Sous-arbre de mission solo inattendu")
    new_root = scene["node_count"] + 1
    replacements = {
        "bsingle mission": b"bcampaign02",
        "actived03": b"actived10",
        "normal03": b"normal10",
    }
    # Preserve every official control at its exact original coordinate.
    layout = bytearray(data)

    def interpolate(left: list[float], right: list[float], ratio: float) -> list[float]:
        return [
            left[axis] + (right[axis] - left[axis]) * ratio
            for axis in range(3)
        ]

    # Place one custom button halfway through the native empty space between
    # Single Mission - Carnage and Back, matching the requested mock-up.
    custom_ratio = 0.5
    custom_positions = {
        "bsingle mission": interpolate(
            by_name["bsingle mission- carnage"]["position"],
            by_name["bback"]["position"],
            custom_ratio,
        ),
        "normal03": interpolate(
            by_name["normal04"]["position"],
            by_name["normal06"]["position"],
            custom_ratio,
        ),
        "actived03": interpolate(
            by_name["actived04"]["position"],
            by_name["actived06"]["position"],
            custom_ratio,
        ),
    }
    clones = []
    for node in [root] + children:
        record = bytearray(layout[node["start"]:node["end"]])
        name_offset = node["name_offset"] - node["start"]
        name_length_offset = node["name_length_offset"] - node["start"]
        old_length = node["name_length"]
        new = replacements[node["name"]]
        record = (
            record[:name_length_offset]
            + bytes((len(new),))
            + new
            + record[name_offset + old_length:]
        )
        parent_offset = node["parent_offset"] - node["start"]
        struct.pack_into("<H", record, parent_offset, 0 if node is root else new_root)
        position = custom_positions[node["name"]]
        struct.pack_into("<3f", record, node["position_offset"] - node["start"], *position)
        clones.append(bytes(record))

    table_end = scene["nodes"][-1]["end"]
    result = bytearray(layout[:table_end] + b"".join(clones) + layout[table_end:])
    struct.pack_into("<H", result, scene["node_count_offset"], scene["node_count"] + 3)
    parsed = parse_4ds_nodes(bytes(result))
    if parsed["node_count"] != 45:
        raise ValueError("Validation 4DS finale impossible")
    for original_node, final_node in zip(nodes, parsed["nodes"][:scene["node_count"]]):
        if (
            original_node["name"] != final_node["name"]
            or original_node["position"] != final_node["position"]
        ):
            raise ValueError("La disposition officielle a été modifiée")
    final_names = {node["name"] for node in parsed["nodes"]}
    if not {"bcampaign02", "normal10", "actived10"} <= final_names:
        raise ValueError("Contrôles personnalisés absents de la scène finale")
    return bytes(result)


def custom_mission_scene(data: bytes) -> bytes:
    """Add a native category menu and reliable Back control to the mission scene.

    The stock list and its controls are kept byte-for-byte. Runtime code only
    hides them while the category selector is active, then restores them for
    the actual mission lists.
    """
    scene = parse_4ds_nodes(data)
    nodes = scene["nodes"]
    by_name = {node["name"]: node for node in nodes}
    reserved = {"bcustom user", "bcustom multi", "bcustom explore"}
    if reserved & set(by_name):
        raise ValueError("Les contrôles du sous-menu personnalisé existent déjà")
    root = by_name["bexit"]
    children = sorted(
        (node for node in nodes if node["parent_id"] == root["index"]),
        key=lambda node: node["index"],
    )
    if [node["name"] for node in children] != ["normal04", "actived04"]:
        raise ValueError("Sous-arbre du bouton Retour inattendu")

    specifications = (
        ("bcustom user", "normal11", "actived11", -0.237),
        ("bcustom multi", "normal12", "actived12", -0.323),
        ("bcustom explore", "normal13", "actived13", -0.409),
    )
    layout = bytearray(data)
    clones: list[bytes] = []
    for control_name, normal_name, active_name, vertical in specifications:
        new_root = scene["node_count"] + len(clones) + 1
        replacements = {
            "bexit": control_name.encode("ascii"),
            "normal04": normal_name.encode("ascii"),
            "actived04": active_name.encode("ascii"),
        }
        for node in [root] + children:
            record = bytearray(layout[node["start"]:node["end"]])
            name_offset = node["name_offset"] - node["start"]
            name_length_offset = node["name_length_offset"] - node["start"]
            replacement = replacements[node["name"]]
            record = (
                record[:name_length_offset]
                + bytes((len(replacement),))
                + replacement
                + record[name_offset + node["name_length"]:]
            )
            parent_offset = node["parent_offset"] - node["start"]
            struct.pack_into(
                "<H", record, parent_offset, 0 if node is root else new_root
            )
            if node is not root and vertical is not None:
                position = list(node["position"])
                position[2] = vertical - (0.004 if node["name"] == "actived04" else 0)
                struct.pack_into(
                    "<3f", record, node["position_offset"] - node["start"], *position
                )
            clones.append(bytes(record))

    table_end = scene["nodes"][-1]["end"]
    result = bytearray(layout[:table_end] + b"".join(clones) + layout[table_end:])
    struct.pack_into(
        "<H", result, scene["node_count_offset"], scene["node_count"] + len(clones)
    )
    parsed = parse_4ds_nodes(bytes(result))
    if parsed["node_count"] != scene["node_count"] + 9:
        raise ValueError("Validation du sous-menu 4DS impossible")
    for original_node, final_node in zip(nodes, parsed["nodes"][:scene["node_count"]]):
        if (
            original_node["name"] != final_node["name"]
            or original_node["position"] != final_node["position"]
        ):
            raise ValueError("La liste de missions native a été modifiée")
    final_names = {node["name"] for node in parsed["nodes"]}
    if not reserved <= final_names:
        raise ValueError("Boutons du sous-menu absents de la scène finale")
    return bytes(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_game", type=Path)
    parser.add_argument("test_game", type=Path)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="construit et valide en mémoire sans écrire dans l'installation de test",
    )
    parser.add_argument(
        "--mission-library",
        type=Path,
        help="dossier contenant un sous-dossier et un mission.json par mission",
    )
    arguments = parser.parse_args()
    original = arguments.original_game.resolve()
    target = arguments.test_game.resolve()
    if original == target or original in target.parents:
        raise ValueError("La cible doit être une installation de test séparée")
    source_executable = original / "HD2_SabreSquadron.exe"
    target_executable = target / "HD2_SabreSquadron.exe"
    packed = source_executable.read_bytes()
    if digest(packed) != EXPECTED_SOURCE_SHA256:
        raise ValueError("Empreinte de l'exécutable original inattendue")
    if not target_executable.is_file():
        raise FileNotFoundError(target_executable)

    packages = (
        load_library(
            arguments.mission_library.resolve(),
            write_registry=not arguments.dry_run,
        )
        if arguments.mission_library is not None else None
    )
    payload_items = [
        {**item, "package_id": package["id"]}
        for package in (packages or [])
        for item in package["files"]
    ]

    rebuilt, report = rebuild_executable(packed)
    validate_rebuilt_executable(rebuilt, report)
    menu = custom_menu_scene(archive_entry(original, "Models\\singleplayer.4ds"))
    catalogues = split_custom_catalogues(
        archive_entry(original, "GameData\\Gamedata01.gdt"), packages
    )
    text_tables = custom_text_tables(target, packages)
    restore_source = PROJECT / "tools" / "RestaurerMenuTest.ps1"
    if not restore_source.is_file():
        raise FileNotFoundError(restore_source)
    report.update({
        "status": "STATIC_BUILD_VALIDATED_NOT_WRITTEN" if arguments.dry_run else "STATIC_TEST_BUILD_NOT_LAUNCHED",
        "target": str(target),
        "menu_sha256": digest(menu),
        "catalogue_sha256": {
            name: digest(data) for name, data in catalogues.items()
        },
        "catalogue_sections": (
            list(CATEGORY_ORDER) if packages is None else [
                category for category in CATEGORY_ORDER
                if any(item["category"] == category for item in packages)
            ]
        ),
        "custom_action": "OPEN_GROUPED_CUSTOM_MISSION_BROWSER",
        "custom_control_name": "bcampaign02",
        "custom_effective_action": "0x0CD00000",
        "custom_action_validation": "EMULATED_CALLBACK_AND_BRANCH_TO_SELECTOR_2",
        "custom_list_scope": "GAMEDATA02_CATEGORIES_AND_GAMEDATA03_TO_05_DETAILS",
        "category_title_ids": {
            category: CATEGORIES[category] for category in CATEGORY_ORDER
        },
        "category_detail_catalogues": {
            category: f"Gamedata{index:02d}.gdt"
            for index, category in enumerate(CATEGORY_ORDER, start=3)
        },
        "custom_visibility": "ALL_CUSTOM_ENTRIES_WITHOUT_PROFILE_WRITE",
        "native_single_mission_scope": "OFFICIAL_CATALOGUES",
        "menu_layout": "ORIGINAL_LAYOUT_PLUS_ONE_CUSTOM_BUTTON",
        "localized_custom_label": 20402,
        "technical_slots": ["Brest", "Libye1", "Sicily1"] if packages is None else [],
        "mission_library": (
            None if arguments.mission_library is None
            else str(arguments.mission_library.resolve())
        ),
        "custom_packages": (
            {"packages": 0, "missions": [], "payload_files": 0}
            if packages is None else package_summary(packages)
        ),
        "text_tables": len(text_tables),
        "restore_script": "RestaurerMenuTest.ps1",
        "original_sha256": digest(packed),
    })
    if arguments.dry_run:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    backup = target / "HD2_SabreSquadron.original.exe"
    if backup.exists():
        if digest(backup.read_bytes()) != EXPECTED_SOURCE_SHA256:
            raise ValueError("La sauvegarde de l'exécutable de test n'est pas l'original attendu")
    else:
        current = target_executable.read_bytes()
        if digest(current) != EXPECTED_SOURCE_SHA256:
            raise ValueError("L'exécutable de test n'est pas une copie propre de l'original")
        atomic_write(backup, current)

    menu_path = target / "Models" / "singleplayer.4ds"
    catalogue_paths = {
        target / "GameData" / name: data for name, data in catalogues.items()
    }
    backup_root = target / "STATIC_MENU_BACKUP"
    payload_targets = [
        {**item, "target": safe_game_target(target, item["relative"])}
        for item in payload_items
    ]
    managed_path = target / "STATIC_MENU_MANAGED_FILES.json"
    managed = {"format": 1, "files": []}
    if managed_path.is_file():
        managed = json.loads(managed_path.read_text(encoding="utf-8-sig"))
        if managed.get("format") != 1 or not isinstance(managed.get("files"), list):
            raise ValueError("Journal des fichiers de missions invalide")
    managed_by_path = {
        item["relative"].casefold(): item for item in managed["files"]
    }
    for item in payload_targets:
        relative = item["relative"].as_posix()
        previous = managed_by_path.get(relative.casefold())
        data = item["source"].read_bytes()
        item["data"] = data
        managed_by_path[relative.casefold()] = {
            "relative": relative,
            "created": (
                previous["created"] if previous is not None
                else not item["target"].exists()
            ),
            "sha256": digest(data),
            "package_id": item["package_id"],
        }
    files_to_replace = [
        menu_path, *catalogue_paths.keys(), *text_tables.keys(),
        *(item["target"] for item in payload_targets),
    ]
    for path in files_to_replace:
        if not path.exists():
            continue
        relative = path.relative_to(target)
        saved = backup_root / relative
        if not saved.exists():
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, saved)

    atomic_write(target_executable, rebuilt)
    atomic_write(menu_path, menu)
    for path, data in catalogue_paths.items():
        atomic_write(path, data)
    for path, data in text_tables.items():
        atomic_write(path, data)
    for item in payload_targets:
        atomic_write(item["target"], item["data"])
    managed["files"] = sorted(
        managed_by_path.values(), key=lambda item: item["relative"].casefold()
    )
    atomic_write(
        managed_path,
        (json.dumps(managed, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    atomic_write(target / "RestaurerMenuTest.ps1", restore_source.read_bytes())
    report_path = target / "STATIC_MENU_PATCH.json"
    atomic_write(
        report_path,
        (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    if not target_executable.exists() or digest(target_executable.read_bytes()) != report["sha256"]:
        raise RuntimeError("L'exécutable statique écrit n'est pas resté intact")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
