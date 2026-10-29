// V3-S1-Open (rough animatic v3, W0 + 1-01). One vessel runs up the frame with the camera locked on its glowing tip.
// The camera pulls back: the vessel is a spine from bottom to top, and side branches sprout off it, bottom to top,
// until their tips spell PREDICT / DESIGN / TEST. The same spine + branches then slide into a liver (portal-vein-like),
// which sickens while four pixel hearts above it run out (or four lights inside it go out).
// Stand-in for the TouchDesigner pass: shapes and timing only.
import React, {useMemo} from "react";
import {AbsoluteFill, Sequence, staticFile, useCurrentFrame} from "remotion";
import {C, W, H, BoilProvider, hash, lerp, ramp, inOut, clamp01} from "../core";
import {Stage, InkDefs} from "../texture";
import {InkPath} from "../ink";
import {Mono} from "../type";
import {liverPts} from "../frames/Title";
import {OnCamCard} from "../oncam/Card";

export const S1_OPEN_FRAMES = 240; // W0 0–60, 1-01 60–240

const WORDS = [["PREDICT", 330], ["DESIGN", 590], ["TEST", 850]];
const FONT_FAMILY = `"Arial Black", Impact, sans-serif`;
const LEAVES = 1600, BANDS = 22;
const Y0 = 1190, Y1 = 130;                       // spine: bottom (off frame) → top
const LIVER = {x: 1010, y: 300, w: 820};
const LY1 = 318;                                 // liver spine top
const SICK = "#8E8A5A", LIVER_OK = "#6E1A10", LIVER_SICK = "#3E3C2C";

// timing (frames)
const RUN = [0, 80];          // the single vessel runs up
const PULL = [70, 132];       // camera pulls back
const SPROUT = [76, 128];     // branch bands start, bottom band first
const LEVEL = 6;              // frames per branching level
const MORPH = [150, 192], SWEEP = 14;
const OFF = [198, 209, 220, 231]; // the four lives go

const mix = (a, b, t) => {
  const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  return `rgb(${A.map((v, i) => Math.round(lerp(v, B[i], clamp01(t)))).join(",")})`;
};
const inside = (poly, x, y) => {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c;
  }
  return c;
};
const pick = (pts, n, seed) => pts.map((p, i) => [hash(i, seed), p]).sort((a, b) => a[0] - b[0]).slice(0, n).map(e => e[1]);
const centroid = pts => [pts.reduce((s, p) => s + p[0], 0) / pts.length, pts.reduce((s, p) => s + p[1], 0) / pts.length];

// spine as a function of s (0 bottom → 1 top); a slow S-curve so the run up has turns to follow
const spineT = s => [960 + 70 * Math.sin(s * 7.5) + 26 * Math.sin(s * 19 + 1), lerp(Y0, Y1, s)];
const spineL = s => [1370 + 22 * Math.sin(s * 6 + 0.5), lerp(Y0, LY1, s)];
const spineAt = (s, u) => { const a = spineT(s), b = spineL(s); return [lerp(a[0], b[0], u), lerp(a[1], b[1], u)]; };
const SPN = 160;
// loose blood cells around the vessel: fixed in the world, so they stream past while the camera runs up
const CELLS = Array.from({length: 150}, (_, i) => ({x: 960 + (hash(i, 41) - 0.5) * 700, y: lerp(Y0 + 60, Y1 - 80, hash(i, 43)),
  r: 1.5 + 3 * hash(i, 47), a: 0.25 + 0.5 * hash(i, 53), dx: (hash(i, 59) - 0.5) * 0.6}));

/** Halve along the longer side, recursively. Same sizes in → same tree shape out, so text and liver trees pair node for node. */
const splitTree = (pts, out, d = 0, parent = -1) => {
  const id = out.length;
  out.push({d, parent, c: centroid(pts), n: pts.length});
  if (pts.length === 1) return;
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const ax = Math.max(...xs) - Math.min(...xs) >= Math.max(...ys) - Math.min(...ys) ? 0 : 1;
  const s = [...pts].sort((a, b) => a[ax] - b[ax]), h = Math.floor(s.length / 2);
  splitTree(s.slice(0, h), out, d + 1, id);
  splitTree(s.slice(h), out, d + 1, id);
};
/** Each node walks ~2/(levels left) of the way from its parent toward its own centroid, so tips land exactly. */
const place = (nodes, root) => {
  const P = [];
  nodes.forEach((n, i) => {
    P[i] = n.parent < 0 ? root : [0, 1].map(a => lerp(P[n.parent][a], n.c[a], Math.min(1, 1.9 / (Math.ceil(Math.log2(n.n)) + 1))));
  });
  return P;
};

/** Leaves grouped by height band and side of the spine; each group is one branch leaving the spine at its band. */
const useNet = () => useMemo(() => {
  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const g = cv.getContext("2d");
  g.fillStyle = "#fff"; g.textAlign = "center"; g.font = `900 245px ${FONT_FAMILY}`;
  WORDS.forEach(([t, y]) => g.fillText(t, W / 2, y));
  const px = g.getImageData(0, 0, W, H).data, txt = [];
  for (let y = 0; y < H; y += 4) for (let x = 0; x < W; x += 4) if (px[(y * W + x) * 4 + 3] > 128) txt.push([x, y]);
  const lp = liverPts(LIVER.x, LIVER.y, LIVER.w), liv = [];
  for (let y = LIVER.y; y < LIVER.y + LIVER.w * 0.65; y += 6) for (let x = LIVER.x; x < LIVER.x + LIVER.w; x += 6) if (inside(lp, x, y)) liv.push([x, y]);

  const T = pick(txt, LEAVES, 3).sort((a, b) => b[1] - a[1]);   // bottom first
  const Lv = pick(liv, LEAVES, 5).sort((a, b) => b[1] - a[1]);
  const per = LEAVES / BANDS, nodes = [];
  for (let b = 0; b < BANDS; b++) {
    const tb = T.slice(Math.round(b * per), Math.round((b + 1) * per)).sort((p, q) => p[0] - q[0]);
    const lb = Lv.slice(Math.round(b * per), Math.round((b + 1) * per)).sort((p, q) => p[0] - q[0]);
    const sb = clamp01((Y0 - centroid(tb)[1]) / (Y0 - Y1));
    const nl = tb.filter(p => p[0] < spineT(sb)[0]).length;
    [[tb.slice(0, nl), lb.slice(0, nl)], [tb.slice(nl), lb.slice(nl)]].forEach(([gt, gl]) => {
      if (!gt.length) return;
      // leave the spine below the group, so the branch climbs up and out like a tree limb, not sideways
      const [gx, gy] = centroid(gt), s = clamp01((Y0 - gy - 0.6 * Math.abs(gx - spineT(sb)[0]) - 30) / (Y0 - Y1));
      const nt = [], nlv = [];
      splitTree(gt, nt);
      splitTree(gl, nlv);
      const pt = place(nt, spineT(s)), pl = place(nlv, spineL(s)), off = nodes.length;
      nt.forEach((n, i) => nodes.push({...n, parent: n.parent < 0 ? -1 : n.parent + off, s, t: pt[i], l: pl[i],
        delay: SWEEP * clamp01((n.c[0] - 240) / 1440)}));
    });
  }
  return nodes;
}, []);

// the run: eases in, then keeps going at speed
const runAt = f => { const t = ramp(f, RUN[0], RUN[1]); return t < 0.25 ? 2 * t * t : 0.125 + (t - 0.25) * (0.875 / 0.75); };
// camera: locked a little ahead of the running tip, then pulls back to the full frame (log-scale zoom so it never jumps)
const camAt = f => {
  const tip = spineT(runAt(f)), p = inOut(ramp(f, PULL[0], PULL[1]));
  return [Math.pow(4.2, 1 - p), lerp(tip[0], W / 2, p), lerp(tip[1] - 60, H / 2, p)];
};

// 9×8 pixel heart: O outline, R red, W highlight, D shade
const HEART = [".OO...OO.", "OWRO.ORRO", "OWRRORRRO", "ORRRRRRDO", ".ORRRRDO.", "..ORRDO..", "...ODO...", "....O...."];
const Heart = ({cell, lost, white = 0}) => <g>
  {HEART.flatMap((row, r) => [...row].map((ch, c) => {
    if (ch === ".") return null;
    const fill = ch === "O" ? (lost ? "#6A625C" : "#1B0B08")
      : mix(lost ? "#211C1A" : {R: C.verm, W: "#FFD8CC", D: "#B0220F"}[ch], "#FFFFFF", white);
    return <rect key={`${r}-${c}`} x={c * cell} y={r * cell} width={cell + 0.5} height={cell + 0.5} fill={fill}/>;
  }))}
</g>;

const Hearts = ({f}) => {
  const cell = 9, wid = 9 * cell, gap = 18, x0 = LIVER.x + LIVER.w / 2 - (4 * wid + 3 * gap) / 2, y0 = 200;
  const left = OFF.filter(o => f < o).length;
  const beat = Math.exp(-(f % 15) / 3);           // pulse with the blood, every half second
  return <g opacity={ramp(f, 172, 182)}>
    {OFF.map((off, i) => {
      const lost = f >= off, flash = lost ? Math.exp(-(f - off) / 2.5) : 0;
      const hit = lost ? Math.sin((f - off) * 2.6) * 8 * Math.exp(-(f - off) / 4) : 0;
      const jitter = !lost && left <= 2 ? (hash(f, i) - 0.5) * (3 - left) * 3 : 0;   // low on hearts: the rest tremble
      const k = lost ? 1 : 1 + 0.08 * beat;
      const cx = x0 + i * (wid + gap) + wid / 2 + hit, cy = y0 + 4 * cell + jitter;
      return <g key={i} transform={`translate(${cx} ${cy}) scale(${k}) translate(${-wid / 2} ${-4 * cell})`}>
        <Heart cell={cell} lost={lost} white={flash}/>
      </g>;
    })}
  </g>;
};

const Lights = ({f}) => <g opacity={ramp(f, 172, 180)}>
  {[[0.24, 0.24], [0.44, 0.17], [0.33, 0.40], [0.62, 0.29]].map(([a, b], i) => {
    const x = LIVER.x + a * LIVER.w, y = LIVER.y + b * LIVER.w, off = OFF[i];
    const on = ramp(f, 172 + i * 3, 180 + i * 3) * (1 - ramp(f, off, off + 6));
    const flash = f >= off ? Math.exp(-(f - off) / 3) : 0;
    return <g key={i}>
      <circle cx={x} cy={y} r={26} fill="#FFC77A" opacity={0.7 * on + 0.5 * flash} filter="url(#s1-glow)"/>
      <circle cx={x} cy={y} r={8} fill={mix("#FFE2B0", "#5A5650", 1 - on)}/>
    </g>;
  })}
</g>;

/** Quadratic edge a→b that leaves a along the incoming direction o→a, with a little sideways sag. */
const curve = (o, a, b, i) => {
  const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, dl = Math.hypot(a[0] - o[0], a[1] - o[1]) || 1;
  const bow = (hash(i, 31) - 0.5) * len * 0.35;
  const c = [a[0] + (a[0] - o[0]) / dl * len * 0.45 - (b[1] - a[1]) / len * bow, a[1] + (a[1] - o[1]) / dl * len * 0.45 + (b[0] - a[0]) / len * bow];
  return `M${a[0].toFixed(1)},${a[1].toFixed(1)} Q${c[0].toFixed(1)},${c[1].toFixed(1)} ${b[0].toFixed(1)},${b[1].toFixed(1)}`;
};

const Scene = ({lives}) => {
  const f = useCurrentFrame();
  const nodes = useNet();
  const [z, cx, cy] = camAt(f);
  const sick = ramp(f, 186, 236);
  const vein = mix(C.verm, SICK, sick), flow = mix("#FFB09A", "#D8D2A8", sick);
  const uS = inOut(ramp(f, MORPH[0], MORPH[1] + SWEEP / 2));
  // branch roots ride the (morphing) spine; everything else slides on its own, swept left to right
  const pos = nodes.map(n => {
    if (n.parent < 0) return spineAt(n.s, uS);
    const u = inOut(ramp(f, MORPH[0] + n.delay, MORPH[1] + n.delay));
    return [lerp(n.t[0], n.l[0], u), lerp(n.t[1], n.l[1], u)];
  });
  const spine = Array.from({length: SPN + 1}, (_, k) => k / SPN).filter(s => s <= runAt(f)).map(s => spineAt(s, uS));
  const spineD = "M" + spine.map(p => p.map(v => v.toFixed(1)).join(",")).join("L");
  const tip = spine[spine.length - 1];
  const liverPoly = liverPts(LIVER.x, LIVER.y, LIVER.w);
  return <svg width={W} height={H} style={{position: "absolute"}}>
    <InkDefs/>
    <defs><filter id="s1-glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="9"/></filter></defs>
    <g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}>
      <path d={"M" + liverPoly.map(p => p.join(",")).join("L") + "Z"} fill={mix(LIVER_OK, LIVER_SICK, sick)} opacity={0.6 * inOut(ramp(f, 168, 194))}/>

      <g opacity={1 - ramp(f, 96, 140)}>
        {CELLS.map((c, i) => <ellipse key={i} cx={c.x + c.dx * f} cy={c.y + 0.35 * f} rx={c.r * 1.4} ry={c.r} fill={C.verm} opacity={c.a}/>)}
      </g>
      {/* branches: a band starts as the pull-back passes it, bottom first; each level takes about LEVEL frames */}
      {nodes.map((n, i) => {
        if (n.parent < 0) return null;
        const st = lerp(SPROUT[0], SPROUT[1], n.s) + (n.d - 1) * LEVEL * 0.8, g = inOut(ramp(f, st, st + LEVEL * 1.3));
        if (g <= 0) return null;
        const p = nodes[n.parent], a = pos[n.parent], b = pos[i];
        const o = p.parent < 0 ? spineAt(Math.max(0, n.s - 0.03), uS) : pos[p.parent];
        const w = 0.9 + 6 * Math.sqrt(n.n / (LEAVES / BANDS / 2));
        return <g key={i}>
          <path d={curve(o, a, b, i)} pathLength={1} fill="none" stroke={vein} strokeWidth={w} strokeLinecap="round" strokeDasharray="1 1" strokeDashoffset={1 - g}/>
          {n.n === 1 && g >= 1 && <circle cx={b[0]} cy={b[1]} r={2.6} fill={vein}/>}
        </g>;
      })}
      {/* the words sit on top of the branches so they read at the hold */}
      <g opacity={0.62 * ramp(f, 118, 142) * (1 - inOut(ramp(f, 142, 160)))}>
        {WORDS.map(([t, y]) => <text key={t} x={W / 2} y={y} textAnchor="middle" fontFamily={FONT_FAMILY} fontWeight={900} fontSize={245} fill="#FF7A5C" style={{mixBlendMode: "screen"}}>{t}</text>)}
      </g>
      {/* the spine: one vessel, with a glowing tip while it runs */}
      {spine.length > 1 && <g>
        <path d={spineD} fill="none" stroke={vein} strokeWidth={13} strokeLinecap="round" strokeLinejoin="round"/>
        <path d={spineD} fill="none" stroke={flow} strokeWidth={5} strokeLinecap="round" strokeDasharray="14 46" strokeDashoffset={-f * 9} opacity={0.8}/>
        {f < RUN[1] + 10 && <g opacity={1 - ramp(f, RUN[1], RUN[1] + 10)}>
          <circle cx={tip[0]} cy={tip[1]} r={22} fill="#FF8A6A" opacity={0.8} filter="url(#s1-glow)"/>
          <circle cx={tip[0]} cy={tip[1]} r={7} fill="#FFE2D6"/>
        </g>}
      </g>}
      <g filter="url(#v3-ink)" opacity={ramp(f, 170, 180)}>
        <InkPath points={liverPoly} seed={301} size={9} progress={inOut(ramp(f, 170, 202))} pressure="brush" jitter={2}/>
      </g>
      {lives === "lights" && <Lights f={f}/>}
    </g>
    {lives === "hearts" && <Hearts f={f}/>}
    <Mono x={LIVER.x + LIVER.w / 2} y={880} size={22} anchor="middle" color={C.dim} letterSpacing={4} reveal={ramp(f, 196, 222)}>
      HONG KONG · ABOUT 4 A DAY
    </Mono>
    <Mono x={960} y={1050} size={16} color={C.dim} anchor="middle" letterSpacing={3}>
      {f < 60 ? "W0 · NO VOICE" : "1-01 · A: “In Hong Kong, about four people a day die of liver cancer.”"} · ROUGH ANIMATIC v3
    </Mono>
  </svg>;
};

export const V3S1Open = ({lives = "hearts"}) => <BoilProvider rate={2.5}>
  <Stage grain={0.16}>
    <Scene lives={lives}/>
    {/* A's voice starts at 1-01 over the vessel; the face comes in as the tree heads for the liver */}
    <Sequence from={148} durationInFrames={92}>
      <AbsoluteFill><OnCamCard who="A" src={staticFile("placeholder_hand.mp4")} videoStart={0} dur={92}/></AbsoluteFill>
    </Sequence>
  </Stage>
</BoilProvider>;
