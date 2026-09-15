#!/usr/bin/env python3
"""Verify the configured H&D2 community master endpoint without launching the game."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import socket
from pathlib import Path


EXPECTED_IP = "78.47.255.224"
EXPECTED_PORT = 28910
ALIASES = (
    "hd2.available.gamespy.com",
    "hd2.master.gamespy.com",
    "hd2.ms14.gamespy.com",
)
QUERY_VALIDATE = b"Ghfg0Vhq"
QUERY_FIELDS = (
    b"\\hostname\\gamemode\\gametype\\mapname\\numplayers\\maxplayers"
    b"\\hostport\\isdedicated\\gamever\\password\\voicechat\\expansion"
)
QUERY_BODY = (
    b"\x00\x01\x03\x01\x00\x00\x00hd2\x00hd2\x00"
    + QUERY_VALIDATE
    + b"\x00"
    + QUERY_FIELDS
    + b"\x00\x00\x00\x00\x00"
)
MASTER_QUERY = (len(QUERY_BODY) + 2).to_bytes(2, "big") + QUERY_BODY


def resolved_ipv4(alias: str) -> tuple[list[str], str | None]:
    try:
        results = socket.getaddrinfo(
            alias,
            None,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
    except OSError as error:
        return [], str(error)
    return sorted({result[4][0] for result in results}), None


def tcp_probe(host: str, port: int, timeout: float) -> dict[str, object]:
    try:
        with socket.create_connection((host, port), timeout=timeout) as stream:
            peer = stream.getpeername()
        return {
            "reachable": True,
            "peer": f"{peer[0]}:{peer[1]}",
            "error": None,
        }
    except OSError as error:
        return {
            "reachable": False,
            "peer": None,
            "error": str(error),
        }


def protocol_probe(host: str, port: int, timeout: float) -> dict[str, object]:
    response = bytearray()
    peer: str | None = None
    error: str | None = None
    try:
        with socket.create_connection((host, port), timeout=timeout) as stream:
            stream.settimeout(timeout)
            endpoint = stream.getpeername()
            peer = f"{endpoint[0]}:{endpoint[1]}"
            stream.sendall(MASTER_QUERY)
            while len(response) < 65536:
                try:
                    chunk = stream.recv(4096)
                except TimeoutError:
                    break
                if not chunk:
                    break
                response.extend(chunk)
    except OSError as protocol_error:
        error = str(protocol_error)

    header_length: int | None = None
    key_material_length: int | None = None
    encrypted_payload_offset: int | None = None
    header_layout_valid = False
    if response:
        header_length = (response[0] ^ 0xEC) + 2
        if 2 <= header_length <= len(response):
            key_material_length = response[header_length - 1] ^ 0xEA
            encrypted_payload_offset = header_length + key_material_length
            header_layout_valid = encrypted_payload_offset <= len(response)

    return {
        "responded": bool(response),
        "peer": peer,
        "request_bytes": len(MASTER_QUERY),
        "request_sha256": hashlib.sha256(MASTER_QUERY).hexdigest().upper(),
        "response_bytes": len(response),
        "response_sha256": (
            hashlib.sha256(response).hexdigest().upper() if response else None
        ),
        "enctypex_header_length": header_length,
        "enctypex_key_material_length": key_material_length,
        "encrypted_payload_offset": encrypted_payload_offset,
        "header_layout_valid": header_layout_valid,
        "decoded_server_count": None,
        "error": error,
    }


def audit(root: Path, timeout: float) -> dict[str, object]:
    config_path = root / "installer" / "Config.cs"
    core_path = root / "installer" / "InstallerCore.cs"
    errors: list[str] = []
    try:
        config = config_path.read_text(encoding="utf-8-sig")
        core = core_path.read_text(encoding="utf-8-sig")
    except OSError as error:
        return {
            "ok": False,
            "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "errors": [str(error)],
        }

    config_markers = [
        f'public const string MasterIp = "{EXPECTED_IP}";',
        *(f'"{alias}"' for alias in ALIASES),
    ]
    missing_config = [
        marker for marker in config_markers if marker not in config
    ]
    if missing_config:
        errors.append(
            "Installer master configuration changed: "
            + ", ".join(missing_config)
        )
    core_markers = [
        "ConfigureMasterServer",
        "DescribeHosts",
        f"CanConnect(AppConfig.MasterIp, {EXPECTED_PORT}, 3000)",
    ]
    missing_core = [marker for marker in core_markers if marker not in core]
    if missing_core:
        errors.append(
            "Installer master wiring changed: " + ", ".join(missing_core)
        )

    aliases: dict[str, object] = {}
    for alias in ALIASES:
        addresses, resolution_error = resolved_ipv4(alias)
        expected = EXPECTED_IP in addresses
        aliases[alias] = {
            "ipv4": addresses,
            "expected_ip_effective": expected,
            "error": resolution_error,
        }
        if resolution_error:
            errors.append(f"{alias}: {resolution_error}")
        elif not expected:
            errors.append(
                f"{alias}: resolves to {addresses}, expected {EXPECTED_IP}"
            )

    tcp = tcp_probe(EXPECTED_IP, EXPECTED_PORT, timeout)
    if not tcp["reachable"]:
        errors.append(
            f"{EXPECTED_IP}:{EXPECTED_PORT}: {tcp['error']}"
        )

    protocol = protocol_probe(ALIASES[-1], EXPECTED_PORT, timeout)
    protocol_valid = (
        protocol["responded"] and protocol["header_layout_valid"]
    )
    if not protocol_valid:
        errors.append(
            "The master accepted TCP but did not return a structurally valid "
            f"H&D2 EncTypeX response: {protocol['error'] or 'no response'}"
        )

    return {
        "ok": not errors,
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "expected_master": f"{EXPECTED_IP}:{EXPECTED_PORT}",
        "installer_configuration": {
            "ip_and_aliases": not missing_config,
            "hosts_and_tcp_wiring": not missing_core,
        },
        "aliases": aliases,
        "tcp": tcp,
        "hd2_master_query": protocol,
        "master_protocol_response_validated": protocol_valid,
        "in_game_server_list_validated": False,
        "in_game_note": (
            "The audit sends the historical 146-byte H&D2 query and verifies "
            "the encrypted response envelope only. Decrypting the current "
            "server rows, displaying them in game and joining one still "
            "require runtime validation."
        ),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    if arguments.timeout <= 0 or arguments.timeout > 30:
        parser.error("--timeout must be greater than 0 and at most 30 seconds")

    report = audit(arguments.root.resolve(), arguments.timeout)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
