"""HKBU SCIE1007 coursework video: step 4 画面 of the phone-footage pipeline. Needs the 5080; everything heavy is on it.

Every video of the person, the WHOLE clip, same length and frame grid for all outputs:
  1. decode on the card (NVDEC), upright, constant 60 fps; frames come through a pipe one at a time as raw 10-bit
     (a 4K frame is 25 MB, the clip never sits in memory)
  2. HLG -> Rec.709 on the card with gpu_color's table (the zscale + hable look the stills were approved with,
     measured against it: under 1 level mean difference)
  3. matte on the card: RVM (keeps hair) and BiRefNet (keeps hands), fused = max(RVM, BiRefNet shrunk and softened)
  4. face: mediapipe landmarks and skin mask every FACE_EVERY frames on a small copy (the only CPU part): face
     box, eye line, top of the head, mean skin colour
  5. writes <name>_std.mp4 (the picture, untouched apart from 1-2) and <name>_mat.mp4 (the matte, white = person),
     both encoded on the card (h264_nvenc), same frame count
Kept as DATA in 4_video/index.json, applied only when a take is placed (step 5), so they can change without
re-matting: the chest-up 5:6 crop box (fitted inside the frame), skin colour for white balance between the four
people, beauty level. A contact sheet per clip (<name>_sheet.jpg: start, middle, end on the backdrop with the crop
box) is for people and for the watching model.
Input:  the originals (read only), 0_probe/probe.json, 1_ident/ident.json
Output: 4_video/<name>_std.mp4, <name>_mat.mp4, <name>_sheet.jpg, index.json, 画面验收.md
"""
import os
import subprocess
import time

import numpy as np

import common as C

FPS = 60
FACE_EVERY = 6            # frames between face measurements (10 per second)
FACE_W = 960              # width of the copy the face model sees
SHRINK_AT_1080 = 7        # px the BiRefNet core is shrunk by, at 1080p; scaled with the frame
GATE_AT_1080 = 12         # px around BiRefNet's person inside which RVM's matte counts (hair wisps yes, the shelf behind no)
# flip: share of the person's pixels (on a 1/8 grid) that are in-out-in or out-in-out over three frames, mean per frame.
# Real movement does not flip back within 1/30 s; a boiling matte edge does.
CHECK = {"frames_tol": 2, "person_min": 0.03, "person_max": 0.75, "face_found_min": 0.9, "flip_max": 0.004}


def clips(ctx):
    """One entry per video file: the name of its first asset (step 1) names the outputs."""
    ident = C.read_json(ctx.out / C.STEP_DIRS[1] / "ident.json")
    by_file = {}
    for a in ident["assets"]:
        by_file.setdefault(a["file"], []).append(a["name"])
    return [(p, by_file[p.name]) for p in ctx.videos if p.name in by_file]


def inputs(ctx):
    return [p for p, _ in clips(ctx)] + [ctx.out / C.STEP_DIRS[0] / "probe.json", ctx.out / C.STEP_DIRS[1] / "ident.json"]


def params(ctx):
    v = ctx.cfg["video"]
    return {"fps": FPS, "matte": v["matte_model"], "color": "gpu_color table of common.SDR_VF", "face_every": FACE_EVERY,
            "aspect": [v["print_aspect_w"], v["print_aspect_h"]], "check": CHECK, "gate": GATE_AT_1080, "version": 3}


class Faces:
    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks import python as mpp
        from mediapipe.tasks.python import vision
        md = C.ENV / "cache" / "mediapipe"
        self.mp = mp
        # mediapipe cannot open model paths with non-ASCII characters on Windows, so hand it the bytes
        self.fl = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=mpp.BaseOptions(model_asset_buffer=(md / "face_landmarker.task").read_bytes()), num_faces=1))
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mpp.BaseOptions(model_asset_buffer=(md / "selfie_multiclass_256x256.tflite").read_bytes()), output_category_mask=True))

    def measure(self, small_rgb, scale):
        """small_rgb: HxWx3 uint8. -> dict in full-frame px, or None when no face is found."""
        import cv2
        mpi = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(small_rgb))
        lm = self.fl.detect(mpi).face_landmarks
        if not lm:
            return None
        h, w = small_rgb.shape[:2]
        pts = np.array([(p.x * w, p.y * h) for p in lm[0]])
        cat = np.squeeze(self.seg.segment(mpi).category_mask.numpy_view())      # 1 hair, 3 face skin
        if cat.shape != (h, w):
            cat = cv2.resize(cat, (w, h), interpolation=cv2.INTER_NEAREST)
        rows = np.flatnonzero(((cat == 1) | (cat == 3)).any(axis=1))
        skin = small_rgb[cat == 3]
        s = scale
        return {"x0": pts[:, 0].min() * s, "x1": pts[:, 0].max() * s, "y0": pts[:, 1].min() * s, "y1": pts[:, 1].max() * s,
                "eye_y": (pts[33, 1] + pts[263, 1]) / 2 * s, "head_top": (rows[0] if len(rows) else pts[:, 1].min()) * s,
                "skin_bgr": skin.mean(axis=0)[::-1].tolist() if len(skin) > 50 else None}


def crop_box(faces, W, H, aw, ah):
    """Chest-up print frame from the median face: eyes a third of the way down, 10% head room; shrunk and shifted
    to stay inside the picture (a low, close camera cannot give the full chest)."""
    med = lambda k: float(np.median([f[k] for f in faces]))
    eye, top, cx = med("eye_y"), med("head_top"), (med("x0") + med("x1")) / 2
    h = (eye - top) / (1 / 3 - 0.10)
    y0 = top - 0.10 * h
    wanted = [cx - h * aw / ah / 2, y0, cx + h * aw / ah / 2, y0 + h]
    h = min(h, H - max(0.0, y0), W * ah / aw)
    w = h * aw / ah
    y0 = min(max(0.0, y0), H - h)
    x0 = min(max(0.0, cx - w / 2), W - w)
    fit = [round(x0), round(y0), round(x0 + w), round(y0 + h)]
    return fit, [round(v) for v in wanted]


def writer(path, W, H, cq, pix):
    return subprocess.Popen([C.FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", pix, "-s", f"{W}x{H}", "-r", str(FPS),
                             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", "-i", "-",
                             "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", str(cq), "-b:v", "0", "-pix_fmt", "yuv420p",
                             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                             "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)


def run(ctx, out):
    import cv2
    import torch
    import matte_models as M
    if not torch.cuda.is_available():
        raise RuntimeError("第 4 步要 5080：现在找不到显卡，先停下")
    # one process per person at a time (two people may run side by side on the 5080)
    lock = out / "running.lock"
    if lock.exists():
        pid = lock.read_text().strip()
        if pid.isdigit() and pid in subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout:
            raise RuntimeError(f"{ctx.person} 的第 4 步已经有一个进程在跑（{pid}），这一个不跑")
    lock.write_text(str(os.getpid()))
    try:
        return _run(ctx, out, cv2, torch, M)
    finally:
        lock.unlink(missing_ok=True)


def _run(ctx, out, cv2, torch, M):
    import torch.nn.functional as F
    import gpu_color as G
    cfg = ctx.cfg["video"]
    aw, ah = cfg["print_aspect_w"], cfg["print_aspect_h"]
    probe = {f["file"]: f for f in C.read_json(ctx.out / C.STEP_DIRS[0] / "probe.json")["files"]}
    C.wait_for_gpu(5000)
    lut = G.load_lut()
    rvm, bir, faces_model = M.RVM(), M.BiRefNet(), Faces()
    backdrop = torch.tensor(M.hex_bgr(cfg["backdrop"])[::-1].copy(), device="cuda").view(1, 3, 1, 1) / 255
    # RGB (0..1) -> limited-range Rec.709 Y'CbCr, the planes the encoder takes as they are
    to_y = torch.tensor([0.2126, 0.7152, 0.0722], device="cuda").view(1, 3, 1, 1)
    adir = ctx.out / C.STEP_DIRS[2] / "align"
    old = C.read_json(out / "index.json")["clips"] if (out / "index.json").exists() else []
    old = {c["name"]: c for c in old}
    index, outputs = [], []
    for src, names in clips(ctx):
        name = names[0]
        pr = probe[src.name]
        W, H = pr["video"]["display"]
        std, mat, sheet = out / f"{name}_std.mp4", out / f"{name}_mat.mp4", out / f"{name}_sheet.jpg"
        stamp = {"size": src.stat().st_size, "params": params(ctx)}
        if old.get(name, {}).get("stamp") == stamp and std.exists() and mat.exists() and sheet.exists():
            index.append(old[name])
            outputs += [std, mat, sheet]
            print(f"  {name:16} 已做过，跳过")
            continue
        t_start = time.time()
        expect = round(pr["duration"] * FPS)
        # phones that record HDR give HLG (converted with the table); phones that record plain SDR (C's: 8-bit
        # Rec.709) need no conversion, ffmpeg hands over RGB as it is
        kind = pr["video"]["transfer_kind"]
        if kind not in ("HLG", "SDR"):
            raise RuntimeError(f"{src.name} 是 {kind}，第 4 步只认 HLG 和普通色彩")
        reader = subprocess.Popen([C.FFMPEG, "-v", "error", "-hwaccel", "cuda", "-i", str(src), "-vf", f"fps={FPS}", "-an",
                                   "-f", "rawvideo", "-pix_fmt", "p010le" if kind == "HLG" else "rgb24", "-"],
                                  stdout=subprocess.PIPE, bufsize=W * H * 3)
        w_std, w_mat = writer(std, W, H, 19, "yuv420p"), writer(mat, W, H, 18, "gray")
        rvm.reset()
        k = 2 * round(SHRINK_AT_1080 * H / 1080) + 1
        gate_k = 2 * round(GATE_AT_1080 * H / 1080) + 1
        sigma = 2 * H / 1080
        gx = torch.arange(-int(3 * sigma), int(3 * sigma) + 1, device="cuda").float()
        gk = torch.exp(-gx ** 2 / (2 * sigma ** 2))
        gk = (gk / gk.sum()).view(1, 1, 1, -1)
        n, hist, flick, flips, share, faces, keep = 0, [], [], [], [], [], {}
        marks = {0: "start", expect // 2: "middle", max(0, expect - 30): "end"}
        while True:
            buf = reader.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            with torch.inference_mode():
                if kind == "HLG":
                    y, uv = G.read_p010(buf, W, H)
                    rgb = G.apply(lut, y, uv)                                          # 1x3xHxW, 0..1
                else:
                    rgb = torch.frombuffer(bytearray(buf), dtype=torch.uint8).cuda().view(H, W, 3).permute(2, 0, 1)[None].float() / 255
                a_r, a_b = rvm.alpha_t(rgb), bir.alpha_t(rgb)
                core = -F.max_pool2d(-a_b[None, None], k, 1, k // 2)                   # shrink BiRefNet's matte
                core = F.conv2d(F.conv2d(F.pad(core, (gk.shape[-1] // 2,) * 2 + (0, 0), mode="replicate"), gk),
                                gk.transpose(2, 3), padding=(gk.shape[-1] // 2, 0))
                # RVM also lets through bits of the room next to the person (a shelf behind the shoulder) and stray
                # specks; keep its matte only within GATE px of what BiRefNet calls the person
                gate = F.max_pool2d(a_b[None, None], gate_k, 1, gate_k // 2)
                gate = F.avg_pool2d(gate, gate_k, 1, gate_k // 2, count_include_pad=False)
                alpha = torch.maximum(a_r * gate[0, 0], core[0, 0])
                yp = (rgb * to_y).sum(1, keepdim=True)
                cb = F.avg_pool2d((rgb[:, 2:3] - yp) / 1.8556, 2)
                cr = F.avg_pool2d((rgb[:, 0:1] - yp) / 1.5748, 2)
                planes = [(16 + 219 * yp), (128 + 224 * cb), (128 + 224 * cr)]
                std_bytes = b"".join(p.round().clamp(0, 255).byte().cpu().numpy().tobytes() for p in planes)
                mat_bytes = (alpha * 255).round().byte().cpu().numpy().tobytes()
                small = alpha[::8, ::8] > 0.5
                hist.append(small)
                if len(hist) == 3:
                    a0, a1, a2 = hist
                    flips.append(float(((a0 == a2) & (a0 != a1)).sum() / a1.sum().clamp(min=1)))
                    hist.pop(0)
                if len(hist) >= 2:
                    flick.append(float((hist[-1] != hist[-2]).float().mean()))
                share.append(float(small.float().mean()))
                if n % FACE_EVERY == 0:
                    sm = F.interpolate(rgb, (round(FACE_W * H / W), FACE_W), mode="area")
                    face_in = (sm[0].permute(1, 2, 0) * 255).round().byte().cpu().numpy()
                if n in marks:
                    comp = rgb * alpha + backdrop * (1 - alpha)
                    keep[marks[n]] = (F.interpolate(comp, (round(640 * H / W), 640), mode="area")[0].permute(1, 2, 0) * 255).round().byte().cpu().numpy()[:, :, ::-1]
            w_std.stdin.write(std_bytes)
            w_mat.stdin.write(mat_bytes)
            if n % FACE_EVERY == 0:
                m = faces_model.measure(face_in, W / FACE_W)
                if m:
                    faces.append(m | {"t": n / FPS})
            n += 1
        reader.wait()
        for w in (w_std, w_mat):
            w.stdin.close()
            w.wait()
        measured = (n + FACE_EVERY - 1) // FACE_EVERY
        # the crop follows the face while the line is spoken (step 2's cut), not while a hand reaches for the phone
        spans = [(t["in"], t["out"]) for t in map(lambda nm: C.read_json(adir / f"{nm}.json") if (adir / f"{nm}.json").exists() else None, names) if t]
        spoken = [f for f in faces if any(a <= f["t"] <= b for a, b in spans)] if spans else []
        crop, wanted = crop_box(spoken or faces, W, H, aw, ah) if faces else (None, None)
        skins = [m["skin_bgr"] for m in faces if m["skin_bgr"]]
        skin = np.median(np.array(skins), axis=0) if skins else None
        lab = cv2.cvtColor(np.uint8([[skin]]), cv2.COLOR_BGR2LAB)[0, 0].astype(int).tolist() if skin is not None else None
        tiles = []
        for key in ("start", "middle", "end"):
            if key in keep:
                im = np.ascontiguousarray(keep[key])
                if crop:
                    s = 640 / W
                    cv2.rectangle(im, (round(crop[0] * s), round(crop[1] * s)), (round(crop[2] * s), round(crop[3] * s)), (255, 200, 0), 2)
                tiles.append(im)
        if tiles:
            C.imwrite(sheet, np.hstack(tiles))
        c = {"name": name, "assets": names, "file": src.name, "std": std.name, "mat": mat.name, "sheet": sheet.name, "size": [W, H], "fps": FPS,
             "frames": n, "frames_expected": expect, "person_share": [round(min(share), 3), round(float(np.mean(share)), 3), round(max(share), 3)],
             "edge_change": round(float(np.mean(flick)), 4), "flip": round(float(np.mean(flips)), 5), "flip_max_frame": round(float(np.max(flips)), 4),
             "face_found": round(len(faces) / max(1, measured), 3),
             # while the line is spoken; a member may turn away before or after it (the face model misses profiles)
             "face_found_spoken": round(len(spoken) / max(1, sum(1 for i in range(0, n, FACE_EVERY) if any(a <= i / FPS <= b for a, b in spans))), 3) if spans else None,
             "crop": crop, "crop_wanted": wanted, "crop_cut_px": max(0, wanted[3] - H) if wanted else None,
             "skin_bgr": [round(float(v), 1) for v in skin] if skin is not None else None, "skin_lab": lab,
             "seconds": round(time.time() - t_start, 1), "ms_per_frame": round((time.time() - t_start) * 1000 / max(1, n)), "source_color": kind, "stamp": stamp}
        fails = []
        if abs(n - expect) > CHECK["frames_tol"]:
            fails.append(f"帧数 {n}，应有 {expect}")
        if min(share) < CHECK["person_min"]:
            fails.append(f"有帧抠出来的人只占 {min(share):.1%}")
        if max(share) > CHECK["person_max"]:
            fails.append(f"有帧抠出来的占 {max(share):.0%}，可能把背景也抠进来了")
        found = c["face_found"] if c["face_found_spoken"] is None else c["face_found_spoken"]
        if found < CHECK["face_found_min"] and "_ext_" not in name:      # clips outside the script may hide the face (drinking)
            fails.append(f"说话那一段只有 {found:.0%} 的帧找到脸")
        if c["flip"] > CHECK["flip_max"]:
            fails.append(f"蒙版边缘来回跳 {c['flip']:.2%}")
        c["fails"] = fails
        index.append(c)
        outputs += [std, mat, sheet]
        C.write_json(out / "index.json", {"person": ctx.person, "clips": index})
        print(f"  {name:16} {n} 帧 {c['seconds']:.0f} 秒（每帧 {c['ms_per_frame']} 毫秒） 人占 {c['person_share'][1]:.0%} 来回跳 {c['flip']:.3%} "
              f"脸 {found:.0%}  {'过' if not fails else '没过：' + '；'.join(fails)}", flush=True)

    C.write_json(out / "index.json", {"person": ctx.person, "made": time.strftime("%Y-%m-%d %H:%M") + " 韩国时间", "clips": index})
    ok = sum(1 for c in index if not c["fails"])
    L = [f"# {ctx.person} 的画面验收（第 4 步）", "",
         f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间。{len(index)} 条，过 {ok} 条。",
         "处理（解码、转色、抠像、编码都在显卡上）：整条原片 → HDR 转普通色彩、摆正、恒定 60 帧 → 两个抠像模型融合出蒙版。裁框、肤色只量出来记成数据，上片时才用。", "",
         f"标准：帧数和原片时长对得上（差 ≤ {CHECK['frames_tol']} 帧）；每一帧抠出的人占画面 {CHECK['person_min']:.0%}–{CHECK['person_max']:.0%}；"
         f"{CHECK['face_found_min']:.0%} 以上的帧找到脸；蒙版边缘来回跳（连着三帧里进-出-进的像素，占人的面积）平均 ≤ {CHECK['flip_max']:.1%}。"
         "每条的三格图 `<名字>_sheet.jpg`（开头、中间、结尾，蓝框是胸口以上的裁框）要人或看片的模型看一眼。", "",
         "| 新名字 | 尺寸 | 帧数 / 应有 | 人占画面 最小 / 平均 / 最大 | 边缘来回跳 平均（最坏一帧） | 找到脸 | 裁框（底边被画面截掉 px） | 肤色 Lab | 用时 秒（每帧毫秒） | 结果 |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for c in index:
        ps = c["person_share"]
        L.append(f"| {c['name']} | {c['size'][0]}×{c['size'][1]} | {c['frames']} / {c['frames_expected']} | {ps[0]:.0%} / {ps[1]:.0%} / {ps[2]:.0%} | "
                 f"{c['flip']:.3%}（{c['flip_max_frame']:.2%}） | {c['face_found']:.0%} | {c['crop']}（{c['crop_cut_px']}） | {c['skin_lab']} | "
                 f"{c['seconds']:.0f}（{c['ms_per_frame']}） | {'过' if not c['fails'] else '；'.join(c['fails'])} |")
    C.write_text(out / "画面验收.md", "\n".join(L) + "\n")
    return outputs + [out / "index.json", out / "画面验收.md"]
