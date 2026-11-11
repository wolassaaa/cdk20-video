#!/bin/bash
# HKBU SCIE1007 coursework science video. W3 with the dark chrome lock (shot w3k of bl_w3k.py, run inside bl_inserts.py through BL_EXTRA) at 4K 60 fps:
# every one of the 952 frames at 3840x2160, 16 samples, JPEG 95, to C:/render_tmp/w3k/4k/f, then one H.264 clip with the song (Take My Breath from bar 104,
# 207.711 s, 15.867 s, as in render_w3l.sh), and the last frame as PNG at 4K and at 1080p.
# One Blender at a time through gpu_slot.sh, two CPU threads, in chunks of 60 frames (under ten minutes each, so gpu_slot never takes the slot back from a live one).
# A chunk whose frames are all there is skipped: run it again after a stop and it picks up where it left off.
# Run: bash render_w3k_4k.sh
set -o pipefail
HERE="$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")"
INS="$HERE/../s1/inserts"
ART="$(cygpath -m "$(cd "$HERE/../.." && pwd)")"
SONG="D:/。hkbu/molecular science/镜头设计_v3/音乐/原曲/Take My Breath - The Weeknd[Dawn FM].flac"
FF="C:/Program Files/digiKam/ffmpeg.exe"          # has h264_nvenc
FR="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"          # has aac
BLENDER=D:/software/tools/blender.exe
WORK=C:/render_tmp/w3k/4k
N=952
CHUNK=60
export BL_EXTRA="$HERE/bl_w3k.py"
mkdir -p "$WORK/f" "$WORK/log" "$WORK/last4k" "$WORK/last1080"
echo "start $(date '+%H:%M:%S')"
( while :; do sleep 30; powershell -NoProfile -c "Get-Process blender,ffmpeg -ErrorAction SilentlyContinue | % { \$_.PriorityClass='BelowNormal' }" > /dev/null 2>&1; done ) &
PRIO=$!
trap 'kill $PRIO 2>/dev/null' EXIT
have() { local n=0 f; for ((f = $1; f <= $2; f++)); do [ -s "$WORK/f/$(printf 'w3k_%04d.jpg' "$f")" ] && n=$((n + 1)); done; echo $n; }
cd "$INS" || exit 1
for ((a = 0; a < N; a += CHUNK)); do
  b=$((a + CHUNK - 1)); ((b >= N)) && b=$((N - 1))
  if [ "$(have "$a" "$b")" -eq $((b - a + 1)) ]; then echo "skip $a-$b"; continue; fi
  BL_JPEG=1 bash "$ART/gpu_slot.sh" "$BLENDER" -b -t 2 -P bl_inserts.py -- w3k "$WORK/f" "$a" "$b" 16 2 1 > "$WORK/log/w3k_$a.log" 2>&1
  grep -q INSERT_OK "$WORK/log/w3k_$a.log" || { echo "CHUNK_FAILED $a-$b"; tail -5 "$WORK/log/w3k_$a.log"; exit 1; }
  echo "done $a-$b $(date '+%H:%M:%S')"
done
[ "$(have 0 $((N - 1)))" -eq "$N" ] || { echo "CHAIN_FAILED frames"; exit 1; }
echo "frames done $(date '+%H:%M:%S')"
# the last frame as PNG, at 4K and at 1080p
[ -s "$WORK/last4k/w3k_0951.png" ] || BL_FRAMES=951 bash "$ART/gpu_slot.sh" "$BLENDER" -b -t 2 -P bl_inserts.py -- w3k "$WORK/last4k" 0 951 16 2 1 > "$WORK/log/last4k.log" 2>&1
[ -s "$WORK/last1080/w3k_0951.png" ] || BL_FRAMES=951 bash "$ART/gpu_slot.sh" "$BLENDER" -b -t 2 -P bl_inserts.py -- w3k "$WORK/last1080" 0 951 32 1 1 > "$WORK/log/last1080.log" 2>&1
cp "$WORK/last4k/w3k_0951.png" "$HERE/W3_K_last_4k.png" && cp "$WORK/last1080/w3k_0951.png" "$HERE/W3_K_last.png" || { echo "CHAIN_FAILED last frame"; exit 1; }
echo "last frames done $(date '+%H:%M:%S')"
"$FF" -y -v error -framerate 60 -i "$WORK/f/w3k_%04d.jpg" -vf "scale=in_range=pc:out_range=tv,format=yuv420p" -c:v h264_nvenc -preset p6 -rc vbr -cq 17 -b:v 0 -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$WORK/w3k_4k60_silent.mp4" || { echo "CHAIN_FAILED encode"; exit 1; }
"$FR" -y -v error -i "$WORK/w3k_4k60_silent.mp4" -ss 207.711 -t 15.867 -i "$SONG" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -af "volume='if(lt(t,0.05),t/0.05,1)':eval=frame" -shortest -f mp4 "$HERE/W3_K_4k60_1.mp4" || { echo "CHAIN_FAILED mux"; exit 1; }
echo "CHAIN_OK $(date '+%H:%M:%S')"
