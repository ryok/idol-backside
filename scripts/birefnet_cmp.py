"""Idol 同梱の birefnet.safetensors が ZhengPeng7/BiRefNet（MIT）の重みと同じか。キー名の違いは値で対応を取る"""
import glob, hashlib, os
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
a = load_file(glob.glob(os.path.expanduser("~/.cache/huggingface/hub/models--speridlabs--idol/snapshots/*/birefnet.safetensors"))[0])
b = load_file(hf_hub_download("ZhengPeng7/BiRefNet", "model.safetensors", cache_dir=os.path.expanduser("~/idol-eval/hf-birefnet")))
print("tensors", len(a), len(b), "params", sum(v.numel() for v in a.values()), sum(v.numel() for v in b.values()))
same_keys = set(a) & set(b)
print("同名キー", len(same_keys))
h = lambda t: hashlib.md5(t.float().contiguous().numpy().tobytes()).hexdigest()
hb = {}
for k, v in b.items(): hb.setdefault((tuple(v.shape), h(v)), []).append(k)
miss = [k for k, v in a.items() if (tuple(v.shape), h(v)) not in hb]
print("値まで一致しない idol 側テンソル", len(miss), miss[:5])
print("dtype", {str(v.dtype) for v in a.values()}, {str(v.dtype) for v in b.values()})
