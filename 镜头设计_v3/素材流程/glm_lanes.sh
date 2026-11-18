#!/usr/bin/env bash
# HKBU SCIE1007 课程作业的科普视频：GLM 页面分道跑。每道按顺序做自己的段：PAGE → PAGELOOK → 不过就再 PAGE → PAGELOOK（最多两轮）。
# 用法：bash 镜头设计_v3/素材流程/glm_lanes.sh <道号 1|2|3>   进度写到 _env/glm_log/lane<道号>.txt
ROOT="D:/。hkbu/molecular science"; cd "$ROOT" || exit 1
W=镜头设计_v3/素材流程/glm_worker.sh; P=镜头设计_v3/映射/_cache/pages
case "$1" in
  1) SEGS="3-02 3-03 3-07 4-02 4-06 4-09 5-01 5-07 7-02 7-03 7-04" ;;
  2) SEGS="6-01 6-02 6-03 6-06 6-07 6-08 6-09 6-10 6-11" ;;
  3) SEGS="3-06 3-09 4-04+4-05 4-08 4-11+4-12 5-02 5-05+5-06 5-09 6-04+6-05 6-12 7-01 8-01 8-04+8-05+8-06+8-07" ;;
esac
LOGF="_env/glm_log/lane$1.txt"
comp() { local a=${1%%+*}; case " 3-06 3-09 4-04 4-08 4-11 5-02 5-05 5-09 6-04 6-12 7-01 8-01 8-04 " in *" $a "*) echo "OnCam${a/-/}" ;; *) echo "Manual${a/-/}" ;; esac; }
for s in $SEGS; do
  C=$(comp "$s")
  if [ -f "$P/$C/look_report.md" ] && head -1 "$P/$C/look_report.md" | grep -q "看图：过"; then echo "$(date '+%m-%d %H:%M') $s 已过，跳过" >> "$LOGF"; continue; fi
  for round in 1 2; do
    echo "$(date '+%m-%d %H:%M') $s 第$round轮 做页" >> "$LOGF"
    for try in 1 2 3; do bash "$W" PAGE "$s" > /dev/null 2>&1; [ -f "$P/$C/report.md" ] && break; sleep 60; done
    [ "$round" = 2 ] && mv "$P/$C/look_report.md" "$P/$C/look_report_r1.md"
    echo "$(date '+%m-%d %H:%M') $s 第$round轮 看图" >> "$LOGF"
    for try in 1 2 3; do bash "$W" PAGELOOK "$s" > /dev/null 2>&1; [ -f "$P/$C/look_report.md" ] && break; sleep 60; done
    r=$(head -1 "$P/$C/look_report.md" 2>/dev/null)
    echo "$(date '+%m-%d %H:%M') $s 第$round轮 结果：$r" >> "$LOGF"
    case "$r" in *看图：过*) break ;; esac
  done
done
echo "$(date '+%m-%d %H:%M') 第$1道 全部做完" >> "$LOGF"
