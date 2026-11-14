"""予測された入力カメラから出発して、上向き軸のまわりを回るカメラで描く（透視投影の簡易スプラット）。
座標の約束は align.py で当てたもの: world = M @ (dx,dy,dz)、上は M @ (0,0,1) = -y。"""
import os, sys, json, math, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import load
M = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)

def view(xyz, col, a, s, cam, dyaw_deg, size=256):
    y, p, rad, fov = cam["yaw"] + math.radians(dyaw_deg), cam["pitch"], cam["radius"], cam["fov"]
    d = M @ np.array([math.cos(p) * math.sin(y), math.cos(p) * math.cos(y), math.sin(p)])
    up = M @ np.array([0, 0, 1.0]); c = d * rad
    f = -d; r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    q = (xyz - c) @ np.stack([r, u, f]).T
    z = q[:, 2]; foc = 0.5 * size / math.tan(math.radians(fov) / 2)
    px = q[:, 0] / z * foc + size / 2; py = -q[:, 1] / z * foc + size / 2
    rr = np.clip(s / z * foc, 0.5, 4)
    img = np.zeros((size, size, 3)); acc = np.zeros((size, size))
    for i in np.argsort(-z):                       # 遠い順
        if a[i] < 0.05 or z[i] <= 1e-3: continue
        x0, x1 = int(max(0, px[i] - rr[i])), int(min(size, px[i] + rr[i] + 1))
        y0, y1 = int(max(0, py[i] - rr[i])), int(min(size, py[i] + rr[i] + 1))
        if x0 >= x1 or y0 >= y1: continue
        al = a[i] * 0.9
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - al) + col[i] * al
        acc[y0:y1, x0:x1] = acc[y0:y1, x0:x1] * (1 - al) + al
    return Image.fromarray((np.clip(img + (1 - acc[..., None]), 0, 1) * 255).astype(np.uint8))

if __name__ == "__main__":
    d, n, inp = sys.argv[1], sys.argv[2], sys.argv[3]
    W = 256; m = Image.new("RGB", (W * 5, W * 4), "white")
    for i, s in enumerate((1, 2, 3, 4)):
        xyz, col, a, sc = load(f"{d}/{n}_s{s}.ply"); cam = json.load(open(f"{d}/{n}_s{s}_camera.json"))
        m.paste(Image.open(inp).convert("RGB").resize((W, W)), (0, i * W))
        for k, g in enumerate((0, 90, 180, 270)):
            m.paste(view(xyz, col, a, sc, cam, g, W), ((k + 1) * W, i * W))
    m.save(f"{d}/{n}_orbit.jpg", quality=88)
