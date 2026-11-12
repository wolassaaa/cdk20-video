"""HKBU SCIE1007 coursework video: step 4 画面 of the phone-footage pipeline. Needs the 5080 (matting).

Every video of the person, the WHOLE clip, same length and frame grid for all outputs:
  1. ffmpeg: HLG -> Rec.709 (zscale + hable, the look step 0's stills were approved with), upright, constant 60 fps,
     full size; frames come through a pipe one at a time (a 4K frame is 25 MB, the clip never sits in memory)
  2. matte: RVM (keeps hair) and BiRefNet (keeps hands) on the GPU, fused = max(RVM, BiRefNet shrunk)
  3. face: mediapipe landmarks and skin mask every FACE_EVERY frames on a small copy (CPU): face box, eye line,
     top of the head, mean skin colour and brightness
  4. writes <name>_std.mp4 (the picture, untouched apart from 1) and <name>_mat.mp4 (the matte, white = person),
     both h264_nvenc, same frame count
Kept as DATA in 4_video/index.json, applied only when a take is placed (step 5), so they can change without
re-matting: the chest-up 5:6 crop box (fitted inside the frame), skin colour for white balance between the four
people, beauty level. A contact sheet per clip (<name>_sheet.jpg: start, middle, end on the backdrop with the crop
box) is for people and for the watching model.
Input:  the originals (read only), 0_probe/probe.json, 1_ident/ident.json
Output: 4_video/<name>_std.mp4, <name>_mat.mp4, <name>_sheet.jpg, index.json, 画面验收.md
"""
import subprocess
import time

import numpy as np

import common as C

FPS = 60
FACE_EVERY = 6            # frames between face measurements (10 per second)
FACE_W = 960              # width of the copy the face model sees
SHRINK_AT_1080 = 7        # px the BiRefNet core is shrunk by, at 1080p; scaled with the frame
CHECK = {"frames_tol": 2, "person_min": 0.03, "person_max": 0.75, "face_found_min": 0.9, "flicker_max": 0.6}
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=bgr24")


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
    return {"fps": FPS, "matte": v["matte_model"], "tonemap": TONEMAP, "face_every": FACE_EVERY, "aspect": [v["print_aspect_w"], v["print_aspect_h"]],
            "check": CHECK, "version": 1}


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

    def measure(self, small_bgr, scale):
        """-> dict in full-frame px, or None when no face is found."""
        import cv2
        mpi = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB))
        lm = self.fl.detect(mpi).face_landmarks
        if not lm:
            return None
        h, w = small_bgr.shape[:2]
        pts = np.array([(p.x * w, p.y * h) for p in lm[0]])
        cat = np.squeeze(self.seg.segment(mpi).category_mask.numpy_view())      # 1 hair, 3 face skin
        if cat.shape != (h, w):
            cat = cv2.resize(cat, (w, h), interpolation=cv2.INTER_NEAREST)
        rows = np.flatnonzero(((cat == 1) | (cat == 3)).any(axis=1))
        skin = small_bgr[cat == 3]
        s = scale
        return {"x0": pts[:, 0].min() * s, "x1": pts[:, 0].max() * s, "y0": pts[:, 1].min() * s, "y1": pts[:, 1].max() * s,
                "eye_y": (pts[33, 1] + pts[263, 1]) / 2 * s, "head_top": (rows[0] if len(rows) else pts[:, 1].min()) * s,
                "skin_bgr": skin.mean(axis=0).tolist() if len(skin) > 50 else None}


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


def writer(path, W, H, cq):
    return subprocess.Popen([C.FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", str(cq), "-b:v", "0", "-pix_fmt", "yuv420p",
                             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", str(path)],
                            stdin=subprocess.PIPE)


def run(ctx, out):
    import cv2
    import torch
    import matte_models as M
    if not torch.cuda.is_available():
        raise RuntimeError("第 4 步要 5080：现在找不到显卡，先停下")
    cv2.setNumThreads(C.CPU_THREADS)
    cfg = ctx.cfg["video"]
    aw, ah = cfg["print_aspect_w"], cfg["print_aspect_h"]
    probe = {f["file"]: f for f in C.read_json(ctx.out / C.STEP_DIRS[0] / "probe.json")["files"]}
    C.wait_for_gpu(6000)
    rvm, bir, faces_model = M.RVM(), M.BiRefNet(), Faces()
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
        reader = subprocess.Popen([C.FFMPEG, "-v", "error", "-i", str(src), "-vf", f"{TONEMAP},fps={FPS}", "-threads", str(C.CPU_THREADS),
                                   "-filter_threads", str(C.CPU_THREADS), "-an", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                                  stdout=subprocess.PIPE, bufsize=W * H * 3)
        w_std, w_mat = writer(std, W, H, 19), writer(mat, W, H, 18)
        rvm.reset()
        k = 2 * round(SHRINK_AT_1080 * H / 1080) + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        n, prev, flick, share, faces, keep = 0, None, [], [], [], {}
        marks = {0: "start", expect // 2: "middle", max(0, expect - 30): "end"}
        while True:
            buf = reader.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            f = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            a_r, a_b = rvm.frame(f), bir.frame(f)
            alpha = np.maximum(a_r, cv2.GaussianBlur(cv2.erode(a_b, kernel), (0, 0), 2 * H / 1080))
            w_std.stdin.write(buf)
            w_mat.stdin.write(cv2.cvtColor(alpha, cv2.COLOR_GRAY2BGR).tobytes())
            small = alpha[::8, ::8].astype(np.int16)
            if prev is not None:
                flick.append(float(np.abs(small - prev).mean()))
            prev = small
            share.append(float((small > 128).mean()))
            if n % FACE_EVERY == 0:
                m = faces_model.measure(cv2.resize(f, (FACE_W, round(FACE_W * H / W)), interpolation=cv2.INTER_AREA), W / FACE_W)
                if m:
                    faces.append(m)
            if n in marks:
                keep[marks[n]] = M.composite(f, alpha, cfg["backdrop"])
            n += 1
        reader.wait()
        for w in (w_std, w_mat):
            w.stdin.close()
            w.wait()
        measured = (n + FACE_EVERY - 1) // FACE_EVERY
        crop, wanted = crop_box(faces, W, H, aw, ah) if faces else (None, None)
        skins = [m["skin_bgr"] for m in faces if m["skin_bgr"]]
        skin = np.median(np.array(skins), axis=0) if skins else None
        lab = cv2.cvtColor(np.uint8([[skin]]), cv2.COLOR_BGR2LAB)[0, 0].astype(int).tolist() if skin is not None else None
        tiles = []
        for key in ("start", "middle", "end"):
            if key in keep:
                im = keep[key].copy()
                if crop:
                    cv2.rectangle(im, (crop[0], crop[1]), (crop[2], crop[3]), (255, 200, 0), max(2, H // 360))
                tiles.append(cv2.resize(im, (640, round(640 * H / W)), interpolation=cv2.INTER_AREA))
        if tiles:
            C.imwrite(sheet, np.hstack(tiles))
        c = {"name": name, "assets": names, "file": src.name, "std": std.name, "mat": mat.name, "sheet": sheet.name, "size": [W, H], "fps": FPS,
             "frames": n, "frames_expected": expect, "person_share": [round(min(share), 3), round(float(np.mean(share)), 3), round(max(share), 3)],
             "flicker": round(float(np.mean(flick)), 3), "face_found": round(len(faces) / max(1, measured), 3),
             "crop": crop, "crop_wanted": wanted, "crop_cut_px": max(0, wanted[3] - H) if wanted else None,
             "skin_bgr": [round(float(v), 1) for v in skin] if skin is not None else None, "skin_lab": lab,
             "seconds": round(time.time() - t_start, 1), "ms_per_frame": round((time.time() - t_start) * 1000 / max(1, n)), "stamp": stamp}
        fails = []
        if abs(n - expect) > CHECK["frames_tol"]:
            fails.append(f"帧数 {n}，应有 {expect}")
        if min(share) < CHECK["person_min"]:
            fails.append(f"有帧抠出来的人只占 {min(share):.1%}")
        if max(share) > CHECK["person_max"]:
            fails.append(f"有帧抠出来的占 {max(share):.0%}，可能把背景也抠进来了")
        if c["face_found"] < CHECK["face_found_min"]:
            fails.append(f"只有 {c['face_found']:.0%} 的帧找到脸")
        if c["flicker"] > CHECK["flicker_max"]:
            fails.append(f"蒙版闪 {c['flicker']}")
        c["fails"] = fails
        index.append(c)
        outputs += [std, mat, sheet]
        C.write_json(out / "index.json", {"person": ctx.person, "clips": index})
        print(f"  {name:16} {n} 帧 {c['seconds']:.0f} 秒（每帧 {c['ms_per_frame']} 毫秒） 人占 {c['person_share'][1]:.0%} 闪 {c['flicker']} "
              f"脸 {c['face_found']:.0%}  {'过' if not fails else '没过：' + '；'.join(fails)}", flush=True)

    C.write_json(out / "index.json", {"person": ctx.person, "made": time.strftime("%Y-%m-%d %H:%M") + " 韩国时间", "clips": index})
    ok = sum(1 for c in index if not c["fails"])
    L = [f"# {ctx.person} 的画面验收（第 4 步）", "",
         f"HKBU SCIE1007 课程作业的科普视频。{time.strftime('%Y-%m-%d %H:%M')} 韩国时间。{len(index)} 条，过 {ok} 条。",
         "处理：整条原片 → HDR 转普通色彩、摆正、恒定 60 帧 → 两个抠像模型融合出蒙版。裁框、肤色只量出来记成数据，上片时才用。", "",
         f"标准：帧数和原片时长对得上（差 ≤ {CHECK['frames_tol']} 帧）；每一帧抠出的人占画面 {CHECK['person_min']:.0%}–{CHECK['person_max']:.0%}；"
         f"{CHECK['face_found_min']:.0%} 以上的帧找到脸；蒙版相邻帧的平均变化 ≤ {CHECK['flicker_max']}。每条的三格图 `<名字>_sheet.jpg`（开头、中间、结尾，蓝框是胸口以上的裁框）要人或看片的模型看一眼。", "",
         "| 新名字 | 尺寸 | 帧数 / 应有 | 人占画面 最小 / 平均 / 最大 | 蒙版闪 | 找到脸 | 裁框（底边被画面截掉 px） | 肤色 Lab | 用时 秒 | 结果 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for c in index:
        ps = c["person_share"]
        L.append(f"| {c['name']} | {c['size'][0]}×{c['size'][1]} | {c['frames']} / {c['frames_expected']} | {ps[0]:.0%} / {ps[1]:.0%} / {ps[2]:.0%} | {c['flicker']} | "
                 f"{c['face_found']:.0%} | {c['crop']}（{c['crop_cut_px']}） | {c['skin_lab']} | {c['seconds']:.0f} | {'过' if not c['fails'] else '；'.join(c['fails'])} |")
    C.write_text(out / "画面验收.md", "\n".join(L) + "\n")
    return outputs + [out / "index.json", out / "画面验收.md"]
