"""HKBU SCIE1007 课程作业的科普视频：出镜三维段逐帧合成的显卡版（11-24）。

和 shot_oncam.py 里 Comp.frame / comp() 同一套合成数学，逐像素运算全搬到 RTX 5080（torch CUDA）：
  零件层（fr_bg）轻高斯 0.6 + 饱和度 ×0.94 + 颗粒 → 人像（抠像 RGBA）时域弱降噪 + unsharp + 抠像漏块剥除 + 右沿渐隐
  → v2 人虚化 / 挡人层（fr_front 闭运算 + 拉满）→ 屋里变暗 → 光包边 → 叠人 → 擦除前景层（fr_fg）→ 出处行 → rawvideo 管道给 h264_nvenc。
读 PNG 用线程池（cv2.imdecode，6 线程）预取，写管道单独一个线程，显卡只做算。

两个进程：drive()（C:/Python314，起 ffmpeg、改名、写 comp.json）+ child()（_env/footage 的 python，有 torch CUDA，原始帧写 stdout）。
_env/footage 的 python 写不了 G 盘（系统挡），所以文件都由 drive 那边写。shot_oncam.comp() 在 CDK20_GPU_COMP=1 时转调 drive()。
  python 镜头设计_v3/inserts/comp_gpu.py 3-09 [--out x.mp4] [--frames 0-119] [--no-grain]      （C:/Python314 跑）
和 CPU 版的差别、实测提速、回退：见同目录 comp_gpu.md。
"""
import json
import math
import os
import queue
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

try:                                   # drive()（C:/Python314，没有 torch）只转发字节，不用这几个
    import cv2
    import torch
    import torch.nn.functional as F
    DEV = torch.device("cuda")
except ImportError:
    torch = None

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shot_oncam as S  # noqa: E402



# ---------------------------------------------------------------- 读帧（CPU 线程里解码，回主线程上传）
def _read(path, mode):
    """mode: 'rgb' / 'rgba'。返回 uint8 HxWxC numpy（RGB 顺序），文件不在返回 None。路径可能带中文：fromfile + imdecode。"""
    try:
        buf = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    im = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    if im.dtype == np.uint16:
        im = (im.astype(np.uint32) * 255 + 32767) // 65535
        im = im.astype(np.uint8)
    if im.ndim == 2:
        im = np.stack([im] * 3, -1)
    if im.shape[2] == 4:
        im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
        if mode == "rgb":
            im = np.ascontiguousarray(im[..., :3])
    else:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        if mode == "rgba":
            im = np.concatenate([im, np.full(im.shape[:2] + (1,), 255, np.uint8)], -1)
    return im


def _up(a):
    """uint8 numpy HxWxC → float32 CUDA [0,1]。"""
    return torch.from_numpy(a).to(DEV, non_blocking=True).float().div_(255.0)


# ---------------------------------------------------------------- 图像算子（对照 PIL 的 GaussianBlur / MinFilter / MaxFilter）
_KC = {}


def _gk(sigma):
    if sigma not in _KC:
        r = max(1, int(math.ceil(3.0 * sigma)))
        x = torch.arange(-r, r + 1, dtype=torch.float32, device=DEV)
        k = torch.exp(-0.5 * (x / sigma) ** 2)
        _KC[sigma] = (k / k.sum(), r)
    return _KC[sigma]


def gblur(x, sigma):
    """x: HxWxC float。可分离高斯（PIL GaussianBlur(radius) 的 radius 就是 σ；边缘按复制处理，同 PIL）。"""
    if sigma <= 0:
        return x
    k, r = _gk(float(sigma))
    C = x.shape[2]
    t = x.permute(2, 0, 1).unsqueeze(1)                       # C,1,H,W
    t = F.pad(t, (r, r, 0, 0), mode="replicate")
    t = F.conv2d(t, k.view(1, 1, 1, -1))
    t = F.pad(t, (0, 0, r, r), mode="replicate")
    t = F.conv2d(t, k.view(1, 1, -1, 1))
    return t.squeeze(1).permute(1, 2, 0).contiguous() if C > 1 else t[:, 0].permute(1, 2, 0).contiguous()


_PK = {}


def _pil_box(sigma, passes=3):
    """Pillow BoxBlur.c 的 _gaussian_blur_radius：σ → 每遍的小数盒半径 l + a（Gwosdek 等 2011）。返回 1 维核（已归一）和半宽。"""
    if sigma not in _PK:
        s2 = sigma * sigma / passes
        L = math.sqrt(12.0 * s2 + 1.0)
        l = math.floor((L - 1.0) / 2.0)
        a = (2 * l + 1) * (l * (l + 1) - 3 * s2) / (6 * (s2 - (l + 1) * (l + 1)))
        r = l + a
        k = torch.ones(2 * l + 3, dtype=torch.float32, device=DEV)
        k[0] = k[-1] = a
        _PK[sigma] = (k / (2 * r + 1), l + 1)
    return _PK[sigma]


def gblur_pil(q, sigma, passes=3):
    """照 Pillow 的 GaussianBlur 做：先横向 3 遍、再纵向 3 遍小数半径盒子模糊，边缘复制，每遍结果四舍五入成 8 位。
    q: HxWxC，0–255 的整数值浮点。真高斯（gblur）高频压得比 Pillow 多：零件层颗粒少 25%（3-09 实测），所以这里逐遍照抄。"""
    if sigma <= 0:
        return q
    k, r = _pil_box(float(sigma), passes)
    t = q.permute(2, 0, 1).unsqueeze(1)                       # C,1,H,W
    for _ in range(passes):
        t = torch.floor(F.conv2d(F.pad(t, (r, r, 0, 0), mode="replicate"), k.view(1, 1, 1, -1)) + 0.5)
    for _ in range(passes):
        t = torch.floor(F.conv2d(F.pad(t, (0, 0, r, r), mode="replicate"), k.view(1, 1, -1, 1)) + 0.5)
    return t.squeeze(1).permute(1, 2, 0).contiguous()


def gblur_u8(x, sigma, trunc=True):
    """CPU 版先把浮点转 uint8（astype 截断，或 +0.5 四舍五入）再给 PIL 模糊、模糊结果是 uint8：两头都照样量化。"""
    q = torch.floor(x.clamp(0, 1) * 255.0) if trunc else torch.floor(x.clamp(0, 1) * 255.0 + 0.5)
    return gblur_pil(q, sigma).clamp_(0, 255) / 255.0


def _rank(m, size, op):
    """m: HxW float。PIL MinFilter/MaxFilter(size)（方窗，边缘复制 = 窗口只看图内）。"""
    r = size // 2
    t = m[None, None]
    if op == "max":
        t = F.max_pool2d(F.pad(t, (r, r, r, r), mode="replicate"), size, 1)
    else:
        t = -F.max_pool2d(F.pad(-t, (r, r, r, r), mode="replicate"), size, 1)
    return t[0, 0]


def _dilate_wrap(m, r):
    """shot_oncam._dilate：布尔图方形膨胀 r 像素，np.roll 实现（边缘环绕）→ 这里用循环填充 + 最大池化，结果相同。"""
    t = m.float()[None, None]
    t = F.max_pool2d(F.pad(t, (r, r, r, r), mode="circular"), 2 * r + 1, 1)
    return t[0, 0] > 0.5


def _lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def _smooth(t):
    t = t.clamp(0, 1)
    return t * t * (3 - 2 * t)


def grain(gen, shape):
    """shot_oncam._grain：白噪声 [1,2,1] 两遍平滑（np.roll，环绕）后归一到标准差 1 × GRAIN_GAIN。种子同 CPU 版（1000+f / 5000+f），
    随机数发生器不同（torch CUDA vs numpy PCG64），逐像素不同、统计相同。"""
    n = torch.randn(shape, generator=gen, device=DEV, dtype=torch.float32)
    for _ in range(2):
        n = (torch.roll(n, 1, 0) + 2 * n + torch.roll(n, -1, 0)) / 4
        n = (torch.roll(n, 1, 1) + 2 * n + torch.roll(n, -1, 1)) / 4
    return n / n.std(unbiased=False) * S.GRAIN_GAIN


# ---------------------------------------------------------------- 抠像漏块（shot_oncam.matte_leak_mask / matte_leak_keep）
def leak_mask(a):
    ML = S.MATTE_LEAK
    A = a[..., 3] > 0.5
    L = a[..., :3].mean(-1)
    m = (a[..., 3] > 0.06) & (L < ML["lum"]) & (a[..., 2] > a[..., 0] + ML["blue_over_red"])
    m[:ML["head_y"], :] = False
    if not bool(m.any()):
        return m
    m = m & _dilate_wrap(~A, ML["edge_px"])
    return (_dilate_wrap(m, ML["grow"]) & (a[..., 3] > 0)) if bool(m.any()) else m


def leak_keep(a):
    m = leak_mask(a)
    if not bool(m.any()):
        return None
    b = a.clone()
    for _ in range(4):
        b[..., 3] = torch.where(m, torch.zeros_like(a[..., 3]), a[..., 3])
        m2 = leak_mask(b) | m
        if bool((m2 == m).all()):
            break
        m = m2
    soft = m.float()
    soft = torch.maximum(soft, 0.5 * (_dilate_wrap(m, 1) & ~m).float())
    return 1.0 - soft


# ---------------------------------------------------------------- 合成
class GpuComp:
    def __init__(self, seg, workers=6, ahead=10):
        self.C = C = S.Comp(seg)                 # 配置、cam.json、颗粒 σ、出处行、右沿渐隐都照 CPU 版取
        self.cfg = C.cfg
        self.work = C.work
        self.sig = torch.tensor(C.sig, device=DEV)
        self.ramp = torch.tensor(C.ramp, device=DEV)
        if C.src is not None:
            L, self.src_fa = C.src
            self.src_L = torch.tensor(np.ascontiguousarray(L[870:940]), device=DEV)
        else:
            self.src_L = None
        self.pool = ThreadPoolExecutor(workers)
        self.ahead = ahead
        self.fut = {}                            # (路径, 模式) → Future
        self.pcache = {}                         # 人物图路径 → CUDA RGBA（含邻帧，留最近 6 张）
        self.seen = set()                        # 已取用过的人物图路径（不再预取，免得预取结果没人取、堆在内存里）
        self.gen = torch.Generator(device=DEV)
        ev = {e["id"]: e for e in self.cfg["K"]["events"]}
        self.dark = ev.get("dark")

    # 预取 ----------------------------------------------------------
    def _paths(self, f):
        cfg, w = self.cfg, self.work
        ps = [(w / "fr_bg" / f"b_{f:04d}.png", "rgb")]
        for g in (f - 1, f, f + 1):          # 邻帧越界时 person_png 自己夹到首尾帧（CPU 版同样拿它当邻帧）
            p = Path(S.person_png(cfg, g))
            if p not in self.seen:
                ps.append((p, "rgba"))
        if f in self.C.front:
            ps.append((w / "fr_front" / f"r_{f:04d}.png", "rgba"))
        if f <= self.C.cam.get("fg_last", -1):
            ps.append((w / "fr_fg" / f"f_{f:04d}.png", "rgba"))
        return ps

    def prefetch(self, f0, f1):
        for f in range(f0, f1):
            for key in self._paths(f):
                if key not in self.fut:
                    self.fut[key] = self.pool.submit(_read, *key)

    def get(self, path, mode):
        key = (Path(path), mode)
        fu = self.fut.pop(key, None)
        return fu.result() if fu is not None else _read(path, mode)

    def person(self, g):
        p = Path(S.person_png(self.cfg, g))
        self.seen.add(p)
        if p not in self.pcache:
            a = self.get(p, "rgba")
            if a is None:
                raise FileNotFoundError(p)
            if len(self.pcache) > 5:
                self.pcache.pop(next(iter(self.pcache)))
            self.pcache[p] = _up(a)
        return self.pcache[p]

    # 人像 ----------------------------------------------------------
    def person_enhance(self, a, f):
        dn, sh = S.PERSON_DN, (S.SEG_SH.get(self.cfg.get("seg"), S.PERSON_SH) if "ONCAM_SH" not in __import__("os").environ else S.PERSON_SH)   # 11-24 段内覆盖，同 shot_oncam.Comp.person_enhance
        if dn <= 0 and sh <= 0:
            return a
        rgb = a[..., :3]
        al = a[..., 3]
        out = rgb
        if dn > 0:
            tau = (0.035, 0.06)[min(dn, 2) - 1]
            acc, wsum = rgb.clone(), torch.ones(rgb.shape[:2] + (1,), device=DEV)
            for g in (f - 1, f + 1):
                try:
                    nb = self.person(g)[..., :3]
                except Exception:
                    continue
                if nb.shape != rgb.shape:
                    continue
                d = (nb - rgb).abs().mean(-1, keepdim=True)
                w = torch.exp(-(d / tau) ** 2)
                acc += nb * w
                wsum += w
            out = acc / wsum
        if sh > 0:
            bl = gblur_u8(out, 1.4, trunc=False)
            out = (out + sh * (out - bl)).clamp(0, 1)
        m = _rank(torch.floor(al * 255.0), 7, "min")[..., None] / 255.0
        res = a.clone()
        res[..., :3] = rgb * (1 - m) + out * m
        return res

    def person_rgba(self, f):
        a = self.person(f).clone()
        a = self.person_enhance(a, f)
        if S.leak_strip_on(self.cfg, f):
            k = leak_keep(a)
            if k is not None:
                a[..., 3] *= k
        a[..., 3] *= self.ramp[None, :]
        return a

    def person_layer(self, f):
        C, P = self.C, S.PERSON
        subs = C.cam["frames"][f]["card"]
        ds = [math.hypot(c[0] - i[0], c[1] - i[1]) for s in subs for c, i in zip(s, C.ident) if c[0] == c[0]]
        if len(ds) < len(subs) * 4:
            return torch.zeros((S.OUT_H, S.OUT_W, 4), device=DEV), float("inf")
        dev = max(ds)
        t0 = C.cam["push_t0"]
        if C.cam.get("version") == 2 or f < t0 or dev < 0.75:
            a = self.person_rgba(f)
            full = torch.zeros((S.OUT_H, S.OUT_W, 4), device=DEV)
            x0, y0 = P["x"], P["y"]
            sx = max(0, -x0)
            w = min(S.OUT_W - max(0, x0), P["w"] - sx)
            h = min(S.OUT_H - y0, P["h"])
            full[y0:y0 + h, max(0, x0):max(0, x0) + w] = a[:h, sx:sx + w]
            return full, 0.0 if (f < t0 or C.cam.get("version") == 2) else dev
        # v1 推进段（老流程，现在没有段在用）：透视变换照 CPU 版算，结果传上显卡
        full, dev = C.person_layer(f)
        return torch.from_numpy(np.ascontiguousarray(full)).to(DEV), dev

    def v2_person(self, Pl, f):
        C = self.C
        Sf = C.cam["frames"][f]["focus"]
        r = 0.0 if Sf >= S.D_PERSON else min(40.0, 30.0 * (S.D_PERSON / max(Sf, 1e-3) - 1.0))
        z0, z1 = self.cfg["P"].get("PBLUR_ZERO", (0, 0))
        if z0 <= f < z1:
            r = 0.0
        if r > 0.6:
            pre = Pl.clone()
            pre[..., :3] *= pre[..., 3:4]
            pre = gblur_u8(pre, r / 2)
            rgb = pre[..., :3] / pre[..., 3:4].clamp(min=1e-4)
            Pl = torch.cat([rgb.clamp(0, 1), pre[..., 3:4]], -1)
        fp = self.work / "fr_front" / f"r_{f:04d}.png"
        if f in C.front:
            im = self.get(fp, "rgba")
            if im is not None:
                A = torch.from_numpy(np.ascontiguousarray(im[..., 3])).to(DEV).float()
                A = _rank(_rank(A, 7, "max"), 7, "min") / 255.0
                A = ((A - 0.3) / 0.55).clamp(0, 1)
                A = A * A * (3 - 2 * A)
                A = A[..., None]
                if r > 0.6:
                    A = gblur_u8(A, r / 2)
                Pl = Pl.clone()
                Pl[..., 3:4] *= (1 - A)
        return Pl

    def person_dim(self, Pl, f):
        k = self.cfg["P"].get("PERSON_DIM")
        ev = self.dark
        if not k or ev is None:
            return Pl
        u = S.smooth((f - ev["f_start"]) / max(1, ev["f_end"] - ev["f_start"])) * k
        if u <= 0:
            return Pl
        x = torch.arange(S.OUT_W, dtype=torch.float32, device=DEV)
        g = ((x - 250.0) / 850.0).clamp(0, 1)
        Pl = Pl.clone()
        Pl[..., :3] *= (1 - u * g)[None, :, None]
        return Pl

    # 一帧 ----------------------------------------------------------
    def frame(self, f, lw=True, grain_on=True, soft=True):
        C = self.C
        bg = self.get(self.work / "fr_bg" / f"b_{f:04d}.png", "rgb")
        if bg is None:
            raise FileNotFoundError(self.work / "fr_bg" / f"b_{f:04d}.png")
        B = _up(bg)
        if soft:
            B = gblur_pil(torch.round(B * 255.0), S.CG_SOFT) / 255.0
            g = _lum(B)[..., None]
            B = g + (B - g) * S.CG_SAT
        if grain_on:
            self.gen.manual_seed(1000 + f)
            B = B + grain(self.gen, B.shape) * self.sig[None, None, :]
        Pl, dev = self.person_layer(f)
        if C.cam.get("version") == 2:
            Pl = self.v2_person(Pl, f)
        Pl = self.person_dim(Pl, f)
        fi = self.cfg.get("fade_in")
        if fi and f < fi[1]:
            Pl[..., 3] *= S.smooth((f - fi[0]) / max(1, fi[1] - fi[0]))
        A = Pl[..., 3:4]
        rgb = Pl[..., :3]
        if lw and float(A.max()) > 0:
            bb = gblur_u8(B, S.LW_BLUR)
            ab = gblur_u8(A, S.LW_BAND)
            band = (A * (1 - ab) * 2.2).clamp(0, 1) * S.LW_STRENGTH
            rgb = rgb * (1 - band) + torch.maximum(rgb, bb) * band
        out = rgb * A + B * (1 - A)
        if f <= C.cam.get("fg_last", -1):
            fg = self.get(self.work / "fr_fg" / f"f_{f:04d}.png", "rgba")
            if fg is not None:
                Fl = _up(fg)
                if grain_on:
                    self.gen.manual_seed(5000 + f)
                    Fl[..., :3] += grain(self.gen, Fl[..., :3].shape) * self.sig
                out = Fl[..., :3] * Fl[..., 3:4] + out * (1 - Fl[..., 3:4])
        if self.src_L is not None:
            a = self.src_fa(f)
            if a > 0.003:
                al = self.src_L[..., 3:4] * a
                out[870:940] = self.src_L[..., :3] * al + out[870:940] * (1 - al)
        return (out.clamp(0, 1) * 255.0 + 0.5).to(torch.uint8), dev

    def frames(self, flist, **kw):
        """按顺序产出 (f, CUDA uint8 帧, dev)，读盘提前 ahead 帧。"""
        flist = list(flist)
        for i, f in enumerate(flist):
            self.prefetch(f, (flist[min(i + self.ahead, len(flist) - 1)] + 1))
            fr, dev = self.frame(f, **kw)
            yield f, fr, dev


PY_GPU = S.ROOT / "_env/footage/Scripts/python.exe"      # 有 torch CUDA 的 python（C:/Python314 没有 torch）


def child(seg, frames=None, grain_on=True):
    """显卡进程：逐帧算好的 rgb24 原始字节写到 stdout，日志和最后的 ONCAM_GPU_RESULT 写 stderr。
    这个 python（_env/footage，连同它起的子进程）被系统挡着写不了 G 盘和项目外的目录（同坑 17 的 _env/ffmpeg），
    所以不自己起 ffmpeg、不写文件：编码、改名、comp.json 都由调用方（C:/Python314，drive）做。"""
    G = GpuComp(seg)
    fl = list(range(G.cfg["nf"])) if frames is None else list(frames)
    out = sys.stdout.buffer
    q = queue.Queue(maxsize=6)
    err = []

    def writer():
        while True:
            b = q.get()
            if b is None:
                break
            try:
                out.write(b)
            except Exception as e:          # 管道断了：记下来，主循环看到就停（不然主线程卡在 q.put）
                err.append(e)
                break
    th = threading.Thread(target=writer, daemon=True)
    th.start()
    devs = []
    t = time.time()
    for f, fr, dev in G.frames(fl, grain_on=grain_on):
        if err:
            raise SystemExit(f"pipe broken: {err[0]}")
        devs.append(dev)
        q.put(fr.cpu().numpy().tobytes())
        if f % 120 == 0:
            print(f"ONCAM gpu comp {seg} f{f} {time.time() - t:.1f}s", file=sys.stderr, flush=True)
    q.put(None)
    th.join()
    out.flush()
    if err:
        raise SystemExit(f"pipe broken: {err[0]}")
    sec = round(time.time() - t, 1)
    print("ONCAM_GPU_RESULT " + json.dumps(dict(card_dev_px=devs, sec=sec, n=len(fl))), file=sys.stderr, flush=True)


def drive(seg, out=None, frames=None, grain_on=True):
    """在 C:/Python314 里跑（shot_oncam.comp 的钩子调它）：起显卡子进程，把它的原始帧原样转给 ffmpeg，
    ffmpeg 命令和 CPU 版 comp() 一字不差（rawvideo rgb24 → h264_nvenc cq14 + 段配音，nvenc 不行自动退 libx264）。
    out 不给 = SEGS[段]["out"]，并写 comp.json；frames=(a, b) 只出一截（验收用，音频从 a 帧截起，不写 comp.json）。"""
    cfg = S.seg_cfg(seg)
    dst = Path(out or cfg["out"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.stem + "_tmp.mp4")
    cmd = [S.FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{S.OUT_W}x{S.OUT_H}", "-r", str(S.FPS), "-i", "-",
           "-i", str(cfg["wav"]), "-map", "0:v", "-map", "1:a", *S._enc_args(),
           "-pix_fmt", "yuv420p", "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-shortest", str(tmp)]
    args = [str(PY_GPU), str(Path(__file__).resolve()), seg, "--raw"]
    nf = cfg["nf"]
    if frames is not None:
        k = cmd.index(str(cfg["wav"]))
        cmd[k - 1:k - 1] = ["-ss", f"{frames[0] / S.FPS:.4f}"]
        args += ["--frames", f"{frames[0]}-{frames[1]}"]
        nf = frames[1] - frames[0] + 1
    if not grain_on:
        args.append("--no-grain")
    t = time.time()
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ch = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    log = []

    def errpump():
        for ln in iter(ch.stderr.readline, b""):
            s = ln.decode("utf-8", "replace").rstrip()
            log.append(s)
            if not s.startswith("ONCAM_GPU_RESULT "):
                print(s, flush=True)
    th = threading.Thread(target=errpump, daemon=True)
    th.start()
    nb = 0
    while True:
        b = ch.stdout.read(1 << 22)
        if not b:
            break
        p.stdin.write(b)
        nb += len(b)
    rc = ch.wait()
    th.join()
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("ffmpeg failed")
    want = nf * S.OUT_W * S.OUT_H * 3
    res = [json.loads(x[17:]) for x in log if x.startswith("ONCAM_GPU_RESULT ")]
    if rc != 0 or not res or nb != want:
        raise SystemExit(f"comp_gpu failed (rc={rc}, bytes {nb}/{want})")
    os.replace(tmp, dst)
    sec = round(time.time() - t, 1)
    if out is None and frames is None:
        (cfg["work"] / "comp.json").write_text(json.dumps(dict(card_dev_px=res[0]["card_dev_px"], sec=sec, gpu=True)), encoding="utf-8")
    print("ONCAM comp", dst, sec, "s", f"(GPU, {sec / nf:.3f} s/帧)", flush=True)
    return dst, sec


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("seg")
    ap.add_argument("--raw", action="store_true", help="显卡子进程模式（drive 用）")
    ap.add_argument("--out")
    ap.add_argument("--frames", help="a-b（含两端）")
    ap.add_argument("--no-grain", action="store_true")
    a = ap.parse_args()
    fr = tuple(int(v) for v in a.frames.split("-")) if a.frames else None
    if a.raw:
        child(a.seg, frames=range(fr[0], fr[1] + 1) if fr else None, grain_on=not a.no_grain)
    else:
        drive(a.seg, out=a.out, frames=fr, grain_on=not a.no_grain)
