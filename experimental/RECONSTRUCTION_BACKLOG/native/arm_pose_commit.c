/* Original bounded pose commit, not a loader or live game hook.
 * Caller supplies a private, exclusively owned arena and disjoint read-only
 * inputs. All six snapshots are checked before any arena write. This is not
 * a cross-thread atomic transaction and does not discover live game pointers.
 */
int __attribute__((stdcall)) _dllstart(void *module,unsigned reason,void *reserved) { return 0; }
static unsigned word(const unsigned char *p) {
    return (unsigned)p[0]|((unsigned)p[1]<<8)|((unsigned)p[2]<<16)|((unsigned)p[3]<<24);
}
static void putword(unsigned char *p,unsigned n) {
    p[0]=(unsigned char)n;p[1]=(unsigned char)(n>>8);
    p[2]=(unsigned char)(n>>16);p[3]=(unsigned char)(n>>24);
}
static int quaternion(const float *q) {
    double length=0;unsigned i;
    for(i=0;i<4;i++) {
        if(!(q[i]==q[i]) || q[i]<-1.00002 || q[i]>1.00002) return 0;
        length+=(double)q[i]*q[i];
    }
    return length>=.99998 && length<=1.00002;
}

/* offsets[6], before[24], after[24], flags[6]; record size >=0x170.
 * 0 success, 1 bad arena/ABI, 2 overlapping or invalid offsets,
 * 3 kind/flags changed, 4 quaternion invalid, 5 pose snapshot changed.
 */
int __attribute__((dllexport,cdecl)) Hd2CommitArms(unsigned char *arena,unsigned bytes,
        const unsigned *offsets,const float *before,const float *after,const unsigned *flags) {
    unsigned i,j,a,b,old[24],next[24],expected[6],at[6];
    union { float value; unsigned bits; } convert;
    if(!arena || !offsets || !before || !after || !flags || bytes<6*0x170 || bytes>0x10000) return 1;
    for(i=0;i<6;i++) {
        at[i]=offsets[i];expected[i]=flags[i];
        if(at[i]%16 || at[i]>bytes-0x170) return 2;
        for(j=0;j<i;j++) {
            a=at[i];b=at[j];if(a<b+0x170 && b<a+0x170) return 2;
        }
        a=at[i];
        if(word(arena+a+0xf8)!=10 || word(arena+a+0xe0)!=expected[i]
                || !(expected[i]&8) || (expected[i]&0x1200)) return 3;
        if(!quaternion(before+4*i) || !quaternion(after+4*i)) return 4;
        for(j=0;j<4;j++) {
            convert.value=before[4*i+j];old[4*i+j]=convert.bits;
            convert.value=after[4*i+j];next[4*i+j]=convert.bits;
            if(word(arena+a+0xc0+4*j)!=old[4*i+j]) return 5;
        }
    }
    for(i=0;i<6;i++) {
        for(j=0;j<4;j++) putword(arena+at[i]+0xc0+4*j,next[4*i+j]);
        putword(arena+at[i]+0xe0,(expected[i]&0xfffffecb)|0x40000008);
    }
    return 0;
}
