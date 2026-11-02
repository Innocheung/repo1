import sys, json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib import font_manager as fm

fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
plt.rcParams.update({'font.family': 'WenQuanYi Zen Hei', 'axes.unicode_minus': False,
                     'font.size': 9, 'axes.edgecolor': '#52514e', 'axes.labelcolor': '#0b0b0b',
                     'xtick.color': '#52514e', 'ytick.color': '#52514e'})
SEQ = LinearSegmentedColormap.from_list('blue', ['#f7fafe', '#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5',
                                                 '#256abf', '#184f95', '#0d366b'])
DIV = LinearSegmentedColormap.from_list('div', ['#104281', '#3987e5', '#9ec5f4', '#f0efec',
                                                '#f2a3a2', '#e34948', '#a12424'])
CAT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
MK = ['o', 's', '^', 'D']; LS = ['-', '--', '-.', ':']


def make(stem, figno, label, outpng):
    d = np.load(stem + '.npz'); info = json.load(open(stem + '.json'))
    U = info['U']; D = info['D']
    X = d['xc'] / D; Y = d['yc'] / D
    sx = (X > -2) & (X < 9); sy = (Y > -2.5) & (Y < 2.5)
    Xs, Ys = X[sx], Y[sy]
    chi = d['chi'][np.ix_(sx, sy)]
    spd = np.hypot(d['uc'], d['vc'])[np.ix_(sx, sy)] / U
    spd = np.where(chi > 0.5, np.nan, spd)
    fig = plt.figure(figsize=(7.2, 6.4), dpi=200)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=0.38, wspace=0.28)
    ax = fig.add_subplot(gs[0, :])
    im = ax.pcolormesh(Xs, Ys, spd.T, cmap=SEQ, vmin=0, vmax=1.6, shading='auto', rasterized=True)
    ax.contour(Xs, Ys, chi.T, [0.5], colors='#0b0b0b', linewidths=0.8)
    ax.set_aspect('equal'); ax.set_xlabel('x / D'); ax.set_ylabel('y / D')
    ax.set_title(f'(a) 瞬时速度幅值云图 |V|/U∞（t = {info["T"]:.1f} s）', loc='left', fontsize=9.5)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01); cb.set_label('|V| / U∞')
    for xs in (1, 2, 4, 6):
        ax.axvline(xs, color='#52514e', lw=0.5, ls=(0, (2, 3)))
    ax.annotate('', xy=(-0.9, 2.1), xytext=(-1.85, 2.1),
                arrowprops=dict(arrowstyle='-|>', color='#0b0b0b', lw=1.0))
    ax.text(-1.85, 1.75, '来流 U∞', fontsize=8, va='center')
    # (b) vorticity close-up
    ax2 = fig.add_subplot(gs[1, 0])
    cx = (X > -1) & (X < 3); cy = (Y > -1.3) & (Y < 1.3)
    w = d['wz'][np.ix_(cx, cy)] * D / U
    c2 = d['chi'][np.ix_(cx, cy)]
    w = np.where(c2 > 0.5, np.nan, w)
    im2 = ax2.pcolormesh(X[cx], Y[cy], w.T, cmap=DIV, norm=TwoSlopeNorm(0, -20, 20), shading='auto', rasterized=True)
    ax2.contourf(X[cx], Y[cy], c2.T, [0.5, 2], colors='#0b0b0b')
    ax2.set_aspect('equal'); ax2.set_xlabel('x / D'); ax2.set_ylabel('y / D')
    ax2.set_title('(b) 近尾迹瞬时涡量 ωz·D/U∞', loc='left', fontsize=9.5)
    cb2 = fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.02); cb2.ax.tick_params(labelsize=7)
    # (c) mean wake profiles
    ax3 = fig.add_subplot(gs[1, 1])
    um = d['um'] / U
    for k, xs in enumerate((1, 2, 4, 6)):
        i = np.argmin(abs(X - xs)); m = (Y > -2) & (Y < 2)
        ax3.plot(um[i, m], Y[m], color=CAT[k], ls=LS[k], lw=1.6, label=f'x/D = {xs}',
                 marker=MK[k], markevery=24, ms=4)
    ax3.axvline(1, color='#9a9994', lw=0.6)
    ax3.axhspan(-0.5, 0.5, color='#f0efec', zorder=0)
    ax3.set_xlabel('时均流向速度 ū / U∞'); ax3.set_ylabel('y / D'); ax3.set_ylim(-2, 2)
    ax3.set_title('(c) 时均尾流速度剖面', loc='left', fontsize=9.5)
    ax3.grid(color='#e6e5e0', lw=0.5); ax3.legend(fontsize=7.5, frameon=False, loc='lower left')
    for a in (ax, ax2, ax3):
        for s in ('top', 'right'):
            a.spines[s].set_visible(a is not ax3)
    fig.suptitle(f'{label}：U∞ = {U:g} m/s，n = {info["rpm"]:.0f} r/min，λ = {info["lam"]:.2f}，'
                 f'Cp = {info["Cp"]:.3f}', fontsize=10.5, y=0.985)
    fig.savefig(outpng, bbox_inches='tight', facecolor='white'); plt.close(fig)


if __name__ == '__main__':
    make(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
