# HKBU SCIE1007 coursework science video. 4-10 in TouchDesigner: copies the W3 network and changes what the dots do. Run build_w3.py first. Runs inside TouchDesigner.
HOME = "D:/。hkbu/molecular science/镜头设计_v3/td/w3"
K = 2                     # 1 is 1080p, 2 is 4K
SWEEP = (5.6, 13.6)       # "each key gets tried in a virtual lock... scores the fit"
GROUP = (14.6, 17.2)      # "similar designs get grouped"
PICK, SEVEN = 17.4, 20.8  # "54 make the shortlist", "chemists pick just seven"

root = op('/project1')
old = root.op('wall')
if old:
    old.destroy()
wall = root.copy(op('/project1/w3'), name='wall')
for c in wall.findChildren():
    for p in c.pars():
        if p.mode == ParMode.CONSTANT and isinstance(p.val, str) and p.val.startswith('/project1/w3/'):
            p.val = p.val.replace('/project1/w3/', '/project1/wall/')

CB = """import numpy as np
A = np.load(r"{}")
def onSetupParameters(scriptOp):
    return
def onPulse(par):
    return
def onCook(scriptOp):
    scriptOp.copyNumpyArray(A)
    return
"""
wall.op('seeds_cb').text = CB.format(HOME + '/wall_a.npy')
seedsb = wall.create(scriptTOP, 'seedsb')
seedsb.par.format = 'rgba32float'
cbb = wall.create(textDAT, 'seedsb_cb')
cbb.text = CB.format(HOME + '/wall_b.npy')
seedsb.par.callbacks = cbb.path

POS = """
uniform vec4 uA;
uniform vec4 uB;
out vec4 fragColor;
float ease(float x) {
    x = clamp(x, 0.0, 1.0);
    return x * x * x * (x * (6.0 * x - 15.0) + 10.0);
}
void main() {
    int i = int(gl_FragCoord.x);
    vec4 a = texelFetch(sTD2DInputs[0], ivec2(i, 0), 0);
    vec4 b = texelFetch(sTD2DInputs[1], ivec2(i, 0), 0);
    float t = uA.x, role = b.z, score = b.w;
    float h = fract(sin(float(i) * 12.9898) * 43758.5453);
    float h2 = fract(sin(float(i) * 78.233) * 12345.678);

    float sx = mix(-1060.0, 1060.0, clamp((t - uA.y) / (uA.z - uA.y), 0.0, 1.0));
    float on = step(uA.y, t);
    float band = on * step(t, uA.z) * exp(-pow((a.x - sx) / 70.0, 2.0));
    float scored = on * smoothstep(0.0, 90.0, sx - a.x);

    float e1 = ease((t - uB.x - 0.6 * h) / (uB.y - uB.x - 0.6));
    vec2 p = mix(a.xy, a.zw, e1);
    vec3 q = vec3(a.xy * 0.0032, t * 0.25 + h);
    p += 14.0 * sin(3.14159265 * e1) * vec2(TDSimplexNoise(q), TDSimplexNoise(q + vec3(17.0, 5.0, 3.0)));

    float shade = mix(1.0, 0.3 + 0.7 * score, scored);
    float size = 3.4 * (1.0 + 0.9 * band);
    if (role < 0.5) {
        shade *= mix(1.0, 0.38, ease((t - uB.z) / 1.6));
    } else {
        float e2 = ease((t - uB.z - 0.5 * h2) / 1.7);
        float c = cos(0.05 * t), s = sin(0.05 * t);
        p = mix(p, mat2(c, s, -s, c) * b.xy, e2);
        size = mix(size, 13.0, e2);
        float e3 = ease((t - uB.w) / 1.4);
        if (role < 1.5) {
            size = mix(size, 3.4, e3);
            shade = mix(shade, 0.3, e3);
        } else {
            size = mix(size, 30.0, e3);
            shade += e3;
        }
    }
    fragColor = vec4(p, size, shade);
}
"""
COL = """
out vec4 fragColor;
void main() {
    vec4 p = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0);
    vec3 bone = vec3(237.0, 235.0, 228.0) / 255.0;
    vec3 klein = vec3(0.0, 47.0, 167.0) / 255.0;
    vec3 red = vec3(232.0, 25.0, 15.0) / 255.0;
    fragColor = vec4(mix(mix(bone, klein, min(p.a, 1.0)), red, clamp(p.a - 1.0, 0.0, 1.0)), 1.0);
}
"""
pos = wall.op('pos')
wall.op('pos_px').text = POS
wall.op('col_px').text = COL
pos.inputConnectors[1].connect(seedsb)
pos.par.vec0valuey, pos.par.vec0valuez, pos.par.vec0valuew = SWEEP[0], SWEEP[1], 0
pos.par.vec1valuex, pos.par.vec1valuey, pos.par.vec1valuez, pos.par.vec1valuew = GROUP[0], GROUP[1], PICK, SEVEN
for n in ('render', 'trail', 'final'):
    wall.op(n).par.resolutionw, wall.op(n).par.resolutionh = 1920 * K, 1080 * K
wall.op('rec').text = f"""
state = dict(n=-1, end=0, dir='', warm=0)
def begin(first, last, folder):
    op('fb').par.resetpulse.pulse()
    state.update(n=first, end=last, dir=folder, warm=30)   # the trail settles before the first saved frame, so W3 cuts into this cleanly
    op('ctl').par.value0 = first / 60
def onFrameStart(frame):
    if state['n'] >= 0:
        op('ctl').par.value0 = state['n'] / 60
    return
def onFrameEnd(frame):
    if state['n'] < 0:
        return
    if state['warm'] > 0:
        state['warm'] -= 1
        return
    op('out').save(state['dir'] + '/wall_%04d.png' % state['n'])
    state['n'] += 1
    if state['n'] > state['end']:
        state['n'] = -1
    return
"""

print('errors', {c.name: (c.errors(), c.warnings()) for c in wall.children if c.errors() or c.warnings()})
