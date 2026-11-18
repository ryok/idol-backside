"""新しい写真から .ply を作る（FLUX.2-dev を読まない作り方。仕組みは regen_klein.py と同じ）。

前処理後の画像（背景を消して切り抜いたもの）も <名前>_prep.png に残し、背景の消え方を確かめられるようにする。
写真の向きは EXIF を当てて直してから渡す（Idol は EXIF の回転を見ない）。

使い方（GPU サーバーの ~/idol-eval/idol-sdk で。スクリプトは ~/idol-eval/ に置く）:
  CUDA_VISIBLE_DEVICES=2 .venv/bin/python ../gen_klein.py <出力フォルダ> <mode> <seed,seed,...> <画像>...
  例: ... ../gen_klein.py ../out/new real 1 ../inputs/plant-a.png ../inputs/elephant-a.png
  LARGEST=1 を付けると、切り抜きの一番大きい塊だけ残す（名前に -big が付く）
"""
import glob, json, os, sys, time

HOME = os.path.expanduser('~')
HUB = os.path.join(HOME, '.cache/huggingface/hub')
NODEV = os.path.join(HOME, 'idol-eval/hf-nodev')
assert os.path.isdir(os.path.join(NODEV, 'hub')), 'regen_klein.py を一度流して hf-nodev を作っておく'
assert not glob.glob(os.path.join(NODEV, 'hub', '*FLUX.2-dev*'))
os.environ['HF_HOME'] = NODEV
os.environ['HF_HUB_OFFLINE'] = '1'
wdir = os.path.join(HOME, 'idol-eval/weights-klein')
assert json.load(open(os.path.join(wdir, 'config.json')))['image_encoders']['flux2_vae'] == 'black-forest-labs/FLUX.2-klein-4B'

from PIL import Image, ImageOps  # noqa: E402
from idol import IdolPipeline  # noqa: E402

out, mode, seeds, imgs = sys.argv[1], sys.argv[2], [int(s) for s in sys.argv[3].split(',')], sys.argv[4:]
os.makedirs(out, exist_ok=True)
pipe = IdolPipeline(wdir)
print('VAE の読み込み元:', pipe.image_encoder.flux2_vae.config._name_or_path, flush=True)
def largest_only(im):
    """BiRefNet の切り抜きから一番大きい塊だけ残す（床のシールや紙片が物と一緒に残るため）。
    アルファ付きで渡すと Idol は背景除去を飛ばしてこのアルファを使う"""
    import numpy as np
    from collections import deque
    from PIL import ImageFilter
    w, h = im.size; sc = pipe.config['image_size'] / min(w, h)
    im = im.resize((round(w * sc), round(h * sc)), Image.LANCZOS)
    rgba = pipe.background_remover.remove_background(im)
    a = np.array(rgba.getchannel(3))
    # 1/4 に縮めた 2 値マスクで塊を数える（venv に scipy が無いので幅優先で塗る）
    sm = np.array(Image.fromarray(((a > 127) * 255).astype(np.uint8)).resize((a.shape[1] // 4, a.shape[0] // 4))) > 127
    lab = np.zeros(sm.shape, int); k = 0; sizes = [0]
    for y0, x0 in zip(*np.nonzero(sm)):
        if lab[y0, x0]: continue
        k += 1; lab[y0, x0] = k; q = deque([(y0, x0)]); c = 0
        while q:
            y, x = q.popleft(); c += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < sm.shape[0] and 0 <= xx < sm.shape[1] and sm[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = k; q.append((yy, xx))
        sizes.append(c)
    if k > 1:
        keep = Image.fromarray(((lab == int(np.argmax(sizes))) * 255).astype(np.uint8))
        keep = keep.filter(ImageFilter.MaxFilter(5)).resize((a.shape[1], a.shape[0]))
        a = np.where(np.array(keep) > 127, a, 0).astype(np.uint8)
    print(f'  塊 {k} 個（大きさ {sorted(sizes[1:], reverse=True)[:5]}）→ 一番大きい塊だけ残した', flush=True)
    rgba.putalpha(Image.fromarray(a))
    return rgba


LARGEST = os.environ.get('LARGEST') == '1'
for p in imgs:
    n = os.path.splitext(os.path.basename(p))[0]
    im = ImageOps.exif_transpose(Image.open(p)).convert('RGB')
    if LARGEST:
        im = largest_only(im)
        n += '-big'
    for s in seeds:
        t = time.time()
        o = pipe(im, mode=mode, seed=s)
        o.gaussian.save_ply(f'{out}/{n}_s{s}.ply')
        json.dump(o.camera, open(f'{out}/{n}_s{s}_camera.json', 'w'))
        o.preprocessed_image.save(f'{out}/{n}_prep.png')
        print(n, s, '%.1fs' % (time.time() - t), {k: round(v, 3) for k, v in o.camera.items()}, flush=True)
