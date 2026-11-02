import re,numpy as np,sys
def load(fn):
    L=open(fn,encoding='latin1').read().splitlines()
    D=[l for l in L if len(l)>72 and l[72]=='D']
    P={int(l[73:80]):l[:64] for l in L if len(l)>72 and l[72]=='P'}
    out=[]
    for i in range(0,len(D),2):
        t=int(D[i][:8]); p=int(D[i][8:16]); n=int(D[i+1][24:32])
        s=''.join(P[p+k] for k in range(n)).replace('D','E')
        v=re.split(r'[,;]',s)
        try:
            if t==126:
                K=int(v[1]);M=int(v[2]); off=7+K+M+2+K+1
                out.append((t,np.array(v[off:off+3*(K+1)],float).reshape(-1,3)))
            if t==128:
                K1,K2,M1,M2=map(int,v[1:5]); off=10+(K1+M1+2)+(K2+M2+2)+(K1+1)*(K2+1)
                out.append((t,np.array(v[off:off+3*(K1+1)*(K2+1)],float).reshape(-1,3)))
            if t==110:
                out.append((t,np.array(v[1:7],float).reshape(2,3)))
        except Exception as e: pass
    return out
if __name__=='__main__':
    for f in sys.argv[1:]:
        o=load(f); p=np.vstack([c for _,c in o])
        print(f,len(o),p.min(0).round(1),p.max(0).round(1))
