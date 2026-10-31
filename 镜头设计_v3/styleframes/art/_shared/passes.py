"""HKBU SCIE1007 coursework science video. Loads the shared CDK20 data passes for quick style tests in numpy.

    import sys; sys.path.insert(0, r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared")
    from passes import load, save
    P = load(scale=0.5)      # dict of float32 arrays. key rim ao depth conf mask: H x W. normal pos: H x W x 3
    save(rgb, "out.png")     # rgb float 0..1, H x W x 3

conf is real pLDDT / 100; below 0.7 is the low-confidence tail. Pixels outside the protein have mask 0, the other passes are undefined there.
"""
from pathlib import Path

import numpy as np
from PIL import Image

NPZ = Path(__file__).resolve().parent.parent / "_passes" / "cdk20_passes.npz"


def load(scale=1.0):
    d = np.load(NPZ)
    out = {k: d[k].astype(np.float32) for k in d.files}
    m = out["mask"] > 0.001
    for k in ("key", "rim", "ao", "depth", "conf", "normal", "pos"):  # undo edge premultiply so style code can threshold freely
        a = out[k]
        a = a / np.maximum(out["mask"], 1e-3) if a.ndim == 2 else a / np.maximum(out["mask"], 1e-3)[..., None]
        out[k] = np.where(m if a.ndim == 2 else m[..., None], a, 0)
    if scale != 1.0:
        h, w = out["mask"].shape
        size = (round(w * scale), round(h * scale))
        for k, a in out.items():
            ch = [a] if a.ndim == 2 else [a[..., i] for i in range(a.shape[2])]
            r = [np.asarray(Image.fromarray(c).resize(size, Image.BILINEAR)) for c in ch]
            out[k] = r[0] if a.ndim == 2 else np.stack(r, -1)
    return out


def save(rgb, path):
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)
