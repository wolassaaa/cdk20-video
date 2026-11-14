"""HKBU SCIE1007 coursework video: the moving background behind on-camera takes: the end card's hand-drawn liver
cells, a different set for every take.

    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/cellbg.py D                       every on-camera take of D
    _env/footage/Scripts/python.exe 镜头设计_v3/素材流程/cellbg.py D D_cam_3-01_t1 --variant normal --tag normal

Director's idea (11-12): the cells of the end card (styleframes/art/fusion/end) drift and bump behind the people,
random per take so nothing repeats, quieter than the end card, thin around the face; only behind on-camera takes.
Per take (5_place/place.json):
  1. cast: a seed made from the take's name picks 8 or so cells (size, sides, tint, one or two nuclei), where
     they start and how they drift; paths are aimed past the face, and a cast that still covers too much of the face
     area is thrown away and drawn again
  2. motion: the end card's own simulation (w5cells2_sim.run: cells flatten against each other, never overlap)
  3. picture: the end card's own Blender drawing (bl_w5cells2.py, EEVEE on the 5080) at the take's size and length,
     through bl_cellbg.py, which only changes the frame size
  4. composite on the card: cells pulled toward the paper colour (contrast), softened (defocus), the person from
     step 5 on top -> 5_place/<name>_wide[_tag].mp4 (11-13: full 16:9 frame, the person standing on the bottom edge at one side) with the take's sound
Settings: config.json video.backdrop_cells (speed, contrast, defocus). The drawn frames are deleted; the toned-down cells are kept as <name>_wideplate.mp4,
so after step 5 is redone `--recomp` only puts the person on again.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402

END = C.ROOT / "镜头设计_v3" / "styleframes" / "art" / "fusion" / "end"
BLENDER = "D:/software/tools/blender.exe"
FPS = 60
DW, DH = 1920, 1080                       # design px of the full 16:9 frame the cells are laid out in (as the end card)
FW, FH = 3840, 2160                       # the film frame
FILL_MAX = 1.40                           # 11-14 Fable: every take was pushed down to stand on the bottom edge, so the eye line sank
                                          # (0.48-0.70H); a take may be enlarged up to this much so its chest reaches the bottom with the eyes at EYE_Y
EYE_Y, TOP_Y = 0.45, 0.30                 # the eye line anchors every person (Fable 11-14); 0.38/0.11 as he gave made heads twice too big
                                          # (shoulders 0.55W against his own 0.26-0.30W), so the head is kept at 0.15H eye-to-top (B 1-06 test); head top
                                          # room 0.11; size follows from step 4's chest-up box (eyes a third down, 10% head room above the top)
SIDE_X = {"left": 0.28, "right": 0.72, "center": 0.50}   # center: monologue without props (Fable 11-14: 7-01, 8-01)    # where the person's centre stands, share of the width; the other side is for motion graphics
FACE_BOX = (0.5, 0.36, 0.156, 0.24)       # face area inside step 5's box: centre x, y, half-width, half-height as shares of the box
SHADOW_RGB, SH_ALPHA, SH_DY, SH_BLUR = (201, 197, 188), 0.18, round(0.01 * 2160), 0.03 * 2160 / 2.5   # Fable 11-14: offset 0.01H, blur 0.03H, 18 %
NO_SHADOW = {"C"}                         # dark shirt: a shadow only looks dirty
CELL_K = 0.66                             # cells sized to the person: the 5:6 version had the person 1560 design px high, now ~1026
FACE = None                               # face area in design px (x, y, half-width, half-height), set per take
SIDE = "left"                             # where the person stands in the take being made
# Fable's review 11-14: three zones instead of an even wallpaper. Behind the person dense and stronger; the motion-graphics
# side sparse, small, faint and slow, with a clean box where the words and ink lines go; a faint top band.
CONTRAST = {"person": 0.55, "gfx": 0.30, "clean": 0.20, "top": 0.35}
GFX_FROM = 0.45                           # the motion-graphics side starts this share of the width from the person's edge of the frame
CLEAN = (0.75, 0.5, 0.20, 0.225)          # clean box on the graphics side (left-standing person): centre x, y, half-width, half-height
GFX_MAX, GFX_R, GFX_V = 8, 0.6, 0.5       # graphics side: at most 8 cells starting there, radius x0.6, speed x0.5
FACE_COVER_MAX = 0.08                     # mean share of the face area cells may cover before the cast is redrawn
FREE_SHOWN_MIN = 0.18                     # mean share of the open background (where the person is not) cells must fill
                                          # (11-13: on D the first casts drifted behind the shoulders and almost nothing showed)
SPEED = {"slow": 0.5, "normal": 1.0}      # 1.0 = the end card's drift, scaled to this frame
PAPER = (237, 235, 228)


def placement(item, side):
    """Where step 5's box goes in the film frame: (x0, y0, w, h) in film px; the box may run past the frame's side."""
    from steps.s5_place import widen
    bw, bh = item["size"]
    c0, c1 = item["crop"], item.get("crop_wanted") or item["crop"]
    (sx0, _, _, _), want, pad_l = widen(c0, item["src_w"])
    s = (EYE_Y - TOP_Y) * FH / ((1 / 3 - 0.10) * (c1[3] - c1[1]))      # source px -> film px
    eye = c1[1] + (c1[3] - c1[1]) / 3                                     # eye line in the source
    s = min(max(s, (1 - EYE_Y) * FH / max(1.0, c0[3] - eye)), s * FILL_MAX)   # enlarge so the chest reaches the bottom
    h, w = round((c0[3] - c0[1]) * s), round(want * s)
    y0 = round(EYE_Y * FH - (eye - c0[1]) * s)
    y0 = max(y0, FH - h)                                                  # never floating above the bottom edge
    cx = (c1[0] + c1[2]) / 2 - (sx0 - pad_l)                              # face centre inside the box, source px
    return round(SIDE_X[side] * FW - cx * s), y0, w, h


def face_px(box):
    x0, y0, w, h = (v * DW / FW for v in box)
    return x0 + FACE_BOX[0] * w, y0 + FACE_BOX[1] * h, FACE_BOX[2] * w, FACE_BOX[3] * h


def side_of(item, items, cfg):
    """Left by default, motion graphics on the right; config video.layout.side moves a take or beat (in a dialogue the one who
    asks or cuts in stands on the right: advice taken 11-14)."""
    named = (cfg.get("layout") or {}).get("side", {})
    return named.get(item["name"], named.get(item["beat"], "left"))


def in_gfx(x):
    """Design x lies on the motion-graphics side."""
    if SIDE == "center":
        return False
    return x > GFX_FROM * DW if SIDE == "left" else x < (1 - GFX_FROM) * DW


def contrast_map(torch, F):
    """Per-pixel contrast of the cells toward the paper colour, film size (1, 1, FH, FW)."""
    y, x = torch.meshgrid(torch.linspace(0, 1, FH // 8, device="cuda"), torch.linspace(0, 1, FW // 8, device="cuda"), indexing="ij")
    gx = x if SIDE == "left" else 1 - x if SIDE == "right" else torch.zeros_like(x)
    k = torch.where(gx > GFX_FROM, torch.tensor(CONTRAST["gfx"], device="cuda"), torch.tensor(CONTRAST["person"], device="cuda"))
    cx, cy, hw, hh = CLEAN
    k = torch.where(((gx - cx).abs() < hw) & ((y - cy).abs() < hh), torch.minimum(k, torch.tensor(CONTRAST["clean"], device="cuda")), k)
    k = torch.where(y < 0.10, torch.minimum(k, torch.tensor(CONTRAST["top"], device="cuda")), k)
    from steps.s5_place import blur
    return F.interpolate(blur(k[None, None], 12.0, F, torch), (FH, FW), mode="bilinear")


def free_area(item, pdir, box):
    """Where the background shows in this take: mean matte of 12 frames placed in the frame at design size, True where it is open."""
    import cv2
    W, H = item["size"]
    x0, y0, w, h = (round(v * DW / FW) for v in box)
    sec = item["frames"] / FPS
    acc = np.zeros((DH, DW), np.float32)
    for k in range(12):
        b = subprocess.run([C.FFMPEG, "-v", "error", "-ss", f"{sec * (k + 0.5) / 12:.3f}", "-i", str(pdir / item["alpha"]), "-frames:v", "1",
                            "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        if len(b) == W * H:
            m = cv2.resize(np.frombuffer(b, np.uint8).reshape(H, W), (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
            a0, a1 = max(0, -x0), min(w, DW - x0)
            q0, q1 = max(0, -y0), min(h, DH - y0)
            acc[y0 + q0:y0 + q1, x0 + a0:x0 + a1] += m[q0:q1, a0:a1]
    return acc / 12 < 0.2


def cast(seed, seconds, speed, free):
    """Cells for one take: (name, radius, x, y, vx, vy, sides, turn, tint, nuclei, enters at)."""
    rng = np.random.default_rng(seed)
    fy_, fx_ = np.nonzero(free[::8, ::8])
    spots = np.stack([fx_ * 8, fy_ * 8], 1).astype(float) if len(fx_) else np.array([[0.0, 0.0], [DW, 0.0]])
    fx, fy, fw, fh = FACE
    inside = lambda x, y, m=1.0: ((x - fx) / (fw * m)) ** 2 + ((y - fy) / (fh * m)) ** 2 < 1

    def clear(x, y, vx, vy, r):
        """The straight path of a cell of radius r stays out of the face area."""
        for t in np.arange(0, seconds + 6, 0.25):
            px, py = x + vx * t, y + vy * t
            if abs(px - fx) < fw + r * 0.9 and abs(py - fy) < fh + r * 0.9:
                return False
        return True

    cells = []
    n_start, n_later = int(rng.integers(9, 14)), max(5, int(round(seconds / 1.1)))
    tries = 0
    while len(cells) < n_start + n_later and tries < 4000:
        tries += 1
        r = float(rng.uniform(90, 145)) * CELL_K
        v = float(rng.uniform(38, 62)) * CELL_K * speed
        k = len(cells)
        if k < n_start:                                   # in the open background from the first frame, off the face
            x, y = (float(v) for v in spots[rng.integers(len(spots))])
            tx, ty = spots[rng.integers(len(spots))]
            ang = float(np.arctan2(ty - y, tx - x)) if np.hypot(tx - x, ty - y) > 50 else float(rng.uniform(0, 2 * np.pi))
            t_on = 0.0
            if inside(x, y, 1.6) or any(np.hypot(x - c[2], y - c[3]) < 1.05 * (r + c[1]) for c in cells):
                continue
        else:                                             # comes in over an edge later on
            edge = int(rng.integers(0, 4))
            x, y = [(-r - 20, rng.uniform(0, DH)), (DW + r + 20, rng.uniform(0, DH)), (rng.uniform(0, DW), -r - 20), (rng.uniform(0, DW), DH + r + 20)][edge]
            tx, ty = spots[rng.integers(len(spots))]            # aimed into the open background
            ang = float(np.arctan2(ty - y, tx - x))
            t_on = float(rng.uniform(0, max(0.5, seconds - 1.5)))
        if in_gfx(x):
            if sum(in_gfx(c[2]) for c in cells) >= GFX_MAX:
                continue
            r, v = r * GFX_R, v * GFX_V
        vx, vy = v * np.cos(ang), v * np.sin(ang)
        if not clear(x, y, vx, vy, r):
            continue
        cells.append((f"c{k}", round(r), round(float(x)), round(float(y)), round(float(vx), 1), round(float(vy), 1), int(rng.integers(5, 8)),
                      round(float(rng.uniform(0.02, 0.045) * rng.choice([-1, 1]) * (0.5 + speed / 2)), 3),
                      "r" if rng.random() < 0.25 else "n", 2 if rng.random() < 0.3 else 1, round(t_on, 2)))
    return cells


def simulate(cells, seconds, tmp, free):
    """Run the end card's simulation on this cast; -> (share of the face area covered, share of the open background
    filled), both averaged over the take."""
    sys.path.insert(0, str(END))
    import w5cells2_sim as S
    S.FPS, S.SUB, S.SHIFT = FPS, 180 // FPS, 0
    S.W, S.H, S.NF = DW, DH, int(round(seconds * FPS))
    S.CAST, S.KICKS, S.SPINS, S.PULSES = cells, [], [], []
    R, out = S.run()
    import cv2
    fx, fy, fw, fh = FACE
    cover, shown = [], []
    free4 = cv2.resize(free.astype(np.uint8), (DW // 4, DH // 4), interpolation=cv2.INTER_NEAREST) > 0
    for f in range(0, S.NF, 6):
        im = np.zeros((DH // 4, DW // 4), np.uint8)
        for i in range(len(cells)):
            if out["pos"][f, i, 0] > -5000:
                cv2.fillPoly(im, [(S.poly(i, R, out, f) / 4).astype(np.int32)], 255)
        cover.append(im[int((fy - fh) / 4):int((fy + fh) / 4), int((fx - fw) / 4):int((fx + fw) / 4)].mean() / 255)
        shown.append(im[free4].mean() / 255 if free4.any() else 0.0)
    tmp.mkdir(parents=True, exist_ok=True)
    np.savez(str(tmp / "sim.npz"), R=R, **out)
    C.write_json(tmp / "cast.json", {"W": DW, "H": DH, "FPS": FPS, "NF": S.NF, "CAST": cells, "TMP": str(tmp).replace("\\", "/") + "/"})
    return float(np.mean(cover)), float(np.mean(shown))


def render(tmp, frames, scale):
    """Blender draws the frames into tmp/png; returns seconds used."""
    t = time.time()
    bt = C.ENV / "tmp" / "blender"                     # Blender's own temp, away from the Windows one (it was wiped mid-render on 11-02)
    bt.mkdir(parents=True, exist_ok=True)
    env = dict(__import__("os").environ, CELLBG_CAST=str(tmp / "cast.json"), TEMP=str(bt), TMP=str(bt))
    r = subprocess.run([BLENDER, "-b", "-t", "2", "--python", str(HERE / "bl_cellbg.py"), "--", "0", str(frames - 1), "1", str(tmp / "png"), f"{scale:.4f}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    done = len(list((tmp / "png").glob("c_*.png")))
    if done < frames:
        raise RuntimeError(f"Blender 只画出 {done}/{frames} 帧：" + (r.stdout[-600:] + r.stderr[-300:]))
    return time.time() - t


def plate(tmp, item, look, dst):
    """The drawn cells, toned down and softened, as <name>_wideplate.mp4: kept so the person can be put on again
    (step 5 redone) without drawing the cells again."""
    import torch
    from steps.s5_place import blur
    import torch.nn.functional as F
    W, H = FW, FH
    w = subprocess.Popen([C.FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "14", "-b:v", "0", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                          "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", str(dst)], stdin=subprocess.PIPE)
    paper = torch.tensor(PAPER, device="cuda").float().view(1, 3, 1, 1) / 255
    kmap = contrast_map(torch, F)
    n = 0
    while (png := tmp / "png" / f"c_{n:04d}.png").exists():
        with torch.inference_mode():
            g = torch.from_numpy(C.imread(png)[:, :, ::-1].copy()).cuda().permute(2, 0, 1)[None].float() / 255
            if g.shape[-2:] != (H, W):
                g = F.interpolate(g, (H, W), mode="bilinear")
            g = paper + kmap * (g - paper)
            if look.get("defocus"):
                g = blur(g, float(look.get("defocus_px", 3.0)), F, torch)
            w.stdin.write(g[0].permute(1, 2, 0).mul(255).round().byte().cpu().numpy().tobytes())
        n += 1
    w.stdin.close()
    w.wait()
    return n


def composite(item, pdir, plate_path, dst, box, shadow=True):
    """The person from step 5, scaled into place (box), on the full-frame cell plate; the take's sound; h264_nvenc."""
    import cv2
    import torch
    from steps.s5_place import blur
    import torch.nn.functional as F
    W, H = item["size"]
    rd = lambda f, pix: subprocess.Popen([C.FFMPEG, "-v", "error", "-i", str(pdir / f), "-f", "rawvideo", "-pix_fmt", pix, "-"], stdout=subprocess.PIPE, bufsize=W * H * 3)
    r_fg, r_a = rd(item["fg"], "rgb24"), rd(item["alpha"], "gray")
    bx, by, bw, bh = box
    a0, a1 = max(0, -bx), min(bw, FW - bx)                  # the part of the box inside the frame
    q0, r1 = max(0, -by), min(bh, FH - by)                  # rows of the box inside the frame
    SH_RGB = torch.tensor(SHADOW_RGB, device="cuda").float().view(1, 3, 1, 1) / 255
    w = subprocess.Popen([C.FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-", "-i", str(pdir / item["wav"]),
                          "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "17", "-b:v", "0", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                          "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(dst)], stdin=subprocess.PIPE)
    r_bg = rd(plate_path.name, "rgb24")
    n, keep = 0, None
    while True:
        b1, b2, b3 = r_fg.stdout.read(W * H * 3), r_a.stdout.read(W * H), r_bg.stdout.read(FW * FH * 3)
        if len(b1) < W * H * 3 or len(b2) < W * H or len(b3) < FW * FH * 3:
            break
        with torch.inference_mode():
            g = torch.frombuffer(bytearray(b3), dtype=torch.uint8).cuda().view(FH, FW, 3).permute(2, 0, 1)[None].float() / 255
            x = torch.frombuffer(bytearray(b1), dtype=torch.uint8).cuda().view(H, W, 3).permute(2, 0, 1)[None].float() / 255
            a = torch.frombuffer(bytearray(b2), dtype=torch.uint8).cuda().view(1, 1, H, W).float() / 255
            x, a = F.interpolate(x, (bh, bw), mode="bicubic").clamp(0, 1)[..., q0:r1, a0:a1], F.interpolate(a, (bh, bw), mode="bilinear")[..., q0:r1, a0:a1]
            if shadow:                                                   # soft shadow so white shirts do not melt into the paper
                sh = torch.zeros_like(g[:, :1])
                t0 = by + q0 + SH_DY
                sh[:, :, t0:FH, bx + a0:bx + a1] = a[..., :FH - t0, :]
                sh = F.interpolate(blur(F.interpolate(sh, scale_factor=0.25, mode="area"), SH_BLUR / 4, F, torch), (FH, FW), mode="bilinear") * SH_ALPHA
                g = g * (1 - sh) + SH_RGB * sh
            reg = g[:, :, by + q0:by + r1, bx + a0:bx + a1]
            g[:, :, by + q0:by + r1, bx + a0:bx + a1] = x * a + reg * (1 - a)
            out = g[0].permute(1, 2, 0).mul(255).round().byte().cpu().numpy()
        w.stdin.write(out.tobytes())
        if n == item["frames"] // 2:
            keep = out[:, :, ::-1]
        n += 1
    for p in (r_fg, r_a, r_bg):
        p.stdout.close()
        p.wait()
    w.stdin.close()
    w.wait()
    return n, keep


def main():
    C.setup_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("person")
    ap.add_argument("takes", nargs="*", help="names of takes; none = every on-camera take of the person")
    ap.add_argument("--variant", default=None, help="slow | normal (default: from config speed)")
    ap.add_argument("--tag", default="", help="suffix of the output name, for samples")
    ap.add_argument("--recomp", action="store_true", help="only put the person (step 5 redone) on the kept cell plates again")
    a = ap.parse_args()
    global FACE, SIDE
    vcfg = C.load_config()["video"]
    look = {k: v for k, v in vcfg["backdrop_cells"].items() if not k.startswith("_")}
    speed = SPEED[a.variant] if a.variant else float(look.get("speed", 0.5))
    pdir = C.OUT / a.person / C.STEP_DIRS[5]
    every = [i for i in C.read_json(pdir / "place.json")["items"] if i.get("fg")]
    items = [i for i in every if not a.takes or i["name"] in a.takes]
    clips = {c["name"]: c for c in C.read_json(C.OUT / a.person / C.STEP_DIRS[4] / "index.json")["clips"]}
    log = C.read_json(pdir / "wide.json") if (pdir / "wide.json").exists() else {}
    for it in items:
        key = it["name"] + ("_" + a.tag if a.tag else "")
        dst = pdir / f"{key.replace(it['name'], it['name'] + '_wide')}.mp4"
        pl = dst.with_name(dst.stem.replace("_wide", "_wideplate") + ".mp4")
        it = it | {"crop_wanted": clips[it["name"]].get("crop_wanted"), "src_w": clips[it["name"]]["size"][0]}
        side = side_of(it, every, vcfg)
        box = placement(it, side)
        FACE = face_px(box)
        SIDE = side
        stamp = {"cast": 5, "zones": CONTRAST, "side": side, "box": list(box),   # list: a tuple never equals the list read back from wide.json
                 "speed": speed, "look": look, "frames": it["frames"], "fg_size": (pdir / it["fg"]).stat().st_size}
        if log.get(key, {}).get("stamp") == stamp and dst.exists():
            print(f"  {key:22} 已做过，跳过")
            continue
        if pl.exists() and {k: v for k, v in log.get(key, {}).get("stamp", {}).items() if k != "fg_size"} == {k: v for k, v in stamp.items() if k != "fg_size"}:
            t0 = time.time()
            n, keep = composite(it, pdir, pl, dst, box, a.person not in NO_SHADOW)
            if keep is not None:
                C.imwrite(pdir / f"{dst.stem}.jpg", keep, 90)
            log[key] |= {"frames": n, "stamp": stamp, "ok": n == it["frames"], "recomp_seconds": round(time.time() - t0, 1)}
            C.write_json(pdir / "wide.json", log)
            print(f"  {key:22} 细胞底片已有，只重新合成人像 {time.time() - t0:.0f} 秒  {'过' if n == it['frames'] else '没过：帧数不对'}", flush=True)
            continue
        if a.recomp:
            print(f"  {key:22} 没有细胞底片，跳过")
            continue
        t0 = time.time()
        tmp = C.ENV / "tmp" / "cellbg" / key
        shutil.rmtree(tmp, ignore_errors=True)
        base = int(hashlib.md5(it["name"].encode()).hexdigest()[:8], 16)
        seconds = it["frames"] / FPS
        free = free_area(it, pdir, box)
        best = None
        for attempt in range(12):
            cells = cast(base + attempt, seconds, speed, free)
            cover, shown = simulate(cells, seconds, tmp, free)
            if cover <= FACE_COVER_MAX and (best is None or shown > best[0]):
                best = (shown, attempt)
            if cover <= FACE_COVER_MAX and shown >= FREE_SHOWN_MIN:
                break
        else:
            if best:                                          # none reached the minimum: the fullest one that keeps off the face
                attempt = best[1]
                cells = cast(base + attempt, seconds, speed, free)
                cover, shown = simulate(cells, seconds, tmp, free)
        t_r = render(tmp, it["frames"], FH / DH)
        n_pl = plate(tmp, it, look, pl)
        n, keep = composite(it, pdir, pl, dst, box, a.person not in NO_SHADOW)
        if keep is not None:
            C.imwrite(pdir / f"{dst.stem}.jpg", keep, 90)
        shutil.rmtree(tmp, ignore_errors=True)
        log[key] = {"file": dst.name, "side": side, "plate": pl.name, "plate_frames": n_pl, "seed": base + attempt, "cells": len(cells), "face_cover": round(cover, 3), "free_shown": round(shown, 3), "frames": n, "frames_expected": it["frames"],
                    "render_seconds": round(t_r, 1), "seconds": round(time.time() - t0, 1), "stamp": stamp, "ok": n == it["frames"]}
        C.write_json(pdir / "wide.json", log)
        print(f"  {key:22} {len(cells)} 个细胞，脸周围平均盖住 {cover:.1%}，露出的背景里细胞占 {shown:.0%}；{n} 帧，画 {t_r:.0f} 秒（每帧 {t_r / max(1, n) * 1000:.0f} 毫秒），共 {time.time() - t0:.0f} 秒  "
              f"{'过' if n == it['frames'] and shown >= FREE_SHOWN_MIN else '没过：帧数不对' if n != it['frames'] else '提醒：细胞偏少'}", flush=True)


if __name__ == "__main__":
    main()
