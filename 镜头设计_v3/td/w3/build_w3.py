# HKBU SCIE1007 coursework science video. W3 in TouchDesigner: builds the network that turns the ring into 8,918 dots on the table. Runs inside TouchDesigner.
HOME = "D:/。hkbu/molecular science/镜头设计_v3/td/w3"
K = 1                     # 1 is 1080p, 2 is 4K

root = op('/project1')
old = root.op('w3')
if old:
    old.destroy()
w3 = root.create(baseCOMP, 'w3')

ctl = w3.create(constantCHOP, 'ctl')
ctl.par.name0 = 't'
ctl.par.value0 = 0

seeds = w3.create(scriptTOP, 'seeds')
seeds.par.format = 'rgba32float'
cb = w3.create(textDAT, 'seeds_cb')
cb.text = f"""import numpy as np
A = np.load(r"{HOME}/seats.npy")
def onSetupParameters(scriptOp):
    return
def onPulse(par):
    return
def onCook(scriptOp):
    scriptOp.copyNumpyArray(A)
    return
"""
seeds.par.callbacks = cb.path

POS = """
uniform vec4 uA;
uniform vec4 uB;
out vec4 fragColor;
void main() {
    int i = int(gl_FragCoord.x);
    vec4 s = texelFetch(sTD2DInputs[0], ivec2(i, 0), 0);
    float t = uA.x, FLY = uA.y, R = uA.z, W = uA.w * 6.2831853;
    float h = fract(sin(float(i) * 12.9898) * 43758.5453);
    float h2 = fract(sin(float(i) * 78.233) * 12345.678);
    float u = clamp((t - s.a) / FLY, 0.0, 1.0);
    float e = u * u * u * (u * (6.0 * u - 15.0) + 10.0);
    float a0 = s.b + W * min(t, s.a);
    float r0 = R + (h - 0.5) * 26.0;
    float rs = length(s.xy), as = atan(s.y, s.x);
    float turns = 0.6 + 0.5 * h2;
    float aim = as + 6.2831853 * ceil((a0 + turns * 6.2831853 - as) / 6.2831853);
    float ang = mix(a0, aim, e), rad = mix(r0, rs, e);
    vec2 p = vec2(cos(ang), sin(ang)) * rad;
    float fly = sin(3.14159265 * u);
    vec3 q = vec3(p * 0.0032, t * 0.25 + h);
    p += 46.0 * fly * vec2(TDSimplexNoise(q), TDSimplexNoise(q + vec3(17.0, 5.0, 3.0)));
    float bar = uB.x, n = floor(t / bar), c = (t - n * bar) * uB.y;
    float wave = (n >= 1.0 && u >= 1.0) ? exp(-pow((rs - 300.0 - c) / 70.0, 2.0)) : 0.0;
    float size = 3.4 * (1.0 + 0.4 * fly + 0.55 * wave);
    fragColor = vec4(p, size, max(fly, wave));
}
"""
COL = """
out vec4 fragColor;
void main() {
    vec4 p = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0);
    fragColor = vec4(mix(vec3(0.0, 47.0, 167.0) / 255.0, vec3(31.0, 59.0, 255.0) / 255.0, p.a), 1.0);
}
"""
TRAIL = """
uniform float uDecay;
out vec4 fragColor;
void main() {
    vec4 cur = texture(sTD2DInputs[0], vUV.st);
    vec4 old = texture(sTD2DInputs[1], vUV.st);
    fragColor = cur + old * uDecay * (1.0 - cur.a);
}
"""
FINAL = """
out vec4 fragColor;
void main() {
    vec4 a = texture(sTD2DInputs[0], vUV.st);
    fragColor = vec4(vec3(237.0, 235.0, 228.0) / 255.0 * (1.0 - a.a) + a.rgb, 1.0);
}
"""


def glsl(name, code, w, h, fmt, inputs, w3=w3):
    d = w3.create(textDAT, name + '_px')
    d.text = code
    g = w3.create(glslTOP, name)
    g.par.pixeldat = d.path
    g.par.outputresolution = 'custom'
    g.par.resmult = False
    g.par.resolutionw, g.par.resolutionh = w, h
    g.par.format = fmt
    g.par.inputextenduv = 'zero'
    for i, x in enumerate(inputs):
        g.inputConnectors[i].connect(x)
    return g


pos = glsl('pos', POS, 8918, 1, 'rgba32float', [seeds])
pos.par.inputfiltertype = 'nearest'
pos.seq.vec.numBlocks = 2
pos.par.vec0name = 'uA'
pos.par.vec0valuex.expr = "op('ctl')['t']"
pos.par.vec0valuey, pos.par.vec0valuez, pos.par.vec0valuew = 1.4, 262, 1.5
pos.par.vec1name = 'uB'
pos.par.vec1valuex, pos.par.vec1valuey = 15.7 / 8, 900
col = glsl('col', COL, 8918, 1, 'rgba8fixed', [pos])
col.par.inputfiltertype = 'nearest'

geo = w3.create(geometryCOMP, 'dots')
for c in list(geo.children):
    c.destroy()
disc = geo.create(circleSOP, 'disc')
disc.par.type = 'poly'
disc.par.orient = 'xy'
disc.par.radx, disc.par.rady, disc.par.divs = 1, 1, 24
disc.render, disc.display = True, True
mat = w3.create(constantMAT, 'dotmat')
geo.par.material = mat.path
geo.par.instancing = True
geo.par.instancecountmode = 'oplength'
geo.par.instanceop = pos.path
geo.par.instancetx, geo.par.instancety = 'r', 'g'
geo.par.instancesx, geo.par.instancesy = 'b', 'b'
geo.par.instancecolorop = col.path
geo.par.instancer, geo.par.instanceg, geo.par.instanceb = 'r', 'g', 'b'

cam = w3.create(cameraCOMP, 'cam')
cam.par.projection = 'ortho'
cam.par.orthowidth = 1920
cam.par.tz = 100
cam.par.far = 1000

render = w3.create(renderTOP, 'render')
render.par.camera, render.par.geometry = cam.path, geo.path
render.par.lights = ''
render.par.outputresolution = 'custom'
render.par.resmult = False
render.par.resolutionw, render.par.resolutionh = 1920 * K, 1080 * K
render.par.antialias = 'aa8'
render.par.bgcolora = 0
render.par.format = 'rgba16float'

fb = w3.create(feedbackTOP, 'fb')
fb.inputConnectors[0].connect(render)
trail = glsl('trail', TRAIL, 1920 * K, 1080 * K, 'rgba16float', [render, fb])
trail.par.vec0name = 'uDecay'
trail.par.vec0valuex = 0.84
fb.par.top = trail.path
final = glsl('final', FINAL, 1920 * K, 1080 * K, 'rgba8fixed', [trail])
out = w3.create(nullTOP, 'out')
out.inputConnectors[0].connect(final)

rec = w3.create(executeDAT, 'rec')
rec.text = f"""
state = dict(n=-1, end=0, dir='')
def begin(first, last, folder):
    op('fb').par.resetpulse.pulse()
    state.update(n=first, end=last, dir=folder)
    op('ctl').par.value0 = first / 60
def onFrameStart(frame):
    if state['n'] >= 0:
        op('ctl').par.value0 = state['n'] / 60
    return
def onFrameEnd(frame):
    if state['n'] >= 0:
        op('out').save(state['dir'] + '/w3_%04d.png' % state['n'])
        state['n'] += 1
        if state['n'] > state['end']:
            state['n'] = -1
    return
"""
rec.par.framestart = True
rec.par.frameend = True
rec.par.active = True

for x, name in enumerate(['ctl', 'seeds', 'seeds_cb', 'pos', 'col', 'dots', 'dotmat', 'cam', 'render', 'fb', 'trail', 'final', 'out', 'rec']):
    w3.op(name).nodeX, w3.op(name).nodeY = x * 170, 0
project.cookRate = 240
print('errors', {c.name: (c.errors(), c.warnings()) for c in w3.children if c.errors() or c.warnings()})
