"""新しい写真の比べ表: 1 行に 1 枚。左から 前処理後の入力 | 横に 0・90・180・270 度 | 真裏の高さ（仰角を反転）。
使い方: python newsheet.py <フォルダ> <seed> <名前>...   → <フォルダ>/sheet_s<seed>.jpg"""
import json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import load
import orbit

d, s, names = sys.argv[1], sys.argv[2], sys.argv[3:]
W = 220
m = Image.new("RGB", (W * 6, W * len(names)), "white")
for i, n in enumerate(names):
    xyz, col, a, sc = load(f"{d}/{n}_s{s}.ply"); cam = json.load(open(f"{d}/{n}_s{s}_camera.json"))
    m.paste(Image.open(f"{d}/{n}_prep.png").convert("RGB").resize((W, W)), (0, i * W))
    for k, g in enumerate((0, 90, 180, 270)):
        m.paste(orbit.view(xyz, col, a, sc, cam, g, W), ((k + 1) * W, i * W))
    m.paste(orbit.view(xyz, col, a, sc, dict(cam, pitch=-cam["pitch"]), 0, W), (5 * W, i * W))
m.save(f"{d}/sheet_s{s}.jpg", quality=88)
print(f"{d}/sheet_s{s}.jpg")
