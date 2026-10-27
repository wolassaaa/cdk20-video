# Runs inside TD. Lava blood v2: the crust breaks into plates stretched along each vessel, glowing flow streaks run
# between them and heat pulses travel downstream, so it reads as blood flowing, not as cracked rock. The liver is a
# real mesh (BodyParts3D v4) in translucent wine red with a lit rim. Four pull-back keyframes, one PNG each.
def main():
    D = r"C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/tdd"
    OUT = D + "/png"
    W, H = 1920, 1080
    root = op('/project1/design') or op('/project1').create(baseCOMP, 'design')
    c = root.op('lava4') or root.create(baseCOMP, 'lava4')
    for ch in list(c.children):
        if ch.valid: ch.destroy()

    def data(nm, f):
        sc = c.create(scriptTOP, nm); sc.par.format = 'rgba32float'
        sc.par.callbacks.eval().text = ("import numpy as np\ndef onSetupParameters(s):\n    return\n"
            "def onCook(s):\n    s.copyNumpyArray(np.load(r'%s/%s').astype(np.float32))\n    return\n" % (D, f))
        return sc

    NOISE = """
vec3 h3(vec3 p){ p = vec3(dot(p,vec3(127.1,311.7,74.7)), dot(p,vec3(269.5,183.3,246.1)), dot(p,vec3(113.5,271.9,124.6)));
    return fract(sin(p)*43758.5453); }
float n3(vec3 p){ vec3 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    float a=h3(i).x, b=h3(i+vec3(1,0,0)).x, c=h3(i+vec3(0,1,0)).x, d=h3(i+vec3(1,1,0)).x;
    float e=h3(i+vec3(0,0,1)).x, g=h3(i+vec3(1,0,1)).x, k=h3(i+vec3(0,1,1)).x, l=h3(i+vec3(1,1,1)).x;
    return mix(mix(mix(a,b,f.x),mix(c,d,f.x),f.y), mix(mix(e,g,f.x),mix(k,l,f.x),f.y), f.z); }
float fbm(vec3 p){ float s=0.0, a=0.5; for(int i=0;i<5;i++){ s+=a*n3(p); p*=2.03; a*=0.5; } return s; }
float vedge(vec3 p){ vec3 i=floor(p), f=fract(p); float d1=8.0, d2=8.0;
    for(int z=-1;z<=1;z++) for(int y=-1;y<=1;y++) for(int x=-1;x<=1;x++){
        vec3 g=vec3(x,y,z); vec3 o=h3(i+g); float d=length(g+o-f);
        if(d<d1){ d2=d1; d1=d; } else if(d<d2){ d2=d; } }
    return d2-d1; }
"""
    VERT = """
out vec3 vW; out vec3 vN; out vec2 vUV; out vec3 vC; out vec3 vCN;
void main(){
    vec4 w = TDDeform(P);
    vW = w.xyz; vN = normalize(TDDeformNorm(N)); vUV = uv[0].st;
    vC = (uTDMats[TDCameraIndex()].cam * w).xyz; vCN = normalize((uTDMats[TDCameraIndex()].cam * vec4(vN, 0.0)).xyz);
    gl_Position = TDWorldToProj(w);
}"""
    # Look taken from photos of Hawaiian pahoehoe flows: mostly dark silver-grey ropy skin, incandescent orange only at
    # the flow margins, the advancing front and thin cracks.
    FRAG = """
uniform float uT;
uniform float uFront;
in vec3 vW; in vec3 vN; in vec2 vUV; in vec3 vC; in vec3 vCN;
out vec4 fragColor;
""" + NOISE + """
void main(){
    TDCheckDiscard();
    float along = vUV.x, ang = vUV.y * 6.2831853;
    vec3 ring = vec3(cos(ang), sin(ang), 0.0);
    float d = uFront - along;
    float ragged = 0.7 * n3(vec3(ring.xy * 1.5, along * 0.4)) + 0.4 * (0.5 + 0.5 * sin(ang * 2.0 + along));
    if (d < ragged) discard;
    float fresh = exp(-(d - ragged) * 0.34);            // 1 at the advancing tongue
    vec3 Lc = normalize(vec3(-0.3, 0.7, 0.6));
    if (gl_FrontFacing) {                               // looking into the open front: molten interior
        float k = n3(vec3(ring.xy * 3.0, along * 1.5));
        fragColor = TDOutputSwizzle(vec4(pow(mix(vec3(1.0, 0.09, 0.004), vec3(1.0, 0.38, 0.05), k * k), vec3(1.0 / 2.2)), 1.0));
        return;
    }
    vec3 n = normalize(vCN), V = normalize(-vC);
    float facing = abs(dot(n, V));
    float edge = smoothstep(0.55, 0.97, 1.0 - facing);                // flow margin as seen from the camera
    float f = along - uT * 0.6;
    // pahoehoe ropes: folds across the flow, bowed downstream in the middle of the channel
    float bow = 1.1 * (1.0 - abs(sin(ang * 0.5)));
    float w = fbm(vec3(f * 0.25, ring.xy * 1.2));
    float ropes = sin((f + bow) * 5.5 + w * 6.0);
    float ropes2 = sin((f + bow * 0.7) * 13.0 + w * 9.0) * 0.35;
    float ridge = 0.5 + 0.5 * (ropes + ropes2) / 1.35;
    // crust plates and the thin cracks between them
    vec3 q = vec3(f * 0.55, ring.xy * 1.6); q += 0.3 * vec3(fbm(q), fbm(q + 3.1), fbm(q + 7.7));
    float e = vedge(q);
    float heat = smoothstep(0.35, 0.8, fbm(vec3(f * 0.08, ring.xy * 0.6)));
    float crack = (1.0 - smoothstep(0.0, 0.035 + 0.07 * heat, e)) * (0.45 + 0.55 * heat);
    // silver-grey skin, lit, darker in the rope grooves, with a glassy sheen on the ridges
    float diff = max(dot(n, Lc), 0.0);
    float spec = pow(max(dot(reflect(-Lc, n), V), 0.0), 24.0) * ridge;
    float grit = fbm(q * 6.0);
    vec3 skin = mix(vec3(0.004, 0.004, 0.0045), vec3(0.16, 0.155, 0.15), ridge * (0.45 + 0.55 * grit)) * (0.4 + 0.8 * diff) + vec3(0.8) * spec * 0.4;
    // incandescence: margins, the fresh tongue, cracks, and a red underglow in the deepest grooves
    float glow = clamp(edge * (0.6 + 0.4 * heat) + crack + smoothstep(0.3, 0.95, fresh) + (1.0 - ridge) * smoothstep(0.1, 0.6, fresh) * 0.6 + (1.0 - ridge) * heat * 0.25, 0.0, 1.0);
    vec3 hot = mix(vec3(0.55, 0.03, 0.004), vec3(1.0, 0.16, 0.012), glow);
    hot = mix(hot, vec3(1.0, 0.38, 0.06), pow(glow, 8.0) * 0.8);
    vec3 col = mix(skin, hot * 1.15, glow);
    col = pow(max(col, vec3(0.0)), vec3(1.0 / 2.2));    // the render goes out linear: encode for display
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}"""
    mat = c.create(glslMAT, 'lava')
    mat.par.vdat.eval().text = VERT
    mat.par.pdat.eval().text = FRAG
    mat.par.cullface = 'neither'
    mat.par.uniname0 = 'uT'; mat.par.value0x = 3.0
    mat.par.uniname1 = 'uFront'; mat.par.value1x = 999.0

    g = c.create(geometryCOMP, 'blood')
    for ch in list(g.children): ch.destroy()
    tb = g.create(fileinSOP, 'tubes'); tb.par.file = D + '/tubes_td.obj'; tb.render = True; tb.display = True
    g.par.material = mat

    # liver: translucent wine-red body, brighter towards the silhouette, faint ink hatching from a noise field
    LV = """
out vec3 vW; out vec3 vN; out vec3 vC; out vec3 vCN;
void main(){ vec4 w = TDDeform(P); vW = w.xyz; vN = normalize(TDDeformNorm(N));
  vC = (uTDMats[TDCameraIndex()].cam * w).xyz; vCN = normalize((uTDMats[TDCameraIndex()].cam * vec4(vN, 0.0)).xyz); gl_Position = TDWorldToProj(w); }"""
    LF = """
in vec3 vW; in vec3 vN; in vec3 vC; in vec3 vCN;
out vec4 fragColor;
""" + NOISE + """
void main(){
    TDCheckDiscard();
    vec3 n = normalize(vN);
    float fr = pow(1.0 - abs(dot(normalize(vCN), normalize(-vC))), 2.2);
    float diff = max(dot(n, normalize(vec3(-0.4, 0.8, 0.5))), 0.0);
    float tex = fbm(vW * 0.08);
    float hatch = smoothstep(0.85, 1.0, abs(sin((vW.x + vW.y * 0.6) * 1.4 + tex * 4.0))) * (1.0 - diff) * 0.5;
    vec3 body = vec3(0.62, 0.16, 0.14) * (0.45 + 0.7 * diff) * (0.75 + 0.5 * tex);
    vec3 rim = vec3(0.95, 0.42, 0.32);
    vec3 col = body + rim * fr * 0.55 + vec3(0.5, 0.12, 0.1) * hatch;
    float a = 0.42 + 0.5 * fr;
    fragColor = TDOutputSwizzle(vec4(col * a, a));
}"""
    lmat = c.create(glslMAT, 'liver_mat')
    lmat.par.vdat.eval().text = LV
    lmat.par.pdat.eval().text = LF
    lmat.par.blending = False
    lmat.par.depthwriting = True; lmat.par.depthtest = True; lmat.par.cullface = 'backfaces'
    lv = c.create(geometryCOMP, 'liver')
    for ch in list(lv.children): ch.destroy()
    fi = lv.create(fileinSOP, 'mesh'); fi.par.file = D + '/liver_td.obj'
    fi.render = True; fi.display = True
    lv.par.material = lmat
    lv.par.drawpriority = -1   # draw after the vessels so they show through

    # (camera, look-at, fov, show liver, flow front)
    CAMS = {
        'lava4_k0_emerge': ((-13, -12, 15), (-1.2, -12.5, 4.5), 34, False, 9.0),
        'lava4_k1_rise':   ((-22, -5, 26), (-2.5, -6, 6.5), 38, False, 21.0),
        'lava4_k2_branch': ((-34, 8, 50), (-4, -1, 4), 40, False, 38.0),
        'lava4_k3_tree':   ((-14, 18, 98), (-6, 2, 0), 44, False, 62.0),
        'lava4_k4_liver':  ((-40, 52, 175), (-2, 0, 0), 40, True, 999.0),
    }
    outs = {}
    for nm_, (t, look, fov, show_liver, front) in CAMS.items():
        k = c.create(cameraCOMP, 'cam_' + nm_); k.par.tx, k.par.ty, k.par.tz = t; k.par.fov = fov
        nl = c.create(nullCOMP, 'look_' + nm_); nl.par.tx, nl.par.ty, nl.par.tz = look; k.par.lookat = nl
        r = c.create(renderTOP, 'r_' + nm_); r.par.camera = k
        r.par.geometry = 'blood'; r.par.lights = ''
        r.par.antialias = 'aa16'; r.par.outputresolution = 'custom'; r.par.resolutionw, r.par.resolutionh = W, H
        r.par.resmult = False; r.par.format = 'rgba16float'
        r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0.0; r.par.bgcolora = 1
        th = c.create(levelTOP, 'th_' + nm_); th.inputConnectors[0].connect(r); th.par.blacklevel = 0.45; th.par.format = 'rgba8fixed'   # 8-bit clamps the negative values the threshold produces
        b1 = c.create(blurTOP, 'b1_' + nm_); b1.inputConnectors[0].connect(th); b1.par.size = 18
        b2 = c.create(blurTOP, 'b2_' + nm_); b2.inputConnectors[0].connect(th); b2.par.size = 70
        m1 = c.create(compositeTOP, 'm1_' + nm_); m1.inputConnectors[0].connect(b1); m1.inputConnectors[1].connect(b2); m1.par.operand = 'add'
        gl = c.create(levelTOP, 'g_' + nm_); gl.inputConnectors[0].connect(m1); gl.par.brightness1 = 0.6
        m = c.create(compositeTOP, 'mix_' + nm_); m.inputConnectors[0].connect(r); m.inputConnectors[1].connect(gl); m.par.operand = 'add'
        last = m
        if show_liver:
            rl = c.create(renderTOP, 'rl_' + nm_); rl.par.camera = k; rl.par.geometry = 'liver'; rl.par.lights = ''
            rl.par.antialias = 'aa16'; rl.par.outputresolution = 'custom'; rl.par.resolutionw, rl.par.resolutionh = W, H
            rl.par.resmult = False; rl.par.format = 'rgba16float'; rl.par.bgcolora = 0
            ov = c.create(overTOP, 'ov_' + nm_); ov.inputConnectors[0].connect(rl); ov.inputConnectors[1].connect(m)
            last = ov
        o = c.create(nullTOP, 'out_' + nm_); o.inputConnectors[0].connect(last)
        outs[nm_] = o
    for nm_, o in outs.items():
        mat.par.value1x = CAMS[nm_][4]
        for _ in range(3): o.cook(force=True)
        o.save(OUT + '/' + nm_ + '.png')
        print(nm_)
    print('errors', {o.path: (o.errors(), o.warnings()) for o in c.findChildren(depth=None) if o.errors() or o.warnings()})

main()
