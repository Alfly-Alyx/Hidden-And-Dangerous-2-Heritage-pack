"""Modern two-bone pose authoring on pinned commercial FPV hand skeletons.

Geometry and bind/rest transforms remain commercial/private. Targets and
finger curls are modern authoring choices, not recovered animation keys.
No bone stretching, scene calls, installation or playable-weapon claim.
"""
import hashlib
import math
import struct

from benelli_fpv_rig_audit import HAND_PINS,HAND_MODELS
from four_ds_skin import read_reviewed
from model_transform import (affine,compose,conjugate,decompose,invert,matmul,matvec,
                             node_transform,point,quaternion,rotation,transpose)


def vector(value):
    if (not isinstance(value,(list,tuple)) or len(value)!=3
            or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>10 for v in value)):
        raise ValueError('Unreviewed IK vector')
    return list(value)


def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def norm(value):return math.sqrt(dot(value,value))


def unit(value):
    length=norm(value)
    if length<1e-9:raise ValueError('Degenerate IK direction')
    return [v/length for v in value]


def shortest_rotation(start,end):
    """Shortest proper active rotation, with a deterministic antiparallel axis."""
    a,b=unit(vector(start)),unit(vector(end));cosine=max(-1,min(1,dot(a,b)))
    if cosine<-1+1e-10:
        reference=min(([1,0,0],[0,1,0],[0,0,1]),key=lambda axis:abs(dot(a,axis)))
        axis=unit(cross(a,reference));return rotation([*axis,0])
    value=[*cross(a,b),1+cosine];length=math.sqrt(sum(v*v for v in value))
    return rotation([v/length for v in value])


def two_bone(shoulder,target,pole,upper_length,forearm_length):
    shoulder,target,pole=map(vector,(shoulder,target,pole))
    if any(type(v) not in (int,float) or not math.isfinite(v) or not .01<=v<=2
           for v in (upper_length,forearm_length)):raise ValueError('Unreviewed IK bone length')
    delta=sub(target,shoulder);distance=norm(delta)
    if not abs(upper_length-forearm_length)+1e-6<distance<upper_length+forearm_length-1e-6:
        raise ValueError('Unreachable or singular hand target; stretching is forbidden')
    axis=unit(delta);hint=sub(pole,shoulder)
    direction=unit([a-dot(hint,axis)*b for a,b in zip(hint,axis)])
    along=(upper_length**2-forearm_length**2+distance**2)/(2*distance)
    height=math.sqrt(max(0,upper_length**2-along**2))
    elbow=[s+along*a+height*b for s,a,b in zip(shoulder,axis,direction)]
    if max(abs(norm(sub(elbow,shoulder))-upper_length),abs(norm(sub(target,elbow))-forearm_length))>1e-8:
        raise ValueError('IK length reconstruction failed')
    return elbow


def validate_basis(value):
    if not isinstance(value,list) or len(value)!=3:raise ValueError('Invalid hand orientation')
    value=[vector(row) for row in value]
    identity=matmul(value,transpose(value))
    if max(abs(identity[i][j]-(i==j)) for i in range(3) for j in range(3))>1e-6:
        raise ValueError('Hand orientation must be orthonormal')
    if dot(value[0],cross(value[1],value[2]))<1-1e-6:raise ValueError('Reflected hand orientation')
    return value


def bend_plane_rotation(start,end,normal):
    """Resolve bone-axis twist with the arm's bending plane, not an antipode."""
    def frame(direction,hint):
        x=unit(vector(direction));hint=vector(hint)
        z=unit([a-dot(hint,x)*b for a,b in zip(hint,x)]);y=cross(z,x)
        return transpose([x,y,z])
    return matmul(frame(end,normal),transpose(frame(start,[0,0,1])))


def pinned_skin(raw):
    digest=hashlib.sha256(raw).hexdigest()
    matches=[name for name in HAND_MODELS if (len(raw),digest)==HAND_PINS[name][1:]]
    if len(matches)!=1:raise ValueError('Unreviewed commercial hand source')
    return matches[0],read_reviewed(raw)


def finger_curls(grip):
    """Resolve bounded modern per-digit choices without changing the input."""
    if (not isinstance(grip,dict) or 'finger_curl_degrees' not in grip
            or set(grip)-{'finger_curl_degrees','finger_curl_overrides'}):
        raise ValueError('Unexpected modern finger fields')
    def checked(angles):
        if (not isinstance(angles,list) or len(angles)!=3
                or any(type(v) not in (int,float) or not math.isfinite(v) or not -110<=v<=110 for v in angles)):
            raise ValueError('Unreviewed authored finger curl')
        return angles[:]
    base=checked(grip['finger_curl_degrees']);overrides=grip.get('finger_curl_overrides',{})
    if (not isinstance(overrides,dict) or set(overrides)-{'1','2','3','4'}
            or ('finger_curl_overrides' in grip and not overrides)):
        raise ValueError('Unreviewed finger override selection')
    result={str(i):base[:] for i in range(1,5)}
    for digit,angles in overrides.items():result[digit]=checked(angles)
    return result


def author_pose(raw,targets,grips,*,arm_rotation_policy='minimal'):
    """Return derived local SRT poses; never export these as original skeleton data.

    Targets contain wrist world position, hand rest-to-target active rotation
    and elbow pole. Four fingers use modern curls; thumb stays at source rest.
    """
    if arm_rotation_policy not in ('minimal','bend_plane'):raise ValueError('Unreviewed arm rotation policy')
    source,skin=pinned_skin(raw);nodes=skin['nodes'];by_name={n['name']:n for n in nodes}
    if set(targets)!={'L','R'} or set(grips)!={'L','R'}:raise ValueError('Both hand targets are required')
    desired={};arm_errors={};axes={}
    for side in ('L','R'):
        target=targets[side];grip=grips[side]
        if set(target)!={'position','rotation','pole'}:
            raise ValueError('Unexpected modern hand target or grip fields')
        wrist=vector(target['position']);turn=validate_basis(target['rotation']);pole=vector(target['pole'])
        curls=finger_curls(grip)
        names=[f'Bip01 {side} '+part for part in ('UpperArm','Forearm','Hand')]
        if any(name not in by_name for name in names):raise ValueError('Missing reviewed arm joint')
        rest=[skin['rest_world'][by_name[name]['index']] for name in names]
        upper=sub(rest[1][1],rest[0][1]);fore=sub(rest[2][1],rest[1][1])
        elbow=two_bone(rest[0][1],wrist,pole,norm(upper),norm(fore))
        upper_target=sub(elbow,rest[0][1]);fore_target=sub(wrist,elbow)
        if arm_rotation_policy=='bend_plane':
            normal=unit(cross(upper_target,fore_target))
            if side=='R':normal=[-v for v in normal]
            upper_turn=bend_plane_rotation(upper,upper_target,normal)
            fore_turn=bend_plane_rotation(fore,fore_target,normal)
        else:
            upper_turn=shortest_rotation(upper,upper_target);fore_turn=shortest_rotation(fore,fore_target)
        desired[names[0]]=(matmul(upper_turn,rest[0][0]),rest[0][1])
        desired[names[1]]=(matmul(fore_turn,rest[1][0]),elbow)
        desired[names[2]]=(matmul(turn,rest[2][0]),wrist)
        arm_errors[side]={'upper_length':norm(upper),'forearm_length':norm(fore),'wrist_target':wrist}
        for finger in range(1,5):
            for segment,angle in enumerate(curls[str(finger)]):
                name=f'Bip01 {side} Finger{finger}'+('' if segment==0 else str(segment))
                if name not in by_name:raise ValueError('Missing reviewed finger joint')
                basis=skin['rest_world'][by_name[name]['index']][0]
                axis=unit(matvec(transpose(basis),[0,0,1]));half=math.radians(angle)/2
                axes[name]=rotation([*[v*math.sin(half) for v in axis],math.cos(half)])
    world={};poses={};max_position_change=0;max_scale_change=0
    for node in nodes:
        parent=node['parent_id'];local=node_transform(raw,node)
        if node['name'] in desired:
            local=compose(invert(world[parent]),desired[node['name']]) if parent else desired[node['name']]
        elif node['name'] in axes:
            local=(matmul(local[0],axes[node['name']]),local[1])
        position,q,scale,_=decompose(local)
        position_change=max(abs(a-b) for a,b in zip(position,node['position']))
        scale_change=max(abs(a-b) for a,b in zip(scale,node['scale']))
        max_position_change=max(max_position_change,position_change);max_scale_change=max(max_scale_change,scale_change)
        if position_change>2e-6 or scale_change>2e-5:raise ValueError('Hand authoring would move or stretch a joint')
        position=list(node['position']);scale=list(node['scale'])
        if node['name'] not in desired and node['name'] not in axes:
            native=list(struct.unpack_from('<4f',raw,node['position_offset']+12));q=conjugate(native)
        else:native=conjugate(q)
        poses[node['name']]={'position':position,'rotation':native,'scale':scale}
        local=affine(position,q,scale);world[node['index']]=compose(world[parent],local) if parent else local
    for side,row in arm_errors.items():
        actual=world[by_name[f'Bip01 {side} Hand']['index']][1]
        row['wrist_error']=max(abs(a-b) for a,b in zip(actual,row['wrist_target']))
        if row['wrist_error']>5e-6:raise ValueError('Authored hand missed its target')
    return poses,{'schema_version':1,'provenance':'DERIVE_MODERNE_SUR_SQUELETTE_COMMERCIAL',
        'hand_source':source,'hand_sha256':hashlib.sha256(raw).hexdigest(),'arms':arm_errors,
        'arm_rotation_policy':arm_rotation_policy,
        'max_local_position_residual':max_position_change,'max_local_scale_residual':max_scale_change,
        'rest_positions_and_scales_preserved':True,'original_geometry_modified':False,
        'original_animation_keys_read':False,'thumb_pose_authored':False,'finger_contact_qualified':False,
        'camera_calibrated':False,'game_modified':False,'game_started':False,'engine_validated':False}
