"""Build a hands-only layer with alpha, so hands can pass in front of the hologram.

The mask is drawn from the tracked landmarks: a capsule along every finger bone, the palm polygon and a short
forearm stub, then feathered. No segmentation model needed.

Usage: python hand_mask.py <video> <hands.json> <ffmpeg.exe> <out.webm>
"""
import sys, json, subprocess, os, tempfile
import cv2
import numpy as np

VIDEO, DATA, FFMPEG, OUT = sys.argv[1:5]
BONES = [(0, 1), (1, 2), (2, 3), (3, 4), (5, 6), (6, 7), (7, 8), (9, 10), (10, 11), (11, 12),
         (13, 14), (14, 15), (15, 16), (17, 18), (18, 19), (19, 20)]
PALM = [0, 1, 2, 5, 9, 13, 17]

data = json.load(open(DATA, encoding="utf-8"))
frames, W, H, fps = data["frames"], data["stats"]["width"], data["stats"]["height"], data["stats"]["fps"]
# OpenCV cannot open non-ASCII paths on Windows, so masks go to an ASCII temp folder as PNGs and ffmpeg does the rest
tmp = tempfile.mkdtemp()

for n, hands in enumerate(frames):
    m = np.zeros((H, W), np.uint8)
    for h in hands.values():
        p = np.array(h["pts"], np.float32)
        s = h["size"]
        for a, b in BONES:
            w = int(max(6, s * (0.30 if a in (1, 2) else 0.24)))
            cv2.line(m, tuple(map(int, p[a])), tuple(map(int, p[b])), 255, w, cv2.LINE_AA)
            cv2.circle(m, tuple(map(int, p[b])), w // 2, 255, -1, cv2.LINE_AA)
        cv2.fillConvexPoly(m, cv2.convexHull(p[PALM].astype(np.int32)), 255, cv2.LINE_AA)
        # forearm stub: continue from the wrist away from the middle knuckle
        d = p[0] - p[9]
        d /= np.linalg.norm(d) + 1e-6
        cv2.line(m, tuple(map(int, p[0])), tuple(map(int, p[0] + d * s * 2.2)), 255, int(s * 0.9), cv2.LINE_AA)
    m = cv2.dilate(m, np.ones((7, 7), np.uint8))
    m = cv2.GaussianBlur(m, (0, 0), 4)
    cv2.imwrite(os.path.join(tmp, f"m{n:04d}.png"), m)

# original colour + mask as alpha -> VP9 WebM with transparency
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", VIDEO, "-framerate", str(fps), "-i", os.path.join(tmp, "m%04d.png"), "-filter_complex",
                "[1:v]format=gray[a];[0:v][a]alphamerge,format=yuva420p", "-an", "-c:v", "libvpx-vp9",
                "-pix_fmt", "yuva420p", "-b:v", "4M", "-auto-alt-ref", "0", OUT], check=True)
print("WROTE", OUT, len(frames), "frames")
