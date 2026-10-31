"""HKBU SCIE1007 coursework science video. Style scout c4 post: push the one red, keep the white clean, set the label. Method only."""
from common import *

im = np.asarray(Image.open(OUT / "_code/_raw/c4.png").convert("RGB"), np.float32) / 255
r, g, b = im[..., 0], im[..., 1], im[..., 2]
sat = np.clip((r - (g + b) / 2 - 0.30) * 5.0, 0, 1)
RED = hexrgb("#FF0A1C")
red_out = (np.clip(r * 1.25, 0, 1) ** 1.5)[..., None] * RED
rgb = comp(im, sat, red_out)
# whites open up, shadows stay cold
rgb = np.clip((rgb - 0.03) * 1.1, 0, 1)
rgb = paste_sprite(rgb, type_sprite(LABEL, font(F + "segoeuib.ttf", 24), pad=2), 182, 682, RED)
tick = np.zeros((H, W), np.float32)
tick[698:702, 28:336] = 1
rgb = comp(rgb, tick, RED)
finish(rgb, "c4_mirrors_edge_white_red.png")
