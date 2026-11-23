"""HKBU SCIE1007 课程作业的科普视频：片尾 W5 滚动字幕逐帧合成的显卡版（11-24 GPU 迁移）。

和 comp_w5roll.py 的 cmd_film 同一套合成数学（台面色 → 零件层 → 板后虚化 10 px → 接触阴影、板厚、骨白磨砂板 0.86
→ TD 等高线墙 0.5 → 字 → 重力帧前 10 帧淡出 → 最后 30 帧淡到黑），逐像素运算搬到 RTX 5080（torch CUDA）。
板后虚化：PIL GaussianBlur 本身是"三次扩展盒式模糊"近似，这里照同一算法（同样的分数半径）在显卡上做，只差中间取整。
零件层 PNG 用线程池在 CPU 上预解码；TD 墙仍由 comp_w5roll.td_reader（ffmpeg）读。

两个进程（照 inserts/comp_gpu.py）：drive()（C:/Python314，起 nvenc 编码、写 film_stats）+ child()（_env/footage 的 python，有 torch CUDA，
原始帧写 stdout）。_env/footage 的 python 写不了 G 盘，所以文件都由 drive 那边写。
comp_w5roll.py film 在 CDK20_GPU_W5=1（默认）时转调 drive()；=0 回 CPU 版。
  python comp_w5roll_gpu.py film [--N 12] [--bg DIR] [--bg-fps 30] [--bg-first 0] [--td MP4] [--out MP4] [--nf 240]
"""
import json
import math
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import comp_w5roll as M  # noqa: E402

FOOT_PY = M.ROOT / "_env/footage/Scripts/python.exe"
MARK = "W5GPU_STATS "


# ---------------------------------------------------------------- 显卡进程
def _pil_box_radius(radius, passes=3):
    """Pillow ImagingGaussianBlur 用的分数盒半径（libImaging/BoxBlur.c _gaussian_blur_radius）。"""
    sigma2 = radius * radius / passes
    L = math.sqrt(12.0 * sigma2 + 1.0)
    l = math.floor((L - 1.0) / 2.0)
    a = (2 * l + 1) * (l * (l + 1) - 3 * sigma2)
    a /= 6 * (sigma2 - (l + 1) * (l + 1))
    return l, a


def child(a):
    import torch
    import torch.nn.functional as F
    from PIL import Image
    dev = torch.device("cuda")
    torch.backends.cuda.matmul.allow_tf32 = False

    def T(x):
        return torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).to(dev)

    meta = json.loads((M.WORK / "sheet_meta.json").read_text(encoding="utf-8"))
    P = M.plan(a["N"], meta)
    NF = P["NF"] if not a.get("nf") else min(P["NF"], int(a["nf"]))
    sheet = np.asarray(Image.open(M.WORK / "sheet.png").convert("RGBA"), np.float32)
    sheet = sheet[meta["content"]["top"]:]
    SH_ = sheet.shape[0]
    S = T(sheet)
    srgb, sa = S[..., :3], S[..., 3] / 255.0
    SW = sheet.shape[1]
    B = M.Board()
    face, edge, shadow, vis = T(B.face), T(B.edge), T(B.shadow), T(B.vis)
    TABLE, BONE, EDGE = T(M.TABLE), T(M.BONE), T(M.EDGE)
    LUM = T(np.array([0.2126, 0.7152, 0.0722], np.float32))
    tx = M.TX0 - B.x0
    y0, x0, bh, bw = B.y0, B.x0, B.h, B.w

    # 盒式模糊核（PIL 三次扩展盒式，半径 BLUR）
    l, fa = _pil_box_radius(float(M.BLUR))
    k = torch.ones(2 * l + 3, dtype=torch.float32, device=dev)
    k[0] = k[-1] = fa
    k = k / (2 * l + 1 + 2 * fa)
    kr = l + 1
    kh = k.view(1, 1, 1, -1).repeat(3, 1, 1, 1)
    kv = k.view(1, 1, -1, 1).repeat(3, 1, 1, 1)

    def pil_blur(img):                                   # img: HxWx3 float（0–255 整数值）
        x = img.permute(2, 0, 1).unsqueeze(0)
        for _ in range(3):
            x = F.conv2d(F.pad(x, (kr, kr, 0, 0), mode="replicate"), kh, groups=3)
        for _ in range(3):
            x = F.conv2d(F.pad(x, (0, 0, kr, kr), mode="replicate"), kv, groups=3)
        return torch.floor(x[0].permute(1, 2, 0) + 0.5)

    # 零件层：CPU 线程池预解码，按需上传
    bg_dir = Path(a["bg"])
    pool = ThreadPoolExecutor(6)
    fut = {}

    def load(idx):
        im = Image.open(bg_dir / ("bg_%04d.png" % idx))
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        return np.asarray(im)

    def idx_of(f):
        src = a["bg_first"] + f
        return src if a["bg_fps"] == 60 else src * a["bg_fps"] // 60

    def want(f):
        for ff in range(f, min(NF, f + 24)):
            i = idx_of(ff)
            if i not in fut:
                fut[i] = pool.submit(load, i)

    td = M.td_reader(a["td"], a["bg_first"], P["NF"]) if a.get("td") else None
    stats = []
    cache = (None, None)
    out = sys.stdout.buffer
    t0 = time.time()
    with torch.no_grad():
        for f in range(NF):
            want(f)
            idx = idx_of(f)
            if cache[0] != idx:
                rgba = T(fut.pop(idx).result())
                al = rgba[..., 3:4] / 255.0
                cache = (idx, TABLE * (1 - al) + rgba[..., :3] * al)
                for old in [i for i in fut if i < idx]:
                    fut.pop(old)
            frame = cache[1].clone()
            g = float(np.clip((P["grav"] - f) / 10.0, 0, 1))
            if g > 0:
                crop = frame[y0:y0 + bh, x0:x0 + bw]
                blur = pil_blur(torch.floor(torch.clamp(crop + 0.5, 0, 255)))
                c = crop * (1 - shadow[..., None] * 0.22)
                c = c * (1 - edge[..., None] * 0.95) + EDGE * (edge[..., None] * 0.95)
                behind = blur * (1 - M.BOARD_OP) + BONE * M.BOARD_OP
                if td is not None:
                    behind = behind * (1 - M.TD_OP) + T(next(td)) * M.TD_OP
                fm = face[..., None]
                c = c * (1 - fm) + behind * fm
                yt = M.content_top(P, f)
                r0, r1 = max(M.VY0, yt), min(M.VY1, yt + SH_)
                ta = torch.zeros((bh, bw), dtype=torch.float32, device=dev)
                trgb = torch.zeros((bh, bw, 3), dtype=torch.float32, device=dev)
                if r1 > r0:
                    ys, ye = r0 - y0, r1 - y0
                    ta[ys:ye, tx:tx + SW] = sa[r0 - yt:r1 - yt] * vis[ys:ye, None]
                    trgb[ys:ye, tx:tx + SW] = srgb[r0 - yt:r1 - yt]
                if f % 3 == 0:                            # 机检数据：板面亮度、字出板的像素（和 CPU 版同一算法）
                    lum = (behind @ LUM) / 255.0
                    ink = ta > 0.5
                    face_lum = None
                    if bool(ink.any()):
                        sel = lum[ink & (face > 0.99)].double()
                        face_lum = float(torch.quantile(sel, 0.01)) if sel.numel() <= 16_000_000 else float(np.percentile(sel.cpu().numpy(), 1))
                    outside = int(((ta > 0.02) & (face < 0.999)).sum())
                    stats.append((f, yt, face_lum, outside))
                c = c * (1 - ta[..., None]) + trgb * ta[..., None]
                frame[y0:y0 + bh, x0:x0 + bw] = crop + g * (c - crop)
            elif td is not None:
                next(td)
            kk = float(np.clip((NF - 1 - f) / 30.0, 0, 1))
            if kk < 1:
                frame *= kk
            out.write(torch.clamp(frame + 0.5, 0, 255).to(torch.uint8).cpu().numpy().tobytes())
            if f % 200 == 0:
                print("frame", f, "%.1f s" % (time.time() - t0), file=sys.stderr, flush=True)
    out.flush()
    print(MARK + json.dumps(dict(plan=P, stats=stats, nf=NF, sec=round(time.time() - t0, 1))), file=sys.stderr, flush=True)


# ---------------------------------------------------------------- 驱动进程（C:/Python314）
def drive(a):
    out = Path(a.out or M.OUTDIR / f"W5_v10_N{a.N}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    args = dict(N=a.N, bg=str(a.bg), bg_fps=a.bg_fps, bg_first=a.bg_first, td=str(a.td) if a.td else None, nf=getattr(a, "nf", None))
    cmd = [str(FOOT_PY), "-X", "utf8", str(Path(__file__).resolve()), "child", json.dumps(args)]
    t0 = time.time()
    ch = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    res = {}

    def drain():
        for ln in iter(ch.stderr.readline, b""):
            s = ln.decode("utf-8", "replace").rstrip()
            if s.startswith(MARK):
                res.update(json.loads(s[len(MARK):]))
            else:
                print(s, flush=True)
    th = threading.Thread(target=drain, daemon=True)
    th.start()
    enc = M.encoder(out)
    sz = M.W * M.H * 3
    n = 0
    while True:
        buf = ch.stdout.read(sz)
        if len(buf) < sz:
            break
        enc.stdin.write(buf)
        n += 1
    enc.stdin.close()
    rc_e = enc.wait()
    rc_c = ch.wait()
    th.join(10)
    if rc_c or rc_e or not res or n != res.get("nf"):
        raise SystemExit(f"W5 显卡合成失败（child={rc_c} enc={rc_e} 帧 {n}/{res.get('nf')}）")
    if not getattr(a, "nf", None):                                        # 试跑（--nf）不写 stats，免得盖掉正式那份
        (M.WORK / f"film_stats_N{a.N}.json").write_text(json.dumps({"plan": res["plan"], "bg": str(a.bg), "bg_fps": a.bg_fps, "bg_first": a.bg_first,
                                                                     "td": str(a.td), "stats": res["stats"], "gpu": True}, ensure_ascii=False), encoding="utf-8")
    print("wrote", out, n, "frames", "%.0f s" % (time.time() - t0), "(GPU)")


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "child":
        child(json.loads(sys.argv[2]))
        return
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["film"])
    ap.add_argument("--N", type=int, default=12, choices=[10, 12])
    ap.add_argument("--bg", default="G:/cdk20/work/w5_bg/frames")
    ap.add_argument("--bg-fps", type=int, default=30)
    ap.add_argument("--bg-first", type=int, default=0)
    ap.add_argument("--td", default=str(M.ROOT / "镜头设计_v3/td/w5/W5_bg_4k60_v1.mp4"))
    ap.add_argument("--out")
    ap.add_argument("--nf", type=int, help="只出前 nf 帧（试跑；不写 film_stats）")
    drive(ap.parse_args())


if __name__ == "__main__":
    main()
