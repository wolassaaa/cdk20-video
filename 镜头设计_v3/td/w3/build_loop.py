# HKBU SCIE1007 coursework science video. 4-07 in TouchDesigner: a few dots go round the design loop, then more and faster, until they blur into the ring W3 opens on. Copies the W3 network, so run build_w3.py first. Runs inside TouchDesigner.
from math import log
K = 2                     # 1 is 1080p, 2 is 4K
FULL = 24.0               # seconds until the ring reaches W3's speed
RATE = (0.08, 1.5)        # turns per second, start and end
ALL = 22.0                # seconds until all 8,918 dots are on the ring

root = op('/project1')
old = root.op('loop')
if old:
    old.destroy()
loop = root.copy(op('/project1/w3'), name='loop')
for c in loop.findChildren():
    for p in c.pars():
        if p.mode == ParMode.CONSTANT and isinstance(p.val, str) and p.val.startswith('/project1/w3/'):
            p.val = p.val.replace('/project1/w3/', '/project1/loop/')

POS = """
uniform vec4 uA;
out vec4 fragColor;
void main() {
    int i = int(gl_FragCoord.x);
    vec4 s = texelFetch(sTD2DInputs[0], ivec2(i, 0), 0);
    float t = uA.x, turn = uA.y, R = uA.z, all = uA.w;
    float h = fract(sin(float(i) * 12.9898) * 43758.5453);
    float born = all * log(1.0 + float(i)) / log(8918.0);
    float a = s.b + turn;
    float r = R + (h - 0.5) * 26.0 * smoothstep(0.0, 20.0, t);
    float size = clamp((t - born) / 0.4, 0.0, 1.0) * mix(11.0, 3.4, smoothstep(2.0, 16.0, t));
    fragColor = vec4(cos(a) * r, sin(a) * r, size, smoothstep(14.0, 24.0, t));
}
"""
pos = loop.op('pos')
loop.op('pos_px').text = POS
k = log(RATE[1] / RATE[0]) / FULL
pos.par.vec0valuey.expr = f"6.2831853 * ({RATE[0]} / {k} * (math.exp({k} * min(op('ctl')['t'], {FULL})) - 1) + {RATE[1]} * max(op('ctl')['t'] - {FULL}, 0))"
pos.par.vec0valuez, pos.par.vec0valuew = 262, ALL
for n in ('render', 'trail', 'final'):
    loop.op(n).par.resolutionw, loop.op(n).par.resolutionh = 1920 * K, 1080 * K
loop.op('rec').text = loop.op('rec').text.replace('w3_%04d', 'loop_%04d')

print('errors', {c.name: (c.errors(), c.warnings()) for c in loop.children if c.errors() or c.warnings()})
