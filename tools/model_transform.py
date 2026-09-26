"""Finite 4DS XYZW transforms for offline inspection, not scene2 conventions."""
import math
import struct


def dot(a,b): return sum(x*y for x,y in zip(a,b))
def transpose(m): return [list(c) for c in zip(*m)]
def matmul(a,b): return [[dot(row,col) for col in transpose(b)] for row in a]
def matvec(m,v): return [dot(row,v) for row in m]


def rotation(q):
    if not all(math.isfinite(v) for v in q): raise ValueError('Nonfinite quaternion')
    length=math.sqrt(dot(q,q))
    if length<1e-12: raise ValueError('Zero quaternion')
    x,y,z,w=[v/length for v in q]
    return [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
            [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
            [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]


def determinant(m):
    a,b,c=m[0]; d,e,f=m[1]; g,h,i=m[2]
    return a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)


def inverse(matrix):
    a,b,c=matrix[0]; d,e,f=matrix[1]; g,h,i=matrix[2]
    det=determinant(matrix)
    if not math.isfinite(det) or abs(det)<1e-12: raise ValueError('Singular transform')
    return [[v/det for v in row] for row in
            [[e*i-f*h,c*h-b*i,b*f-c*e],[f*g-d*i,a*i-c*g,c*d-a*f],[d*h-e*g,b*g-a*h,a*e-b*d]]]


def affine(position, quaternion, scale):
    if not all(math.isfinite(v) for v in (*position,*scale)): raise ValueError('Nonfinite transform')
    return ([[v*scale[j] for j,v in enumerate(row)] for row in rotation(quaternion)], list(position))


def compose(parent, child):
    basis=matmul(parent[0],child[0])
    position=[a+b for a,b in zip(matvec(parent[0],child[1]),parent[1])]
    return basis,position


def invert(transform):
    basis=inverse(transform[0])
    return basis,[-v for v in matvec(basis,transform[1])]


def point(transform, value):
    return [a+b for a,b in zip(matvec(transform[0],value),transform[1])]


def quaternion(m):
    trace=m[0][0]+m[1][1]+m[2][2]
    if trace>0:
        s=2*math.sqrt(1+trace)
        q=[(m[2][1]-m[1][2])/s,(m[0][2]-m[2][0])/s,(m[1][0]-m[0][1])/s,s/4]
    else:
        i=max(range(3),key=lambda k:m[k][k]); j=(i+1)%3; k=(i+2)%3
        s=2*math.sqrt(max(0,1+m[i][i]-m[j][j]-m[k][k]))
        if s<1e-12: raise ValueError('Degenerate rotation basis')
        q=[0,0,0,(m[k][j]-m[j][k])/s]
        q[i]=s/4; q[j]=(m[i][j]+m[j][i])/s; q[k]=(m[i][k]+m[k][i])/s
    norm=math.sqrt(dot(q,q))
    return [v/norm for v in q]


def decompose(transform, tolerance=1e-5):
    matrix,position=transform
    columns=transpose(matrix)
    scale=[math.sqrt(dot(col,col)) for col in columns]
    if any(s<1e-10 for s in scale): raise ValueError('Degenerate transform scale')
    basis=[[v/scale[j] for j,v in enumerate(row)] for row in matrix]
    if determinant(basis)<=0: raise ValueError('Reflected transform requires separate review')
    columns=transpose(basis)
    if max(abs(dot(a,b)) for i,a in enumerate(columns) for b in columns[i+1:])>tolerance:
        raise ValueError('Sheared transform cannot be represented as 4DS SRT')
    q=quaternion(basis)
    rebuilt=affine(position,q,scale)
    error=max(abs(matrix[i][j]-rebuilt[0][i][j]) for i in range(3) for j in range(3))
    if not math.isfinite(error) or error>tolerance: raise ValueError('Transform decomposition residual too large')
    return list(position),q,scale,error


def node_transform(data,node):
    return affine(node['position'],struct.unpack_from('<4f',data,node['position_offset']+12),node['scale'])


def world_transforms(data,nodes):
    by_id={node['index']:node for node in nodes}
    result={}; visiting=set()
    def visit(index):
        if index in result: return result[index]
        if index in visiting or index not in by_id: raise ValueError('Invalid or cyclic model hierarchy')
        visiting.add(index); node=by_id[index]
        value=node_transform(data,node)
        if node['parent_id']: value=compose(visit(node['parent_id']),value)
        visiting.remove(index); result[index]=value
        return value
    for node in nodes: visit(node['index'])
    return result
