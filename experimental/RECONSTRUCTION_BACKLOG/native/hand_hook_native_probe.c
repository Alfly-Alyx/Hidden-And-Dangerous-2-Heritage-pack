/* Original console test of the actual C/assembly adapter on invented records.
 * No game code, game file, DLL loading, process access or installed hook.
 */
#include <stdio.h>
#include <string.h>
typedef struct {
    void *model;unsigned char *arena;unsigned bytes;const unsigned *offsets;unsigned count;
    const int *parents;const unsigned *roles;unsigned role_count;const double *rest,*grips;
    float *poses;void *work;unsigned work_bytes,busy,status,calls;
} Context;
int Hd2ConfigureHandHook(Context *);
void Hd2ProbeHandAdapter(void *);
void Hd2ProbeHandRefresh(void);
unsigned char Hd2NativeBefore[108],Hd2NativeRefreshState[108],Hd2NativeAfter[108];
unsigned Hd2NativeControl=0x27f,Hd2NativeRefreshCount,Hd2NativeRefreshModel;
static unsigned char arena[65536],saved[65536];
static double workspace[942],rest[90],grips[30];
static float poses[110];
static unsigned offsets[11],roles[11]={0,1,2,5,9,4,5,6,8,9,10};
static int parents[11]={-1,0,0,-1,3,4,5,-1,7,8,9};
static unsigned vtable[10],model[1],other_model[1];
static Context context;

static void put_float(unsigned at,float value) { memcpy(arena+at,&value,4); }
static void put_word(unsigned at,unsigned value) { memcpy(arena+at,&value,4); }
static void seed(void) {
    unsigned i,j,s;
    memset(arena,0,sizeof(arena));memset(rest,0,sizeof(rest));memset(grips,0,sizeof(grips));
    memset(poses,0x5a,sizeof(poses));memset(&context,0,sizeof(context));
    for(i=0;i<11;i++) {
        offsets[i]=512*i;put_float(offsets[i]+0xcc,1);
        for(j=0;j<3;j++) put_float(offsets[i]+0xd0+4*j,1);
        put_word(offsets[i]+0xe0,8);put_word(offsets[i]+0xf8,10);
    }
    put_float(offsets[1]+0xb0,.4f);put_float(offsets[1]+0xb4,.1f);put_float(offsets[1]+0xb8,.1f);
    put_float(offsets[2]+0xb0,.35f);put_float(offsets[2]+0xb4,-.1f);put_float(offsets[2]+0xb8,.1f);
    put_float(offsets[5]+0xb0,.3f);put_float(offsets[9]+0xb0,.3f);
    put_float(offsets[6]+0xb0,.25f);put_float(offsets[10]+0xb0,.25f);
    for(s=0;s<2;s++) {
        for(i=0;i<3;i++) for(j=0;j<3;j++) rest[45*s+12*i+4*j]=1;
        rest[45*s+21]=(double).3f;rest[45*s+33]=(double).55f;
        for(j=0;j<3;j++) {rest[45*s+36+4*j]=1;grips[15*s+3+4*j]=1;}
    }
    vtable[9]=(unsigned)Hd2ProbeHandRefresh;model[0]=(unsigned)vtable;other_model[0]=(unsigned)vtable;
    context.model=model;context.arena=arena;context.bytes=65536;context.offsets=offsets;context.count=11;
    context.parents=parents;context.roles=roles;context.role_count=11;context.rest=rest;context.grips=grips;
    context.poses=poses;context.work=workspace;context.work_bytes=7536;
}

int main(void) {
    unsigned scenario,expected_status,expected_calls,changed;void *called_model;
    for(scenario=0;scenario<6;scenario++) {
        seed();if(Hd2ConfigureHandHook(&context)) return 10;
        Hd2NativeControl=0x27f;Hd2NativeRefreshCount=0;Hd2NativeRefreshModel=0;
        expected_status=0;expected_calls=1;called_model=model;
        if(scenario==1) {called_model=other_model;expected_calls=0;}
        if(scenario==2) {if(Hd2ConfigureHandHook(0)) return 11;expected_calls=0;}
        if(scenario==3) {context.busy=1;expected_calls=0;}
        if(scenario==4) {Hd2NativeControl=0x37f;expected_status=6;}
        if(scenario==5) {put_word(offsets[10]+0xf8,1);expected_status=43;}
        memcpy(saved,arena,sizeof(arena));Hd2ProbeHandAdapter(called_model);
        if(memcmp(Hd2NativeBefore,Hd2NativeRefreshState,108) || memcmp(Hd2NativeBefore,Hd2NativeAfter,108)) {
            printf("FAIL: x87 state changed in adapter scenario %u\n",scenario);return 20;
        }
        if(Hd2NativeRefreshCount!=1 || Hd2NativeRefreshModel!=(unsigned)called_model
                || context.status!=expected_status || context.calls!=expected_calls) {
            printf("FAIL: adapter scenario %u, status %u, calls %u\n",scenario,context.status,context.calls);return 21;
        }
        changed=memcmp(saved,arena,sizeof(arena))!=0;
        if(changed!=(scenario==0)) {printf("FAIL: arena contract in scenario %u\n",scenario);return 22;}
        if(scenario==3 && Hd2ConfigureHandHook(0)!=1) return 23;
        context.busy=0;if(Hd2ConfigureHandHook(0)) return 24;
    }
    puts("PASS: 6 actual-adapter cases, full 108-byte x87 state, model forwarding and arena refusal");
    return 0;
}
