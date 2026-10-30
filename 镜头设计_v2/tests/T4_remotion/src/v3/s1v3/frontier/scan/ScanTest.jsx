// SCAN: data anatomy. S1 opening test 1-01 -> 1-02, 10 s @ 30 fps.
//
// One decision carries the piece: the liver is cut into exactly 1,412 axial sections (BodyParts3D v4 meshes,
// computed in numpy by prep_dense.py: 155.2 mm / 1,412 = 0.11 mm apart), one section for each person the
// registry counted in 2022. The organ is the ledger.
//   0-3 s  a scan line deposits the sections, in steps on the syllables of the VO
//   3-7 s  it reads back up; four sections turn blood red, hold, and go black
//   7-10 s it comes down again and puts out every remaining section, counting; behind it is the number
// Every number on screen is a real property of the data (z, area) or the count of sections.
// Every section is a hairline of light, added together: the outline bunches into a bright rim where the surface
// turns away and the vessels glow inside, the way a CT volume rendering looks. Nothing here is shaded or textured.
// No noise, no boil, fixed camera: each frame is a pure function of the frame number.
import React, {useEffect, useLayoutEffect, useRef, useState} from "react";
import {AbsoluteFill, continueRender, delayRender, staticFile, useCurrentFrame} from "remotion";
import {K, W, H, GROT, T, fmt, ramp, lerp, smoother, smooth, makeCam} from "./lib";

export const DUR = 300;
const SS = 2;                                   // canvas supersampling
const LW = 0.5, TONE = 0.078, VT = 0.032;       // section hairline: px, opacity (parenchyma, vessels)

// ------------------------------------------------------------------ data (fetched once per tab)
let DATA_P = null;
const loadData = () => DATA_P || (DATA_P = (async () => {
  const [j, b] = await Promise.all([
    fetch(staticFile("liver1412.json")).then(r => r.json()),
    fetch(staticFile("liver1412.bin")).then(r => r.arrayBuffer()),
  ]);
  return {...j, bin: new Int16Array(b), m: [(j.bmin[0] + j.bmax[0]) / 2, (j.bmin[1] + j.bmax[1]) / 2, (j.bmin[2] + j.bmax[2]) / 2]};
})());
const useData = () => {
  const [d, setD] = useState(null);
  const [h] = useState(() => delayRender("scan data"));
  useEffect(() => { loadData().then(x => { setD(x); continueRender(h); }); }, [h]);
  return d;
};

// ------------------------------------------------------------------ camera: fixed, the object does not perform
const CAMP = {yaw: -6 * Math.PI / 180, el: 20 * Math.PI / 180, s: 5.3, cx: 960, cy: 578};

const buildGeom = D => {
  const cam = makeCam({...CAMP, m: D.m});
  const decode = ([o, n]) => { const P = new Float64Array(n * 2); for (let i = 0; i < n * 2; i++) P[i] = D.bin[o + i] / D.q; return P; };
  const sec = D.sec.map(s => {
    const fill = new Path2D(), line = new Path2D(), ves = new Path2D();
    for (const r of s.f) fill.addPath(new Path2D(cam.path(decode(r), s.z, true)));
    for (const r of s.o) line.addPath(new Path2D(cam.path(decode(r), s.z, false)));
    for (const r of s.v) ves.addPath(new Path2D(cam.path(decode(r), s.z, false)));
    return {z: s.z, a: s.a, fill, line, ves};
  });
  return {cam, sec};
};
let GEOM = null;

// ------------------------------------------------------------------ timing (frames)
// Assumed VO syllable onsets (s) for "Ev-ery day / in Hong Kong / a-bout four"; re-time to the real VO.
const SYL = [0.30, 0.47, 0.64, 1.05, 1.22, 1.45, 2.05, 2.22, 2.50].map(t => t * 30);
const STEP = 5;
const buildU = f => SYL.reduce((a, t) => a + smoother((f - t) / STEP) / SYL.length, 0);    // 0..1
const END_BUILD = SYL[SYL.length - 1] + STEP;

const Z_D = [1075, 1100, 1125, 1150];                     // the four sections: every 25 mm, read upwards
const DF = [98, 127, 156, 185];                           // red begins, one every 0.97 s
const RED_IN = 6, HOLD = 12, OUT = 8, BLACK = 3, BACK = 9; // one flash per 0.97 s (WCAG limit is 3 per s)
const WIPE0 = 214, WIPE1 = 264;                           // the last sweep, on "1,412 people"

const idxOfZ = (D, z) => (D.zTop - z) / D.dz - 0.5;
const deadIdx = D => Z_D.map(z => Math.round(idxOfZ(D, z)));

// height of the scan line, as a section index (float)
const lineIdx = (D, f) => {
  const N = D.N;
  if (f < END_BUILD + 2) return buildU(f) * (N - 1);
  const ks = [[END_BUILD + 2, N - 1]];
  DF.forEach((f0, i) => {
    ks.push([f0 - 3, idxOfZ(D, Z_D[i])]);
    ks.push([f0 + RED_IN + HOLD + OUT - 6, idxOfZ(D, Z_D[i])]);
  });
  ks.push([WIPE0, -8]);
  ks.push([WIPE1, N - 1]);
  for (let i = 1; i < ks.length; i++) {
    const [fa, a] = ks[i - 1], [fb, b] = ks[i];
    if (f <= fb) {
      const u = (f - fa) / (fb - fa);
      return lerp(a, b, fb === WIPE1 ? 0.5 * u + 0.5 * smooth(u) : smoother(u));
    }
  }
  return N - 1;
};
// One death, as frames from f0: the section rises in red over everything (red), holds, then the whole shape sinks to
// black (veil 1 -> 0), stays black for a beat, and only the sections in front of it return (back 0 -> 1). Pixels move
// along black-red and then black-bone, never directly between red and bone, so nothing ever passes through pink.
const deathState = (f0, f) => {
  const t = f - f0, tOut = RED_IN + HOLD, tBlack = tOut + OUT;
  if (t < 0) return {on: false, red: 0, veil: 1, back: 1, plane: 0};
  const red = smooth(t / RED_IN) * (1 - smooth((t - tOut) / OUT));
  return {
    on: t < tBlack + BLACK + BACK,
    red,
    veil: 1 - smooth((t - tOut) / OUT),
    back: smooth((t - tBlack - BLACK) / BACK),
    plane: t >= tBlack ? 1 : 0,                     // the opaque plane appears while the shape is black
  };
};

// ------------------------------------------------------------------ the organ
// grade: additive 8-bit light -> stage black ... bone
const LUT = [[6, 237], [6, 235], [6, 228]].map(([b, t]) => Uint8ClampedArray.from({length: 256}, (_, i) => Math.round(b + (t - b) * i / 255)));

let OFF = null;
const lightPass = (D, G, f) => {
  if (!OFF) { OFF = document.createElement("canvas"); OFF.width = W * SS; OFF.height = H * SS; }
  const ctx = OFF.getContext("2d");
  const N = D.N;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalCompositeOperation = "source-over";
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, W * SS, H * SS);
  if (f >= WIPE1) return OFF;
  ctx.setTransform(SS, 0, 0, SS, 0, 0);
  ctx.lineJoin = "round";
  const li = lineIdx(D, f);
  const building = f < END_BUILD + 2;
  const first = f >= WIPE0 ? Math.max(0, Math.ceil(li)) : 0;
  const last = building ? Math.floor(li) : N - 1;
  const dark = {};
  deadIdx(D).forEach((k, i) => { if (deathState(DF[i], f).plane) dark[k] = 1; });
  ctx.globalCompositeOperation = "lighter";
  ctx.lineWidth = LW;
  const sLine = `rgba(255,255,255,${TONE})`, sVes = `rgba(255,255,255,${VT})`;
  // bottom section first: a dead section is an opaque plane, in depth order
  for (let k = last; k >= first; k--) {
    const s = G.sec[k];
    if (dark[k]) {
      ctx.globalCompositeOperation = "source-over";
      ctx.fillStyle = "#000";
      ctx.fill(s.fill, "evenodd");
      ctx.globalCompositeOperation = "lighter";
      continue;
    }
    ctx.strokeStyle = sLine; ctx.stroke(s.line);
    ctx.strokeStyle = sVes; ctx.stroke(s.ves);
  }
  return OFF;
};

const grade = ctx => {
  const im = ctx.getImageData(0, 0, W, H), d = im.data;
  for (let i = 0; i < d.length; i += 4) { d[i] = LUT[0][d[i]]; d[i + 1] = LUT[1][d[i + 1]]; d[i + 2] = LUT[2][d[i + 2]]; }
  ctx.putImageData(im, 0, 0);
};

// red on top of the graded organ. Inside the section everything is first multiplied by the red, then the red rises
// through 'lighten': every pixel stays on the black-red axis, so the fade never passes through pink.
const drawOver = (ctx, D, G, f) => {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.lineJoin = "round";
  const li = lineIdx(D, f);
  deadIdx(D).forEach((k, i) => {
    const st = deathState(DF[i], f);
    if (!st.on) return;
    const s = G.sec[k];
    const grey = v => { const c = Math.round(255 * v); return `rgb(${c},${c},${c})`; };
    ctx.save();
    ctx.clip(s.fill, "evenodd");
    ctx.globalCompositeOperation = "multiply";
    if (st.plane) {                                 // black, then the front sections come back in bone
      ctx.fillStyle = grey(st.back);
      ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = "lighten";
      ctx.fillStyle = K.bg;
      ctx.fillRect(0, 0, W, H);
    } else {
      const v = st.veil;                            // lines go red at once, then everything sinks with the veil
      ctx.fillStyle = `rgb(${Math.round(232 * v)},${Math.round(25 * v)},${Math.round(15 * v)})`;
      ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = "lighten";
      ctx.globalAlpha = st.red;
      ctx.fillStyle = K.red;
      ctx.fillRect(0, 0, W, H);
      ctx.globalAlpha = 1;
      ctx.fillStyle = K.bg;
      ctx.fillRect(0, 0, W, H);
    }
    ctx.restore();
    if (st.red > 0) {
      ctx.globalAlpha = st.red;
      ctx.strokeStyle = K.red;
      ctx.lineWidth = 1.2;
      ctx.stroke(s.line);
      ctx.strokeStyle = K.bg;                       // the section's own vessels, cut through: black rings in the red
      ctx.lineWidth = 0.8;
      ctx.stroke(s.ves);
      ctx.globalAlpha = 1;
    }
  });
  // bright live section at the scan line while it builds or puts out
  const k = Math.round(li);
  const a = f < END_BUILD + 2 ? ramp(f, 8, 11) : (f >= WIPE0 && f < WIPE1 ? 1 : 0);
  if (a > 0 && k >= 0 && k < D.N) {
    ctx.strokeStyle = K.b(0.95 * a);
    ctx.lineWidth = 1.1;
    ctx.stroke(G.sec[k].line);
  }
};

const OrganCanvas = ({f, D}) => {
  const ref = useRef(null);
  useLayoutEffect(() => {
    if (!D || !ref.current) return;
    if (!GEOM) GEOM = buildGeom(D);
    const src = lightPass(D, GEOM, f);
    const ctx = ref.current.getContext("2d", {willReadFrequently: true});
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = "copy";
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(src, 0, 0, W, H);
    ctx.globalCompositeOperation = "source-over";
    grade(ctx);
    drawOver(ctx, D, GEOM, f);
  }, [f, D]);
  return <canvas ref={ref} width={W} height={H} style={{position: "absolute", left: 0, top: 0, width: W, height: H}}/>;
};

// ------------------------------------------------------------------ overlay: ruler, scan line, readouts
const countAt = (D, f, li) => {
  if (f >= WIPE1) return D.N;
  const passed = Math.max(0, Math.ceil(li));
  const below = deadIdx(D).filter(k => k >= passed).length;
  return Math.min(D.N, passed + below);
};
const Overlay = ({f, D}) => {
  if (!D) return null;
  const cam = makeCam({...CAMP, m: D.m});
  const li = lineIdx(D, f);
  const k = Math.max(0, Math.min(D.N - 1, Math.round(li)));
  const s = D.sec[k];
  const yAt = z => cam.pt(D.m[0], D.m[1], z)[1];
  const y = Math.round(yAt(D.zTop - (li + 0.5) * D.dz)) + 0.5;
  const red = Math.max(...DF.map(f0 => deathState(f0, f).red));
  const lineVis = smooth(ramp(f, 4, 10)) * (1 - smooth(ramp(f, WIPE1, WIPE1 + 8)));
  const col = red > 0.02 ? K.red : K.bone;
  const shown = f < WIPE0 ? DF.filter(f0 => f >= f0).length : countAt(D, f, li);
  const rx = 64;
  const ticks = [];
  for (let z = 1030; z <= 1180; z += 5) {
    const ty = Math.round(yAt(z)) + 0.5;
    const major = z % 25 === 0;
    ticks.push(<line key={z} x1={rx} y1={ty} x2={rx + (major ? 12 : 6)} y2={ty} stroke={K.bone} strokeOpacity={major ? 0.6 : 0.3} strokeWidth={1}/>);
    if (major) ticks.push(<T key={"l" + z} x={rx + 20} y={ty + 4} size={10.5} ls={1} op={0.5}>{fmt(z)}</T>);
  }
  const furn = smooth(ramp(f, 2, 12)) * (1 - smooth(ramp(f, WIPE1 - 6, WIPE1 + 8)));
  return <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
    <g opacity={furn}>
      {ticks}
      <T x={rx} y={yAt(1180) - 26} size={10.5} ls={2} op={0.5}>Z MM</T>
    </g>
    <g opacity={lineVis}>
      <line x1={0} y1={y} x2={W} y2={y} stroke={col} strokeOpacity={0.85} strokeWidth={1}/>
      <T x={W - 64} y={y - 10} size={13} anchor="end" ls={1.5} color={col}>{`Z ${fmt(s.z, 1)} MM · A ${fmt(s.a)} MM²`}</T>
      {shown > 0 ? <T x={W - 64} y={y + 23} size={13} anchor="end" ls={1.5} color={col}>{fmt(shown)}</T> : null}
    </g>
  </svg>;
};

// the number sits under the organ; the last sweep uncovers it
const Number_ = ({f, D}) => {
  if (!D || f < WIPE0 - 2) return null;
  const cam = makeCam({...CAMP, m: D.m});
  const li = lineIdx(D, f);
  const y = cam.pt(D.m[0], D.m[1], D.zTop - (li + 0.5) * D.dz)[1];
  const c = smooth(ramp(f, WIPE1 + 2, WIPE1 + 16));
  return <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
    <defs><clipPath id="sweep"><rect x={0} y={0} width={W} height={f >= WIPE1 ? H : Math.max(0, y)}/></clipPath></defs>
    <g clipPath="url(#sweep)">
      <text x={64} y={900} fontFamily={GROT} fontWeight={200} fontSize={379} fill={K.bone} letterSpacing={-6}
        style={{fontVariantNumeric: "lining-nums"}}>1,412<tspan fontSize={80} fontWeight={300} dx={44} letterSpacing={0}>deaths in Hong Kong, 2022</tspan></text>
    </g>
    <T x={W - 64} y={960} size={14} anchor="end" ls={1.5} op={0.55 * c}>Hong Kong Cancer Registry, Hospital Authority</T>
  </svg>;
};

export const ScanTest = () => {
  const f = useCurrentFrame();
  const D = useData();
  return <AbsoluteFill style={{backgroundColor: K.bg}}>
    <OrganCanvas f={f} D={D}/>
    <Number_ f={f} D={D}/>
    <Overlay f={f} D={D}/>
  </AbsoluteFill>;
};
