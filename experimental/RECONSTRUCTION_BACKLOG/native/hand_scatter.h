/* Original caller-owned scatter bridge. Not an engine pointer discovery API.
 * Every view and input must remain valid, disjoint and exclusively owned for
 * the complete call. No concurrent mutation, free or model replacement allowed.
 */
typedef struct {
    unsigned char *node;
    unsigned bytes;
} Hd2HandNodeView;

typedef struct {
    unsigned char arena[128*0x170];
    float poses[128*10];
    unsigned offsets[128],flags[128],kinds[128],parent_pointers[128];
    double pipeline[942];
} Hd2HandScatterWorkspace;

int Hd2CorrectScatteredHandPose(void *,const Hd2HandNodeView *,unsigned,const int *,
        const unsigned *,unsigned,const double *,const double *,Hd2HandScatterWorkspace *,unsigned);
