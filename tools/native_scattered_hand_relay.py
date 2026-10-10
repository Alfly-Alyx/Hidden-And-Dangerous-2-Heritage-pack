"""Native animation, registered scatter correction and native recursive refresh."""
import struct

from native_hand_relay import HandRelayOracle,HOOK_SITE,HOOK_ORIGINAL
from native_hand_scatter_hook import HandScatterHookOracle,ENTRY
from native_hand_scatter import WORK_SIZE


def scatter_relay_patch(original,site=HOOK_SITE,target=ENTRY):
    if (type(original) is not bytes or original!=HOOK_ORIGINAL or type(site) is not int
            or site!=HOOK_SITE or type(target) is not int or target!=ENTRY):
        raise ValueError('Unreviewed scattered native relay patch contract')
    return b'\xe8'+struct.pack('<i',target-(site+5))+b'\x90'


class ScatteredHandRelayOracle(HandRelayOracle):
    ADAPTER=HandScatterHookOracle
    HOOK_ENTRY=ENTRY
    PATCH_BUILDER=staticmethod(scatter_relay_patch)
    EXPECTED_CALLS={**HandRelayOracle.EXPECTED_CALLS,'Hd2CorrectScatteredHandPose':1}
    OWNER=0x4800000

    def __init__(self,library,compiled):
        super().__init__(library,compiled)
        self.uc.mem_map(self.OWNER,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)

    def node_addresses(self,offsets):
        return [self.adapter.NODES+((i*37)%128)*0x2000+4 for i in range(len(offsets))]

    def owner_address(self):return self.OWNER

    def seed_adapter(self,data,arena,offsets,roles):
        h=self.adapter
        h.seed(data,arena,offsets,roles,alignment=4,model_identity=self.STATE+0x100)
        self.owner_seed=arena[0xf000:0xf240]+b'Z'*(4096-0x240)
        self.uc.mem_write(self.OWNER,self.owner_seed)

    def read_arena(self):
        h=self.adapter;arena=bytearray(65536)
        for pointer,offset in zip(h.pointers,h.offsets):
            arena[offset:offset+0x170]=self.uc.mem_read(pointer,0x170)
        arena[0xf000:0xf240]=self.uc.mem_read(self.OWNER,0x240)
        return bytes(arena)

    def prepare_adapter(self):
        h=self.adapter
        h.phase_writes=[(h.CONTEXT+40,h.CONTEXT+52),(h.WORK,h.WORK+WORK_SIZE),*h.allowed]
        h.return_to_scatter=None;h.late_mutation=None

    def begin_adapter(self):self.adapter.mode='hook';self.adapter.active=True
    def end_adapter(self):self.adapter.mode=None;self.adapter.active=False

    def check_adapter_success(self):
        h=self.adapter
        if struct.unpack('<2I',self.uc.mem_read(h.CONTEXT+40,8))!=(0,0):raise ValueError('Scattered native relay correction failed')
        snapshot=struct.pack('<'+'f'*(h.count*10),*(v for p in self.observed['poses'] for v in p))
        if bytes(self.uc.mem_read(h.WORK+128*0x170,h.count*40))!=snapshot:
            raise ValueError('Scatter adapter did not gather native animated poses')

    def check_external_guards(self):
        h=self.adapter
        for page,seed in zip(h.pages,h.blocks):
            current=bytes(self.uc.mem_read(page,4096))
            if current[:4]!=seed[:4] or current[0x174:]!=seed[0x174:]:raise ValueError('Scattered node page guard changed')
        if bytes(self.uc.mem_read(self.OWNER+0x240,4096-0x240))!=self.owner_seed[0x240:]:
            raise ValueError('Scattered owning-visual guard changed')

    def run(self,**kwargs):
        result=super().run(**kwargs)
        return {**result,'node_allocations_are_separate_guarded_pages':True,
            'callback_uses_compiled_gather_and_scatter':True,'four_byte_aligned_native_records':True,
            'native_pose_data_not_reinjected_between_steps':True,'live_allocation_ownership_qualified':False}
