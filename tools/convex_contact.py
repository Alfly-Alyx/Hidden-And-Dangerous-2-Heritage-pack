"""Convex closed-mesh interior distances; no claim of full hand collision.

Inside depth is the minimum distance to a supporting plane. Outside returns
zero. Callers must separately check face crossings and contact coverage.
"""
from collections import Counter
import math


def vector(row):
    if (not isinstance(row, (list, tuple)) or len(row) != 3
            or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>10 for v in row)):
        raise ValueError('Expected finite bounded contact point')
    return tuple(row)


def dot(a,b): return sum(x*y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))


def planes(points, triangles):
    if not isinstance(points,(list,tuple)) or not 4 <= len(points) <= 4096:
        raise ValueError('Unreviewed convex contact mesh')
    points = [vector(p) for p in points]
    if not isinstance(triangles,(list,tuple)) or not 4 <= len(triangles) <= 4096:
        raise ValueError('Unreviewed convex face count')
    unique = set(points)
    center = tuple(sum(p[i] for p in unique)/len(unique) for i in range(3))
    edges, result = Counter(), []
    for triangle in triangles:
        if (not isinstance(triangle,(list,tuple)) or len(triangle)!=3
                or any(type(i) is not int or not 0<=i<len(points) for i in triangle)):
            raise ValueError('Invalid contact triangle')
        a,b,c = [points[i] for i in triangle]
        u,v = sub(b,a),sub(c,a)
        normal = (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        length = math.sqrt(dot(normal,normal))
        if length < 1e-12: raise ValueError('Degenerate convex contact face')
        normal = tuple(x/length for x in normal)
        if dot(normal,sub(center,a)) > 0: normal = tuple(-x for x in normal)
        offset = dot(normal,a)
        if dot(normal,center)-offset > -1e-8:
            raise ValueError('Flat or open contact volume')
        if max(dot(normal,p)-offset for p in unique) > 2e-7:
            raise ValueError('Nonconvex contact volume')
        for x,y in ((a,b),(b,c),(c,a)): edges[tuple(sorted((x,y)))] += 1
        result.append((normal,offset))
    if any(count != 2 for count in edges.values()):
        raise ValueError('Contact surface is not closed')
    return result


def penetration(point, support):
    point = vector(point)
    if not support: raise ValueError('Missing contact planes')
    return max(0.0, min(offset-dot(normal,point) for normal,offset in support))


def measure(points, support, tolerance=1e-5):
    if type(tolerance) not in (int,float) or not math.isfinite(tolerance) or not 0<=tolerance<=.01:
        raise ValueError('Invalid contact tolerance')
    depths = [penetration(point,support) for point in points]
    return {'samples':len(depths), 'inside':sum(d>tolerance for d in depths),
            'max_depth':max(depths,default=0), 'sum_depth':sum(depths),
            'surface_crossings_checked':False, 'full_contact_qualified':False}
