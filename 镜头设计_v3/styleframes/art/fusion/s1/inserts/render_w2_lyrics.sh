#!/bin/bash
# HKBU SCIE1007 coursework science video. W2 with its burned-in rhyming captions: shot d's frames become the base clip, Remotion lays the captions over it
# (composition W2Lyrics in src/v3/fusion/entry.jsx, words in 音乐/W2_押韵字幕.md), then the song goes under it from 50.446 s, so its first sung bar (52.39 s) lands on beat 4, for 25.3 s (version 1 started at 5.732 s, the bass drop on the splat, but nobody sings there).
# Stops at the first failure and says so. Run: bash render_w2_lyrics.sh <frame dir> <out.mp4>
set -o pipefail
export TEMP=D:/render_tmp TMP=D:/render_tmp
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$1"; OUT="$2"
PUB="D:/。hkbu/molecular science/镜头设计_v3/remotion_public"
SONG="D:/。hkbu/molecular science/镜头设计_v3/音乐/原曲/Harder, Better, Faster, Stronger - Daft Punk[Harder, Better, Faster, Stronger].flac"
FF="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
BUNDLE="D:/render_tmp/w2_bundle"
cd "$HERE" && python take_d.py "$SRC" "$PUB/fusion_s1/w2_shake_3.mp4" | grep -q TAKE_OK || { echo CHAIN_FAILED base; exit 1; }
cd "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/entry.jsx --out-dir="$BUNDLE" --public-dir="$PUB" > "$BUNDLE.log" 2>&1 || { tail -20 "$BUNDLE.log"; echo CHAIN_FAILED bundle; exit 1; }
npx remotion render "$BUNDLE" W2Lyrics "D:/render_tmp/w2_lyrics_silent.mp4" --image-format=jpeg --jpeg-quality=95 --crf=16 --color-space=bt709 --concurrency=4 >> "$BUNDLE.log" 2>&1 || { tail -30 "$BUNDLE.log"; echo CHAIN_FAILED remotion; exit 1; }
"$FF" -y -v error -i "D:/render_tmp/w2_lyrics_silent.mp4" -ss 50.446 -t 25.3 -i "$SONG" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 -af "volume='if(gt(t,24.3),max(0,1-(t-24.3)),1)':eval=frame" -shortest "$OUT" || { echo CHAIN_FAILED audio; exit 1; }
[ -s "$OUT" ] && echo CHAIN_OK || echo CHAIN_FAILED output
