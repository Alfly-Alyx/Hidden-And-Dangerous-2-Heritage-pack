/* Original registered adapter for supplied non-contiguous model nodes.
 * Never installs a hook. Caller serializes access and unregisters BEFORE any
 * model/node/input release, reuse or replacement. No live discovery is implied.
 */
#include "hand_scatter_context.h"
void Hd2AfterHandPose(void);
static Hd2ScatterHookContext *active_context;

static int bounded(const Hd2ScatterHookContext *c) {
    return c->model && c->nodes && c->parents && c->roles && c->rest && c->grips && c->work
        && c->count>=11 && c->count<=128 && c->role_count==11
        && !((unsigned)c->work&7) && c->work_bytes==sizeof(Hd2HandScatterWorkspace);
}

/* Registration checks context shape only. Record bounds, linkage and numerical
 * validity are checked on each callback by the scatter bridge before writing.
 * 0 success; 1 old callback busy; 2 invalid or busy new context. */
int __attribute__((dllexport,cdecl)) Hd2ConfigureHandHook(Hd2ScatterHookContext *context) {
    if(active_context && active_context->busy) return 1;
    if(context && (context->busy || !bounded(context))) return 2;
    active_context=context;
    if(context) {context->status=0;context->calls=0;}
    return 0;
}

void __attribute__((cdecl)) Hd2OnModelHandPose(void *model,unsigned control) {
    Hd2ScatterHookContext *c=active_context;
    if(!c || c->model!=model || c->busy) return;
    c->busy=1;c->calls++;
    if(control!=0x27f) c->status=6;
    else if(!bounded(c)) c->status=7;
    else c->status=Hd2CorrectScatteredHandPose(model,c->nodes,c->count,c->parents,c->roles,
        c->role_count,c->rest,c->grips,c->work,c->work_bytes);
    c->busy=0;
}

unsigned __attribute__((dllexport,cdecl)) Hd2HandHookEntry(void) { return (unsigned)Hd2AfterHandPose; }
