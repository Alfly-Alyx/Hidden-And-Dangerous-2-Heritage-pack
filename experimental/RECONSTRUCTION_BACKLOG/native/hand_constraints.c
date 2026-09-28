/* Original, standalone x86 arm solver. NOT an ASI, loader or installed hook.
 * No Windows API, commercial data, allocation, imports or persistent state.
 * Input: 60 row-major doubles (three rest-world basis/position pairs,
 * shoulder-parent basis, target wrist position, active hand turn, elbow pole).
 * side: +1 left, -1 right. Output: three native/conjugate XYZW quaternions.
 * Failure never writes output. Count/capacity must be exactly 60/12.
 */
#define EXPORT __attribute__((dllexport))
#ifdef HD2_CONSTRAINTS_STANDALONE
/* Diagnostic PE only: ordinary Windows loading is explicitly refused. */
int __attribute__((stdcall)) _dllstart(void *module,unsigned reason,void *reserved) { return 0; }
#endif
static double absolute(double x) { return x<0 ? -x : x; }
static double dot(const double *a,const double *b) { return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
static double root(double x) {
    double r; int i;
    if (x<=0) return 0;
    r=x>1 ? x : 1;
    for(i=0;i<80;i++) r=.5*(r+x/r);
    return r;
}
static void sub(const double *a,const double *b,double *v) { int i; for(i=0;i<3;i++) v[i]=a[i]-b[i]; }
static void cross(const double *a,const double *b,double *v) {
    v[0]=a[1]*b[2]-a[2]*b[1]; v[1]=a[2]*b[0]-a[0]*b[2]; v[2]=a[0]*b[1]-a[1]*b[0];
}
static int unit(const double *a,double *v) {
    double n=root(dot(a,a)); int i;
    if(n<1e-9) return 0;
    for(i=0;i<3;i++) v[i]=a[i]/n;
    return 1;
}
static void transpose(const double *a,double *t) { int i,j; for(i=0;i<3;i++) for(j=0;j<3;j++) t[3*i+j]=a[3*j+i]; }
static void mul(const double *a,const double *b,double *v) {
    int i,j,k; for(i=0;i<3;i++) for(j=0;j<3;j++) {
        v[3*i+j]=0; for(k=0;k<3;k++) v[3*i+j]+=a[3*i+k]*b[3*k+j];
    }
}
static int basis(const double *m) {
    double c[3]; int i,j;
    for(i=0;i<3;i++) for(j=0;j<3;j++)
        if(absolute(dot(m+3*i,m+3*j)-(i==j ? 1 : 0))>1e-6) return 0;
    cross(m+3,m+6,c); return dot(m,c)>=1-1e-6;
}
static int frame(const double *direction,const double *hint,double *m) {
    double x[3],y[3],z[3],a[3],d; int i;
    if(!unit(direction,x)) return 0;
    d=dot(hint,x); for(i=0;i<3;i++) a[i]=hint[i]-d*x[i];
    if(!unit(a,z)) return 0;
    cross(z,x,y);
    for(i=0;i<3;i++) { m[3*i]=x[i]; m[3*i+1]=y[i]; m[3*i+2]=z[i]; }
    return 1;
}
static int bend(const double *start,const double *end,const double *normal,double *m) {
    double before[9],after[9],t[9],z[3]={0,0,1};
    if(!frame(start,z,before) || !frame(end,normal,after)) return 0;
    transpose(before,t); mul(after,t,m); return 1;
}
static int quaternion(const double *raw,double *q) {
    double m[9],s,n,trace; int i,j,k;
    /* Rest-world matrices retain tiny float32 scale residuals. Match the
     * reference SRT decomposition: remove column scales before conversion. */
    for(j=0;j<3;j++) {
        n=root(raw[j]*raw[j]+raw[3+j]*raw[3+j]+raw[6+j]*raw[6+j]);
        if(n<1e-10) return 0;
        for(i=0;i<3;i++) m[3*i+j]=raw[3*i+j]/n;
    }
    trace=m[0]+m[4]+m[8];
    if(!basis(m)) return 0;
    if(trace>0) {
        s=2*root(1+trace); q[0]=(m[7]-m[5])/s; q[1]=(m[2]-m[6])/s; q[2]=(m[3]-m[1])/s; q[3]=s/4;
    } else {
        i=0; if(m[4]>m[0]) i=1; if(m[8]>m[3*i+i]) i=2;
        j=(i+1)%3; k=(i+2)%3; s=2*root(1+m[3*i+i]-m[3*j+j]-m[3*k+k]);
        if(s<1e-12) return 0;
        q[3]=(m[3*k+j]-m[3*j+k])/s; q[i]=s/4;
        q[j]=(m[3*i+j]+m[3*j+i])/s; q[k]=(m[3*i+k]+m[3*k+i])/s;
    }
    n=root(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3]);
    if(n<1e-12) return 0;
    for(i=0;i<4;i++) q[i]=(i<3 ? -q[i] : q[i])/n;
    return 1;
}

EXPORT int __attribute__((cdecl)) Hd2SolveArm(const double *in,unsigned count,int side,double *out,unsigned capacity) {
    double upper[3],fore[3],delta[3],axis[3],hint[3],direction[3],elbow[3],ut[3],ft[3],normal[3];
    double turns[2][9],wanted[3][9],local[9],parent[9],result[12];
    double l1,l2,d,along,h,projection; int i,j;
    if(!in || !out || count!=60 || capacity!=12 || (side!=1 && side!=-1)) return 1;
    for(i=0;i<60;i++) if(!(in[i]==in[i]) || in[i]<-10 || in[i]>10) return 2;
    if(!basis(in) || !basis(in+12) || !basis(in+24) || !basis(in+36) || !basis(in+48)) return 3;
    sub(in+21,in+9,upper); sub(in+33,in+21,fore); sub(in+45,in+9,delta);
    l1=root(dot(upper,upper)); l2=root(dot(fore,fore)); d=root(dot(delta,delta));
    if(l1<.01 || l1>2 || l2<.01 || l2>2 || d<=absolute(l1-l2)+1e-6 || d>=l1+l2-1e-6) return 4;
    if(!unit(delta,axis)) return 5;
    sub(in+57,in+9,hint); projection=dot(hint,axis);
    for(i=0;i<3;i++) direction[i]=hint[i]-projection*axis[i];
    if(!unit(direction,direction)) return 5;
    along=(l1*l1-l2*l2+d*d)/(2*d); h=root(l1*l1-along*along);
    for(i=0;i<3;i++) elbow[i]=in[9+i]+along*axis[i]+h*direction[i];
    sub(elbow,in+9,ut); sub(in+45,elbow,ft); cross(ut,ft,normal);
    if(!unit(normal,normal)) return 5;
    for(i=0;i<3;i++) normal[i]*=side;
    if(!bend(upper,ut,normal,turns[0]) || !bend(fore,ft,normal,turns[1])) return 5;
    mul(turns[0],in,wanted[0]); mul(turns[1],in+12,wanted[1]); mul(in+48,in+24,wanted[2]);
    for(i=0;i<3;i++) {
        transpose(i ? wanted[i-1] : in+36,parent); mul(parent,wanted[i],local);
        if(!quaternion(local,result+4*i)) return 5;
    }
    for(j=0;j<12;j++) out[j]=result[j];
    return 0;
}
