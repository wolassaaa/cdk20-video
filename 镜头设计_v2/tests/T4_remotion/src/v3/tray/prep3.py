"""HKBU SCIE1007 课程作业的科普视频。托盘样板 2、3 的素材准备（1080p60）：人像分层（带软阴影的 RGBA 帧，做法同 prep.py）、细胞纸底、
接进来的上一段末帧、推近要落到的下一段第一帧、声音。按 sample3.json 的节拍；不改旧文件。
用法：_env/footage/Scripts/python.exe prep3.py <t309|t411> <public 目录>
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
SRC = ROOT / "素材流程_out"
FUS = ROOT / "镜头设计_v3/styleframes/art/fusion"
HERE = Path(__file__).resolve().parent
S = json.load(open(HERE / "sample3.json", encoding="utf-8"))
NAME, OUT = sys.argv[1], Path(sys.argv[2])
CFG = S[NAME]
W, H = 1920, 1080


def blur(x, sigma):
    r = int(3 * sigma)
    k = torch.exp(-torch.arange(-r, r + 1, device=x.device).float() ** 2 / (2 * sigma ** 2))
    k = (k / k.sum()).view(1, 1, 1, -1)
    x = F.conv2d(F.pad(x, (r, r, 0, 0), mode="replicate"), k)
    return F.conv2d(F.pad(x, (0, 0, r, r), mode="replicate"), k.transpose(2, 3))


def person(take, who, first, n_need, tag):
    """take 的第 first 帧起 n_need 帧，写到 public/<tag>/p_0000.png…（编号从 0）。"""
    PD = SRC / who / "5_place"
    it = next(i for i in json.load(open(PD / "place.json", encoding="utf-8"))["items"] if i["name"] == take)
    bx, by, bw, bh = [v / 2 for v in json.load(open(PD / "wide.json", encoding="utf-8"))[take]["stamp"]["box"]]
    sw, sh = it["size"]
    rd = lambda f, pix: subprocess.Popen([FF, "-v", "error", "-i", str(PD / f), "-f", "rawvideo", "-pix_fmt", pix, "-"], stdout=subprocess.PIPE)
    r_fg, r_a = rd(it["fg"], "rgb24"), rd(it["alpha"], "gray")
    d = OUT / tag
    d.mkdir(parents=True, exist_ok=True)
    bw_, bh_, x0, y0 = round(bw), round(bh), round(bx), round(by)
    n, k = 0, 0
    last = None
    while n < n_need:
        b1, b2 = r_fg.stdout.read(sw * sh * 3), r_a.stdout.read(sw * sh)
        if len(b1) < sw * sh * 3 or len(b2) < sw * sh:
            break
        k += 1
        if k - 1 < first:
            continue
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
        last = img
        n += 1
    while n < n_need:                                      # 录音比画面长时不会走到这里；画面先完就复制最后一帧（不出现在成片里：push 前人已退出）
        Image.fromarray(last, "RGBA").save(d / ("p_%04d.png" % n), compress_level=1)
        n += 1
    r_fg.kill(), r_a.kill()
    print(tag, "person frames", n)


def ff(*a):
    subprocess.run([FF, "-v", "error", "-y", *map(str, a)], check=True)


def still(src, t, dst, sseof=False):
    ff(*(["-sseof", "-0.05"] if sseof else ["-ss", str(t)]), "-i", src, "-frames:v", "1", "-vf", "scale=1920:1080:flags=lanczos", dst)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    enc = ["-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-an", "-r", "60"]
    parts = CFG.get("parts") or [dict(CFG["audio"][0], until=CFG["frames"], box=CFG["box"], person_side=CFG["person_side"])]
    ins = []
    fc = []
    for i, p in enumerate(parts):
        PD = SRC / p["who"] / "5_place"
        n = p["until"] - p["at"]
        ff("-ss", f"{p['from']:.3f}", "-i", PD / f"{p['take']}_wideplate.mp4", "-t", f"{n / 60 + 0.5:.3f}", "-vf", "scale=1920:1080:flags=lanczos", *enc, OUT / f"plate{i}.mp4")
        person(p["take"], p["who"], round(p["from"] * 60), n, f"person{i}")
        ins += ["-ss", f"{p['from']:.3f}", "-t", f"{n / 60:.4f}", "-i", str(PD / f"{p['take']}.wav")]
        fc.append(f"[{i}]aresample=48000,aformat=channel_layouts=stereo,afade=t=out:st={n / 60 - 0.04:.4f}:d=0.04,adelay={p['at'] / 60 * 1000:.0f}:all=1[a{i}]")
    fc.append("".join(f"[a{i}]" for i in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{CFG['frames'] / 60:.4f}[o]")
    ff(*ins, "-filter_complex", ";".join(fc), "-map", "[o]", "-c:a", "pcm_s16le", OUT / "audio.wav")
    if NAME == "t309":
        still(FUS / "s1/inserts/S3_all_nocards_1080_v2.mp4", 122.98, OUT / "start.png")
        still(FUS / "s4/W2_lyrics_en_1080_v1.mp4", 0, OUT / "end.png")
    else:
        still(FUS / "s4/S4_410_3d_test_1.mp4", 0, OUT / "start.png", sseof=True)
        d501 = Path("C:/render_tmp/s5d_d501/d501_0000.png")
        if d501.exists():
            Image.open(d501).convert("RGB").save(OUT / "end.png")
        else:
            print("d501_0000.png 还没有")
    print("prep3 done", NAME)
