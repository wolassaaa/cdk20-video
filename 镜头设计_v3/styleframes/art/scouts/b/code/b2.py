"""HKBU SCIE1007 coursework science video. Style scout b2: one wavelength of light and mist. Everything is a single ramp, the real CDK20 stands as an eclipse."""
import numpy as np

from common import *

P = load()
SUN = (640, 300)
R = 395
V = view(P, zoom=1.0, at=(640, 262), src=(945, 545))
y, x = grid()
m = V["mask"]
r = np.hypot(x - SUN[0], y - SUN[1])

# sun and the sky it lights, scene luminance
disc = sstep(R + 1.2, R - 1.2, r)
glow = 0.34 * np.exp(-((r - R).clip(0) / 110) ** 1.1) + 0.10 * np.exp(-((r - R).clip(0) / 420))
L = 0.05 + glow + disc * 1.5

# god rays: push the occluded sun outward along the radii, real silhouette gaps cut the beams
src = blur(disc, 5) * (1 - blur(m, 2))
rays = np.zeros_like(src)
for i in range(120):
    k = 1 - (i + 0.5) / 120 * 0.7
    rays += sample(src, SUN[0] + (x - SUN[0]) * k, SUN[1] + (y - SUN[1]) * k) * (1 - i / 120) ** 1.5
rays /= 34
ang = np.arctan2(y - SUN[1], x - SUN[0])
beam = np.interp(ang, np.linspace(-np.pi, np.pi, 720), blur(noise(21, 90, (9, 720), 1.2), 2)[4])
rays = rays * (0.35 + 1.5 * sstep(0.3, 0.75, beam))

# protein in the mist: dark mass, faint rim of scattered light, depth eats it
mist = noise(3, 500, slope=2.4)
mist2 = noise(9, 180, slope=2.0)
form = 0.015 + 0.11 * V["ao"] * V["rim"] + 0.04 * V["key"] + 0.09 * sstep(0.25, 0.5, V["depth"]) * m
sky = L.copy()
L = L * (1 - m) + form * m
L = L + rays * 0.95 * (1 - m * 0.75)

# floor: wet, mirrors the sky
hz = 596
floor = sstep(hz - 1, hz + 1, y)
fl = 2 * hz - y
mirror = blur(sample(sky + rays * 0.95, x, fl), 2.5)  # the wet floor holds the sun, not the protein, so nothing stray sits at the frame edge
L = L * (1 - floor) + floor * (mirror * (0.62 - 0.5 * sstep(hz, 720, y)) + 0.01)

# the name stands on the horizon like a building
# mist over everything, heaviest low down
fog = (0.10 + 0.34 * sstep(200, hz, y) * sstep(700, hz, y)) * (0.25 + 1.5 * mist) + 0.14 * mist2
L = L + fog * 0.55

tm = text("CDK20", "ariblk.ttf", 172, (640, hz + 1), "mb", tracking=26)
tm = tm * (y < hz)
tmr = sample(tm, x, fl) * floor * sstep(720, hz, y) * 0.75
L = L * (1 - tm) * (1 - tmr) + tm * 0.012

# small crowd on the floor, black dashes in the glare
rng = np.random.default_rng(12)
people = np.zeros((H, W), np.float32)
for cxx in (118, 212, 1080, 1196):
    for i in range(5):
        px, py = cxx + rng.normal(0, 16), hz + 7 + rng.random() * 8
        h = rng.uniform(15, 20)
        head = sstep(1, 0, np.hypot(x - px, y - (py - h)) - h * 0.14)
        body = sstep(0.8, 0, np.abs(x - px) - h * 0.13) * (y > py - h) * (y < py)
        people = np.maximum(people, np.maximum(head, body))
L = L * (1 - people * 0.97)

# single wavelength: one ramp, nothing else is allowed in the frame
t = np.clip(1 - np.exp(-L * 1.75), 0, 1)
rgb = ramp(t, [(0, "#0a0200"), (0.14, "#2c0a00"), (0.34, "#7a2200"), (0.56, "#d65a00"), (0.74, "#ff9a00"), (0.9, "#ffd21a"), (1, "#fff6a8")])
lab = text(LABEL, "bahnschrift.ttf", 21, (36, 694), "lm", tracking=2)
rgb = over(rgb, hexc("#ffd84a"), lab)
finish(rgb, "b2_mono_sun.png")
