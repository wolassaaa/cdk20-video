# HKBU SCIE1007 coursework science video. W2 in TouchDesigner: draws the beads fold.py computed, lit in 3D, and brings the lights up from the centre. Runs inside TouchDesigner.
from math import tan, radians
HOME = "D:/。hkbu/molecular science/镜头设计_v3/td/w2"
K = 2                     # 1 is 1080p, 2 is 4K

root = op('/project1')
old = root.op('w2')
if old:
    old.destroy()
w2 = root.create(baseCOMP, 'w2')

ctl = w2.create(constantCHOP, 'ctl')
ctl.par.name0, ctl.par.name1 = 'n', 'r'


def table(name, npy, w2=w2, HOME=HOME):
    t = w2.create(scriptTOP, name)
    t.par.format = 'rgba32float'
    cb = w2.create(textDAT, name + '_cb')
    cb.text = f"""import numpy as np
A = np.load(r"{HOME}/{npy}", mmap_mode='r')
def onSetupParameters(scriptOp):
    return
def onPulse(par):
    return
def onCook(scriptOp):
    scriptOp.copyNumpyArray(np.array(A[[int(op('ctl')['n'])]]))
    return
"""
    t.par.callbacks = cb.path
    return t


pos = table('pos', 'pos.npy')
col = table('col', 'col.npy')

geo = w2.create(geometryCOMP, 'beads')
for c in list(geo.children):
    c.destroy()
ball = geo.create(sphereSOP, 'ball')
ball.par.type = 'mesh'
ball.par.rows, ball.par.cols = 24, 24
ball.par.radx, ball.par.rady, ball.par.radz = 1, 1, 1
ball.render, ball.display = True, True
mat = w2.create(phongMAT, 'glaze')
mat.par.diffr, mat.par.diffg, mat.par.diffb = 1, 1, 1
mat.par.ambr, mat.par.ambg, mat.par.ambb = 1, 1, 1
mat.par.specr, mat.par.specg, mat.par.specb = 0.28, 0.28, 0.28
mat.par.shininess = 42
geo.par.material = mat.path
geo.par.instancing = True
geo.par.instancecountmode = 'oplength'
geo.par.instanceop = pos.path
geo.par.instancetx, geo.par.instancety, geo.par.instancetz = 'r', 'g', 'b'
geo.par.instancesx, geo.par.instancesy, geo.par.instancesz = 'a', 'a', 'a'
geo.par.instancecolorop = col.path
geo.par.instancer, geo.par.instanceg, geo.par.instanceb = 'r', 'g', 'b'

cam = w2.create(cameraCOMP, 'cam')
cam.par.fov = 26
cam.par.tz = 960 / tan(radians(13))
cam.par.near, cam.par.far = 10, 12000
sun = w2.create(lightCOMP, 'sun')
sun.par.lighttype = 'distant'
sun.par.rx, sun.par.ry = -42, 28
sun.par.dimmer = 0.72
fill = w2.create(ambientlightCOMP, 'fill')
fill.par.dimmer = 0.42

render = w2.create(renderTOP, 'render')
render.par.camera, render.par.geometry = cam.path, geo.path
render.par.lights = sun.path + ' ' + fill.path
render.par.outputresolution = 'custom'
render.par.resmult = False
render.par.resolutionw, render.par.resolutionh = 1920 * K, 1080 * K
render.par.antialias = 'aa8'
render.par.bgcolora = 0
render.par.format = 'rgba16float'

soft = w2.create(blurTOP, 'soft')
soft.inputConnectors[0].connect(render)
soft.par.size = 26 * K

d = w2.create(textDAT, 'final_px')
d.text = """
uniform float uR;
out vec4 fragColor;
float ease(float x) {
    x = clamp(x, 0.0, 1.0);
    return x * x * x * (x * (6.0 * x - 15.0) + 10.0);
}
void main() {
    vec4 a = texture(sTD2DInputs[0], vUV.st);
    float shade = texture(sTD2DInputs[1], vUV.st + vec2(-0.007, 0.016)).a;
    vec2 p = (vUV.st - 0.5) * vec2(1920.0, 1080.0);
    vec3 bg = mix(vec3(17.0, 17.0, 19.0) / 255.0, vec3(237.0, 235.0, 228.0) / 255.0 * (1.0 - 0.3 * shade), ease((uR - length(p)) / 280.0));
    fragColor = vec4(bg * (1.0 - a.a) + a.rgb, 1.0);
}
"""
final = w2.create(glslTOP, 'final')
final.par.pixeldat = d.path
final.par.outputresolution = 'custom'
final.par.resmult = False
final.par.resolutionw, final.par.resolutionh = 1920 * K, 1080 * K
final.par.format = 'rgba8fixed'
final.inputConnectors[0].connect(render)
final.inputConnectors[1].connect(soft)
final.par.vec0name = 'uR'
final.par.vec0valuex.expr = "op('ctl')['r']"
out = w2.create(nullTOP, 'out')
out.inputConnectors[0].connect(final)

rec = w2.create(executeDAT, 'rec')
rec.text = f"""import numpy as np
R = np.load(r"{HOME}/light.npy")
state = dict(n=-1, end=0, dir='')
def show(n):
    op('ctl').par.value0 = n
    op('ctl').par.value1 = float(R[n])
def begin(first, last, folder):
    state.update(n=first, end=last, dir=folder)
    show(first)
def onFrameStart(frame):
    if state['n'] >= 0:
        show(state['n'])
    return
def onFrameEnd(frame):
    if state['n'] >= 0:
        op('out').save(state['dir'] + '/w2_%04d.png' % state['n'])
        state['n'] += 1
        if state['n'] > state['end']:
            state['n'] = -1
    return
"""
rec.par.framestart = True
rec.par.frameend = True
rec.par.active = True

for x, name in enumerate(['ctl', 'pos', 'pos_cb', 'col', 'col_cb', 'beads', 'glaze', 'cam', 'sun', 'fill', 'render', 'soft', 'final_px', 'final', 'out', 'rec']):
    w2.op(name).nodeX, w2.op(name).nodeY = x * 170, 0
print('errors', {c.name: (c.errors(), c.warnings()) for c in w2.children if c.errors() or c.warnings()})
