"""HKBU SCIE1007 coursework science video. Style scout g3: crossed polarisers. Colour is computed, not picked: retardation from real surface height, Michel-Levy spectrum, sin^2(2 theta) extinction."""
from glib import *


def g(l, m, s1, s2):
    s = np.where(l < m, s1, s2)
    return np.exp(-.5 * ((l - m) / s) ** 2)


def michel_levy(n=3000, gmax=3000):
    lam = np.arange(400, 701, 5, dtype=np.float32)
    x = 1.056 * g(lam, 599.8, 37.9, 31.0) + .362 * g(lam, 442, 16, 26.7) - .065 * g(lam, 501.1, 20.4, 26.2)
    y = .821 * g(lam, 568.8, 46.9, 40.5) + .286 * g(lam, 530.9, 16.3, 31.1)
    z = 1.217 * g(lam, 437, 11.8, 36) + .681 * g(lam, 459, 26, 13.8)
    G = np.linspace(0, gmax, n, dtype=np.float32)
    T = np.sin(np.pi * G[:, None] / lam[None]) ** 2
    XYZ = np.stack([(T * x).sum(1), (T * y).sum(1), (T * z).sum(1)], -1) / y.sum() * 2
    M = np.array([[3.2406, -1.5372, -.4986], [-.9689, 1.8758, .0415], [.0557, -.2040, 1.0570]], dtype=np.float32)
    rgb = np.clip(XYZ @ M.T, 0, None)
    l = rgb.mean(1, keepdims=True)
    rgb = l + (rgb - l) * 1.22  # a little push, real plates are not neon
    return np.clip(rgb, 0, 1.4)


LUT = michel_levy()


def lookup(gamma):
    return LUT[np.clip((gamma / 3000 * (len(LUT) - 1)).astype(np.int32), 0, len(LUT) - 1)]


S = surface()
R = rot(-90, 0, -18)
SC = 17.5
P = smooth_pass(render(R, SC, 620, 330, S=S), 2.2)
m = P["mask"]; z = P["z"]
zn = (z - P["zmin"])  # Angstrom above the back of the protein
wob = fbm(beta=3.4, seed=3)
gamma = 92 * zn + 900 * (wob - .5)
gamma = 230 + 1640 * np.abs(((gamma / 1640) % 2) - 1)  # ping-pong inside the saturated orders so bands stay vivid
rng = np.random.default_rng(7)
grain_th = rng.uniform(-.5, .5, 400)[P["res"]]  # each residue lies as a slightly different grain
grain_g = rng.uniform(-70, 70, 400)[P["res"]]
theta = np.arctan2(P["n"][..., 1], P["n"][..., 0]) + gblur(grain_th * m, 1.0) + .5 * (wob - .5)
ext = np.sin(2 * theta) ** 2
ext = ext ** .55
col = lookup(gamma + gblur(grain_g * m, 1.0))
cav = cavity(z * SC, m, (3, 8, 18))
crossed = col * ext[..., None] * (1 - .92 * np.clip(cav * 1.8, 0, 1))[..., None] * m[..., None]
crossed = crossed * 1.12 + gblur(np.clip(crossed - .6, 0, 1), 18) * .5

# outside the second filter: a plain bright field, the protein is almost nothing
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
relief = (P["n"][..., 0] * .5 + P["n"][..., 1] * .5) * m
pale = (.66 + .05 * relief + .04 * (fbm(beta=2.4, seed=9) - .5))[..., None] * np.array([1, .985, .955], np.float32)
pale = pale - .10 * (gblur(m, 2) * (1 - gblur(m, 5)))[..., None] * 3

# the filter is a sheet with one straight edge, dragged in from the right
d = (xx - 330 - .36 * (yy - 360))
inside = np.clip(d / 1.5 + .5, 0, 1)
rgb = pale * (1 - inside[..., None]) + crossed * inside[..., None]
edge = np.exp(-(d / 2.2) ** 2)
rgb = rgb + edge[..., None] * np.array([.75, .75, .72], np.float32)
rgb = rgb * (1 - .55 * np.exp(-((d + 26) / 26) ** 2))[..., None] * (1 - inside[..., None]) + rgb * inside[..., None]

# the title is a hole cut in the second filter, so through it you see the plain bright field again
f = font("impact.ttf", 250)
t = text_mask("CDK20", f, (1262, 708), "rs")
hole = pale * .98 + (gblur(t, 6) - t)[..., None] * 0
shadow = gblur(t, 5)[..., None]
rgb = rgb * (1 - .75 * shadow)
rgb = rgb * (1 - t[..., None]) + hole * t[..., None]

tag = text_mask(LABEL, font("consolab.ttf", 25), (26, 694), "ls")
rgb = over(rgb, (.05, .05, .05), tag)
save(rgb, "g3_polarized.png")
