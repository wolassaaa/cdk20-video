# HKBU SCIE1007 coursework science video. W5 end card, the layer behind the type: on bone-white paper, very faint Klein blue dots on a tilted lattice and a few hair lines,
# flowing very slowly. No full-screen effect, nothing blinks; the type is on top (W5_end_4k60_1.mp4, 33 s, 60 fps), so the contrast stays low.
# Runs inside TouchDesigner: python td/scripts/tdc.py run td/w5/build_w5.py, then op('/project1/w5bg/rec').module.begin(first, last, '<folder>'). 4K frames, 60 fps.
root = op('/project1')
old = root.op('w5bg')
if old:
    old.destroy()
w5 = root.create(baseCOMP, 'w5bg')

ctl = w5.create(constantCHOP, 'ctl')
ctl.par.name0 = 'n'
ctl.par.value0 = 0

BG = """
uniform vec4 uA;   // time in s, dot alpha, line alpha, pixels per 4K frame height / 2160
out vec4 fragColor;

vec2 h2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}
float gn(vec2 p) {                                   // gradient noise, about -1 to 1
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    return 1.4 * mix(mix(dot(h2(i), f), dot(h2(i + vec2(1, 0)), f - vec2(1, 0)), u.x),
                     mix(dot(h2(i + vec2(0, 1)), f - vec2(0, 1)), dot(h2(i + vec2(1, 1)), f - vec2(1, 1)), u.x), u.y);
}

void main() {
    float t = uA.x, k = uA.w;
    vec2 pix = vec2(gl_FragCoord.x, 2160.0 * k - gl_FragCoord.y) / k;      // 4K pixels from the top left
    // the paper slides slowly, and a wide slow field bends it a little
    vec2 q = pix + vec2(9.0, -6.0) * t;
    q += 34.0 * vec2(gn(q * 0.0011 + vec2(0.0, t * 0.045)), gn(q * 0.0011 + vec2(7.3, 3.1 + t * 0.045)));
    // dots on a tilted square lattice; how big each one is follows another slow field, so patches of bigger dots drift across
    const float S = 58.0;
    float ca = cos(0.31), sa = sin(0.31);
    vec2 r = vec2(ca * q.x - sa * q.y, sa * q.x + ca * q.y);
    vec2 c = (floor(r / S) + 0.5) * S;
    float n = gn(c * 0.0014 + vec2(t * 0.035, 11.0 - t * 0.02));
    float rad = 4.6 * smoothstep(-0.35, 0.55, n);
    float d = length(r - c);
    float dots = (1.0 - smoothstep(rad - 0.9, rad + 0.9, d)) * step(0.35, rad);
    // a few hair lines: the contours of the field that moves under the dots
    float f = gn(q * 0.00085 + vec2(5.0 + t * 0.03, -t * 0.02)) * 5.0;
    float g = abs(fract(f) - 0.5) / max(fwidth(f), 1e-5);                  // pixels from the nearest contour
    float lines = 1.0 - smoothstep(0.6, 1.6, g * 1.0);
    lines *= smoothstep(-0.45, 0.1, gn(q * 0.0007 + 20.0));                  // lines only where this second field is up
    float a = clamp(uA.y * dots + uA.z * lines, 0.0, 1.0);
    vec3 bone = vec3(0.929, 0.922, 0.894);                                  // #EDEBE4
    vec3 ikb = vec3(0.0, 0.184, 0.655);                                     // #002FA7
    fragColor = TDOutputSwizzle(vec4(mix(bone, ikb, a), 1.0));
}
"""

px = w5.create(textDAT, 'bg_px')
px.text = BG
bg = w5.create(glslTOP, 'bg')
bg.par.pixeldat = px.path
bg.par.outputresolution = 'custom'
bg.par.resmult = False
bg.par.resolutionw, bg.par.resolutionh = 3840, 2160
bg.par.format = 'rgba8fixed'
bg.seq.vec.numBlocks = 1
bg.par.vec0name = 'uA'
bg.par.vec0valuex.expr = "op('ctl')['n'] / 60.0"
bg.par.vec0valuey = 0.22
bg.par.vec0valuez = 0.12
bg.par.vec0valuew = 1.0                          # 4K; the preview scales it

out = w5.create(nullTOP, 'out')
out.inputConnectors[0].connect(bg)

rec = w5.create(executeDAT, 'rec')
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
        op('out').save(state['dir'] + '/bg_%04d.png' % state['n'])
        state['n'] += 1
        if state['n'] > state['end']:
            state['n'] = -1
    return
"""
rec.par.framestart = True
rec.par.frameend = True
rec.par.active = True

for x, name in enumerate(['ctl', 'bg_px', 'bg', 'out', 'rec']):
    w5.op(name).nodeX, w5.op(name).nodeY = x * 170, 0
project.cookRate = 240
print('errors', {c.name: (c.errors(), c.warnings()) for c in w5.children if c.errors() or c.warnings()})
