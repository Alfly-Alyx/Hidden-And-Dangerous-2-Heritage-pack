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


def clip_polygon(points, support, depth=0):
    """Clip a surface polygon to the convex volume inset by a given depth."""
    polygon=list(points)
    for normal,offset in support:
        if not polygon:break
        result=[];previous=polygon[-1]
        before=dot(normal,previous)-offset+depth
        for current in polygon:
            after=dot(normal,current)-offset+depth
            if (before<=0)!=(after<=0):
                ratio=before/(before-after)
                result.append(tuple(a+ratio*(b-a) for a,b in zip(previous,current)))
            if after<=0:result.append(current)
            previous,before=current,after
        polygon=result
    return polygon


def polygon_area(points):
    if len(points)<3:return 0
    origin=points[0];cross=[0.0,0.0,0.0]
    for a,b in zip(points[1:-1],points[2:]):
        u,v=sub(a,origin),sub(b,origin)
        cross[0]+=u[1]*v[2]-u[2]*v[1]
        cross[1]+=u[2]*v[0]-u[0]*v[2]
        cross[2]+=u[0]*v[1]-u[1]*v[0]
    return math.sqrt(dot(cross,cross))*.5


def surface_measure(points, triangles, support, tolerance=1e-5, *, volume_bounds=None, boundary_support=None):
    """Detect crossing triangles even if ALL their vertices are outside.

    Depth is a lower bound obtained by clipping inset volumes, using 1e-7
    search resolution and a 1e-14 area cutoff (not an unconditional depth
    accuracy guarantee for arbitrarily thin polygons).
    With boundary_support, depth refers only to the selected physical planes
    of this cell, NOT the global nearest-boundary distance of a nonconvex union.
    This checks the supplied surface versus one convex solid only; it does not
    certify complete contact, watertight hands or hand self-intersection.
    """
    # A decomposed solid has internal cell faces. Clip those at depth zero,
    # but apply penetration tolerance/depth ONLY to actual exterior faces.
    # Otherwise a triangle on a cell seam would disappear from both cells.
    if boundary_support is None:boundary_support=support
    if not boundary_support or any(plane not in support for plane in boundary_support):
        raise ValueError('Boundary planes must belong to the convex cell')
    if (type(tolerance) not in (int,float) or not math.isfinite(tolerance)
            or not 0<=tolerance<=.01 or not support):raise ValueError('Invalid surface contact domain')
    if not isinstance(points,(list,tuple)) or not 3<=len(points)<=4096:
        raise ValueError('Invalid contact surface vertices')
    points=[vector(p) for p in points]
    if not isinstance(triangles,(list,tuple)) or not 1<=len(triangles)<=4096:
        raise ValueError('Invalid contact surface triangles')
    if volume_bounds is not None:
        if not isinstance(volume_bounds,(list,tuple)) or len(volume_bounds)!=2:
            raise ValueError('Invalid contact volume bounds')
        lower,upper=map(vector,volume_bounds)
        if any(a>=b for a,b in zip(lower,upper)):raise ValueError('Flat or reversed contact bounds')
    count=0;deepest=0;area=0
    for face in triangles:
        if (not isinstance(face,(list,tuple)) or len(face)!=3
                or any(type(i) is not int or not 0<=i<len(points) for i in face)):
            raise ValueError('Invalid contact surface index')
        triangle=[points[i] for i in face]
        if volume_bounds is not None and any(
                max(triangle[0][j],triangle[1][j],triangle[2][j])<lower[j]
                or min(triangle[0][j],triangle[1][j],triangle[2][j])>upper[j] for j in range(3)):
            continue
        region=clip_polygon(triangle,support)
        interior=clip_polygon(region,boundary_support,tolerance)
        size=polygon_area(interior)
        if size<=1e-14:continue
        count+=1;area+=size
        low=tolerance
        high=min(max(offset-dot(normal,p) for p in interior) for normal,offset in boundary_support)
        if high<low-1e-10:raise ValueError('Invalid inset depth bound')
        # Each upper plane bound is valid for every point of this polygon.
        for _ in range(32):
            if high-low<=1e-7:break
            middle=(low+high)*.5
            if polygon_area(clip_polygon(interior,boundary_support,middle))>1e-14:low=middle
            else:high=middle
        deepest=max(deepest,low)
    return {'triangles':len(triangles),'penetrating_triangles':count,
            'inset_surface_area':area,'max_depth_lower_bound':deepest,
            'penetration_tolerance':tolerance,'inset_area_cutoff':1e-14,
            'depth_search_resolution':1e-7,'surface_crossings_checked':True,
            'depth_reference':'selected_cell_boundary_planes' if boundary_support!=support else 'convex_solid_planes',
            'full_contact_qualified':False,'hand_self_intersection_checked':False}
