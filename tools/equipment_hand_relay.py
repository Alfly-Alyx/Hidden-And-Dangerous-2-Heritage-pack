"""Pinned complete hand/weapon poses through the collected native model relay.

The records are still supplied diagnostic joints, not a scene loaded by the
client. Commercial source bytes and derived poses never leave the private lab.
"""
from copy import deepcopy
import math
import struct

from animation_tick_audit import model_poses
from build_equipment_hand_animation import HAND_NAMES
from build_native_hand_pipeline import make_arena
from fpv_contact_constraints import world,targets,wrist_errors
from hand_pose_ik import pinned_skin
from ls3d_animation_stream_oracle import validate
from menu_gui_audit import parse_4ds_nodes
from native_collected_hand_relay import CollectedHandRelayOracle
from native_hand_targets import preparation_inputs,encode_inputs


def equipment_case(hand,rig,clips,steps,grips):
    _,skin=pinned_skin(hand)
    hn,hi=model_poses(hand);gn,gi=model_poses(rig);names=hn+gn;initial=hi+gi
    if len(hn)!=37 or set(hn)!=HAND_NAMES or len(names)>=120 or len(set(names))!=len(names):
        raise ValueError('Unreviewed complete hand/weapon identities or owner arena overlap')
    gear_nodes=parse_4ds_nodes(rig)['nodes']
    validate(names,clips,initial,steps,9)
    data,_=preparation_inputs(skin,gear_nodes,dict(zip(names,initial)),grips)
    encode_inputs(data)
    roles=data['roles']+[names.index(f'Bip01 {side} {part}') for side in ('L','R') for part in ('UpperArm','Forearm','Hand')]
    offsets=[i*0x200 for i in range(len(names))]
    return {'fixture':(data,make_arena(data,offsets),offsets,roles,names,clips,initial,steps),
            'hand_nodes':skin['nodes'],'gear_nodes':gear_nodes,'grips':grips}


class EquipmentHandRelayOracle(CollectedHandRelayOracle):
    def __init__(self,*args):
        self.equipment=None
        super().__init__(*args)

    def relay_case(self,turned):
        if type(turned) is not bool or turned or self.equipment is None:
            raise ValueError('A pinned complete equipment case is required without synthetic rotation')
        return deepcopy(self.equipment['fixture'])

    def correction_measurement(self):
        names=self.equipment['fixture'][4];poses={}
        for name,at in zip(names,self.offsets):
            poses[name]={key:list(struct.unpack_from('<'+'f'*width,self.adapter.arena_at_refresh,at+offset))
                for key,offset,width in (('position',0xb0,3),('rotation',0xc0,4),('scale',0xd0,3))}
        before={name:{'position':p[:3],'rotation':p[3:7],'scale':p[7:]} for name,p in zip(names,self.observed['poses'])}
        wanted=targets(world(self.equipment['gear_nodes'],before),self.equipment['grips'],root_name='fpv_weapon')
        old=wrist_errors(world(self.equipment['hand_nodes'],before),wanted)
        new=wrist_errors(world(self.equipment['hand_nodes'],poses),wanted)
        if any(not math.isfinite(v) for v in (*old.values(),*new.values())) or max(new.values())>5e-6:
            raise ValueError('Collected native relay missed a complete hand wrist target')
        return {'wrist_before':old,'wrist_after':new,'wrist_measurement_is_independent_math':True}

    def run_equipment(self,hand,rig,clips,steps,grips,*,patched=True,registered=True,controller_present=True):
        if self.equipment is not None:raise ValueError('Nested complete equipment relay case')
        self.equipment=equipment_case(hand,rig,clips,steps,grips)
        try:
            result=super().run(patched=patched,registered=registered,controller_present=controller_present)
            return {**result,'complete_hand_nodes':37,'total_nodes':len(self.equipment['fixture'][4]),
                    'all_records_are_diagnostic_joints':True,'native_scene_loading_qualified':False,
                    'source_geometry_or_poses_exported':False,'native_palette_or_skin_executed':False}
        finally:self.equipment=None
