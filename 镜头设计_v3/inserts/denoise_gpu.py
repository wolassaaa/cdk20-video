"""HKBU SCIE1007 课程作业的科普视频：成片级显卡时域降噪（11-24 夜，替代来不及的 64 采样补渲）。

半透明 / 体积件（kit_clear、kit_frost、琥珀插头、蓝色分子团）在 16 采样 + 景深下有"沙粒"噪点。这里不重渲，
直接对拼片里用的成片做运动补偿的时域滤波：构图、时间、颜色不变，只把逐帧乱跳的沙粒压下去。

算法（全部 torch CUDA，YUV420 原样进出，不做 RGB 换算，所以颜色均值不动）：
  1. 亮度先 σ1 高斯，分层块匹配估光流（1/8 分辨率 ±6 格全搜 → 1/4、1/2、全分辨率逐层 ±1 细化 → 全分辨率半像素），
     每个邻帧（t±1…t±R）各估一次，邻帧按光流扭到当前帧。
  2. 权重看"低频差"：扭过来的邻帧和当前帧之差先 σ1.2 模糊再平方、σ2 平均（噪点是高频，模糊后几乎不剩；对不齐、遮挡、
     字和边缘错位是低频大差），w = exp(-D / h²)。对不上的地方权重≈0，自动退回当前帧（不拖影）。
  3. 输出 = (当前帧 + Σ w·邻帧) / (1 + Σ w)，色度用同一套权重（降采样到半分辨率）。
  4. 出镜段：人物（抠像 alpha，按 shot_oncam 的摆位）膨胀羽化后排除在外，人像一点不动；合成时零件层加过匹配人像的颗粒，
     降噪会把它也压掉，所以在非人区域按"压掉的比例"补回同统计的颗粒（换种子），质感不变。

两个进程（照 comp_gpu.py）：drive()（C:/Python314）起解码 ffmpeg（-hwaccel cuda，yuv420p 原始帧）→ child()（_env/footage 的
python，有 torch）→ h264_nvenc 编码 ffmpeg（CQ 与原片同档）→ 写 G:/cdk20/work/dn1124/<段>_v.mp4 → 拷音轨封装 → 换名。
_env/footage 的 python 写不了 G 盘：它只读、只写 stdout/stderr（标定模式写项目内 _tmp/dn1124）。

  python 镜头设计_v3/inserts/denoise_gpu.py run <段|all> [--h 4.0] [--R 3] [--frames a-b --out x.mp4]   降噪并换片（原片改名 _rc08）
  python 镜头设计_v3/inserts/denoise_gpu.py undo <段|all>                                                 换回 _rc08 原片
  python 镜头设计_v3/inserts/denoise_gpu.py sheet <段|all>                                                前后对比联系表
  _env/footage/Scripts/python.exe 镜头设计_v3/inserts/denoise_gpu.py calib ...                            5-04 帧层标定（见 calib()）
段名照拼片清单（manifest_v10.json）的 group：1-02 1-09 1-10 3-02 3-03 3-06 3-09 W2 4-04+4-05 W3 5-05+5-06 5-09 W4 6-04+6-05。
5-04、3-04 不在名单里（在补渲，不许动）。
"""
import json
import math
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np

try:
    import torch
    import torch.nn.functional as F
    DEV = torch.device("cuda")
except ImportError:
    torch = None

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY_GPU = ROOT / "_env/footage/Scripts/python.exe"
FF = next(p for p in ("D:/software/tools/CipherTalk/resources/app.asar.unpacked/node_modules/ffmpeg-static/ffmpeg.exe",
                      str(ROOT / "_env/ffmpeg/ffmpeg.exe")) if Path(p).exists())       # CipherTalk 的 ffmpeg 有 nvenc、能写 G
FP = str(ROOT / "_env/ffmpeg/ffprobe.exe")
MANIFEST = HERE.parent / "粗剪/v10/manifest_v10.json"
WORKD = Path("G:/cdk20/work/dn1124")
W, H = 1920, 1080
FORBID = {"5-04", "3-04"}                                   # 在补渲，别的步骤换片

# 段 → 类型、出镜段在 shot_oncam 里的键、强度 h（标定后定；None = 用默认 H_DEFAULT）
SEGS = {
    "1-02": dict(kind="ch1"), "1-09": dict(kind="ch1"), "1-10": dict(kind="ch1"),
    "3-02": dict(kind="drill"), "3-03": dict(kind="drill"), "W4": dict(kind="drill"),
    "W2": dict(kind="w23"), "W3": dict(kind="w23"),
    "3-06": dict(kind="oncam", oc="3-06"), "3-09": dict(kind="oncam", oc="3-09"),
    "4-04+4-05": dict(kind="oncam", oc="4-04_4-05"), "5-05+5-06": dict(kind="oncam", oc="5-05_5-06"),
    "5-09": dict(kind="oncam", oc="5-09"), "6-04+6-05": dict(kind="oncam", oc="6-04_6-05"),
}
H_DEFAULT = 6.0          # 权重宽度（8 位刻度）；5-04 帧层标定：R5 h6 插头平坦区噪声 = 真值 1.02 倍，边缘保留 93%
R_DEFAULT = 5            # 前后各 5 帧（60 fps，共 11 帧 ≈ 0.18 s）


# ======================================================================== 显卡算子
def _gk(sigma, _c={}):
    if sigma not in _c:
        r = max(1, int(math.ceil(3 * sigma)))
        x = torch.arange(-r, r + 1, dtype=torch.float32, device=DEV)
        k = torch.exp(-0.5 * (x / sigma) ** 2)
        _c[sigma] = ((k / k.sum()).contiguous(), r)
    return _c[sigma]


def gblur(t, sigma):
    """t: (N,1,h,w) float。可分离高斯，边缘复制。"""
    if sigma <= 0:
        return t
    k, r = _gk(float(sigma))
    t = F.conv2d(F.pad(t, (r, r, 0, 0), mode="replicate"), k.view(1, 1, 1, -1))
    return F.conv2d(F.pad(t, (0, 0, r, r), mode="replicate"), k.view(1, 1, -1, 1))


def box(t, r):
    return F.avg_pool2d(F.pad(t, (r, r, r, r), mode="replicate"), 2 * r + 1, 1)


def shift_int(t, dx, dy):
    """out[y, x] = t[y+dy, x+dx]（越界复制边缘）。"""
    if dx == 0 and dy == 0:
        return t
    p = max(abs(dx), abs(dy))
    tp = F.pad(t, (p, p, p, p), mode="replicate")
    h, w = t.shape[-2:]
    return tp[..., p + dy:p + dy + h, p + dx:p + dx + w]


_GRID = {}


def base_grid(h, w):
    if (h, w) not in _GRID:
        ys, xs = torch.meshgrid(torch.arange(h, device=DEV, dtype=torch.float32), torch.arange(w, device=DEV, dtype=torch.float32), indexing="ij")
        _GRID[(h, w)] = (xs, ys)
    return _GRID[(h, w)]


def warp(t, flow):
    """t: (N,C,h,w)；flow: (2,h,w) 像素位移（x, y）。返回扭过来的图和"在画内"掩码 (1,1,h,w)。"""
    h, w = t.shape[-2:]
    xs, ys = base_grid(h, w)
    x = xs + flow[0]
    y = ys + flow[1]
    g = torch.stack([x / (w - 1) * 2 - 1, y / (h - 1) * 2 - 1], -1)[None]
    out = F.grid_sample(t, g.expand(t.shape[0], -1, -1, -1), mode="bilinear", padding_mode="border", align_corners=True)
    inside = ((x >= -0.5) & (x <= w - 0.5) & (y >= -0.5) & (y <= h - 0.5)).float()[None, None]
    return out, inside


def median3(fl):
    """flow (2,h,w) 3×3 中值，去孤立错配。"""
    p = F.pad(fl[:, None], (1, 1, 1, 1), mode="replicate")
    u = F.unfold(p, 3)                      # (2, 9, h*w)
    return u.median(1).values.view(fl.shape)


_OFF = {}


def _offsets(S, st=1.0):
    k = (S, st)
    if k not in _OFF:
        o = torch.tensor([(dx * st, dy * st) for dy in range(-S, S + 1) for dx in range(-S, S + 1)], device=DEV, dtype=torch.float32)
        _OFF[k] = o                                           # (K,2) x,y
    return _OFF[k]


def _refine(A, B, fl, st, r):
    """一次批量细化：9 个候选偏移一起 grid_sample、一起盒滤波、取最小。"""
    h, w = A.shape[-2:]
    o = _offsets(1, st)                                       # (9,2)
    xs, ys = base_grid(h, w)
    x = xs[None] + fl[0][None] + o[:, 0, None, None]
    y = ys[None] + fl[1][None] + o[:, 1, None, None]
    g = torch.stack([x / (w - 1) * 2 - 1, y / (h - 1) * 2 - 1], -1)
    wb = F.grid_sample(B.expand(9, -1, -1, -1), g, mode="bilinear", padding_mode="border", align_corners=True)
    c = box((A - wb).abs(), r)[:, 0] + (o.abs().sum(1) > 0).float()[:, None, None] * 0.05
    i = c.argmin(0)
    return fl + o[i].permute(2, 0, 1)


def bm_flow(a, b):
    """a、b: (1,1,H,W) 预模糊亮度（8 位刻度）。返回 a→b 的光流 (2,H,W)：a(x) ≈ b(x + flow)。
    1/8 分辨率 ±6 格全搜（一次性代价体）→ 1/4、1/2 逐层 ±1 细化 → 1/2 层 ±0.5、±0.25 → 双线性放大到全分辨率（精度约 0.5 像素）。"""
    Hh, Ww = a.shape[-2:]
    pa, pb = [a], [b]
    for _ in range(3):
        pa.append(F.avg_pool2d(pa[-1], 2))
        pb.append(F.avg_pool2d(pb[-1], 2))
    A, B = pa[3], pb[3]
    S = 6
    h, w = A.shape[-2:]
    Bp = F.pad(B, (S, S, S, S), mode="replicate")
    cv = F.unfold(Bp, 2 * S + 1).view(1, (2 * S + 1) ** 2, h, w)          # 通道 k = dy*13+dx 的平移版
    c = box((A - cv).abs().transpose(0, 1), 2)[:, 0]                       # (K,h,w)
    o = _offsets(S)
    c = c + 0.15 * o.abs().sum(1)[:, None, None]
    fl = o[c.argmin(0)].permute(2, 0, 1)
    fl = median3(fl)
    for lv, r in ((2, 2), (1, 3)):
        A, B = pa[lv], pb[lv]
        fl = F.interpolate(fl[None], size=A.shape[-2:], mode="nearest")[0] * 2
        fl = _refine(A, B, fl, 1.0, r)
        if lv == 1:
            fl = _refine(A, B, fl, 0.5, r)
            fl = _refine(A, B, fl, 0.25, r)
        fl = median3(fl)
    return F.interpolate(fl[None], size=(Hh, Ww), mode="bilinear", align_corners=False)[0] * 2


# ======================================================================== 降噪器
class Denoiser:
    """逐帧喂 (Y, U, V)（float 8 位刻度，(1,1,h,w)），按顺序出降噪帧。mask_fn(f) → (1,1,H,W) 0–1 人物（不降噪），grain_fn(f) → (gy, gu, gv) 补回颗粒。"""

    def __init__(self, R=R_DEFAULT, h=H_DEFAULT, hc=None, mask_fn=None, grain_fn=None, stats=True):
        self.R, self.h = R, float(h)
        self.hc = float(hc if hc is not None else h)
        self.mask_fn, self.grain_fn = mask_fn, grain_fn
        self.stats = stats

    def prep(self, yuv):
        Y, U, V = yuv
        return dict(Y=Y, U=U, V=V, Ys=gblur(Y, 1.0))

    def frame(self, f, cur, nbs):
        """cur: prep 过的当前帧；nbs: [(d, prep 过的邻帧)]。返回 (Y, U, V) 和统计。"""
        Y, U, V = cur["Y"], cur["U"], cur["V"]
        accY, accU, accV = Y.clone(), U.clone(), V.clone()
        ws, ws2 = torch.ones_like(Y), torch.ones_like(Y)
        wsc = torch.ones_like(U)
        pm = self.mask_fn(f) if self.mask_fn else None
        mot = []
        Lc = gblur(Y, 1.2)
        Uc, Vc = gblur(U, 1.0), gblur(V, 1.0)
        Ec = gblur((Y - gblur(Y, 1.5)) ** 2, 2.0)             # 当前帧局部高频能量
        Ysm = F.avg_pool2d(Y, 8)
        # 整帧快动作闸门：到相邻帧的光流中位速度 8–12 像素/帧渐退，12 以上整帧原样不动
        # （甩镜、推镜里看不见沙粒，块匹配在平滑虚化区会留下淡环纹：W2 第 1460 帧）
        flows = {}
        n1 = next(((d, nb) for d, nb in nbs if d == 1), None) or next(((d, nb) for d, nb in nbs if d == -1), None)
        gk = 1.0
        if n1 is not None:
            flows[n1[0]] = bm_flow(cur["Ys"], n1[1]["Ys"])
            gmot = float(flows[n1[0]].norm(dim=0).median())
            gk = min(1.0, max(0.0, (12.0 - gmot) / 4.0))
        for d, nb in nbs:
            if gk <= 0:
                if abs(d) == 1 and d in flows:
                    mot.append(float(flows[d].abs().mean()))
                continue
            if float((Ysm - F.avg_pool2d(nb["Y"], 8)).abs().mean()) > 20:
                continue                                       # 切镜 / 前景整屏扫过：这张邻帧整张不用
            fl = flows[d] if d in flows else bm_flow(cur["Ys"], nb["Ys"])
            if abs(d) == 1:
                mot.append(float(fl.abs().mean()))
            Yw, ins = warp(nb["Y"], fl)
            flc = F.avg_pool2d(fl[None], 2)[0] / 2
            UVw, _ = warp(torch.cat([nb["U"], nb["V"]], 1), flc)
            Uw, Vw = UVw[:, :1], UVw[:, 1:]
            D = gblur((Lc - gblur(Yw, 1.2)) ** 2, 2.0)
            Dc = gblur((Uc - gblur(Uw, 1.0)) ** 2 + (Vc - gblur(Vw, 1.0)) ** 2, 1.5)
            D = D + F.interpolate(Dc, size=Y.shape[-2:], mode="bilinear", align_corners=False) * (self.h / self.hc) ** 2
            w = torch.exp(-D / (self.h ** 2)) * ins
            # 高频能量对不上（邻帧扭过来带进了当前帧没有的边、拼缝）：沙粒两边能量相当，能过；3-09 第 336 帧前景扫过时块匹配拼出过波纹
            Ew = gblur((Yw - gblur(Yw, 1.5)) ** 2, 2.0)
            w = w * torch.exp(-(Ew - Ec).abs() / (2 * self.h ** 2))
            # 快动作（逐像素 > 6 像素/帧）渐退、14 以上不做：运动模糊里看不见沙粒，块匹配对推拉/旋转也不准，
            # 平滑的虚焦区对不齐也过得了低频差检查（W2 第 1460 帧推镜出过块状糊，3-09 第 336 帧 20 像素/帧处出过波纹；第一版门限 12–24 不够）
            spd = fl.norm(dim=0)[None, None] / abs(d)
            w = w * ((14.0 - spd) / 8.0).clamp(0, 1) * gk
            if pm is not None:
                w = w * (1 - pm)
            accY += w * Yw
            ws += w
            ws2 += w * w
            wc = F.avg_pool2d(w, 2)
            accU += wc * Uw
            accV += wc * Vw
            wsc += wc
        oY, oU, oV = accY / ws, accU / wsc, accV / wsc
        # 全帧均值钉回原帧（闪白 / 转场帧里邻帧亮度不同，加权平均会让均值漂 0.5/255 以上；W2 第一遍 0.68）
        oY = oY + (Y.mean() - oY.mean())
        oU = oU + (U.mean() - oU.mean())
        oV = oV + (V.mean() - oV.mean())
        if self.grain_fn is not None:
            neff = ws * ws / ws2                                   # 有效平均张数：颗粒方差被压到 1/neff
            k = (1 - 1 / neff).clamp(min=0).sqrt()
            if pm is not None:
                k = k * (1 - pm)
            gy, gu, gv = self.grain_fn(f)
            oY = oY + gy * k
            kc = F.avg_pool2d(k, 2)
            oU = oU + gu * kc
            oV = oV + gv * kc
        st = None
        if self.stats:
            st = dict(f=f, mot=round(sum(mot) / max(1, len(mot)), 3), cov=round(float(ws.mean()) - 1, 3),
                      dm=[round(float(oY.mean() - Y.mean()), 4), round(float(oU.mean() - U.mean()), 4), round(float(oV.mean() - V.mean()), 4)],
                      hf0=tile_noise(Y), hf1=tile_noise(oY), drop=drop_tile(Y, oY))
        return (oY, oU, oV), st


def tile_noise(Y, t=60):
    """高频噪声数：Y - σ1 高斯 的 60×60 块标准差，返回 [中位, 95 分位, 最大块的 (x, y)]（8 位刻度）。"""
    r = Y - gblur(Y, 1.0)
    h, w = Y.shape[-2:]
    v = F.avg_pool2d(r * r, t) - F.avg_pool2d(r, t) ** 2
    s = v.clamp(min=0).sqrt().flatten()
    q = torch.quantile(s, torch.tensor([0.5, 0.95], device=DEV))
    i = int(s.argmax())
    nw = w // t
    return [round(float(q[0]), 3), round(float(q[1]), 3), [(i % nw) * t, (i // nw) * t]]


def drop_tile(Y, oY, t=120):
    """降噪降得最多的 120×120 块左上角 (x, y)（联系表裁切用；文字区不该被选上，所以按"前后差的高频"挑）。"""
    r = (Y - gblur(Y, 1.0)) - (oY - gblur(oY, 1.0))
    v = F.avg_pool2d(r * r, t).flatten()
    i = int(v.argmax())
    nw = Y.shape[-1] // t
    return [(i % nw) * t, (i // nw) * t]


def run_stream(den, nf, read_fn, write_fn, log_every=120, tag=""):
    """read_fn(i) → (Y,U,V) 或 None（读完）；write_fn(i, (Y,U,V))。按顺序滑窗。返回逐帧统计。"""
    R = den.R
    buf = {}
    stats = []
    t0 = time.time()
    eof = None
    f = 0
    nxt = 0
    while True:
        while eof is None and nxt <= f + R:
            x = read_fn(nxt)
            if x is None:
                eof = nxt
                break
            buf[nxt] = den.prep(x)
            nxt += 1
        if f not in buf:
            break
        nbs = [(d, buf[f + d]) for d in range(-R, R + 1) if d != 0 and (f + d) in buf]
        out, st = den.frame(f, buf[f], nbs)
        write_fn(f, out)
        if st:
            stats.append(st)
        buf.pop(f - R, None)
        if f % log_every == 0:
            print(f"DN {tag} f{f} {time.time() - t0:.1f}s", file=sys.stderr, flush=True)
        f += 1
        if nf is not None and f >= nf:
            break
    return stats


# ======================================================================== 出镜段：人物遮罩 + 颗粒
def oncam_hooks(oc):
    import comp_gpu as CG                    # 同目录；导入 shot_oncam
    G = CG.GpuComp(oc)
    S = CG.S
    gen = torch.Generator(device=DEV)
    sig = G.sig.float()                      # RGB 0–1 刻度
    # BT.709 限幅：RGB(0–1) 增量 → Y/U/V（8 位）增量
    M = torch.tensor([[0.2126, 0.7152, 0.0722], [-0.1146, -0.3854, 0.5], [0.5, -0.4542, -0.0458]], device=DEV)
    M = M * torch.tensor([219.0, 224.0, 224.0], device=DEV)[:, None]

    def mask_fn(f):
        Pl, _ = G.person_layer(f)
        a = Pl[..., 3][None, None].float()
        a = F.max_pool2d(F.pad(a, (12, 12, 12, 12), mode="replicate"), 25, 1)
        return gblur(a, 4.0).clamp(0, 1)

    def grain_fn(f):
        gen.manual_seed(770000 + f)          # 换种子：统计同原合成，逐像素不同
        g = CG.grain(gen, (H, W, 3)) * sig[None, None, :]
        yuv = torch.einsum("ij,hwj->ihw", M, g)
        gy = yuv[0][None, None]
        gu = F.avg_pool2d(yuv[1][None, None], 2)
        gv = F.avg_pool2d(yuv[2][None, None], 2)
        return gy, gu, gv
    return mask_fn, grain_fn, S


# ======================================================================== 子进程：stdin yuv420p → stdout yuv420p
def child(seg, h, R, hc=None):
    torch.backends.cudnn.benchmark = False
    try:
        torch.cuda.set_per_process_memory_fraction(3.0 * 1024 ** 3 / torch.cuda.get_device_properties(0).total_memory)
    except Exception:
        pass
    mask_fn = grain_fn = None
    info = SEGS[seg]
    if info["kind"] == "oncam":
        mask_fn, grain_fn, _ = oncam_hooks(info["oc"])
    den = Denoiser(R=R, h=h, hc=hc, mask_fn=mask_fn, grain_fn=grain_fn)
    fin, fout = sys.stdin.buffer, sys.stdout.buffer
    ny, nc = W * H, (W // 2) * (H // 2)
    fsz = ny + 2 * nc
    q = queue.Queue(maxsize=8)
    err = []

    def writer():
        while True:
            b = q.get()
            if b is None:
                break
            try:
                fout.write(b)
            except Exception as e:
                err.append(e)
                break
    th = threading.Thread(target=writer, daemon=True)
    th.start()

    def read_fn(i):
        b = fin.read(fsz)
        if len(b) < fsz:
            return None
        a = torch.frombuffer(bytearray(b), dtype=torch.uint8).to(DEV).float()
        Y = a[:ny].view(1, 1, H, W)
        U = a[ny:ny + nc].view(1, 1, H // 2, W // 2)
        V = a[ny + nc:].view(1, 1, H // 2, W // 2)
        return Y, U, V

    def write_fn(i, out):
        if err:
            raise SystemExit(f"pipe broken: {err[0]}")
        Y, U, V = (x.round().clamp(0, 255).to(torch.uint8).flatten() for x in out)
        q.put(torch.cat([Y, U, V]).cpu().numpy().tobytes())

    t = time.time()
    stats = run_stream(den, None, read_fn, write_fn, tag=seg)
    q.put(None)
    th.join()
    fout.flush()
    print("DN_RESULT " + json.dumps(dict(n=len(stats), sec=round(time.time() - t, 1), peak_gb=round(torch.cuda.max_memory_allocated() / 1e9, 2),
                                         stats=stats)), file=sys.stderr, flush=True)


# ======================================================================== drive（C:/Python314）
def manifest_file(seg):
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for s in m["segments"]:
        if s["group"] == seg:
            p = Path(s["file"])
            return (p if p.is_absolute() else ROOT / p), s["frames"]
    raise KeyError(seg)


def probe(p):
    r = subprocess.run([FP, "-v", "error", "-count_packets", "-show_entries",
                        "stream=codec_type,nb_read_packets,color_range,color_space,color_transfer,color_primaries,bit_rate,width,height,r_frame_rate",
                        "-of", "json", str(p)], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout)["streams"]


def align_check(a_path, b_path):
    """按拼装的读法（ffmpeg 默认解码）把原片和新片缩到 96×54 灰度逐帧对：张数相同，且新片第 n 帧最像原片第 n 帧（不是 n±1）。"""
    def dec(p):
        raw = subprocess.run([FF, "-v", "error", "-i", str(p), "-vf", "scale=96:54", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(-1, 54, 96).astype(np.float32)
    a, b = dec(a_path), dec(b_path)
    n = min(len(a), len(b))
    bad = []
    for i in range(n):
        d0 = float(np.abs(a[i] - b[i]).mean())
        dn = min(float(np.abs(a[j] - b[i]).mean()) for j in (max(i - 1, 0), min(i + 1, n - 1)))
        if d0 > 1.0 and d0 > dn:
            bad.append(i)
    return dict(n_src=len(a), n_new=len(b), bad=bad[:20])


def cq_for(vs):
    """CQ 与原片同档：钻取 / W 段原片 nvenc cq15，出镜 cq14；第 1 章大板原片 200 Mb/s 以上（近无损）→ cq10。"""
    br = int(vs.get("bit_rate") or 0)
    if br > 120e6:
        return 10
    if br > 70e6:
        return 12
    return 14


def drive(seg, h=None, R=None, frames=None, out=None, swap=True):
    if seg in FORBID:
        raise SystemExit(f"{seg} 在补渲，不许动")
    info = SEGS[seg]
    h = float(h if h is not None else info.get("h", H_DEFAULT))
    R = int(R if R is not None else info.get("R", R_DEFAULT))
    src, nf_man = manifest_file(seg)
    bak = src.with_name(src.stem + "_rc08.mp4")
    if bak.exists():
        src_in = bak                                          # 已换过：总从原片重做（试一截 --out 也一样）
    else:
        src_in = src
    st = probe(src_in)
    vs = next(s for s in st if s["codec_type"] == "video")
    nf = int(vs["nb_read_packets"])
    if nf != nf_man:
        print(f"!! {seg} 原片 {nf} 帧，清单 {nf_man} 帧", flush=True)
    WORKD.mkdir(parents=True, exist_ok=True)
    tag = seg.replace("+", "_")
    mkv = WORKD / f"{tag}_v.mp4"          # 直接写 mp4（时间基 1/60000）：mkv 毫秒时间戳在 60 fps 下抖，封装后解码会补帧/丢帧（第一版错过一帧）
    dec = [FF, "-v", "error", "-i", str(src_in)]
    if frames:
        dec += ["-vf", f"select='between(n\\,{frames[0]}\\,{frames[1]})'"]
    dec += ["-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"]       # 一包一帧，不补不丢
    col = []
    for k, opt in (("color_range", "-color_range"), ("color_space", "-colorspace"), ("color_transfer", "-color_trc"), ("color_primaries", "-color_primaries")):
        if vs.get(k):
            col += [opt, vs[k]]
    cq = cq_for(vs)
    enc = [FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-r", "60", "-i", "-",
           "-c:v", "h264_nvenc", "-preset", "p7", "-tune", "hq", "-rc", "vbr", "-cq", str(cq), "-b:v", "0", "-maxrate", "250M",
           "-profile:v", "high", "-pix_fmt", "yuv420p", *col, "-video_track_timescale", "60000", str(mkv)]
    t = time.time()
    pd = subprocess.Popen(dec, stdout=subprocess.PIPE)
    pc = subprocess.Popen([str(PY_GPU), str(Path(__file__).resolve()), "child", seg, "--h", str(h), "--R", str(R)],
                          stdin=pd.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    pd.stdout.close()
    log = []

    def errpump():
        for ln in iter(pc.stderr.readline, b""):
            s = ln.decode("utf-8", "replace").rstrip()
            log.append(s)
            if not s.startswith("DN_RESULT "):
                print(s, flush=True)
    th = threading.Thread(target=errpump, daemon=True)
    th.start()
    pe = subprocess.Popen(enc, stdin=pc.stdout)
    pc.stdout.close()
    rc_e = pe.wait()
    rc_c = pc.wait()
    th.join()
    pd.wait()
    res = [json.loads(x[10:]) for x in log if x.startswith("DN_RESULT ")]
    if rc_e != 0 or rc_c != 0 or not res:
        raise SystemExit(f"denoise failed {seg}: enc {rc_e} child {rc_c}")
    res = res[0]
    want = (frames[1] - frames[0] + 1) if frames else nf
    if res["n"] != want:
        raise SystemExit(f"{seg} 帧数不对：{res['n']} / {want}")
    # 封装：视频 + 原音轨（拷贝，不重编码）
    dst = Path(out) if out else src.with_name(src.stem + "_dn_tmp.mp4")
    mux = [FF, "-y", "-v", "error", "-i", str(mkv)]
    if frames:
        mux += ["-ss", f"{frames[0] / 60:.4f}", "-t", f"{want / 60:.4f}"]
    mux += ["-i", str(src_in), "-map", "0:v", "-map", "1:a?", "-c", "copy", "-movflags", "+faststart", str(dst)]
    if subprocess.run(mux).returncode != 0:
        raise SystemExit("封装失败")
    st2 = probe(dst)
    v2 = next(s for s in st2 if s["codec_type"] == "video")
    if int(v2["nb_read_packets"]) != want:
        raise SystemExit(f"{seg} 出片帧数 {v2['nb_read_packets']} ≠ {want}")
    if not frames:
        al = align_check(src_in, dst)
        if al["n_new"] != al["n_src"] or al["bad"]:
            raise SystemExit(f"{seg} 逐帧对位不过：{al}")
    sec = round(time.time() - t, 1)
    S_ = res["stats"]
    dm = np.array([s["dm"] for s in S_])
    summ = dict(seg=seg, src=str(src_in), h=h, R=R, cq=cq, nf=want, sec=sec, child_sec=res["sec"], peak_gb=res["peak_gb"],
                mean_shift_max=[round(float(x), 3) for x in np.abs(dm).max(0)], mean_shift_avg=[round(float(x), 4) for x in dm.mean(0)],
                hf95_before=round(float(np.median([s["hf0"][1] for s in S_])), 3), hf95_after=round(float(np.median([s["hf1"][1] for s in S_])), 3),
                hfmax_before=round(float(np.median([max(s["hf0"][1], 0) for s in S_])), 3),
                mot_max=max(s["mot"] for s in S_), time=time.strftime("%Y-%m-%d %H:%M:%S"))
    (WORKD / f"{tag}_stats.json").write_text(json.dumps(dict(summary=summ, frames=S_)), encoding="utf-8")
    print("DN", json.dumps(summ, ensure_ascii=False), flush=True)
    if out is None and swap:
        if not bak.exists():
            os.replace(src, bak)                              # 原片 → _rc08
        os.replace(dst, src)                                  # 新片用原文件名（拼装直接读到）
        print(f"DN 换片 {src.name}（原片 {bak.name}）", flush=True)
    return summ


def undo(seg):
    src, _ = manifest_file(seg)
    bak = src.with_name(src.stem + "_rc08.mp4")
    if not bak.exists():
        print(f"{seg}: 没有 _rc08 备份，跳过")
        return
    keep = src.with_name(src.stem + "_dn.mp4")
    if src.exists():
        os.replace(src, keep)
    os.replace(bak, src)
    print(f"{seg}: 已换回原片；降噪版留在 {keep.name}")


# ======================================================================== 联系表（C:/Python314）
def grab(p, idx):
    """抽指定帧（rgb24）。"""
    sel = "+".join(f"eq(n\\,{i})" for i in idx)
    raw = subprocess.run([FF, "-v", "error", "-i", str(p), "-vf", f"select='{sel}'", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def sheet(seg, out_dir=None):
    from PIL import Image, ImageDraw, ImageFont
    tag = seg.replace("+", "_")
    S_ = json.loads((WORKD / f"{tag}_stats.json").read_text(encoding="utf-8"))
    fr, summ = S_["frames"], S_["summary"]
    fr = [x for x in fr if 2 <= x["f"] < len(S_["frames"]) - 3]          # 首尾几帧邻帧少、抽帧也容易丢，不挑
    src, _ = manifest_file(seg)
    bak = src.with_name(src.stem + "_rc08.mp4")
    before = bak if bak.exists() else Path(summ["src"])
    after = src if bak.exists() else Path(summ["src"]).with_name(Path(summ["src"]).stem + "_dn_tmp.mp4")
    # 挑帧：噪声降得最多的、运动最快的、中间
    drop = sorted(fr, key=lambda s: s["hf0"][1] - s["hf1"][1], reverse=True)
    picks = [drop[0]]
    fast = max(fr, key=lambda s: s["mot"])
    picks.append(fast)
    picks.append(fr[len(fr) // 2])
    seen, P = set(), []
    for s in picks:
        if s["f"] not in seen:
            seen.add(s["f"])
            P.append(s)
    idx = sorted(s["f"] for s in P)
    A, B = grab(before, idx), grab(after, idx)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
    except OSError:
        font = ImageFont.load_default()
    rows = []
    for k, f in enumerate(idx):
        s = next(x for x in fr if x["f"] == f)
        x0, y0 = s.get("drop", s["hf0"][2])
        cx, cy = min(max(x0 + 60 - 240, 0), W - 480), min(max(y0 + 60 - 135, 0), H - 270)
        a, b = Image.fromarray(A[k]), Image.fromarray(B[k])
        row = Image.new("RGB", (1920, 540 + 540 + 40), (20, 20, 20))
        row.paste(a.resize((960, 540)), (0, 40))
        row.paste(b.resize((960, 540)), (960, 40))
        row.paste(a.crop((cx, cy, cx + 480, cy + 270)).resize((960, 540), Image.NEAREST), (0, 580))
        row.paste(b.crop((cx, cy, cx + 480, cy + 270)).resize((960, 540), Image.NEAREST), (960, 580))
        d = ImageDraw.Draw(row)
        why = "噪声降最多" if s is P[0] or f == P[0]["f"] else ("运动最快" if f == fast["f"] else "中间帧")
        d.text((10, 8), f"{seg}  第 {f} 帧（{why}，运动 {s['mot']:.1f} px/帧）  左：原片 rc08   右：降噪   下排：({cx},{cy}) 480×270 放大 2 倍  "
               f"噪声块 95 分位 {s['hf0'][1]:.2f} → {s['hf1'][1]:.2f}", fill=(240, 240, 240), font=font)
        d.rectangle([cx / 2, 40 + cy / 2, (cx + 480) / 2, 40 + (cy + 270) / 2], outline=(255, 60, 60), width=2)
        rows.append(row)
    sh = Image.new("RGB", (1920, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        sh.paste(r, (0, y))
        y += r.height
    od = Path(out_dir) if out_dir else ROOT / "导演检查_20261124/_联系表"
    od.mkdir(parents=True, exist_ok=True)
    p = od / f"dn_{tag}.jpg"
    sh.save(p, quality=90)
    print("sheet", p, idx)
    return p


# ======================================================================== 标定（_env/footage 的 python，读 PNG 帧层）
def calib(argv):
    """5-04 帧层：旧 16 采样帧（frames/）降噪后对 64 采样 + OIDN 真值（frames_n64/）量 PSNR/SSIM、插头/分子团平坦区噪声、边缘拉普拉斯方差。
    python denoise_gpu.py calib --grid "2,3,4,5,6" --R 3 --fr 4-56 --metric 10,20,30,40,50"""
    import argparse
    import cv2
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default="G:/cdk20/work/drill/5-04/frames")
    ap.add_argument("--ref", default="G:/cdk20/work/drill/5-04/frames_n64")
    ap.add_argument("--grid", default="2,3,4,5,6")
    ap.add_argument("--R", type=int, default=3)
    ap.add_argument("--fr", default="4-56")
    ap.add_argument("--metric", default="10,20,30,40,50")
    ap.add_argument("--out", default=str(ROOT / "_tmp/dn1124"))
    ap.add_argument("--crops", default="")                # 出对比裁切的 h
    a = ap.parse_args(argv)
    f0, f1 = (int(v) for v in a.fr.split("-"))
    mfr = [int(v) for v in a.metric.split(",")]
    od = Path(a.out)
    od.mkdir(parents=True, exist_ok=True)
    # 709 限幅 RGB ↔ YUV
    Mf = torch.tensor([[0.2126, 0.7152, 0.0722], [-0.1146, -0.3854, 0.5], [0.5, -0.4542, -0.0458]], device=DEV)
    Mi = torch.linalg.inv(Mf)

    def to_yuv(rgb):                                     # rgb (3,H,W) 0–255
        x = torch.einsum("ij,jhw->ihw", Mf, rgb / 255.0)
        Y = 16 + 219 * x[0]
        U = F.avg_pool2d((128 + 224 * x[1])[None, None], 2)
        V = F.avg_pool2d((128 + 224 * x[2])[None, None], 2)
        q = lambda t: t.round().clamp(0, 255)
        return q(Y)[None, None], q(U), q(V)

    def to_rgb(Y, U, V):
        Uu = F.interpolate(U, scale_factor=2, mode="bilinear", align_corners=False)
        Vu = F.interpolate(V, scale_factor=2, mode="bilinear", align_corners=False)
        x = torch.cat([(Y - 16) / 219, (Uu - 128) / 224, (Vu - 128) / 224], 1)[0]
        return (torch.einsum("ij,jhw->ihw", Mi, x) * 255).round().clamp(0, 255)

    cache = {}

    def load(d, f):
        k = (d, f)
        if k not in cache:
            im = cv2.imread(f"{d}/f_{f:04d}.png", cv2.IMREAD_COLOR)
            cache[k] = to_yuv(torch.from_numpy(im[..., ::-1].copy()).to(DEV).permute(2, 0, 1).float())
        return cache[k]

    def roi(f, name):
        c10 = dict(plug=(860, 470, 1180, 760), mol=(1520, 520, 1920, 900))[name]
        c40 = dict(plug=(890, 470, 1220, 790), mol=(1520, 500, 1920, 880))[name]
        u = (f - 10) / 30
        return [int(round(p + (q - p) * u)) for p, q in zip(c10, c40)]

    def ssim(x, y):
        C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
        mx, my = gblur(x, 1.5), gblur(y, 1.5)
        sxx = gblur(x * x, 1.5) - mx * mx
        syy = gblur(y * y, 1.5) - my * my
        sxy = gblur(x * y, 1.5) - mx * my
        return float((((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx * mx + my * my + C1) * (sxx + syy + C2))).mean())

    def metrics(Y, Yref, f, Yold):
        r = {}
        mse = float(((Y - Yref) ** 2).mean())
        r["psnr"] = round(10 * math.log10(255 ** 2 / max(mse, 1e-9)), 2)
        r["ssim"] = round(ssim(Y, Yref), 4)
        for name in ("plug", "mol"):
            x0, y0, x1, y1 = roi(f, name)
            R_ = Yref[..., y0:y1, x0:x1]
            gm = gblur((F.pad(R_, (0, 1, 0, 0), mode="replicate").diff(dim=-1) ** 2 + F.pad(R_, (0, 0, 0, 1), mode="replicate").diff(dim=-2) ** 2).sqrt(), 2.0)
            flat = gm <= torch.quantile(gm.flatten(), 0.4)
            edge = gm >= torch.quantile(gm.flatten(), 0.85)
            for lab, Z in (("", Y), ("ref_", Yref), ("old_", Yold)):
                Zr = Z[..., y0:y1, x0:x1]
                hp = Zr - gblur(Zr, 1.0)
                r[f"{lab}{name}_flat"] = round(float(hp[flat].std()), 3)
                lap = F.conv2d(F.pad(Zr, (1, 1, 1, 1), mode="replicate"), torch.tensor([[0, 1, 0], [1, -4, 1], [0, 1, 0]], device=DEV, dtype=torch.float32).view(1, 1, 3, 3))
                r[f"{lab}{name}_lapv"] = round(float(gblur(lap, 2.0)[edge].var()), 3)    # 边缘处拉普拉斯（σ2 平滑后：量结构，不量噪点）
        return r

    results = {}
    hs = [float(v) for v in a.grid.split(",")]
    mean_shift = {}
    for h in hs:
        den = Denoiser(R=a.R, h=h, stats=False) if h > 0 else None
        rows = []
        outs = {}

        def read_fn(i):
            f = f0 + i
            if f > f1:
                return None
            return load(a.old, f)

        def write_fn(i, out):
            f = f0 + i
            if f in mfr or (a.crops and f == 10):
                outs[f] = out
        if den:
            run_stream(den, None, read_fn, write_fn, log_every=10 ** 9)
        else:
            for f in mfr:
                outs[f] = load(a.old, f)
        ms = []
        for f in mfr:
            Y = outs[f][0]
            Yref = load(a.ref, f)[0]
            Yold = load(a.old, f)[0]
            ms.append(float((Y.mean() - Yold.mean()).abs()))
            rows.append(dict(f=f, **metrics(Y, Yref, f, Yold)))
        agg = {k: round(float(np.mean([r[k] for r in rows])), 3) for k in rows[0] if k != "f"}
        agg["plug_ratio"] = round(agg["plug_flat"] / agg["ref_plug_flat"], 3)
        agg["mol_ratio"] = round(agg["mol_flat"] / agg["ref_mol_flat"], 3)
        agg["plug_edge_keep"] = round(agg["plug_lapv"] / agg["old_plug_lapv"], 3)
        agg["mol_edge_keep"] = round(agg["mol_lapv"] / agg["old_mol_lapv"], 3)
        agg["mean_shift_max"] = round(max(ms), 4)
        results[h] = agg
        print(json.dumps(dict(h=h, **agg)), flush=True)
        if a.crops and h == float(a.crops):
            for f, o in outs.items():
                rgb = to_rgb(*o).permute(1, 2, 0).byte().cpu().numpy()
                cv2.imencode(".png", rgb[..., ::-1])[1].tofile(str(od / f"den_h{h:g}_f{f:04d}.png"))
                for lab, d in (("old", a.old), ("ref", a.ref)):
                    rgb = to_rgb(*load(d, f)).permute(1, 2, 0).byte().cpu().numpy()
                    cv2.imencode(".png", rgb[..., ::-1])[1].tofile(str(od / f"{lab}_f{f:04d}.png"))
    (od / f"calib_R{a.R}.json").write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "calib":
        calib(sys.argv[2:])
        sys.exit(0)
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("seg")
    ap.add_argument("--h", type=float)
    ap.add_argument("--hc", type=float)
    ap.add_argument("--R", type=int)
    ap.add_argument("--frames")
    ap.add_argument("--out")
    ap.add_argument("--no-swap", action="store_true")
    a = ap.parse_args()
    segs = list(SEGS) if a.seg == "all" else [a.seg]
    if a.cmd == "child":
        child(a.seg, a.h if a.h is not None else H_DEFAULT, a.R if a.R is not None else R_DEFAULT, a.hc)
    elif a.cmd == "run":
        fr = tuple(int(v) for v in a.frames.split("-")) if a.frames else None
        for s in segs:
            drive(s, h=a.h, R=a.R, frames=fr, out=a.out, swap=not a.no_swap)
    elif a.cmd == "undo":
        for s in segs:
            undo(s)
    elif a.cmd == "sheet":
        for s in segs:
            sheet(s)
    else:
        raise SystemExit("cmd: run / undo / sheet / child / calib")
