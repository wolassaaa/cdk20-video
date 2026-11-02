#!/bin/bash
# HKBU SCIE1007 coursework science video. Joins the three S3 clips into one, 283-412 s, so the whole section can be watched through. The first clip runs on past the start of the second, so it stops at 310 s. Nothing is re-encoded. k is 1 for 1080p, 2 for 4K. Run: bash join_s3.sh [k]
K="${1:-1}"
FF="D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe"
cd "$(dirname "$0")" || exit 1
printf "file 'S3_lock_key_%s.mp4'\noutpoint 26.97\nfile 'S3_cdk20_%s.mp4'\nfile 'S3_q_%s.mp4'\n" "$K" "$K" "$K" > "join_$K.txt"
"$FF" -y -loglevel error -f concat -safe 0 -i "join_$K.txt" -c copy -an "S3_all_$K.mp4" || { echo JOIN_FAILED; exit 1; }
mv "join_$K.txt" "D:/render_tmp/join_$K.txt"
echo JOIN_OK
