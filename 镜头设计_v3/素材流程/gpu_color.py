"""HKBU SCIE1007 coursework video: the pipeline's HDR -> Rec.709 conversion as a 3D table, applied on the GPU.

The look the stills were approved with is ffmpeg's zscale + hable chain (common.SDR_VF). That chain runs on the
CPU and was the bottleneck of step 4 (about 60-90 ms per 4K frame). Here the SAME chain is run once on a small
picture holding every point of an N^3 grid of 10-bit Y'CbCr codes, and the answers are kept as a table
(_env/cache/lut/). A frame is then converted by looking its pixels up in the table (trilinear), in torch:

    lut = load_lut()                              # builds the table with ffmpeg the first time (a few seconds)
    rgb = apply(lut, y, uv)                       # y: HxW uint16, uv: H/2 x W/2 x 2 uint16 (p010, 10 bits in the
                                                  # top of each word) -> 1x3xHxW float 0..1, R'G'B' Rec.709

Only for sources tagged like the phones' clips (bt2020nc, arib-std-b67, bt2020, tv range); check() compares a real
frame converted both ways.
"""
import subprocess

import numpy as np

import common as C

N = 65
W_, H_ = 525, 524                                  # N^3 = 274 625 points fit in 525 x 524
TAGS = ["-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", "-color_range", "tv"]
CHAIN = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
         "zscale=t=bt709:m=bt709:r=pc:d=none,format=gbrp16le")


def build_lut():
    """-> float32 array [N, N, N, 3] indexed [cr, cb, y], values 0..1 (R, G, B)."""
    code = np.round(np.arange(N) * 1023 / (N - 1)).astype(np.uint16)
    cr, cb, y = np.meshgrid(code, code, code, indexing="ij")
    planes = []
    for p in (y, cb, cr):
        full = np.full(W_ * H_, 512, np.uint16)
        full[: N ** 3] = p.ravel()
        planes.append(full)
    raw = np.concatenate(planes).astype("<u2").tobytes()
    out = subprocess.run([C.FFMPEG, "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv444p10le", "-s", f"{W_}x{H_}", *TAGS, "-i", "-",
                          "-vf", CHAIN, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gbrp16le", "-"], input=raw, capture_output=True)
    if out.returncode or len(out.stdout) != W_ * H_ * 6:
        raise RuntimeError("建色彩表失败：" + out.stderr.decode("utf-8", "replace")[:300])
    g, b, r = np.frombuffer(out.stdout, "<u2").reshape(3, W_ * H_)[:, : N ** 3].astype(np.float32) / 65535
    return np.stack([r, g, b], axis=-1).reshape(N, N, N, 3)


def load_lut(device="cuda"):
    import torch
    path = C.ENV / "cache" / "lut" / f"hlg_bt2020_to_709_hable_{N}.npy"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, build_lut())
    lut = torch.from_numpy(np.load(path)).to(device)                 # [cr, cb, y, 3]
    return lut.permute(3, 0, 1, 2)[None].contiguous()                # 1 x 3 x D(cr) x H(cb) x W(y) for grid_sample


def apply(lut, y, uv):
    """y: HxW, uv: (H/2)x(W/2)x2 torch uint16/int tensors on the lut's device, p010 layout. -> 1x3xHxW float."""
    import torch
    import torch.nn.functional as F
    h, w = y.shape
    yv = (y.float() / 64.0)                                           # 10-bit code, 0..1023
    c = (uv.float() / 64.0).permute(2, 0, 1)[None]                    # 1 x 2 x h/2 x w/2
    # chroma is sited left (between rows, on even columns): half a chroma pixel to the left of centre
    c = F.interpolate(c, size=(h, w), mode="bilinear", align_corners=False)
    grid = torch.stack([yv, c[0, 0], c[0, 1]], dim=-1) / 1023.0 * 2 - 1   # x = y, y = cb, z = cr
    out = F.grid_sample(lut, grid[None, None], mode="bilinear", padding_mode="border", align_corners=True)
    return out[:, :, 0].clamp(0, 1)


def read_p010(buf, w, h, device="cuda"):
    """One raw p010le frame (w*h*3 bytes) -> (y, uv) tensors on the device."""
    import torch
    a = torch.frombuffer(bytearray(buf), dtype=torch.int16).to(device)
    y = (a[: w * h].int() & 0xFFFF).reshape(h, w)
    uv = (a[w * h:].int() & 0xFFFF).reshape(h // 2, w // 2, 2)
    return y, uv


def check(src, t=3.0, device="cpu"):
    """Convert one frame of a real clip both ways; -> (mean, 99th percentile, max) absolute difference in 8-bit levels."""
    import torch
    w, h = [int(v) for v in subprocess.run([C.FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                             "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip().split(",")[:2]]
    one = lambda vf, fmt: subprocess.run([C.FFMPEG, "-v", "error", "-noautorotate", "-ss", str(t), "-i", str(src), "-frames:v", "1"] +
                                         (["-vf", vf] if vf else []) + ["-f", "rawvideo", "-pix_fmt", fmt, "-"], capture_output=True).stdout
    ref = np.frombuffer(one(C.SDR_VF.replace("format=yuv420p", "format=bgr24"), "bgr24"), np.uint8).reshape(h, w, 3)[:, :, ::-1]
    y, uv = read_p010(one(None, "p010le"), w, h, device)
    got = (apply(load_lut(device), y, uv)[0].permute(1, 2, 0) * 255).round().cpu().numpy()
    d = np.abs(got - ref.astype(np.float32))
    d_tv = np.abs(np.round(got * 219 / 255 + 16) - ref.astype(np.float32))
    return {"full": [float(d.mean()), float(np.percentile(d, 99)), float(d.max())],
            "tv": [float(d_tv.mean()), float(np.percentile(d_tv, 99)), float(d_tv.max())], "ref_min_max": [int(ref.min()), int(ref.max())]}
