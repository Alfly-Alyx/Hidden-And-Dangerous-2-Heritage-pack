/* Original parent-change guard sharing the existing caller-owned lifecycle
 * state. No native object is dereferenced. The diagnostic shim must not be
 * installed in a game: refusal stops the private emulator before mutation.
 */
#include "hand_lifecycle.h"
void Hd2BeforeNativeParentChange(void);
static Hd2HandLifecycle *watched;

int __attribute__((stdcall)) _dllstart(void *module,unsigned reason,void *reserved) {return 0;}

int __attribute__((dllexport,cdecl)) Hd2ConfigureParentHooks(Hd2HandLifecycle *state,unsigned bytes) {
    if(watched && watched->context) return 1;
    if(state && (((unsigned)state&3) || bytes!=sizeof(Hd2HandLifecycle) || state->context || state->configure)) return 2;
    if(!state && bytes) return 2;
    watched=state;return 0;
}

/* 0 unrelated/inactive; 1 retired; 2 registry busy; 3 invalid contract.
 * Null new_parent means detach. Retire conservatively even for a no-op request.
 * Both the moved frame and the destination may affect the watched hierarchy.
 * Event 4 is reserved for parent changes; generations remain caller-controlled.
 */
int __attribute__((dllexport,cdecl)) Hd2BeforeHandParentChange(Hd2HandLifecycle *state,unsigned bytes,
        void *frame,void *new_parent) {
    Hd2ScatterHookContext *context;
    unsigned i,matched;
    if(!state || ((unsigned)state&3) || bytes!=sizeof(Hd2HandLifecycle) || !frame) return 3;
    context=state->context;
    if(!context) return state->configure ? 3 : 0;
    if(!state->configure || !context->model || !context->nodes || ((unsigned)context->nodes&3)
            || context->count<11 || context->count>128) return 3;
    matched=frame==context->model || new_parent==context->model;
    if(!matched) for(i=0;i<context->count;i++) {
        void *node=context->nodes[i].node;
        if(node==frame || (new_parent && node==new_parent)) {matched=1;break;}
    }
    if(!matched) return 0;
    if(state->configure(0)) return 2;
    state->context=0;state->configure=0;state->last_event=4;
    if(state->invalidations!=0xffffffffu) state->invalidations++;
    return 1;
}

int __attribute__((cdecl)) Hd2BeforeParentEvent(void *frame,void *new_parent) {
    if(!watched) return 0;
    return Hd2BeforeHandParentChange(watched,sizeof(Hd2HandLifecycle),frame,new_parent);
}

unsigned __attribute__((dllexport,cdecl)) Hd2ParentHookEntry(void) {return (unsigned)Hd2BeforeNativeParentChange;}
