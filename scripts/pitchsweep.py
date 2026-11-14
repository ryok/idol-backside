"""仰角を上から下へ振る（yaw は入力のまま）。底面が「見えない側」として出てくるかを見る。"""
import os, sys, json, math, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import load
import orbit
d, n, s = sys.argv[1], sys.argv[2], sys.argv[3]
xyz, col, a, sc = load(f"{d}/{n}_s{s}.ply"); cam = json.load(open(f"{d}/{n}_s{s}_camera.json"))
W = 256; ps = [cam["pitch"], 0.6, 0.0, -0.6, -cam["pitch"]]
m = Image.new("RGB", (W * len(ps), W), "white")
for k, p in enumerate(ps):
    c = dict(cam, pitch=p); m.paste(orbit.view(xyz, col, a, sc, c, 0, W), (k * W, 0))
m.save(f"{d}/{n}_s{s}_pitch.jpg", quality=88)
print([round(math.degrees(p)) for p in ps])
