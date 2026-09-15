#!/usr/bin/env python3
"""Conservative static audit of HD2 objectives and dormant script clues."""
from __future__ import annotations
import argparse, json, re, struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Block:
    kind: int
    start: int
    end: int
    payload: bytes
    children: tuple["Block", ...] = ()

def blocks(data: bytes, start: int, end: int):
    result, cursor = [], start
    while cursor < end:
        if cursor + 6 > end:
            return None
        kind, size = struct.unpack_from("<HI", data, cursor)
        if size < 6 or cursor + size > end:
            return None
        payload_start, block_end = cursor + 6, cursor + size
        nested = blocks(data, payload_start, block_end)
        result.append(Block(kind, cursor, block_end, data[payload_start:block_end], nested or ()))
        cursor = block_end
    return tuple(result) if cursor == end else None

def walk(items):
    for item in items:
        yield item
        yield from walk(item.children)

def direct(block, kind):
    return [child for child in block.children if child.kind == kind]

def catalogue(path: Path):
    data = path.read_bytes()
    root = blocks(data, 0, len(data))
    if root is None:
        raise ValueError(f"Invalid GDT block structure: {path}")
    missions = []
    for node in walk(root):
        if node.kind != 0x32:
            continue
        names = direct(node, 0x36)
        if not names:
            continue
        name = names[0].payload.rstrip(b"\0").decode("cp1252", errors="replace")
        objectives = []
        for index, objective in enumerate(direct(node, 0x28), 1):
            ids = direct(objective, 0x29)
            text_id = struct.unpack_from("<I", ids[0].payload)[0] if ids and len(ids[0].payload) >= 4 else None
            objectives.append({"index": index, "text_id": text_id})
        missions.append({"name": name, "objectives": objectives, "source": str(path)})
    return missions

LINE_COMMENT = re.compile(r"//.*?$", re.MULTILINE)
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
OBJECTIVE = re.compile(r"\bSetObjectiveStatus\s*\(\s*(\d+)\s*,\s*([^\),]+)", re.IGNORECASE)
SIGNAL_IN = re.compile(r"\bOnSignal\s*\(\s*([^\)]+)", re.IGNORECASE)
SIGNAL_OUT = re.compile(r"\bSendSignal\s*\(\s*([^,]+),\s*([^\)]+)", re.IGNORECASE)
SUSPICIOUS = re.compile(r"\b(TODO|FIXME|DOPLNIT|POZDEJI|NOT\s+USED|UNUSED|DISABLED|OLD|TEST)\b", re.IGNORECASE)

def split_comments(text):
    """Separate active source from comments without confusing `//*//` lines.

    Several commercial scripts use `//*//` as a line-comment marker. A pair
    of independent regular expressions sees the embedded `/*` first and can
    incorrectly hide the remainder of the file. This small lexer honours the
    language rule that `/*` inside an existing `//` comment has no meaning.
    """
    active = []
    comments = []
    comment = []
    state = "active"
    quote = None
    index = 0
    while index < len(text):
        char = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "active":
            if quote is not None:
                active.append(char)
                if char == "\\" and following:
                    active.append(following)
                    index += 2
                    continue
                if char == quote:
                    quote = None
            elif char in ('"', "'"):
                quote = char
                active.append(char)
            elif char == "/" and following == "/":
                state = "line"
                comment = [char, following]
                active.extend((" ", " "))
                index += 2
                continue
            elif char == "/" and following == "*":
                state = "block"
                comment = [char, following]
                active.extend((" ", " "))
                index += 2
                continue
            else:
                active.append(char)
        elif state == "line":
            if char in "\r\n":
                comments.append("".join(comment))
                comment = []
                state = "active"
                active.append(char)
            else:
                comment.append(char)
                active.append(" ")
        else:
            comment.append(char)
            if char == "*" and following == "/":
                comment.append(following)
                active.extend((" ", " "))
                comments.append("".join(comment))
                comment = []
                state = "active"
                index += 2
                continue
            active.append(char if char in "\r\n" else " ")
        index += 1
    if comment:
        comments.append("".join(comment))
    return "".join(active), "\n".join(comments)

def effective_scripts(roots):
    effective = {}
    for root in roots:
        scripts_dir = next((p for p in root.iterdir() if p.is_dir() and p.name.casefold() == "scripts"), root)
        for path in scripts_dir.rglob("*.scr"):
            effective[path.relative_to(scripts_dir).as_posix().casefold()] = path
    return effective

def analyze_scripts(files):
    by_dir = defaultdict(lambda: {"active_objectives": Counter(), "commented_objectives": Counter(),
        "signals_in": Counter(), "signals_out": Counter(), "suspicious": []})
    all_suspicious = []
    for relative, path in sorted(files.items()):
        mission = relative.split("/", 1)[0]
        raw = path.read_bytes().decode("cp1252", errors="replace")
        active, comments = split_comments(raw)
        bucket = by_dir[mission]
        for match in OBJECTIVE.finditer(active):
            bucket["active_objectives"][int(match.group(1))] += 1
        for match in OBJECTIVE.finditer(comments):
            bucket["commented_objectives"][int(match.group(1))] += 1
        for match in SIGNAL_IN.finditer(active):
            bucket["signals_in"][match.group(1).strip().casefold()] += 1
        for match in SIGNAL_OUT.finditer(active):
            bucket["signals_out"][match.group(2).strip().casefold()] += 1
        for line_number, line in enumerate(raw.splitlines(), 1):
            if SUSPICIOUS.search(line):
                finding = {"file": relative, "line": line_number, "text": line.strip()[:240]}
                bucket["suspicious"].append(finding)
                all_suspicious.append(finding)
    return by_dir, all_suspicious

def mission_candidates(catalogues, scripts):
    result, script_dirs = [], list(scripts)
    for mission in catalogues:
        name = mission["name"].casefold()
        # GDT entries describe the single-player mission. Do not mix the
        # similarly named _mp/_obj directories into its objective calls.
        matching = [key for key in script_dirs if key == name]
        active, commented, suspicious = Counter(), Counter(), []
        for key in matching:
            active.update(scripts[key]["active_objectives"])
            commented.update(scripts[key]["commented_objectives"])
            suspicious.extend(scripts[key]["suspicious"])
        declared = [item["index"] for item in mission["objectives"]]
        missing = [index for index in declared if not active[index]]
        by_index = {item["index"]: item for item in mission["objectives"]}
        active_text_ids = {
            by_index[index]["text_id"] for index in declared
            if active[index] and by_index[index]["text_id"] is not None
        }
        duplicate_text_missing = [
            index for index in missing
            if by_index[index]["text_id"] in active_text_ids
        ]
        result.append({"mission": mission["name"], "declared": len(declared),
            "objectives": mission["objectives"], "script_dirs": matching,
            "active_indices": sorted(active), "missing_indices": missing,
            "commented_only_indices": [index for index in missing if commented[index]],
            "missing_duplicate_text_indices": duplicate_text_missing,
            "suspicious_lines": suspicious, "source": mission["source"]})
    return result

def serialize_scripts(value):
    return {key: {"active_objectives": dict(sorted(bucket["active_objectives"].items())),
        "commented_objectives": dict(sorted(bucket["commented_objectives"].items())),
        "signals_in": dict(sorted(bucket["signals_in"].items())),
        "signals_out": dict(sorted(bucket["signals_out"].items())),
        "suspicious": bucket["suspicious"]} for key, bucket in value.items()}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gdt", action="append", type=Path, required=True)
    parser.add_argument("--scripts", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cats = [mission for path in args.gdt for mission in catalogue(path)]
    effective = effective_scripts(args.scripts)
    script_audit, suspicious = analyze_scripts(effective)
    report = {"catalogue_missions": len(cats), "effective_scripts": len(effective),
        "missions": mission_candidates(cats, script_audit), "suspicious_lines": suspicious,
        "script_directories": serialize_scripts(script_audit)}
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
