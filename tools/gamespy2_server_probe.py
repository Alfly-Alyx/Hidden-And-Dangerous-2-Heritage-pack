#!/usr/bin/env python3
"""Probe the public H&D2 game endpoints with a read-only GameSpy2 query."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import socket
from collections.abc import Iterable


DEFAULT_HOST = "78.47.255.224"
DEFAULT_GAME_PORTS = (11001, 11005, 11009, 11013, 11017, 11021, 11025)
PORT_OFFSETS = (0, 1, 2, 3)
PING = b"HD2P"
# Server details only. Player and team lists are deliberately not requested.
STATUS_QUERY = b"\xfe\xfd\x00" + PING + b"\xff\x00\x00"
PUBLIC_FIELDS = (
    "hostname",
    "hostport",
    "mapname",
    "gametype",
    "gamemode",
    "numplayers",
    "maxplayers",
    "gamever",
    "password",
    "dedicated",
    "isdedicated",
    "expansion",
)


def decode_text(value: bytes) -> str:
    return value.decode("cp1252", errors="replace")


def parse_server_info(payload: bytes) -> tuple[dict[str, str], str | None]:
    expected = b"\x00" + PING
    if not payload.startswith(expected):
        return {}, "response transaction header does not match"

    chunks = payload[len(expected) :].split(b"\x00")
    fields: dict[str, str] = {}
    index = 0
    while index < len(chunks):
        key = chunks[index]
        index += 1
        if not key:
            break
        if index >= len(chunks):
            return fields, "truncated key/value response"
        value = chunks[index]
        index += 1
        fields[decode_text(key)] = decode_text(value)
    return fields, None


def probe_endpoint(host: str, port: int, timeout: float) -> dict[str, object]:
    response = b""
    peer: tuple[str, int] | None = None
    error: str | None = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            udp.settimeout(timeout)
            udp.sendto(STATUS_QUERY, (host, port))
            response, peer = udp.recvfrom(65535)
    except OSError as probe_error:
        error = str(probe_error)

    fields: dict[str, str] = {}
    parse_error: str | None = None
    if response:
        fields, parse_error = parse_server_info(response)
    public = {key: fields[key] for key in PUBLIC_FIELDS if key in fields}
    return {
        "query_port": port,
        "responded": bool(response),
        "valid_gamespy2_response": bool(response) and parse_error is None,
        "peer": f"{peer[0]}:{peer[1]}" if peer else None,
        "response_bytes": len(response),
        "server_info": public,
        "parse_error": parse_error,
        "network_error": error,
    }


def endpoints(game_ports: Iterable[int]) -> list[tuple[int, int]]:
    return [
        (game_port, game_port + offset)
        for game_port in game_ports
        for offset in PORT_OFFSETS
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument(
        "--game-port",
        action="append",
        type=int,
        dest="game_ports",
        help="base game port; repeat to probe several (defaults to RpR's seven)",
    )
    parser.add_argument("--timeout", type=float, default=2.0)
    arguments = parser.parse_args()
    if arguments.timeout <= 0 or arguments.timeout > 10:
        parser.error("--timeout must be greater than 0 and at most 10 seconds")

    game_ports = tuple(arguments.game_ports or DEFAULT_GAME_PORTS)
    targets = endpoints(game_ports)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(
                probe_endpoint,
                arguments.host,
                query_port,
                arguments.timeout,
            ): (game_port, query_port)
            for game_port, query_port in targets
        }
        results = []
        for future in concurrent.futures.as_completed(futures):
            game_port, query_port = futures[future]
            result = future.result()
            result["game_port"] = game_port
            result["query_port"] = query_port
            results.append(result)

    results.sort(key=lambda item: (item["game_port"], item["query_port"]))
    valid = [item for item in results if item["valid_gamespy2_response"]]
    report = {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "host": arguments.host,
        "game_ports": list(game_ports),
        "query_port_offsets": list(PORT_OFFSETS),
        "player_information_requested": False,
        "valid_response_count": len(valid),
        "responsive_game_ports": sorted({item["game_port"] for item in valid}),
        "probes": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
