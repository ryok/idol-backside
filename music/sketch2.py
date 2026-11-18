"""「裏側」の曲（48 小節・96 BPM・120 秒＝上下の回り込み 3 往復）を ableton-cli で Live に作る。

スケッチ 1（16 小節）を真ん中に置き、前後に「入り」と「山」を足した 3 部構成。
- 1 部（0〜15 小節）: ハット・ベル・パッド・まばらなベースだけ。パッドは 1 オクターブ上（150Hz 以下を空ける）
- 2 部（16〜31 小節）: スケッチ 1 そのまま（キック・リムが入る）
- 3 部（32〜47 小節）: コードが B♭–C–Dm–A に動き、ベルに合いの手が増える。最後の 2 小節は Dm で閉じる
決めごと（TD の解析に合わせる。理由は sketch1.py）:
- 区切りは 16 小節ごと＝回り込みの 1 往復の頭（正面が見えて音がきれいな所）。真裏（各部の 8〜9 小節目）は音を足し引きしない
- ハットは全小節で 1.5 拍と 3.5 拍に 2 発（打音の検出はこれだけで決まる）
- ベースはどの部にも隙間つきで入れる（低音が無い部があると自動ゲインでパッドが膨らむ）
使い方: uv run python music/sketch2.py  （Live を起動し AbletonMCP の Remote Script を読み込んだ状態で）
"""
import json

from sketch1 import BASS_ROOT, BELL, HAT, KICK, PAD, RIM, ab, bass, n

BARS = 48
BEATS = BARS * 4
SLOT = 2  # 0 段目は初版、1 段目はスケッチ 1

BASS_ROOT = {**BASS_ROOT, "C": 36}
PAD = {**PAD, "C": [52, 55, 60]}
BELL = {**BELL, "C": [(79, 0, 1), (84, 1.5, .5), (88, 2, 1.5), (86, 3.5, .5), (84, 4, 2), (79, 7, 1)]}
FILL = {  # 3 部だけの合いの手（2 小節のうち 5〜6.5 拍、ベルの伸ばしの後ろ）
    "Bb": [(86, 5.5, .5), (84, 6, .5)], "C": [(91, 5.5, .5), (88, 6, .5)],
    "Dm": [(86, 5.5, .5), (84, 6, .5)], "A": [(88, 5.5, .5), (85, 6, .5)],
}

# (開始小節, 2 小節ごとのコード 8 個)
SECTIONS = [
    (0, ["Dm", "Bb", "Gm", "A"] * 2),
    (16, ["Dm", "Bb", "Gm", "A"] * 2),
    (32, ["Bb", "C", "Dm", "A", "Bb", "C", "A", "Dm"]),
]
END = 46  # 最後の 2 小節（Dm）は閉じるだけ


def drums():
    out = []
    for bar in range(BARS):
        b = bar * 4
        out += [n(HAT, b + 1.5, .25, 90), n(HAT, b + 3.5, .25, 90)]
        if bar < 16 or bar >= END:
            continue
        out += [n(KICK, b, .5, 110), n(KICK, b + 2.5, .5, 100), n(RIM, b + 3, .25, 95)]
        if bar % 2 == 1:
            out.append(n(KICK, b + 1.75, .25, 90))
        if bar >= 32:
            out.append(n(RIM, b + 1, .25, 80))
    out.append(n(KICK, END * 4, .5, 110))
    return out


def basses():
    out = []
    for start, chords in SECTIONS:
        b0 = start * 4
        if start == 0:  # 1 部はまばら: 1 小節に 1 音
            out += [n(BASS_ROOT[c], b0 + i * 8 + k, .75, 100) for i, c in enumerate(chords) for k in (0, 4)]
        else:
            import sketch1
            sketch1.CHORDS, sketch1.BASS_ROOT = chords, BASS_ROOT
            out += [{**x, "start_time": x["start_time"] + b0} for x in bass()
                    if x["start_time"] + b0 < END * 4]
    out.append(n(BASS_ROOT["Dm"], END * 4, .75, 110))
    return out


def bells():
    out = []
    for start, chords in SECTIONS:
        b0 = start * 4
        for i, c in enumerate(chords):
            t0 = b0 + i * 8
            if t0 >= END * 4:
                continue
            notes = BELL[c] + (FILL[c] if start == 32 else [])
            out += [n(p, t0 + t, d, 95) for p, t, d in notes]
    out.append(n(74, END * 4, 6, 95))
    return out


def pads():
    out = []
    for start, chords in SECTIONS:
        up = 12 if start == 0 else 0
        out += [n(p + up, start * 4 + i * 8, 7.5, 70) for i, c in enumerate(chords) for p in PAD[c]]
    return out


def lint(parts):
    names = ["Drums", "Bass", "Bells", "Pad"]
    for name, notes in zip(names, parts):
        end = max(x["start_time"] + x["duration"] for x in notes)
        assert end <= BEATS, (name, end)
    hats = [0] * BARS
    for x in parts[0]:
        if x["pitch"] == HAT:
            hats[int(x["start_time"] // 4)] += 1
    assert hats == [2] * BARS, hats
    bs = sorted(parts[1], key=lambda x: x["start_time"])
    gaps = [b["start_time"] - (a["start_time"] + a["duration"]) for a, b in zip(bs, bs[1:])]
    assert min(gaps) >= .25, min(gaps)
    for start, _ in SECTIONS:
        lo = min(x["pitch"] for x in parts[3] if start * 4 <= x["start_time"] < start * 4 + 64)
        print(f"{start:2d} 小節〜 パッドの最低音 {lo}（{440 * 2 ** ((lo - 69) / 12):.0f}Hz）")
    print("ノート数", {k: len(v) for k, v in zip(names, parts)}, "ベースの隙間の最小", min(gaps), "拍")


def main(dry=False):
    parts = [drums(), basses(), bells(), pads()]
    lint(parts)
    if dry:
        return
    ab("tempo", 96)
    for t, (name, notes) in enumerate(zip(["Drums", "Bass", "Bells", "Pad"], parts)):
        info = json.loads(ab("track", "info", t))
        assert info["name"] == name, info["name"]
        if len(info["clip_slots"]) <= SLOT:
            raise SystemExit(f"track {t} に {SLOT} 段目が無い（Session で scene を足す）")
        if info["clip_slots"][SLOT]["has_clip"]:
            raise SystemExit(f"track {t} slot {SLOT} に既にクリップがある。SLOT を変えて流し直す")
        ab("clip", "create", t, SLOT, "--length", BEATS)
        ab("clip", "rename", t, SLOT, f"sketch2 {name}")
        ab("clip", "add-notes", t, SLOT, json.dumps(notes))
        got = json.loads(ab("clip", "notes", t, SLOT))
        cnt = len(got) if isinstance(got, list) else len(got.get("notes", []))
        print(f"{name}: track {t}, notes {len(notes)} -> read back {cnt}")
        assert cnt == len(notes)
        ab("clip", "to-arrangement", t, SLOT, 0)


if __name__ == "__main__":
    import sys
    main(dry="--dry" in sys.argv)
