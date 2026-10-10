#ifndef HD2_HAND_LIFECYCLE_H
#define HD2_HAND_LIFECYCLE_H
#include "hand_scatter_context.h"
typedef int (__attribute__((cdecl)) *Hd2ConfigureHandFunction)(Hd2ScatterHookContext *);
typedef struct {
    Hd2ScatterHookContext *context;
    Hd2ConfigureHandFunction configure;
    unsigned generation,last_event,invalidations;
} Hd2HandLifecycle;
#endif
