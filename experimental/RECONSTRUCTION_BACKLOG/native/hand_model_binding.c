/* Original deterministic binding of supplied named native records.
 * No native record is written. The output is committed only after all checks.
 * The caller supplies live, disjoint, stable record/name spans and separately
 * establishes which modern equipment profile owns this model. Names alone are
 * NOT permission to enable a gameplay feature on an arbitrary loaded model.
 */
#include "hand_model_binding.h"
int __attribute__((stdcall)) _dllstart(void *module,unsigned reason,void *reserved) { return 0; }
static unsigned word(const unsigned char *p) {
    return (unsigned)p[0]|((unsigned)p[1]<<8)|((unsigned)p[2]<<16)|((unsigned)p[3]<<24);
}
static unsigned fold(unsigned c) {return c>='A' && c<='Z' ? c+32 : c;}
static int equal_folded(const unsigned char *a,const unsigned char *b,unsigned bytes) {
    unsigned i;for(i=0;i<bytes;i++) if(fold(a[i])!=fold(b[i])) return 0;return 1;
}
static int exact_name(const Hd2NamedHandNode *node,const char *expected) {
    unsigned i;for(i=0;i<node->name_bytes;i++) {
        if(node->name[i]!=(unsigned char)expected[i]) return 0;
        if(!expected[i]) return i+1==node->name_bytes;
    }
    return 0;
}
static const char *role_names[11]={"fpv_weapon","MOD_left_hand","MOD_right_hand",
    "Bip01 L Forearm","Bip01 R Forearm","Bip01 L UpperArm","Bip01 L Forearm","Bip01 L Hand",
    "Bip01 R UpperArm","Bip01 R Forearm","Bip01 R Hand"};

/* 0 success; 1 ABI; 2 spans/overlap; 3 outside parent or cycle;
 * 4 malformed/ambiguous names; 5 missing role, kind or arm/marker linkage;
 * 6 native metadata changed before output commit.
 */
int __attribute__((dllexport,cdecl)) Hd2BuildHandModelBinding(void *model,
        const Hd2NamedHandNode *input,unsigned count,Hd2HandModelBinding *output,unsigned output_bytes,
        Hd2HandBindingWorkspace *work,unsigned work_bytes) {
    unsigned i,j,k,a,b,n,p,done,found,progress,at;int parent;
    Hd2HandModelBinding *result;
    if(!model || !input || !output || !work || count<11 || count>128 || ((unsigned)output&3)
            || ((unsigned)work&3) || output_bytes!=sizeof(Hd2HandModelBinding)
            || work_bytes!=sizeof(Hd2HandBindingWorkspace)) return 1;
    for(i=0;i<count;i++) {
        a=(unsigned)input[i].record.node;n=input[i].record.bytes;
        b=(unsigned)input[i].name;p=input[i].name_bytes;
        if(a<0x1000 || (a&3) || n<0x10c || n>0x10000 || a>0xffffffffu-n
                || b<0x1000 || p<1 || p>64 || b>0xffffffffu-p) return 2;
        if((unsigned)model>=a && (unsigned)model<a+n) return 2;
        for(j=0;j<i;j++) {
            b=(unsigned)input[j].record.node;
            if(a<b+input[j].record.bytes && b<a+n) return 2;
        }
    }
    for(i=0;i<count;i++) {
        p=input[i].name_bytes;
        if(word(input[i].record.node+0xe8)!=(unsigned)input[i].name || input[i].name[p-1]) return 4;
        for(j=0;j+1<p;j++) if(input[i].name[j]<32 || input[i].name[j]>126) return 4;
        for(j=0;j<i;j++) if(p==input[j].name_bytes && equal_folded(input[i].name,input[j].name,p)) return 4;
        a=word(input[i].record.node+0x108);parent=-2;
        if(a==(unsigned)model) parent=-1;
        else for(j=0;j<count;j++) if(a==(unsigned)input[j].record.node) {parent=(int)j;break;}
        if(parent==-2) return 3;
        work->source_parents[i]=parent;work->emitted[i]=0;work->kinds[i]=word(input[i].record.node+0xf8);
    }
    result=&work->result;
    for(i=0;i<sizeof(Hd2HandModelBinding);i++) ((unsigned char*)result)[i]=0;
    result->model=model;result->count=count;done=0;
    while(done<count) {
        progress=0;
        for(i=0;i<count;i++) if(!work->emitted[i]) {
            parent=work->source_parents[i];
            if(parent>=0 && !work->emitted[parent]) continue;
            result->nodes[done].node=input[i].record.node;result->nodes[done].bytes=input[i].record.bytes;
            result->parents[done]=parent<0 ? -1 : (int)work->emitted[parent]-1;
            work->source_indices[done]=i;work->emitted[i]=done+1;done++;progress=1;
        }
        if(!progress) return 3;
    }
    for(k=0;k<11;k++) {
        found=0;
        for(i=0;i<count;i++) if(exact_name(input+work->source_indices[i],role_names[k])) {
            result->roles[k]=i;found++;
        }
        if(found!=1) return 5;
    }
    if(result->parents[result->roles[0]]!=-1 || result->parents[result->roles[1]]!=(int)result->roles[0]
            || result->parents[result->roles[2]]!=(int)result->roles[0]) return 5;
    for(k=0;k<2;k++) {
        at=5+3*k;parent=result->parents[result->roles[at]];
        if(parent<0 || !exact_name(input+work->source_indices[parent],k ? "Bip01 R Clavicle" : "Bip01 L Clavicle")
                || result->parents[result->roles[at+1]]!=(int)result->roles[at]
                || result->parents[result->roles[at+2]]!=(int)result->roles[at+1]) return 5;
        for(i=0;i<3;i++) if(work->kinds[work->source_indices[result->roles[at+i]]]!=10) return 5;
    }
    for(i=0;i<count;i++) {
        parent=work->source_parents[i];a=parent<0 ? (unsigned)model : (unsigned)input[parent].record.node;
        if(word(input[i].record.node+0x108)!=a || word(input[i].record.node+0xe8)!=(unsigned)input[i].name
                || word(input[i].record.node+0xf8)!=work->kinds[i]) return 6;
    }
    for(i=0;i<sizeof(Hd2HandModelBinding);i++) ((unsigned char*)output)[i]=((unsigned char*)result)[i];
    return 0;
}

unsigned __attribute__((dllexport,cdecl)) Hd2HandModelBindingSize(void) {return sizeof(Hd2HandModelBinding);}
unsigned __attribute__((dllexport,cdecl)) Hd2HandBindingWorkspaceSize(void) {return sizeof(Hd2HandBindingWorkspace);}
