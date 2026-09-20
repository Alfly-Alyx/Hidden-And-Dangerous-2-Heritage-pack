#!/usr/bin/env python3
"""Small GameSpy enctypeX decoder used by the H&D2 network audits.

The algorithm follows Luigi Auriemma's GPL-2.0-or-later
``enctypex_decoder.c`` (2008-2012).  This Python port is distributed under
the H&D2 Heritage Pack's GPL-3.0-or-later licence.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ServerEntry:
    host: str
    port: int
    fields: dict[str, str]


def _func5(
    key_state: bytearray,
    count: int,
    identity: bytearray,
    n1: int,
    n2: int,
) -> tuple[int, int, int]:
    if count == 0:
        return 0, n1, n2
    mask = 1
    if count > 1:
        while mask < count:
            mask = (mask << 1) + 1
    attempts = 0
    while True:
        n1 = key_state[n1 & 0xFF] + identity[n2]
        n2 += 1
        if n2 >= len(identity):
            n2 = 0
            n1 += len(identity)
        result = n1 & mask
        attempts += 1
        if attempts > 11:
            result %= count
        if result <= count:
            return result, n1, n2


def _func4(identity: bytearray) -> bytearray:
    if not identity:
        raise ValueError("empty enctypeX identity")
    state = bytearray(range(256)) + bytearray(5)
    n1 = 0
    n2 = 0
    for index in range(255, -1, -1):
        target, n1, n2 = _func5(state, index, identity, n1, n2)
        state[index], state[target] = state[target], state[index]
    state[256] = state[1]
    state[257] = state[3]
    state[258] = state[5]
    state[259] = state[7]
    state[260] = state[n1 & 0xFF]
    return state


def _decrypt_byte(state: bytearray, encrypted: int) -> int:
    rotor = state[256]
    ratchet = (state[257] + state[rotor]) & 0xFF
    rotor = (rotor + 1) & 0xFF
    avalanche = state[258]
    last_plain = state[259]
    last_cipher = state[260]

    swap = state[last_cipher]
    state[last_cipher] = state[ratchet]
    state[ratchet] = state[last_plain]
    state[last_plain] = state[rotor]
    state[rotor] = swap
    avalanche = (avalanche + state[swap]) & 0xFF

    clear = encrypted ^ state[
        (state[avalanche] + state[rotor]) & 0xFF
    ] ^ state[
        state[
            (state[last_plain] + state[last_cipher] + state[ratchet]) & 0xFF
        ]
    ]
    state[256] = rotor
    state[257] = ratchet
    state[258] = avalanche
    state[259] = clear
    state[260] = encrypted
    return clear


def _encrypt_byte(state: bytearray, clear: int) -> int:
    """Encrypt one byte with the inverse of :func:`_decrypt_byte`."""
    rotor = state[256]
    ratchet = (state[257] + state[rotor]) & 0xFF
    rotor = (rotor + 1) & 0xFF
    avalanche = state[258]
    last_plain = state[259]
    last_cipher = state[260]

    swap = state[last_cipher]
    state[last_cipher] = state[ratchet]
    state[ratchet] = state[last_plain]
    state[last_plain] = state[rotor]
    state[rotor] = swap
    avalanche = (avalanche + state[swap]) & 0xFF

    encrypted = clear ^ state[
        (state[avalanche] + state[rotor]) & 0xFF
    ] ^ state[
        state[
            (state[last_plain] + state[last_cipher] + state[ratchet]) & 0xFF
        ]
    ]
    state[256] = rotor
    state[257] = ratchet
    state[258] = avalanche
    state[259] = clear
    state[260] = encrypted
    return encrypted


def _crypt_parts(
    payload: bytes, game_key: bytes, validate: bytes
) -> tuple[bytes, bytearray, int]:
    if len(validate) != 8:
        raise ValueError("the enctypeX validation token must contain eight bytes")
    if not game_key:
        raise ValueError("the GameSpy game key is empty")
    if not payload:
        raise ValueError("the enctypeX response is empty")

    header_length = (payload[0] ^ 0xEC) + 2
    if header_length > len(payload):
        raise ValueError("truncated enctypeX crypt header")
    challenge_length = payload[header_length - 1] ^ 0xEA
    encrypted_offset = header_length + challenge_length
    if encrypted_offset > len(payload):
        raise ValueError("truncated enctypeX server challenge")

    identity = bytearray(validate)
    challenge = payload[header_length:encrypted_offset]
    for index, value in enumerate(challenge):
        slot = (game_key[index % len(game_key)] * index) & 7
        identity[slot] ^= identity[index & 7] ^ value
    return payload[:encrypted_offset], _func4(identity), encrypted_offset


def decrypt(payload: bytes, game_key: bytes, validate: bytes) -> bytes:
    """Decrypt one complete enctypeX response and remove its crypt header."""
    _, state, encrypted_offset = _crypt_parts(payload, game_key, validate)
    return bytes(_decrypt_byte(state, value) for value in payload[encrypted_offset:])


def encrypt_with_header(
    template_response: bytes,
    clear_payload: bytes,
    game_key: bytes,
    validate: bytes,
) -> bytes:
    """Encrypt a clear response using a master's existing crypt header."""
    header, state, _ = _crypt_parts(template_response, game_key, validate)
    encrypted = bytes(_encrypt_byte(state, value) for value in clear_payload)
    return header + encrypted


def _read_nts(data: bytes, offset: int) -> tuple[str, int]:
    end = data.find(b"\x00", offset)
    if end < 0:
        raise ValueError("unterminated enctypeX string")
    return data[offset:end].decode("cp1252", errors="replace"), end + 1


def _server_table_end(data: bytes) -> int:
    if len(data) < 7:
        raise ValueError("truncated enctypeX server list")
    offset = 6
    field_count = data[offset]
    offset += 1
    for _ in range(field_count):
        if offset >= len(data):
            raise ValueError("truncated enctypeX field table")
        offset += 1
        _, offset = _read_nts(data, offset)
    if offset >= len(data):
        raise ValueError("truncated enctypeX popular-value table")
    popular_count = data[offset]
    offset += 1
    for _ in range(popular_count):
        _, offset = _read_nts(data, offset)
    return offset


def build_endpoint_response(
    template_clear: bytes, endpoints: Iterable[tuple[str, int]]
) -> bytes:
    """Build a V2 list using the template's client and field tables.

    Every endpoint carries an explicit query port, so lists obtained from
    masters with different default ports can safely be combined.
    """
    table_end = _server_table_end(template_clear)
    result = bytearray(template_clear[:table_end])
    unique = sorted(
        {(str(ipaddress.IPv4Address(host)), int(port)) for host, port in endpoints},
        key=lambda item: (int(ipaddress.IPv4Address(item[0])), item[1]),
    )
    for host, port in unique:
        if port < 1 or port > 65535:
            raise ValueError(f"invalid GameSpy query port: {port}")
        result.append(0x10)
        result.extend(ipaddress.IPv4Address(host).packed)
        result.extend(port.to_bytes(2, "big"))
    result.extend(b"\x00\xff\xff\xff\xff")
    return bytes(result)


def parse_server_list(data: bytes) -> tuple[str, int, list[ServerEntry]]:
    """Parse a decrypted V2 server-list response."""
    if len(data) < 7:
        raise ValueError("truncated enctypeX server list")
    client_ip = str(ipaddress.IPv4Address(data[0:4]))
    default_port = int.from_bytes(data[4:6], "big")
    offset = 6

    field_count = data[offset]
    offset += 1
    fields: list[tuple[int, str]] = []
    for _ in range(field_count):
        if offset >= len(data):
            raise ValueError("truncated enctypeX field table")
        field_type = data[offset]
        offset += 1
        name, offset = _read_nts(data, offset)
        fields.append((field_type, name))

    if offset >= len(data):
        raise ValueError("truncated enctypeX popular-value table")
    popular_count = data[offset]
    offset += 1
    popular: list[str] = []
    for _ in range(popular_count):
        value, offset = _read_nts(data, offset)
        popular.append(value)

    servers: list[ServerEntry] = []
    while offset < len(data):
        flags = data[offset]
        offset += 1
        if flags == 0 and data[offset : offset + 4] == b"\xff\xff\xff\xff":
            return client_ip, default_port, servers

        address_length = 5
        if flags & 0x02:
            address_length = 9
        if flags & 0x08:
            address_length += 4
        if flags & 0x10:
            address_length += 2
        if flags & 0x20:
            address_length += 2
        address_data_length = address_length - 1
        if offset + address_data_length > len(data):
            raise ValueError("truncated enctypeX server address")
        address_data = data[offset : offset + address_data_length]
        host = str(ipaddress.IPv4Address(address_data[0:4]))
        port = (
            int.from_bytes(address_data[4:6], "big")
            if flags & 0x10
            else default_port
        )
        offset += address_data_length

        values: dict[str, str] = {}
        if flags & 0x40:
            for field_type, name in fields:
                if offset >= len(data):
                    raise ValueError("truncated enctypeX server fields")
                marker = data[offset]
                offset += 1
                if field_type == 0:
                    if marker == 0xFF:
                        value, offset = _read_nts(data, offset)
                    elif marker < len(popular):
                        value = popular[marker]
                    else:
                        value = ""
                else:
                    value = str(marker if marker < 128 else marker - 256)
                values[name] = value
        servers.append(ServerEntry(host=host, port=port, fields=values))

    raise ValueError("enctypeX terminator missing")
