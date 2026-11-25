#!/bin/bash
# HKBU SCIE1007 coursework video: read-only status for the GLM render supervisor (no writes, no kills).
echo "time: $(date '+%m-%d %H:%M')"
df -h /c /d /g | sed 1d
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
echo "blender: $(tasklist | grep -ci blender.exe)  ffmpeg: $(tasklist | grep -ci ffmpeg.exe)"
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name='blender.exe'\" | ForEach-Object { \$_.CommandLine.Substring(0,[Math]::Min(200,\$_.CommandLine.Length)) }"
echo "--- logs changed in the last 60 min"
find /g/cdk20/work "/d/。hkbu/molecular science/镜头设计_v3/粗剪" -maxdepth 4 -name "*.log" -mmin -60 2>/dev/null | head -12 | while read f; do echo "== $f"; tail -n 2 "$f" | cut -c1-200; done
echo "--- outputs"
ls -la "/d/。hkbu/molecular science/镜头设计_v3/粗剪/"cut_v8*.mp4 2>/dev/null || echo "cut_v8.mp4 not yet"
[ -f "/d/。hkbu/molecular science/_env/jobs/resume_renders.sh" ] && echo "resume script: present" || echo "resume script: missing"
