/* Original diagnostic lifecycle delivery. No installation or process access.
 * One caller-owned guard state, configured before watching a context. The
 * assembly interceptors stop with UD2 on a guard refusal; such a stop must
 * never be installed in a game. Client error handling remains unqualified.
 */
#include "hand_lifecycle.h"
int Hd2BeforeHandModelChange(Hd2HandLifecycle *,unsigned,void *,void *,unsigned);
void Hd2BeforeNativeModelAdd(void);
void Hd2BeforeNativeModelRemove(void);
void Hd2BeforeNativeObjectRelease(void);
static Hd2HandLifecycle *watched;

int __attribute__((dllexport,cdecl)) Hd2ConfigureLifecycleHooks(Hd2HandLifecycle *state,unsigned bytes) {
    if(watched && watched->context) return 1;
    if(state && (((unsigned)state&3) || bytes!=sizeof(Hd2HandLifecycle) || state->context || state->configure)) return 2;
    if(!state && bytes) return 2;
    watched=state;return 0;
}

int __attribute__((cdecl)) Hd2BeforeLifecycleEvent(void *model,void *node,unsigned event) {
    if(!watched) return 0;
    return Hd2BeforeHandModelChange(watched,sizeof(Hd2HandLifecycle),model,node,event);
}

unsigned __attribute__((dllexport,cdecl)) Hd2LifecycleAddEntry(void) {return (unsigned)Hd2BeforeNativeModelAdd;}
unsigned __attribute__((dllexport,cdecl)) Hd2LifecycleRemoveEntry(void) {return (unsigned)Hd2BeforeNativeModelRemove;}
unsigned __attribute__((dllexport,cdecl)) Hd2LifecycleReleaseEntry(void) {return (unsigned)Hd2BeforeNativeObjectRelease;}
