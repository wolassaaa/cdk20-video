"""HKBU SCIE1007 课程作业的科普视频。托盘试片 1 的素材准备（1080p60）：人像分层（带软阴影的 RGBA 帧）、细胞纸底、2-08 末尾、3-02 开头、声音。
按 cellbg.py composite() 的做法把 D 的 fg/alpha 缩进 wide.json 的框（4K 框 /2），阴影同参数；不改任何旧文件。
用法：_env/footage/Scripts/python.exe prep.py <public 目录>
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

ROOT = Path("D:/。hkbu/molecular science")
FF = str(ROOT / "_env/ffmpeg/ffmpeg.exe")
PD = ROOT / "素材流程_out/D/5_place"
INS = ROOT / "镜头设计_v3/styleframes/art/fusion/s1/inserts"
OUT = Path(sys.argv[1])
T301, VO302, END = 92, 466, 742
W, H = 1920, 1080


def blur(x, sigma):
    r = int(3 * sigma)
    k = torch.exp(-torch.arange(-r, r + 1, device=x.device).float() ** 2 / (2 * sigma ** 2))
    k = (k / k.sum()).view(1, 1, 1, -1)
    x = F.conv2d(F.pad(x, (r, r, 0, 0), mode="replicate"), k)
    return F.conv2d(F.pad(x, (0, 0, r, r), mode="replicate"), k.transpose(2, 3))


def person():
    it = next(i for i in json.load(open(PD / "place.json", encoding="utf-8"))["items"] if i["name"] == "D_cam_3-01_t1")
    bx, by, bw, bh = [v / 2 for v in json.load(open(PD / "wide.json", encoding="utf-8"))["D_cam_3-01_t1"]["stamp"]["box"]]
    sw, sh = it["size"]
    rd = lambda f, pix: subprocess.Popen([FF, "-v", "error", "-i", str(PD / f), "-f", "rawvideo", "-pix_fmt", pix, "-"], stdout=subprocess.PIPE)
    r_fg, r_a = rd(it["fg"], "rgb24"), rd(it["alpha"], "gray")
    d = OUT / "person"
    d.mkdir(parents=True, exist_ok=True)
    bw_, bh_ = round(bw), round(bh)
    x0, y0 = round(bx), round(by)
    n = 0
    while True:
        b1, b2 = r_fg.stdout.read(sw * sh * 3), r_a.stdout.read(sw * sh)
        if len(b1) < sw * sh * 3 or len(b2) < sw * sh:
            break
        x = torch.frombuffer(bytearray(b1), dtype=torch.uint8).cuda().view(sh, sw, 3).permute(2, 0, 1)[None].float() / 255
        a = torch.frombuffer(bytearray(b2), dtype=torch.uint8).cuda().view(1, 1, sh, sw).float() / 255
        x = F.interpolate(x, (bh_, bw_), mode="bicubic", antialias=True).clamp(0, 1)
        a = F.interpolate(a, (bh_, bw_), mode="bilinear", antialias=True).clamp(0, 1)
        cx = torch.zeros(1, 3, H, W, device="cuda")
        ca = torch.zeros(1, 1, H, W, device="cuda")
        c0, c1 = max(0, -x0), min(bw_, W - x0)
        r0, r1 = max(0, -y0), min(bh_, H - y0)
        cx[..., y0 + r0:y0 + r1, x0 + c0:x0 + c1] = x[..., r0:r1, c0:c1]
        ca[..., y0 + r0:y0 + r1, x0 + c0:x0 + c1] = a[..., r0:r1, c0:c1]
        dy = round(0.01 * H)
        sh_a = torch.zeros_like(ca)
        sh_a[..., dy:, :] = ca[..., :H - dy, :]
        sh_a = F.interpolate(blur(F.interpolate(sh_a, scale_factor=0.25, mode="area"), 0.03 * H / 2.5 / 4), (H, W), mode="bilinear") * 0.18
        shc = torch.tensor((201, 197, 188), device="cuda").float().view(1, 3, 1, 1) / 255
        oa = ca + sh_a * (1 - ca)
        orgb = (cx * ca + shc * sh_a * (1 - ca)) / oa.clamp(min=1e-6)
        img = torch.cat([orgb, oa], 1)[0].permute(1, 2, 0).mul(255).round().byte().cpu().numpy()
        Image.fromarray(img, "RGBA").save(d / ("p_%04d.png" % n), compress_level=1)
        n += 1
    print("person frames", n)


def ff(*a):
    subprocess.run([FF, "-v", "error", "-y", *map(str, a)], check=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    enc = ["-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-an"]
    ff("-i", PD / "D_cam_3-01_t1_wideplate.mp4", "-vf", "scale=1920:1080:flags=lanczos", *enc, OUT / "plate.mp4")
    ff("-ss", "279.6", "-t", "2.2", "-i", INS / "S1S2_table_3_1080.mp4", *enc, "-r", "60", OUT / "a208.mp4")
    ff("-ss", "5.3", "-t", "3.5", "-i", INS / "S3_all_2.mp4", "-vf", "scale=1920:1080:flags=lanczos", *enc, "-r", "60", OUT / "s3.mp4")
    # 声音：2-08 的最后一句（help? 在第 80 帧说完）+ 3-01 整条（第 92 帧起）+ 3-02（掐头 0.37 秒，第 466 帧起）
    A = ROOT / "素材流程_out/A/5_place/A_vo_2-08_t1.wav"
    D1, D2 = PD / "D_cam_3-01_t1.wav", PD / "D_vo_3-02_t1.wav"
    s208 = 15.65 - 80 / 60
    ff("-ss", f"{s208:.3f}", "-i", A, "-i", D1, "-ss", "0.37", "-i", D2, "-filter_complex",
       f"[0]atrim=0:{(T301 - 2) / 60:.4f},afade=t=out:st={(T301 - 8) / 60:.4f}:d=0.1,aresample=48000,aformat=channel_layouts=stereo[a];"
       f"[1]aresample=48000,aformat=channel_layouts=stereo,adelay={T301 / 60 * 1000:.0f}:all=1[b];"
       f"[2]aresample=48000,aformat=channel_layouts=stereo,adelay={VO302 / 60 * 1000:.0f}:all=1[c];"
       f"[a][b][c]amix=inputs=3:normalize=0,atrim=0:{END / 60:.4f}[o]", "-map", "[o]", "-c:a", "pcm_s16le", OUT / "audio.wav")
    person()
