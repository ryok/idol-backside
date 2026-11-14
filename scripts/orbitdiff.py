import os, sys, json, math, itertools, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import load
import orbit
d, n = sys.argv[1], sys.argv[2]
data = [(load(f"{d}/{n}_s{s}.ply"), json.load(open(f"{d}/{n}_s{s}_camera.json"))) for s in (1, 2, 3, 4)]
out = []
for g in (0, 90, 180, 270):
    ims = [np.asarray(orbit.view(*p, c, g, 256)).astype(float) for p, c in data]
    out.append("%ddeg=%.1f" % (g, np.mean([np.abs(ims[i] - ims[j]).mean() for i, j in itertools.combinations(range(4), 2)])))
print(n, " ".join(out), flush=True)
