// V3-S1-Open (rough animatic, W0 + 1-01): red vessels grow toward a close, low camera, the camera pulls back and the
// vessels turn out to spell PREDICT / DESIGN / TEST; then they unweave into a liver that sickens while four lights go out.
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
const FONT = `900 245px "Arial Black", Impact, sans-serif`;
const N = 1100, TRUNKS = 64;
const LIVER = {x: 1010, y: 300, w: 820};
const SICK = "#9A8A3E", LIVER_OK = "#6E1A10", LIVER_SICK = "#4A4424";

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

/** Strand targets on the letters and in the liver, grouped into trunks that leave the bottom edge together. */
const useStrands = () => useMemo(() => {
  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const g = cv.getContext("2d");
  g.fillStyle = "#fff"; g.textAlign = "center"; g.font = FONT;
  WORDS.forEach(([t, y]) => g.fillText(t, W / 2, y));
  const d = g.getImageData(0, 0, W, H).data;
  const txt = [];
  for (let y = 0; y < H; y += 5) for (let x = 0; x < W; x += 5) if (d[(y * W + x) * 4 + 3] > 128) txt.push([x, y]);
  const lp = liverPts(LIVER.x, LIVER.y, LIVER.w), liv = [];
  for (let y = LIVER.y; y < LIVER.y + LIVER.w * 0.65; y += 9) for (let x = LIVER.x; x < LIVER.x + LIVER.w; x += 9) if (inside(lp, x, y)) liv.push([x, y]);
  const T = pick(txt, N, 3).sort((a, b) => a[0] - b[0]);
  const L = pick(liv, N, 5).sort((a, b) => a[0] - b[0]);
  return T.map((t, i) => {
    const k = Math.floor(i / (N / TRUNKS));
    return {t, l: L[i], k, sx: 140 + (W - 280) * (k + 0.5) / TRUNKS + (hash(k, 9) - 0.5) * 60,
      bend: (hash(k, 11) - 0.5) * 260, fan: (hash(i, 13) - 0.5) * 120, ph: hash(i, 23)};
  }).map(s => ({...s, start: 44 * Math.abs(s.sx - 940) / 840 + 8 * hash(s.k, 17) + 8 * hash(s.ph * 1e4, 19)}));
}, []);

/** One thick trunk per bundle, from below the frame up to where its strands fan out. */
const trunkPath = (s, u) => {
  const sx = lerp(s.sx, 1260 + (s.sx - W / 2) * 0.12, u), sy = H + 160, split = lerp(sy, lerp(600, 560, u), 0.33);
  return {sx, sy, x2: sx + s.bend * 0.45, y2: split};
};

// camera: [frame, zoom, centre x, centre y]
const CAM = [[0, 4.6, 940, 960], [62, 3.1, 980, 640], [78, 2.8, 960, 600], [122, 1, 960, 540]];
const camAt = f => {
  let i = 0;
  while (i < CAM.length - 2 && f > CAM[i + 1][0]) i++;
  const [f0, z0, x0, y0] = CAM[i], [f1, z1, x1, y1] = CAM[i + 1];
  const u = inOut(ramp(f, f0, f1));
  return [lerp(z0, z1, u), lerp(x0, x1, u), lerp(y0, y1, u)];
};

const LIGHTS = [[0.24, 0.24, 190], [0.44, 0.17, 203], [0.33, 0.40, 216], [0.62, 0.29, 229]];

const Scene = () => {
  const f = useCurrentFrame();
  const S = useStrands();
  const [z, cx, cy] = camAt(f);
  const u = inOut(ramp(f, 132, 176));          // letters → liver
  const sick = ramp(f, 176, 236);
  const vein = mix(C.verm, SICK, sick), flow = mix("#FFB09A", "#D8CC8A", sick);
  const P = (a, b) => [LIVER.x + a * LIVER.w, LIVER.y + b * LIVER.w];
  return <svg width={W} height={H} style={{position: "absolute"}}>
    <InkDefs/>
    <defs>
      <linearGradient id="s1-fade" gradientUnits="userSpaceOnUse" x1="0" y1={H + 200} x2="0" y2="200">
        <stop offset="0" stopColor="#fff" stopOpacity="0.25"/><stop offset="1" stopColor="#fff" stopOpacity="1"/>
      </linearGradient>
      <mask id="s1-mask"><rect x={-W} y={-H} width={W * 3} height={H * 3} fill="url(#s1-fade)"/></mask>
      <filter id="s1-glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="9"/></filter>
    </defs>
    <g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}>
      {/* liver body under the vessels */}
      <path d={"M" + liverPts(LIVER.x, LIVER.y, LIVER.w).map(p => p.join(",")).join("L") + "Z"}
        fill={mix(LIVER_OK, LIVER_SICK, sick)} opacity={0.55 * outCubic(ramp(f, 150, 180))}/>
      {/* letters, faintly filled once the camera is far enough back to read them */}
      <g opacity={0.5 * ramp(f, 92, 124) * (1 - u)}>
        {WORDS.map(([t, y]) => <text key={t} x={W / 2} y={y} textAnchor="middle" fontFamily={`"Arial Black", Impact, sans-serif`}
          fontWeight={900} fontSize={245} fill={C.verm}>{t}</text>)}
      </g>
      <g mask="url(#s1-mask)">
        {S.map((s, i) => {
          const grow = outCubic(ramp(f, s.start + 4, s.start + 44));
          if (grow <= 0) return null;
          const tx = lerp(s.t[0], s.l[0], u), ty = lerp(s.t[1], s.l[1], u);
          const tr = trunkPath(s, u), tg = outCubic(ramp(f, s.start - 6, s.start + 10));
          const d = `M${tr.x2},${tr.y2} C${tr.x2 + s.bend * 0.4},${lerp(tr.y2, ty, 0.35)} ${tx + s.fan},${lerp(tr.y2, ty, 0.75)} ${tx},${ty}`;
          const first = i % (N / TRUNKS) < 1;
          return <g key={i}>
            {first && <path d={`M${tr.sx},${tr.sy} Q${tr.sx + s.bend * 0.1},${(tr.sy + tr.y2) / 2} ${tr.x2},${tr.y2}`} pathLength={1} fill="none"
              stroke={vein} strokeWidth={7} strokeLinecap="round" strokeDasharray="1 1" strokeDashoffset={1 - tg} opacity={0.9}/>}
            <path d={d} pathLength={1} fill="none" stroke={vein} strokeWidth={1.5} strokeDasharray="1 1" strokeDashoffset={1 - grow} opacity={0.75}/>
            {grow > 0.98 && <path d={d} pathLength={1} fill="none" stroke={flow} strokeWidth={1.1} strokeDasharray="0.035 0.2"
              strokeDashoffset={-(f * 0.011 + s.ph)} opacity={0.8}/>}
            {grow > 0.98 && <circle cx={tx} cy={ty} r={2.2} fill={vein}/>}
          </g>;
        })}
      </g>
      {/* liver outline and the four lights */}
      <g filter="url(#v3-ink)" opacity={ramp(f, 158, 166)}>
        <InkPath points={liverPts(LIVER.x, LIVER.y, LIVER.w)} seed={301} size={9} progress={outCubic(ramp(f, 158, 192))} pressure="brush" jitter={2}/>
      </g>
      {LIGHTS.map(([a, b, off], i) => {
        const [x, y] = P(a, b), on = ramp(f, 172 + i * 3, 180 + i * 3) * (1 - ramp(f, off, off + 6));
        const flash = Math.exp(-Math.max(0, f - off) / 3) * (f >= off ? 1 : 0);
        return <g key={i} opacity={ramp(f, 172, 180)}>
          <circle cx={x} cy={y} r={26} fill="#FFC77A" opacity={0.7 * on + 0.5 * flash} filter="url(#s1-glow)"/>
          <circle cx={x} cy={y} r={8} fill={mix("#FFE2B0", "#5A5650", 1 - on)}/>
        </g>;
      })}
    </g>
    <Mono x={LIVER.x + LIVER.w / 2} y={880} size={22} anchor="middle" color={C.dim} letterSpacing={4} reveal={ramp(f, 186, 214)}>
      HONG KONG · ABOUT 4 A DAY
    </Mono>
    <Mono x={960} y={1050} size={16} color={C.dim} anchor="middle" letterSpacing={3}>
      {f < 60 ? "W0 · NO VOICE" : "1-01 · A: “In Hong Kong, about four people a day die of liver cancer.”"} · ROUGH ANIMATIC
    </Mono>
  </svg>;
};

export const V3S1Open = () => <BoilProvider rate={2.5}>
  <Stage grain={0.16}>
    <Scene/>
    {/* A's voice starts at 1-01 over the letters; the face comes in once the vessels head for the liver */}
    <Sequence from={140} durationInFrames={100}>
      <AbsoluteFill><OnCamCard who="A" src={staticFile("placeholder_hand.mp4")} videoStart={0} dur={100}/></AbsoluteFill>
    </Sequence>
  </Stage>
</BoilProvider>;
