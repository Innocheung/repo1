import json, numpy as np
out = {}
for U in (4, 6, 8, 10):
    s = f'case_U{U}'
    d = np.load(s + '.npz'); i = json.load(open(s + '.json'))
    D = i['D']; X = d['xc'] / D; Y = d['yc'] / D
    um = d['um'] / U; uu = d['uu']
    tq = d['tq']; t = tq[:, 0]; m = t > i['T'] - i['Tavg']
    T = tq[m, 2]; q = 0.5 * 1.225 * U ** 2 * D
    rec = {}
    for xs in (1, 2, 4, 6, 8):
        k = np.argmin(abs(X - xs)); w = (Y > -1.5) & (Y < 1.5)
        prof = um[k, w]; yy = Y[w]
        j = np.argmin(prof)
        deficit = 1 - prof
        half = deficit >= 0.5 * deficit.max()
        width = yy[half].max() - yy[half].min()
        ti = np.sqrt(np.clip(uu[k, w], 0, None)).max() / U
        # mean deficit across rotor projection
        rp = (yy > -0.5) & (yy < 0.5)
        rec[str(xs)] = dict(umin=float(prof[j]), ymin=float(yy[j]), width=float(width), TI=float(ti),
                            uavg=float(prof[rp].mean()))
    # torque spectrum
    Tc = T - T.mean(); dt = i['dt']
    f = np.fft.rfftfreq(len(Tc), dt); A = np.abs(np.fft.rfft(Tc * np.hanning(len(Tc))))
    sel = f > 0.5
    fpk = float(f[sel][np.argmax(A[sel])])
    Fx = tq[m, 4].mean() if tq.shape[1] > 4 else np.nan
    out[str(U)] = dict(lam=i['lam'], Tm=float(T.mean()), Tstd=float(T.std()), Tmin=float(T.min()), Tmax=float(T.max()),
                       Cp=float(T.mean() * i['omega'] / (q * U)), Ct=float(T.mean() / (q * D / 2)),
                       Cd=float(Fx / q), Cl=float(tq[m, 5].mean() / q), P=float(T.mean() * i['omega']),
                       fpk=fpk, wake=rec, dt=dt, nsteps=i['nsteps'], wall=i['wall'])
    print(U, json.dumps(out[str(U)], ensure_ascii=False)[:600])
json.dump(out, open('wake_stats.json', 'w'), indent=1, ensure_ascii=False)
