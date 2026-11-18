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

def _back(y, pt):
    """視点 (y, pt) が入力の視点からどれだけ裏か（0＝正面、1＝真裏）"""
    y0, p0 = _f('yaw'), _f('pitch')
    d = math.cos(pt)*math.cos(p0)*math.cos(y - y0) + math.sin(pt)*math.sin(p0)
    return (1 - d) / 2

def backness():
    """今のカメラが入力の視点からどれだけ裏に回ったか。音の崩れに使う"""
    return _back(*angles())

def back_max():
    """今のカメラの動きで一番裏に回ったときの backness。
    cam_mode 1: 往復の一番下（sweep_to_deg）、cam_mode 0: 横に 180 度。
    斜めから撮った物は真裏まで行けないので、ここで割り戻して「一番裏＝一番崩れる」にそろえる（2026-11-19）"""
    lim = math.radians(85)
    if int(_f('cam_mode')) == 0:
        return _back(_f('yaw') + math.pi, _f('pitch'))
    return _back(_f('yaw') + math.radians(_f('view_deg')), max(-lim, min(lim, math.radians(_f('sweep_to_deg')))))

def snd_mix():
    """崩れた音の混ぜ具合。snd_start（一番裏までの道のりに対する割合）までは原音のまま、一番裏で snd_amt"""
    s = _f('snd_start'); w = (backness() / max(back_max(), 1e-6) - s) / max(1 - s, 1e-6)
    return max(0.0, min(1.0, w)) * _f('snd_amt')
