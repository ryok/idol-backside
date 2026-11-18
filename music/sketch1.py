"""「裏側」の曲のスケッチ 1（16 小節・96 BPM・40 秒＝上下の回り込み 1 往復）を ableton-cli で Live に作る。

Live のセットを保存しなくても、このスクリプトを流し直せば同じ曲になる。
音の解析（TD）に合わせた決めごと:
- 打音の検出は 2.5kHz 以上の立ち上がり → ハットとリムは間を空けて、強さを揃える（16 分の刻みや一発だけ強いクラッシュは避ける）
- 低音の膨らみは 150Hz 以下 → ベースは音を切って隙間を作る（伸ばしっぱなしにしない）
- 裏に回ったときも崩れが聞こえるように、中高域のベル（主旋律）を通しで鳴らす
使い方: uv run python music/sketch1.py  （Live を起動し AbletonMCP の Remote Script を読み込んだ状態で）
"""
import json, subprocess

BPM = 96
BARS = 16
BEATS = BARS * 4

SLOT = 1  # Session のどの段に作るか。直したら段を変えて流し直す（CLI にクリップ削除が無いため）。0 段目は初版（リム 37・ベースの余韻 3.4 秒で音が割れた）

# 音色の調整（名前, デバイス番号, パラメータ, 値）。初版の書き出しが 0dBFS に張り付き、150Hz 以下が 8 割だった
SETTINGS = [(1, 0, "Release", 45)]          # 808 Pure の余韻 3.39 秒 → 236ms（音を切って隙間を作る）
VOLUMES_DB = {0: -3, 1: -9, 2: -3, 3: -6}

TRACKS = [  # (名前, 読み込む音色の URI)
    ("Drums", "query:Drums#FileId_188735"),          # 808 Core Kit
    ("Bass", "query:Sounds#Bass:FileId_188495"),     # 808 Pure
    ("Bells", "query:Sounds#Mallets:FileId_188344"),  # Basic FM Bells
    ("Pad", "query:Sounds#Pad:FileId_189432"),       # Analog Soft Pad
]

# 2 小節ごとのコード: Dm | Bb | Gm | A を 2 周
CHORDS = ["Dm", "Bb", "Gm", "A"] * 2
BASS_ROOT = {"Dm": 38, "Bb": 34, "Gm": 31, "A": 33}
PAD = {"Dm": [50, 53, 57], "Bb": [50, 53, 58], "Gm": [50, 55, 58], "A": [49, 52, 57]}
BELL = {  # 2 小節ぶんの (音, 拍, 長さ)
    "Dm": [(81, 0, 1), (77, 1.5, .5), (74, 2, 1.5), (76, 3.5, .5), (77, 4, 2), (69, 7, 1)],
    "Bb": [(74, 0, 1), (77, 1.5, .5), (82, 2, 1.5), (81, 3.5, .5), (77, 4, 2), (74, 7, 1)],
    "Gm": [(79, 0, 1), (82, 1.5, .5), (86, 2, 1.5), (84, 3.5, .5), (82, 4, 2), (79, 7, 1)],
    "A":  [(76, 0, 1), (81, 1.5, .5), (85, 2, 1.5), (88, 3.5, .5), (85, 4, 2), (81, 7, 1)],
}
KICK, RIM, HAT = 36, 39, 42   # 37（リム）は 808 Core Kit ではほぼ無音だったので 39 に


def n(p, t, d, v):
    return {"pitch": p, "start_time": float(t), "duration": float(d), "velocity": int(v)}


def drums():
    out = []
    for bar in range(BARS):
        b = bar * 4
        out += [n(HAT, b + 1.5, .25, 90), n(HAT, b + 3.5, .25, 90)]
        if bar < 2:
            continue  # 頭の 2 小節はハットだけ
        out += [n(KICK, b, .5, 110), n(KICK, b + 2.5, .5, 100), n(RIM, b + 3, .25, 95)]
        if bar % 2 == 1:
            out.append(n(KICK, b + 1.75, .25, 90))
    return out


def bass():
    out = []
    for i, c in enumerate(CHORDS):
        b, r = i * 8, BASS_ROOT[c]
        out += [n(r, b, .75, 110), n(r, b + 1.5, .5, 95), n(r, b + 2.75, .5, 100),
                n(r, b + 4, .75, 110), n(r, b + 6, .5, 95)]
    return out


def bells():
    return [n(p, i * 8 + t, d, 95) for i, c in enumerate(CHORDS) for p, t, d in BELL[c]]


def pad():
    return [n(p, i * 8, 7.5, 70) for i, c in enumerate(CHORDS) for p in PAD[c]]


def ab(*a):
    r = subprocess.run(["ableton", *map(str, a)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ableton {' '.join(map(str, a))}: {r.stderr or r.stdout}")
    return r.stdout


def main():
    ab("tempo", BPM)
    info = json.loads(ab("session"))
    # 先頭に MIDI トラックを 4 本用意（足りなければ作る）
    midi = [i for i in range(info["track_count"])
            if json.loads(ab("track", "info", i))["is_midi_track"]]
    while len(midi) < len(TRACKS):
        ab("track", "create", "-i", len(midi))
        midi = list(range(len(midi) + 1))
    parts = [drums(), bass(), bells(), pad()]
    for ti, ((name, uri), notes) in enumerate(zip(TRACKS, parts)):
        t = midi[ti]
        ab("track", "rename", t, name)
        tinfo = json.loads(ab("track", "info", t))
        if not tinfo.get("devices"):
            ab("load", t, uri)
        if tinfo["clip_slots"][SLOT]["has_clip"]:
            raise SystemExit(f"track {t} slot {SLOT} に既にクリップがある。SLOT を変えて流し直す")
        ab("clip", "create", t, SLOT, "--length", BEATS)
        ab("clip", "rename", t, SLOT, f"sketch1.{SLOT} {name}")
        ab("clip", "add-notes", t, SLOT, json.dumps(notes))
        got = json.loads(ab("clip", "notes", t, SLOT))
        cnt = len(got) if isinstance(got, list) else len(got.get("notes", []))
        print(f"{name}: track {t}, notes {len(notes)} -> read back {cnt}")
        ab("clip", "to-arrangement", t, SLOT, 0)
        ab("track", "volume", t, "--db", VOLUMES_DB[ti])
    for t, d, k, v in SETTINGS:
        ab("device", "set", t, d, k, v)


if __name__ == "__main__":
    main()
