"""render.py の不透明版: 各ピクセルで一番手前の点（不透明度 0.5 以上）だけを描く。透けの影響を除いて形を見る。"""
import sys, numpy as np
from PIL import Image
sys.path.insert(0, sys.argv[4])
from render import load, rot
xyz, col, a, s = load(sys.argv[1])
xyz = xyz @ rot('z', 180).T
p = xyz @ rot('y', float(sys.argv[3])).T
size = 384; ext = np.abs(xyz).max() * 1.05
u = (((p[:, 0] / ext) * 0.5 + 0.5) * size).astype(int); w = (((-p[:, 1] / ext) * 0.5 + 0.5) * size).astype(int)
m = (a > 0.5) & (u >= 0) & (u < size) & (w >= 0) & (w < size)
u, w, z, c = u[m], w[m], p[m, 2], col[m]
order = np.argsort(z)  # 奥から書いて手前で上書き
img = np.ones((size, size, 3))
img[w[order], u[order]] = c[order]
Image.fromarray((img * 255).astype(np.uint8)).save(sys.argv[2])
