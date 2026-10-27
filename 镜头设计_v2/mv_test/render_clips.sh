#!/usr/bin/env bash
# Renders the 3D clips for the 5-minute music test on the RTX 5080 (PNG frames, then an MP4 per clip).
set -e
ROOT="D:/。hkbu/molecular science/镜头设计_v2"
MV="$ROOT/mv_test"
BLENDER=/d/software/tools/blender
FF="D:/。hkbu/molecular science/视觉音乐测试_5分钟_20261018/_deps/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
PDB="D:/dsh project/cdk20-film/assets/structures/CDK20_py.pdb"
LIVER="D:/dsh project/cdk20-film/assets/structures/FMA7197_liver.stl"
POSES="$ROOT/tests/T6_molecules/poses.json"
export CLIP_HELPER_DIR="$MV"
export CLIP_SAMPLES="${CLIP_SAMPLES:-64}"   # 64 samples + OptiX denoise is clean enough for moving shots
export CLIP_NOHAZE=1
ONLY="${ONLY:-}"                           # e.g. ONLY="wall_dolly pose_048" renders just those

clip() {  # name seconds move amount -- blender args...
  local name=$1 secs=$2 move=$3 amount=$4; shift 4
  if [ -n "$ONLY" ] && [[ " $ONLY " != *" $name "* ]]; then return; fi
  local t0=$(date +%s)
  mkdir -p "$MV/clips/$name"
  CLIP_SECONDS=$secs CLIP_MOVE=$move CLIP_AMOUNT=$amount CLIP_OUT="$MV/clips/$name" \
    "$BLENDER" -b "$@" 2>&1 | grep -E "CLIP DONE|Error|Traceback" || true
  "$FF" -y -loglevel error -framerate 30 -i "$MV/clips/$name/f%04d.png" -filter_complex \
    "[0]format=gbrp,split[a][b];[b]gblur=sigma=18,eq=saturation=1.3[g];[a][g]blend=all_mode=screen:all_opacity=0.5,format=yuv420p" \
    -c:v libx264 -crf 15 "$MV/clips/$name.mp4"
  echo "MP4 $name ($(( $(date +%s) - t0 )) s)"
}

clip body_liver 12 orbit 50 -P "$ROOT/tests/T5_body/T5_body_liver.py" -- "$LIVER" unused.png "$ROOT/tests/T5_body/assets/FMA7163_skin.stl"
clip keyhole_push 10 dolly 0.45 -P "$ROOT/styleframes/holo_styleframes.py" -- "$PDB" "$MV/clips" keyhole
clip wall_dolly 12 dolly 0.35 -P "$ROOT/styleframes/holo_styleframes.py" -- "$PDB" "$MV/clips" wall
clip pose_048 10 orbit 60 -P "$ROOT/tests/T6_molecules/render_poses.py" -- "$POSES" "$MV/clips" 048
clip pose_001 8 orbit 50 -P "$ROOT/tests/T6_molecules/render_poses.py" -- "$POSES" "$MV/clips" 001
echo ALL CLIPS DONE
