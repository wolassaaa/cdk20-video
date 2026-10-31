"""HKBU SCIE1007 coursework science video. falsecolor art direction: T6 picture layer, the road map as a one-dimensional heat map.

python comp_t6.py [door] [out.png]   door = how far the signal has got, in stations (3 for this still)

Colour along the road is the station number reached, on the s6 map. Road walked has signal, road not walked has none.
The bar runs to 6, Approval, and the signal stops at 3: the top of the bar is never reached in this film. That is the point of the shot.
"""
import os
import sys

import numpy as np
from PIL import Image

from fc_common import PUB, apply, blur, l2s, s2l, smooth, to_u8

W, H = 1920, 1080
X0, X1 = 96, 1660      # road, in px; six equal cells. The lit part runs in from off the frame
Y0, Y1 = -40, 660


def compose(door=3.0, name="s6_route"):
    cell = (X1 - X0) / 6
    x = (np.arange(W) + 0.5 - X0) / cell              # position along the road, in stations
    v = (1 + np.clip(x, 0, 3) * 2 / 3) / 6             # 1 where the road enters, 3 at the door of station 4: stations reached, interpolated
    road = x <= door
    y = np.arange(H) + 0.5
    band = ((y >= Y0) & (y <= Y1)).astype(float)[:, None] * road[None, :].astype(float)
    band = blur(band, 0.7)
    col = apply(np.broadcast_to(v[None, :], (H, W)), name)
    lin = s2l(col) * band[..., None]
    # the walked road lights the dark around it. Soft and slow, no grain
    g = blur(lin, 24) * 0.45 + blur(lin, 110) * 0.8
    out = lin + g * (1 - band[..., None])
    # past the door there is no signal, so no glow either: pure floor of the bar
    return l2s(out * road[None, :, None])


if __name__ == "__main__":
    door = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PUB, "t6_bg.png")
    Image.fromarray(to_u8(compose(door))).save(out)
    print("wrote", out)
