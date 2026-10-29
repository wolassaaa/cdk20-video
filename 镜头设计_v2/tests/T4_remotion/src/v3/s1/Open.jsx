// V3-S1-Open (rough animatic v2, W0 + 1-01). One vessel enters from below and keeps forking (11 levels, 2048 tips).
// The camera rides up the trunk and pulls back: the tips spell PREDICT / DESIGN / TEST. The same tree then slides,
// node by node, into a liver, which sickens while four lives go out (lights or pixel hearts).
// Stand-in for the TouchDesigner pass: shapes and timing only.
import React, {useMemo} from "react";
import {AbsoluteFill, Sequence, staticFile, useCurrentFrame} from "remotion";
import {C, W, H, BoilProvider, hash, lerp, ramp, inOut, outCubic, clamp01} from "../core";
import {Stage, InkDefs} from "../texture";
import {InkPath} from "../ink";
import {Mono} from "../type";
import {liverPts} from "../frames/Title";
import {OnCamCard} from "../oncam/Card";

export const S1_OPEN_FRAMES = 240; // W0 0–60, 1-01 60–240

const WORDS = [["PREDICT", 330], ["DESIGN", 590], ["TEST", 850]];
const FONT_FAMILY = `"Arial Black", Impact, sans-serif`;
const L = 11, LEAVES = 1 << L;
const ROOT_T = [960, 1190], ROOT_L = [1330, 1190];
const LIVER = {x: 1010, y: 300, w: 820};
const SICK = "#8E8A5A", LIVER_OK = "#6E1A10", LIVER_SICK = "#3E3C2C";

// growth: level k edges start at T[k], take D[k] frames; each level starts when its parent is ~80% grown
const D = Array.from({length: L}, (_, k) => lerp(20, 8, Math.pow(k / (L - 1), 0.7)));
const T = D.reduce((a, d, k) => [...a, a[k] + 0.8 * d], [0]);
const MORPH = [140, 182], SWEEP = 14;     // letters → liver, sweeping left to right

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

/** Halve the point set along its longer side, recursively: every tree built this way has the same shape. */
const splitTree = (pts, out, d = 0, parent = -1) => {
  const id = out.length;
  out.push({d, parent, c: centroid(pts), n: pts.length});
  if (d === L) return;
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const ax = Math.max(...xs) - Math.min(...xs) >= Math.max(...ys) - Math.min(...ys) ? 0 : 1;
  const s = [...pts].sort((a, b) => a[ax] - b[ax]), h = s.length / 2;
  splitTree(s.slice(0, h), out, d + 1, id);
  splitTree(s.slice(h), out, d + 1, id);
};
/** Node positions: each level walks ~2/(levels left) of the way from its parent toward its own centroid, so tips land exactly. */
const place = (nodes, root) => {
  const P = [];
  nodes.forEach((n, i) => { P[i] = n.parent < 0 ? root : [0, 1].map(a => lerp(P[n.parent][a], n.c[a], Math.min(1, 1.9 / (L - n.d + 1)))); });
  return P;
};

const useTree = () => useMemo(() => {
  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const g = cv.getContext("2d");
  g.fillStyle = "#fff"; g.textAlign = "center"; g.font = `900 245px ${FONT_FAMILY}`;
  WORDS.forEach(([t, y]) => g.fillText(t, W / 2, y));
  const px = g.getImageData(0, 0, W, H).data, txt = [];
  for (let y = 0; y < H; y += 4) for (let x = 0; x < W; x += 4) if (px[(y * W + x) * 4 + 3] > 128) txt.push([x, y]);
  const lp = liverPts(LIVER.x, LIVER.y, LIVER.w), liv = [];
  for (let y = LIVER.y; y < LIVER.y + LIVER.w * 0.65; y += 6) for (let x = LIVER.x; x < LIVER.x + LIVER.w; x += 6) if (inside(lp, x, y)) liv.push([x, y]);
  const nt = [], nl = [];
  splitTree(pick(txt, LEAVES, 3), nt);
  splitTree(pick(liv, LEAVES, 5), nl);
  const pt = place(nt, ROOT_T), pl = place(nl, ROOT_L);
  const meanY = Array.from({length: L + 1}, (_, k) => { const ys = pt.filter((_, i) => nt[i].d === k).map(p => p[1]); return ys.reduce((a, b) => a + b, 0) / ys.length; });
  return {nodes: nt.map((n, i) => ({d: n.d, parent: n.parent, n: n.n, t: pt[i], l: pl[i], delay: SWEEP * clamp01((nt[i].c[0] - 240) / 1440)})), meanY};
}, []);

// camera: rides up with the growth front while zooming out (log-scale zoom so it never jumps), then settles on the full frame
const camAt = (f, meanY) => {
  let k = 0;
  while (k < L && f > T[k] + D[k]) k++;
  const fr = k >= L ? 1 : clamp01((f - T[k]) / D[k]);
  const front = k >= L ? meanY[L] : lerp(meanY[k], meanY[k + 1], fr);
  const z = Math.pow(5.2, 1 - inOut(ramp(f, 0, 126)));
  const y = lerp(front, H / 2, inOut(ramp(f, 40, 126)));
  return [z, W / 2, y];
};

const PIX_HEART = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."];
const Heart = ({x, y, cell, fill, stroke}) => <g>
  {PIX_HEART.flatMap((row, r) => [...row].map((ch, c) => ch === "X" &&
    <rect key={`${r}-${c}`} x={x + c * cell} y={y + r * cell} width={cell} height={cell} fill={fill} stroke={stroke} strokeWidth={stroke ? 2 : 0}/>))}
</g>;

const OFF = [192, 205, 218, 231];

const Lives = ({f, lives, P}) => {
  if (lives === "hearts") {
    const cell = 9, gap = 22, wid = 7 * cell, x0 = LIVER.x + LIVER.w / 2 - (4 * wid + 3 * gap) / 2, y0 = 232;
    return <g opacity={ramp(f, 170, 180)}>
      {OFF.map((off, i) => {
        const lost = f >= off, flash = lost ? Math.exp(-(f - off) / 2.5) : 0;
        const shake = lost ? Math.sin((f - off) * 2.4) * 7 * Math.exp(-(f - off) / 4) : 0;
        const x = x0 + i * (wid + gap) + shake;
        return <g key={i}>
          <Heart x={x} y={y0} cell={cell} fill={lost ? "#1A1716" : C.verm} stroke={lost ? "#5A5650" : undefined}/>
          {flash > 0.02 && <g opacity={flash}><Heart x={x} y={y0} cell={cell} fill="#FFFFFF"/></g>}
        </g>;
      })}
    </g>;
  }
  return <g opacity={ramp(f, 172, 180)}>
    {[[0.24, 0.24], [0.44, 0.17], [0.33, 0.40], [0.62, 0.29]].map(([a, b], i) => {
      const [x, y] = P(a, b), off = OFF[i];
      const on = ramp(f, 172 + i * 3, 180 + i * 3) * (1 - ramp(f, off, off + 6));
      const flash = f >= off ? Math.exp(-(f - off) / 3) : 0;
      return <g key={i}>
        <circle cx={x} cy={y} r={26} fill="#FFC77A" opacity={0.7 * on + 0.5 * flash} filter="url(#s1-glow)"/>
        <circle cx={x} cy={y} r={8} fill={mix("#FFE2B0", "#5A5650", 1 - on)}/>
      </g>;
    })}
  </g>;
};

const Scene = ({lives}) => {
  const f = useCurrentFrame();
  const {nodes, meanY} = useTree();
  const [z, cx, cy] = camAt(f, meanY);
  const sick = ramp(f, 178, 236);
  const vein = mix(C.verm, SICK, sick), flow = mix("#FFB09A", "#D8D2A8", sick);
  const pos = nodes.map(n => { const u = inOut(ramp(f, MORPH[0] + n.delay, MORPH[1] + n.delay)); return [lerp(n.t[0], n.l[0], u), lerp(n.t[1], n.l[1], u)]; });
  const P = (a, b) => [LIVER.x + a * LIVER.w, LIVER.y + b * LIVER.w];
  const liverPoly = liverPts(LIVER.x, LIVER.y, LIVER.w);
  return <svg width={W} height={H} style={{position: "absolute"}}>
    <InkDefs/>
    <defs><filter id="s1-glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="9"/></filter></defs>
    <g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}>
      <path d={"M" + liverPoly.map(p => p.join(",")).join("L") + "Z"} fill={mix(LIVER_OK, LIVER_SICK, sick)} opacity={0.6 * inOut(ramp(f, 160, 186))}/>
      <g opacity={0.3 * ramp(f, 104, 128) * (1 - inOut(ramp(f, 128, 146)))}>
        {WORDS.map(([t, y]) => <text key={t} x={W / 2} y={y} textAnchor="middle" fontFamily={FONT_FAMILY} fontWeight={900} fontSize={245} fill={C.verm}>{t}</text>)}
      </g>
      {nodes.map((n, i) => {
        if (n.parent < 0) return null;
        const k = n.d - 1, g = inOut(ramp(f, T[k], T[k] + D[k]));
        if (g <= 0) return null;
        const a = pos[n.parent], b = pos[i];
        const gp = nodes[n.parent].parent, o = gp < 0 ? [a[0], a[1] + 1] : pos[gp];
        const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, dl = Math.hypot(a[0] - o[0], a[1] - o[1]) || 1;
        const bow = (hash(i, 31) - 0.5) * len * 0.35; // a little sideways sag so branches don't read as ruled lines
        const c1 = [a[0] + (a[0] - o[0]) / dl * len * 0.45 - (b[1] - a[1]) / len * bow, a[1] + (a[1] - o[1]) / dl * len * 0.45 + (b[0] - a[0]) / len * bow];
        const d = `M${a[0].toFixed(1)},${a[1].toFixed(1)} Q${c1[0].toFixed(1)},${c1[1].toFixed(1)} ${b[0].toFixed(1)},${b[1].toFixed(1)}`;
        const w = 0.9 + 12 * Math.sqrt(n.n / LEAVES);
        return <g key={i}>
          <path d={d} pathLength={1} fill="none" stroke={vein} strokeWidth={w} strokeLinecap="round" strokeDasharray="1 1" strokeDashoffset={1 - g}/>
          {n.d <= 7 && g >= 1 && <path d={d} pathLength={1} fill="none" stroke={flow} strokeWidth={w * 0.45} strokeLinecap="round"
            strokeDasharray="0.06 0.3" strokeDashoffset={-(f * 0.05 + hash(i, 4))} opacity={0.75}/>}
          {n.d === L && g >= 1 && <circle cx={b[0]} cy={b[1]} r={2.6} fill={vein}/>}
        </g>;
      })}
      <g filter="url(#v3-ink)" opacity={ramp(f, 162, 172)}>
        <InkPath points={liverPoly} seed={301} size={9} progress={inOut(ramp(f, 162, 196))} pressure="brush" jitter={2}/>
      </g>
      {lives === "lights" && <Lives f={f} lives={lives} P={P}/>}
    </g>
    {lives === "hearts" && <Lives f={f} lives={lives} P={P}/>}
    <Mono x={LIVER.x + LIVER.w / 2} y={880} size={22} anchor="middle" color={C.dim} letterSpacing={4} reveal={ramp(f, 188, 214)}>
      HONG KONG · ABOUT 4 A DAY
    </Mono>
    <Mono x={960} y={1050} size={16} color={C.dim} anchor="middle" letterSpacing={3}>
      {f < 60 ? "W0 · NO VOICE" : "1-01 · A: “In Hong Kong, about four people a day die of liver cancer.”"} · ROUGH ANIMATIC v2
    </Mono>
  </svg>;
};

export const V3S1Open = ({lives = "lights"}) => <BoilProvider rate={2.5}>
  <Stage grain={0.16}>
    <Scene lives={lives}/>
    {/* A's voice starts at 1-01 over the letters; the face comes in as the tree heads for the liver */}
    <Sequence from={140} durationInFrames={100}>
      <AbsoluteFill><OnCamCard who="A" src={staticFile("placeholder_hand.mp4")} videoStart={0} dur={100}/></AbsoluteFill>
    </Sequence>
  </Stage>
</BoilProvider>;
