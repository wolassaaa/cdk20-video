"""HKBU SCIE1007 课程作业的科普视频：出镜素材的人体关键点跟踪测试（只用 CPU）。

用法（系统 Python 3.11，依赖装在 G:/cdk20/work/track/pydeps）：
  PYTHONPATH=G:/cdk20/work/track/pydeps py -3.11 track_pose.py clip [A_cam_1-01_t1]   # 逐帧跟踪一条（默认 2-02，带检查视频），写 <段>_landmarks.json
  PYTHONPATH=G:/cdk20/work/track/pydeps python track_pose.py census # 全部出镜段，每 5 帧抽 1 帧
输入：素材流程_out/A/5_place/A_cam_2-02_t1_fg.mp4（人在黑底上）；原片只读，不写。
"""
import json, math, os, subprocess, sys, time
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

ROOT = "D:/。hkbu/molecular science"
OUT = "G:/cdk20/work/track"
PLACE = f"{ROOT}/素材流程_out"
FFMPEG = f"{ROOT}/_env/ffmpeg/ffmpeg.exe"
DET_W = 1280  # 检测时缩到这个宽度，坐标再换回原分辨率

# Pose 索引
PJ = {"nose": 0, "eye_l": 2, "eye_r": 5, "shoulder_l": 11, "shoulder_r": 12,
      "elbow_l": 13, "elbow_r": 14, "wrist_l": 15, "wrist_r": 16}
PALM_IDS = [0, 5, 9, 13, 17]


def make_pose():
    return vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=f"{OUT}/pose_landmarker_full.task"),
        running_mode=vision.RunningMode.VIDEO, num_poses=1,
        min_pose_detection_confidence=0.4, min_tracking_confidence=0.4))


def make_hands():
    return vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=f"{OUT}/hand_landmarker.task"),
        running_mode=vision.RunningMode.VIDEO, num_hands=2,
        min_hand_detection_confidence=0.3, min_tracking_confidence=0.3))


def detect(pose, hands, bgr, t_ms, W, H):
    """返回 {点名: (x, y, 置信度)}，像素坐标（原分辨率）。找不到的点为 None。"""
    s = DET_W / bgr.shape[1]
    small = cv2.resize(bgr, (DET_W, int(round(bgr.shape[0] * s))), interpolation=cv2.INTER_AREA)
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
    res = {k: None for k in PJ}
    res["palm_l"] = res["palm_r"] = None
    pr = pose.detect_for_video(img, t_ms)
    if pr.pose_landmarks:
        lm = pr.pose_landmarks[0]
        for k, i in PJ.items():
            p = lm[i]
            conf = min(p.visibility, p.presence)
            res[k] = (p.x * W, p.y * H, float(conf))
    hr = hands.detect_for_video(img, t_ms)
    # 手按离姿态手腕最近分配左右（不信 MediaPipe 的镜像标签）
    for h, hl in enumerate(hr.hand_landmarks or []):
        pts = np.array([[hl[i].x * W, hl[i].y * H] for i in PALM_IDS])
        c = pts.mean(0)
        sc = hr.handedness[h][0].score
        best, bd = None, 1e9
        for side in ("l", "r"):
            w = res.get("wrist_" + side)
            d = math.hypot(c[0] - w[0], c[1] - w[1]) if w else (0.5 * W if res["palm_" + side] is None else 1e9)
            if d < bd and (res["palm_" + side] is None or d < 1e8):
                best, bd = side, d
        if best and res["palm_" + best] is None:
            res["palm_" + best] = (float(c[0]), float(c[1]), float(sc))
    return res


class OneEuro:
    def __init__(self, fps, mincut=1.0, beta=0.02, dcut=1.0):
        self.dt = 1.0 / fps; self.mc = mincut; self.b = beta; self.dc = dcut
        self.x = None; self.dx = 0.0

    @staticmethod
    def a(dt, cut):
        r = 2 * math.pi * cut * dt
        return r / (r + 1)

    def __call__(self, v):
        if self.x is None:
            self.x = v; return v
        d = (v - self.x) / self.dt
        self.dx += self.a(self.dt, self.dc) * (d - self.dx)
        cut = self.mc + self.b * abs(self.dx)
        self.x += self.a(self.dt, cut) * (v - self.x)
        return self.x


def smooth_track(raw, fps, minconf):
    """raw: 每帧 (x,y,c) 或 None。置信度低或缺失的帧先线性补洞（补洞最长 0.5 秒），再 One-Euro。"""
    n = len(raw)
    ok = np.array([r is not None and r[2] >= minconf for r in raw])
    xs = np.array([r[0] if r else np.nan for r in raw]); ys = np.array([r[1] if r else np.nan for r in raw])
    xs[~ok] = np.nan; ys[~ok] = np.nan
    idx = np.arange(n)
    fx, fy = xs.copy(), ys.copy()
    if ok.sum() >= 2:
        fx = np.interp(idx, idx[ok], xs[ok]); fy = np.interp(idx, idx[ok], ys[ok])
        # 超过 0.5 秒的缺口不补
        gap = int(fps * 0.5); i = 0
        while i < n:
            if not ok[i]:
                j = i
                while j < n and not ok[j]: j += 1
                if j - i > gap or i == 0 or j == n:
                    fx[i:j] = np.nan; fy[i:j] = np.nan
                i = j
            else:
                i += 1
    else:
        fx[:] = np.nan; fy[:] = np.nan
    ex, ey = OneEuro(fps), OneEuro(fps)
    sx, sy = np.full(n, np.nan), np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(fx[i]):
            sx[i] = ex(fx[i]); sy[i] = ey(fy[i])
        else:
            ex.x = ey.x = None
    return ok, sx, sy, fx, fy


def run_clip():
    take = sys.argv[2] if len(sys.argv) > 2 else "A_cam_2-02_t1"      # 例：B_cam_1-06_t1
    seg = take.split("_")[2]
    src = f"{PLACE}/{take[0]}/5_place/{take}_fg.mp4"
    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS); W = int(cap.get(3)); H = int(cap.get(4)); N = int(cap.get(7))
    pose, hands = make_pose(), make_hands()
    frames, times, store = [], [], []
    t_all = time.time()
    i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        t0 = time.time()
        res = detect(pose, hands, f, int(i * 1000 / fps), W, H)
        times.append(time.time() - t0)
        store.append(res); i += 1
    cap.release()
    n = len(store)
    names = list(PJ) + ["palm_l", "palm_r"]
    minconf = {k: 0.5 for k in PJ}; minconf["palm_l"] = minconf["palm_r"] = 0.3
    raw_out = {k: [list(map(float, r[k])) if r[k] else None for r in store] for k in names}
    sm_out, stats = {}, {}
    for k in names:
        ok, sx, sy, fx, fy = smooth_track([r[k] for r in store], fps, minconf[k])
        sm_out[k] = [[float(a), float(b)] if not np.isnan(a) else None for a, b in zip(sx, sy)]
        # 抖动：原始（补洞后）与平滑的逐帧位移，取一阶差分的 RMS，以及原始与平滑的偏差
        d_raw = np.hypot(np.diff(fx), np.diff(fy)); d_sm = np.hypot(np.diff(sx), np.diff(sy))
        stats[k] = {
            "detected_frames": int(ok.sum()), "lost_frames": int(n - ok.sum()),
            "lost_pct": round(100 * (n - ok.sum()) / n, 1),
            "jitter_raw_px_per_frame_median": round(float(np.nanmedian(d_raw)), 2) if ok.sum() > 2 else None,
            "jitter_smooth_px_per_frame_median": round(float(np.nanmedian(d_sm)), 2) if ok.sum() > 2 else None,
            "jitter_raw_px_p95": round(float(np.nanpercentile(d_raw, 95)), 2) if ok.sum() > 2 else None,
            "jitter_smooth_px_p95": round(float(np.nanpercentile(d_sm, 95)), 2) if ok.sum() > 2 else None,
            "raw_vs_smooth_dev_px_rms": round(float(np.sqrt(np.nanmean((fx - sx) ** 2 + (fy - sy) ** 2))), 2) if ok.sum() > 2 else None,
        }
    # 二阶差分（加速度）才是看得见的抖：x[i+1]-2x[i]+x[i-1]
    for k in names:
        a = np.array([[p[0], p[1]] if p else [np.nan, np.nan] for p in sm_out[k]])
        stats[k]["accel_smooth_px_rms"] = round(float(np.sqrt(np.nanmean(np.sum(np.diff(a, 2, axis=0) ** 2, 1)))), 2)
        stats[k]["accel_raw_px_rms"] = None
    for k in names:
        r = np.array([[p[0], p[1]] if p else [np.nan, np.nan] for p in raw_out[k]], dtype=float)
        stats[k]["accel_raw_px_rms"] = round(float(np.sqrt(np.nanmean(np.sum(np.diff(r, 2, axis=0) ** 2, 1)))), 2) if np.isfinite(r).any() else None
    tms = np.array(times) * 1000
    out = {"source": src, "fps": fps, "width": W, "height": H, "frames": n,
           "detect_width": DET_W, "device": "CPU", "model": "pose_landmarker_full + hand_landmarker (mediapipe %s)" % mp.__version__,
           "smoothing": "linear fill gaps<=0.5s, One-Euro(mincutoff=1.0, beta=0.02, dcut=1.0)",
           "ms_per_frame": {"mean": round(float(tms.mean()), 1), "median": round(float(np.median(tms)), 1), "p95": round(float(np.percentile(tms, 95)), 1)},
           "total_seconds": round(time.time() - t_all, 1), "stats": stats,
           "raw": raw_out, "smoothed": sm_out}
    json.dump(out, open(f"{OUT}/{seg}_landmarks.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps({"ms": out["ms_per_frame"], "total_s": out["total_seconds"], "stats": stats}, ensure_ascii=False, indent=1))
    if seg == "2-02":
        render_check(src, out, fps, W, H, n)


def render_check(src, out, fps, W, H, n):
    cw, ch = W // 2, H // 2
    tmp = f"{OUT}/2-02_check_tmp.mp4"
    cmd = [FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{cw}x{ch}", "-r", str(int(round(fps))),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(int(round(fps))),
           "-movflags", "frag_keyframe+empty_moov", "-f", "mp4", "pipe:1"]
    # 这台机器上 ffmpeg.exe 不能直接写文件（Permission denied），改从管道出，由 Python 落盘（碎片化 mp4，播放器和浏览器都能放）
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=open(f"{OUT}/2-02_check.mp4", "wb"))
    cap = cv2.VideoCapture(src)
    sm = out["smoothed"]
    cols = {"nose": (0, 255, 255), "eye_l": (0, 255, 255), "eye_r": (0, 255, 255), "shoulder_l": (255, 128, 0), "shoulder_r": (255, 128, 0),
            "elbow_l": (0, 200, 0), "elbow_r": (0, 200, 0), "wrist_l": (0, 0, 255), "wrist_r": (0, 0, 255),
            "palm_l": (255, 0, 255), "palm_r": (255, 0, 255)}
    saved = {}
    want = [int(n * q) for q in (0.1, 0.35, 0.6, 0.85)]
    for i in range(n):
        ok, f = cap.read()
        if not ok: break
        f = cv2.resize(f, (cw, ch), interpolation=cv2.INTER_AREA)
        P = {k: (v[i][0] / 2, v[i][1] / 2) if v[i] else None for k, v in sm.items()}
        for a, b in [("shoulder_l", "shoulder_r"), ("shoulder_l", "elbow_l"), ("elbow_l", "wrist_l"), ("shoulder_r", "elbow_r"), ("elbow_r", "wrist_r")]:
            if P[a] and P[b]:
                cv2.line(f, tuple(map(int, P[a])), tuple(map(int, P[b])), (200, 200, 200), 2, cv2.LINE_AA)
        for k, p in P.items():
            if p: cv2.circle(f, (int(p[0]), int(p[1])), 7, cols[k], -1, cv2.LINE_AA)
        if P["wrist_r"]:  # 画面里"右手腕"：姿态里的 wrist_r（人的右手）
            cx, cy = int(P["wrist_r"][0]), int(P["wrist_r"][1] - 60)  # 120 原像素 = 60 检查像素
            cv2.circle(f, (cx, cy), 12, (0, 255, 0), 3, cv2.LINE_AA)
            cv2.line(f, (cx, cy + 12), (int(P["wrist_r"][0]), int(P["wrist_r"][1])), (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(f, f"frame {i}  t={i / fps:.2f}s  (half-res, original speed)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        pr.stdin.write(f.tobytes())
        if i in want:
            cv2.imwrite(f"{OUT}/2-02_check_f{i:04d}.png", f)
    pr.stdin.close(); pr.wait()
    print("check video done rc", pr.returncode)


def run_census():
    import glob
    files = sorted(glob.glob(f"{PLACE}/*/5_place/*_fg.mp4"))
    rows = []
    for fp in files:
        name = os.path.basename(fp).replace("_t1_fg.mp4", "").replace("_t2_fg.mp4", "").replace("_fg.mp4", "")
        cap = cv2.VideoCapture(fp)
        fps = cap.get(cv2.CAP_PROP_FPS); W = int(cap.get(3)); H = int(cap.get(4)); N = int(cap.get(7))
        pose = make_pose()
        xs, wr_vis, wr_up, nose_x, nsamp = [], 0, 0, [], 0
        t0 = time.time()
        for i in range(0, N, 5):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, f = cap.read()
            if not ok: break
            s = DET_W / f.shape[1]
            small = cv2.resize(f, (DET_W, int(f.shape[0] * s)), interpolation=cv2.INTER_AREA)
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
            pr = pose.detect_for_video(img, int(i * 1000 / fps))
            nsamp += 1
            if not pr.pose_landmarks: continue
            lm = pr.pose_landmarks[0]
            nose = lm[0]
            if min(nose.visibility, nose.presence) > 0.5: nose_x.append(nose.x * W)
            vis = up = False
            for w, e in ((15, 13), (16, 14)):
                lw, le = lm[w], lm[e]
                inframe = 0 <= lw.x <= 1 and 0 <= lw.y <= 1 and min(lw.visibility, lw.presence) > 0.5
                if inframe:
                    vis = True
                    if le.visibility > 0.5 and lw.y < le.y: up = True
            wr_vis += vis; wr_up += up
        cap.release(); pose.close()
        nx = np.array(nose_x)
        rows.append({"name": name, "seconds": round(N / fps, 1), "sampled": nsamp,
                     "wrist_visible_pct": round(100 * wr_vis / max(nsamp, 1), 1),
                     "wrist_above_elbow_pct": round(100 * wr_up / max(nsamp, 1), 1),
                     "head_sway_px": round(float(np.percentile(nx, 95) - np.percentile(nx, 5)), 0) if len(nx) > 3 else None,
                     "head_sway_pct_width": round(float((np.percentile(nx, 95) - np.percentile(nx, 5)) / W * 100), 1) if len(nx) > 3 else None,
                     "head_found_pct": round(100 * len(nx) / max(nsamp, 1), 1), "width": W, "secs_spent": round(time.time() - t0, 1)})
        print(rows[-1], flush=True)
    json.dump(rows, open(f"{OUT}/census.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def run_check():
    d = json.load(open(f"{OUT}/2-02_landmarks.json", encoding="utf-8"))
    render_check(d["source"], d, d["fps"], d["width"], d["height"], d["frames"])


if __name__ == "__main__":
    {"clip": run_clip, "census": run_census, "check": run_check}[sys.argv[1]]()
