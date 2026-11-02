"""HKBU SCIE1007 coursework science video. Motion spike for seconds 25-52: patches a scratch copy of the S1 code and a copy of entry.jsx. The real code and films stay as they are."""
import sys
S = sys.argv[1]
R = "D:/。hkbu/molecular science"
FU = R + "/镜头设计_v3/styleframes/art/fusion/s1"


def sub(s, a, b):
    assert s.count(a) >= 1, a
    return s.replace(a, b, 1)


# ---------------- timeline
p = S + "/motion/code/timeline.py"
s = open(p, encoding="utf8").read()
s = sub(s, 'TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "节奏表.csv")', 'TABLE = r"%s/节奏表.csv"' % FU)
s = sub(s, 'src/v3/fusion/s1_timeline.json', 'src/v3/fusion/s1_timeline_motion.json')
s = sub(s, '''def camera(t):
    """Centre x, y and zoom. Zoom eases on a log scale, so a pull back reads at one even speed."""
    keys = CAM
''', '''# Spike: the camera never stops. It leaves a station fast, rises as it travels, and settles into a slow push that is still going when the next move starts.
GLIDE = [(20.0, 2870, 540, 0.955), (30.6, 2915, 540, 1.0), (31.2, 3840, 556, 0.86), (33.2, 4745, 548, 0.93), (50.6, 4850, 538, 1.01),
         (51.2, 5760, 540, 0.87), (53.2, 6690, 540, 0.95), (59.6, 6735, 540, 1.0)]


def hermite_table(keys):
    ts = np.array([k[0] for k in keys], dtype=float)
    vs = np.array([(k[1], k[2], math.log(k[3])) for k in keys], dtype=float)
    h, d = np.diff(ts), np.diff(vs, axis=0) / np.diff(ts)[:, None]
    m = np.zeros_like(vs)
    m[0], m[-1] = d[0], d[-1]
    for c in range(3):
        for i in range(1, len(ts) - 1):
            if d[i - 1, c] * d[i, c] > 0:
                w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
                m[i, c] = (w1 + w2) / (w1 / d[i - 1, c] + w2 / d[i, c])
    return ts, vs, m


G_T, G_V, G_M = hermite_table(GLIDE)


def glide(t):
    i = min(len(G_T) - 2, int(np.searchsorted(G_T, t, side="right")) - 1)
    h = G_T[i + 1] - G_T[i]
    x = (t - G_T[i]) / h
    a, b, c, d = 2 * x ** 3 - 3 * x ** 2 + 1, x ** 3 - 2 * x ** 2 + x, -2 * x ** 3 + 3 * x ** 2, x ** 3 - x ** 2
    v = a * G_V[i] + b * h * G_M[i] + c * G_V[i + 1] + d * h * G_M[i + 1]
    return float(v[0]), float(v[1]), math.exp(float(v[2]))


def camera(t):
    """Centre x, y and zoom. Zoom eases on a log scale, so a pull back reads at one even speed."""
    if GLIDE[0][0] <= t <= GLIDE[-1][0]:
        return glide(t)
    keys = CAM
''')
open(p, "w", encoding="utf8").write(s)

# ---------------- base
p = S + "/motion/code/base.py"
s = open(p, encoding="utf8").read()
s = sub(s, 'WORK = "../_work/" if K == 1 else "../_work_4k/"', 'WORK = r"%s/" + ("_work/" if K == 1 else "_work_4k/")' % FU)
s = sub(s, 'BONE = (238, 236, 229)                   # the table\'s own tone as rendered\n', '''BONE = (238, 236, 229)                   # the table's own tone as rendered
LIFT = 1.035                             # objects stand above the table, so they cross the frame a little faster than it does
RISE = 0.9                               # seconds an object takes to slide into place
RISERS = [(W.BLISTER, (250, 170), T.PILL_ON), (((W.VIALS[0][0] + W.VIALS[1][0]) / 2, 235), (360, 235), T.VIAL_ON)]
SPEED, GAP, SPAN = 380.0, 1100.0, 280.0  # pulses along the tube: px/s, spacing, length
DARK = np.array((154, 14, 8), dtype=np.float32)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16
DITHER = np.tile(BAYER, (FH // 4 + 1, FW // 4 + 1))[:FH, :FW, None]
''')
s = sub(s, 'def masks_at(t, cam):', '''def pulses_at(t, cam):
    """Soft dark bands that keep running along every filled length of tube."""
    m = Image.new("L", (FW * SS, FH * SS), 0)
    d = ImageDraw.Draw(m)
    cx, cy, z = cam
    x0, x1, y0, y1 = cx - FW / 2 / z - 300, cx + FW / 2 / z + 300, cy - FH / 2 / z - 300, cy + FH / 2 / z + 300
    w = max(2, int(14 * z * SS))
    for name, front in (("main_a", T.front_a(t)), ("liver", T.seg(T.FRONT_L, t))):
        pts = W.PATHS[name]
        front = min(front, len(pts) * 4 - 8)
        s = (t * SPEED) % GAP - GAP
        while s < front:
            for i in range(0, int(SPAN), 20):
                p = s + i
                if 0 <= p < front - 24:
                    a, b = pts[int(p / 4)], pts[int((p + 24) / 4)]
                    if x0 < a[0] < x1 and y0 < a[1] < y1:
                        d.line([to_s(cam, a), to_s(cam, b)], fill=int(255 * 0.6 * math.sin(math.pi * i / SPAN) ** 2), width=w)
            s += GAP
    return np.asarray(m.resize((FW, FH), Image.BOX), dtype=np.float32)[..., None] / 255


def smear(a, n, axis):
    """A camera's motion blur: a box along the direction of travel."""
    n = int(round(n))
    if n < 2:
        return a
    pad = [(0, 0)] * 3
    pad[axis] = (n // 2 + 1, n - n // 2 - 1)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    size = c.shape[axis]
    return ((np.take(c, range(n, size), axis=axis) - np.take(c, range(0, size - n), axis=axis)) / n).astype(np.float32)


class Light:
    """The room's light shifting slowly, on a plane above the table so it drifts against it."""

    def __init__(self):
        n, rng = 256, np.random.default_rng(7)
        ky, kx = np.meshgrid(np.fft.fftfreq(n), np.fft.rfftfreq(n), indexing="ij")
        g = np.fft.irfft2(np.fft.rfft2(rng.standard_normal((n, n))) * np.exp(-(kx ** 2 + ky ** 2) / (2 * 0.012 ** 2)), s=(n, n)).astype(np.float32)
        self.n, self.im = n, Image.fromarray(np.tile(g / np.abs(g).max(), (3, 3)))

    def at(self, t, cam):
        cx, cy, z = cam
        u = 12.0
        ox, oy = ((cx * 0.7 + 11 * t) / u) % self.n, ((cy * 0.7 + 6 * t) / u) % self.n
        box = (ox, oy, ox + FW / z / u, oy + FH / z / u)
        m = self.im.resize((FW // 8, FH // 8), Image.BILINEAR, box=box).resize((FW, FH), Image.BICUBIC)
        return 1 + 0.02 * np.asarray(m, dtype=np.float32)[..., None]


def masks_at(t, cam, cf):''')
s = sub(s, '''    d = ImageDraw.Draw(mo)
    for i, (xy, t0) in enumerate(zip(W.DROPS, T.HITS)):''', '''    d = ImageDraw.Draw(mo)
    cam = cf
    for i, (xy, t0) in enumerate(zip(W.DROPS, T.HITS)):''')
s = sub(s, '''    rect(d, cam, W.BLISTER, (250, 170), T.lift(t, T.PILL_ON) * (1 - 0.6 * T.lift(t, T.PILL_DIM, 0.8)))
    rect(d, cam, ((W.VIALS[0][0] + W.VIALS[1][0]) / 2, 235), (360, 235), T.lift(t, T.VIAL_ON))
''', '''    rect(d, cam, W.BLISTER, (250, 170), (t >= T.PILL_ON + RISE) * (1 - 0.6 * T.lift(t, T.PILL_DIM, 0.8)))
    rect(d, cam, RISERS[1][0], (360, 235), float(t >= T.VIAL_ON + RISE))
''')
s = sub(s, '''        cx, cy, z = T.camera(t)
        cam = cx, cy, z * K
        ml, mo = masks_at(t, cam)
        a = self.layer(self.E, cam) * (1 - ml) + self.layer(self.L, cam) * ml
        if mo.max() > 0:
            a = a * (1 - mo) + self.layer(self.F, cam) * mo
        self.liver.apply(a, round((t - W.LIVER_T[0]) * T.FPS), cam)
        if t >= W.PROTEIN_T[0]:
            self.protein.apply(a, round((t - W.PROTEIN_T[0]) * T.FPS), cam, T.smooth((t - W.PROTEIN_T[0]) / 0.4))
        return (a + 0.5).astype(np.uint8)
''', '''        cx, cy, z = T.camera(t)
        cam = cx, cy, z * K
        cf = cx, cy, z * K * LIFT
        ml, mo = masks_at(t, cam, cf)
        a = self.layer(self.E, cam) * (1 - ml) + self.layer(self.L, cam) * ml
        mb = pulses_at(t, cam) * ml
        a = a * (1 - mb) + DARK * mb
        if mo.max() > 0:
            a = a * (1 - mo) + self.layer(self.F, cf) * mo
        for xy, half, on in RISERS:
            x = (t - on) / RISE
            if 0 < x < 1:
                cr = cx, cy - 130 * (1 - x) ** 3, z * K * LIFT
                m = Image.new("L", (FW * SS, FH * SS), 0)
                rect(ImageDraw.Draw(m), cr, xy, half, T.lift(t, on, 0.25))
                m = np.asarray(m.resize((FW, FH), Image.BOX), dtype=np.float32)[..., None] / 255
                a = a * (1 - m) + self.layer(self.F, cr) * m
        self.liver.apply(a, round((t - W.LIVER_T[0]) * T.FPS), cam)
        if t >= W.PROTEIN_T[0]:
            self.protein.apply(a, round((t - W.PROTEIN_T[0]) * T.FPS), cam, T.smooth((t - W.PROTEIN_T[0]) / 0.4))
        a = a * self.light.at(t, cam)
        c0, c1 = T.camera(t - 1 / 120), T.camera(t + 1 / 120)
        a = smear(smear(a, abs(c1[0] - c0[0]) * z * K / 2, 1), abs(c1[1] - c0[1]) * z * K / 2, 0)
        return np.clip(a + DITHER, 0, 255).astype(np.uint8)
''')
s = sub(s, '        self.protein = Hero("protein", int((W.PROTEIN_T[1] - W.PROTEIN_T[0]) * T.FPS), (W.ROAD_X0, 1080, W.ROAD_X0 + 1920, 2160))\n',
        '        self.protein = Hero("protein", int((W.PROTEIN_T[1] - W.PROTEIN_T[0]) * T.FPS), (W.ROAD_X0, 1080, W.ROAD_X0 + 1920, 2160))\n        self.light = Light()\n')
s = sub(s, '        key = state(t)\n', '        key = t\n')
open(p, "w", encoding="utf8").write(s)

# ---------------- remotion copy
A = R + "/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
s = open(A + "entry.jsx", encoding="utf8").read()
s = sub(s, 's1_timeline.json', 's1_timeline_motion.json')
s = sub(s, '''      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
        <g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}>
          <Liver/>''', '''      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
        <defs><filter id="mb" filterUnits="userSpaceOnUse" x={0} y={0} width={W} height={H}><feGaussianBlur stdDeviation={`${blur[0]} ${blur[1]}`}/></filter></defs>
        <g filter={blur[0] > 0.3 || blur[1] > 0.3 ? "url(#mb)" : undefined}><g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}>
          <Liver/>''')
s = sub(s, '''          <Pin xy={TL.world.hkstp} at={122.0}>Pak Shek Kok</Pin>
        </g>
''', '''          <Pin xy={TL.world.hkstp} at={122.0}>Pak Shek Kok</Pin>
        </g></g>
''')
s = sub(s, '''  const f = useCurrentFrame(), t = TL.u[f], [cx, cy, z] = TL.cam[f];
  return <Clock.Provider value={t}><Zoom.Provider value={z}>''', '''  const f = useCurrentFrame(), t = TL.u[f], [cx, cy, z] = TL.cam[f], next = TL.cam[Math.min(f + 1, TL.cam.length - 1)];
  const blur = [Math.abs(next[0] - cx) * z / 7, Math.abs(next[1] - cy) * z / 7];
  return <Clock.Provider value={t}><Zoom.Provider value={z}>''')
open(A + "entry_motion.jsx", "w", encoding="utf8").write(s)
print("patched")
