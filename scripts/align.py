"""予測カメラの座標の約束を総当たりで当てる。各候補で入力カメラ位置から見たシルエットを描き、入力画像のシルエットと IoU を比べる。"""
import sys, json, glob, itertools, math, numpy as np
from plyfile import PlyData
from PIL import Image

def load(p):
    v = PlyData.read(p)["vertex"]
    xyz = np.stack([v["x"], v["y"], v["z"]], 1)
    a = 1 / (1 + np.exp(-np.asarray(v["opacity"])))
    return xyz[a > 0.3]

def lookat(cpos, up):
    f = -cpos / np.linalg.norm(cpos)                # 原点を向く
    r = np.cross(f, up); 
    if np.linalg.norm(r) < 1e-6: r = np.cross(f, up + 1e-3)
    r /= np.linalg.norm(r); u = np.cross(r, f)
    return np.stack([r, u, f])                       # 行: 右・上・前

def sil(xyz, cam, M, S=96):
    y, p, rad, fov = cam["yaw"], cam["pitch"], cam["radius"], cam["fov"]
    d = np.array([math.cos(p) * math.sin(y), math.cos(p) * math.cos(y), math.sin(p)])   # camera.py の逆: dx,dy,dz
    d = M @ d; up = M @ np.array([0, 0, 1.0])
    R = lookat(d * rad, up)
    q = (xyz - d * rad) @ R.T
    z = q[:, 2]; ok = z > 1e-3
    u, w = q[ok, 0] / z[ok], -q[ok, 1] / z[ok]
    return bbox_norm(u, w, S)

def bbox_norm(u, w, S):
    u0, u1, w0, w1 = np.percentile(u, 0.5), np.percentile(u, 99.5), np.percentile(w, 0.5), np.percentile(w, 99.5)
    s = max(u1 - u0, w1 - w0)
    cu, cw = (u0 + u1) / 2, (w0 + w1) / 2
    iu = np.clip(((u - cu) / s + 0.5) * (S - 1), 0, S - 1).astype(int)
    iw = np.clip(((w - cw) / s + 0.5) * (S - 1), 0, S - 1).astype(int)
    m = np.zeros((S, S), bool); m[iw, iu] = True
    return m

def input_sil(p, S=96):
    a = np.asarray(Image.open(p).convert("RGB")).astype(int).sum(2) > 30
    w, u = np.nonzero(a)
    sub = np.random.default_rng(0).choice(len(u), min(len(u), 200000), replace=False)
    return bbox_norm(u[sub].astype(float), w[sub].astype(float), S)

def dil(m, k=2):
    o = m.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1): o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o

def iou(a, b):
    a = dil(a); b = dil(b)
    return (a & b).sum() / max((a | b).sum(), 1)

d = sys.argv[1]
inputs = {"real-drum": "../out/qual/real-drum_input.png", "real-bowl": "../out/qual/real-bowl_input.png", "fig-fox": "../out/bench/fig-fox_input.png"}
items = []
for cj in sorted(glob.glob(f"{d}/*_camera.json")):
    n = cj.split("/")[-1].rsplit("_s", 1)[0]
    items.append((cj.split("/")[-1], load(cj.replace("_camera.json", ".ply")), json.load(open(cj)), input_sil(inputs[n])))
mats = []
for perm in itertools.permutations(range(3)):
    for sg in itertools.product([1, -1], repeat=3):
        M = np.zeros((3, 3)); 
        for i in range(3): M[perm[i], i] = sg[i]
        mats.append(M)
res = []
for M in mats:
    s = [iou(sil(x, c, M), m) for _, x, c, m in items]
    res.append((np.mean(s), M, s))
res.sort(key=lambda t: -t[0])
for sc, M, s in res[:4]:
    print("%.3f" % sc, M.astype(int).tolist(), " ".join("%.2f" % v for v in s))
print([i[0] for i in items]); print([ {k: round(v, 2) for k, v in i[2].items()} for i in items])
