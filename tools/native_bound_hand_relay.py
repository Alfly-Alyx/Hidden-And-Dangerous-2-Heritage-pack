"""Compiled named-node binding feeds the registered native scatter relay."""
import struct

from native_scattered_hand_relay import ScatteredHandRelayOracle
from native_hand_model_binding import HandModelBindingOracle,OUTPUT_SIZE


class BoundHandRelayOracle(ScatteredHandRelayOracle):
    def __init__(self,library,compiled,binding_raw):
        self.binding=None
        super().__init__(library,compiled)
        self.binding=HandModelBindingOracle(binding_raw,self)

    def on_code(self,uc,address,size,context):
        if self.binding is not None and self.binding.active:return self.binding.on_code(uc,address,size,context)
        return super().on_code(uc,address,size,context)

    def on_write(self,uc,access,address,size,value,context):
        if self.binding is not None and self.binding.active:return self.binding.on_write(uc,access,address,size,value,context)
        return super().on_write(uc,access,address,size,value,context)

    def seed_adapter(self,data,arena,offsets,roles):
        super().seed_adapter(data,arena,offsets,roles)
        h=self.adapter;records=[];original={pointer:i for i,pointer in enumerate(h.pointers)}
        # Supply a deliberately reversed native enumeration. Names and links
        # come from the actual private records already used by native attachment.
        for pointer in reversed(h.pointers):
            node=bytes(self.uc.mem_read(pointer,0x170));name_pointer=struct.unpack_from('<I',node,0xe8)[0]
            i=original[pointer]
            if name_pointer!=self.SOURCE+0x1000+i*64:raise ValueError('Unreviewed supplied name ownership')
            raw=bytes(self.uc.mem_read(name_pointer,64));end=raw.find(b'\0')
            if end<0:raise ValueError('Unterminated supplied model name')
            name=raw[:end].decode('ascii')
            records.append({'pointer':pointer,'bytes':0x170,'name_pointer':name_pointer,'name_bytes':end+1,
                            'name':name,'parent':struct.unpack_from('<I',node,0x108)[0]})
        raw,order,receipt=self.binding.bind(self.STATE+0x100,records)
        if receipt['status'] or order is None:raise ValueError('Compiled native model binding refused')
        self.bound_result=raw;self.binding_receipt=receipt
        self.binding_source_indices=[original[records[i]['pointer']] for i in order]
        # Context points directly into the C-produced, now read-only result.
        # Python does not synthesize a replacement order, parent table or roles.
        for offset,pointer in ((4,self.binding.OUTPUT+8),(12,self.binding.OUTPUT+0x408),(16,self.binding.OUTPUT+0x608)):
            self.uc.mem_write(h.CONTEXT+offset,struct.pack('<I',pointer))

    def check_adapter_success(self):
        h=self.adapter
        if struct.unpack('<2I',self.uc.mem_read(h.CONTEXT+40,8))!=(0,0):raise ValueError('Bound scatter correction failed')
        snapshot=struct.pack('<'+'f'*(h.count*10),*(v for i in self.binding_source_indices for v in self.observed['poses'][i]))
        if bytes(self.uc.mem_read(h.WORK+128*0x170,h.count*40))!=snapshot:
            raise ValueError('Bound scatter poses do not follow the C-produced node order')

    def check_external_guards(self):
        super().check_external_guards()
        if bytes(self.uc.mem_read(self.binding.OUTPUT,OUTPUT_SIZE))!=self.bound_result:
            raise ValueError('Native animation changed immutable compiled binding')

    def run(self,**kwargs):
        result=super().run(**kwargs)
        return {**result,'compiled_model_binding':self.binding_receipt,
            'context_uses_compiled_binding_directly':True,'named_records_enumerated_in_reverse':True,
            'model_identity_and_memory_ownership_supplied':True,'modern_equipment_profile_discovery_qualified':False}
