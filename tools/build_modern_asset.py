#!/usr/bin/env python3
"""Build original, disabled static HD2 meshes without reading game resources.

Restricted procedural recipe -> two LODs, 4DS v41, OBJ/MTL and preview.
This is an asset factory, not an Item/Weapon, animation or installation tool.
Format references are documented in BENELLI_M4_ADDITIVE/MODELE_MODERNE.md.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "experimental/BENELLI_M4_ADDITIVE/modern-world-model.json"
PROVENANCE = "MODERNE"
NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,62}\Z")


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Expected a finite numeric coordinate")
    return float(value)


def vector(value, count=3):
    if not isinstance(value, list) or len(value) != count:
        raise ValueError("Invalid vector")
    return tuple(finite(n) for n in value)


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def unit(v):
    length = math.sqrt(sum(n*n for n in v))
    if length < 1e-10:
        raise ValueError("Degenerate triangle or direction")
    return tuple(n / length for n in v)


@dataclass
class Mesh:
    name: str
    material: int
    points: list
    triangles: list

    def validate(self):
        if not NAME.fullmatch(self.name) or not 3 <= len(self.points) <= 21845:
            raise ValueError("Invalid mesh name or vertex count")
        if not self.triangles or len(self.triangles) > 21845:
            raise ValueError("Invalid face count")
        for p in self.points:
            if len(p) != 3 or any(not math.isfinite(n) or abs(n) > 10 for n in p):
                raise ValueError("Invalid or out-of-scale point")
        for face in self.triangles:
            if len(face) != 3 or any(type(i) is not int or not 0 <= i < len(self.points) for i in face):
                raise ValueError("Face references an invalid point")
            a, b, c = [self.points[i] for i in face]
            unit(cross(sub(b, a), sub(c, a)))

    def expanded(self):
        self.validate()
        # Split every triangle: no ambiguous hard-edge normals or UV seams.
        vertices = []
        for face in self.triangles:
            a, b, c = [self.points[i] for i in face]
            normal = unit(cross(sub(b, a), sub(c, a)))
            vertices.extend((*point, *normal, point[1], point[2]) for point in (a, b, c))
        return vertices


def profile_mesh(part, material):
    """Extrude a strictly convex CCW YZ silhouette through X."""
    shape = [vector(v, 2) for v in part["outline_yz"]]
    width = finite(part["width"])
    center = finite(part.get("center_x", 0))
    if width <= 0 or not 3 <= len(shape) <= 64:
        raise ValueError("Invalid extruded profile")
    for i in range(len(shape)):
        a, b, c = shape[i-2], shape[i-1], shape[i]
        if (b[0]-a[0])*(c[1]-b[1]) - (b[1]-a[1])*(c[0]-b[0]) <= 1e-10:
            raise ValueError("Profile must be strictly convex and counterclockwise")
    n = len(shape)
    points = [(center + x, y, z) for x in (-width/2, width/2) for y, z in shape]
    faces = []
    for i in range(1, n-1):
        faces.extend(((0, i+1, i), (n, n+i, n+i+1)))
    for i in range(n):
        j = (i+1) % n
        faces.extend(((i, j, n+j), (i, n+j, n+i)))
    return Mesh(part["name"], material, points, faces)


def ring_mesh(part, material, low=False):
    count = part["segments"]
    if type(count) is not int or not 6 <= count <= 64:
        raise ValueError("Invalid ring resolution")
    count = max(6, count // 2) if low else count
    sections = [vector(v, 4) for v in part["sections"]]  # Y, X, Z, radius
    if not 2 <= len(sections) <= 32 or any(s[3] <= 0 for s in sections):
        raise ValueError("Invalid ring sections")
    if any(a[0] >= b[0] for a, b in zip(sections, sections[1:])):
        raise ValueError("Ring sections must ascend along Y")
    inner = finite(part.get("inner_ratio", 0))
    if not 0 <= inner < 0.95:
        raise ValueError("Invalid bore proportion")
    points, faces = [], []
    for scale in ((1, inner) if inner else (1,)):
        for y, x, z, radius in sections:
            points.extend((x + radius*scale*math.cos(2*math.pi*i/count), y,
                           z + radius*scale*math.sin(2*math.pi*i/count)) for i in range(count))
    span = len(sections)*count
    surfaces = [(0, False), (span, True)] if inner else [(0, False)]
    for offset, reverse in surfaces:
        for row in range(len(sections)-1):
            for i in range(count):
                a = offset + row*count + i
                b = offset + row*count + (i+1) % count
                pair = ((a, a+count, b+count), (a, b+count, b))
                faces.extend(tuple(reversed(f)) if reverse else f for f in pair)
    for end in (0, len(sections)-1):
        base = end*count
        if inner:
            for i in range(count):
                a, b = base+i, base+(i+1) % count
                pair = ((a, b, b+span), (a, b+span, a+span))
                faces.extend(tuple(reversed(f)) if end else f for f in pair)
        else:
            y, x, z, _ = sections[end]
            middle = len(points)
            points.append((x, y, z))
            for i in range(count):
                face = (middle, base+i, base+(i+1) % count)
                faces.append(tuple(reversed(face)) if end else face)
    return Mesh(part["name"], material, points, faces)


def transform_mesh(mesh, specification):
    """Bake a modern rigid part transform; never introduces skeleton binding."""
    if specification is None:
        return mesh
    if not isinstance(specification,dict) or set(specification)-{'rotation_degrees','translation'}:
        raise ValueError('Unknown modern part transform')
    angles=vector(specification.get('rotation_degrees',[0,0,0]))
    if any(abs(a)>360 for a in angles):raise ValueError('Part rotation outside reviewed domain')
    tx,ty,tz=vector(specification.get('translation',[0,0,0]))
    rx,ry,rz=(math.radians(a) for a in angles)
    sx,cx,sy,cy,sz,cz=math.sin(rx),math.cos(rx),math.sin(ry),math.cos(ry),math.sin(rz),math.cos(rz)
    points=[]
    for x,y,z in mesh.points:
        y,z=cx*y-sx*z,sx*y+cx*z
        x,z=cy*x+sy*z,-sy*x+cy*z
        x,y=cz*x-sz*y,sz*x+cz*y
        points.append((x+tx,y+ty,z+tz))
    return Mesh(mesh.name,mesh.material,points,list(mesh.triangles))


def sweep_mesh(part, material, low=False):
    """Original planar decorative tube; not a physical hose simulation.

    A fixed plane normal gives a twist-free frame, including the closed seam.
    Open paths are capped. The recipe explicitly supplies the plane normal.
    """
    count=part['segments']
    if type(count) is not int or not 6<=count<=64:
        raise ValueError('Invalid sweep resolution')
    count=max(6,count//2) if low else count
    radius=finite(part['radius'])
    closed=part.get('closed',False)
    if type(closed) is not bool or not 0<radius<=1:
        raise ValueError('Invalid sweep radius or closure')
    path=[vector(p) for p in part['path']]
    if not (3 if closed else 2)<=len(path)<=128:
        raise ValueError('Invalid sweep path size')
    normal=unit(vector(part['plane_normal']))
    if any(abs(sum(a*b for a,b in zip(sub(p,path[0]),normal)))>1e-8 for p in path):
        raise ValueError('Sweep path must lie in the declared plane')
    edges=[sub(b,a) for a,b in zip(path,path[1:]+([path[0]] if closed else []))]
    lengths=[math.sqrt(sum(v*v for v in e)) for e in edges]
    if any(length<1e-6 for length in lengths):
        raise ValueError('Sweep contains a repeated or indistinguishable point')
    directions=[unit(e) for e in edges]
    points=[]
    for i,center in enumerate(path):
        previous=directions[(i-1)%len(edges)] if i or closed else directions[0]
        following=directions[i%len(edges)] if closed or i<len(edges) else directions[-1]
        cosine=sum(a*b for a,b in zip(previous,following))
        if cosine<0:
            raise ValueError('Sweep corner exceeds ninety degrees')
        if cosine<1-1e-10:
            available=min(lengths[(i-1)%len(edges)],lengths[i%len(edges)])
            if radius*1.25>=available*math.sqrt((1+cosine)/(1-cosine))/2:
                raise ValueError('Sweep radius too wide for its corner')
        tangent=unit(tuple(a+b for a,b in zip(previous,following)))
        side=unit(cross(normal,tangent))
        for j in range(count):
            angle=2*math.pi*j/count
            points.append(tuple(c+radius*(n*math.cos(angle)+s*math.sin(angle))
                                for c,n,s in zip(center,normal,side)))
    faces=[]
    for i in range(len(edges)):
        first=i*count;second=((i+1)%len(path))*count
        for j in range(count):
            a,b=first+j,first+(j+1)%count
            c,d=second+j,second+(j+1)%count
            faces.extend(((a,c,d),(a,d,b)))
    if not closed:
        for end in (0,len(path)-1):
            middle=len(points);points.append(path[end])
            for j in range(count):
                face=(middle,end*count+j,end*count+(j+1)%count)
                faces.append(tuple(reversed(face)) if end else face)
    return Mesh(part['name'],material,points,faces)


def build_meshes(recipe):
    if (recipe.get("schema_version") != 1 or recipe.get("provenance") != PROVENANCE
            or recipe.get("runtime_status") != "pending" or recipe.get("units") != "metres"
            or not NAME.fullmatch(recipe.get("name", ""))
            or not recipe["name"].startswith("PROTOTYPE_HERITAGE_")):
        raise ValueError("Not an explicitly modern, unvalidated recipe")
    materials = recipe["materials"]
    if not 1 <= len(materials) <= 32:
        raise ValueError("Invalid material count")
    names = set()
    for mat in materials:
        if not NAME.fullmatch(mat["name"]) or mat["name"] in names:
            raise ValueError("Invalid or duplicate material name")
        names.add(mat["name"])
        if any(not 0 <= n <= 1 for n in vector(mat["diffuse"])):
            raise ValueError("Invalid material colour")
    mat_ids = {m["name"]: i+1 for i, m in enumerate(materials)}
    meshes = []
    node_names = set()
    for part in recipe["parts"]:
        if part["name"] in node_names or not NAME.fullmatch(part["name"]):
            raise ValueError("Invalid or duplicate node")
        node_names.add(part["name"])
        if part["material"] not in mat_ids:
            raise ValueError("Unknown material")
        mat = mat_ids[part["material"]]
        if part["kind"] == "profile":
            high = profile_mesh(part, mat)
            low = profile_mesh(part, mat)
        elif part["kind"] == "rings":
            high = ring_mesh(part, mat)
            low = ring_mesh(part, mat, low=True)
        elif part["kind"] == "sweep":
            high = sweep_mesh(part, mat)
            low = sweep_mesh(part, mat, low=True)
        else:
            raise ValueError("Unsupported original geometry primitive")
        high=transform_mesh(high,part.get('transform'))
        low=transform_mesh(low,part.get('transform'))
        high.validate()
        low.validate()
        meshes.append((high, low))
    if not meshes or len(meshes) > 128:
        raise ValueError("Invalid mesh count")
    for anchor in recipe["anchors"]:
        if not NAME.fullmatch(anchor["name"]) or anchor["name"] in node_names:
            raise ValueError("Duplicate or invalid anchor")
        node_names.add(anchor["name"])
        if any(abs(n) > 10 for n in vector(anchor["position"])):
            raise ValueError("Anchor out of scale")
    return meshes


def pack(fmt, *values):
    return struct.pack("<" + fmt, *values)


def counted(value):
    raw = value.encode("ascii")
    if len(raw) > 255:
        raise ValueError("4DS string exceeds byte count")
    return bytes([len(raw)]) + raw


def node_header(name, position=(0, 0, 0), parent=1):
    # All geometry is root-local; identity XYZW quaternion, unit scale.
    return (pack("H3f4f3ffB", parent, *position, 0, 0, 0, 1, 1, 1, 1, 0, 9)
            + counted(name) + counted("MODERNE;Heritage;static;pending"))


def encode_4ds(recipe, meshes):
    # Fixed timestamp, untextured original materials, no external resources.
    data = bytearray(b"4DS\0" + pack("HQH", 41, 0, len(recipe["materials"])))
    for mat in recipe["materials"]:
        diffuse = mat["diffuse"]
        colours = (*[c*0.35 for c in diffuse], 1, *diffuse, 1,
                   0.12, 0.12, 0.12, 1, 0, 0, 0, 1)
        data.extend(pack("I18fB", 1, *colours, 12, 1, 0))
    data.extend(pack("H", 1 + len(meshes) + len(recipe["anchors"])))
    bounds = [[fn(p[i] for high, _ in meshes for p in high.points) for i in range(3)]
              for fn in (min, max)]
    data.extend(b"\x06" + node_header(recipe["name"], parent=0))
    data.extend(pack("3fi3fi", *bounds[0], 0, *bounds[1], 0))
    for levels in meshes:
        data.extend(pack("BBH", 1, 0, 0x1800) + node_header(levels[0].name))
        data.extend(pack("HB", 0, 2))
        # Native meshes put the finite high-detail range first and the terminal
        # zero-range LOD last (checked against the pinned w_garand structure).
        for level, distance in zip(levels, (25, 0)):
            vertices = level.expanded()
            if len(vertices) > 65535:
                raise ValueError("Expanded mesh exceeds uint16 index range")
            data.extend(pack("fIH", distance, 0, len(vertices)))
            for vert in vertices:
                data.extend(pack("8f", *vert))
            data.extend(pack("BH", 1, len(level.triangles)))
            for i in range(0, len(vertices), 3):
                data.extend(pack("3H", i, i+1, i+2))
            data.extend(pack("H", level.material))
    for anchor in recipe["anchors"]:
        data.extend(b"\x06" + node_header(anchor["name"], anchor["position"]))
        data.extend(pack("3fi3fi", -0.002, -0.002, -0.002, 0, 0.002, 0.002, 0.002, 0))
    data.extend(b"\0")  # No companion animation, no implied FPV compatibility.
    return bytes(data)


def encode_obj(recipe, meshes):
    text = ["# MODERNE - original Heritage static geometry; not a playable weapon",
            f"mtllib {recipe['name']}.mtl"]
    index = 1
    for levels in meshes:
        mesh = levels[0]
        text.extend((f"o {mesh.name}", f"usemtl {recipe['materials'][mesh.material-1]['name']}"))
        vertices = mesh.expanded()
        text.extend("v " + " ".join(f"{n:.8f}" for n in v[:3]) for v in vertices)
        text.extend("vn " + " ".join(f"{n:.8f}" for n in v[3:6]) for v in vertices)
        for i in range(0, len(vertices), 3):
            text.append("f " + " ".join(f"{j}//{j}" for j in range(index+i, index+i+3)))
        index += len(vertices)
    materials = ["# MODERNE - colours only; no commercial texture"]
    for mat in recipe["materials"]:
        materials.extend((f"newmtl {mat['name']}", "Kd " + " ".join(map(str, mat["diffuse"])), "d 1", "illum 2"))
    return "\n".join(text) + "\n", "\n".join(materials) + "\n"


def preview(recipe, meshes, output):
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (1600, 900), "#101820")
    draw = ImageDraw.Draw(image)
    draw.text((36, 24), "HERITAGE / MODERNE / MODELE EXTERIEUR EXPERIMENTAL", fill="#d2b984")
    draw.text((36, 49), "Geometrie originale - rendu hors moteur - ni arme jouable, ni animation FPV", fill="#b9c5d0")
    views = [((35, 100, 1530, 420), (0, 1, 0), (0, 0, 1), "PROFIL"),
             ((35, 515, 1000, 330), (0.30, 0.92, -0.24), (-0.12, 0.28, 0.95), "PERSPECTIVE ORTHOGRAPHIQUE"),
             ((1100, 510, 435, 335), (0, 1, 0), (-1, 0, 0), "DESSUS")]
    all_points = [p for high, _ in meshes for p in high.points]
    dot = lambda p, axis: sum(a*b for a, b in zip(p, axis))
    for (left, top, width, height), right, up, title in views:
        right, up = unit(right), unit(up)
        forward = unit(cross(right, up))
        up = cross(forward, right)
        xs, ys = [dot(p, right) for p in all_points], [dot(p, up) for p in all_points]
        scale = min((width-35)/(max(xs)-min(xs)), (height-60)/(max(ys)-min(ys)))
        center_x, center_y = (max(xs)+min(xs))/2, (max(ys)+min(ys))/2
        draw.text((left, top), title, fill="#8295a5")
        triangles = []
        for high, _ in meshes:
            for face in high.triangles:
                p = [high.points[i] for i in face]
                normal = unit(cross(sub(p[1], p[0]), sub(p[2], p[0])))
                shade = 0.38 + 0.62*max(0, dot(normal, unit((0.6, -0.3, 1))))
                rgb = tuple(round(255*min(1, c*shade)**(1/2.2)) for c in recipe["materials"][high.material-1]["diffuse"])
                screen = [(left+width/2+(dot(q, right)-center_x)*scale,
                           top+height/2+18-(dot(q, up)-center_y)*scale) for q in p]
                triangles.append((sum(dot(q, forward) for q in p)/3, screen, rgb))
        for _, points, colour in sorted(triangles, key=lambda item: item[0]):
            draw.polygon(points, fill=colour)
    image.save(output)


def output_directory(root, name):
    if (not isinstance(name,str) or not NAME.fullmatch(name)
            or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',name)):
        raise ValueError("Unsafe output name")
    base = root / ".analysis"
    candidate = base / "modern-assets" / name
    for parent in (root, base, base / "modern-assets", candidate):
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError("Linked output paths are refused")
    if not candidate.resolve().is_relative_to(base.resolve()):
        raise ValueError("Output outside ignored assets directory")
    if candidate.exists():
        raise ValueError("Output already exists; use a fresh name")
    return candidate


def build(recipe, output):
    meshes = build_meshes(recipe)
    data = encode_4ds(recipe, meshes)
    from menu_gui_audit import parse_4ds_nodes
    parsed = parse_4ds_nodes(data)
    if parsed["has_animation"] or parsed["node_count"] != 1+len(meshes)+len(recipe["anchors"]):
        raise ValueError("Generated 4DS failed independent structural parse")
    obj, mtl = encode_obj(recipe, meshes)
    output.mkdir(parents=True, exist_ok=False)
    stem = recipe["name"]
    (output / (stem + ".4ds.disabled")).write_bytes(data)
    (output / (stem + ".obj")).write_text(obj, encoding="utf-8")
    (output / (stem + ".mtl")).write_text(mtl, encoding="utf-8")
    preview(recipe, meshes, output / "preview.png")
    report = {
        "schema_version": 1, "provenance": PROVENANCE, "runtime_status": "pending",
        "recipe_sha256": hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest(),
        "model_sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
        "commercial_assets_read": False, "game_modified": False, "game_launched": False,
        "playable_weapon": False, "animation_binding": False,
        "materials": len(recipe["materials"]), "mesh_nodes": len(meshes),
        "anchors": recipe["anchors"],
        "lod_triangles": [sum(len(pair[i].triangles) for pair in meshes) for i in (0, 1)],
        "bounds": [[min(p[i] for high, _ in meshes for p in high.points) for i in range(3)],
                   [max(p[i] for high, _ in meshes for p in high.points) for i in range(3)]],
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())},
    }
    (output / "MANIFEST.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", type=Path, default=RECIPE)
    parser.add_argument("--output-name", help="Fresh directory below .analysis/modern-assets; otherwise check only")
    args = parser.parse_args()
    recipe = json.loads(args.recipe.read_text(encoding="utf-8"))
    if args.output_name:
        report = build(recipe, output_directory(ROOT, args.output_name))
    else:
        meshes = build_meshes(recipe)
        from menu_gui_audit import parse_4ds_nodes
        parsed = parse_4ds_nodes(encode_4ds(recipe, meshes))
        report = {"provenance": PROVENANCE, "runtime_status": "pending", "nodes": parsed["node_count"],
                  "lod_triangles": [sum(len(p[i].triangles) for p in meshes) for i in (0, 1)], "written": False}
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
