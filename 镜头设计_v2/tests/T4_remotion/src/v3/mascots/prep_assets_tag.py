# HKBU SCIE1007 coursework video: post-credits AI skit (ShowTag.jsx). Character art -> lean Remotion public dir + size table.
# 19 section 4.2 (2): Gemini reads codex/v5/gemini first (v4 only as a stand-in), everything else as before; then every
# published image is measured into art_meta.json. ShowTag.jsx takes ALL scaling, placement and cropping from that table.
#   <cbx python> prep_assets_tag.py [--dst G:/cdk20/work/mascots/pub_tag/t] [--meta art_meta.json] [--force-gemini]
# Measured per image: w, h, bbox of the opaque area (alpha > 40), top (head top y), foot (bbox bottom, full-body art),
# face_cx (centroid x of the opaque area in the top 18 % band of the bbox).
# Busts also get k = bust px per full_neutral px of the same character, found by matching the head silhouette width profile
# (top 9 % of the full figure) between the two images; this makes a bust "equivalent to" a given full-body zoom.
import argparse, json, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "G:/cdk20/work/mascots/codex"
EXPR = "neutral blink talk_a talk_o wink laugh smug pout surprised shy sigh think wave prop".split()
WHO = ["claude", "gpt", "deepseek", "gemini"]
TAGS = ["Pro", "Flash", "Flash-Lite", "Nano", "Deep-Think", "Exp-1120"]


def src_dir(w):
    if w == "gemini" and os.path.isdir(f"{ROOT}/v5/gemini"):
        return f"{ROOT}/v5/gemini"
    return f"{ROOT}/v4/{w}"


def convert(dst, force_gemini):
    for w in WHO:
        os.makedirs(f"{dst}/{w}", exist_ok=True)
        s = src_dir(w)
        force = force_gemini and w == "gemini"
        for e in EXPR:
            for kind, tw in (("full", 1536), ("bust", 2304)):
                out = f"{dst}/{w}/{kind}_{e}.webp"
                if os.path.exists(out) and not force:
                    continue
                im = Image.open(f"{s}/{kind}_{e}.png").convert("RGBA")
                th = round(im.height * tw / im.width)
                im.resize((tw, th), Image.LANCZOS).save(out, "WEBP", quality=93, method=4)
        if w == "gemini":
            out = f"{dst}/gemini/clone.webp"
            if force or not os.path.exists(out):
                im = Image.open(f"{s}/clone.png").convert("RGBA")
                im.resize((1536, round(im.height * 1536 / im.width)), Image.LANCZOS).save(out, "WEBP", quality=92, method=4)
            for t in TAGS:
                out = f"{dst}/gemini/tag_{t}.png"
                if force or not os.path.exists(out):
                    Image.open(f"{s}/tag_{t}.png").save(out)
        print(w, "from", s, flush=True)


def alpha(p):
    return np.asarray(Image.open(p).convert("RGBA"))[:, :, 3] > 40


def measure(p, full=True):
    a = alpha(p)
    h, w = a.shape
    ys = np.where(a.any(1))[0]; xs = np.where(a.any(0))[0]
    x0, x1, y0, y1 = int(xs[0]), int(xs[-1]) + 1, int(ys[0]), int(ys[-1]) + 1
    band = a[y0: y0 + max(2, int((y1 - y0) * 0.18))]
    cols = np.where(band)[1]
    m = {"w": w, "h": h, "bbox": [x0, y0, x1, y1], "top": y0, "face_cx": round(float(cols.mean()), 1)}
    if full:
        m["foot"] = y1
    return m, a


def width_profile(a):
    ys = np.where(a.any(1))[0]
    out = []
    for y in range(ys[0], ys[-1] + 1):
        xs = np.where(a[y])[0]
        out.append(xs[-1] - xs[0] if len(xs) else 0)
    return np.array(out, float)


def bust_k(full_a, bust_a):
    wf, wb = width_profile(full_a), width_profile(bust_a)
    D = int(len(wf) * 0.09)
    d = np.arange(D)
    best = None
    for k in np.linspace(0.5, 8.0, 1501):
        idx = (d * k).astype(int)
        if idx[-1] >= len(wb):
            break
        err = float(np.mean((wb[idx] / k - wf[d]) ** 2))
        if best is None or err < best[0]:
            best = (err, k)
    return round(best[1], 4), round(best[0] ** 0.5, 1)


def build_meta(dst):
    meta = {}
    for w in WHO:
        d = {}
        fm, fa = measure(f"{dst}/{w}/full_neutral.webp")
        for e in EXPR:
            d[f"full_{e}"] = measure(f"{dst}/{w}/full_{e}.webp")[0] if e != "neutral" else fm
            bm, ba = measure(f"{dst}/{w}/bust_{e}.webp", full=False)
            bm["k"], bm["k_rmse"] = bust_k(fa, ba)
            d[f"bust_{e}"] = bm
        if w == "gemini":
            d["clone"] = measure(f"{dst}/gemini/clone.webp")[0]
            for t in TAGS:
                im = Image.open(f"{dst}/gemini/tag_{t}.png")
                d[f"tag_{t}"] = {"w": im.width, "h": im.height}
        meta[w] = d
        print(w, "full H", fm["foot"] - fm["top"], "bust k", [d[f"bust_{e}"]["k"] for e in EXPR], flush=True)
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dst", default="G:/cdk20/work/mascots/pub_tag/t")
    ap.add_argument("--meta", default=os.path.join(HERE, "art_meta.json"))
    ap.add_argument("--force-gemini", action="store_true")
    ap.add_argument("--meta-only", action="store_true")
    a = ap.parse_args()
    if not a.meta_only:
        convert(a.dst, a.force_gemini)
    m = build_meta(a.dst)
    m["_note"] = "HKBU SCIE1007 coursework video: generated by prep_assets_tag.py from " + a.dst + " (do not edit by hand)"
    m["_gemini_src"] = src_dir("gemini")
    json.dump(m, open(a.meta, "w", encoding="utf-8"), indent=1)
    print("wrote", a.meta)
