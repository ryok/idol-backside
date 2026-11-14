"""1枚あたりの内訳（前処理・エンコード・サンプリング・デコード）と、VAE を klein-4B に替えた時の条件特徴の一致。"""
import time, subprocess, threading, numpy as np, torch
from idol import IdolPipeline
from idol.conditioning import ImageEncoder
from idol.sampler import sample_flow
from tensordict import TensorDict
pipe = IdolPipeline.from_pretrained('speridlabs/idol')
img = 'demo/examples/fig-fox.webp'
clocks = []; stop = False
def poll():
    while not stop:
        r = subprocess.run(['nvidia-smi', '-i', '0', '--query-gpu=clocks.sm,power.draw', '--format=csv,noheader,nounits'],
                           capture_output=True, text=True).stdout.strip()
        clocks.append(r); time.sleep(0.5)
pipe(img, num_gaussians=262144)  # compile
th = threading.Thread(target=poll); th.start()
S = lambda: torch.cuda.synchronize()
for ng in (262144, 1048576):
    S(); t0 = time.time()
    prep = pipe.preprocess(img, mode='synthetic')
    px = torch.from_numpy(np.array(prep)).permute(2, 0, 1).float().div(255)[None].cuda()
    S(); t1 = time.time()
    torch.manual_seed(42); cond = pipe.image_encoder(px)
    S(); t2 = time.time()
    noise = TensorDict({'latent': torch.randn(1, pipe.denoiser.q_token_length, pipe.denoiser.in_channels, device='cuda'),
                        'camera': torch.randn(1, 1, pipe.denoiser.cam_channels, device='cuda')}, batch_size=1, device='cuda')
    with torch.no_grad(), pipe._sampling_settings():
        smp = sample_flow(pipe.denoiser, noise, cond=cond, neg_cond=cond.apply(torch.zeros_like), steps=50,
                          rescale_t=3.0, cfg_strength=3.0, verbose=False, batch_cfg=pipe.optimize)
    S(); t3 = time.time()
    with torch.no_grad(): g = pipe.decode(smp['latent'], ng)
    S(); t4 = time.time()
    print('PHASE ng=%d preprocess=%.2fs encode=%.2fs sample50=%.2fs decode=%.2fs total=%.2fs' % (ng, t1-t0, t2-t1, t3-t2, t4-t3, t4-t0), flush=True)
stop = True; th.join()
cl = [float(c.split(',')[0]) for c in clocks if c]; pw = [float(c.split(',')[1]) for c in clocks if c]
print('CLOCK sm_mhz median=%.0f max=%.0f power_w median=%.0f n=%d' % (np.median(cl), max(cl), np.median(pw), len(cl)), flush=True)
# VAE 差し替え: klein-4B の VAE で同じ画像の条件特徴を作って比べる
enc2 = ImageEncoder('facebook/dinov3-vith16plus-pretrain-lvd1689m', 'black-forest-labs/FLUX.2-klein-4B', device='cuda')
with torch.no_grad():
    c1 = pipe.image_encoder(px); c2 = enc2(px)
for k in c1.keys():
    print('VAESWAP', k, 'max_abs_diff=%.3g' % (c1[k] - c2[k]).abs().max().item(), 'equal=', torch.equal(c1[k], c2[k]), flush=True)
