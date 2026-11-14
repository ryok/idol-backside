import json, math

def load(name):
    """.ply とその推定カメラ（yaw/pitch）を選ぶ。その他の行（gain など）は残す。"""
    d = json.load(open('/Users/ryookada/work/idol-eval-local/ply/%s_camera.json' % name))
    t = op('select')
    t['name', 1] = name; t['yaw', 1] = d['yaw']; t['pitch', 1] = d['pitch']
    # 上下に回り込む先: 入力の仰角の反対側（真横から撮った写真でも 60 度は下に回る）
    p = math.degrees(d['pitch'])
    t['sweep_to_deg', 1] = -max(abs(p), 60.0) if p >= 0 else max(abs(p), 60.0)

def _f(k):
    return float(op('select')[k, 1])

def angles():
    """今のカメラの yaw, pitch（ラジアン）。
    cam_mode 0: 入力の視点から上下軸のまわりを回る（orbit_deg_per_sec）
    cam_mode 1: yaw は入力のまま、仰角を入力の角度 → sweep_to_deg → 入力の角度と往復（1往復 sweep_sec 秒）"""
    yaw = _f('yaw') + math.radians(_f('view_deg'))
    pitch = _f('pitch')
    if int(_f('cam_mode')) == 0:
        yaw += math.radians(_f('orbit_deg_per_sec') * absTime.seconds)
    else:
        ph = (1 - math.cos(2 * math.pi * (absTime.seconds - _f('sweep_t0')) / max(_f('sweep_sec'), 1))) / 2   # 0→1→0
        if _f('sweep_phase') >= 0: ph = _f('sweep_phase')   # 確認用: 0〜1 で位置を固定（-1 で無効）
        pitch = pitch + (math.radians(_f('sweep_to_deg')) - pitch) * ph
    lim = math.radians(85)   # 真上・真下ではカメラの上向きが決まらないので手前で止める
    return yaw, max(-lim, min(lim, pitch))

def campos(i):
    y, p = angles(); d = _f('dist')
    return (d * math.cos(p) * math.sin(y), d * math.sin(p), -d * math.cos(p) * math.cos(y))[i]
