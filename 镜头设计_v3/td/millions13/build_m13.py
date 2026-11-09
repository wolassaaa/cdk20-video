# HKBU SCIE1007 coursework science video. "millions -> 13" dot sample (about 8 s, 1080p 30 fps): 2,097,152 tiny grey dots on the bone-white table, four slow waves each screen most of them
# out (they fade and sink, no flash), and what is left grows a little darker and larger each time; after the fourth wave exactly 13 Klein blue ink dots stay. A drawing, not a measurement.
# Data: gen_millions13.py writes C:/render_tmp/td_m13/m13_data.npy (one table texel = one dot). Runs inside TouchDesigner:
#   python td/scripts/tdc.py run td/millions13/build_m13.py, then op('/project1/m13/rec').module.begin(0, 239, 'C:/render_tmp/td_m13/f')
root = op('/project1')
old = root.op('m13')
if old:
    old.destroy()
m = root.create(baseCOMP, 'm13')

ctl = m.create(constantCHOP, 'ctl')
ctl.par.name0 = 'n'
ctl.par.value0 = 0

# the dot table
data = m.create(scriptTOP, 'data')
cb = m.create(textDAT, 'data_cb')
cb.text = """
import numpy as np
def onCook(scriptOp):
    scriptOp.copyNumpyArray(np.load('C:/render_tmp/td_m13/m13_data.npy'))
    return
"""
data.par.callbacks = cb.path

WAVES = """
// the four waves: where each starts on the table (px from the centre, y up), when, and how long it takes to cross the whole table
const vec2 O[4] = vec2[](vec2(-1150.0, -650.0), vec2(1150.0, 600.0), vec2(-1100.0, 700.0), vec2(1150.0, -550.0));
const float T0[4] = float[](0.55, 1.95, 3.35, 4.75);
const float DUR = 1.45;
const float FADE = 0.85;
float vmax(int k) {
    float d = 0.0;
    d = max(d, length(vec2(-960.0, -540.0) - O[k]));
    d = max(d, length(vec2(960.0, -540.0) - O[k]));
    d = max(d, length(vec2(-960.0, 540.0) - O[k]));
    d = max(d, length(vec2(960.0, 540.0) - O[k]));
    return d / DUR;
}
"""

STATE = WAVES + """
uniform vec4 uA;   // time in s
out vec4 fragColor;
void main() {
    vec4 d = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0);
    vec2 p = d.xy;
    float stg = d.z, rnd = d.w, t = uA.x;
    float R[5] = float[](0.52, 0.95, 1.8, 3.2, 7.4);
    float r = R[0] * (0.8 + 0.4 * rnd);
    float e = 0.0;
    for (int k = 0; k < 4; k++) {
        float Tk = T0[k] + length(p - O[k]) / vmax(k);
        float pk = smoothstep(Tk, Tk + FADE, t);
        if (float(k) < stg) r = mix(r, R[k + 1] * (0.85 + 0.3 * rnd * (k < 3 ? 1.0 : 0.0)), pk);
        else if (float(k) == floor(stg + 0.5)) e = pk;
    }
    float sink = 7.0 * e;
    r *= 1.0 - 0.55 * e;
    fragColor = vec4(p.x, p.y - sink, r, 0.0);
}
"""

COLOR = WAVES + """
uniform vec4 uA;
out vec4 fragColor;
void main() {
    vec4 d = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0);
    vec2 p = d.xy;
    float stg = d.z, rnd = d.w, t = uA.x;
    float G[5] = float[](0.50, 0.42, 0.34, 0.26, 0.0);
    float A[5] = float[](0.22, 0.55, 0.78, 0.92, 1.0);
    vec3 col = vec3(G[0]);
    float a = A[0] * (0.85 + 0.3 * rnd);
    float e = 0.0, g3 = 0.0;
    for (int k = 0; k < 4; k++) {
        float Tk = T0[k] + length(p - O[k]) / vmax(k);
        float pk = smoothstep(Tk, Tk + FADE, t);
        if (float(k) < stg) { col = mix(col, vec3(G[k + 1]), pk); a = mix(a, A[k + 1], pk); if (k == 3) g3 = pk; }
        else if (float(k) == floor(stg + 0.5)) e = pk;
    }
    col = mix(col, vec3(0.0, 0.184, 0.655), g3);                      // #002FA7: the last 13
    float appear = smoothstep(0.0, 0.7, t);                            // the field comes up out of the bone paper, no cut
    fragColor = vec4(col, a * (1.0 - e) * appear);
}
"""

FINAL = WAVES + """
uniform vec4 uA;
out vec4 fragColor;
void main() {
    vec2 pix = vec2(gl_FragCoord.x - 960.0, gl_FragCoord.y - 540.0);
    float t = uA.x;
    vec4 dots = texture(sTD2DInputs[0], vUV.st);
    vec3 bone = vec3(0.929, 0.922, 0.894);                              // #EDEBE4
    vec3 ikb = vec3(0.0, 0.184, 0.655);
    float band = 0.0, hair = 0.0;
    for (int k = 0; k < 4; k++) {                                       // each wave front: a wide faint band and a hair line
        float v = vmax(k), s = t - T0[k];
        float gate = smoothstep(0.0, 0.35, s) * (1.0 - smoothstep(DUR - 0.2, DUR + 0.3, s));
        float x = length(pix - O[k]) - v * s;
        band += gate * exp(-(x * x) / (2.0 * 36.0 * 36.0));
        hair += gate * exp(-(x * x) / (2.0 * 1.0 * 1.0));
    }
    vec3 base = mix(bone, ikb, 0.05 * band + 0.14 * hair);
    fragColor = TDOutputSwizzle(vec4(dots.rgb + base * (1.0 - dots.a), 1.0));
}
"""


def glsl(name, code, fmt, w, h, inputs, m=m):          # exec in TD does not see module names inside functions
    d = m.create(textDAT, name + '_px')
    d.text = code
    g = m.create(glslTOP, name)
    g.par.pixeldat = d.path
    g.par.outputresolution = 'custom'
    g.par.resmult = False
    g.par.resolutionw, g.par.resolutionh = w, h
    g.par.format = fmt
    for i, x in enumerate(inputs):
        g.inputConnectors[i].connect(x)
    g.seq.vec.numBlocks = 1
    g.par.vec0name = 'uA'
    g.par.vec0valuex.expr = "op('ctl')['n'] / 30.0"
    return g


glsl('stA', STATE, 'rgba32float', 2048, 1024, [data])
glsl('stB', COLOR, 'rgba32float', 2048, 1024, [data])

# one small round dot, instanced 2,097,152 times: position and size from stA, colour from stB
geo = m.create(geometryCOMP, 'geo')
for c in list(geo.children):
    c.destroy()
circ = geo.create(circleSOP, 'circle1')
circ.par.divs = 10
circ.par.radx = circ.par.rady = 1.0
circ.par.type = 'poly'
o = geo.create(outSOP, 'out1')
o.inputConnectors[0].connect(circ)
o.display = True
o.render = True

mat = m.create(constantMAT, 'mat')
mat.par.blending = True
mat.par.srcblend = 'one'
mat.par.destblend = 'omsa'
mat.par.depthtest = False
geo.par.material = mat.path
geo.par.instancing = True
geo.par.instancecountmode = 'manual'
geo.par.numinstances = 2048 * 1024
geo.par.instanceop = m.op('stA').path
geo.par.instancetop = m.op('stA').path
geo.par.instancetx = 'r'
geo.par.instancety = 'g'
geo.par.instancesop = m.op('stA').path
geo.par.instancesx = 'b'
geo.par.instancesy = 'b'
geo.par.instancecolormode = 'replace'
geo.par.instancecolorop = m.op('stB').path
geo.par.instancer, geo.par.instanceg, geo.par.instanceb, geo.par.instancea = 'r', 'g', 'b', 'a'

cam = m.create(cameraCOMP, 'cam')
cam.par.projection = 'ortho'
cam.par.orthowidth = 1920
cam.par.tz = 10
rn = m.create(renderTOP, 'render')
rn.par.camera = cam.path
rn.par.geometry = geo.path
rn.par.outputresolution = 'custom'
rn.par.resmult = False
rn.par.resolutionw, rn.par.resolutionh = 1920, 1080
rn.par.bgcolorr = rn.par.bgcolorg = rn.par.bgcolorb = 0
rn.par.bgcolora = 0
rn.par.antialias = 'aa4'

final = glsl('final', FINAL, 'rgba8fixed', 1920, 1080, [rn])
out = m.create(nullTOP, 'out')
out.inputConnectors[0].connect(final)

rec = m.create(executeDAT, 'rec')
rec.text = """
state = dict(n=-1, end=0, dir='')
def begin(first, last, folder):
    state.update(n=first, end=last, dir=folder)
    op('ctl').par.value0 = first
def onFrameStart(frame):
    if state['n'] >= 0:
        op('ctl').par.value0 = state['n']
    return
def onFrameEnd(frame):
    if state['n'] >= 0:
        op('out').save(state['dir'] + '/m13_%04d.png' % state['n'])
        state['n'] += 1
        if state['n'] > state['end']:
            state['n'] = -1
    return
"""
rec.par.framestart = True
rec.par.frameend = True
rec.par.active = True

for x, name in enumerate(['ctl', 'data_cb', 'data', 'stA', 'stB', 'geo', 'mat', 'cam', 'render', 'final', 'out', 'rec']):
    m.op(name).nodeX, m.op(name).nodeY = x * 170, 0
project.cookRate = 240
print('errors', {c.name: (c.errors(), c.warnings()) for c in m.children if c.errors() or c.warnings()})
print('instances', geo.par.numinstances.eval(), m.op('stA').width, m.op('stA').height)
