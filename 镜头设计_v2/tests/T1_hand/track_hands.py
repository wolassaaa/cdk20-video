"""T1: track both hands in a clip with MediaPipe and export smoothed per-frame data for the hologram composite.

Usage: python track_hands.py <video> <hand_landmarker.task> <out_dir>
Writes hands.json (per frame: palm centre, pinch, openness, 21 landmarks per hand, in pixels)
and debug.mp4 (landmarks drawn on the footage) for checking the tracking by eye.
"""
import sys, json, math
import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

VIDEO, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PALM = (0, 5, 9, 13, 17)
TIPS = (4, 8, 12, 16, 20)
BONES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12),
         (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)]


class OneEuro:
    """One Euro filter: smooths jitter when the hand is still, follows quickly when it moves."""
    def __init__(self, fps, min_cutoff=1.2, beta=0.02, d_cutoff=1.0):
        self.fps, self.min_cutoff, self.beta, self.d_cutoff = fps, min_cutoff, beta, d_cutoff
        self.x = self.dx = None

    def _alpha(self, cutoff):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau * self.fps)

    def __call__(self, x):
        if self.x is None:
            self.x, self.dx = x, 0.0
            return x
        dx = (x - self.x) * self.fps
        self.dx += self._alpha(self.d_cutoff) * (dx - self.dx)
        self.x += self._alpha(self.min_cutoff + self.beta * abs(self.dx)) * (x - self.x)
        return self.x

    def reset(self):
        self.x = self.dx = None


cap = cv2.VideoCapture(VIDEO)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
landmarker = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO, num_hands=2,
    min_hand_detection_confidence=0.5, min_hand_presence_confidence=0.5, min_tracking_confidence=0.5))
debug = cv2.VideoWriter(f"{OUT}/debug.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

# one filter per (hand, landmark, axis); hands keyed by MediaPipe's handedness label
filters = {side: [[OneEuro(fps) for _ in range(2)] for _ in range(21)] for side in ("Left", "Right")}
frames, i = [], 0
while True:
    ok, img = cap.read()
    if not ok:
        break
    res = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)),
                                      int(i * 1000 / fps))
    seen, hands = set(), {}
    for lms, hd in zip(res.hand_landmarks, res.handedness):
        side = hd[0].category_name
        if side in seen:  # both detections claim the same side: keep the first
            continue
        seen.add(side)
        pts = [(filters[side][k][0](lm.x * W), filters[side][k][1](lm.y * H)) for k, lm in enumerate(lms)]
        size = math.dist(pts[0], pts[9]) or 1.0
        palm = (sum(pts[k][0] for k in PALM) / 5, sum(pts[k][1] for k in PALM) / 5)
        hands[side] = {
            "palm": [round(v, 1) for v in palm],
            "size": round(size, 1),
            "pinch": round(math.dist(pts[4], pts[8]) / size, 3),
            "open": round(sum(math.dist(pts[t], palm) for t in TIPS) / 5 / size, 3),
            "pts": [[round(x, 1), round(y, 1)] for x, y in pts],
            "score": round(hd[0].score, 3),
        }
        for a, b in BONES:
            cv2.line(img, tuple(map(int, pts[a])), tuple(map(int, pts[b])), (250, 220, 90), 2)
        cv2.circle(img, tuple(map(int, palm)), 9, (60, 140, 255), -1)
    for side in ("Left", "Right"):
        if side not in seen:  # lost the hand: restart its filter so it does not glide in from the old spot
            for f in filters[side]:
                f[0].reset(); f[1].reset()
    frames.append(hands)
    debug.write(img)
    i += 1

debug.release()
n = len(frames)
stats = {"frames": n, "fps": fps, "width": W, "height": H,
         "any_hand": round(sum(1 for f in frames if f) / n, 3),
         "both_hands": round(sum(1 for f in frames if len(f) == 2) / n, 3)}
json.dump({"stats": stats, "frames": frames}, open(f"{OUT}/hands.json", "w"))
print("STATS", json.dumps(stats))
