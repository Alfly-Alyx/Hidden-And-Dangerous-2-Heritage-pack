"""Convex cells for serialized original ring meshes, preserving hollow bores.

Recipe topology indexes the serialized vertices; generated coordinates are
never substituted for actual posed geometry. Internal decomposition faces
must not be interpreted as physical contact surfaces.
"""
import math
from dataclasses import dataclass
from build_modern_asset import ring_mesh
from convex_contact import planes,surface_measure,vector


def bounded(points,support,boundary):
    return {'bounds':[tuple(fn(p[i] for p in points) for i in range(3)) for fn in (min,max)],
            'support':support,'boundary_support':boundary}


def ring_cells(mesh,part,lod=0):
    if type(lod) is not int or lod not in (0,1) or part.get('kind')!='rings' or mesh.name!=part.get('name'):
        raise ValueError('Unreviewed ring cell topology')
    template=ring_mesh(part,mesh.material,low=bool(lod))
    if len(mesh.triangles)!=len(template.triangles) or len(mesh.points)!=3*len(template.triangles):
        raise ValueError('Ring cells require the serialized expanded mesh')
    points={}
    for original,actual in zip(template.triangles,mesh.triangles):
        # FPV handedness conversion reverses every serialized triangle.
        for key,index in zip(original,(actual[0],actual[2],actual[1])):
            value=mesh.points[index]
            if key in points and points[key]!=value:raise ValueError('Inconsistent serialized ring vertex')
            points[key]=value
    if set(points)!=set(range(len(template.points))):raise ValueError('Incomplete ring vertex correspondence')
    count=max(6,part['segments']//2) if lod else part['segments'];rows=len(part['sections']);span=rows*count
    hollow=bool(part.get('inner_ratio',0));cells=[]
    for row in range(rows-1):
        for sector in range(count):
            a=row*count+sector;b=row*count+(sector+1)%count
            if hollow:
                vertices=[points[i] for i in (a,b,b+span,a+span,a+count,b+count,b+span+count,a+span+count)]
                polygons=((0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2))
                physical={2,3}
            else:
                centers=[tuple(math.fsum(points[r*count+i][j] for i in range(count))/count for j in range(3))
                         for r in (row,row+1)]
                vertices=[centers[0],points[a],points[b],centers[1],points[a+count],points[b+count]]
                polygons=((0,1,2),(3,5,4),(1,4,5,2),(0,3,4,1),(0,2,5,3));physical={2}
            if row==0:physical.add(0)
            if row==rows-2:physical.add(1)
            triangles=[];boundary_indices=[]
            for i,polygon in enumerate(polygons):
                for k in range(1,len(polygon)-1):
                    if i in physical:boundary_indices.append(len(triangles))
                    triangles.append((polygon[0],polygon[k],polygon[k+1]))
            support=planes(vertices,triangles);boundary=[support[i] for i in boundary_indices]
            cells.append(bounded(vertices,support,boundary))
    return cells


def cells(mesh,parts,lod=0):
    try:
        support=planes(mesh.points,mesh.triangles)
        return [bounded(mesh.points,support,support)]
    except ValueError as convex_error:
        part=next((p for p in parts if p['name']==mesh.name),None)
        if part is None or part.get('kind')!='rings':raise convex_error
        return ring_cells(mesh,part,lod)


@dataclass(frozen=True)
class PreparedSurface:
    points: tuple
    faces_with_bounds: tuple


def prepare_surface(points,triangles):
    """Exact AABB broad phase plus compact face subsets, never point sampling.

Discard only triangles whose full bounding box cannot meet a cell box. Every
remaining triangle is still clipped as a surface, including all-vertices-outside
crossings and internal cell seams. Original geometry is not modified.
"""
    if not isinstance(points,(list,tuple)) or not 3<=len(points)<=4096:raise ValueError('Unreviewed surface points')
    points=[vector(p) for p in points]
    if not isinstance(triangles,(list,tuple)) or not 1<=len(triangles)<=4096:raise ValueError('Unreviewed surface faces')
    prepared=[]
    for face in triangles:
        if (not isinstance(face,(tuple,list)) or len(face)!=3
                or any(type(i) is not int or not 0<=i<len(points) for i in face)):raise ValueError('Invalid surface index')
        vertices=[points[i] for i in face]
        prepared.append((face,tuple(min(p[j] for p in vertices) for j in range(3)),
                              tuple(max(p[j] for p in vertices) for j in range(3))))
    return PreparedSurface(tuple(points),tuple((tuple(face),lo,hi) for face,lo,hi in prepared))


def measure_surface_cells(surface,volumes):
    if not isinstance(surface,PreparedSurface):raise ValueError('Expected a prepared surface')
    points,prepared=surface.points,surface.faces_with_bounds
    if not isinstance(volumes,list) or not volumes:raise ValueError('Missing convex cells')
    count=0;depth=0;area=0;clipped=0
    for volume in volumes:
        lower,upper=map(vector,volume['bounds'])
        if any(a>=b for a,b in zip(lower,upper)):raise ValueError('Invalid convex cell bounds')
        if (not volume['boundary_support'] or not volume['support']
                or any(p not in volume['support'] for p in volume['boundary_support'])):
            raise ValueError('Invalid cell boundary planes')
        selected=[face for face,lo,hi in prepared if all(lo[j]<=upper[j] and hi[j]>=lower[j] for j in range(3))]
        if not selected:continue
        indices=sorted({i for face in selected for i in face});remap={i:n for n,i in enumerate(indices)}
        result=surface_measure([points[i] for i in indices],[tuple(remap[i] for i in f) for f in selected],
                               volume['support'],boundary_support=volume['boundary_support'])
        count+=result['penetrating_triangles'];depth=max(depth,result['max_depth_lower_bound']);area+=result['inset_surface_area']
        clipped+=len(selected)
    return {'convex_cells':len(volumes),'penetrating_triangle_cells':count,'max_cell_boundary_depth':depth,
            'inset_surface_area_sum':area,'broad_phase_candidate_triangle_cells':clipped,
            'all_input_triangle_cells':len(prepared)*len(volumes),'exact_aabb_broad_phase':True}


def surface_for_cells(points,triangles,volumes):
    return measure_surface_cells(prepare_surface(points,triangles),volumes)
