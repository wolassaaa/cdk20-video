#!/bin/bash
# HKBU SCIE1007 课程作业的科普视频。托盘试片 1：打包 Tray.jsx（public = 试片工作目录），1080p60 出片。用法：bash render.sh [输出名]
R="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion"
O="D:/。hkbu/molecular science/镜头设计_v3/粗剪/样片/托盘试片1"
cd "$R" || exit 1
export TEMP="$(cygpath -w "$O/_work/tmp")" TMP="$(cygpath -w "$O/_work/tmp")"; mkdir -p "$O/_work/tmp"
node node_modules/@remotion/cli/remotion-cli.js render src/v3/tray/Tray.jsx TrayTrial1 "$O/${1:-托盘试片1_v1}.mp4" --public-dir="$O/_work/public" --concurrency=4 --codec=h264 --crf=16 --audio-codec=aac 2>&1 | tail -3
