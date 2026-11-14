"""VAE を dev → klein-4B に替えても同じ条件特徴・同じ出力になるか。latent_dist.sample() が乱数を使うので seed を揃える。"""
import numpy as np, torch, os
from idol import IdolPipeline
from idol.conditioning import ImageEncoder
pipe = IdolPipeline.from_pretrained('speridlabs/idol', optimize=False)
img = 'demo/examples/fig-fox.webp'
px = torch.from_numpy(np.array(pipe.preprocess(img))).permute(2, 0, 1).float().div(255)[None].cuda()
def feat(enc, seed):
    torch.manual_seed(seed); return enc(px)
a = feat(pipe.image_encoder, 42); a2 = feat(pipe.image_encoder, 42); a3 = feat(pipe.image_encoder, 7)
enc_k = ImageEncoder('facebook/dinov3-vith16plus-pretrain-lvd1689m', 'black-forest-labs/FLUX.2-klein-4B', device='cuda')
b = feat(enc_k, 42)
for k in a.keys():
    print('FEAT', k, 'dev_vs_dev_same_seed equal=%s' % torch.equal(a[k], a2[k]),
          'dev_vs_dev_other_seed max=%.3g' % (a[k] - a3[k]).abs().max().item(),
          'dev_vs_klein_same_seed equal=%s max=%.3g' % (torch.equal(a[k], b[k]), (a[k] - b[k]).abs().max().item()), flush=True)
# 出力の .ply まで比べる（optimize=False で決定的に）
o1 = pipe(img, seed=42).gaussian
pipe.image_encoder = enc_k
o2 = pipe(img, seed=42).gaussian
o1.save_ply('/tmp/idol_dev.ply'); o2.save_ply('/tmp/idol_klein.ply')
d1, d2 = open('/tmp/idol_dev.ply', 'rb').read(), open('/tmp/idol_klein.ply', 'rb').read()
print('PLY bytes_equal=%s size=%d' % (d1 == d2, len(d1)), flush=True)
