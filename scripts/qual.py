import os, sys, time, torch
from idol import IdolPipeline
pipe = IdolPipeline.from_pretrained('speridlabs/idol')
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
jobs = [('../inputs/real-drum.png', 'real'), ('../inputs/real-bowl.png', 'real'),
        ('../inputs/own-origami.png', 'synthetic'), ('../inputs/own-metal.png', 'synthetic'),
        ('demo/examples/obj-backpack.webp', 'synthetic')]
for p, m in jobs:
    t = time.time()
    o = pipe(p, mode=m, seed=42)
    n = os.path.splitext(os.path.basename(p))[0]
    o.gaussian.save_ply(f'{out}/{n}.ply'); o.preprocessed_image.save(f'{out}/{n}_input.png')
    print(n, m, '%.1fs' % (time.time() - t), flush=True)
