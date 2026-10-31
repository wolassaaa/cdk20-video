"""HKBU SCIE1007 coursework science video. Style scout c5 post: trajectory line and label. Method only."""
from common import *

rgb = np.asarray(Image.open(OUT / "_code/_raw/c5.png").convert("RGB"), np.float32) / 255
rgb = np.clip((rgb - 0.02) * 1.06, 0, 1)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
sat = np.clip((r - (g + b) / 2 - 0.1) * 6, 0, 1)[..., None]
vivid = np.stack([np.clip((r - 0.66) / 0.26 * 0.40 + 0.66, 0, 1), np.clip((g - 0.14) * 0.7, 0, 1), np.clip((b - 0.14) * 0.6, 0, 1)], -1)
rgb = rgb * (1 - sat) + vivid * sat
K = np.zeros(3, np.float32)
tag = np.zeros((H, W), np.float32)
tag[664:700, 30:398] = 1
rgb = comp(rgb, tag, K)
rgb = paste_sprite(rgb, type_sprite(LABEL, font(F + "seguibli.ttf", 24), pad=2), 214, 681, np.array([1, 1, 1], np.float32))
finish(rgb, "c5_superhot_shatter.png")
