// 1-11 v2 (01:52–02:03, 11 s, C voice-over): one continuous camera move.
// Pearl River Delta with Hong Kong pinned -> the whole of Hong Kong (Lantau, Kowloon, Hong Kong Island, Victoria Harbour, Sha Tin)
// -> tilts down into Tolo Harbour, where one blood-red line runs from Prince of Wales Hospital (CUHK, Sha Tin)
// to Hong Kong Science Park (Pak Shek Kok).
// Map data: OSM natural=coastline + HK boundary relation 913110 (© OpenStreetMap contributors, ODbL), prepared by
// 镜头设计_v3/styleframes/S1/v2/_code/reel2/map111/prep111.py into ./prd.json (local metres, origin 114.17E 22.35N).
// Everything is drawn as vector per frame through a small perspective camera (so the zoom is continuous and sharp).
import React, {useMemo} from "react";
import {AbsoluteFill, useCurrentFrame} from "remotion";
import {ramp, inOut, clamp01, lerp} from "../../../core";
import {Finish, K, GROT, MONO, OSM_CREDIT, W, H} from "../../s110/lib";
import DATA from "./prd.json";

export const DUR_111 = 330;

const COL = {
  sea0: "#0638C4", sea1: "#002FA7", sea2: "#001660", shallow: "#1F3BFF",
  land: "#060606", other: "#0A1236", wall: "#15171D", rim: "rgba(237,235,228,0.55)", rimOther: "rgba(237,235,228,0.10)",
  ink: K.ink, dim: "rgba(237,235,228,0.62)", red: "#E8190F", redDeep: "#9A0E08",
};

// ------------------------------------------------------------------ camera
const LON0 = 114.17, LAT0 = 22.35, KX = 111320 * Math.cos(LAT0 * Math.PI / 180), KY = 110574;
const P = (lon, lat) => [(lon - LON0) * KX, (lat - LAT0) * KY];
const FOV = 28 * Math.PI / 180, TANH = Math.tan(FOV / 2), FPX = (H / 2) / TANH;

// three framings: Pearl River Delta, all of Hong Kong, Tolo Harbour
const S0 = 98000, S1 = 41000, S2 = 10200;
const C0 = P(113.80, 22.37), C1 = P(114.12, 22.355), C2 = [5200, 6900];
const Z1 = [10, 104], Z2 = [168, 262];
const ease = x => { x = clamp01(x); return x * x * x * (x * (6 * x - 15) + 10); }; // quintic smootherstep

export const camAt = f => {
  const e1 = ease((f - Z1[0]) / (Z1[1] - Z1[0])), e2 = ease((f - Z2[0]) / (Z2[1] - Z2[0]));
  const s1 = S0 * Math.pow(S1 / S0, e1), s2 = S1 * Math.pow(S2 / S1, e2);
  const w1 = (S0 - s1) / (S0 - S1), w2 = (S1 - s2) / (S1 - S2);          // zoom towards a fixed point
  const drift = Math.exp(-0.00042 * f);                                      // the camera never stops: slow push all through
  const s = (e2 > 0 ? s2 : s1) * drift;
  const c = [lerp(lerp(C0[0], C1[0], w1), C2[0], w2) + 300 * Math.sin(f / 70), lerp(lerp(C0[1], C1[1], w1), C2[1], w2)];
  const pitch = (36 * ease((f - Z2[0] - 12) / (Z2[1] - Z2[0] + 20))) * Math.PI / 180;
  const bear = (-11 * ease((f - Z2[0]) / (DUR_111 - Z2[0]))) * Math.PI / 180;
  return {s, c, pitch, bear};
};

const makeProj = ({s, c, pitch, bear}) => {
  const D = (s * H / W) / TANH;
  const g = [-Math.sin(bear), Math.cos(bear)], rt = [Math.cos(bear), Math.sin(bear)];
  const st = Math.sin(pitch), ct = Math.cos(pitch);
  const cam = [c[0] - D * st * g[0], c[1] - D * st * g[1], D * ct];
  const fwd = [st * g[0], st * g[1], -ct], up = [ct * g[0], ct * g[1], st];
  const pr = (x, y, z = 0) => {
    const vx = x - cam[0], vy = y - cam[1], vz = z - cam[2];
    const d = vx * fwd[0] + vy * fwd[1] + vz * fwd[2];
    if (d < D * 0.05) return null;
    return [W / 2 + FPX * (vx * rt[0] + vy * rt[1]) / d, H / 2 - FPX * (vx * up[0] + vy * up[1] + vz * up[2]) / d];
  };
  // ground footprint of the screen (for culling): unproject the corners onto z = 0
  const un = (sx, sy) => {
    const a = (sx - W / 2) / FPX, b = -(sy - H / 2) / FPX;
    const r = [fwd[0] + a * rt[0] + b * up[0], fwd[1] + a * rt[1] + b * up[1], fwd[2] + b * up[2]];
    const t = r[2] < -1e-6 ? -cam[2] / r[2] : 1e9;
    return [cam[0] + r[0] * Math.min(t, 40 * D), cam[1] + r[1] * Math.min(t, 40 * D)];
  };
  const cs = [un(0, 0), un(W, 0), un(0, H), un(W, H)];
  const m = 0.15 * s;
  const fp = [Math.min(...cs.map(p => p[0])) - m, Math.min(...cs.map(p => p[1])) - m, Math.max(...cs.map(p => p[0])) + m, Math.max(...cs.map(p => p[1])) + m];
  return {pr, fp, D};
};

// ------------------------------------------------------------------ geometry -> SVG path, per frame
const prepRings = rings => rings.map(r => {
  const xs = r.p.map(q => q[0]), ys = r.p.map(q => q[1]);
  return {p: r.p, a: r.a, bb: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]};
});
const LODS = DATA.lod.map(L => ({box: L.box, rings: prepRings(L.rings)}));
const HKB = DATA.hk.map(p => ({p, a: 1, bb: [Math.min(...p.map(q => q[0])), Math.min(...p.map(q => q[1])), Math.max(...p.map(q => q[0])), Math.max(...p.map(q => q[1]))]}));

const pathOf = (rings, pr, fp, z, pxMin = 0.8, close = true) => {
  let d = "";
  for (const r of rings) {
    const b = r.bb;
    if (b[2] < fp[0] || b[0] > fp[2] || b[3] < fp[1] || b[1] > fp[3]) continue;
    let lx = -1e9, ly = -1e9, n = 0, seg = "";
    for (const q of r.p) {
      const s = pr(q[0], q[1], z);
      if (!s) continue;
      if (Math.abs(s[0] - lx) + Math.abs(s[1] - ly) < pxMin) continue;
      seg += (n ? "L" : "M") + s[0].toFixed(1) + "," + s[1].toFixed(1);
      lx = s[0]; ly = s[1]; n++;
    }
    if (n >= 3) d += seg + (close ? "Z" : "");
  }
  return d;
};

// smooth route (Catmull-Rom through the control points), resampled by length
const ROUTE = (() => {
  const c = DATA.route, out = [];
  for (let i = 0; i < c.length - 1; i++) {
    const p0 = c[Math.max(0, i - 1)], p1 = c[i], p2 = c[i + 1], p3 = c[Math.min(c.length - 1, i + 2)];
    for (let k = 0; k < 16; k++) {
      const t = k / 16, t2 = t * t, t3 = t2 * t;
      out.push([0, 1].map(j => 0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)));
    }
  }
  out.push(c[c.length - 1]);
  const L = [0];
  for (let i = 1; i < out.length; i++) L.push(L[i - 1] + Math.hypot(out[i][0] - out[i - 1][0], out[i][1] - out[i - 1][1]));
  return {p: out, L, len: L[L.length - 1]};
})();
const routeUpTo = u => {
  const tgt = u * ROUTE.len, pts = [];
  for (let i = 0; i < ROUTE.p.length; i++) {
    if (ROUTE.L[i] <= tgt) { pts.push(ROUTE.p[i]); continue; }
    const a = ROUTE.p[i - 1], b = ROUTE.p[i], t = (tgt - ROUTE.L[i - 1]) / (ROUTE.L[i] - ROUTE.L[i - 1]);
    pts.push([lerp(a[0], b[0], t), lerp(a[1], b[1], t)]);
    break;
  }
  return pts;
};

// ------------------------------------------------------------------ labels
const LB = DATA.lab, POI = DATA.poi;
const fadeIO = (f, a, b, k = 10) => Math.min(ramp(f, a, a + k), 1 - ramp(f, b - k, b));
// kind: place (mono caps), water (mono, lighter, wider), small
const LABELS = [
  // the delta
  {at: LB.shenzhen, t: "SHENZHEN", a: 8, b: 92, kind: "other"},
  {at: LB.macau, t: "MACAU", a: 12, b: 92, kind: "other"},
  {at: LB.zhuhai, t: "ZHUHAI", a: 14, b: 92, kind: "other"},
  {at: LB.estuary, t: "PEARL RIVER ESTUARY", a: 10, b: 92, kind: "water"},
  {at: LB.scs, t: "SOUTH CHINA SEA", a: 16, b: 96, kind: "water"},
  // Hong Kong
  {at: LB.lantau, t: "LANTAU", a: 84, b: 196, kind: "place"},
  {at: LB.nt, t: "NEW TERRITORIES", a: 92, b: 192, kind: "place"},
  {at: LB.kowloon, t: "KOWLOON", a: 98, b: 200, kind: "place", dy: -2},
  {at: LB.hkisland, t: "HONG KONG ISLAND", a: 104, b: 200, kind: "place"},
  {at: LB.harbour, t: "VICTORIA HARBOUR", a: 110, b: 200, kind: "water", size: 14, dy: 4, strong: true},
  {at: LB.shatin, t: "SHA TIN", a: 118, b: 236, kind: "place", dx: -70},
  // Tolo Harbour
  {at: LB.tolo, t: "TOLO HARBOUR", a: 222, b: 400, kind: "water", size: 15},
  {at: LB.shingmun, t: "SHING MUN RIVER", a: 232, b: 400, kind: "water", size: 11, dx: -150, dy: 10},
];

const Label = ({x, y, l, op}) => {
  const st = {
    other: {size: 14, color: "rgba(237,235,228,0.55)", ls: 4, w: 400},
    place: {size: 16, color: COL.ink, ls: 4, w: 700},
    water: {size: l.size || 14, color: "rgba(237,235,228,0.78)", ls: 6, w: 400},
  }[l.kind];
  return <div style={{position: "absolute", left: x + (l.dx || 0), top: y + (l.dy || 0), transform: "translate(-50%, -50%)", opacity: op,
    fontFamily: MONO, fontSize: st.size, letterSpacing: st.ls, fontWeight: l.strong ? 700 : st.w, color: l.strong ? COL.ink : st.color, whiteSpace: "pre",
    textShadow: "0 0 10px rgba(0,0,0,0.55)"}}>
    {l.dot ? <span style={{display: "inline-block", width: 7, height: 7, borderRadius: 4, background: COL.ink, marginRight: 12, verticalAlign: 2}}/> : null}
    {l.t}
  </div>;
};

// a pin with a hairline leader and a two-line label
const Pin = ({at, dx, dy, title, sub, op, color = COL.ink, dot = COL.red, r = 6, ring = 0, anchor = "right"}) => {
  if (!at) return null;
  const [x, y] = at, lx = x + dx, ly = y + dy;
  const tx = anchor === "right" ? lx - 10 : lx + 10;
  return <>
    <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0, opacity: op}}>
      <line x1={x} y1={y} x2={lx} y2={ly} stroke="rgba(237,235,228,0.7)" strokeWidth={1}/>
      {ring > 0 ? <circle cx={x} cy={y} r={r + 22 * ring} fill="none" stroke={COL.ink} strokeOpacity={0.8 * (1 - ring)} strokeWidth={1.2}/> : null}
      <circle cx={x} cy={y} r={r} fill={dot}/>
      <circle cx={x} cy={y} r={r + 4} fill="none" stroke={COL.ink} strokeOpacity={0.85} strokeWidth={1}/>
    </svg>
    <div style={{position: "absolute", top: ly - 22, opacity: op, textAlign: anchor,
      ...(anchor === "right" ? {right: W - tx} : {left: tx})}}>
      <div style={{fontFamily: MONO, fontSize: 17, fontWeight: 700, letterSpacing: 3.5, color, whiteSpace: "pre"}}>{title}</div>
      {sub ? <div style={{fontFamily: MONO, fontSize: 12, letterSpacing: 2.2, color: COL.dim, marginTop: 7, whiteSpace: "pre"}}>{sub}</div> : null}
    </div>
  </>;
};

// scale bar that follows the zoom
const NICE = [50000, 20000, 10000, 5000, 2000, 1000, 500];
const ScaleBar = ({s, op}) => {
  const ppm = (W / 2) / s;
  const L = NICE.find(v => v * ppm <= 230) || 500, w = L * ppm;
  const txt = L >= 1000 ? `${L / 1000} KM` : `${L} M`;
  return <div style={{position: "absolute", left: 96, bottom: 72, opacity: op, width: 260, height: 40}}>
    <div style={{position: "absolute", left: 0, bottom: 0, width: w, height: 6, borderLeft: "1px solid rgba(237,235,228,0.75)", borderRight: "1px solid rgba(237,235,228,0.75)", borderBottom: "1px solid rgba(237,235,228,0.75)"}}/>
    <div style={{position: "absolute", left: w + 12, bottom: -4, fontFamily: MONO, fontSize: 11, letterSpacing: 2, color: COL.dim, whiteSpace: "pre"}}>{txt}</div>
  </div>;
};

// faint lat/lon graticule on the ground plane (shows the tilt; spacing adapts to the zoom)
const GSTEPS = [0.5, 0.2, 0.1, 0.05, 0.02, 0.01];
const Graticule = ({pr, fp, s}) => {
  const out = [];
  GSTEPS.forEach((st, k) => {
    const px = st * KY * (W / 2) / s;                       // screen spacing at the target
    const op = Math.min(ramp(px, 70, 160), 1 - ramp(px, 520, 900));
    if (op <= 0.01) return;
    const lon0 = LON0 + fp[0] / KX, lon1 = LON0 + fp[2] / KX, lat0 = LAT0 + fp[1] / KY, lat1 = LAT0 + fp[3] / KY;
    let d = "";
    for (let lo = Math.ceil(lon0 / st) * st; lo <= lon1; lo += st) {
      const a = pr((lo - LON0) * KX, fp[1]), b = pr((lo - LON0) * KX, fp[3]);
      if (a && b) d += `M${a[0].toFixed(1)},${a[1].toFixed(1)}L${b[0].toFixed(1)},${b[1].toFixed(1)}`;
    }
    for (let la = Math.ceil(lat0 / st) * st; la <= lat1; la += st) {
      const a = pr(fp[0], (la - LAT0) * KY), b = pr(fp[2], (la - LAT0) * KY);
      if (a && b) d += `M${a[0].toFixed(1)},${a[1].toFixed(1)}L${b[0].toFixed(1)},${b[1].toFixed(1)}`;
    }
    out.push(<path key={k} d={d} fill="none" stroke={COL.ink} strokeOpacity={0.09 * op} strokeWidth={1}/>);
  });
  return <>{out}</>;
};

// ------------------------------------------------------------------ the shot
export const Beat111 = () => {
  const f = useCurrentFrame();
  const cam = camAt(f);
  const {pr, fp} = makeProj(cam);
  const s = cam.s, zt = 0.011 * s;                       // slab thickness (only shows once the camera tilts)

  // level of detail: coarse always underneath, finer ones fade in on top as the camera closes in
  const a1 = ramp(Math.log(s), Math.log(52000), Math.log(44000));
  const a2 = ramp(Math.log(s), Math.log(14000), Math.log(11000));
  const layers = [{L: LODS[0], op: 1 - ramp(Math.log(s), Math.log(30000), Math.log(26000))}, {L: LODS[1], op: a1 * (1 - ramp(Math.log(s), Math.log(9500), Math.log(8200)))}, {L: LODS[2], op: a2}]
    .filter(o => o.op > 0.001)
    .map(o => ({...o, top: pathOf(o.L.rings, pr, fp, zt), base: cam.pitch > 0.01 ? pathOf(o.L.rings, pr, fp, 0) : ""}));
  const hk = pathOf(HKB, pr, fp, zt, 0.8);
  const hkLine = pathOf(HKB, pr, fp, zt, 0.8);
  const glowW = 10 + 10 * clamp01((S1 - s) / (S1 - S2));

  // route
  const u = inOut(ramp(f, 246, 300));
  const rpts = routeUpTo(u).map(q => pr(q[0], q[1], zt)).filter(Boolean);
  const rd = rpts.length > 1 ? "M" + rpts.map(p => p[0].toFixed(1) + "," + p[1].toFixed(1)).join("L") : "";
  const head = rpts[rpts.length - 1];
  const pA = pr(POI.pwh[0], POI.pwh[1], zt), pB = pr(POI.hkstp[0], POI.hkstp[1], zt);
  const pHK = pr(LB.hk[0], LB.hk[1], zt);

  const kick = f < 150 ? {t: "PEARL RIVER DELTA · SOUTH CHINA", op: fadeIO(f, 6, 100)} : {t: "HONG KONG · NEW TERRITORIES", op: fadeIO(f, 214, 600)};
  const boundaryOp = 0.55 * (1 - ramp(f, 190, 230));

  return <AbsoluteFill style={{background: COL.sea2, overflow: "hidden"}}>
    <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
      <defs>
        <radialGradient id="m111sea" cx="56%" cy="48%" r="75%">
          <stop offset="0%" stopColor={COL.sea0}/><stop offset="55%" stopColor={COL.sea1}/><stop offset="100%" stopColor={COL.sea2}/>
        </radialGradient>
        <filter id="m111blur" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation={glowW * 0.8}/></filter>
        <filter id="m111rblur" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation={7}/></filter>
        <clipPath id="m111hk"><path d={hk}/></clipPath>
      </defs>
      <rect width={W} height={H} fill="url(#m111sea)"/>
      {/* shallow water: a soft lighter-blue halo along every coast */}
      {layers.map((o, i) => <path key={"g" + i} d={o.top} fill="none" stroke={COL.shallow} strokeOpacity={0.55 * o.op} strokeWidth={glowW} filter="url(#m111blur)"/>)}
      {/* slab walls (visible once tilted), then tops: other land navy, Hong Kong black */}
      {layers.map((o, i) => o.base ? <path key={"w" + i} d={o.base} fill={COL.wall} fillOpacity={o.op}/> : null)}
      {layers.map((o, i) => <path key={"o" + i} d={o.top} fill={COL.other} fillOpacity={o.op}/>)}
      <g clipPath="url(#m111hk)">
        {layers.map((o, i) => <path key={"h" + i} d={o.top} fill={COL.land} fillOpacity={o.op}/>)}
        {layers.map((o, i) => <path key={"r" + i} d={o.top} fill="none" stroke={COL.rim} strokeOpacity={o.op} strokeWidth={1}/>)}
      </g>
      <Graticule pr={pr} fp={fp} s={s}/>
      {/* the Hong Kong boundary, dotted */}
      <path d={hkLine} fill="none" stroke={COL.ink} strokeOpacity={boundaryOp} strokeWidth={1.2} strokeDasharray="2 6" strokeLinecap="round"/>
      {/* the red line */}
      {pA && f < 246 ? <circle cx={pA[0]} cy={pA[1]} r={4.5} fill={COL.red} opacity={ramp(f, 118, 132)}/> : null}
      {rd && u > 0 ? <>
        <path d={rd} fill="none" stroke="#000" strokeOpacity={0.9} strokeWidth={30} strokeLinecap="round" strokeLinejoin="round" filter="url(#m111rblur)"/>
        <path d={rd} fill="none" stroke={COL.red} strokeOpacity={0.7} strokeWidth={14} strokeLinecap="round" strokeLinejoin="round" filter="url(#m111rblur)"/>
        <path d={rd} fill="none" stroke={COL.red} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round"/>
      </> : null}
      {head && u > 0 && u < 1 ? <circle cx={head[0]} cy={head[1]} r={7} fill={COL.red}/> : null}
    </svg>

    {/* place names */}
    {LABELS.map((l, i) => {
      const op = fadeIO(f, l.a, l.b, 12);
      if (op <= 0) return null;
      const p = pr(l.at[0], l.at[1], zt);
      if (!p || p[0] < -200 || p[0] > W + 200 || p[1] < -100 || p[1] > H + 100) return null;
      return <Label key={i} x={p[0]} y={p[1]} l={l} op={op}/>;
    })}
    {/* Hong Kong pinned on the delta */}
    <Pin at={pHK} dx={150} dy={-120} anchor="left" title="HONG KONG" op={fadeIO(f, 4, 90, 10)} dot={COL.red} r={6} ring={ramp(f, 6, 40)}/>
    {/* the two ends of the line */}
    <Pin at={pA} dx={-150} dy={70} title="PRINCE OF WALES HOSPITAL" sub="CUHK · SHA TIN" op={ramp(f, 238, 252)} ring={ramp(f, 240, 272)}/>
    <Pin at={pB} dx={-170} dy={-60} title="HONG KONG SCIENCE PARK" sub="PAK SHEK KOK" op={ramp(f, 292, 306)} ring={ramp(f, 296, 326)}/>

    {/* title block */}
    <div style={{position: "absolute", left: 96, top: 74, opacity: kick.op, fontFamily: MONO, fontSize: 13, letterSpacing: 4, color: COL.dim, whiteSpace: "pre"}}>{kick.t}</div>
    <div style={{position: "absolute", left: 90, top: 96, opacity: Math.min(ramp(f, 14, 30), 1 - ramp(f, 196, 222)), fontFamily: GROT, fontWeight: 800, fontSize: 96, letterSpacing: -3, color: COL.ink,
      transform: `translateY(${8 * (1 - inOut(ramp(f, 14, 34)))}px)`}}>Hong Kong</div>
    <div style={{position: "absolute", left: 92, top: 100, opacity: ramp(f, 222, 244), fontFamily: GROT, fontWeight: 600, fontSize: 54, letterSpacing: -1.5, color: COL.ink, whiteSpace: "pre",
      transform: `translateY(${6 * (1 - inOut(ramp(f, 222, 246)))}px)`}}>Sha Tin <span style={{color: COL.red}}>→</span> Pak Shek Kok</div>
    <ScaleBar s={s} op={ramp(f, 20, 36)}/>
    <div style={{position: "absolute", left: 96, bottom: 40, fontFamily: MONO, fontSize: 11, letterSpacing: 1.2, color: "rgba(237,235,228,0.6)"}}>{OSM_CREDIT}</div>
    <Finish grain={0.14} vignette={0.32}/>
  </AbsoluteFill>;
};
