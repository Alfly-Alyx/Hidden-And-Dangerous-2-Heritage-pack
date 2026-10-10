/* Supplied, exclusively owned spans; no arbitrary process-memory probing. */
#include "hand_model_binding.h"
typedef struct {
    Hd2NamedHandNode ordered[128];
    Hd2HandModelBinding pending;
    Hd2HandBindingWorkspace binding;
    unsigned source_indices[128],pointers[128];
} Hd2HandCollectionWorkspace;

int Hd2CollectHandModelBinding(const unsigned char *,unsigned,const unsigned *,unsigned,
        const Hd2NamedHandNode *,unsigned,Hd2HandModelBinding *,unsigned,Hd2HandCollectionWorkspace *,unsigned);
