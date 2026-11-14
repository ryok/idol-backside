"""seed 違いの比較: 物ごとに 行=seed、列=0/90/180/270 度。角度ごとに seed 間の平均画素差も出す。"""
import os, sys, itertools, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import load, rot, render
d = sys.argv[1]; names = sys.argv[2:]
angles = (0, 90, 180, 270)
for n in names:
    rows = []
    for s in (1, 2, 3, 4):
        xyz, col, a, sc = load(f"{d}/{n}_s{s}.ply")
        xyz = xyz @ rot("z", 180).T
        ext = 0.6
        rows.append([np.asarray(render(xyz, col, a, sc, rot("y", g), size=256, extent=ext)).astype(float) for g in angles])
    diffs = []
    for k, g in enumerate(angles):
        ds = [np.abs(rows[i][k] - rows[j][k]).mean() for i, j in itertools.combinations(range(4), 2)]
        diffs.append(np.mean(ds))
    print(n, " ".join(f"{g}deg={v:.1f}" for g, v in zip(angles, diffs)), flush=True)
    W = 256; m = Image.new("RGB", (W * 4, W * 4), "white")
    for i, r in enumerate(rows):
        for k, t in enumerate(r): m.paste(Image.fromarray(t.astype(np.uint8)), (k * W, i * W))
    m.save(f"{d}/{n}_sheet.jpg", quality=88)
