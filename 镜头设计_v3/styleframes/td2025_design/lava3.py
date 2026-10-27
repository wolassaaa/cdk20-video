# Runs inside TD. Lava blood v2: the crust breaks into plates stretched along each vessel, glowing flow streaks run
# between them and heat pulses travel downstream, so it reads as blood flowing, not as cracked rock. The liver is a
# real mesh (BodyParts3D v4) in translucent wine red with a lit rim. Four pull-back keyframes, one PNG each.
def main():
    D = r"C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/tdd"
    OUT = D + "/png"
    W, H = 1920, 1080
    root = op('/project1/design') or op('/project1').create(baseCOMP, 'design')
    c = root.op('lava3') or root.create(baseCOMP, 'lava3')
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
out vec3 vW; out vec3 vN; out vec2 vUV;
void main(){
    vec4 w = TDDeform(P);
    vW = w.xyz; vN = normalize(TDDeformNorm(N)); vUV = uv[0].st;
    gl_Position = TDWorldToProj(w);
}"""
    FRAG = """
uniform float uT;
uniform float uFront;   // how far (arc length from the roots) the blood has flowed so far
in vec3 vW; in vec3 vN; in vec2 vUV;
out vec4 fragColor;
""" + NOISE + """
void main(){
    TDCheckDiscard();
    vec3 n = normalize(vN);
    float along = vUV.x;                               // distance downstream along the vessel (tube UV)
    float ang = vUV.y * 6.2831853;                     // position around the vessel
    float d = uFront - along;                          // distance behind the flow front
    float ragged = 0.9 * (0.5 + 0.5 * sin(ang * 3.0 + along * 0.7)) + 0.6 * n3(vec3(ang * 2.0, along * 0.5, 0.0));
    if (d < ragged) discard;                           // not reached yet: pure black
    float fresh = exp(-(d - ragged) * 0.32);           // 1 at the front, fades as the lava cools behind it
    if (gl_FrontFacing) {                              // looking into the open front: a solid molten core
        float k = 0.55 + 0.45 * n3(vec3(ang * 3.0, along * 1.5, 0.0));
        fragColor = TDOutputSwizzle(vec4(mix(vec3(0.85, 0.12, 0.02), vec3(1.0, 0.55, 0.2), k * k) * (0.9 + 0.5 * fresh), 1.0));
        return;
    }
    float f = along - uT * 2.0;                        // texture moves downstream with time
    vec3 ring = vec3(cos(ang), sin(ang), 0.0) * 1.7;
    // crust plates: Voronoi cells stretched about 3x along the flow
    vec3 q = vec3(f * 0.3, ring.x * 1.4, ring.y * 1.4);
    q += 0.35 * vec3(fbm(q * 0.8), fbm(q * 0.8 + 3.1), fbm(q * 0.8 + 7.7));
    float e = vedge(q);
    // flow streaks: thin lines parallel to the vessel, wobbling slowly
    float wob = fbm(vec3(f * 0.12, ring.xy * 1.3));
    float streak = pow(abs(sin(ang * 14.0 + wob * 9.0)), 40.0);
    // heat pulses travelling downstream (the heartbeat pushing blood along)
    float pulse = 0.5 + 0.5 * sin(f * 0.22);
    float heat = clamp(0.35 + 0.65 * pulse * smoothstep(0.2, 0.7, fbm(vec3(f * 0.05, ring.xy * 0.5))), 0.0, 1.0);
    float crack = 1.0 - smoothstep(0.0, 0.04 + 0.1 * heat, e);
    float g = clamp(crack + streak * 0.9 * heat, 0.0, 1.0);
    vec3 L = normalize(vec3(-0.4, 0.8, 0.5));
    float diff = max(dot(n, L), 0.0);
    float rough = fbm(q * 3.0);
    vec3 crust = vec3(0.40, 0.29, 0.26) * (0.2 + 1.1 * diff) * (0.5 + 0.9 * rough);
    crust += vec3(0.35, 0.03, 0.0) * exp(-e * 7.0) * (0.4 + heat);
    vec3 hot = mix(vec3(0.45, 0.02, 0.0), vec3(0.95, 0.15, 0.03), g);
    hot = mix(hot, vec3(1.0, 0.5, 0.16), pow(g, 5.0) * heat);
    vec3 col = crust * (1.0 - g) + hot * g * (0.7 + 0.9 * heat);
    // fresh lava at the front: no crust yet, molten and brightest right at the tip
    vec3 molten = mix(vec3(0.85, 0.08, 0.01), vec3(1.0, 0.52, 0.18), fresh * (0.55 + 0.45 * streak));
    col = mix(col, molten * (0.75 + 0.75 * fresh), smoothstep(0.25, 0.9, fresh));
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
        'lava3_k0_emerge': ((-13, -12, 15), (-1.2, -12.5, 4.5), 34, False, 9.0),
        'lava3_k1_rise':   ((-22, -5, 26), (-2.5, -6, 6.5), 38, False, 21.0),
        'lava3_k2_branch': ((-34, 8, 50), (-4, -1, 4), 40, False, 38.0),
        'lava3_k3_tree':   ((-14, 18, 98), (-6, 2, 0), 44, False, 62.0),
        'lava3_k4_liver':  ((-40, 52, 175), (-2, 0, 0), 40, True, 999.0),
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
        th = c.create(levelTOP, 'th_' + nm_); th.inputConnectors[0].connect(r); th.par.blacklevel = 0.45
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
