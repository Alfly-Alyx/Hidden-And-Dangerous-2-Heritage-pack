/* Original named-record binding. All record/name spans are validated and owned
 * by the caller for the whole operation; this API does not query live memory.
 */
#include "hand_scatter.h"
typedef struct {
    Hd2HandNodeView record;
    const unsigned char *name;
    unsigned name_bytes; /* Includes final NUL, maximum 64 bytes. */
} Hd2NamedHandNode;
typedef struct {
    void *model;
    unsigned count;
    Hd2HandNodeView nodes[128];
    int parents[128];
    unsigned roles[11];
} Hd2HandModelBinding;
typedef struct {
    Hd2HandModelBinding result;
    unsigned source_indices[128],emitted[128],kinds[128];
    int source_parents[128];
} Hd2HandBindingWorkspace;

int Hd2BuildHandModelBinding(void *,const Hd2NamedHandNode *,unsigned,Hd2HandModelBinding *,unsigned,
        Hd2HandBindingWorkspace *,unsigned);
