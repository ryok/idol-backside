# idol-backside

写真1枚から立体を作る [Idol](https://github.com/speridlabs/idol-sdk)（Speridlabs、Apache 2.0）を使った AV 作品の試作。
仮題は「裏側」。写真に写っていた正面は写真どおりに残り、写っていなかった側（AI が想像した側）だけが音で崩れる。

問い: **見ていない側を、AI は何で埋めるのか**

## 構成

| パス | 中身 |
|---|---|
| `scripts/` | GPU サーバーで動かす生成・検証スクリプト（Idol SDK の `.venv` で実行） |
| `idol_pc.tox` | TouchDesigner の部品（点群の描画・音での崩し・カメラ） |
| `td/` | `idol_pc.tox` の中の GLSL とカメラの Python。TD の DAT がこのファイルと同期している（`syncfile`） |
| `music/` | 曲。`sketch1.py` が ableton-cli で Live にノートを書く、`make_broken.sh` が崩した音と 4ch WAV を作る、`idol_backside Project/idol_backside.als` が Live のセット（Live の `Backup/` などは git 管理外） |
| `ply/` `rec/` `audio/` | 生成物・録画・曲の書き出し（git 管理外） |

### scripts/

| ファイル | 用途 |
|---|---|
| `seeds.py` | 物ごとに seed 1〜4 で生成し、`.ply` と推定カメラ `_camera.json` を保存 |
| `align.py` | 推定カメラの座標の約束（軸の入れ替え・符号 48 通り）をシルエットの IoU で当てる |
| `orbit.py` / `orbitdiff.py` | 推定カメラから出発して上下軸まわりに回した図と、seed 間の角度ごとの差 |
| `pitchsweep.py` | 仰角を入力の角度から反対側まで振った図（底面が出るか） |
| `render.py` / `render_opaque.py` / `seedsheet.py` | 確認用の簡易スプラット描画（正射影・等方の円。正式なラスタライザではない） |
| `bench.py` / `phase.py` / `qual.py` / `vaeswap.py` | 検証（速度・VRAM、処理段ごとの時間、見た目、VAE 差し替え） |
| `regen_klein.py` | 作品用の `.ply` を FLUX.2-dev の VAE を読まずに作り直し、旧版と比べる |
| `birefnet_cmp.py` | Idol 同梱の BiRefNet の重みが ZhengPeng7/BiRefNet（MIT）と同じかを値で比べる |

## 生成の再現

```bash
git clone https://github.com/speridlabs/idol-sdk && cd idol-sdk   # 検証は commit 4702a7f
# 環境構築は idol-sdk の README に従う（検証時は .venv、torch 2.11.0+cu128）
# DINOv3・FLUX.2-dev はゲート付き。Hugging Face でライセンスに同意し hf auth login しておく
cp ../idol-backside/scripts/*.py ..   # スクリプトは idol-sdk の1つ上に置いて使っている
.venv/bin/python ../seeds.py ../out/seeds
```

入力画像（`qual.py` などが読む `../inputs/`）は git 管理外。

同じ seed なら `.ply` はバイト単位で同じになる（`optimize` 既定のまま、再実行で確認）。

作品用は FLUX.2-dev の VAE を使わずに作る: `CUDA_VISIBLE_DEVICES=2 .venv/bin/python ../regen_klein.py ../out/seeds_klein ../out/seeds`（下の「ライセンスの注意」）。

## TouchDesigner

`idol_pc.tox` を読み込み、中の `select` 表で操作する。

- `load_cam` の `module.load('<名前>')` で `ply/<名前>.ply` と `ply/<名前>_camera.json` を読む
- `cam_mode`: 0＝上下軸のまわりを回る（`orbit_deg_per_sec`）、1＝上から下へ回り込む（`sweep_sec`・`sweep_to_deg`）
- `audio_src`: 0＝ファイル、1＝マイク（`audio_dev` の `device`、既定は macOS の既定入力）。`bass_floor`・`hit_floor` は自動ゲインの下限（直近 8 秒の最大がこれより小さいときはこの値で割る。静かな部屋の小さな音で最大まで動かないようにするため。Shure MV7+ を 30cm 以内で叩いたときの値で `hit_floor` 0.0005 に合わせた）。マイクの値は `mic_log`（Execute DAT）が毎フレーム `parent().fetch('miclog')` に 5 分ぶん残す（storage は tox に保存されるので、書き出す前に `parent().unstore('miclog')` で消す）。TD 起動後に macOS 側でマイクのサンプルレートが変わると、`audio_dev` が `Audio driver not detected` で 0 になる。そのときは TD を再起動する。`bass_gain`・`hit_gain` で強さ、`back_only`=1 で写っていなかった側だけを崩す
- 点の描き方: `select` の `pt_style`（0＝箱のインスタンス〔作品はこれ〕、1＝丸い点、2＝ぼかした点）。1・2 は `mat_splat`（GLSL MAT、`td/splat_vert.glsl`・`td/splat_pixel.glsl`）でカメラに向けた板を描く。`pt_size` は板の大きさの倍率、`pt_sharp` は 2 のぼかしの鋭さ。2 は奥→手前に並べ替えずに半透明を重ねるので、一番裏が透ける（比べた結果は LIFE の記録）
- 共通: `bass_gain` 0.3（低音の膨らみは全部の点にかかり、正面まで大きくなるので弱める）、`hit_gain` 1.0（2.0 だとボウルでは強い打音で画面いっぱいに散り、形が消える）。`bg` は背景の明るさ（0〜1、1＝白）
- 物ごとの設定（録画で合わせた値。tox はサンセベリアの設定で保存、2026-11-19）:

  | 物 | カメラ | `dist` | `bg` |
  |---|---|---|---|
  | fig-fox_s1（横から撮影） | `cam_mode` 0（横に回る、毎秒 24 度） | 2.4 | 1（白） |
  | real-drum_s2（真上から） | `cam_mode` 1（上下に回り込む、`sweep_sec` 20） | 1.8 | 1（白） |
  | real-bowl_s1（真上から） | `cam_mode` 1（`sweep_sec` 40） | 2.6 | 0.06（銀色の点が白に溶けるので暗くする） |
  | plant-0577_s1（斜め上 44 度から、作品の主役） | `cam_mode` 1（`sweep_sec` 40、曲の頭で `sweep_t0`） | 3.0 | 0.06 |
  | elephant-0581-big_s3（正面から、`LARGEST=1`、横に回す版） | `cam_mode` 0（毎秒 9 度＝40 秒で 1 周、曲の区切りと揃える） | 3.0 | 0.06 |
- 回り込むほど音も崩す: `audio_file` は 4ch（1・2ch 原音、3・4ch 崩した音。`music/make_broken.sh` で作る）。`snd_mix`（Cross CHOP）で混ぜてスピーカー（`audio_out`）と録画（`rec` の音声）に出す。混ぜる量は `load_cam` の `snd_mix()`＝入力の視点からどれだけ裏に回ったか（カメラと入力の向きの内積から 0＝正面・1＝真裏）を、今のカメラの動きで一番裏に行ったときの値（`back_max()`。`cam_mode` 1 は往復の一番下、0 は真後ろ）で割ったもの。斜めから撮った物は真裏まで回れないので、割り戻して「一番裏＝一番崩れる」にそろえる。`snd_start`（0.1、ここまでは原音のまま）・`snd_amt`（1、0 で崩さない）。点を崩す解析（`mono` 以降）は `snd_clean`（原音の 2ch）だけを見る（崩した音を解析に入れると打音の検出と自動ゲインが角度でずれる）
- 曲: `music/sketch1.py`（16 小節・96 BPM・40 秒＝`sweep_sec` 40 の 1 往復）。打音の検出は 2.5kHz 以上の立ち上がりなのでハットは間を空けて強さを揃え、低音の膨らみは 150Hz 以下なのでベースは音を切る。`mic_log` は混ぜる量も 6 番目に残す
- 録画: `rec_ctl`（Text DAT）。`cue(gain)` で `bass_gain` を入れて音を頭出し、`start(path)` で録画開始（`cam_mode` 0 のときだけ、カメラの回転角を録画の頭で入力の正面に揃える。上下の回り込みで yaw をずらすと、写真の正面からずれた向きで回る）、`stop()` で停止。曲の通しは、`sweep_t0` に今の時刻を入れて頭出しし、すぐ `start` して 124 秒後に `stop` を `run(..., delayFrames=)` で予約する。録画の音は PCM 24bit（`rec` の `audiocodec`。以前の mp3 128k は作品には粗い）。本番は mjpa の mov で録ってから `ffmpeg -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a aac -b:a 320k -movflags +faststart` で mp4 にする（124 秒でサンセベリア 130MB・ゾウ 274MB）
- tox を書き出すときは、`mcp_webserver_base` が中に入っていないこと、storage が空であることを確かめる
- `.ply` と `td/` のパスは今は `/Users/ryookada/work/idol-eval-local/` の絶対パス

## ライセンスの注意

部品ごとのライセンス（2026-11-18 に確認）:

| 部品 | ライセンス | この作品での扱い |
|---|---|---|
| Idol（コード・重み） | Apache 2.0 | そのまま使える。重みは再配布しない |
| FLUX.2-dev の VAE | FLUX Non-Commercial License | **使わない**。作品用の `.ply` は klein-4B で作る（下） |
| FLUX.2-klein-4B の VAE | Apache 2.0 | dev の VAE の代わりに使う |
| DINOv3 ViT-H+/16 | DINOv3 License（2025-08-19 版） | 商用の禁止は無い。重みを配布するときは同意書の写しを付ける（配布しないので該当しない）。研究の結果を発表するときは DINOv3 を使ったと書く（1.b.ii）。軍事・武器などの用途は禁止 |
| BiRefNet（背景除去） | MIT | Idol 同梱の `birefnet.safetensors` の 742 テンソルは、ZhengPeng7/BiRefNet（MIT）の重みと名前・値とも一致（`scripts/birefnet_cmp.py`）。MIT の著作権表示を載せる |

- 以前このファイルに書いた「配布時は Built with DINOv3 と表示」は誤り。今の DINOv3 License（GitHub facebookresearch/dinov3 の LICENSE.md、初版 2025-08-14 から）にその条項は無い。あるのは発表時に使用を明記する条項
- 作品用の `.ply`（ドラム・ボウルの seed 1〜4）は `scripts/regen_klein.py` で、FLUX.2-dev の VAE を一度も読まずに作り直した。dev を含まない Hugging Face のキャッシュをオフラインで使い、VAE は klein-4B を読んだことをログで確認。8 個とも dev で作った旧版とバイト単位で一致した（`optimize` 既定のまま）ので、今の `ply/` はそのまま使える
- 残る判断: Idol の重み自体が dev の VAE の特徴で学習されている点がライセンス上どう扱われるかは、ここでは判断していない
- なお idol-sdk の今の README には、`IdolPipeline.from_pretrained(..., image_encoders={"flux2_vae": ".../FLUX.2-klein-4B"})` で VAE を差し替える方法が載っている（検証した commit 4702a7f には無い）
