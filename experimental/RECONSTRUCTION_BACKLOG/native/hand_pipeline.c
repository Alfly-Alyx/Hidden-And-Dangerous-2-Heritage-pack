/* Original bounded numerical pipeline, not an installed game hook.
 * All buffers must be valid, disjoint, and exclusively caller-owned.
 * node_offsets[count] addresses supplied records inside arena only.
 * poses[count*10] must bit-match every current record's P3/Q4/S3.
 * roles[11]: held root, L/R marker, L/R elbow, then L upper/fore/hand,
 * R upper/fore/hand. The binding and immutable rest identity are supplied,
 * not discovered here. No allocation, system API or persistent state.
 * A failed operation leaves the entire arena unchanged; scratch may change.
 */
int __attribute__((stdcall)) _dllstart(void *module,unsigned reason,void *reserved) { return 0; }
int Hd2PrepareArms(const float *,const int *,unsigned,const unsigned *,const double *,
                   const double *,float *,unsigned,double *,unsigned);
int Hd2SolveArm(const double *,unsigned,int,double *,unsigned);
int Hd2CommitArms(unsigned char *,unsigned,const unsigned *,const float *,const float *,const unsigned *);

typedef struct {
    float world[128*12];
    double inputs[120],rotations[24];
    float before[24],after[24];
    unsigned offsets[6],flags[6];
} Hd2HandWorkspace;

static unsigned readword(const unsigned char *p) {
    return (unsigned)p[0]|((unsigned)p[1]<<8)|((unsigned)p[2]<<16)|((unsigned)p[3]<<24);
}
static unsigned floatword(float value) {
    union { float value;unsigned bits; } u;u.value=value;return u.bits;
}
static double absvalue(double value) { return value<0 ? -value : value; }

/* 0 success; 1 ABI; 2 record offsets/roles; 3 hierarchy;
 * 4 stale pose snapshot; 5 non-resting clavicle basis;
 * 10 + preparation status; 20/30 + L/R solver status;
 * 40 + pose-commit status. No output pose is committed before both arms pass.
 * Workspace must be 8-byte aligned, exactly sizeof(Hd2HandWorkspace)=7536.
 */
int __attribute__((dllexport,cdecl)) Hd2CorrectHandPose(unsigned char *arena,unsigned bytes,
        const unsigned *node_offsets,unsigned count,const float *poses,const int *parents,
        const unsigned *roles,unsigned role_count,const double *rest,const double *grips,
        Hd2HandWorkspace *work,unsigned work_bytes) {
    unsigned i,j,a,b,offset,s,arm;int status,parent;double value;
    if(!arena || !node_offsets || !poses || !parents || !roles || !rest || !grips || !work
            || bytes<11*0x170 || bytes>0x10000 || count<11 || count>128 || role_count!=11
            || ((unsigned)work&7) || work_bytes!=sizeof(Hd2HandWorkspace)) return 1;
    for(i=0;i<count;i++) {
        a=node_offsets[i];if(a%16 || a>bytes-0x170) return 2;
        for(j=0;j<i;j++) {b=node_offsets[j];if(a<b+0x170 && b<a+0x170) return 2;}
    }
    for(i=0;i<11;i++) if(roles[i]>=count) return 2;
    if(roles[3]!=roles[6] || roles[4]!=roles[9]) return 2;
    for(i=5;i<11;i++) {
        for(j=0;j<3;j++) if(roles[i]==roles[j]) return 2;
        for(j=5;j<i;j++) if(roles[i]==roles[j]) return 2;
    }
    for(s=0;s<2;s++) {
        arm=5+3*s;
        if(parents[roles[arm]]<0 || parents[roles[arm]]>=(int)roles[arm]
                || parents[roles[arm+1]]!=(int)roles[arm]
                || parents[roles[arm+2]]!=(int)roles[arm+1]) return 3;
    }
    for(i=0;i<count;i++) for(j=0;j<10;j++) {
        offset=j<3 ? 0xb0+4*j : j<7 ? 0xc0+4*(j-3) : 0xd0+4*(j-7);
        if(readword(arena+node_offsets[i]+offset)!=floatword(poses[10*i+j])) return 4;
    }
    status=Hd2PrepareArms(poses,parents,count,roles,rest,grips,work->world,count*12,work->inputs,120);
    if(status) return 10+status;
    for(s=0;s<2;s++) {
        parent=parents[roles[5+3*s]];
        for(i=0;i<9;i++) {
            value=(double)work->world[12*parent+i]-rest[45*s+36+i];
            if(!(value==value) || absvalue(value)>2e-6) return 5;
        }
        status=Hd2SolveArm(work->inputs+60*s,60,s==0 ? 1 : -1,work->rotations+12*s,12);
        if(status) return (s==0 ? 20 : 30)+status;
    }
    for(i=0;i<6;i++) {
        work->offsets[i]=node_offsets[roles[5+i]];
        work->flags[i]=readword(arena+work->offsets[i]+0xe0);
        for(j=0;j<4;j++) {
            work->before[4*i+j]=poses[10*roles[5+i]+3+j];
            work->after[4*i+j]=(float)work->rotations[4*i+j];
        }
        if(work->after[4*i+3]<0) for(j=0;j<4;j++) work->after[4*i+j]=-work->after[4*i+j];
    }
    status=Hd2CommitArms(arena,bytes,work->offsets,work->before,work->after,work->flags);
    return status ? 40+status : 0;
}
