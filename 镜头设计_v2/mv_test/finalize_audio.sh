#!/usr/bin/env bash
# Two-pass loudness normalisation of a rendered film: -14 LUFS integrated, true peak <= -1.5 dBTP, video copied as is.
# Usage: finalize_audio.sh <in.mp4> <out.mp4>
set -e
FF="D:/。hkbu/molecular science/视觉音乐测试_5分钟_20261018/_deps/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
IN="$1"; OUT="$2"
M=$("$FF" -hide_banner -i "$IN" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
get() { echo "$M" | grep "\"$1\"" | sed 's/.*: "\(.*\)".*/\1/'; }
"$FF" -y -loglevel error -i "$IN" -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true" \
  -ar 48000 -c:a aac -b:a 320k "$OUT"
"$FF" -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:" | tail -2
