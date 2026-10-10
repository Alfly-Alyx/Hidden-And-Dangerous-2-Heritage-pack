/* Original diagnostic post-blend adapter. Never installs or patches a hook.
 * Context and every referenced buffer must be valid, disjoint and exclusively
 * owned on one thread. Registration/lifetime of a real model is NOT implemented.
 * The diagnostic owner must unregister before releasing/reusing the model.
 */
int Hd2CorrectHandPose(unsigned char *,unsigned,const unsigned *,unsigned,const float *,const int *,
        const unsigned *,unsigned,const double *,const double *,void *,unsigned);
void Hd2AfterHandPose(void);

typedef struct {
    void *model;
    unsigned char *arena;
    unsigned bytes;
    const unsigned *offsets;
    unsigned count;
    const int *parents;
    const unsigned *roles;
    unsigned role_count;
    const double *rest,*grips;
    float *poses;
    void *work;
    unsigned work_bytes;
    unsigned busy,status,calls;
} Hd2HandHookContext;

static Hd2HandHookContext *active_context;
static unsigned word(const unsigned char *p) {
    return (unsigned)p[0]|((unsigned)p[1]<<8)|((unsigned)p[2]<<16)|((unsigned)p[3]<<24);
}
static int bounded(const Hd2HandHookContext *c) {
    unsigned i,j,a,b;
    if(!c->model || !c->arena || !c->offsets || !c->parents || !c->roles || !c->rest || !c->grips
            || !c->poses || !c->work || c->count<11 || c->count>128 || c->bytes<11*0x170
            || c->bytes>0x10000 || c->role_count!=11 || c->work_bytes!=7536 || ((unsigned)c->work&7)) return 0;
    for(i=0;i<c->count;i++) {
        a=c->offsets[i];if(a%16 || a>c->bytes-0x170) return 0;
        for(j=0;j<i;j++) {b=c->offsets[j];if(a<b+0x170 && b<a+0x170) return 0;}
    }
    return 1;
}

/* No synchronization primitive: caller serializes registration and callbacks.
 * 0 success; 1 callback active; 2 invalid caller-owned diagnostic context. */
int __attribute__((dllexport,cdecl)) Hd2ConfigureHandHook(Hd2HandHookContext *context) {
    if(active_context && active_context->busy) return 1;
    if(context && (context->busy || !bounded(context))) return 2;
    active_context=context;
    if(context) {context->status=0;context->calls=0;}
    return 0;
}

/* The assembler passes the original x87 control word. Unsupported precision
 * deliberately skips correction; FPU state is restored by the adapter.
 * status 6 means unsupported FPU state, 7 invalidated bounded context. */
void __attribute__((cdecl)) Hd2OnModelHandPose(void *model,unsigned control) {
    Hd2HandHookContext *c=active_context;unsigned i,j,offset;union { unsigned bits;float value; } u;
    if(!c || c->model!=model || c->busy) return;
    c->busy=1;c->calls++;
    if(control!=0x27f) c->status=6;
    else if(!bounded(c)) c->status=7;
    else {
        for(i=0;i<c->count;i++) for(j=0;j<10;j++) {
            offset=j<3 ? 0xb0+4*j : j<7 ? 0xc0+4*(j-3) : 0xd0+4*(j-7);
            u.bits=word(c->arena+c->offsets[i]+offset);c->poses[10*i+j]=u.value;
        }
        c->status=Hd2CorrectHandPose(c->arena,c->bytes,c->offsets,c->count,c->poses,c->parents,
            c->roles,c->role_count,c->rest,c->grips,c->work,c->work_bytes);
    }
    c->busy=0;
}

unsigned __attribute__((dllexport,cdecl)) Hd2HandHookEntry(void) { return (unsigned)Hd2AfterHandPose; }
