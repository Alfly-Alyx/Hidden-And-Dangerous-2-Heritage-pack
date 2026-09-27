"""Diagnostic +Z-forward pinhole projection; NOT the native game camera."""
import math

from build_modern_asset import cross, sub, unit
from software_depth import draw_triangles


def clip_near(points, near):
    if type(near) not in (int, float) or not math.isfinite(near) or not .001 <= near <= 1:
        raise ValueError('Invalid diagnostic near plane')
    if len(points) < 3 or any(len(p) != 3 or any(not math.isfinite(v) for v in p) for p in points):
        raise ValueError('Invalid diagnostic polygon')
    result = []
    for a, b in zip(points, points[1:]+points[:1]):
        if a[2] >= near:
            result.append(list(a))
        if (a[2] >= near) != (b[2] >= near):
            t = (near-a[2])/(b[2]-a[2])
            result.append([a[i]+t*(b[i]-a[i]) for i in range(2)]+[near])
    return result


def project(p, width, height, horizontal_fov):
    if (len(p) != 3 or any(not math.isfinite(v) for v in p) or p[2] <= 0
            or any(type(v) is not int or v <= 0 for v in (width, height))
            or type(horizontal_fov) not in (int, float) or not 30 <= horizontal_fov <= 120):
        raise ValueError('Invalid diagnostic projection')
    focal = width/(2*math.tan(math.radians(horizontal_fov)/2))
    # Reciprocal Z is affine in screen space; closer fragments win.
    return width/2+focal*p[0]/p[2], height/2-focal*p[1]/p[2], 1/p[2]


def preview(recipe, meshes, output, title, *, horizontal_fov=90):
    from PIL import Image, ImageDraw
    width, height, near = 960, 600, .03
    project([0, 0, 1], width, height, horizontal_fov)
    picture = Image.new('RGB', (width, height), '#18222c')
    triangles = []
    for mesh in meshes:
        for face in mesh.triangles:
            vertices = [mesh.points[i] for i in face]
            normal = cross(sub(vertices[1], vertices[0]), sub(vertices[2], vertices[0]))
            if sum(v*v for v in normal) < 1e-18:
                continue
            normal = unit(normal)
            light = unit((.6, .9, -.4))
            shade = .38+.62*max(0, sum(a*b for a, b in zip(normal, light)))
            rgb = tuple(round(255*min(1, c*shade)**(1/2.2))
                        for c in recipe['materials'][mesh.material-1]['diffuse'])
            polygon = clip_near(vertices, near)
            for i in range(1, len(polygon)-1):
                triangles.append(([project(p, width, height, horizontal_fov)
                    for p in (polygon[0], polygon[i], polygon[i+1])], rgb))
    draw_triangles(picture, triangles, (0, 0, width, height))
    draw = ImageDraw.Draw(picture)
    draw.line((width/2-8, height/2, width/2+8, height/2), fill='#8295a5')
    draw.line((width/2, height/2-8, width/2, height/2+8), fill='#8295a5')
    draw.rectangle((0, 0, width, 58), fill='#101820')
    draw.text((18, 12), 'PRIVATE / MODERN POSES / '+title, fill='#d2b984')
    draw.text((18, 33), f'DIAGNOSTIC CAMERA / HFOV {horizontal_fov} / NOT NATIVE GAME RENDERING', fill='#b9c5d0')
    picture.save(output)
