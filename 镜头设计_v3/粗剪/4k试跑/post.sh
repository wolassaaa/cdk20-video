#!/bin/bash
cd "/d/。hkbu/molecular science"; O=镜头设计_v3/粗剪/4k试跑; FF=_env/ffmpeg/ffmpeg.exe; R=$O/试片_4k60.mp4
until [ -f $O/log/enc_done ]; do sleep 10; done
for f in $O/enc/*.mp4; do n=$(basename $f .mp4)
  [ -f _render_tmp/vmaf4k/$n.json ] && continue
  s=$(date +%s)
  $FF -hide_banner -y -i $f -i $R -lavfi "[0:v]setpts=PTS-STARTPTS,format=yuv420p[d];[1:v]setpts=PTS-STARTPTS,format=yuv420p[r];[d][r]libvmaf=model=version=vmaf_4k_v0.6.1:n_subsample=8:n_threads=4:log_fmt=json:log_path=_render_tmp/vmaf4k/$n.json" -f null - 2> $O/log/$n.vmaf.log
  echo "$n $(( $(date +%s)-s ))" >> $O/log/vmaf_times.txt
done
echo done > $O/log/vmaf_done
