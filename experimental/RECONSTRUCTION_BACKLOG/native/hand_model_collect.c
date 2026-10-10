/* Original collection from the reviewed model frame-vector layout.
 * Caller first establishes ownership and readable extents for model, vector,
 * every node and every name. The vector is never used to dereference an address
 * not present exactly once in that supplied ownership collection.
 * No allocation, OS call, native record mutation, or lifetime claim.
 */
#include "hand_model_collect.h"
static unsigned word(const unsigned char *p) {
    return (unsigned)p[0]|((unsigned)p[1]<<8)|((unsigned)p[2]<<16)|((unsigned)p[3]<<24);
}
static int span(const void *pointer,unsigned bytes,unsigned minimum) {
    unsigned p=(unsigned)pointer;
    return p>=0x1000 && !(p&3) && bytes>=minimum && bytes<=0x10000 && p<=0xffffffffu-bytes;
}

/* 0 success; 1 ABI; 2 model/vector kind, identity or bounds;
 * 3 incomplete, duplicate or foreign vector membership;
 * 4 model/vector changed before commit; 10 + named binding status.
 * Native model: kind at +f8, frame vector +120, count +128.
 */
int __attribute__((dllexport,cdecl)) Hd2CollectHandModelBinding(const unsigned char *model,unsigned model_bytes,
        const unsigned *vector,unsigned vector_bytes,const Hd2NamedHandNode *owned,unsigned owned_count,
        Hd2HandModelBinding *output,unsigned output_bytes,Hd2HandCollectionWorkspace *work,unsigned work_bytes) {
    unsigned count,kind,i,j,matches,index,p;
    int status;
    if(!owned || !output || !work || ((unsigned)output&3) || ((unsigned)work&3)
            || owned_count<11 || owned_count>128 || output_bytes!=sizeof(Hd2HandModelBinding)
            || work_bytes!=sizeof(Hd2HandCollectionWorkspace)) return 1;
    if(!span(model,model_bytes,0x12c) || !span(vector,vector_bytes,11*4)) return 2;
    kind=word(model+0xf8);count=word(model+0x128);
    if((kind&0xffff)!=9 || word(model+0x120)!=(unsigned)vector || count<11 || count>128
            || count!=owned_count || count>vector_bytes/4) return 2;
    for(i=0;i<count;i++) {
        p=word((const unsigned char*)vector+4*i);matches=0;index=0;
        for(j=0;j<owned_count;j++) if((unsigned)owned[j].record.node==p) {matches++;index=j;}
        if(matches!=1) return 3;
        for(j=0;j<i;j++) if(work->source_indices[j]==index) return 3;
        work->source_indices[i]=index;work->pointers[i]=p;
        work->ordered[i].record.node=owned[index].record.node;work->ordered[i].record.bytes=owned[index].record.bytes;
        work->ordered[i].name=owned[index].name;work->ordered[i].name_bytes=owned[index].name_bytes;
    }
    status=Hd2BuildHandModelBinding((void*)model,work->ordered,count,&work->pending,sizeof(work->pending),
            &work->binding,sizeof(work->binding));
    if(status) return 10+status;
    if(word(model+0xf8)!=kind || word(model+0x120)!=(unsigned)vector || word(model+0x128)!=count) return 4;
    for(i=0;i<count;i++) if(word((const unsigned char*)vector+4*i)!=work->pointers[i]) return 4;
    for(i=0;i<sizeof(Hd2HandModelBinding);i++) ((unsigned char*)output)[i]=((unsigned char*)&work->pending)[i];
    return 0;
}

unsigned __attribute__((dllexport,cdecl)) Hd2HandCollectionWorkspaceSize(void) {return sizeof(Hd2HandCollectionWorkspace);}
