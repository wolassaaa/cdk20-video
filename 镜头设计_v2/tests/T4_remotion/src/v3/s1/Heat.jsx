// V3-S1-Heat (rough animatic, W0 + 1-01): the opening told in heat. Life is warm, loss is cooling, the computer is cold cyan.
// Hit 1: a hot point. Hit 2: it shoots up, its trail cooling behind it. Hit 3: it floods a vessel tree like contrast dye,
// and the camera pulls back on a warm liver. 1-01: four heartbeat hot spots stop and go cold, one by one.
// Everything inside the scene is drawn as heat (white on black) and mapped to false colour by ThermalFilter.
import React, {useMemo} from "react";
import {AbsoluteFill, Sequence, staticFile, useCurrentFrame} from "remotion";
import {C, W, H, BoilProvider, useBoil, hash, lerp, ramp, inOut, clamp01} from "../core";
import {Stage} from "../texture";
import {Mono} from "../type";
import {liverPts} from "../frames/Title";
import {OnCamCard} from "../oncam/Card";
import {ThermalFilter, heatColor} from "../thermal";
import {inside, pick, splitTree, place} from "./Open";

export const S1_HEAT_FRAMES = 240; // W0 0–60, 1-01 60–240

const LIVER = {x: 560, y: 250, w: 800};
const LP = (a, b) => [LIVER.x + a * LIVER.w, LIVER.y + b * LIVER.w];
const HILUM = LP(0.55, 0.47);
const START = [930, 1200];
const LEAVES = 1024;

// timing (frames)
const HIT = [4, 24, 46];               // the three percussion hits
const RUN = [24, 46];                  // hot point runs from START to the hilum
const FILL = [46, 4.5, 8];             // tree fill: start, frames per level, frames per edge
const PULL = [40, 108];                // camera pull-back
const DIE = [150, 170, 190, 210];      // the four spots stop
const SPOTS = [[0.25, 0.24, 19], [0.42, 0.15, 23], [0.33, 0.37, 17], [0.63, 0.28, 21]]; // position, beat period

// the run: one vessel from below the frame up into the liver's hilum, with two slow bends
const runPt = s => [lerp(START[0], HILUM[0], s) + 46 * Math.sin(s * 6.3), lerp(START[1], HILUM[1], s)];
const runS = f => { const t = ramp(f, RUN[0], RUN[1]); return 1 - Math.pow(1 - t, 1.6); };
const RUNN = 90;

const useTree = () => useMemo(() => {
  const lp = liverPts(LIVER.x, LIVER.y, LIVER.w), pts = [];
  for (let y = LIVER.y; y < LIVER.y + LIVER.w * 0.65; y += 7) for (let x = LIVER.x; x < LIVER.x + LIVER.w; x += 7) if (inside(lp, x, y)) pts.push([x, y]);
  const nodes = [];
  splitTree(pick(pts, LEAVES, 7), nodes);
  const P = place(nodes, HILUM);
  return nodes.map((n, i) => ({...n, p: P[i]}));
}, []);

// camera: close on the point, rides the run, then pulls back and settles with the liver on the right (card goes left)
const camAt = f => {
  const tip = runPt(runS(f)), u = inOut(ramp(f, PULL[0], PULL[1]));
  return [Math.pow(3.2, 1 - u), lerp(tip[0], W / 2 - 400, u), lerp(tip[1] - 30, H / 2 + 20, u)];
};

/** A hot blob: three nested discs, so the core maps hotter than the rim. */
const Hot = ({x, y, r, h}) => <g filter="url(#s1-hot)">
  <circle cx={x} cy={y} r={r * 2.4} fill="#fff" opacity={0.28 * h}/>
  <circle cx={x} cy={y} r={r * 1.4} fill="#fff" opacity={Math.min(1, 0.5 * h)}/>
  <circle cx={x} cy={y} r={r * 0.6} fill="#fff" opacity={Math.min(1, 1.1 * h)}/>
  <circle cx={x} cy={y} r={r * 0.3} fill="#fff" opacity={Math.min(1, h)}/>
</g>;

/** A warm tube: wide cool rim, warmer body, hot core. */
const Tube = ({d, w, h, g = 1}) => <g>
  {[[2.4, 0.3], [1.4, 0.55], [0.5, 0.95]].map(([k, o], i) => <path key={i} d={d} pathLength={1} fill="none" stroke="#fff" strokeWidth={w * k}
    strokeLinecap="round" opacity={o * h} strokeDasharray="1 1" strokeDashoffset={1 - g}/>)}
</g>;

const Scene = () => {
  const f = useCurrentFrame(), b = useBoil();
  const tree = useTree();
  const [z, cx, cy] = camAt(f);
  const dead = DIE.filter(t => f >= t).length;
  const lp = liverPts(LIVER.x, LIVER.y, LIVER.w);
  const s = runS(f);
  // the trail: each bit of the vessel is hottest when the point passes it, then cools to a steady warmth once the tree fills
  const run = Array.from({length: RUNN + 1}, (_, k) => k / RUNN).filter(q => q <= s);
  const passed = q => lerp(RUN[0], RUN[1], 1 - Math.pow(1 - q, 1 / 1.6));
  const settle = inOut(ramp(f, 70, 110));
  const tipHeat = 1 - ramp(f, RUN[1], RUN[1] + 8);
  const pop = f < HIT[1] ? 0.7 + 0.3 * Math.exp(-(f - HIT[0]) / 4) : 1;
  const tip = runPt(s);
  return <svg width={W} height={H} style={{position: "absolute"}}>
    <defs>
      <ThermalFilter id="s1-heat" seed={(b % 97) + 1} blur={1.6}/>
      <filter id="s1-hot" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="7"/></filter>
      <filter id="s1-soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>
      <filter id="s1-softer" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="40"/></filter>
    </defs>
    <g filter="url(#s1-heat)">
      <rect width={W} height={H} fill="#000"/>
      <g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}>
        {/* perfusion: the organ warms as the tree fills, and cools a little with each loss */}
        <path d={"M" + lp.map(p => p.join(",")).join("L") + "Z"} fill="#fff" opacity={0.62 * inOut(ramp(f, 64, 112)) * (1 - 0.13 * dead) - 0.06 * ramp(f, DIE[3], DIE[3] + 30)} filter="url(#s1-soft)"/>
        {/* vessel tree, filling level by level like contrast dye */}
        {tree.map((n, i) => {
          if (n.parent < 0) return null;
          const st = FILL[0] + (n.d - 1) * FILL[1], g = inOut(ramp(f, st, st + FILL[2]));
          if (g <= 0) return null;
          const a = tree[n.parent].p, q = n.p, gp = tree[n.parent].parent;
          const o = gp < 0 ? runPt(0.97) : tree[gp].p;
          const len = Math.hypot(q[0] - a[0], q[1] - a[1]) || 1, dl = Math.hypot(a[0] - o[0], a[1] - o[1]) || 1;
          const bow = (hash(i, 31) - 0.5) * len * 0.35;
          const c = [a[0] + (a[0] - o[0]) / dl * len * 0.45 - (q[1] - a[1]) / len * bow, a[1] + (a[1] - o[1]) / dl * len * 0.45 + (q[0] - a[0]) / len * bow];
          const d = `M${a[0].toFixed(1)},${a[1].toFixed(1)} Q${c[0].toFixed(1)},${c[1].toFixed(1)} ${q[0].toFixed(1)},${q[1].toFixed(1)}`;
          const fresh = Math.exp(-Math.max(0, f - st - FILL[2]) / 10);
          const h = (0.62 + 0.38 * fresh) * (1 - 0.1 * dead);
          return <Tube key={i} d={d} w={0.7 + 5.5 * Math.sqrt(n.n / LEAVES)} h={h} g={g}/>;
        })}
        {/* the run: short segments, each cooling after the point passes */}
        {run.slice(1).map((q, k) => {
          const a = runPt(run[k]), p = runPt(q);
          const h = lerp(0.45 + 0.55 * Math.exp(-Math.max(0, f - passed(q)) / 9), 0.7 * (1 - 0.15 * dead), settle);
          return <Tube key={k} d={`M${a[0]},${a[1]} L${p[0]},${p[1]}`} w={7} h={h}/>;
        })}
        {f >= HIT[0] && tipHeat > 0 && <Hot x={tip[0]} y={tip[1]} r={14 * pop} h={tipHeat}/>}
        {/* four lives: hot spots beating at their own rates; each stops, fades, and leaves a cold hole */}
        {SPOTS.map(([u, v, per], i) => {
          const [x, y] = LP(u, v), t = DIE[i], on = ramp(f, 104 + i * 4, 116 + i * 4);
          const beat = Math.exp(-(((f + i * 7) % per)) / 3.5);
          const alive = f < t;
          const h = alive ? on * (0.7 + 0.3 * beat) : 0.85 * Math.exp(-(f - t) / 7);
          const cold = alive ? 0 : inOut(ramp(f, t, t + 24));
          return <g key={i}>
            <circle cx={x} cy={y} r={58} fill="#000" opacity={0.85 * cold} filter="url(#s1-softer)"/>
            {h > 0.01 && <Hot x={x} y={y} r={19 * (alive ? 1 + 0.18 * beat : 1)} h={1.5 * h}/>}
          </g>;
        })}
      </g>
    </g>
    {/* camera UI, drawn outside the heat map: the computer's cold voice */}
    <g opacity={ramp(f, 96, 116)}>
      <Mono x={1040} y={92} size={17} color={C.cyan} letterSpacing={3}>THERMAL VIEW · ILLUSTRATIVE</Mono>
      {Array.from({length: 40}, (_, k) => <rect key={k} x={1836} y={180 + k * 14} width={22} height={14} fill={heatColor(1 - k / 39)}/>)}
      <Mono x={1826} y={172} size={14} color={C.dim} anchor="end">WARM</Mono>
      <Mono x={1826} y={752} size={14} color={C.dim} anchor="end">COLD</Mono>
    </g>
    <Mono x={1040} y={960} size={24} color={C.cyan} letterSpacing={4} reveal={ramp(f, DIE[0], DIE[0] + 26)}>HONG KONG · ABOUT 4 PEOPLE A DAY</Mono>
    <Mono x={960} y={1050} size={16} color={C.dim} anchor="middle" letterSpacing={3}>
      {f < 60 ? "W0 · NO VOICE · THREE HITS" : "1-01 · A: “In Hong Kong, about four people a day die of liver cancer.”"} · ROUGH ANIMATIC · HEAT
    </Mono>
  </svg>;
};

export const V3S1Heat = () => <BoilProvider rate={2.5}>
  <Stage grain={0.1} blotch={0}>
    <Scene/>
    {/* A's voice starts at 1-01 over the run; the face arrives as a heat image and develops into the warm print */}
    <Sequence from={112} durationInFrames={128}>
      <AbsoluteFill><OnCamCard who="A" src={staticFile("placeholder_hand.mp4")} videoStart={0} dur={128} thermal={[18, 34]}/></AbsoluteFill>
    </Sequence>
  </Stage>
</BoilProvider>;
