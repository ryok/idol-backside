"""Idol の速度・VRAM 計測。1枚目は torch.compile 込みなので warmup として別記録。"""
import json, os, sys, time, statistics
import torch
from idol import IdolPipeline

ex = sorted(os.listdir('demo/examples'))
names = ['fig-alien.webp', 'fig-knight.webp', 'fig-fox.webp', 'fig-dj.webp', 'fig-ghost.webp',
         'fig-panda.webp', 'fig-viking.webp', 'fig-robot-mech.webp', 'fig-snowman.webp']
imgs = [os.path.join('demo/examples', n) for n in names]
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
t0 = time.time()
pipe = IdolPipeline.from_pretrained('speridlabs/idol')
torch.cuda.synchronize()
print('LOAD %.1fs alloc=%.2fGB' % (time.time() - t0, torch.cuda.memory_allocated() / 1e9), flush=True)
res = []
for ng in [262144, 1048576]:
    for i, p in enumerate(imgs):
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize(); t = time.time()
        o = pipe(p, mode='synthetic', seed=42, num_gaussians=ng)
        torch.cuda.synchronize(); dt = time.time() - t
        pk = torch.cuda.max_memory_allocated() / 1e9
        pr = torch.cuda.max_memory_reserved() / 1e9
        name = os.path.splitext(os.path.basename(p))[0]
        ply = os.path.join(out, f'{name}_{ng}.ply')
        o.gaussian.save_ply(ply)
        o.preprocessed_image.save(os.path.join(out, f'{name}_input.png'))
        r = dict(ng=ng, img=name, sec=dt, peak_alloc_gb=pk, peak_reserved_gb=pr, ply_mb=os.path.getsize(ply) / 1e6)
        res.append(r)
        print(json.dumps(r), flush=True)
for ng in [262144, 1048576]:
    xs = [r for r in res if r['ng'] == ng]
    w = xs[0]; rest = xs[1:] if ng == 262144 else xs  # 262k の1枚目だけ compile 込み
    print('SUMMARY ng=%d warm=%s median=%.2fs min=%.2fs max=%.2fs peak_alloc_max=%.2fGB peak_reserved_max=%.2fGB n=%d' % (
        ng, '%.1fs' % w['sec'] if ng == 262144 else '-', statistics.median(r['sec'] for r in rest),
        min(r['sec'] for r in rest), max(r['sec'] for r in rest),
        max(r['peak_alloc_gb'] for r in rest), max(r['peak_reserved_gb'] for r in rest), len(rest)), flush=True)
json.dump(res, open(os.path.join(out, 'bench.json'), 'w'), indent=1)
