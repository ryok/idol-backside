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
| `ply/` `rec/` `audio/` | 生成物・録画・試験音（git 管理外） |

### scripts/

| ファイル | 用途 |
|---|---|
| `seeds.py` | 物ごとに seed 1〜4 で生成し、`.ply` と推定カメラ `_camera.json` を保存 |
| `align.py` | 推定カメラの座標の約束（軸の入れ替え・符号 48 通り）をシルエットの IoU で当てる |
| `orbit.py` / `orbitdiff.py` | 推定カメラから出発して上下軸まわりに回した図と、seed 間の角度ごとの差 |
| `pitchsweep.py` | 仰角を入力の角度から反対側まで振った図（底面が出るか） |
| `render.py` / `render_opaque.py` / `seedsheet.py` | 確認用の簡易スプラット描画（正射影・等方の円。正式なラスタライザではない） |
| `bench.py` / `phase.py` / `qual.py` / `vaeswap.py` | 検証（速度・VRAM、処理段ごとの時間、見た目、VAE 差し替え） |

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

## TouchDesigner

`idol_pc.tox` を読み込み、中の `select` 表で操作する。

- `load_cam` の `module.load('<名前>')` で `ply/<名前>.ply` と `ply/<名前>_camera.json` を読む
- `cam_mode`: 0＝上下軸のまわりを回る（`orbit_deg_per_sec`）、1＝上から下へ回り込む（`sweep_sec`・`sweep_to_deg`）
- `audio_src`: 0＝ファイル、1＝マイク。`bass_gain`・`hit_gain` で強さ、`back_only`=1 で写っていなかった側だけを崩す
- `.ply` と `td/` のパスは今は `/Users/ryookada/work/idol-eval-local/` の絶対パス

## ライセンスの注意

- Idol 本体は Apache 2.0。リクエスト全体では DINOv3（Meta の独自ライセンス、配布時は「Built with DINOv3」表示）と FLUX.2 の VAE を使う
- VAE は FLUX.2-klein-4B（Apache 2.0）のものに差し替えても出力がバイト単位で同じ（`scripts/vaeswap.py`）。ただし Idol の重みが dev の VAE で学習されている点の扱いは未判断
- 背景除去の BiRefNet の元ライセンスは未確認
