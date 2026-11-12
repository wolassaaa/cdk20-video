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
     step 5 on top -> 5_place/<name>_cells[_tag].mp4 with the take's sound
Settings: config.json video.backdrop_cells (speed, contrast, defocus). The drawn frames are temporary and deleted.
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
DW, DH = 1300, 1560                       # design px the cells are laid out in (5:6); the end card used 1920 x 1080
FACE = (0.5, 0.36, 0.25, 0.24)            # centre x, y and half-width, half-height of the face area, as shares of the frame
FACE_COVER_MAX = 0.08                     # mean share of the face area cells may cover before the cast is redrawn
SPEED = {"slow": 0.5, "normal": 1.0}      # 1.0 = the end card's drift, scaled to this frame
PAPER = (237, 235, 228)


def cast(seed, seconds, speed):
    """Cells for one take: (name, radius, x, y, vx, vy, sides, turn, tint, nuclei, enters at)."""
    rng = np.random.default_rng(seed)
    fx, fy, fw, fh = FACE[0] * DW, FACE[1] * DH, FACE[2] * DW, FACE[3] * DH
    inside = lambda x, y, m=1.0: ((x - fx) / (fw * m)) ** 2 + ((y - fy) / (fh * m)) ** 2 < 1

    def clear(x, y, vx, vy, r):
        """The straight path of a cell of radius r stays out of the face area."""
        for t in np.arange(0, seconds + 6, 0.25):
            px, py = x + vx * t, y + vy * t
            if abs(px - fx) < fw + r * 0.9 and abs(py - fy) < fh + r * 0.9:
                return False
        return True

    cells = []
    n_start, n_later = int(rng.integers(4, 6)), max(2, int(round(seconds / 2.2)))
    tries = 0
    while len(cells) < n_start + n_later and tries < 4000:
        tries += 1
        r = float(rng.uniform(100, 160))
        v = float(rng.uniform(38, 62)) * speed
        k = len(cells)
        if k < n_start:                                   # in the picture from the first frame, off the face
            x, y = float(rng.uniform(-0.05, 1.05) * DW), float(rng.uniform(-0.02, 1.02) * DH)
            ang = float(rng.uniform(0, 2 * np.pi))
            t_on = 0.0
            if inside(x, y, 1.6) or any(np.hypot(x - c[2], y - c[3]) < 1.05 * (r + c[1]) for c in cells):
                continue
        else:                                             # comes in over an edge later on
            edge = int(rng.integers(0, 4))
            x, y = [(-r - 20, rng.uniform(0, DH)), (DW + r + 20, rng.uniform(0, DH)), (rng.uniform(0, DW), -r - 20), (rng.uniform(0, DW), DH + r + 20)][edge]
            tx, ty = rng.uniform(0, DW), rng.uniform(0, DH)
            ang = float(np.arctan2(ty - y, tx - x))
            t_on = float(rng.uniform(0, max(0.5, seconds - 1.5)))
        vx, vy = v * np.cos(ang), v * np.sin(ang)
        if not clear(x, y, vx, vy, r):
            continue
        cells.append((f"c{k}", round(r), round(float(x)), round(float(y)), round(float(vx), 1), round(float(vy), 1), int(rng.integers(5, 8)),
                      round(float(rng.uniform(0.02, 0.045) * rng.choice([-1, 1]) * (0.5 + speed / 2)), 3),
                      "r" if rng.random() < 0.25 else "n", 2 if rng.random() < 0.3 else 1, round(t_on, 2)))
    return cells


def simulate(cells, seconds, tmp):
    """Run the end card's simulation on this cast; -> (R, out, share of the face area covered, averaged over the take)."""
    sys.path.insert(0, str(END))
    import w5cells2_sim as S
    S.FPS, S.SUB, S.SHIFT = FPS, 180 // FPS, 0
    S.W, S.H, S.NF = DW, DH, int(round(seconds * FPS))
    S.CAST, S.KICKS, S.SPINS, S.PULSES = cells, [], [], []
    R, out = S.run()
    import cv2
    fx, fy, fw, fh = FACE[0] * DW, FACE[1] * DH, FACE[2] * DW, FACE[3] * DH
    cover = []
    for f in range(0, S.NF, 6):
        im = np.zeros((DH // 4, DW // 4), np.uint8)
        for i in range(len(cells)):
            if out["pos"][f, i, 0] > -5000:
                cv2.fillPoly(im, [(S.poly(i, R, out, f) / 4).astype(np.int32)], 255)
        cover.append(im[int((fy - fh) / 4):int((fy + fh) / 4), int((fx - fw) / 4):int((fx + fw) / 4)].mean() / 255)
    tmp.mkdir(parents=True, exist_ok=True)
    np.savez(str(tmp / "sim.npz"), R=R, **out)
    C.write_json(tmp / "cast.json", {"W": DW, "H": DH, "FPS": FPS, "NF": S.NF, "CAST": cells, "TMP": str(tmp).replace("\\", "/") + "/"})
    return float(np.mean(cover))


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


def composite(item, pdir, tmp, look, dst):
    """Cells (softened, toned down) under the person from step 5; the take's sound; h264_nvenc."""
    import cv2
    import torch
    from steps.s5_place import blur
    import torch.nn.functional as F
    W, H = item["size"]
    rd = lambda f, pix: subprocess.Popen([C.FFMPEG, "-v", "error", "-i", str(pdir / f), "-f", "rawvideo", "-pix_fmt", pix, "-"], stdout=subprocess.PIPE, bufsize=W * H * 3)
    r_fg, r_a = rd(item["fg"], "rgb24"), rd(item["alpha"], "gray")
    w = subprocess.Popen([C.FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(pdir / item["wav"]),
                          "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "17", "-b:v", "0", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
                          "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(dst)], stdin=subprocess.PIPE)
    paper = torch.tensor(PAPER, device="cuda").float().view(1, 3, 1, 1) / 255
    n, keep = 0, None
    while True:
        b1, b2 = r_fg.stdout.read(W * H * 3), r_a.stdout.read(W * H)
        png = tmp / "png" / f"c_{n:04d}.png"
        if len(b1) < W * H * 3 or len(b2) < W * H or not png.exists():
            break
        bg = C.imread(png)[:, :, ::-1]
        with torch.inference_mode():
            g = torch.from_numpy(bg.copy()).cuda().permute(2, 0, 1)[None].float() / 255
            if g.shape[-2:] != (H, W):
                g = F.interpolate(g, (H, W), mode="bilinear")
            g = paper + look["contrast"] * (g - paper)
            if look.get("defocus"):
                g = blur(g, float(look.get("defocus_px", 3.0)), F, torch)
            x = torch.frombuffer(bytearray(b1), dtype=torch.uint8).cuda().view(H, W, 3).permute(2, 0, 1)[None].float() / 255
            a = torch.frombuffer(bytearray(b2), dtype=torch.uint8).cuda().view(1, 1, H, W).float() / 255
            out = (x * a + g * (1 - a))[0].permute(1, 2, 0).mul(255).round().byte().cpu().numpy()
        w.stdin.write(out.tobytes())
        if n == item["frames"] // 2:
            keep = out[:, :, ::-1]
        n += 1
    for p in (r_fg, r_a):
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
    a = ap.parse_args()
    look = {k: v for k, v in C.load_config()["video"]["backdrop_cells"].items() if not k.startswith("_")}
    speed = SPEED[a.variant] if a.variant else float(look.get("speed", 0.5))
    pdir = C.OUT / a.person / C.STEP_DIRS[5]
    items = [i for i in C.read_json(pdir / "place.json")["items"] if i.get("fg") and (not a.takes or i["name"] in a.takes)]
    log = C.read_json(pdir / "cells.json") if (pdir / "cells.json").exists() else {}
    for it in items:
        key = it["name"] + ("_" + a.tag if a.tag else "")
        dst = pdir / f"{key.replace(it['name'], it['name'] + '_cells')}.mp4"
        stamp = {"speed": speed, "look": look, "frames": it["frames"], "fg_size": (pdir / it["fg"]).stat().st_size}
        if log.get(key, {}).get("stamp") == stamp and dst.exists():
            print(f"  {key:22} 已做过，跳过")
            continue
        t0 = time.time()
        tmp = C.ENV / "tmp" / "cellbg" / key
        shutil.rmtree(tmp, ignore_errors=True)
        base = int(hashlib.md5(it["name"].encode()).hexdigest()[:8], 16)
        seconds = it["frames"] / FPS
        for attempt in range(12):
            cells = cast(base + attempt, seconds, speed)
            cover = simulate(cells, seconds, tmp)
            if cover <= FACE_COVER_MAX:
                break
        t_r = render(tmp, it["frames"], it["size"][1] / DH)
        n, keep = composite(it, pdir, tmp, look, dst)
        if keep is not None:
            C.imwrite(pdir / f"{dst.stem}.jpg", keep, 90)
        shutil.rmtree(tmp, ignore_errors=True)
        log[key] = {"file": dst.name, "seed": base + attempt, "cells": len(cells), "face_cover": round(cover, 3), "frames": n, "frames_expected": it["frames"],
                    "render_seconds": round(t_r, 1), "seconds": round(time.time() - t0, 1), "stamp": stamp, "ok": n == it["frames"]}
        C.write_json(pdir / "cells.json", log)
        print(f"  {key:22} {len(cells)} 个细胞，脸周围平均盖住 {cover:.1%}；{n} 帧，画 {t_r:.0f} 秒（每帧 {t_r / max(1, n) * 1000:.0f} 毫秒），共 {time.time() - t0:.0f} 秒  "
              f"{'过' if n == it['frames'] else '没过：帧数不对'}", flush=True)


if __name__ == "__main__":
    main()
