import numpy as np, sys, json
for f in sys.argv[1:]:
    d=np.load(f+'.npz'); i=json.load(open(f+'.json')); tq=d['tq']; t=tq[:,0]; m=t>i['T']-i['Tavg']
    U=i['U']; q=0.5*1.225*U**2*0.9
    print(f, 'lam=%.2f Ct=%.3f Cp=%.3f Cd=%.3f Cl=%.3f slip=%.3f'%(i['lam'], tq[m,2].mean()/(q*0.45), tq[m,2].mean()*i['omega']/(q*U), tq[m,4].mean()/q, tq[m,5].mean()/q, tq[m,3].mean()))
