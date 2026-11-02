# HKBU SCIE1007 coursework science video. Matter test in TouchDesigner: blends one body of grains from shape to shape as a pure function of the frame number, and records. Runs inside TouchDesigner.
HOME = "D:/。hkbu/molecular science/镜头设计_v3/td/matter"
K = 1                     # 1 is 1080p, 2 is 4K

root = op('/project1')
old = root.op('matter')
if old:
    old.destroy()
m = root.create(baseCOMP, 'matter')

ctl = m.create(constantCHOP, 'ctl')
ctl.par.name0 = 'n'

calc = m.create(textDAT, 'calc')
calc.text = f"""import numpy as np
D = np.load(r"{HOME}/poses.npz")
P, C, S = D['p'], D['c'], D['s']
LEAD, SEED, FIG = D['lead'], D['seed'], D['fig']
CAM = np.load(r"{HOME}/cam.npy")
W_, H_ = 800, 500
# start, grain time, spread of starts, from, to, height of the arc, width of the stream
SEG = [(5.4, 1.5, 1.4, 0, 1, 260.0, 150.0), (10.2, 1.3, 1.2, 1, 2, 220.0, 130.0), (15.6, 1.5, 1.4, 2, 3, 240.0, 170.0)]
KEEP = {{}}

def ease(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (x * (6.0 * x - 15.0) + 10.0)

def state(n):
    if KEEP.get('n') == n:
        return KEEP['p'], KEEP['c']
    t = n / 60.0
    p, c, s = P[0].copy(), C[0].copy(), S[0].copy()
    for t0, dur, spread, a, b, lift, width in SEG:
        if t < t0:
            break
        u = (t - t0 - spread * (1 - LEAD_X[a])) / dur
        e = ease(u)[:, None]
        p = P[a] + (P[b] - P[a]) * e
        c = C[a] + (C[b] - C[a]) * e
        s = S[a] + (S[b] - S[a]) * e[:, 0]
        w = np.sin(np.pi * e[:, 0])
        phi = SEED[:, 0] * 6.283 + e[:, 0] * 7.0
        r = width * np.sqrt(SEED[:, 1]) * w
        p = p + np.stack((np.zeros_like(r), r * np.cos(phi) + lift * w, r * np.sin(phi)), axis=1)
    if t >= 19.6:
        u = (t - 19.6 - (FIG - 3) * 0.22 - 0.7 * SEED[:, 0]) / 3.2
        e = np.where(FIG >= 3, ease(u), 0.0)[:, None]
        p = p + (P[4] - P[3]) * e
        c = c + (C[4] - C[3]) * e
        s = s + (S[4] - S[3]) * e[:, 0]
    p = p + np.stack((np.zeros(len(p)), 5.0 * np.sin(0.011 * p[:, 0] - 2.2 * t), 5.0 * np.cos(0.009 * p[:, 1] - 1.7 * t)), axis=1)    # a slow wave through the whole body
    a = np.concatenate((p, s[:, None]), axis=1).astype(np.float32).reshape(H_, W_, 4)
    b = np.concatenate((c, np.ones((len(c), 1), dtype=np.float32)), axis=1).astype(np.float32).reshape(H_, W_, 4)
    KEEP.update(n=n, p=a, c=b)
    return a, b

# grains leave from the right-hand side of each shape first, so the body pours towards the next one
LEAD_X = [np.argsort(np.argsort(P[i][:, 0])).astype(np.float32) / len(P[i]) for i in range(3)]
"""


def table(name, index, m=m):
    t = m.create(scriptTOP, name)
    t.par.format = 'rgba32float'
    cb = m.create(textDAT, name + '_cb')
    cb.text = f"""def onSetupParameters(scriptOp):
    return
def onPulse(par):
    return
def onCook(scriptOp):
    scriptOp.copyNumpyArray(op('calc').module.state(int(op('ctl')['n']))[{index}])
    return
"""
    t.par.callbacks = cb.path
    return t


pos = table('pos', 0)
col = table('col', 1)

geo = m.create(geometryCOMP, 'grains')
for c in list(geo.children):
    c.destroy()
ball = geo.create(sphereSOP, 'ball')
ball.par.type = 'mesh'
ball.par.rows, ball.par.cols = 6, 8
ball.par.radx, ball.par.rady, ball.par.radz = 1, 1, 1
ball.render, ball.display = True, True
mat = m.create(phongMAT, 'flat')
mat.par.diffr, mat.par.diffg, mat.par.diffb = 1, 1, 1
mat.par.ambr, mat.par.ambg, mat.par.ambb = 1, 1, 1
mat.par.specr, mat.par.specg, mat.par.specb = 0, 0, 0
geo.par.material = mat.path
geo.par.instancing = True
geo.par.instancecountmode = 'oplength'
geo.par.instanceop = pos.path
geo.par.instancetx, geo.par.instancety, geo.par.instancetz = 'r', 'g', 'b'
geo.par.instancesx, geo.par.instancesy, geo.par.instancesz = 'a', 'a', 'a'
geo.par.instancecolorop = col.path
geo.par.instancer, geo.par.instanceg, geo.par.instanceb = 'r', 'g', 'b'

aim = m.create(nullCOMP, 'aim')
cam = m.create(cameraCOMP, 'cam')
cam.par.fov = 26
cam.par.near, cam.par.far = 50, 14000
cam.par.lookat = aim.path
fill = m.create(ambientlightCOMP, 'fill')
fill.par.dimmer = 1

render = m.create(renderTOP, 'render')
render.par.camera, render.par.geometry = cam.path, geo.path
render.par.lights = fill.path
render.par.outputresolution = 'custom'
render.par.resmult = False
render.par.resolutionw, render.par.resolutionh = 1920 * K, 1080 * K
render.par.antialias = 'aa8'
render.par.bgcolora = 0
render.par.format = 'rgba16float'

soft = m.create(blurTOP, 'soft')
soft.inputConnectors[0].connect(render)
soft.par.size = 30 * K

d = m.create(textDAT, 'final_px')
d.text = """
out vec4 fragColor;
void main() {
    vec4 a = texture(sTD2DInputs[0], vUV.st);
    float shade = texture(sTD2DInputs[1], vUV.st + vec2(-0.012, 0.028)).a;
    vec3 bg = vec3(237.0, 235.0, 228.0) / 255.0 * (1.0 - 0.2 * shade);
    fragColor = vec4(bg * (1.0 - a.a) + a.rgb * a.a, 1.0);
}
"""
final = m.create(glslTOP, 'final')
final.par.pixeldat = d.path
final.par.outputresolution = 'custom'
final.par.resmult = False
final.par.resolutionw, final.par.resolutionh = 1920 * K, 1080 * K
final.par.format = 'rgba8fixed'
final.inputConnectors[0].connect(render)
final.inputConnectors[1].connect(soft)
out = m.create(nullTOP, 'out')
out.inputConnectors[0].connect(final)

rec = m.create(executeDAT, 'rec')
rec.text = """state = dict(n=-1, end=0, dir='')
def show(n):
    op('ctl').par.value0 = n
    e = op('calc').module.CAM[n]
    c, a = op('cam'), op('aim')
    c.par.tx, c.par.ty, c.par.tz = float(e[0]), float(e[1]), float(e[2])
    a.par.tx, a.par.ty, a.par.tz = float(e[3]), float(e[4]), float(e[5])
def begin(first, last, folder):
    state.update(n=first, end=last, dir=folder)
    show(first)
def onFrameStart(frame):
    if state['n'] >= 0:
        show(state['n'])
    return
def onFrameEnd(frame):
    if state['n'] >= 0:
        op('out').save(state['dir'] + '/matter_%04d.png' % state['n'])
        state['n'] += 1
        if state['n'] > state['end']:
            state['n'] = -1
    return
"""
rec.par.framestart = True
rec.par.frameend = True
rec.par.active = True

for x, name in enumerate(['ctl', 'calc', 'pos', 'pos_cb', 'col', 'col_cb', 'grains', 'flat', 'aim', 'cam', 'fill', 'render', 'soft', 'final_px', 'final', 'out', 'rec']):
    m.op(name).nodeX, m.op(name).nodeY = x * 170, 0
print('errors', {c.name: (c.errors(), c.warnings()) for c in m.children if c.errors() or c.warnings()})
