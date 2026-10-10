"""Bounded original collector of the native model's supplied frame vector."""
import struct

from native_hand_model_binding import HandModelBindingOracle,OUTPUT_SIZE,reference_binding

BASE=0x30000000
BINARY_SIZE=7168
BINARY_SHA='05bfa7667cfb0adc7bf61662930ad0f46c94620ca4b29fba16c45522c2d5b7a9'
CODE_END=BASE+0x22a8
SNAPSHOT_CHECK=BASE+0x2183
WORK_SIZE=8296
EXPORTS={b'Hd2BuildHandModelBinding':0x11b9,b'Hd2CollectHandModelBinding':0x1dff,
         b'Hd2HandBindingWorkspaceSize':0x1d3f,b'Hd2HandCollectionWorkspaceSize':0x2295,
         b'Hd2HandModelBindingSize':0x1d2e}


class HandModelCollectionOracle(HandModelBindingOracle):
    BASE=BASE;BINARY_SIZE=BINARY_SIZE;BINARY_SHA=BINARY_SHA;CODE_END=CODE_END;SNAPSHOT_CHECK=SNAPSHOT_CHECK
    EXPORTS=EXPORTS;WORK_SIZE=WORK_SIZE;WORK_MAP_SIZE=0x3000;VECTOR=0x5800000
    ARGUMENTS={b'Hd2CollectHandModelBinding':10,b'Hd2HandCollectionWorkspaceSize':0,b'Hd2HandModelBindingSize':0}

    def __init__(self,raw,parent=None):
        super().__init__(raw,parent)
        if parent is None:
            for at in (self.MODEL,self.VECTOR):self.uc.mem_map(at,4096,self.uni.UC_PROT_READ)

    def bind(self,*args,**kwargs):
        raise ValueError('Collection requires explicit owned model and vector extents')

    def collect(self,model,model_bytes,vector,vector_bytes,records,*,overrides=None):
        if (self.active or any(type(p) is not int or not 0x1000<=p<=0xffffffff or p&3 for p in (model,vector))
                or any(type(n) is not int or not 0<=n<=0x10000 for n in (model_bytes,vector_bytes))
                or not isinstance(records,list) or not 11<=len(records)<=128):
            raise ValueError('Invalid collection fixture')
        source=bytearray(4096)
        for i,row in enumerate(records):struct.pack_into('<4I',source,i*16,row['pointer'],row['bytes'],row['name_pointer'],row['name_bytes'])
        args=[model,model_bytes,vector,vector_bytes,self.INPUT,len(records),self.OUTPUT,OUTPUT_SIZE,self.WORK,WORK_SIZE]
        if overrides:
            if any(type(i) is not int or i not in (0,1,2,3,5,7,9) or type(v) is not int for i,v in overrides.items()):
                raise ValueError('Unreviewed collection ABI override')
            for i,v in overrides.items():args[i]=v
        before=[(model,bytes(self.uc.mem_read(model,model_bytes))),(vector,bytes(self.uc.mem_read(vector,vector_bytes)))]
        mutation=self.late_fault
        self.uc.mem_write(self.INPUT,bytes(source));self.uc.mem_protect(self.OUTPUT,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.uc.mem_write(self.OUTPUT,b'Z'*4096);self.uc.mem_write(self.WORK,b'Z'*self.WORK_MAP_SIZE)
        for name,size in ((b'Hd2HandModelBindingSize',OUTPUT_SIZE),(b'Hd2HandCollectionWorkspaceSize',WORK_SIZE)):
            if self.invoke(BASE+EXPORTS[name],[])!=size:raise ValueError('Collection workspace/output ABI differs')
        status=self.invoke(BASE+EXPORTS[b'Hd2CollectHandModelBinding'],args)
        raw=bytes(self.uc.mem_read(self.OUTPUT,OUTPUT_SIZE))
        if (bytes(self.uc.mem_read(self.INPUT,4096))!=bytes(source)
                or bytes(self.uc.mem_read(self.OUTPUT+OUTPUT_SIZE,4096-OUTPUT_SIZE))!=b'Z'*(4096-OUTPUT_SIZE)
                or bytes(self.uc.mem_read(self.WORK+WORK_SIZE,self.WORK_MAP_SIZE-WORK_SIZE))!=b'Z'*(self.WORK_MAP_SIZE-WORK_SIZE)
                or (status and (raw!=b'Z'*OUTPUT_SIZE or self.output_writes))):
            raise ValueError('Collection changed input/guard or failed output')
        for at,snapshot in before:
            expected=bytearray(snapshot)
            if self.injected and mutation is not None and at<=mutation[0] and mutation[0]+4<=at+len(expected):
                struct.pack_into('<I',expected,mutation[0]-at,mutation[1])
            if bytes(self.uc.mem_read(at,len(expected)))!=bytes(expected):raise ValueError('Collection wrote native model/vector')
        order=None
        if not status:
            pointers=struct.unpack('<'+'I'*len(records),before[1][1][:len(records)*4])
            supplied={row['pointer']:i for i,row in enumerate(records)}
            vector_indices=[supplied[p] for p in pointers]
            expected,ordered=reference_binding(model,[records[i] for i in vector_indices])
            if raw!=expected:raise ValueError('Compiled collection differs from model-vector reference')
            order=[vector_indices[i] for i in ordered]
        self.uc.mem_protect(self.OUTPUT,4096,self.uni.UC_PROT_READ)
        return raw,order,{'status':status,'compiled_calls':dict(self.calls),'output_write_operations':self.output_writes,
            'source_and_guards_unchanged':True,'failed_output_unchanged':True,'native_nodes_not_written':True,
            'native_model_vector_collected':True,'adversarial_vector_change_injected':self.injected,
            'memory_ownership_supplied':True,'live_model_discovery_implemented':False,'game_started':False}
