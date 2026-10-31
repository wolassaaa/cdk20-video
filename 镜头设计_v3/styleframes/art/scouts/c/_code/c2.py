"""HKBU SCIE1007 coursework science video. Style scout c2 post: glow, space tearing around the portal, a redaction bar for the label. Method only."""
from common import *

im = np.asarray(Image.open(OUT / "_code/_raw/c2.png").convert("RGB"), np.float32) / 255
R = hexrgb("#FF0A16")
rgb = im.copy()
glow = gblur(np.clip(im - 0.55, 0, 1) * np.array([1, .1, .1], np.float32), 30)
rgb = 1 - (1 - np.clip(rgb, 0, 1)) * (1 - np.clip(glow * 0.55, 0, 1))
xx, yy = np.meshgrid(np.linspace(-1, 1, W, dtype=np.float32), np.linspace(-1, 1, H, dtype=np.float32))
rgb *= (1 - 0.45 * np.clip(xx ** 2 * 0.9 + yy ** 2 * 0.5, 0, 1) ** 1.3)[..., None]

# redaction bars, the label is what survives
bar = np.zeros((H, W), np.float32)
bar[676:708, 34:390] = 1
bar[676:708, 402:520] = 1
rgb = comp(rgb, bar, np.zeros(3, np.float32))
rgb = paste_sprite(rgb, type_sprite(LABEL, font(F + "arialbd.ttf", 23), pad=2), 212, 692, np.array([1, 1, 1], np.float32))
finish(rgb, "c2_control_brutalism.png")
