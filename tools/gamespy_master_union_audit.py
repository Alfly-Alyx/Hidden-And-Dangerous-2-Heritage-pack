#!/usr/bin/env python3
"""Compare and merge the two public H&D2 GameSpy-compatible master lists."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import socket

import gamespy_enctypex
import network_master_audit


GAME_KEY = b"sK8pQ9"
MASTERS = {
    "community": "78.47.255.224",
    "openspy": "134.122.16.249",
}


def query_master(host: str, timeout: float) -> dict[str, object]:
    response = bytearray()
    error: str | None = None
    try:
        with socket.create_connection(
            (host, network_master_audit.EXPECTED_PORT), timeout=timeout
        ) as stream:
            stream.settimeout(timeout)
            stream.sendall(network_master_audit.MASTER_QUERY)
            while len(response) < 1024 * 1024:
                try:
                    chunk = stream.recv(65536)
                except TimeoutError:
                    break
                if not chunk:
                    break
                response.extend(chunk)
                try:
                    clear = gamespy_enctypex.decrypt(
                        bytes(response),
                        GAME_KEY,
                        network_master_audit.QUERY_VALIDATE,
                    )
                    _, _, entries = gamespy_enctypex.parse_server_list(clear)
                    break
                except ValueError:
                    continue
    except OSError as query_error:
        error = str(query_error)

    entries: list[gamespy_enctypex.ServerEntry] = []
    client_ip: str | None = None
    default_port: int | None = None
    decode_error: str | None = None
    codec_roundtrip = False
    if response:
        try:
            clear = gamespy_enctypex.decrypt(
                bytes(response),
                GAME_KEY,
                network_master_audit.QUERY_VALIDATE,
            )
            client_ip, default_port, entries = (
                gamespy_enctypex.parse_server_list(clear)
            )
            rebuilt = gamespy_enctypex.build_endpoint_response(
                clear, ((entry.host, entry.port) for entry in entries)
            )
            encoded = gamespy_enctypex.encrypt_with_header(
                bytes(response), rebuilt, GAME_KEY,
                network_master_audit.QUERY_VALIDATE,
            )
            codec_roundtrip = gamespy_enctypex.decrypt(
                encoded, GAME_KEY, network_master_audit.QUERY_VALIDATE
            ) == rebuilt
        except ValueError as parser_error:
            decode_error = str(parser_error)

    return {
        "host": host,
        "response_bytes": len(response),
        "client_ip": client_ip,
        "default_query_port": default_port,
        "servers": [
            {
                "host": entry.host,
                "query_port": entry.port,
                "fields": entry.fields,
            }
            for entry in entries
        ],
        "codec_roundtrip": codec_roundtrip,
        "error": error or decode_error,
    }


def audit(timeout: float) -> dict[str, object]:
    results = {
        name: query_master(host, timeout) for name, host in MASTERS.items()
    }
    endpoints = {
        name: {
            (server["host"], server["query_port"])
            for server in result["servers"]
        }
        for name, result in results.items()
    }
    union = endpoints["community"] | endpoints["openspy"]
    overlap = endpoints["community"] & endpoints["openspy"]
    return {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "masters": results,
        "counts": {
            "community": len(endpoints["community"]),
            "openspy": len(endpoints["openspy"]),
            "overlap": len(overlap),
            "union": len(union),
        },
        "overlap": [f"{host}:{port}" for host, port in sorted(overlap)],
        "union": [f"{host}:{port}" for host, port in sorted(union)],
        "ok": all(
            result["error"] is None and result["codec_roundtrip"]
            for result in results.values()
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=5.0)
    arguments = parser.parse_args()
    if arguments.timeout <= 0 or arguments.timeout > 30:
        parser.error("--timeout must be greater than 0 and at most 30 seconds")
    report = audit(arguments.timeout)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
