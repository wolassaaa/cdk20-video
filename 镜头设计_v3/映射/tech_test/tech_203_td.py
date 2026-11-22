# HKBU SCIE1007 课程作业的科普视频：技术选型小测试（11-17）TouchDesigner 一方。在 TD 里跑（td/scripts/tdc.py run 本文件）。
# 2-03 一句：TD 擅长的层 = 随词生长的生成式墨晕底纹（透明底，垫在三维物件后面）。
# 所有时间读 映射/keys/2-03.json：事件帧号写进着色器常量，着色器只吃一个输入"段内帧号 F"，纯函数、无反馈，
# 所以离线逐帧可重复。Movie File Out 出 PNG 序列（RGBA），project.realTime=False 逐帧不丢。
import json

KEYS = r"D:/。hkbu/molecular science/镜头设计_v3/映射/keys/2-03.json"
try:
    OUT = TECH_OUT                          # 第二遍（确定性对比）前面先写 TECH_OUT = "..."
except NameError:
    OUT = "G:/cdk20/work/tech_test/td/run_a"
K = json.load(open(KEYS, encoding="utf-8"))
E = {e["id"]: e for e in K["events"]}
LEN = K["len_f"]

V = {}                      # TD 的 run 用 exec，函数里看不到这里的全局名，所以不写函数
for e in K["events"]:
    V[e["id"]] = "vec3(%d.0, %d.0, %d.0)" % (e["f_start"], e["f_land"], e["f_end"])

FRAG = """
uniform float uF;
out vec4 fragColor;
const vec3 RUN = %s, CAV = %s, TAG = %s, CDK = %s, LIV = %s, CAN = %s;
const float LEN = %d.0;
float hash(vec2 p){ p = 50.0*fract(p*0.3183099 + vec2(0.71, 0.113)); return fract(p.x*p.y*(p.x + p.y)); }   // 不用 sin 哈希：显卡上 sin 大数精度差，会出方块
float noise(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f);
  return mix(mix(hash(i), hash(i+vec2(1,0)), u.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), u.x), u.y); }
float fbm(vec2 p){ float s = 0.0, a = 0.5; for (int k = 0; k < 6; k++){ s += a*noise(p); p = p*2.03 + 7.1; a *= 0.5; } return s; }
float prog(vec3 e, float f){ return smoothstep(e.x, e.y, f); }                  // 起动→落点
float sus(vec3 e, float f){ return e.z > e.y ? clamp((f - e.y)/(e.z - e.y), 0.0, 1.0) : step(e.y, f); }
// 墨晕：中心 c、半径 r，边缘被 fbm 扭曲
float bloom(vec2 p, vec2 c, float r, float t, float seed){
  vec2 q = (p - c) / max(r, 1e-3);
  float w = fbm(q*2.2 + seed + vec2(0.0, t*0.15));
  float d = length(q) + (w - 0.5)*0.9;
  return smoothstep(1.0, 0.55, d) * (0.55 + 0.45*fbm(q*5.0 + seed*3.0 - t*0.2));
}
void main(){
  vec2 p = vUV.st * vec2(16.0/9.0, 1.0);
  float f = uF, t = f/60.0;
  vec3 col = vec3(0.0); float a = 0.0;
  // one：骨白淡晕（托槽位置后面）
  float b0 = bloom(p, vec2(1.36, 0.62), 0.16 + 0.06*prog(CAV,f), t, 1.0) * prog(CAV, f) * 0.35;
  col += vec3(0.93, 0.90, 0.85) * b0; a += b0;
  // CDK20：克莱因蓝墨晕长开，持续到 CDK20 说完后仍慢慢扩
  float g = prog(CDK, f);
  float b1 = bloom(p, vec2(1.38, 0.64), 0.05 + 0.24*g + 0.05*clamp((f - CDK.y)/(LEN - CDK.y), 0.0, 1.0), t, 4.0) * g;
  col = mix(col, vec3(0.12, 0.25, 0.75), b1*0.85); a = max(a, b1*0.85);
  // liver：暗红褐小晕；cancer：红色灌满到句尾
  float l = prog(LIV, f), c = prog(CAN, f) * (0.6 + 0.4*sus(CAN, f));
  float b2 = bloom(p, vec2(1.20, 0.30), 0.06 + 0.07*l + 0.10*c, t, 9.0) * max(l*0.45, c);
  col = mix(col, mix(vec3(0.35, 0.12, 0.10), vec3(0.70, 0.15, 0.12), c), b2*0.9); a = max(a, b2*0.9);
  // answer → study：一条红丝从左往右长（流道）
  float r = 0.15*prog(RUN, f) + 0.85*sus(RUN, f);
  float x0 = 0.95, x1 = 0.95 + 0.75*r;
  float yy = 0.215 + 0.008*(fbm(vec2(p.x*6.0, t)) - 0.5);
  float th = smoothstep(0.006, 0.0, abs(p.y - yy)) * step(x0, p.x) * smoothstep(x1, x1 - 0.02, p.x) * step(0.001, r);
  col = mix(col, vec3(0.70, 0.15, 0.12), th); a = max(a, th);
  fragColor = TDOutputSwizzle(vec4(col * a, a));          // 预乘 alpha
}
""" % (V["runner_flow"], V["cavity_one"], V["tag_case"], V["part_cdk20"], V["liver_in"], V["cancer_red"], LEN)

root = op('/project1')
old = root.op('tech203')
if old:
    old.destroy()
c = root.create(baseCOMP, 'tech203')
src = c.create(textDAT, 'frag'); src.text = FRAG
g = c.create(glslTOP, 'ink')
g.par.pixeldat = src.path
g.par.outputresolution = 'custom'; g.par.resolutionw = 1920; g.par.resolutionh = 1080
g.par.format = 'rgba8fixed'
g.par.uniname0 = 'uF'; g.par.value0x = 0
mfo = c.create(moviefileoutTOP, 'mfo')
mfo.inputConnectors[0].connect(g)
mfo.par.type = 'imagesequence'; mfo.par.imagefiletype = 'png'
# 文件名直接取着色器正在用的段内帧号：哪一帧存成哪个文件一目了然，不靠 TD 的自动编号
mfo.par.file.expr = "'%s/td_' + str(int(op('ink').par.value0x)).zfill(4) + '.png'" % OUT
mfo.par.record = False
ctl = c.create(executeDAT, 'drv')
ctl.text = """
import time
S = dict(n=-1, end=0, t0=0.0, t1=0.0)
def go(end):
    S.update(n=0, end=end, t0=time.perf_counter())
    op('ink').par.value0x = 0
    op('mfo').par.record = True
def onFrameStart(frame):
    if S['n'] >= 0:
        op('ink').par.value0x = S['n']
    return
def onFrameEnd(frame):
    if S['n'] >= 0:
        S['n'] += 1
        if S['n'] > S['end']:
            op('mfo').par.record = False
            S['n'] = -1
            S['t1'] = time.perf_counter()
            print('TECH203_TD_DONE', S['t1'] - S['t0'])
        else:
            op('ink').par.value0x = S['n']
    return
"""
ctl.par.framestart = True; ctl.par.frameend = True; ctl.par.active = True
project.realTime = False
print('errors', g.errors(), g.warnings(), mfo.errors(), 'LEN', LEN)
