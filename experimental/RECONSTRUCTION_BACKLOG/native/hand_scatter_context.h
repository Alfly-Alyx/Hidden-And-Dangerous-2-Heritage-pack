#ifndef HD2_HAND_SCATTER_CONTEXT_H
#define HD2_HAND_SCATTER_CONTEXT_H
#include "hand_scatter.h"
typedef struct {
    void *model;
    const Hd2HandNodeView *nodes;
    unsigned count;
    const int *parents;
    const unsigned *roles;
    unsigned role_count;
    const double *rest,*grips;
    Hd2HandScatterWorkspace *work;
    unsigned work_bytes,busy,status,calls;
} Hd2ScatterHookContext;
#endif
