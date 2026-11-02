"""2D incompressible LES of a 3-blade Savonius-type VAWT section.
MAC staggered grid, 3rd-order upwind advection, AB2, Smagorinsky SGS,
FFT pressure projection, direct-forcing immersed boundary, fringe region
for inflow recycling (periodic box)."""
import numpy as np, scipy.fft as sfft, sys, time, json
F = np.float32

def run(U, rpm=100.0, D=0.9, ppd=64, Lx=(-4, 12), Ly=8, T=4.0, Tavg=2.0,
        cfl=0.4, Cs=0.17, out='case', rho=1.225, nu=1.5e-5, nsnap=1, niter=2, theta0=0.0):
    R = D / 2; a = R / 2
    dx = D / ppd
    nx = int((Lx[1] - Lx[0]) * ppd); ny = int(Ly * ppd)
    x0 = Lx[0] * D; y0 = -Ly / 2 * D
    xu = x0 + np.arange(nx) * dx; yu = y0 + (np.arange(ny) + .5) * dx      # u points
    xv = x0 + (np.arange(nx) + .5) * dx; yv = y0 + np.arange(ny) * dx      # v points
    omega = rpm * 2 * np.pi / 60
    lam = omega * R / U
    # fringe
    xf0, xf1 = (Lx[1] - 2.5) * D, Lx[1] * D
    def fr(x):
        sm = lambda z: (lambda c: c * c * (3 - 2 * c))(np.clip(z, 0, 1))
        return 20 * U / D * sm((x - xf0) / (1.2 * D)) * sm((xf1 - x) / (0.4 * D))
    lfu = fr(xu)[:, None].astype(F); lfv = fr(xv)[:, None].astype(F)
    # local box for IB
    ib = int(0.62 * D / dx)
    iu = slice(np.searchsorted(xu, -0.62 * D), np.searchsorted(xu, 0.62 * D))
    jv = slice(np.searchsorted(yv, -0.62 * D), np.searchsorted(yv, 0.62 * D))
    ju = slice(np.searchsorted(yu, -0.62 * D), np.searchsorted(yu, 0.62 * D))
    iv = slice(np.searchsorted(xv, -0.62 * D), np.searchsorted(xv, 0.62 * D))
    XU, YU = [A.astype(F) for A in np.meshgrid(xu[iu], yu[ju], indexing='ij')]
    XV, YV = [A.astype(F) for A in np.meshgrid(xv[iv], yv[jv], indexing='ij')]
    t_bl = 2.0 * dx; r_in = 0.10 * R; r_sh = 0.06 * R
    phi_end = 2 * np.arccos(r_in / R)
    eps = 0.6 * dx
    def mask(X, Y, th):
        chi = 0.5 * (1 - np.tanh((np.hypot(X, Y) - r_sh) / eps))
        for k in range(3):
            tk = th + 2 * np.pi * k / 3
            c, s = np.cos(tk), np.sin(tk)
            xl = c * X + s * Y; yl = -s * X + c * Y
            dxl = xl - a; rho_ = np.hypot(dxl, yl); psi = np.arctan2(yl, dxl)
            d_arc = np.abs(rho_ - a)
            e1 = (xl - 2 * a) ** 2 + yl ** 2
            ex, ey = a + a * np.cos(phi_end), a * np.sin(phi_end)
            e2 = (xl - ex) ** 2 + (yl - ey) ** 2
            d_end = np.sqrt(np.minimum(e1, e2))
            d = np.where((psi >= 0) & (psi <= phi_end), d_arc, d_end)
            chi = np.maximum(chi, 0.5 * (1 - np.tanh((d - t_bl / 2) / eps)))
        return chi
    # Poisson eigenvalues
    kx = np.arange(nx); ky = np.arange(ny // 2 + 1)
    ex_ = (2 * np.cos(2 * np.pi * kx / nx) - 2) / dx ** 2
    ey_ = (2 * np.cos(2 * np.pi * ky / ny) - 2) / dx ** 2
    eig = ex_[:, None] + ey_[None, :]; eig[0, 0] = 1.0; eig = eig.astype(F)
    def S(f, s, ax): return np.roll(f, -s, ax)
    def d3(f, vel, ax):
        fm2, fm1, fp1, fp2 = S(f, -2, ax), S(f, -1, ax), S(f, 1, ax), S(f, 2, ax)
        dp = (2 * fp1 + 3 * f - 6 * fm1 + fm2) / (6 * dx)
        dm = (-fp2 + 6 * fp1 - 3 * f - 2 * fm1) / (6 * dx)
        return np.where(vel > 0, dp, dm).astype(F, copy=False)
    def lap(f):
        return (S(f, 1, 0) + S(f, -1, 0) + S(f, 1, 1) + S(f, -1, 1) - 4 * f) / dx ** 2
    def rhs(u, v):
        vu = 0.25 * (S(v, -1, 0) + v + S(S(v, -1, 0), 1, 1) + S(v, 1, 1))
        uv = 0.25 * (u + S(u, 1, 0) + S(u, -1, 1) + S(S(u, 1, 0), -1, 1))
        s11 = (S(u, 1, 0) - u) / dx; s22 = (S(v, 1, 1) - v) / dx
        s12 = 0.5 * ((u - S(u, -1, 1)) / dx + (v - S(v, -1, 0)) / dx)
        s12c = 0.25 * (s12 + S(s12, 1, 0) + S(s12, 1, 1) + S(S(s12, 1, 0), 1, 1))
        nut = (Cs * dx) ** 2 * np.sqrt(2 * s11 ** 2 + 2 * s22 ** 2 + 4 * s12c ** 2)
        nu_u = nu + 0.5 * (nut + S(nut, -1, 0)); nu_v = nu + 0.5 * (nut + S(nut, -1, 1))
        ru = -(u * d3(u, u, 0) + vu * d3(u, vu, 1)) + nu_u * lap(u) - lfu * (u - U)
        rv = -(uv * d3(v, uv, 0) + v * d3(v, v, 1)) + nu_v * lap(v) - lfv * v
        return ru, rv
    def project(u, v, dt):
        div = (S(u, 1, 0) - u + S(v, 1, 1) - v) / dx
        ph = sfft.irfft2(sfft.rfft2(div, workers=1) / eig, s=(nx, ny), workers=1)
        u -= (ph - S(ph, -1, 0)) / dx; v -= (ph - S(ph, -1, 1)) / dx
        return u, v
    # init
    rng = np.random.default_rng(1)
    u = U * (1 + 0.01 * rng.standard_normal((nx, ny))); v = 0.01 * U * rng.standard_normal((nx, ny))
    u = u.astype(F); v = v.astype(F)
    u, v = project(u, v, 1.0)
    umax = max(2.8 * U, U + 1.5 * omega * R)
    dt = cfl * dx / umax
    nsteps = int(round(T / dt)); navg0 = int(round((T - Tavg) / dt))
    th = theta0; ru0 = rv0 = None
    tq = []; um = np.zeros((nx, ny)); vm = np.zeros_like(um); uu = np.zeros_like(um); na = 0
    t0 = time.time()
    for n in range(nsteps):
        ru, rv = rhs(u, v)
        if ru0 is None: ru0, rv0 = ru, rv
        u = u + dt * (1.5 * ru - 0.5 * ru0); v = v + dt * (1.5 * rv - 0.5 * rv0)
        ru0, rv0 = ru, rv
        th += omega * dt
        cu = mask(XU, YU, th); cv = mask(XV, YV, th)
        ub = -omega * YU; vb = omega * XV
        Tz = 0.0; Fx = 0.0; Fy = 0.0
        for it in range(niter):
            fu = cu * (ub - u[iu, ju]); fv = cv * (vb - v[iv, jv])
            u[iu, ju] += fu; v[iv, jv] += fv
            Tz -= rho * dx ** 2 / dt * (np.sum(XV * fv) - np.sum(YU * fu))
            Fx -= rho * dx ** 2 / dt * np.sum(fu); Fy -= rho * dx ** 2 / dt * np.sum(fv)
            u, v = project(u, v, dt)
        slip = float(np.abs(cu * (ub - u[iu, ju])).max() / U)
        tq.append((n * dt + dt, th, Tz, slip, Fx, Fy))
        if n >= navg0:
            um += u; vm += v; uu += u * u; na += 1
        if n % 500 == 0:
            print(f'U={U} step {n}/{nsteps} t={n*dt:.3f} Tz={Tz:.2f} slip={slip:.3f} umax={np.abs(u).max():.2f} {time.time()-t0:.0f}s', flush=True)
            if not np.isfinite(u).all(): raise RuntimeError('blow-up')
    um /= na; vm /= na; uu = uu / na - um ** 2
    # final fields at cell centers
    uc = 0.5 * (u + S(u, 1, 0)); vc = 0.5 * (v + S(v, 1, 1))
    wz = (S(v, 1, 0) - v) / dx - (S(u, 1, 1) - u) / dx  # at corners (i+1,j+1)... approx
    wz = 0.25 * (wz + S(wz, -1, 0) + S(wz, -1, 1) + S(S(wz, -1, 0), -1, 1))
    umc = 0.5 * (um + S(um, 1, 0)); vmc = 0.5 * (vm + S(vm, 1, 1)); uuc = 0.5 * (uu + S(uu, 1, 0))
    xc = x0 + (np.arange(nx) + .5) * dx; yc = y0 + (np.arange(ny) + .5) * dx
    chic = mask(*np.meshgrid(xc, yc, indexing='ij'), th)
    tq = np.array(tq)
    np.savez_compressed(out + '.npz', xc=xc, yc=yc, uc=uc.astype(np.float32), vc=vc.astype(np.float32),
                        wz=wz.astype(np.float32), um=umc.astype(np.float32), vm=vmc.astype(np.float32),
                        uu=uuc.astype(np.float32), chi=chic.astype(np.float32), tq=tq, theta=th)
    Tm = tq[tq[:, 0] > T - Tavg, 2].mean()
    P = Tm * omega
    Cp = P / (0.5 * rho * U ** 3 * D)
    Ct = Tm / (0.5 * rho * U ** 2 * D * R)
    info = dict(U=U, rpm=rpm, omega=omega, lam=lam, D=D, dx=dx, nx=nx, ny=ny, dt=dt, nsteps=nsteps,
                T=T, Tavg=Tavg, Tm=Tm, P_per_m=P, Cp=Cp, Ct=Ct, wall=time.time() - t0)
    json.dump(info, open(out + '.json', 'w'), indent=1)
    print(info, flush=True)

if __name__ == '__main__':
    U = float(sys.argv[1]); T = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    ppd = int(sys.argv[3]) if len(sys.argv) > 3 else 64
    niter = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    rpm = float(sys.argv[6]) if len(sys.argv) > 6 else 100.0
    th0 = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0
    cfl = float(sys.argv[8]) if len(sys.argv) > 8 else 0.4
    run(U, cfl=cfl, theta0=np.radians(th0), T=T, Tavg=(float(sys.argv[9]) if len(sys.argv) > 9 else min(2.0, T / 2)), ppd=ppd, out=sys.argv[4] if len(sys.argv) > 4 else f'case_U{U:g}', niter=niter, rpm=rpm)
