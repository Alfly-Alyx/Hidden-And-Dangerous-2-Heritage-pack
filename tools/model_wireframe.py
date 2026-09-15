#!/usr/bin/env python3
"""Render simple H&D2 4DS meshes as three SVG or PNG wireframe projections."""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def unpack(self, fmt: str):
        size = struct.calcsize("<" + fmt)
        values = struct.unpack_from("<" + fmt, self.data, self.offset)
        self.offset += size
        return values[0] if len(values) == 1 else values

    def skip(self, size: int) -> None:
        self.offset += size

    def text(self) -> str:
        size = self.unpack("B")
        value = self.data[self.offset:self.offset + size]
        self.offset += size
        return value.decode("cp1252", errors="replace")


def parse(path: Path):
    reader = Reader(path.read_bytes())
    if reader.data[:4] != b"4DS\0":
        raise ValueError("Not a 4DS file")
    reader.skip(4)
    version = reader.unpack("H")
    if version != 41:
        raise ValueError(f"Expected H&D2 version 41, got {version}")
    reader.skip(8)
    material_count = reader.unpack("H")
    for _ in range(material_count):
        flags = reader.unpack("I")
        reader.skip(72)
        has_texture = False
        if flags & (1 << 19):
            reader.skip(4)
            reader.text()
        if flags & (1 << 18):
            has_texture = True
            reader.text()
        if flags & (1 << 30) and not flags & (1 << 24):
            has_texture = True
            reader.text()
        if not has_texture:
            reader.skip(1)
        if flags & (1 << 25) or flags & (1 << 26):
            reader.skip(18)

    node_count = reader.unpack("H")
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    names: list[str] = []
    for _ in range(node_count):
        frame_type = reader.unpack("B")
        visual_type = None
        if frame_type == 1:
            visual_type = reader.unpack("B")
            reader.skip(2)
        reader.skip(2 + 12 + 16 + 12 + 4 + 1)
        names.append(reader.text())
        reader.text()
        if frame_type == 1 and visual_type in (0, 1):
            instance_id = reader.unpack("H")
            if instance_id:
                continue
            lod_count = reader.unpack("B")
            for lod_index in range(lod_count):
                reader.skip(4)
                extra_count = reader.unpack("I")
                vertex_count = reader.unpack("H")
                lod_vertices = []
                for _ in range(vertex_count):
                    point = reader.unpack("3f")
                    reader.skip(20)
                    lod_vertices.append(point)
                reader.skip(extra_count * vertex_count * 4)
                face_group_count = reader.unpack("B")
                lod_faces = []
                for _ in range(face_group_count):
                    face_count = reader.unpack("H")
                    lod_faces.extend(reader.unpack("3H") for _ in range(face_count))
                    reader.skip(2)
                if lod_index == 0:
                    base = len(vertices)
                    vertices.extend(lod_vertices)
                    faces.extend(tuple(base + index for index in face) for face in lod_faces)
        elif frame_type == 2:
            reader.skip(84)
        elif frame_type == 5:
            reader.skip(8)
            vertex_count = reader.unpack("I")
            face_count = reader.unpack("I")
            reader.skip(32)
            base = len(vertices)
            for _ in range(vertex_count):
                point = reader.unpack("3f")
                reader.skip(4)
                vertices.append(point)
            faces.extend(
                tuple(base + index for index in reader.unpack("3H"))
                for _ in range(face_count)
            )
            portal_count = reader.unpack("B")
            for _ in range(portal_count):
                portal_vertices = reader.unpack("B")
                reader.skip(16 + 4 + 4 + 4 + 4 + portal_vertices * 16)
        elif frame_type == 6:
            reader.skip(32)
        elif frame_type == 7:
            reader.skip(2)
            reader.skip(reader.unpack("B") * 2)
        elif frame_type == 10:
            reader.skip(4)
        elif frame_type == 12:
            vertex_count = reader.unpack("I")
            face_count = reader.unpack("I")
            base = len(vertices)
            for _ in range(vertex_count):
                point = reader.unpack("3f")
                reader.skip(4)
                vertices.append(point)
            faces.extend(
                tuple(base + index for index in reader.unpack("3H"))
                for _ in range(face_count)
            )
        else:
            raise ValueError(
                f"Unsupported node type {frame_type} / {visual_type} "
                f"at offset 0x{reader.offset:X}"
            )
    return vertices, faces, names


def projected_points(vertices, axis_a, axis_b, panel_index, panel, margin):
    values_a = [vertex[axis_a] for vertex in vertices]
    values_b = [vertex[axis_b] for vertex in vertices]
    min_a, max_a = min(values_a), max(values_a)
    min_b, max_b = min(values_b), max(values_b)
    scale = (panel - margin * 2) / max(max_a - min_a, max_b - min_b, 1e-6)
    return [
        (
            panel_index * panel + margin + (vertex[axis_a] - min_a) * scale,
            panel - margin - (vertex[axis_b] - min_b) * scale,
        )
        for vertex in vertices
    ]


def projection_svg(vertices, faces, labels):
    projections = ((0, 1, "XY"), (0, 2, "XZ"), (2, 1, "ZY"))
    panel = 500
    margin = 24
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{panel * 3}" height="{panel}">',
        '<rect width="100%" height="100%" fill="#101418"/>',
    ]
    for panel_index, (axis_a, axis_b, label) in enumerate(projections):
        points = projected_points(vertices, axis_a, axis_b, panel_index, panel, margin)
        for face in faces:
            path = " ".join(f"{points[index][0]:.1f},{points[index][1]:.1f}" for index in face)
            chunks.append(f'<polygon points="{path}" fill="none" stroke="#80c8ff" stroke-width="0.45" opacity="0.55"/>')
        chunks.append(f'<text x="{panel_index * panel + 12}" y="20" fill="white" font-family="sans-serif" font-size="15">{label}</text>')
    chunks.append(f'<text x="12" y="{panel - 8}" fill="#ccc" font-family="sans-serif" font-size="12">nodes: {", ".join(labels)}</text>')
    chunks.append("</svg>")
    return "\n".join(chunks)


def projection_png(vertices, faces, labels, output):
    projections = ((0, 1, "XY"), (0, 2, "XZ"), (2, 1, "ZY"))
    panel = 500
    margin = 24
    canvas = Image.new("RGB", (panel * 3, panel), "#101418")
    draw = ImageDraw.Draw(canvas)
    for panel_index, (axis_a, axis_b, label) in enumerate(projections):
        points = projected_points(vertices, axis_a, axis_b, panel_index, panel, margin)
        for face in faces:
            polygon = [points[index] for index in face]
            draw.line(polygon + [polygon[0]], fill="#407898", width=1)
        draw.text((panel_index * panel + 12, 6), label, fill="white")
    draw.text((12, panel - 18), f"nodes: {', '.join(labels)}", fill="#cccccc")
    canvas.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    vertices, faces, names = parse(args.model)
    if args.output.suffix.lower() == ".png":
        projection_png(vertices, faces, names, args.output)
    else:
        args.output.write_text(projection_svg(vertices, faces, names), encoding="utf-8")
    spans = [
        max(vertex[i] for vertex in vertices) - min(vertex[i] for vertex in vertices)
        for i in range(3)
    ]
    print(f"vertices={len(vertices)} faces={len(faces)} spans={spans} nodes={names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())