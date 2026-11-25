#!/bin/bash
cd "/d/。hkbu/molecular science"; O=镜头设计_v3/粗剪/4k试跑; FF=_env/ffmpeg/ffmpeg.exe; R=$O/试片_4k60.mp4
mkdir -p $O/enc $O/log
NV="-preset p7 -tune hq -rc vbr -multipass fullres -spatial-aq 1 -temporal-aq 1 -rc-lookahead 32"
enc(){ # name codec-args bitrate
  n=$1; shift; b=$1; shift
  [ -f $O/enc/$n.mp4 ] && return
  s=$(date +%s.%N)
  $FF -hide_banner -y -i $R -an "$@" -b:v $b -maxrate $(( ${b%k} * 2 ))k -bufsize $(( ${b%k} * 2 ))k $O/enc/$n.mp4 2> $O/log/$n.enc.log
  e=$(date +%s.%N); echo "$n $(python -c "print(round($e-$s,1))")" >> $O/log/times.txt
}
B1=6900k; B2=10350k
for m in 1 2; do
 B=$B1; sfx=1.0x; [ $m = 2 ] && B=$B2 && sfx=1.5x
 enc hevc10_$sfx $B -c:v hevc_nvenc $NV -profile:v main10 -pix_fmt p010le -tag:v hvc1
 enc hevc8_$sfx $B -c:v hevc_nvenc $NV -profile:v main -pix_fmt yuv420p -tag:v hvc1
 enc av1_$sfx $B -c:v av1_nvenc $NV -pix_fmt p010le
done
enc x265med_1.0x $B1 -c:v libx265 -preset medium -pix_fmt yuv420p -tag:v hvc1 -x265-params log-level=error
echo done > $O/log/enc_done
