"""HKBU SCIE1007 coursework science video. Clay direction: the keyhole shape as a signed distance. A prop, not a molecule."""
import numpy as np


def keyhole(x, y):
    """Signed distance in table units, negative inside. Round head at the top, flared slot below."""
    head = np.hypot(x, y - 1.15) - 1.5
    t = np.clip((1.15 - y) / 4.6, 0, 1)
    half = 0.55 + 0.75 * t
    slot = np.maximum(np.abs(x) - half, np.maximum(y - 1.15, -3.45 - y))
    return {"d": np.minimum(head, slot)}
