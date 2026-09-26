"""Small original orthographic Z-buffer for offline asset previews."""
from array import array
import math


def draw_triangles(image,triangles,region):
    """Pixels with larger interpolated depth win, independently of face order."""
    left,top,width,height=region
    if any(type(v) is not int for v in region) or width<=0 or height<=0:
        raise ValueError('Invalid raster region')
    right=min(image.width,left+width);bottom=min(image.height,top+height)
    left=max(0,left);top=max(0,top)
    if left>=right or top>=bottom:return
    width=right-left
    depths=array('d',[-math.inf])*(width*(bottom-top))
    pixels=image.load()
    for vertices,colour in triangles:
        if len(vertices)!=3 or any(len(v)!=3 or not all(math.isfinite(c) for c in v) for v in vertices):
            raise ValueError('Invalid screen-space triangle')
        (x0,y0,z0),(x1,y1,z1),(x2,y2,z2)=vertices
        determinant=(x1-x0)*(y2-y0)-(x2-x0)*(y1-y0)
        if abs(determinant)<1e-10:continue
        dzdx=((z1-z0)*(y2-y0)-(z2-z0)*(y1-y0))/determinant
        dzdy=((x1-x0)*(z2-z0)-(x2-x0)*(z1-z0))/determinant
        first=max(top,math.ceil(min(y0,y1,y2)-.5))
        last=min(bottom,math.ceil(max(y0,y1,y2)-.5))
        edges=tuple(zip(vertices,vertices[1:]+vertices[:1]))
        for y in range(first,last):
            py=y+.5;intersections=[]
            for (a,b,_),(c,d,_) in edges:
                if min(b,d)<=py<max(b,d):
                    intersections.append(a+(py-b)*(c-a)/(d-b))
            if len(intersections)!=2:continue
            start=max(left,math.ceil(min(intersections)-.5))
            end=min(right,math.ceil(max(intersections)-.5))
            depth=z0+dzdx*(start+.5-x0)+dzdy*(py-y0)
            offset=(y-top)*width+start-left
            for x in range(start,end):
                if depth>depths[offset]+1e-12:
                    depths[offset]=depth;pixels[x,y]=colour
                offset+=1;depth+=dzdx

