"""HKBU SCIE1007 coursework video: step 5 上片 of the phone-footage pipeline: every chosen take, cut and finished.

For each line step 2 picked (2_pick/picks.json):
  on-camera takes  the frames between the cut's in and out, from step 4's whole-clip picture (the restored one
                   when restore.py made it) and matte, cropped to the chest-up box and scaled to the print size:
                     1. colour: gains that move this member's skin part of the way to the reference member's
                        (config video.match: reference, strength); applied in linear light, the same for every
                        frame of every take of that member, so nothing pumps
                     2. beauty, on skin only (face and neck from the segmenter): mid-size unevenness (blotches,
                        spots) is turned down, fine texture and the shape of the face stay; skin colour is evened
                        a little; level off | light | medium (config video.beauty)
                     3. sharpening for members listed in config video.sharpen
                   writes <name>_fg.mp4 (the person), <name>_a.mp4 (the matte) and <name>_print.mp4 (on the flat
                   backdrop, with the cut sound), so a moving background can replace the flat one later
  every take       the cut of step 3's sound as <name>.wav
  5_place/place.json lists them with the script line and its word times counted from the cut's in (for subtitles
  and for the film's timeline); 上片对比.jpg shows one frame per member before and after.
Input:  2_pick/picks.json and align/, 3_audio/, 4_video/ (index.json, pictures, mattes)
Output: 5_place/<name>_fg.mp4, _a.mp4, _print.mp4, <name>.wav, place.json, 上片对比.jpg, 上片验收.md
"""
import subprocess
import time

import numpy as np

import common as C

FPS = 60
OUT_W, OUT_H = 1560, 1872             # 5:6, 1.5x the print's size in the 4K film (1040 x 1248): room for a slow push-in
BEAUTY = {"off": 0.0, "light": 0.45, "medium": 0.7}       # how much of the mid-size skin unevenness is taken out
BAND = (1.5, 9.0)                     # px at output size: detail between these two blur widths is "mid-size"
GAIN_LIMIT = (0.75, 1.45)             # per-channel gain in linear light
ALPHA_CURVE = (0.15, 0.85)            # matte below / above these counts as clear / solid (picked on A's hair over a black TV, 11-13)
DEFG_R = (60, 4)                      # px at output size: the two passes of the foreground estimate


def inputs(ctx):
    d = ctx.out
    return [d / C.STEP_DIRS[2] / "picks.json", d / C.STEP_DIRS[4] / "index.json", d / C.STEP_DIRS[3] / "results.json"]


def params(ctx):
    v = ctx.cfg["video"]
    return {"size": [OUT_W, OUT_H], "beauty": v["beauty"], "match": v.get("match"), "grade": v.get("grade"), "sharpen": v.get("sharpen"), "backdrop": v["backdrop"],
            "band": BAND, "unmix": DEFG_R, "alpha_curve": ALPHA_CURVE, "version": 2}


def skin_reference(cfg):
    """Median skin colour (B, G, R, 0-255) of every member who has step 4 results; kept in 素材流程_out/match.json so
    all members are matched against the same numbers whoever runs first."""
    out = {}
    for P in "ABCD":
        idx = C.OUT / P / C.STEP_DIRS[4] / "index.json"
        if idx.exists():
            s = [c["skin_bgr"] for c in C.read_json(idx)["clips"] if c.get("skin_bgr") and "_cam_" in c["name"]]
            if s:
                out[P] = np.median(np.array(s), axis=0).round(1).tolist()
    C.write_json(C.OUT / "match.json", {"skin_bgr": out, "reference": cfg["video"]["match"]["reference"]})
    return out


def gains(person, skins, m):
    """Per-channel gain in linear light: this member's skin moves `strength` of the way to the reference member's."""
    ref, mine = np.array(skins[m["reference"]]), np.array(skins[person])
    target = mine + m["strength"] * (ref - mine)
    g = (target / mine) ** 2.2
    return np.clip(g, *GAIN_LIMIT)[::-1].copy()            # R, G, B


def blur(x, sigma, F, torch):
    r = int(3 * sigma)
    k = torch.exp(-torch.arange(-r, r + 1, device=x.device).float() ** 2 / (2 * sigma ** 2))
    k = (k / k.sum()).view(1, 1, 1, -1).repeat(x.shape[1], 1, 1, 1)
    x = F.conv2d(F.pad(x, (r, r, 0, 0), mode="replicate"), k, groups=x.shape[1])
    return F.conv2d(F.pad(x, (0, 0, r, r), mode="replicate"), k.transpose(2, 3), groups=x.shape[1])


def box(x, r, F):
    """Mean over a (2r+1) square, edges replicated; cost does not grow with r."""
    x = F.pad(x, (r + 1, r, r + 1, r), mode="replicate")
    c = x.cumsum(-1)
    x = c[..., 2 * r + 1:] - c[..., :-(2 * r + 1)]
    c = x.cumsum(-2)
    return (c[..., 2 * r + 1:, :] - c[..., :-(2 * r + 1), :]) / (2 * r + 1) ** 2


def unmix(img, a, F):
    """Colour of the person where the matte is part-way (hair strands): the old background showing through
    (A's black TV, 11-13) would otherwise come along as a dark rim. Blur-fusion foreground estimate
    (Forte & Pitie 2021), a wide pass then a narrow one."""
    fg, bg = img, img
    for r in DEFG_R:
        ba, bb = box(a, r, F), box(1 - a, r, F)
        bf = box(fg * a, r, F) / (ba + 1e-5)
        bbk = box(bg * (1 - a), r, F) / (bb + 1e-5)
        fg = (bf + a * (img - a * bf - (1 - a) * bbk)).clamp(0, 1)
        bg = bbk
    solid = (a > 0.98).float()                         # inside the person the picture stays as it was
    return solid * img + (1 - solid) * fg


def reader(path, t0, dur, crop, pix):
    x0, y0, x1, y1 = crop
    return subprocess.Popen([C.FFMPEG, "-v", "error", "-ss", f"{t0:.4f}", "-i", str(path), "-t", f"{dur:.4f}",
                             "-vf", f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0},scale={OUT_W}:{OUT_H}:flags=lanczos", "-an",
                             "-f", "rawvideo", "-pix_fmt", pix, "-"], stdout=subprocess.PIPE, bufsize=OUT_W * OUT_H * 3)


def writer(path, pix, audio=None):
    cmd = [C.FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", pix, "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-i", str(audio)]
    cmd += ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "17", "-b:v", "0", "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    return subprocess.Popen(cmd + ["-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)


def run(ctx, out):
    import cv2
    import torch
    import torch.nn.functional as F
    import matte_models as M
    from steps.s4_video import Faces
    if not torch.cuda.is_available():
        raise RuntimeError("第 5 步要 5080：现在找不到显卡，先停下")
    cfg = ctx.cfg["video"]
    P = ctx.person
    picks = C.read_json(ctx.out / C.STEP_DIRS[2] / "picks.json")["picks"]
    adir = ctx.out / C.STEP_DIRS[2] / "align"
    vdir, sdir = ctx.out / C.STEP_DIRS[4], ctx.out / C.STEP_DIRS[3]
    clips = {}
    if (vdir / "index.json").exists():
        for c in C.read_json(vdir / "index.json")["clips"]:
            for a in c["assets"]:
                clips[a] = c
    skins = skin_reference(ctx.cfg)
    grade = (cfg.get("grade") or {}).get(P)              # the neutral grade (G6, checked by grade.py) replaces the skin match when set
    g = torch.tensor(grade["gain"] if grade else gains(P, skins, cfg["match"]) if P in skins else [1.0, 1.0, 1.0], device="cuda").float().view(1, 3, 1, 1)
    sat = float(grade.get("sat", 1.0)) if grade else 1.0
    k_beauty = BEAUTY[cfg["beauty"]["level"]]
    sharpen = float((cfg.get("sharpen") or {}).get(P, 0.0))
    backdrop = torch.tensor(M.hex_bgr(cfg["backdrop"])[::-1].copy(), device="cuda").view(1, 3, 1, 1) / 255
    seg = Faces()
    items, outputs, before_after = [], [], None
    for pk in picks:
        name = pk["pick"]
        t = C.read_json(adir / f"{name}.json")
        t_in, t_out = pk["in"], pk["out"]
        dur = round(t_out - t_in, 4)
        wav = out / f"{name}.wav"
        C.ffmpeg("-i", sdir / f"{name}_aud.wav", "-ss", f"{t_in:.4f}", "-t", f"{dur:.4f}", "-c:a", "pcm_s24le", wav)
        item = {"name": name, "beat": pk["beat"], "class": t["class"], "seconds": dur, "wav": wav.name, "script": t["script"],
                "words": [{"w": w["w"], "t0": round(w["t0"] - t_in, 3), "t1": round(w["t1"] - t_in, 3)} for w in t["words"]]}
        outputs.append(wav)
        c = clips.get(name)
        if t["class"] == "cam" and c and c.get("crop"):
            t_start = time.time()
            src = vdir / (c.get("std_restored") or c["std"])
            fg, al, pr = out / f"{name}_fg.mp4", out / f"{name}_a.mp4", out / f"{name}_print.mp4"
            r_std, r_mat = reader(src, t_in, dur, c["crop"], "rgb24"), reader(vdir / c["mat"], t_in, dur, c["crop"], "gray")
            w_fg, w_al, w_pr = writer(fg, "rgb24"), writer(al, "gray"), writer(pr, "rgb24", wav)
            n = 0
            want = round(dur * FPS)
            while True:
                b1, b2 = r_std.stdout.read(OUT_W * OUT_H * 3), r_mat.stdout.read(OUT_W * OUT_H)
                if len(b1) < OUT_W * OUT_H * 3 or len(b2) < OUT_W * OUT_H:
                    break
                with torch.inference_mode():
                    x0 = torch.frombuffer(bytearray(b1), dtype=torch.uint8).cuda().view(OUT_H, OUT_W, 3).permute(2, 0, 1)[None].float() / 255
                    a = torch.frombuffer(bytearray(b2), dtype=torch.uint8).cuda().view(1, 1, OUT_H, OUT_W).float() / 255
                    a = ((a - ALPHA_CURVE[0]) / (ALPHA_CURVE[1] - ALPHA_CURVE[0])).clamp(0, 1)      # soft grey band over dark backgrounds gone, strands kept
                    x = (x0.clamp(min=1e-4) ** 2.2 * g).clamp(0, 1) ** (1 / 2.2)                    # colour match, linear light
                    if sat != 1.0:
                        y = (x * torch.tensor([0.2126, 0.7152, 0.0722], device="cuda").view(1, 3, 1, 1)).sum(1, keepdim=True)
                        x = (y + sat * (x - y)).clamp(0, 1)
                    if k_beauty:
                        small = (F.interpolate(x, (OUT_H // 4, OUT_W // 4), mode="area")[0].permute(1, 2, 0) * 255).round().byte().cpu().numpy()
                        mpi = seg.mp.Image(image_format=seg.mp.ImageFormat.SRGB, data=np.ascontiguousarray(small))
                        cat = torch.from_numpy(np.squeeze(seg.seg.segment(mpi).category_mask.numpy_view()).copy()).cuda()
                        skin = ((cat == 3) | (cat == 2)).float()[None, None]                        # face skin, body skin (neck, hands)
                        skin = blur(F.interpolate(skin, (OUT_H, OUT_W), mode="bilinear"), 6.0, F, torch) * a
                        lo1, lo2 = blur(x, BAND[0], F, torch), blur(x, BAND[1], F, torch)
                        yv = x - k_beauty * skin * (lo1 - lo2)                                      # mid-size unevenness down
                        luma = (yv * torch.tensor([0.2126, 0.7152, 0.0722], device="cuda").view(1, 3, 1, 1)).sum(1, keepdim=True)
                        chroma = yv - luma
                        x = (luma + chroma + 0.5 * k_beauty * skin * (blur(chroma, BAND[1], F, torch) - chroma)).clamp(0, 1)   # skin colour evened
                    if sharpen:
                        x = (x + sharpen * (x - blur(x, 1.2, F, torch))).clamp(0, 1)
                    x = unmix(x, a, F)
                    comp = x * a + backdrop * (1 - a)
                    to8 = lambda v: (v[0].permute(1, 2, 0) * 255).round().byte().cpu().numpy().tobytes()
                    d_fg, d_pr, d_al = to8(x), to8(comp), (a[0, 0] * 255).round().byte().cpu().numpy().tobytes()
                    if n == want // 2 and P not in (before_after or {}):
                        before_after = {P: np.hstack([np.frombuffer(to8(x0 * a + backdrop * (1 - a)), np.uint8).reshape(OUT_H, OUT_W, 3),
                                                      np.frombuffer(d_pr, np.uint8).reshape(OUT_H, OUT_W, 3)])[:, :, ::-1]}
                w_fg.stdin.write(d_fg)
                w_al.stdin.write(d_al)
                w_pr.stdin.write(d_pr)
                n += 1
            for p in (r_std, r_mat):
                p.stdout.close()
                p.wait()
            for w in (w_fg, w_al, w_pr):
                w.stdin.close()
                w.wait()
            item |= {"fg": fg.name, "alpha": al.name, "print": pr.name, "frames": n, "frames_expected": want, "size": [OUT_W, OUT_H],
                     "source": src.name, "crop": c["crop"], "process_seconds": round(time.time() - t_start, 1)}
            item["fails"] = [f"帧数 {n}，应有 {want}"] if abs(n - want) > 1 else []
            outputs += [fg, al, pr]
            print(f"  {name:16} {n} 帧 {time.time() - t_start:.0f} 秒  {'过' if not item['fails'] else '没过：' + item['fails'][0]}", flush=True)
        else:
            item["fails"] = [] if t["class"] == "vo" else ["没有第 4 步的画面"]
        items.append(item)
    info = {"person": P, "made": time.strftime("%Y-%m-%d %H:%M") + " 韩国时间", "gains_rgb": [round(float(v), 3) for v in g.flatten()],
            "beauty": cfg["beauty"]["level"], "sharpen": sharpen, "restored": bool(cfg.get("restore", {}).get(P)), "items": items}
    C.write_json(out / "place.json", info)
    if before_after:
        C.imwrite(out / "上片对比.jpg", cv2.resize(before_after[P], (OUT_W, OUT_H // 2), interpolation=cv2.INTER_AREA), 93)
        outputs.append(out / "上片对比.jpg")
    cams = [i for i in items if i["class"] == "cam"]
    L = [f"# {P} 的上片验收（第 5 步）", "",
         f"HKBU SCIE1007 课程作业的科普视频。{info['made']}。出镜 {len(cams)} 段、画外音 {len(items) - len(cams)} 段。",
         (f"色彩：中正调色（config.json video.grade），红绿蓝增益 {info['gains_rgb']}，饱和度 {sat}；" if grade else f"色彩：向标杆 {cfg['match']['reference']} 靠 {cfg['match']['strength']:.0%}，红绿蓝增益 {info['gains_rgb']}；") + f"美颜 {info['beauty']}；锐化 {sharpen}；"
         f"{'画面用的是修复后的' if info['restored'] else '画面没做修复'}。底色是占位的米色，细胞背景渲好后换上。`上片对比.jpg` 左边处理前、右边处理后。", "",
         "| 名字 | 段号 | 类 | 时长 秒 | 帧数 / 应有 | 结果 |", "|---|---|---|---|---|---|"]
    for i in items:
        L.append(f"| {i['name']} | {i['beat']} | {i['class']} | {i['seconds']:.2f} | {i.get('frames', '—')} / {i.get('frames_expected', '—')} | {'过' if not i['fails'] else '；'.join(i['fails'])} |")
    C.write_text(out / "上片验收.md", "\n".join(L) + "\n")
    return outputs + [out / "place.json", out / "上片验收.md"]
