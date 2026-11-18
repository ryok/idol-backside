#!/bin/bash
# 書き出した曲から「崩した音」を作り、原音（1・2ch）＋崩した音（3・4ch）の 4ch WAV にする。TD の audio_file はこれを読む
# usage: music/make_broken.sh audio/sketch1.wav [秒数]   → audio/sketch1_x_smear.wav（採用: smear、2026-11-18）
# 試した他の案（不採用）: crush = aresample=4000,acrusher=bits=5:mode=log:aa=0,aresample=48000
#                          wash  = aecho=0.8:0.9:60|170|330|610:0.6|0.5|0.45|0.4,lowpass=f=1200,volume=0.82
set -euo pipefail
src=$1; dur=${2:-40}
base=${src%.wav}
mkdir -p "$(dirname "$src")/broken"
broken="$(dirname "$src")/broken/$(basename "$base")_smear.wav"
# smear: 周波数ごとの大きさは残し、位相をランダムにしてにじませる。音量は原音と 1dB 以内に揃える
ffmpeg -v error -y -i "$src" -t "$dur" -af "afftfilt=real='hypot(re,im)*cos(2*PI*random(0))':imag='hypot(re,im)*sin(2*PI*random(1))':win_size=4096:overlap=0.75,volume=1.8,alimiter=limit=0.85:level=false" "$broken"
ffmpeg -v error -y -t "$dur" -i "$src" -i "$broken" -filter_complex "[0:a][1:a]amerge=inputs=2[a]" -map "[a]" -c:a pcm_s16le -t "$dur" "${base}_x_smear.wav"
for f in "$src" "$broken"; do echo "$f: $(ffmpeg -hide_banner -t "$dur" -i "$f" -af volumedetect -f null - 2>&1 | grep -oE 'mean_volume: [-0-9.]+ dB')"; done
