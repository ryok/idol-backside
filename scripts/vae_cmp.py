"""FLUX.2-dev の VAE と FLUX.2-klein-4B の VAE の重みを値で比べる。

dev 版は fp32、klein 版は bf16 で保存されている。dev 版を bf16 にそろえてテンソルごとに一致を見る。
2026-11-19 の結果: 251 テンソルすべて一致（名前も同じ）。Idol は VAE を bf16 にして読むので、
dev と klein のどちらを読んでも同じ重みになる（regen_klein.py で .ply がバイト一致した理由）。

使い方（GPU サーバーの ~/idol-eval/idol-sdk で。dev と klein の両方が HF のキャッシュにあること）:
  .venv/bin/python ../vae_cmp.py
"""
import glob, os
import torch
from safetensors.torch import load_file

H = os.path.expanduser('~')
pat = 'models--black-forest-labs--%s/snapshots/*/vae/diffusion_pytorch_model.safetensors'
dev = glob.glob(os.path.join(H, '.cache/huggingface/hub', pat % 'FLUX.2-dev'))
kl = glob.glob(os.path.join(H, 'idol-eval/hf-nodev/hub', pat % 'FLUX.2-klein-4B')) + \
     glob.glob(os.path.join(H, '.cache/huggingface/hub', pat % 'FLUX.2-klein-4B'))
print(dev, kl)
a, b = load_file(dev[0]), load_file(kl[0])
print('keys dev', len(a), 'klein', len(b), 'same names', set(a) == set(b))
print('dtypes', {str(v.dtype) for v in a.values()}, {str(v.dtype) for v in b.values()})
eq = sum(torch.equal(a[k].to(torch.bfloat16), b[k].to(torch.bfloat16)) for k in a if k in b)
mx = max((a[k].float() - b[k].float()).abs().max().item() for k in a if k in b)
print('bf16 equal tensors', eq, '/', len(a), 'max abs diff (fp32)', mx)
