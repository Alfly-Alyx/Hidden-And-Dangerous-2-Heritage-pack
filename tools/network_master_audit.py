#!/usr/bin/env python3
"""Verify the configured H&D2 community master endpoint without launching the game."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import socket
from pathlib import Path

import gamespy_enctypex


EXPECTED_IP = "78.47.255.224"
OPENSPY_IP = "134.122.16.249"
LOCAL_BRIDGE_IP = "127.0.0.1"
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
    decoded_server_count: int | None = None
    codec_roundtrip = False
    if response:
        header_length = (response[0] ^ 0xEC) + 2
        if 2 <= header_length <= len(response):
            key_material_length = response[header_length - 1] ^ 0xEA
            encrypted_payload_offset = header_length + key_material_length
            header_layout_valid = encrypted_payload_offset <= len(response)
    if header_layout_valid:
        try:
            clear = gamespy_enctypex.decrypt(
                bytes(response), b"sK8pQ9", QUERY_VALIDATE
            )
            _, _, servers = gamespy_enctypex.parse_server_list(clear)
            decoded_server_count = len(servers)
            rebuilt = gamespy_enctypex.build_endpoint_response(
                clear, ((server.host, server.port) for server in servers)
            )
            encrypted = gamespy_enctypex.encrypt_with_header(
                bytes(response), rebuilt, b"sK8pQ9", QUERY_VALIDATE
            )
            codec_roundtrip = gamespy_enctypex.decrypt(
                encrypted, b"sK8pQ9", QUERY_VALIDATE
            ) == rebuilt
        except ValueError as decode_error:
            error = str(decode_error)

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
        "decoded_server_count": decoded_server_count,
        "codec_roundtrip": codec_roundtrip,
        "error": error,
    }


def audit(root: Path, timeout: float) -> dict[str, object]:
    config_path = root / "installer" / "Config.cs"
    core_path = root / "installer" / "InstallerCore.cs"
    bridge_installer_path = root / "installer" / "MasterBridgeInstaller.cs"
    bridge_source_path = root / "network-bridge" / "BridgeHost.cs"
    errors: list[str] = []
    try:
        config = config_path.read_text(encoding="utf-8-sig")
        core = core_path.read_text(encoding="utf-8-sig")
        bridge_installer = bridge_installer_path.read_text(encoding="utf-8-sig")
        bridge_source = bridge_source_path.read_text(encoding="utf-8-sig")
    except OSError as error:
        return {
            "ok": False,
            "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "errors": [str(error)],
        }

    config_markers = [
        f'public const string MasterIp = "{EXPECTED_IP}";',
        f'public const string OpenSpyMasterIp = "{OPENSPY_IP}";',
        f'public const string LocalMasterIp = "{LOCAL_BRIDGE_IP}";',
        "ExpectedIpForMasterAlias",
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
        "DescribeInternetFusion",
        "MasterBridgeInstaller.Install(journal, progress)",
        "CanConnect(AppConfig.MasterIp, AppConfig.MasterPort, 3000)",
        "CanConnect(AppConfig.OpenSpyMasterIp, AppConfig.MasterPort, 3000)",
    ]
    missing_core = [marker for marker in core_markers if marker not in core]
    if missing_core:
        errors.append(
            "Installer master wiring changed: " + ", ".join(missing_core)
        )
    bridge_markers = [
        '"78.47.255.224"',
        '"134.122.16.249"',
        "BuildMergedList",
        "HashSet<ServerEndpoint>",
        "IPAddress.Loopback",
    ]
    missing_bridge = [
        marker for marker in bridge_markers if marker not in bridge_source
    ]
    if "HD2CommunityInstaller.MasterBridge.exe" not in bridge_installer:
        missing_bridge.append("embedded bridge installer resource")
    if missing_bridge:
        errors.append("Local master bridge wiring changed: " + ", ".join(missing_bridge))

    aliases: dict[str, object] = {}
    for alias in ALIASES:
        addresses, resolution_error = resolved_ipv4(alias)
        expected = any(
            address in (EXPECTED_IP, LOCAL_BRIDGE_IP) for address in addresses
        )
        aliases[alias] = {
            "ipv4": addresses,
            "expected_endpoint_effective": expected,
            "error": resolution_error,
        }
        if resolution_error:
            errors.append(f"{alias}: {resolution_error}")
        elif not expected:
            errors.append(
                f"{alias}: resolves to {addresses}, expected {EXPECTED_IP} "
                f"or installed bridge {LOCAL_BRIDGE_IP}"
            )

    masters: dict[str, object] = {}
    for name, host in (("community", EXPECTED_IP), ("openspy", OPENSPY_IP)):
        tcp = tcp_probe(host, EXPECTED_PORT, timeout)
        protocol = protocol_probe(host, EXPECTED_PORT, timeout)
        protocol_valid = bool(
            protocol["responded"]
            and protocol["header_layout_valid"]
            and protocol["codec_roundtrip"]
        )
        masters[name] = {
            "host": host,
            "tcp": tcp,
            "hd2_master_query": protocol,
            "protocol_valid": protocol_valid,
        }
        if not tcp["reachable"]:
            errors.append(f"{host}:{EXPECTED_PORT}: {tcp['error']}")
        if not protocol_valid:
            errors.append(
                f"{name} did not return a decodable H&D2 EnctypeX response: "
                f"{protocol['error'] or 'no response'}"
            )

    return {
        "ok": not errors,
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "expected_masters": {
            "community": f"{EXPECTED_IP}:{EXPECTED_PORT}",
            "openspy": f"{OPENSPY_IP}:{EXPECTED_PORT}",
        },
        "installer_configuration": {
            "ip_and_aliases": not missing_config,
            "hosts_and_tcp_wiring": not missing_core and not missing_bridge,
        },
        "aliases": aliases,
        "masters": masters,
        "master_protocol_response_validated": all(
            item["protocol_valid"] for item in masters.values()
        ),
        "in_game_server_list_validated": False,
        "in_game_note": (
            "The audit sends the historical 146-byte H&D2 query to both "
            "services, decodes every current server row and verifies a "
            "decrypt/re-encrypt roundtrip. Displaying the merged response "
            "in game and joining one still require runtime validation."
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
