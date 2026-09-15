#!/usr/bin/env python3
"""Verify the configured H&D2 community master endpoint without launching the game."""

from __future__ import annotations

import argparse
import datetime as dt
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
        "in_game_server_list_validated": False,
        "in_game_note": (
            "The Internet list and a full join still require the runtime "
            "validation register."
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
