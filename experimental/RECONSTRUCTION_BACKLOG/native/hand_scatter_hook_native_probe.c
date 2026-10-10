/* Original console-only scatter-adapter probe, invented heap records.
 * No game code, game files, library loading or process injection.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hand_scatter.h"
typedef struct {
    void *model;const Hd2HandNodeView *nodes;unsigned count;const int *parents;const unsigned *roles;
    unsigned role_count;const double *rest,*grips;Hd2HandScatterWorkspace *work;
    unsigned work_bytes,busy,status,calls;
} Context;
int Hd2ConfigureHandHook(Context *);
void Hd2ProbeHandAdapter(void *);
void Hd2ProbeHandRefresh(void);
unsigned char Hd2NativeBefore[108],Hd2NativeRefreshState[108],Hd2NativeAfter[108];
unsigned Hd2NativeControl=0x27f,Hd2NativeRefreshCount,Hd2NativeRefreshModel;
static Hd2HandScatterWorkspace workspace;
static Hd2HandNodeView views[11];
static unsigned char *blocks[11],saved[11][1024];
static double rest[90],grips[30];
static unsigned roles[11]={0,1,2,5,9,4,5,6,8,9,10};
static int parents[11]={-1,0,0,-1,3,4,5,-1,7,8,9};
static unsigned vtable[10],model[1],other[1];
static Context context;
static void putf(unsigned i,unsigned at,float value) {memcpy(views[i].node+at,&value,4);}
static void probe_word(unsigned i,unsigned at,unsigned value) {memcpy(views[i].node+at,&value,4);}
static void seed(void) {
    unsigned i,j,s;
    memset(rest,0,sizeof(rest));memset(grips,0,sizeof(grips));memset(&context,0,sizeof(context));
    for(i=0;i<11;i++) {
        memset(blocks[i],0x5a,0x220+i*0x20);memset(views[i].node,0,0x170);
        putf(i,0xcc,1);for(j=0;j<3;j++) putf(i,0xd0+4*j,1);
        probe_word(i,0xe0,8);probe_word(i,0xf8,10);
        probe_word(i,0x108,parents[i]<0 ? (unsigned)model : (unsigned)views[parents[i]].node);
    }
    putf(1,0xb0,.4f);putf(1,0xb4,.1f);putf(1,0xb8,.1f);
    putf(2,0xb0,.35f);putf(2,0xb4,-.1f);putf(2,0xb8,.1f);
    putf(5,0xb0,.3f);putf(9,0xb0,.3f);putf(6,0xb0,.25f);putf(10,0xb0,.25f);
    for(s=0;s<2;s++) {
        for(i=0;i<3;i++) for(j=0;j<3;j++) rest[45*s+12*i+4*j]=1;
        rest[45*s+21]=(double).3f;rest[45*s+33]=(double).55f;
        for(j=0;j<3;j++) {rest[45*s+36+4*j]=1;grips[15*s+3+4*j]=1;}
    }
    context.model=model;context.nodes=views;context.count=11;context.parents=parents;context.roles=roles;
    context.role_count=11;context.rest=rest;context.grips=grips;context.work=&workspace;context.work_bytes=sizeof(workspace);
}
int main(void) {
    unsigned i,j,k,scenario,status,calls,changed,allowed;void *called;
    vtable[9]=(unsigned)Hd2ProbeHandRefresh;model[0]=(unsigned)vtable;other[0]=(unsigned)vtable;
    for(i=0;i<11;i++) {
        blocks[i]=malloc(0x220+i*0x20);if(!blocks[i]) return 10;
        views[i].node=blocks[i]+4;views[i].bytes=0x170;
    }
    for(scenario=0;scenario<8;scenario++) {
        seed();if(Hd2ConfigureHandHook(&context)) return 11;
        Hd2NativeControl=0x27f;Hd2NativeRefreshCount=0;Hd2NativeRefreshModel=0;called=model;status=0;calls=1;
        if(scenario==1) {called=other;calls=0;}
        if(scenario==2) {if(Hd2ConfigureHandHook(0)) return 12;context.nodes=(void*)0xffffffff;calls=0;}
        if(scenario==3) {context.busy=1;calls=0;}
        if(scenario==4) {Hd2NativeControl=0x37f;status=6;}
        if(scenario==5) {probe_word(10,0xf8,1);status=143;}
        if(scenario==6) {probe_word(10,0x108,0);status=3;}
        if(scenario==7) {context.count=129;status=7;}
        for(i=0;i<11;i++) memcpy(saved[i],blocks[i],0x220+i*0x20);
        Hd2ProbeHandAdapter(called);
        if(memcmp(Hd2NativeBefore,Hd2NativeRefreshState,108) || memcmp(Hd2NativeBefore,Hd2NativeAfter,108)) return 20;
        if(Hd2NativeRefreshCount!=1 || Hd2NativeRefreshModel!=(unsigned)called || context.status!=status || context.calls!=calls) return 21;
        changed=0;
        for(i=0;i<11;i++) for(j=0;j<0x220+i*0x20;j++) if(blocks[i][j]!=saved[i][j]) {
            allowed=0;
            for(k=5;k<11;k++) if(i==roles[k] && ((j>=4+0xc0 && j<4+0xd0) || (j>=4+0xe0 && j<4+0xe4))) allowed=1;
            if(scenario || !allowed) return 22;changed=1;
        }
        if(changed!=(scenario==0)) return 23;
        if(scenario==3 && Hd2ConfigureHandHook(0)!=1) return 24;
        context.busy=0;if(Hd2ConfigureHandHook(0)) return 25;
    }
    for(i=0;i<11;i++) free(blocks[i]);
    puts("PASS: 8 scatter-adapter cases, separate heap records, full 108-byte x87 state and refusal guards");
    return 0;
}
