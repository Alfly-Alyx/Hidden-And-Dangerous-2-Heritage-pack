"""Original opaque indexed inventory art derived only from modern mesh recipes.

No commercial bitmap, palette or transparency rule is reused. BMP storage is
checked independently; native UI loading and background treatment remain open.
"""
import io
import struct

from build_modern_asset import build_meshes,cross,sub,unit
from build_modern_equipment_hose import digest
from software_depth import draw_triangles

SIZE=(64,32)
BACKGROUND=(18,24,30)


def palette():
    # Original fixed colour cube plus fine neutral shades for small metal parts.
    return [(r*51,g*51,b*51) for r in range(6) for g in range(6) for b in range(6)]+[(round(i*255/39),)*3 for i in range(40)]


def colour_index(rgb,colours):
    return min(range(256),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,colours[i])))


def encode_bitmap(image):
    if image.mode!='RGB' or image.size!=SIZE:raise ValueError('Expected a 64 by 32 RGB modern icon')
    pixels=image.load();width,height=SIZE;body=bytearray();colours=palette();indices={}
    for y in range(height-1,-1,-1):
        for x in range(width):
            rgb=pixels[x,y]
            if rgb not in indices:indices[rgb]=colour_index(rgb,colours)
            body.append(indices[rgb])
    offset=14+40+1024
    header=struct.pack('<2sIHHI',b'BM',offset+len(body),0,0,offset)
    dib=struct.pack('<IiiHHIIiiII',40,width,height,1,8,0,len(body),0,0,256,256)
    colours=b''.join(bytes((b,g,r,0)) for r,g,b in palette())
    return header+dib+colours+bytes(body)


def prepare(recipe):
    from PIL import Image
    meshes=build_meshes(recipe);points=[p for high,_ in meshes for p in high.points]
    # Slight elevated side view reveals the lateral FG42 magazine. These are
    # artistic projection axes, not an engine camera or engineering drawing.
    right=unit((0,1,0));up=unit((-.42,0,1));forward=unit(cross(right,up))
    dot=lambda p,a:sum(x*y for x,y in zip(p,a))
    xs=[dot(p,right) for p in points];ys=[dot(p,up) for p in points]
    width,height=256,128
    if min(max(xs)-min(xs),max(ys)-min(ys))<=0:raise ValueError('Degenerate modern icon geometry')
    scale=min((width-16)/(max(xs)-min(xs)),(height-16)/(max(ys)-min(ys)))
    cx=(max(xs)+min(xs))/2;cy=(max(ys)+min(ys))/2
    image=Image.new('RGB',(width,height),BACKGROUND);triangles=[];light=unit((.6,-.3,1))
    for high,_ in meshes:
        diffuse=recipe['materials'][high.material-1]['diffuse']
        for face in high.triangles:
            p=[high.points[i] for i in face];normal=unit(cross(sub(p[1],p[0]),sub(p[2],p[0])))
            shade=.38+.62*max(0,dot(normal,light))
            colour=tuple(round(255*min(1,c*shade)**(1/2.2)) for c in diffuse)
            screen=[(width/2+(dot(q,right)-cx)*scale,height/2-(dot(q,up)-cy)*scale,dot(q,forward)) for q in p]
            triangles.append((screen,colour))
    draw_triangles(image,triangles,(0,0,width,height))
    raw=encode_bitmap(image.resize(SIZE,Image.Resampling.BOX))
    with Image.open(io.BytesIO(raw)) as decoded:
        decoded.load()
        if decoded.mode!='P' or decoded.size!=SIZE or len(set(decoded.tobytes()))<3:
            raise ValueError('Modern icon decode or visibility check failed')
        if decoded.getpalette()!=[v for rgb in palette() for v in rgb]:raise ValueError('Modern icon palette differs')
    return raw,{'schema_version':1,'provenance':'MODERN_ORIGINAL_MESH_RENDER','runtime_status':'pending',
        'size':len(raw),'sha256':digest(raw),'width':64,'height':32,'bits_per_pixel':8,'compression':'BI_RGB',
        'projection':'original_elevated_side','supersampling':4,'palette':'original_rgb666_gray40',
        'background_input_rgb':list(BACKGROUND),'background_rgb':list(palette()[colour_index(BACKGROUND,palette())]),
        'transparent_background':False,'commercial_bitmap_or_palette_used':False,
        'native_ui_load_qualified':False,'engine_background_or_transparency_qualified':False}
