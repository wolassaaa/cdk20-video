#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频：透明/体积件噪点补渲（11-24，路线 A，1080p）。
# 定案：64 采样 + OpenImageDenoise（显卡，albedo+normal，accurate），场景、相机、材质、时间一律不改；帧写到 <原目录>_n64/，不碰原帧。
# 用法（项目根，Git Bash；给渲染队列用，可重跑，已出的帧跳过）：
#   bash 镜头设计_v3/inserts/render_noise_1124.sh drill 5-04 0 754      钻取主层（shot_drill.py render）→ G:/cdk20/work/drill/<段>/frames_n64/
#   bash 镜头设计_v3/inserts/render_noise_1124.sh oncam 3-09             出镜三维 bg + front（shot_oncam.py render）→ fr_bg_n64/、fr_front_n64/
#   bash 镜头设计_v3/inserts/render_noise_1124.sh ch1 1-09               第 1 章大板（fast_render.py）→ G:/cdk20/work/ch1/<段>/frames_n64/
# 帧没出齐返回 1（队列会重试）。渲完的验收、换目录、重合成见 镜头设计_v3/深化/交接_终版重算_1124.md。
set -u
KIND=$1; SEG=$2
ROOT="D:/。hkbu/molecular science"
B=${CDK20_BLENDER:-D:/software/blender-5.3/blender.exe}
export CDK20_SAMPLES=${CDK20_SAMPLES:-64} CDK20_DENOISER=${CDK20_DENOISER:-oidn} CDK20_FR_TAG=_n64 PYTHONIOENCODING=utf-8
[ -e "C:/Users/woola/cdk20_guard/GPU_PAUSED" ] && { echo "GPU paused"; exit 1; }
cd "$ROOT/镜头设计_v3/inserts"
cnt() { find "$1" -name "$2" -size +0 2>/dev/null | wc -l; }
case "$KIND" in
  drill)
    F0=$3; F1=$4; D="G:/cdk20/work/drill/$SEG/frames_n64"; mkdir -p "$D"
    find "$D" -name 'f_*.png' -size 0 -delete
    "$B" -b --factory-startup --python-exit-code 1 -P shot_drill.py -- render "$SEG" "$F0" "$F1" 2>&1 | grep -E "DRILL|Error|Traceback|Saved: .*f_0*[0-9]*0\.png"
    find "$D" -name 'f_*.png' -size 0 -delete
    n=0; for f in $(seq "$F0" "$F1"); do [ -s "$D/$(printf 'f_%04d.png' $f)" ] && n=$((n + 1)); done
    echo "$SEG $F0-$F1：$n/$((F1 - F0 + 1)) 帧"; [ "$n" -eq $((F1 - F0 + 1)) ] ;;
  oncam)
    W="G:/cdk20/work/oncam/$SEG"
    for w in bg front; do mkdir -p "$W/fr_${w}_n64"; find "$W/fr_${w}_n64" -name '*.png' -size 0 -delete; done
    for w in bg front; do "$B" -b --factory-startup --python-exit-code 1 -P shot_oncam.py -- render "$SEG" $w 2>&1 | grep -E "ONCAM|Error|Traceback"; done
    for w in bg front; do find "$W/fr_${w}_n64" -name '*.png' -size 0 -delete; done
    a=$(cnt "$W/fr_bg" 'b_*.png'); b=$(cnt "$W/fr_bg_n64" 'b_*.png'); c=$(cnt "$W/fr_front" 'r_*.png'); d=$(cnt "$W/fr_front_n64" 'r_*.png')
    echo "$SEG：bg $b/$a，front $d/$c"; [ "$b" -ge "$a" ] && [ "$d" -ge "$c" ] ;;
  ch1)
    W="G:/cdk20/work/ch1/$SEG"; case "$SEG" in 1-02) N=1036;; 1-09) N=1458;; 1-10) N=838;; esac
    mkdir -p "$W/frames_n64"; find "$W/frames_n64" -name 'f_*.png' -size 0 -delete
    python "$ROOT/镜头设计_v3/styleframes/art/fusion/s1/inserts/fast_render.py" "$W/board.blend" --out "$W/frames_n64" --f0 0 --f1 $((N - 1)) \
      --blender "$B" --no-bake --split 1 --samples "$CDK20_SAMPLES" >> "$W/render_n64.log" 2>&1
    find "$W/frames_n64" -name 'f_*.png' -size 0 -delete
    n=$(cnt "$W/frames_n64" 'f_*.png'); echo "$SEG：$n/$N 帧"; [ "$n" -ge "$N" ] ;;
  *) echo "kind = drill | oncam | ch1"; exit 2 ;;
esac
