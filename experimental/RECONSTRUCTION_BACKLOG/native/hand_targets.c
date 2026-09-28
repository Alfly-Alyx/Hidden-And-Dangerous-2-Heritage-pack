/* Original bounded preparation of arm inputs from current local transforms.
 * No game pointers, loader, API, allocation or persistent state. ABI:
 * poses[count*10] float P3/Q4/S3, parents[count] signed parent-first indices,
 * roles[5] = held root, left/right contact markers, left/right forearms,
 * rest[90] = each arm's first 45 solver doubles,
 * grips[30] = each side's contact3/active rest-turn9/wrist-to-contact3,
 * workspace[count*12] floats = caller-owned scratch, writable on failure;
 * output[120] = two complete Hd2SolveArm inputs. All buffers must be disjoint
 * and valid for their declared sizes. Failure never writes output. Scratch
 * is provided explicitly rather than reserving a large unprobed x86 stack.
 */
#ifndef HD2_HAND_PIPELINE
int __attribute__((stdcall)) _dllstart(void *module,unsigned reason,void *reserved) { return 0; }
#endif
static int finite_bound(double v,double bound) { return v==v && v>=-bound && v<=bound; }
static void product(const float *a,const float *b,float *out) {
    int r,c,k;double sum;
    for(r=0;r<3;r++) for(c=0;c<3;c++) {
        sum=0;for(k=0;k<3;k++) sum+=(double)a[3*r+k]*b[3*k+c];
        out[3*r+c]=(float)sum;
    }
    for(r=0;r<3;r++) out[9+r]=(float)((double)b[9]*a[3*r]+a[9+r]
                                           +(double)b[10]*a[3*r+1]+(double)b[11]*a[3*r+2]);
}
static int local(const float *p,float *m) {
    double x=p[3],y=p[4],z=p[5],w=p[6],norm=x*x+y*y+z*z+w*w;int r,c;
    if(norm<.99998 || norm>1.00002) return 0;
    if(w>=1 || w<=-1) {
        for(r=0;r<3;r++) for(c=0;c<3;c++) m[3*r+c]=(float)(r==c);
    } else {
        m[0]=(float)(1-2*(y*y+z*z));m[1]=(float)(2*(x*y+z*w));m[2]=(float)(2*(x*z-y*w));
        m[3]=(float)(2*(x*y-z*w));m[4]=(float)(1-2*(x*x+z*z));m[5]=(float)(2*(y*z+x*w));
        m[6]=(float)(2*(x*z+y*w));m[7]=(float)(2*(y*z-x*w));m[8]=(float)(1-2*(x*x+y*y));
    }
    for(r=0;r<3;r++) {
        for(c=0;c<3;c++) m[3*r+c]=(float)((double)m[3*r+c]*p[7+c]);
        m[9+r]=p[r];
    }
    return 1;
}

/* 0 success; 1 pointers/count/capacity; 2 number/scale; 3 hierarchy/roles;
 * 4 quaternion; 5 composed coordinates outside the reviewed domain. */
int __attribute__((dllexport,cdecl)) Hd2PrepareArms(const float *poses,const int *parents,unsigned count,
        const unsigned *roles,const double *rest,const double *grips,float *workspace,unsigned workspace_count,
        double *output,unsigned capacity) {
    float m[12];double result[120],turn[9],contact,palm;
    const float *held,*anchor,*elbow;const double *grip;unsigned i,j,k,r,c,s;int parent;
    if(!poses || !parents || !roles || !rest || !grips || !workspace || !output
            || count<5 || count>128 || workspace_count!=count*12 || capacity!=120) return 1;
    for(i=0;i<count*10;i++) if(!finite_bound(poses[i],10)) return 2;
    for(i=0;i<90;i++) if(!finite_bound(rest[i],10)) return 2;
    for(i=0;i<30;i++) if(!finite_bound(grips[i],10)) return 2;
    for(i=0;i<5;i++) {
        if(roles[i]>=count) return 3;
        for(j=0;j<i;j++) if(roles[i]==roles[j]) return 3;
    }
    for(i=0;i<count;i++) {
        parent=parents[i];if(parent < -1 || parent>=(int)i) return 3;
        for(j=7;j<10;j++) if(poses[10*i+j]<.01 || poses[10*i+j]>2) return 2;
        if(!local(poses+10*i,m)) return 4;
        if(parent==-1) {for(j=0;j<12;j++) workspace[12*i+j]=m[j];}
        else product(workspace+12*parent,m,workspace+12*i);
        for(j=0;j<12;j++) if(!finite_bound(workspace[12*i+j],10)) return 5;
    }
    held=workspace+12*roles[0];
    for(s=0;s<2;s++) {
        grip=grips+15*s;anchor=workspace+12*roles[1+s];elbow=workspace+12*roles[3+s];
        for(r=0;r<3;r++) for(c=0;c<3;c++) {
            turn[3*r+c]=0;
            for(k=0;k<3;k++) turn[3*r+c]+=(double)held[3*r+k]*grip[3+3*k+c];
        }
        for(i=0;i<45;i++) result[s*60+i]=rest[s*45+i];
        for(r=0;r<3;r++) {
            contact=0;palm=0;
            for(k=0;k<3;k++) {contact+=(double)held[3*r+k]*grip[k];palm+=turn[3*r+k]*grip[12+k];}
            result[s*60+45+r]=(double)anchor[9+r]+contact-palm;
            result[s*60+57+r]=elbow[9+r];
        }
        for(i=0;i<9;i++) result[s*60+48+i]=turn[i];
    }
    for(i=0;i<120;i++) if(!finite_bound(result[i],10)) return 5;
    for(i=0;i<120;i++) output[i]=result[i];
    return 0;
}
