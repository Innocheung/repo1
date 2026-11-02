import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from PIL import Image
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
plt.rcParams.update({'font.family':'WenQuanYi Zen Hei','axes.unicode_minus':False,'font.size':9})
base='../igs/新建文件夹/垂直轴3叶片/'
fig,ax=plt.subplots(1,3,figsize=(7.4,3.6),dpi=200,gridspec_kw=dict(width_ratios=[1,0.75,1.25]))
for a,f,t in [(ax[0],'整体.png','(a) 风力机整体三维模型'),(ax[1],'叶片.png','(b) 单个扭曲叶片')]:
    a.imshow(Image.open(base+f)); a.axis('off'); a.set_title(t,fontsize=9.5,y=-0.1)
a=ax[2]; R=0.45; ar=R/2; r_in=0.1*R; pe=2*np.arccos(0.1)
phi=np.linspace(0,pe,200)
for k in range(3):
    tk=2*np.pi*k/3+0.35
    xl=ar+ar*np.cos(phi); yl=ar*np.sin(phi)
    a.plot(np.cos(tk)*xl-np.sin(tk)*yl, np.sin(tk)*xl+np.cos(tk)*yl, color='#0b0b0b', lw=2.4, solid_capstyle='round')
a.add_patch(plt.Circle((0,0),0.06*R,color='#0b0b0b'))
a.add_patch(plt.Circle((0,0),R,fill=False,ls='--',color='#52514e',lw=0.8))
a.annotate('',xy=(R*np.cos(2.2),R*np.sin(2.2)),xytext=(R*np.cos(1.6),R*np.sin(1.6)),
           arrowprops=dict(arrowstyle='->',color='#2a78d6',lw=1.2,connectionstyle='arc3,rad=0.25'))
a.text(-0.2,0.5,'ω（逆时针）',color='#256abf',fontsize=8)
for yy in (-0.3,0,0.3):
    a.annotate('',xy=(-0.55,yy),xytext=(-0.8,yy),arrowprops=dict(arrowstyle='->',color='#52514e',lw=0.9))
a.text(-0.82,0.42,'U∞',fontsize=9)
a.plot([0,R],[-0.56,-0.56],color='#52514e',lw=0.8); a.text(0.04,-0.64,'R = 0.45 m',fontsize=8)
a.set_xlim(-0.85,0.6); a.set_ylim(-0.7,0.65); a.set_aspect('equal'); a.axis('off')
a.set_title('(c) 二维计算截面（等效半径）',fontsize=9.5,y=-0.1)
plt.savefig('fig1_model.png',bbox_inches='tight',facecolor='white')
