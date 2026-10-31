"""HKBU SCIE1007 coursework science video. Lantern T3 (3-08): the darkest moment. One person stands inside a keyhole as tall as the frame with the lamp held up, and the light gives out long before it touches anything. The keyhole is a chalk metaphor, marked schematic, not a structure."""
from lk import *

CX, CY, R = 334.0, 300.0, 250.0
FLOOR = 958.0


def keyhole(cx=CX, cy=CY, r=R, floor=FLOOR):
    """Dashed outline as a list of points: a big circle over a flared foot."""
    a0 = 90 + 21
    pts = [(cx + r * np.cos(np.radians(t)), cy + r * np.sin(np.radians(t))) for t in np.linspace(a0, 360 + 180 - a0, 90)]
    return pts + [(cx + 320, floor), (cx - 320, floor)]


def scene(c, px=CX - 12, ax_deg=-90.0, half=15.0, reach=250.0, floor=FLOOR):
    """The person, the cone that stops short, the small pool at their feet. Used here and in the motion film."""
    fig, (lx, ly) = walker(px, floor + 2, 1.9)
    ang = np.arctan2(yy - ly, xx - lx)
    da = np.abs(np.angle(np.exp(1j * (ang - np.radians(ax_deg)))))
    dist = np.hypot(xx - lx, yy - ly)
    cone = ((da < np.radians(half)) & (dist < reach)).astype(np.float32)
    c = add(c, fft_blur(cone, 0.7) * 0.30, AMBER)
    pool = (((xx - px) / 96) ** 2 + ((yy - floor - 7) / 8) ** 2 < 1).astype(np.float32)
    c = add(c, fft_blur(pool, 0.8) * 0.42, AMBER)
    c = lay(c, fig, AMBER)
    c = add(c, (np.hypot(xx - lx, yy - ly) < 6).astype(np.float32), AMBER_HI)
    return c


if __name__ == "__main__":
    c = blank()
    c = lay(c, dash(keyhole(), on=20, off=15, width=3.6, closed=True), CHALK * 0.6)
    c = scene(c)
    c = lay(c, tx("no one had measured CDK20's shape", 44, 500, 1860, 932, anchor="rs"), CHALK)
    bw = tw("schematic", 36, 500)
    fr = [(1860 - bw - 48, 960), (1860, 960), (1860, 1028), (1860 - bw - 48, 1028)]
    c = lay(c, dash(fr, on=12, off=9, width=3, closed=True), CHALK)
    c = lay(c, tx("schematic", 36, 500, 1836, 1007, anchor="rs"), CHALK)
    save(c, "T3.png")
