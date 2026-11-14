import os, sys, time, torch
from idol import IdolPipeline
pipe = IdolPipeline.from_pretrained("speridlabs/idol")
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
jobs = [("../inputs/real-drum.png", "real"), ("../inputs/real-bowl.png", "real"), ("demo/examples/fig-fox.webp", "synthetic")]
for p, m in jobs:
    for s in [1, 2, 3, 4]:
        t = time.time()
        o = pipe(p, mode=m, seed=s)
        n = os.path.splitext(os.path.basename(p))[0]
        o.gaussian.save_ply(f"{out}/{n}_s{s}.ply"); import json; json.dump(o.camera, open(f"{out}/{n}_s{s}_camera.json", "w"))
        print(n, s, "%.1fs" % (time.time() - t), flush=True)
