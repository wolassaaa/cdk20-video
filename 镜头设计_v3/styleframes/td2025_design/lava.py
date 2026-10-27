# Runs inside TD. Lava-crust blood vessels (dark cooled crust, glowing cracks, slow flow) + pull-back keyframes
# from the vessel surface out to the whole liver. Builds /project1/design/lava and saves one PNG per camera.
def main():
    D = r"C:/Users/woola/AppData/Local/Temp/claude/D---hkbu-molecular-science/99ee4c52-bc4b-442d-ae78-602740c170d9/scratchpad/tdd"
    OUT = D + "/png"
    W, H = 1920, 1080
    root = op('/project1/design') or op('/project1').create(baseCOMP, 'design')
    c = root.op('lava') or root.create(baseCOMP, 'lava')
    for ch in list(c.children):
        if ch.valid: ch.destroy()

    def data(nm, f):
        sc = c.create(scriptTOP, nm); sc.par.format = 'rgba32float'
        sc.par.callbacks.eval().text = ("import numpy as np\ndef onSetupParameters(s):\n    return\n"
            "def onCook(s):\n    s.copyNumpyArray(np.load(r'%s/%s').astype(np.float32))\n    return\n" % (D, f))
        return sc

    VERT = """
out vec3 vW; out vec3 vN;
void main(){
    vec4 w = TDDeform(P);
    vW = w.xyz; vN = normalize(TDDeformNorm(N));
    gl_Position = TDWorldToProj(w);
}"""
    FRAG = """
uniform float uT;      // time in seconds (flow offset)
uniform float uScale;  // crack cell size
in vec3 vW; in vec3 vN;
out vec4 fragColor;
vec3 h3(vec3 p){ p = vec3(dot(p,vec3(127.1,311.7,74.7)), dot(p,vec3(269.5,183.3,246.1)), dot(p,vec3(113.5,271.9,124.6)));
    return fract(sin(p)*43758.5453); }
float n3(vec3 p){ vec3 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    float a=h3(i).x, b=h3(i+vec3(1,0,0)).x, c=h3(i+vec3(0,1,0)).x, d=h3(i+vec3(1,1,0)).x;
    float e=h3(i+vec3(0,0,1)).x, g=h3(i+vec3(1,0,1)).x, k=h3(i+vec3(0,1,1)).x, l=h3(i+vec3(1,1,1)).x;
    return mix(mix(mix(a,b,f.x),mix(c,d,f.x),f.y), mix(mix(e,g,f.x),mix(k,l,f.x),f.y), f.z); }
float fbm(vec3 p){ float s=0.0, a=0.5; for(int i=0;i<5;i++){ s+=a*n3(p); p*=2.03; a*=0.5; } return s; }
// distance to the nearest Voronoi cell border (the crack network of the cooled crust)
float vedge(vec3 p){ vec3 i=floor(p), f=fract(p); float d1=8.0, d2=8.0;
    for(int z=-1;z<=1;z++) for(int y=-1;y<=1;y++) for(int x=-1;x<=1;x++){
        vec3 g=vec3(x,y,z); vec3 o=h3(i+g); float d=length(g+o-f);
        if(d<d1){ d2=d1; d1=d; } else if(d<d2){ d2=d; } }
    return d2-d1; }
void main(){
    TDCheckDiscard();
    vec3 n = normalize(vN);
    vec3 p = vW / uScale + vec3(uT*0.15, 0.0, uT*0.05);
    vec3 q = p + 0.6*vec3(fbm(p*0.7), fbm(p*0.7+3.1), fbm(p*0.7+7.7));   // warp so cracks look molten, not tiled
    float e = vedge(q);
    float heat = smoothstep(0.25, 0.75, fbm(vW*0.06 + vec3(0.0, uT*0.03, 0.0)));   // big hot / cooler zones
    float crack = 1.0 - smoothstep(0.0, 0.10 + 0.22*heat, e);
    float pool = smoothstep(0.55, 0.9, heat) * (1.0 - smoothstep(0.0, 0.5, e)) * 0.6;   // molten pools where it is hottest
    float g = clamp(crack + pool, 0.0, 1.0);
    vec3 L = normalize(vec3(-0.4, 0.8, 0.5));
    float diff = max(dot(n, L), 0.0);
    float rough = fbm(q*3.0);
    vec3 crust = vec3(0.36, 0.29, 0.26) * (0.2 + 1.1*diff) * (0.5 + 0.9*rough);
    crust += vec3(0.30, 0.035, 0.0) * exp(-e * 8.0) * (0.5 + heat);          // rock still warm next to a crack
    float rim = pow(1.0 - abs(n.z), 3.0);
    vec3 hot = mix(vec3(0.42, 0.02, 0.0), vec3(0.85, 0.16, 0.02), g);
    hot = mix(hot, vec3(1.0, 0.55, 0.18), pow(g, 5.0) * heat);
    vec3 col = crust*(1.0 - g) + hot * g * (0.75 + 0.9*heat) + vec3(0.18, 0.015, 0.0) * rim * 0.3;
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}"""
    mat = c.create(glslMAT, 'lava')
    mat.par.vdat.eval().text = VERT
    mat.par.pdat.eval().text = FRAG
    mat.par.uniname0 = 'uT'; mat.par.value0x = 7.0
    mat.par.uniname1 = 'uScale'; mat.par.value1x = 1.1

    g = c.create(geometryCOMP, 'blood')
    for ch in list(g.children): ch.destroy()
    sp = g.create(sphereSOP, 'sph'); sp.par.rows, sp.par.cols = 20, 30; sp.render = True; sp.display = True
    g.par.material = mat
    pos = data('pos', 'liquid.npy')
    g.par.instancing = True
    g.par.instancetop = pos; g.par.instancetx, g.par.instancety, g.par.instancetz = 'r', 'g', 'b'
    g.par.instancesop = pos; g.par.instancesx = 'a'; g.par.instancesy = 'a'; g.par.instancesz = 'a'

    # liver surface as a faint dust of bone-white ink points (only reads in the wide shots)
    lv = c.create(geometryCOMP, 'liver')
    for ch in list(lv.children): ch.destroy()
    bx = lv.create(boxSOP, 'b'); bx.render = True; bx.display = True
    lm = c.create(constantMAT, 'dust'); lm.par.colorr, lm.par.colorg, lm.par.colorb = 0.5, 0.48, 0.44
    lm.par.blending = True; lm.par.srcblend = 'one'; lm.par.destblend = 'one'; lm.par.depthwriting = False
    lv.par.material = lm
    lp = data('lpos', 'liver_pts.npy')
    lv.par.instancing = True
    lv.par.instancetop = lp; lv.par.instancetx, lv.par.instancety, lv.par.instancetz = 'r', 'g', 'b'
    lv.par.instancesop = lp; lv.par.instancesx = 'a'; lv.par.instancesy = 'a'; lv.par.instancesz = 'a'

    # pull-back keyframes: on the crust -> one branch -> the tree -> the whole liver
    CAMS = {
        'lava_k1_surface': ((-12.5, -3.0, 4.0), (-3.0, -4.6, 7.0), 34, False),
        'lava_k2_branch':  ((-24, 2, 30), (-4, -3, 4), 38, False),
        'lava_k3_tree':    ((-10, 14, 80), (-6, 2, 0), 42, True),
        'lava_k4_liver':   ((-30, 40, 150), (-2, 0, 0), 40, True),
    }
    outs = {}
    for nm, (t, look, fov, show_liver) in CAMS.items():
        k = c.create(cameraCOMP, 'cam_' + nm); k.par.tx, k.par.ty, k.par.tz = t; k.par.fov = fov
        n = c.create(nullCOMP, 'look_' + nm); n.par.tx, n.par.ty, n.par.tz = look; k.par.lookat = n
        r = c.create(renderTOP, 'r_' + nm); r.par.camera = k
        r.par.geometry = 'blood liver' if show_liver else 'blood'; r.par.lights = ''
        r.par.antialias = 'aa16'; r.par.outputresolution = 'custom'; r.par.resolutionw, r.par.resolutionh = W, H
        r.par.resmult = False; r.par.format = 'rgba16float'
        r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0.027; r.par.bgcolora = 1
        # bloom: only the hot cracks glow (threshold the render, blur, add back)
        th = c.create(levelTOP, 'th_' + nm); th.inputConnectors[0].connect(r); th.par.blacklevel = 0.45
        b1 = c.create(blurTOP, 'b1_' + nm); b1.inputConnectors[0].connect(th); b1.par.size = 18
        b2 = c.create(blurTOP, 'b2_' + nm); b2.inputConnectors[0].connect(th); b2.par.size = 70
        m1 = c.create(compositeTOP, 'm1_' + nm); m1.inputConnectors[0].connect(b1); m1.inputConnectors[1].connect(b2); m1.par.operand = 'add'
        gl = c.create(levelTOP, 'g_' + nm); gl.inputConnectors[0].connect(m1); gl.par.brightness1 = 0.6
        m = c.create(compositeTOP, 'mix_' + nm); m.inputConnectors[0].connect(r); m.inputConnectors[1].connect(gl); m.par.operand = 'add'
        o = c.create(nullTOP, 'out_' + nm); o.inputConnectors[0].connect(m)
        outs[nm] = o
    for nm, o in outs.items():
        for _ in range(3): o.cook(force=True)
        o.save(OUT + '/' + nm + '.png')
        print(nm)
    print('errors', {o.path: (o.errors(), o.warnings()) for o in c.findChildren(depth=None) if o.errors() or o.warnings()})

main()
