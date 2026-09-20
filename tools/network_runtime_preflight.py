#!/usr/bin/env python3
"""Check every local and remote prerequisite before the H&D2 visual network test."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
from pathlib import Path

import gamespy2_server_probe
import network_master_audit


WIDESCREEN_FILES = {
    "d3d8.dll": "A07F2B90B0EA9CFFB568218E500EA3280B750C195E83D82A6BB7A252642708E3",
    "Maps/2e_camra.tga": "43B609F80497959D1127B2A7F3F0FCAAEA1322A8BD9F770ECEEEC4146D2D1EF0",
    "Maps/2e_scope.tga": "8E6E892F11B710F395853EA97CA4D09337FF4842AF543986941A59ADF90738E1",
    "Maps/e_zamer.tga": "0D86A937580805EBFE1F932F218E6407ACB4D7DC365A34C0C50385A7522F6FD7",
    "Scripts/HiddenandDangerous2.WidescreenFix.asi": "8375F31A2A1F6C6B401AF40BB4F8C741FD3BA90B36B14603176FB71465D62768",
    "Scripts/HiddenandDangerous2.WidescreenFix.ini": "337A157743D015644EA7DB069C5BDE05D4084C511730F480237B96146D96E701",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def hosts_state(path: Path) -> dict[str, object]:
    mappings: dict[str, list[str]] = {
        alias: [] for alias in network_master_audit.ALIASES
    }
    error: str | None = None
    try:
        for raw_line in path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            line = raw_line.split("#", 1)[0].strip()
            fields = line.split()
            if len(fields) < 2:
                continue
            address = fields[0]
            for name in fields[1:]:
                key = name.casefold()
                if key in mappings:
                    mappings[key].append(address)
    except OSError as hosts_error:
        error = str(hosts_error)
    exact = {
        alias: addresses == [
            (
                network_master_audit.LOCAL_BRIDGE_IP
                if alias == "hd2.ms14.gamespy.com"
                else network_master_audit.EXPECTED_IP
            )
        ]
        for alias, addresses in mappings.items()
    }
    return {
        "path": str(path),
        "mappings": mappings,
        "exact": exact,
        "all_exact": all(exact.values()),
        "error": error,
    }


def widescreen_state(game: Path) -> dict[str, object]:
    files: dict[str, object] = {}
    for relative, expected in WIDESCREEN_FILES.items():
        path = game / Path(relative)
        actual = sha256(path) if path.is_file() else None
        files[relative] = {
            "present": path.is_file(),
            "sha256": actual,
            "expected_sha256": expected,
            "exact": actual == expected,
        }
    return {
        "exact_files": sum(
            1 for item in files.values() if item["exact"]
        ),
        "expected_files": len(WIDESCREEN_FILES),
        "all_exact": all(item["exact"] for item in files.values()),
        "files": files,
    }


def widescreen_source_sync(root: Path) -> dict[str, object]:
    source_path = root / "installer" / "WidescreenInstaller.cs"
    try:
        source = source_path.read_text(encoding="utf-8-sig")
    except OSError as source_error:
        return {
            "path": str(source_path),
            "synchronized": False,
            "missing_markers": [],
            "error": str(source_error),
        }
    folded_source = source.casefold()
    missing = [
        f"{relative}={expected}"
        for relative, expected in WIDESCREEN_FILES.items()
        if (
            relative.casefold() not in folded_source
            and relative.replace("/", "\\").casefold() not in folded_source
        )
        or expected.casefold() not in folded_source
    ]
    return {
        "path": str(source_path),
        "synchronized": not missing,
        "missing_markers": missing,
        "error": None,
    }


def directplay_state() -> dict[str, object]:
    command = (
        "$feature=Get-CimInstance -ClassName Win32_OptionalFeature "
        "-Filter \"Name='DirectPlay'\"; "
        "if($null -eq $feature){'MISSING'}else{$feature.InstallState}"
    )
    try:
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = completed.stdout.strip()
        error = completed.stderr.strip() or None
        install_state = int(output) if output.isdigit() else None
        return {
            "install_state": install_state,
            "enabled": install_state == 1,
            "error": error,
        }
    except (OSError, subprocess.SubprocessError) as directplay_error:
        return {
            "install_state": None,
            "enabled": False,
            "error": str(directplay_error),
        }


def public_servers(timeout: float) -> dict[str, object]:
    targets = [
        (port, port + 3) for port in gamespy2_server_probe.DEFAULT_GAME_PORTS
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(
                gamespy2_server_probe.probe_endpoint,
                gamespy2_server_probe.DEFAULT_HOST,
                query_port,
                timeout,
            ): game_port
            for game_port, query_port in targets
        }
        results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            result["game_port"] = futures[future]
            results.append(result)
    results.sort(key=lambda item: item["game_port"])
    valid = [item for item in results if item["valid_gamespy2_response"]]
    return {
        "expected": len(targets),
        "valid": len(valid),
        "all_valid": len(valid) == len(targets),
        "player_information_requested": False,
        "servers": results,
    }


def default_hosts_path() -> Path:
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    return windows / "System32" / "drivers" / "etc" / "hosts"


def audit(root: Path, game: Path, hosts: Path, timeout: float) -> dict[str, object]:
    master = network_master_audit.audit(root, timeout)
    local_bridge = network_master_audit.protocol_probe(
        network_master_audit.LOCAL_BRIDGE_IP,
        network_master_audit.EXPECTED_PORT,
        timeout,
    )
    local_hosts = hosts_state(hosts)
    widescreen = widescreen_state(game)
    widescreen_sync = widescreen_source_sync(root)
    directplay = directplay_state()
    servers = public_servers(timeout)
    game_executable = game / "HD2_SabreSquadron.exe"
    prerequisites = {
        "game_executable": game_executable.is_file(),
        "hosts": local_hosts["all_exact"],
        "directplay": directplay["enabled"],
        "widescreen": widescreen["all_exact"],
        "widescreen_manifest_sync": widescreen_sync["synchronized"],
        "master": master["ok"],
        "local_bridge": bool(
            local_bridge["responded"]
            and local_bridge["header_layout_valid"]
            and local_bridge["codec_roundtrip"]
        ),
        "seven_public_servers": servers["all_valid"],
    }
    return {
        "ok": all(prerequisites.values()),
        "game": str(game),
        "prerequisites": prerequisites,
        "hosts": local_hosts,
        "directplay": directplay,
        "widescreen": widescreen,
        "widescreen_manifest_sync": widescreen_sync,
        "master": master,
        "local_bridge": local_bridge,
        "public_servers": servers,
        "ready_for_visual_game_test": all(prerequisites.values()),
        "in_game_server_list_validated": False,
        "server_join_validated": False,
        "note": (
            "Passing this preflight proves the prerequisites only. The Internet "
            "list and an actual player join still require an in-game test."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--hosts", type=Path, default=default_hosts_path())
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    if arguments.timeout <= 0 or arguments.timeout > 10:
        parser.error("--timeout must be greater than 0 and at most 10 seconds")
    report = audit(
        arguments.root.resolve(),
        arguments.game.resolve(),
        arguments.hosts.resolve(),
        arguments.timeout,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
