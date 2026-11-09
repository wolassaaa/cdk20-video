# HKBU SCIE1007 coursework science video. W3 explored again (11-09), direction C in TouchDesigner: over a still of the lock (Blender, w3c in fusion/w3/bl_w3x.py,
# A's lock and camera, no key) thousands of key outlines flash through the one place where the key hangs, twenty new ones every frame, like a computer trying them;
# on every beat they all pull together into one Klein blue key, then scatter again. Never inside the keyhole: every outline's tip sits on the hovering key's tip.
# At 20 a frame and 30 fps, 15 s is about 8,900 outlines, the paper's 8,918 designs (here only a drawing: the outlines are random, not the designs).
# Runs inside TouchDesigner: python td/scripts/tdc.py run td/w3x/build_w3x.py, then op('/project1/w3x/rec').module.begin(0, 179, '<folder>').
import json

SCREEN = json.load(open("C:/render_tmp/w3x/c_plate/screen.json"))     # where A's key sits on screen: tip (px from the top left), px per mm
PLATE = "C:/render_tmp/w3x/c_plate/w3c_0000.png"
BEAT = 60.0 / 121.0          # Take My Breath, bar 104 on frame 0
M = 20                       # outlines a frame

root = op('/project1')
old = root.op('w3x')
if old:
    old.destroy()
w3 = root.create(baseCOMP, 'w3x')

ctl = w3.create(constantCHOP, 'ctl')
ctl.par.name0 = 'n'
ctl.par.value0 = 0

KEYS = """
uniform vec4 uA;   // frame (30 fps), px per mm, outlines a frame, beat in s
uniform vec4 uB;   // the tip's x and y in px from the top left
out vec4 fragColor;

float h(float n) { return fract(sin(n * 12.9898 + 4.1) * 43758.5453); }
float sdBox(vec2 p, vec2 c, vec2 b) { vec2 d = abs(p - c) - b; return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0); }
float sdHex(vec2 p, float r) {
    const vec3 k = vec3(-0.866025404, 0.5, 0.577350269);
    p = abs(p.yx);
    p -= 2.0 * min(dot(k.xy, p), 0.0) * k.xy;
    p -= vec2(clamp(p.x, -k.z * r, k.z * r), r);
    return length(p) * sign(p.y);
}

// One key in mm: u runs up the key from its tip, v across it, the cuts on +v (screen right, as A's key). Every number is mixed between this outline's own
// random value (seed s) and the beat's key (seed sb) by c, so at c = 1 every outline is the beat's key.
float keySD(vec2 p, float s, float sb, float c) {
    #define R(k) mix(h(s * 37.0 + k), h(sb * 37.0 + k), c)
    float L = 34.0 + 12.0 * R(1.0);
    float W = 9.0 + 3.0 * R(2.0);
    float d = sdBox(p, vec2(L * 0.5, 0.0), vec2(L * 0.5, W * 0.5));
    vec2 a = vec2(0.0, -0.6);
    vec2 dir = normalize(vec2(6.5, -W * 0.5 + 0.6));
    d = max(d, dot(p - a, vec2(dir.y, -dir.x)));                         // the tip's long bevel, on the uncut edge
    d = max(d, dot(p - vec2(0.0, 0.6), normalize(vec2(-1.0, 0.75))));     // and a short one on the cut edge
    float N = 3.0 + floor(R(3.0) * 4.99);
    for (int i = 0; i < 7; i++) {
        if (float(i) >= N) break;
        float ui = mix(7.5, L - 8.0, (float(i) + 0.5) / N);
        float dep = 1.0 + 5.0 * R(10.0 + float(i));
        float tw = 1.5 - 0.35 * clamp((p.y - W * 0.5) / max(dep, 0.1), 0.0, 1.0);          // each cut narrows toward its point
        d = min(d, sdBox(p, vec2(ui, W * 0.5 + dep * 0.5), vec2(tw, dep * 0.5)));
    }
    d = min(d, sdBox(p, vec2(L - 0.25, -W * 0.5 - 1.1), vec2(4.25, 1.11)));          // the shoulder
    float RB = 10.5 + 3.5 * R(20.0);
    vec2 q = p - vec2(L + 2.5 + RB, 0.0);
    float kind = floor(R(21.0) * 2.99);
    float bow = kind < 1.0 ? length(q) - RB : kind < 2.0 ? sdHex(q, RB * 0.9) : sdBox(q, vec2(0.0), vec2(RB * 0.82)) - RB * 0.12;
    bow = max(bow, -(length(q) - 4.5));
    return min(d, bow);
}

void main() {
    float n = uA.x, ppm = uA.y, Mn = uA.z, beat = uA.w;
    float t = n / 30.0;
    vec2 pix = vec2(gl_FragCoord.x, 1080.0 - gl_FragCoord.y);
    vec2 p = vec2(uB.y - pix.y, pix.x - uB.x) / ppm;           // key space in mm
    float ph = t / beat;
    float db = abs(fract(ph + 0.5) - 0.5) * beat;               // seconds to the nearest beat
    float c = smoothstep(0.13, 0.0, db);
    c = c * c * (3.0 - 2.0 * c);
    float sb = floor(ph + 0.5) + 5000.0;
    float ink = 0.0;
    float fill = 0.0;
    for (int j = 0; j < 32; j++) {
        if (float(j) >= Mn) break;
        float sd = keySD(p, n * Mn + float(j), sb, c);
        float px = abs(sd) * ppm;
        ink = 1.0 - (1.0 - ink) * (1.0 - 0.42 * (1.0 - smoothstep(0.35, 1.25, px)));
        if (j == 0) fill = step(sd, 0.0);
    }
    float blue = smoothstep(0.75, 1.0, c);
    vec3 inkc = mix(vec3(0.07, 0.07, 0.08), vec3(0.0, 0.184, 0.655), blue);        // #002FA7 as the outlines meet
    float a = clamp(ink * (1.0 + 1.4 * blue), 0.0, 1.0);
    float f = 0.10 * blue * fill;
    vec3 col = inkc * a + vec3(0.0, 0.184, 0.655) * f * (1.0 - a);
    fragColor = TDOutputSwizzle(vec4(col, a + f * (1.0 - a)));
}
"""

TRAIL = """
uniform vec4 uDecay;
out vec4 fragColor;
void main() {
    vec4 cur = texture(sTD2DInputs[0], vUV.st);
    vec4 old = texture(sTD2DInputs[1], vUV.st) * uDecay.x;
    fragColor = TDOutputSwizzle(cur + old * (1.0 - cur.a));
}
"""

FINAL = """
out vec4 fragColor;
void main() {
    vec4 lines = texture(sTD2DInputs[0], vUV.st);
    vec3 plate = texture(sTD2DInputs[1], vUV.st).rgb;
    fragColor = TDOutputSwizzle(vec4(plate * (1.0 - lines.a) + lines.rgb, 1.0));
}
"""


def glsl(name, code, fmt, inputs, w3=w3):          # exec in TD does not see module names inside functions
    d = w3.create(textDAT, name + '_px')
    d.text = code
    g = w3.create(glslTOP, name)
    g.par.pixeldat = d.path
    g.par.outputresolution = 'custom'
    g.par.resmult = False
    g.par.resolutionw, g.par.resolutionh = 1920, 1080
    g.par.format = fmt
    for i, x in enumerate(inputs):
        g.inputConnectors[i].connect(x)
    return g


keys = glsl('keys', KEYS, 'rgba16float', [])
keys.seq.vec.numBlocks = 2
keys.par.vec0name = 'uA'
keys.par.vec0valuex.expr = "op('ctl')['n']"
keys.par.vec0valuey, keys.par.vec0valuez, keys.par.vec0valuew = SCREEN["ppm"], M, BEAT
keys.par.vec1name = 'uB'
keys.par.vec1valuex, keys.par.vec1valuey = SCREEN["tip"][0], SCREEN["tip"][1]

fb = w3.create(feedbackTOP, 'fb')
fb.inputConnectors[0].connect(keys)
trail = glsl('trail', TRAIL, 'rgba16float', [keys, fb])
trail.par.vec0name = 'uDecay'
trail.par.vec0valuex = 0.6
fb.par.top = trail.path

plate = w3.create(moviefileinTOP, 'plate')
plate.par.file = PLATE
final = glsl('final', FINAL, 'rgba8fixed', [trail, plate])
out = w3.create(nullTOP, 'out')
out.inputConnectors[0].connect(final)

rec = w3.create(executeDAT, 'rec')
rec.text = """
state = dict(n=-1, end=0, dir='')
def begin(first, last, folder):
    op('fb').par.resetpulse.pulse()
    state.update(n=first, end=last, dir=folder)
    op('ctl').par.value0 = first
def onFrameStart(frame):
    if state['n'] >= 0:
        op('ctl').par.value0 = state['n']
    return
def onFrameEnd(frame):
    if state['n'] >= 0:
        op('out').save(state['dir'] + '/w3c_%04d.png' % state['n'])
        state['n'] += 1
        if state['n'] > state['end']:
            state['n'] = -1
    return
"""
rec.par.framestart = True
rec.par.frameend = True
rec.par.active = True

for x, name in enumerate(['ctl', 'keys_px', 'keys', 'fb', 'trail_px', 'trail', 'plate', 'final_px', 'final', 'out', 'rec']):
    w3.op(name).nodeX, w3.op(name).nodeY = x * 170, 0
project.cookRate = 240
print('errors', {c.name: (c.errors(), c.warnings()) for c in w3.children if c.errors() or c.warnings()})
