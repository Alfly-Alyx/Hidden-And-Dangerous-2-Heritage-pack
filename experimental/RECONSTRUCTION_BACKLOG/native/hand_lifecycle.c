/* Original explicit lifetime guard. The caller owns and serializes all state,
 * context, node views and the reviewed configure function. Registration must
 * be controlled exclusively through this guard while watched. No native object
 * is dereferenced here; identities are compared against supplied owned views.
 * A refusal MUST prevent the caller from forwarding a native mutation/release.
 * This component does not install or discover client lifecycle hooks.
 */
#include "hand_lifecycle.h"

int __attribute__((stdcall)) _dllstart(void *module,unsigned reason,void *reserved) {return 0;}

static int valid(Hd2HandLifecycle *state,unsigned bytes) {
    return state && !((unsigned)state&3) && bytes==sizeof(Hd2HandLifecycle);
}

/* 0 watched; 1 occupied; 2 ABI; 3 native registry refused; 4 generation exhausted.
 * Begin with a caller-zeroed state. A fresh registration is always explicit. */
int __attribute__((dllexport,cdecl)) Hd2WatchHandContext(Hd2HandLifecycle *state,unsigned bytes,
        Hd2ScatterHookContext *context,Hd2ConfigureHandFunction configure) {
    if(!valid(state,bytes) || !context || ((unsigned)context&3) || !configure) return 2;
    if(state->context || state->configure) return 1;
    if(state->generation==0xffffffffu) return 4;
    if(configure(context)) return 3;
    state->context=context;state->configure=configure;state->generation++;state->last_event=0;
    return 0;
}

/* event: 1 model-add, 2 model-remove, 3 object-release.
 * add/remove supply model and node; release supplies object in model, node=0.
 * 0 unrelated/inactive; 1 invalidated; 2 registry refused; 3 invalid contract.
 * Retire on ANY matching release, not only a final reference: conservative.
 */
int __attribute__((dllexport,cdecl)) Hd2BeforeHandModelChange(Hd2HandLifecycle *state,unsigned bytes,
        void *model,void *node,unsigned event) {
    Hd2ScatterHookContext *context;
    void *target;
    unsigned i,matched;
    if(!valid(state,bytes) || !model || event<1 || event>3 || (event==3 ? node!=0 : node==0)) return 3;
    context=state->context;
    if(!context) return state->configure ? 3 : 0;
    if(!state->configure || !context->model || !context->nodes || ((unsigned)context->nodes&3)
            || context->count<11 || context->count>128) return 3;
    matched=model==context->model;
    target=event==3 ? model : node;
    if(!matched) for(i=0;i<context->count;i++) if(context->nodes[i].node==target) {matched=1;break;}
    if(!matched) return 0;
    if(state->configure(0)) return 2;
    state->context=0;state->configure=0;state->last_event=event;
    if(state->invalidations!=0xffffffffu) state->invalidations++;
    return 1;
}

unsigned __attribute__((dllexport,cdecl)) Hd2HandLifecycleSize(void) {return sizeof(Hd2HandLifecycle);}
