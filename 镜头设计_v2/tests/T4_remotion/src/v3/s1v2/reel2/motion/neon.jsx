// 1-09 · neon metro, animated. Same scene as s108 RoadNeon (Blender, blood red), rendered in four layers by
// 镜头设计_v3/styleframes/S1/v2/_code/reel2/motion/neon_layers.py:
//   base  = unlit tube, dark stations, no beads      line  = tube lit, stations dark
//   st    = tube + stations lit                      beads = + the hanging bead columns (attrition)
// The line is revealed left to right as D names each step; each station flicks on like a neon tube; the beads drop at "Any step can fail."
// D's line (script v3.3, 01:16–01:36), estimated word times (s from the start of the beat):
//   To see why, let's follow one drug's journey. (0.2–3.2) Every medicine walks the same road. (3.5–5.6)
//   Find a target. (6.0–7.0) Find a hit, a first molecule that works on it. (7.3–10.9) Improve it. (11.1–11.9)
//   Test it in cells, then animals. (12.2–14.3) Then human trials: phase one, two, three. (14.6–17.0) Then approval. (17.3–18.2)
//   Any step can fail. (18.5–19.7)
import React from "react";
import {AbsoluteFill, Img, staticFile} from "remotion";
import {ramp, outExpo, outCubic, inOut} from "../../../core";
import {useFrame30} from "../../../time30";
import {Print, Tag, Svg, GText, MText, P, ST, W, H} from "../../s108/common";

export const DUR_109 = 600;
const sec = s => Math.round(s * 30);

// scene -> screen (the neon camera is near-orthographic on the wall; fitted to s108 anch.json "neon")
const sx = X => 155.2 + (X + 7.8) * 107.32, sz = Z => 325.5 + (3.0 - Z) * 107.2;
const PATH = [[-11.5, 3.0], [-2.0, 3.0], [1.7, -0.7], [11.5, -0.7]].map(([x, z]) => [sx(x), sz(z)]);
const STX = [[-7.8, 3.0], [-5.3, 3.0], [-2.8, 3.0], [2.6, -0.7], [4.9, -0.7], [7.2, -0.7]].map(([x, z]) => [sx(x), sz(z)]);
const yOnPath = x => { for (let i = 1; i < PATH.length; i++) { const [a, b] = [PATH[i - 1], PATH[i]]; if (x <= b[0]) return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]); } return PATH[3][1]; };

// timing: [line starts moving, station lights] per station, local frames
const T = [[sec(5.9), sec(6.6)], [sec(7.6), sec(8.0)], [sec(11.0), sec(11.4)], [sec(12.2), sec(13.0)], [sec(14.7), sec(15.2)], [sec(17.3), sec(17.7)]];
const TAIL = [sec(17.9), sec(18.5)];        // after approval the line runs on off the right edge
const PHASES = [sec(16.0), sec(16.4), sec(16.8)];
const SUBS = {1: sec(8.6), 3: sec(13.9), 4: sec(15.6)};
const BEADS = sec(18.4), FAIL = sec(18.9), HEAD = sec(3.4);

const headX = f => {
  let x = PATH[0][0];
  // each run stops just past the station's lit disc (the disc's clip circle also holds a bit of lit tube)
  const stop = i => STX[i][0] + (i === 5 ? 66 : 58);
  T.forEach(([a, b], i) => { const x0 = i ? stop(i - 1) : PATH[0][0]; if (f >= a) x = x0 + (stop(i) - x0) * outCubic(ramp(f, a, b)); });
  if (f >= TAIL[0]) x = stop(5) + (W + 40 - stop(5)) * inOut(ramp(f, TAIL[0], TAIL[1]));
  return x;
};
// a neon tube striking: off/on stutter, then steady
const FLICK = [1, 0.15, 0.9, 0, 0.35, 1, 0.6, 1, 1, 0.85, 1];
const flick = (f, a) => f < a ? 0 : f - a < FLICK.length ? FLICK[Math.floor(f - a)] : 1;
const moving = f => T.some(([a, b]) => f >= a && f < b) || (f >= TAIL[0] && f < TAIL[1]);

const plate = n => staticFile(`motion/neon/${n}.png`);
const Layer = ({n, clip, opacity = 1}) => <Img src={plate(n)} style={{position: "absolute", left: 0, top: 0, width: W, height: H, clipPath: clip, opacity}}/>;

export const Beat109 = () => {
  const f = useFrame30();
  const xh = headX(f), yh = yOnPath(xh);
  const drops = [34, 17, 8, 4, 3, 1];
  const A = STX;
  const k = 107.2;
  return <Print grain={0.17} band={0.05}>
    <AbsoluteFill style={{opacity: outCubic(ramp(f, 0, 14))}}>
      <Layer n="base"/>
      {/* the lit tube up to the head, with a 24 px feathered tip */}
      {xh > 0 ? <Layer n="line" clip={`inset(0px ${Math.max(0, W - xh)}px 0px 0px)`}/> : null}
      {[1, 2, 3, 4].map(j => xh > 0 && xh < W ? <Layer key={j} n="line" opacity={1 - j / 5} clip={`inset(0px ${W - (xh + j * 6)}px 0px ${xh + (j - 1) * 6}px)`}/> : null)}
      {/* stations strike one by one */}
      {A.map(([x, y], i) => { const o = flick(f, T[i][1]); return o > 0 ? <Layer key={i} n="st" opacity={o} clip={`circle(${i === 5 ? 64 : 56}px at ${x}px ${y}px)`}/> : null; })}
      {/* the bead columns drop in, station by station */}
      {A.map(([x, y], i) => {
        const a = BEADS + i * 3, p = outCubic(ramp(f, a, a + 12));
        if (p <= 0) return null;
        const top = y + 34, bot = i === 0 ? y + 540 : y + 330, w = i === 0 ? 52 : 40;
        return <Layer key={"b" + i} n="beads" clip={`inset(${top}px ${W - x - w}px ${H - (top + (bot - top) * p)}px ${x - w}px)`}/>;
      })}
    </AbsoluteFill>
    <Svg>
      <defs><radialGradient id="mo-head"><stop offset="0" stopColor="#fff" stopOpacity="0.95"/><stop offset="0.25" stopColor={P.red} stopOpacity="0.8"/><stop offset="1" stopColor={P.red} stopOpacity="0"/></radialGradient></defs>
      {moving(f) && xh > 0 && xh < W ? <circle cx={xh} cy={yh} r={29} fill="url(#mo-head)" style={{mixBlendMode: "screen"}}/> : null}
      {A.map(([x, y], i) => {
        const o = flick(f, T[i][1]), on = o > 0.5 && f >= T[i][1];
        const dimIn = 0.28 * ramp(f, HEAD + 6 + i * 2, HEAD + 18 + i * 2);
        const top = i < 3, sz = i === 5 ? 40 : top ? 36 : 32;
        const two = !top && ST[i].short.includes(String.fromCharCode(10));
        const ty = y - 62 - (two ? sz : 0);
        const n = i === 0 ? 34 : drops[i], per = i === 0 ? 17 : 9;
        const yb = y + (0.35 + 0.3 + Math.min(n, per) * 0.25) * k + 26;
        const lab = Math.max(dimIn, f >= T[i][1] ? 0.28 + 0.72 * o : 0);
        const sub = ST[i].sub && SUBS[i] !== undefined ? outCubic(ramp(f, SUBS[i], SUBS[i] + 12)) : 0;
        const cnt = ramp(f, BEADS + i * 3 + 8, BEADS + i * 3 + 16);
        return <g key={i}>
          <g opacity={lab}>
            <MText x={x} y={ty - sz - 6} size={15} anchor="middle" color={on ? P.red : P.ink}>{ST[i].n}</MText>
            <GText x={x} y={ty} size={sz} anchor="middle" lh={1.0}>{top ? ST[i].name : ST[i].short}</GText>
          </g>
          {i === 4 ? <g>
            <MText x={x} y={y - 36} size={12} anchor="middle" weight={400} ls={1}>
              <tspan opacity={0.55 * ramp(f, PHASES[0] - 4, PHASES[0] + 4)}>phase </tspan>
              {["I", "II", "III"].map((r, j) => <tspan key={j} fill={P.red} fontWeight={800} opacity={flick(f, PHASES[j])}>{(j ? " · " : "") + r}</tspan>)}
            </MText></g>
            : sub > 0 ? <MText x={x} y={top ? y - 34 : y - 36} size={12} anchor="middle" weight={400} ls={1} opacity={0.55 * sub}>{ST[i].sub}</MText> : null}
          {cnt > 0 ? <MText x={x} y={yb} size={14} anchor="middle" color={i === 0 ? P.red : P.ink} opacity={0.75 * cnt} ls={1}>{i === 0 ? "34 START" : "−" + drops[i]}</MText> : null}
        </g>;
      })}
      <MText x={70} y={96} size={15} opacity={0.65 * ramp(f, HEAD, HEAD + 12)} ls={4}>{"EVERY MEDICINE WALKS THE SAME ROAD".slice(0, Math.round(34 * ramp(f, HEAD, HEAD + 24)))}</MText>
      {(() => { const l = outCubic(ramp(f, FAIL, FAIL + 10)); return <g opacity={l} transform={`translate(0 ${10 * (1 - outExpo(ramp(f, FAIL, FAIL + 14)))})`}>
        <GText x={1850} y={972} size={30} weight={600} anchor="end" color={P.red}>Any step can fail.</GText></g>; })()}
      <Tag/>
    </Svg>
  </Print>;
};
