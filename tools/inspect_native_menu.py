"""Inspect the stock client's menu offline. Never starts or rewrites an EXE."""
from pathlib import Path
import argparse
import hashlib
import sys

import build_static_custom_menu as stock
from capstone import Cs, CS_ARCH_X86, CS_MODE_32


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--range", nargs=2, action="append", metavar=("START", "SIZE"))
    args = parser.parse_args()
    data = (args.game / "HD2_SabreSquadron.exe").read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != stock.EXPECTED_SOURCE_SHA256:
        raise SystemExit("Unsupported stock executable; no files changed.")
    cache = stock.PROJECT / "tmp" / "stock-menu-analysis.bin"
    if cache.exists():
        raw = cache.read_bytes()
    else:
        raw, _ = stock.emulate_unpack(data)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
    dis = Cs(CS_ARCH_X86, CS_MODE_32)
    for start, size in (args.range or []):
        address, length = int(start, 0), int(size, 0)
        offset = address - 0x401000
        for ins in dis.disasm(raw[offset:offset + length], address):
            print(f"{ins.address:08x}: {ins.mnemonic:8s} {ins.op_str}")


if __name__ == "__main__":
    main()
