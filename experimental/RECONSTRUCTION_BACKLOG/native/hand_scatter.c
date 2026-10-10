/* Original gather/solve/checked scatter for non-contiguous supplied records.
 * All native destinations are checked before any write to any native record.
 * This is a single-thread ownership contract, NOT an atomic transaction and
 * NOT a test that an arbitrary pointer is mapped or belongs to a live model.
 */
#include "hand_scatter.h"
int Hd2CorrectHandPose(unsigned char *,unsigned,const unsigned *,unsigned,const float *,const int *,
        const unsigned *,unsigned,const double *,const double *,void *,unsigned);

static unsigned getword(const unsigned char *p) {
    return (unsigned)p[0]|((unsigned)p[1]<<8)|((unsigned)p[2]<<16)|((unsigned)p[3]<<24);
}
static void putword(unsigned char *p,unsigned v) {
    p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);
}
static unsigned pose_offset(unsigned j) { return j<3 ? 0xb0+4*j : j<7 ? 0xc0+4*(j-3) : 0xd0+4*(j-7); }

/* 0 success; 1 ABI; 2 record bounds/overlap; 3 current parent linkage;
 * 4 changed snapshot before scatter; 100 + numerical pipeline refusal.
 * Roots must be immediate children of the supplied (opaque) model identity.
 * Every parent precedes its child. Only the six selected arm Q/flags are written.
 */
int __attribute__((dllexport,cdecl)) Hd2CorrectScatteredHandPose(void *model,
        const Hd2HandNodeView *nodes,unsigned count,const int *parents,const unsigned *roles,
        unsigned role_count,const double *rest,const double *grips,Hd2HandScatterWorkspace *work,unsigned work_bytes) {
    unsigned i,j,a,b,n,offset,value,expected;int status;
    union { unsigned bits;float value; } convert;
    if(!model || !nodes || !parents || !roles || !rest || !grips || !work || count<11 || count>128
            || role_count!=11 || ((unsigned)work&7) || work_bytes!=sizeof(Hd2HandScatterWorkspace)) return 1;
    for(i=0;i<count;i++) {
        a=(unsigned)nodes[i].node;n=nodes[i].bytes;
        if(a<0x1000 || (a&3) || n<0x10c || n>0x10000 || a>0xffffffffu-n) return 2;
        if((unsigned)model>=a && (unsigned)model<a+n) return 2;
        for(j=0;j<i;j++) {
            b=(unsigned)nodes[j].node;if(a<b+nodes[j].bytes && b<a+n) return 2;
        }
    }
    for(i=0;i<count;i++) {
        if(parents[i]<-1 || parents[i]>=(int)i) return 3;
        expected=parents[i]<0 ? (unsigned)model : (unsigned)nodes[parents[i]].node;
        if(getword(nodes[i].node+0x108)!=expected) return 3;
    }
    for(i=0;i<count;i++) {
        offset=i*0x170;work->offsets[i]=offset;
        for(j=0;j<0x170;j+=4) putword(work->arena+offset+j,0);
        for(j=0;j<10;j++) {
            a=pose_offset(j);value=getword(nodes[i].node+a);
            putword(work->arena+offset+a,value);convert.bits=value;work->poses[10*i+j]=convert.value;
        }
        work->flags[i]=getword(nodes[i].node+0xe0);
        work->kinds[i]=getword(nodes[i].node+0xf8);
        work->parent_pointers[i]=getword(nodes[i].node+0x108);
        putword(work->arena+offset+0xe0,work->flags[i]);putword(work->arena+offset+0xf8,work->kinds[i]);
    }
    status=Hd2CorrectHandPose(work->arena,count*0x170,work->offsets,count,work->poses,parents,
        roles,role_count,rest,grips,work->pipeline,sizeof(work->pipeline));
    if(status) return 100+status;
    /* The full collection is rechecked, including markers and late destinations.
     * No partial left-arm write precedes a changed right-arm snapshot. */
    for(i=0;i<count;i++) {
        if(getword(nodes[i].node+0xe0)!=work->flags[i] || getword(nodes[i].node+0xf8)!=work->kinds[i]
                || getword(nodes[i].node+0x108)!=work->parent_pointers[i]) return 4;
        for(j=0;j<10;j++) {
            convert.value=work->poses[10*i+j];
            if(getword(nodes[i].node+pose_offset(j))!=convert.bits) return 4;
        }
    }
    for(i=5;i<11;i++) {
        n=roles[i];offset=work->offsets[n];
        for(j=0;j<4;j++) putword(nodes[n].node+0xc0+4*j,getword(work->arena+offset+0xc0+4*j));
        putword(nodes[n].node+0xe0,getword(work->arena+offset+0xe0));
    }
    return 0;
}

unsigned __attribute__((dllexport,cdecl)) Hd2HandScatterWorkspaceSize(void) { return sizeof(Hd2HandScatterWorkspace); }
