#!/usr/bin/env python3
"""Inspect and extract Hidden & Dangerous 2 ISD0/ISD1 DTA archives.

Format reference and GPL-3.0 implementation:
https://github.com/M3tox/HD2unpacker
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path, PureWindowsPath

ARCHIVES = (
    ("Maps", 0xB438AB00, 0xF26527FAB438D0A5),
    ("Maps_C", 0xB038DC00, 0xE26520FAB038D0A0),
    ("Maps_U", 0xB038DD00, 0xF26520FAB038D1A1),
    ("Missions", 0x7654A100, 0x22BCDA987654A3F0),
    ("Models", 0x5D804E00, 0x10ACB2525D805259),
    ("Others", 0xEA859B00, 0x65F7AB23EA85902A),
    ("Sounds", 0x4FE84300, 0x8D2965CA4FE85106),
    ("Scripts", 0x0AB4EB00, 0xCF7612980AB4E72D),
    ("SabreSquadron", 0xA0A08600, 0xA0A0A0A0A0A0A0A1),
    ("Patch", 0x5D805600, 0x10ACB2525D805270),
    ("LangEnglish", 0xA0A0A600, 0xA0A0A0A0A0A0A0A0),
    ("Demo SP data", 0x5D804D00, 0x10ACB2525D8052A0),
    ("Demo MP data", 0x5D807600, 0x10ACB2525D8052A0),
    ("Demo Sabre Squadron data", 0x5D807300, 0x10ACB2525D8052A0),
    ("PatchX01", 0xA0A0A000, 0xA0A0A0A0A0A0A0A2),
)


@dataclass(frozen=True)
class Entry:
    index: int
    name: str
    size: int
    blocks: int
    encrypted: bool
    header_offset: int
    data_offset: int


def xor_data(data: bytes, key: int) -> bytes:
    key_bytes = key.to_bytes(8, "little")
    return bytes(value ^ key_bytes[index % 8] for index, value in enumerate(data))


def decode_name(data: bytes) -> str:
    return data.rstrip(b"\x00").decode("cp1252", errors="replace")


def decompress_lzss(source: bytes) -> bytes:
    destination = bytearray()
    position = 0
    while position < len(source):
        if position + 2 > len(source):
            raise ValueError("Truncated LZSS group")
        value = (source[position] << 8) | source[position + 1]
        position += 2
        if value == 0:
            segment = min(len(source) - position, 16)
            destination.extend(source[position : position + segment])
            position += segment
            continue
        for _ in range(16):
            if position >= len(source):
                break
            if value & 0x8000:
                if position + 2 > len(source):
                    raise ValueError("Truncated LZSS back-reference")
                offset = (source[position] << 4) | (source[position + 1] >> 4)
                length = source[position + 1] & 0x0F
                if offset == 0:
                    if position + 4 > len(source):
                        raise ValueError("Truncated LZSS run")
                    length = ((length << 8) | source[position + 2]) + 16
                    destination.extend(bytes((source[position + 3],)) * length)
                    position += 4
                else:
                    length += 3
                    if offset > len(destination):
                        raise ValueError("Invalid LZSS back-reference")
                    for _ in range(length):
                        destination.append(destination[-offset])
                    position += 2
            else:
                destination.append(source[position])
                position += 1
            value = (value << 1) & 0xFFFF
    return bytes(destination)


class DtaArchive:
    def __init__(self, path: Path):
        self.path = path
        self.stream = path.open("rb")
        signature = self.stream.read(4)
        if signature not in (b"ISD0", b"ISD1"):
            raise ValueError(f"Unsupported DTA signature: {signature!r}")
        self.version = signature.decode("ascii")
        encrypted_header = self.stream.read(16)
        encrypted_count = struct.unpack_from("<I", encrypted_header)[0]
        definition = next(
            (item for item in ARCHIVES if item[1] == encrypted_count & 0xFFFFFF00),
            None,
        )
        if definition is None and encrypted_count == 0xA0A0B170:
            definition = ARCHIVES[10]
        if definition is None:
            raise ValueError(f"Unknown DTA identifier 0x{encrypted_count:08X}")
        self.kind, _, self.key = definition
        header = xor_data(encrypted_header, self.key)
        self.file_count, self.table_offset, self.table_size, self.extra = struct.unpack(
            "<IIII", header
        )
        if self.file_count <= 0 or self.table_size < self.file_count * 28:
            raise ValueError("Invalid DTA table metadata")
        if self.table_offset + self.file_count * 28 > path.stat().st_size:
            raise ValueError("DTA table lies outside the archive")
        self.stream.seek(self.table_offset)
        table = xor_data(self.stream.read(self.file_count * 28), self.key)
        self.records = [
            struct.unpack_from("<HHII16s", table, index * 28)
            for index in range(self.file_count)
        ]
        self.entries = tuple(self._read_entry(index) for index in range(self.file_count))

    def close(self) -> None:
        self.stream.close()

    def __enter__(self) -> "DtaArchive":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _read_entry(self, index: int) -> Entry:
        _, table_name_length, header_offset, data_offset, _ = self.records[index]
        self.stream.seek(header_offset)
        header = xor_data(self.stream.read(32), self.key)
        if self.version == "ISD0":
            _, _, _, size, blocks, name_length, flags = struct.unpack(
                "<IIQIIB7s", header
            )
        else:
            _, _, _, size, blocks, _, name_length, flags = struct.unpack(
                "<IIQIIIB3s", header
            )
        if table_name_length != name_length:
            raise ValueError(f"Inconsistent filename length at index {index}")
        name = decode_name(xor_data(self.stream.read(name_length), self.key))
        return Entry(
            index, name, size, blocks, bool(flags[0] & 0x80),
            header_offset, data_offset
        )

    def read(self, entry: Entry) -> bytes:
        self.stream.seek(entry.header_offset + 32)
        name = xor_data(self.stream.read(self.records[entry.index][1]), self.key)
        if decode_name(name) != entry.name:
            raise ValueError(f"Filename changed while reading {entry.name}")
        destination = bytearray()
        if self.version == "ISD1":
            raw_sizes = self.stream.read(entry.blocks * 4)
            sizes = struct.unpack(f"<{entry.blocks}I", raw_sizes)
            types = xor_data(self.stream.read(entry.blocks), self.key)
            for raw_size, block_type in zip(sizes, types):
                block = self.stream.read(raw_size & 0xFFFF)
                if entry.encrypted:
                    block = xor_data(block, self.key)
                destination.extend(self._decode_block(block_type, block, entry.name))
        else:
            for _ in range(entry.blocks):
                raw_size = self.stream.read(4)
                if len(raw_size) != 4:
                    raise ValueError(f"Truncated block size in {entry.name}")
                size = struct.unpack("<I", raw_size)[0] & 0xFFFF
                block = self.stream.read(size)
                if entry.encrypted:
                    block = xor_data(block, self.key)
                if not block:
                    raise ValueError(f"Empty block in {entry.name}")
                destination.extend(self._decode_block(block[0], block[1:], entry.name))
        if len(destination) != entry.size:
            raise ValueError(
                f"Decoded size mismatch for {entry.name}: "
                f"{len(destination)} != {entry.size}"
            )
        return bytes(destination)

    @staticmethod
    def _decode_block(block_type: int, block: bytes, name: str) -> bytes:
        if block_type == 0:
            return block
        if block_type == 1:
            return decompress_lzss(block)
        raise ValueError(
            f"Unsupported DPCM audio block type {block_type} in {name}"
        )

    def extract(self, entry: Entry, destination: Path) -> Path:
        relative = PureWindowsPath(entry.name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe archived path: {entry.name}")
        output = destination.joinpath(*relative.parts)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(self.read(entry))
        return output


def matches(name: str, patterns: list[str]) -> bool:
    lowered = name.lower()
    return not patterns or any(
        fnmatch.fnmatch(lowered, pattern.lower()) for pattern in patterns
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--extract", type=Path)
    parser.add_argument("--match", action="append", default=[], metavar="GLOB")
    arguments = parser.parse_args()
    with DtaArchive(arguments.archive) as archive:
        selected = [
            entry for entry in archive.entries
            if matches(entry.name, arguments.match)
        ]
        if arguments.extract:
            for entry in selected:
                archive.extract(entry, arguments.extract)
        if arguments.json:
            print(json.dumps({
                "archive": str(arguments.archive),
                "kind": archive.kind,
                "version": archive.version,
                "file_count": archive.file_count,
                "selected_count": len(selected),
                "entries": [asdict(entry) for entry in selected],
            }, ensure_ascii=False, indent=2))
        else:
            print(
                f"{archive.kind} {archive.version}: "
                f"{len(selected)}/{archive.file_count} files"
            )
            for entry in selected:
                print(f"{entry.size:>10}  {entry.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
