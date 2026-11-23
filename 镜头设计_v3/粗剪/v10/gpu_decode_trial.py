"""HKBU SCIE1007 课程作业的科普视频：v10 拼片转码的显卡解码/缩放试验（只试验，不改 build_v10.py，不动 G:/cdk20/work/v10）。
每段取前 600 帧，A = 现做法（CPU 解码 + CPU lanczos + h264_nvenc），B = 显卡做法（cuvid/cuda 解码 + scale_cuda lanczos 留在显卡直送 nvenc）。
记录墙钟、ffmpeg 进程平均 CPU（psutil 采样）、帧数，再对 A/B 算 ssim、psnr，并核对色彩标记。一次只跑一个转码。
用法：C:/Python314/python -X utf8 gpu_decode_trial.py [段名...]"""
import json, os, re, subprocess, sys, time
from pathlib import Path
import psutil

ROOT = Path(__file__).resolve().parents[3]
FF = os.environ.get("CDK20_FF") or next(p for p in ("D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe",
                                                    str(ROOT / "_env/ffmpeg/ffmpeg.exe")) if Path(p).exists())   # 与 build_v10.py 同一个 ffmpeg（只有它有写 G 盘的许可）
FP = str(ROOT / "_env/ffmpeg/ffprobe.exe")
OUT = Path("G:/cdk20/work/gpu_trial"); OUT.mkdir(parents=True, exist_ok=True)
N = 600
D23 = ROOT / "导演检查_20261123"
NCPU = psutil.cpu_count()
# 与 build_v10.py 第 60–70 行一致
NV = ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "0", "-pix_fmt", "yuv420p", "-r", "60",
      "-g", "120", "-bf", "0", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-video_track_timescale", "60000"]
VF_A = "fps=60,scale=1920:1080:flags=lanczos:out_range=tv,format=yuv420p,setsar=1"
VF_B = "fps=60,scale_cuda=1920:1080:interp_algo=lanczos:format=yuv420p,setsar=1"
NV_B = [a for i, a in enumerate(NV) if a != "-pix_fmt" and NV[i - 1] != "-pix_fmt"]   # 显卡帧不能再带 -pix_fmt（会插入 CPU 转换而失败），格式由 scale_cuda 的 format= 定
HW = ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
SEGS = {  # 名 → 源
    "W3_4k": OUT / "src_W3_4k60.mp4",                      # 合成的 4K60（W3 加工 放大），代表 4K 源缩 1080p
    "oncam3D": D23 / "15_出镜3D_1-05_1-06_1-07.mp4",        # 1080p 出镜三维
    "Bpage": D23 / "14_B档_4-01.mp4",                       # B 页（bt470bg 标记）
    "overlay_1-02": D23 / "21_1-02_无字幕.mp4",             # 带头尾叠层的段（High 4:4:4 源）
}


def run_sampled(cmd):
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    ps = psutil.Process(p.pid); samples = []; cpu_t = 0.0
    psutil.cpu_percent(None)
    while p.poll() is None:
        time.sleep(0.5)
        samples.append(psutil.cpu_percent(None))   # 全机 CPU %
        try:
            c = ps.cpu_times(); cpu_t = c.user + c.system
        except psutil.Error:
            pass
    err = p.stderr.read(); wall = time.time() - t0
    return p.returncode, wall, cpu_t, (sum(samples) / len(samples) if samples else 0), err


def probe(p):
    r = subprocess.run([FP, "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_packets,pix_fmt,color_range,color_space,color_transfer,color_primaries,width,height,r_frame_rate", "-of", "json", str(p)],
                       capture_output=True, text=True)
    return json.loads(r.stdout)["streams"][0]


def make_4k():
    dst = SEGS["W3_4k"]
    if dst.exists():
        return
    src = D23 / "24_W3_加工.mp4"
    subprocess.run([FF, "-y", "-v", "error", "-i", str(src), "-vf", "scale=3840:2160:flags=lanczos", "-frames:v", str(N), "-c:v", "h264_nvenc", "-preset", "p5",
                    "-cq", "17", "-b:v", "0", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-an", str(dst)], check=True)


def main():
    names = sys.argv[1:] or list(SEGS)
    make_4k()
    res = {}
    rf = OUT / "trial_results.json"
    if rf.exists():
        res = json.loads(rf.read_text(encoding="utf-8"))
    for nm in names:
        src = SEGS[nm]; row = {}
        for mode in ("A", "B"):
            o = OUT / f"{nm}_{mode}.mp4"
            if mode == "A":
                cmd = [FF, "-y", "-v", "error", "-i", str(src), "-vf", VF_A, "-frames:v", str(N), *NV, "-an", str(o)]
            else:
                cmd = [FF, "-y", "-v", "error", *HW, "-i", str(src), "-vf", VF_B, "-frames:v", str(N), *NV_B, "-an", str(o)]
            rc, wall, cpu_t, sys_cpu, err = run_sampled(cmd)
            pr = probe(o) if rc == 0 else {}
            row[mode] = dict(rc=rc, wall=round(wall, 2), ffmpeg_cpu_s=round(cpu_t, 1), ffmpeg_cores=round(cpu_t / wall, 2),
                             ffmpeg_pct_of_machine=round(cpu_t / wall / NCPU * 100, 1), sys_cpu_pct=round(sys_cpu, 1),
                             frames=pr.get("nb_read_packets"), range=pr.get("color_range"), space=pr.get("color_space"),
                             trc=pr.get("color_transfer"), prim=pr.get("color_primaries"), pix=pr.get("pix_fmt"), err=err[-300:])
            print(nm, mode, row[mode], flush=True)
        # ssim / psnr
        r = subprocess.run([FF, "-hide_banner", "-i", str(OUT / f"{nm}_A.mp4"), "-i", str(OUT / f"{nm}_B.mp4"), "-lavfi",
                            "[0:v][1:v]ssim;[0:v][1:v]psnr", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        ss = re.search(r"SSIM.*All:([\d.]+)", r.stderr); ps_ = re.search(r"PSNR.*average:([\d.inf]+)", r.stderr)
        row["ssim"] = float(ss.group(1)) if ss else None
        row["psnr"] = ps_.group(1) if ps_ else None
        print(nm, "ssim", row["ssim"], "psnr", row["psnr"], flush=True)
        res[nm] = row
        rf.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
