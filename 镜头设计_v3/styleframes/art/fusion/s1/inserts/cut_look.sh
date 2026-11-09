#!/bin/bash
# HKBU SCIE1007 coursework science video. Look test on shot k: joins the lk1 or lk2 frames into a 1080p 30 fps take from 287.0 to 312.0 s (the holds between moves are
# one frame each, as in take_k.py), lays the words and the pen marks on it with Remotion (look.jsx from make_look_jsx.py), and writes look_k_v1.mp4 or look_k_v2.mp4.
# Run: bash cut_look.sh <lk1|lk2> <frames dir> <work dir>
export TEMP=D:/render_tmp TMP=D:/render_tmp          # the Remotion ffmpeg is refused writes under C:, so its pre-encode goes to D:
V="$1"; FR="$2"; W="$3"
ROOT="D:/。hkbu/molecular science"
HERE="$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts"
A="$ROOT/镜头设计_v2/tests/T4_remotion/src/v3/fusion"
OUT="$ROOT/镜头设计_v3/styleframes/art/fusion/look/look_k_v${V#lk}.mp4"
FF="C:/Program Files/digiKam/ffmpeg.exe"          # the Remotion ffmpeg has x264 but almost no filters; this one has both
PUB="$W/pub_$V"
mkdir -p "$PUB/fusion_s1" "$(dirname "$OUT")"
cp -r "$ROOT/镜头设计_v3/remotion_public/fusion_s1/fonts" "$PUB/fusion_s1/"
date '+start %H:%M:%S'
python - "$FR" "$V" "$PUB/fusion_s1/look_take.mp4" "$FF" <<'EOF' || { echo CUT_FAILED take; exit 1; }
import subprocess, sys
fr, v, out, ff = sys.argv[1:]
moves = [(72, 780), (1100, 1426)]
seq = []
for n in range(72, 1572, 2):                     # 287.0 to 312.0 s on the 60 fps clock of shot k, every other frame
    held = next((b for a, b in reversed(moves) if n > b), None) if not any(a <= n <= b for a, b in moves) else n
    seq.append(n if held == n else held)
p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "png", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
                      "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out], stdin=subprocess.PIPE)
for n in seq:
    p.stdin.write(open("%s/%s_%04d.png" % (fr, v, n), "rb").read())
p.stdin.close()
if p.wait():
    raise SystemExit("TAKE_FAILED")
print("take frames", len(seq))
EOF
python "$HERE/make_look_jsx.py" || exit 1
cd "$ROOT/镜头设计_v2/tests/T4_remotion" || exit 1
npx remotion bundle src/v3/fusion/look.jsx --out-dir="$W/bundle_$V" --public-dir="$PUB" 2>&1 | tail -1
mv "$A/look.jsx" "$W/look.jsx"
# on 11-09 the Remotion ffmpeg was refused every write, so Remotion writes frames and the digiKam ffmpeg encodes them
rm -rf "$W/seq_$V"
npx remotion render "$W/bundle_$V" LookK "$W/seq_$V" --sequence --image-format=jpeg --jpeg-quality=95 --concurrency="${JOBS:-4}" > "$W/cut_$V.log" 2>&1 || { tail -20 "$W/cut_$V.log"; echo CUT_FAILED remotion; exit 1; }
"$FF" -y -loglevel error -framerate 30 -i "$W/seq_$V/element-%03d.jpeg" -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$OUT" || { ls "$W/seq_$V" | head -3; echo CUT_FAILED encode; exit 1; }
date '+end %H:%M:%S'
echo CUT_OK "$OUT"
