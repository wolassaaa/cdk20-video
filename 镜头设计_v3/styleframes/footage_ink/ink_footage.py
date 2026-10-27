"""Turn plain-wall footage into the v3 look without a green screen.

MediaPipe multiclass segmentation finds the person (hair, skin, clothes); the wall becomes black; the person is drawn
as white ink: XDoG edges (a pen-and-ink stylisation) over a dim posterised fill, with the ink boiling every few frames
like hand-drawn animation.

usage: python ink_footage.py <in.mp4> <out_dir> [start_frame] [n_frames] [boil_every]
Writes PNG frames to <out_dir> (keep it an ASCII path: OpenCV cannot open non-ASCII paths on Windows).
"""
import sys, os
import numpy as np
import cv2
import mediapipe as mp

SRC, OUT = sys.argv[1], sys.argv[2]
START = int(sys.argv[3]) if len(sys.argv) > 3 else 0
N = int(sys.argv[4]) if len(sys.argv) > 4 else 90
BOIL = int(sys.argv[5]) if len(sys.argv) > 5 else 3
MODEL = os.path.join(os.path.dirname(os.path.abspath(OUT)), "models", "selfie_multiclass_256x256.tflite")
os.makedirs(OUT, exist_ok=True)

seg = mp.tasks.vision.ImageSegmenter.create_from_options(mp.tasks.vision.ImageSegmenterOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=MODEL),
    running_mode=mp.tasks.vision.RunningMode.VIDEO, output_category_mask=True))


def xdog(gray, sigma, k=1.6, p=22.0, eps=0.0, phi=12.0):
    """eXtended Difference of Gaussians: soft-thresholded edges that read like ink."""
    g1 = cv2.GaussianBlur(gray, (0, 0), sigma)
    g2 = cv2.GaussianBlur(gray, (0, 0), sigma * k)
    d = (1 + p) * g1 - p * g2
    e = np.where(d >= eps, 1.0, 1.0 + np.tanh(phi * (d - eps)))
    return 1.0 - np.clip(e, 0, 1)   # 1 = ink


cap = cv2.VideoCapture(SRC)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
cap.set(cv2.CAP_PROP_POS_FRAMES, START)
rng = np.random.default_rng(3)
for i in range(N):
    ok, frame = cap.read()
    if not ok:
        break
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), int((START + i) * 1000 / fps))
    cat = res.category_mask.numpy_view()
    person = (cat > 0).astype(np.float32)                       # 0 = background
    person = cv2.GaussianBlur(cv2.resize(person, (w, h)), (0, 0), 2.0)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    # boil: re-jitter the drawing every BOIL frames (animated "on threes")
    b = (START + i) // BOIL
    jit = np.random.default_rng(b)
    dx, dy = jit.normal(0, 0.8, 2)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    gj = cv2.warpAffine(gray, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    sigma = 0.9 + 0.2 * jit.random()
    ink = xdog(gj, sigma, p=28.0, phi=15.0)
    # chalk-on-black shading: hatch strokes where the subject is lit, cross-hatch where it is brightest
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    tone = clahe.apply((gj * 255).astype(np.uint8)).astype(np.float32) / 255.0
    tone = cv2.GaussianBlur(tone, (0, 0), 2)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ph = jit.random() * 6.28
    wob = 1.5 * np.sin(yy / 37.0 + ph)                      # strokes wander a little, like a hand
    h1 = (np.sin((xx + yy + wob) * 2 * np.pi / 7.0 + ph) > 0.82).astype(np.float32)
    h2 = (np.sin((xx - yy - wob) * 2 * np.pi / 9.0 + ph) > 0.86).astype(np.float32)
    hatch = h1 * (tone > 0.42) * 0.55 + h2 * (tone > 0.68) * 0.5
    grain = rng.normal(0, 0.06, (h, w)).astype(np.float32)
    img = np.clip((np.maximum(ink * 0.95, hatch) + grain * ink + 0.04) * person, 0, 1)
    # silhouette contour: a heavier hand line round the person
    edge = cv2.morphologyEx((person > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(np.float32)
    img = np.maximum(img, edge * 0.9)
    out = (img * 255).astype(np.uint8)
    out = cv2.merge([out, out, out])
    out[..., :] = np.clip(out.astype(np.float32) * np.array([0.894, 0.922, 0.929]), 0, 255).astype(np.uint8)  # off-white ink #EDEBE4 (BGR)
    cv2.imwrite(os.path.join(OUT, f"f{i:04d}.png"), out)
print("frames", i + 1)
