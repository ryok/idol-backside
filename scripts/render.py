"""簡易の正射影スプラット描画（確認用）。各ガウシアンを半径つきの円で、奥から手前へアルファ合成する。
正式なラスタライザではない（異方性・SHの高次は無視）。見えない側が埋まっているかを見るためのもの。"""
import sys
import numpy as np
from plyfile import PlyData
from PIL import Image

def load(p):
    v = PlyData.read(p)['vertex']
    xyz = np.stack([v['x'], v['y'], v['z']], 1)
    col = np.clip(0.5 + 0.28209479 * np.stack([v['f_dc_0'], v['f_dc_1'], v['f_dc_2']], 1), 0, 1)
    a = 1 / (1 + np.exp(-np.asarray(v['opacity'])))
    s = np.exp(np.stack([v['scale_0'], v['scale_1'], v['scale_2']], 1)).max(1)
    return xyz, col, a, s

def rot(axis, deg):
    t = np.deg2rad(deg); c, s = np.cos(t), np.sin(t)
    if axis == 'y': return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    if axis == 'z': return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def render(xyz, col, a, s, R, size=384, extent=None):
    p = xyz @ R.T
    if extent is None: extent = np.abs(xyz).max() * 1.05
    u = ((p[:, 0] / extent) * 0.5 + 0.5) * size
    w = ((-p[:, 1] / extent) * 0.5 + 0.5) * size
    order = np.argsort(p[:, 2])  # z 小さい=奥 として奥から
    img = np.zeros((size, size, 3)); acc = np.zeros((size, size))
    r = np.clip(s / extent * 0.5 * size, 0.5, 4)
    for i in order:
        if a[i] < 0.05: continue
        x, y, rr = u[i], w[i], r[i]
        x0, x1 = int(max(0, x - rr)), int(min(size, x + rr + 1))
        y0, y1 = int(max(0, y - rr)), int(min(size, y + rr + 1))
        if x0 >= x1 or y0 >= y1: continue
        al = a[i] * 0.9
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - al) + col[i] * al
        acc[y0:y1, x0:x1] = acc[y0:y1, x0:x1] * (1 - al) + al
    bg = 1.0
    out = img + (1 - acc[..., None]) * bg
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))

if __name__ == '__main__':
    src, dst, axis = sys.argv[1], sys.argv[2], sys.argv[3]
    pre = sys.argv[4] if len(sys.argv) > 4 else None  # 'x-90' など、先に掛ける回転
    xyz, col, a, s = load(src)
    if pre: xyz = xyz @ rot(pre[0], float(pre[1:])).T
    tiles = [render(xyz, col, a, s, rot(axis, d)) for d in (0, 90, 180, 270)]
    W = tiles[0].width
    m = Image.new('RGB', (W * 4, W), 'white')
    for k, t in enumerate(tiles): m.paste(t, (k * W, 0))
    m.save(dst)
