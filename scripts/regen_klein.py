"""作品用の .ply を、FLUX.2-dev（非商用ライセンス）の VAE を一度も読まずに作り直す。

- 重みの config.json の flux2_vae を FLUX.2-klein-4B（Apache 2.0）に書き換えた複製フォルダから読む
- Hugging Face のキャッシュは dev を含まない別フォルダ（idol・klein-4B・DINOv3 だけの symlink）にして、
  オフラインで動かす。dev を読もうとすると「見つからない」で止まるので、読んでいないことの裏付けになる
- seeds.py と同じ条件（既定の optimize=True、mode・seed も同じ）で作り、旧版（dev で作った out/seeds）と比べる

使い方（GPU サーバーの ~/idol-eval/idol-sdk で。スクリプトは ~/idol-eval/ に置く）:
  CUDA_VISIBLE_DEVICES=2 .venv/bin/python ../regen_klein.py ../out/seeds_klein ../out/seeds
"""
import glob, hashlib, json, os, sys, time

HOME = os.path.expanduser('~')
HUB = os.path.join(HOME, '.cache/huggingface/hub')
NODEV = os.path.join(HOME, 'idol-eval/hf-nodev')
KEEP = ['models--speridlabs--idol', 'models--black-forest-labs--FLUX.2-klein-4B',
        'models--facebook--dinov3-vith16plus-pretrain-lvd1689m']
KLEIN = 'black-forest-labs/FLUX.2-klein-4B'

# 1. dev を含まないキャッシュ
os.makedirs(os.path.join(NODEV, 'hub'), exist_ok=True)
for k in KEEP:
    dst = os.path.join(NODEV, 'hub', k)
    if not os.path.exists(dst):
        os.symlink(os.path.join(HUB, k), dst)
assert not glob.glob(os.path.join(NODEV, 'hub', '*FLUX.2-dev*'))
os.environ['HF_HOME'] = NODEV
os.environ['HF_HUB_OFFLINE'] = '1'

# 2. flux2_vae を klein-4B にした重みフォルダ
snap = glob.glob(os.path.join(HUB, 'models--speridlabs--idol/snapshots/*'))[0]
wdir = os.path.join(HOME, 'idol-eval/weights-klein')
os.makedirs(wdir, exist_ok=True)
for f in os.listdir(snap):
    if f.endswith('.safetensors') and not os.path.exists(os.path.join(wdir, f)):
        os.symlink(os.path.realpath(os.path.join(snap, f)), os.path.join(wdir, f))
cfg = json.load(open(os.path.join(snap, 'config.json')))
print('元の image_encoders:', cfg['image_encoders'], flush=True)
cfg['image_encoders']['flux2_vae'] = KLEIN
json.dump(cfg, open(os.path.join(wdir, 'config.json'), 'w'), indent=2)

from idol import IdolPipeline  # noqa: E402  環境変数を決めてから読み込む

pipe = IdolPipeline(wdir)
print('VAE の読み込み元:', pipe.image_encoder.flux2_vae.config._name_or_path,
      '| config の指定:', pipe.config['image_encoders']['flux2_vae'], flush=True)

out, old = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
os.makedirs(out, exist_ok=True)
jobs = [('../inputs/real-drum.png', 'real'), ('../inputs/real-bowl.png', 'real')]
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
for p, m in jobs:
    for s in [1, 2, 3, 4]:
        t = time.time()
        o = pipe(p, mode=m, seed=s)
        n = os.path.splitext(os.path.basename(p))[0]
        ply = f'{out}/{n}_s{s}.ply'
        o.gaussian.save_ply(ply)
        json.dump(o.camera, open(f'{out}/{n}_s{s}_camera.json', 'w'))
        msg = f'{n} s{s} {time.time() - t:.1f}s'
        if old and os.path.exists(f'{old}/{n}_s{s}.ply'):
            msg += ' 旧版とバイト一致=%s' % (md5(ply) == md5(f'{old}/{n}_s{s}.ply'))
            oc = json.load(open(f'{old}/{n}_s{s}_camera.json'))
            msg += ' カメラ差=%s' % {k: round(o.camera[k] - oc[k], 6) for k in oc}
        print(msg, flush=True)
