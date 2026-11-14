// HKBU SCIE1007 coursework video: on-camera motion v2 for all 28 beats, after the full-film review
// (镜头设计_v3/script/出镜新版式_v1.md, last section "Fable 整片审片…采用的部分").
// Grid (person on the left; person on the right = mirrored zone): align x 1000 (mirror 160); title baseline 380, sub 470,
// prop centre 540 (with text: prop 430, text 600); nothing at x > 1800 or y < 220. Type 120 / 64 / 40.
// Prop box 420 x 320 centred (1300, 540); wide props 760 (x 1000-1760). One subject per beat: a second object comes 8 f later
// and the first steps back to 0.4. Red area <= 25 % of the prop box.
// Push-in x1.18 of the whole frame (person + cells), 2.0 s ease-out from 10 f before the first word: 1-06, 4-12, 6-05, 8-04, 8-07,
// and 4-04 (no prop). 7-01 and 8-01: centred person, no graphics.
// Relays: 4-11 monitor -> 4-12 the same monitor, new screen content; 8-05 headline bar -> 8-06 road slides out of the bar.
import React from "react";
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame} from "remotion";
import {ramp, outCubic, outBack, inOut, outExpo, handLine, loopPts, quad, hash} from "../core";
import {InkPath, InkLine} from "../ink";
import {W, H, INK, RED, CYAN, SERIF, wf, enter, exitK, Word, Full, textW, InkSheet, inkPoly, toD, INK_OUT, edgeVol} from "./kit";
import {HKMap} from "./S12";
import {Key, Scissors} from "./S34";
import {LockArt, Road, hex} from "./S58";
import {BEATS} from "./Beats";
import {S12_SEGS} from "./S12";
import {S34_SEGS} from "./S34";
import {S58_SEGS} from "./S58";

const T1 = 120, T2 = 64, T3 = 40;
const PAPER = "#EAEAE1";
const zone = side => side === "right" ? {x0: 160, x1: 920, cx: 620} : {x0: 1000, x1: 1760, cx: 1300};
const back = (f, t2) => 1 - 0.6 * ramp(f, t2, t2 + 8); // first object steps back to 0.4 when the second arrives

// ---- shared props ----
const Monitor = ({cx, cy, k = 1, op = 1}) => <g opacity={op}>
  <InkPath points={[[cx - 200, cy - 135], [cx + 200, cy - 135], [cx + 200, cy + 115], [cx - 200, cy + 115], [cx - 200, cy - 135]]} color={INK} seed={411} size={8} progress={k} pressure="nib"/>
  <InkPath points={[[cx, cy + 115], [cx, cy + 150]]} color={INK} seed={412} size={7} progress={k} pressure="nib"/>
  <InkPath points={[[cx - 65, cy + 155], [cx + 65, cy + 155]]} color={INK} seed={413} size={7} progress={k} pressure="nib"/>
</g>;
const Trophy = ({x, y, k}) => <g>
  <InkPath points={[[x - 45, y - 60], [x + 45, y - 60], [x + 37, y], [x + 17, y + 26], [x - 17, y + 26], [x - 37, y], [x - 45, y - 60]]} color={RED} seed={414} size={6} progress={k} pressure="marker"/>
  <InkPath points={[[x, y + 26], [x, y + 55], [x - 30, y + 70], [x + 30, y + 70]]} color={RED} seed={417} size={5} progress={k} pressure="marker"/>
</g>;
// trial-and-error loop, words land upright clockwise (think top, make right, test bottom, fix left)
const Loop = ({f, cx, cy, r, tL, tT, trailFrom}) => {
  if (f < tL) return null;
  const kl = outCubic(ramp(f, tL, tL + 11));
  const spin = f < tT ? 0 : 720 * outCubic(ramp(f, tT, tT + 24));
  const path = quad(trailFrom, [trailFrom[0] + 120, cy + r + 40], [cx - r * 0.9, cy + r * 0.5], 60);
  const lf = f - tT, head = outExpo(ramp(lf, 0, 12)) * (path.length - 1), len = 26, fade = 1 - ramp(lf, 14, 30);
  const segs = [];
  if (lf >= 0) for (let i = Math.max(1, Math.floor(head - len)); i <= Math.floor(head); i++) {
    const k = 1 - (head - i) / len;
    segs.push(<line key={i} x1={path[i - 1][0]} y1={path[i - 1][1]} x2={path[i][0]} y2={path[i][1]} stroke={CYAN} strokeWidth={2 + 12 * k} strokeLinecap="round" opacity={k}/>);
  }
  const a1 = -1.3 + 0.9 * 2 * Math.PI;
  return <g>
    <g opacity={enter(f, tL)}>
      <g transform={`rotate(${spin} ${cx} ${cy})`}>
        <InkPath points={loopPts(cx, cy, r, r, {a0: -1.3, turns: 0.9, seed: 81, spiral: 0})} color={INK} seed={81} size={6} progress={kl} pressure="nib"/>
        <InkPath points={[[cx + Math.cos(a1) * r - 24, cy + Math.sin(a1) * r - 8], [cx + Math.cos(a1) * r, cy + Math.sin(a1) * r], [cx + Math.cos(a1) * r - 6, cy + Math.sin(a1) * r + 24]]}
          color={INK} seed={82} size={6} progress={ramp(kl, 0.8, 1)} pressure="marker"/>
      </g>
      {["think", "make", "test", "fix"].map((w, i) => {
        const a = (-90 + i * 90 + spin) * Math.PI / 180;
        return <text key={w} x={cx + Math.cos(a) * (r + 52)} y={cy + Math.sin(a) * (r + 52) + 14} fontFamily={SERIF} fontSize={T3} fill={INK} textAnchor="middle">{w}</text>;
      })}
    </g>
    {segs.length > 0 && <g opacity={fade}>
      <filter id="v2-glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
      <g filter="url(#v2-glow)">{segs}</g>{segs}
      {Array.from({length: 8}, (_, i) => { const q = path[Math.max(0, Math.floor(head - hash(i, 3) * len * 1.4))];
        return <circle key={i} cx={q[0] + (hash(i, 4) - 0.5) * 30} cy={q[1] + (hash(i, 5) - 0.5) * 30} r={1.5 + hash(i, 6) * 3} fill={CYAN}/>; })}
    </g>}
  </g>;
};

// ---- S1 ----
const G101 = ({f, out}) => {
  const tM = wf(1.329) - 6, t4 = wf(2.692) - 6, tS = wf(4.196) - 6;
  return <Full opacity={exitK(f, out)}>
    <g opacity={back(f, t4)}>
      <g transform="translate(90 0)"><HKMap f={f} t0={tM}/></g>
      <Word x={1470} y={410} size={T3} f={f} t0={tM + 8}>Hong Kong</Word>
    </g>
    <Word x={1000} y={600} size={T1} f={f} t0={t4} color={RED}>4</Word>
    <Word x={1000 + textW("4", T1) + 24} y={600} size={T2} f={f} t0={t4 + 8}>every day</Word>
    <Word x={1000} y={680} size={T3} f={f} t0={tS} opacity={0.72}>Source: HKCaR 2022</Word>
  </Full>;
};
const G103 = ({f, out}) => {
  const tB = wf(1.971) - 5, tC = wf(2.592) - 5, tT = wf(3.676) - 7, tS = wf(3.896) - 3;
  const kB = ramp(f, tB, tB + 10), x = 1150, y = 300, bw = 130, bh = 170;
  const body = [[x + 8, y + 60], [x + bw - 8, y + 60], [x + bw, y + 78], [x + bw, y + 60 + bh], [x, y + 60 + bh], [x, y + 78], [x + 8, y + 60]];
  return <Full opacity={exitK(f, out)}>
    <g opacity={back(f, tT)}>
      {f >= tB && <g opacity={enter(f, tB)}>
        <InkPath points={[[x + 16, y], [x + bw - 16, y], [x + bw - 16, y + 44], [x + 16, y + 44], [x + 16, y]]} color={INK} seed={201} size={7} progress={kB} pressure="nib"/>
        <InkPath points={body} color={INK} seed={202} size={8} progress={kB} pressure="nib"/>
      </g>}
      {f >= tC && <InkPath points={[[1340, 420], [1385, 468], [1490, 350]]} color={INK} seed={210} size={11} progress={outCubic(ramp(f, tC, tC + 10))} pressure="marker"/>}
    </g>
    {f >= tS && <InkLine from={[1320, 480]} to={[1510, 330]} bow={-5} over={4} seed={211} size={10} color={RED} progress={outCubic(ramp(f, tS, tS + 10))} pressure="marker"/>}
    <Word x={1000} y={600} size={T2} f={f} t0={tT}>not good enough</Word>
  </Full>;
};
const G105 = ({f, out}) => <Full opacity={exitK(f, out)}><Word x={160} y={380} size={T1} f={f} t0={73}>a better one?</Word></Full>;
const G106 = ({f, out}) => <Full opacity={exitK(f, out)}>
  <Word x={1000} y={380} size={T1} f={f} t0={27}>way harder</Word>
  <InkPath points={handLine([1000, 410], [1000 + textW("way harder", T1), 405], {bow: 4, over: 5})} seed={61} size={9} color={RED}
    progress={outCubic(ramp(f, 37, 48))} pressure="marker"/>
</Full>;
const TL = {x0: 1000, x1: 1760, y: 540};
const Timeline = ({f, thin}) => {
  const L = TL.x1 - TL.x0, d = thin ? 1 : outCubic(ramp(f, 0, 11));
  return <g>
    <InkPath points={handLine([TL.x0, TL.y], [TL.x1, TL.y - 6], {bow: -4, over: 3})} seed={100} size={thin ? 3 : 7} progress={d} color={thin ? CYAN : INK} pressure="nib"/>
    {Array.from({length: 17}, (_, i) => {
      const tx = TL.x0 + L * (i + 1) / 17.4, late = i >= 9, h = late ? 22 : 13;
      if (tx > TL.x0 + L * d) return null;
      return <InkLine key={i} from={[tx, TL.y - h]} to={[tx, TL.y + h]} seed={110 + i} size={thin ? 2 : late ? 5 : 3.5} color={thin ? CYAN : late ? RED : INK} pressure="marker"/>;
    })}
  </g>;
};
const G107 = ({f, out, ink}) => {
  const lf = f - 35;
  if (lf < 0) return null;
  // ink comes from BeatV2 (same flood as every other beat); the cyan thin timeline shows where the ink has passed
  const T0 = ink ? ink.T0 : out, inkOn = !!ink && f >= T0, edge = ink ? ink.edge : W + 400, it = f - T0;
  const poly = inkPoly(edge, true, it);
  const wet = inkOn ? toD(poly) : "M0 0 Z";
  const dry = inkOn ? toD(poly.map(([x, y], i, a) => i === 0 || i === a.length - 1 ? [-400, y] : [x, y])) : `M0 0 H${W} V${H} H0 Z`;
  return <>
    <Full>
      <defs><clipPath id="v2-dry"><path d={dry}/></clipPath></defs>
      <g clipPath="url(#v2-dry)">
        <Timeline f={lf}/>
        <Word x={1000} y={380} size={T1} f={lf} t0={12}>10–17 years</Word>
      </g>
    </Full>
    {inkOn && <InkSheet edgeX={edge} fromRight t={it} id="v2-ink" seed={9}/>}
    {inkOn && <Full><defs><clipPath id="v2-wet"><path d={wet}/></clipPath></defs><g clipPath="url(#v2-wet)"><Timeline f={99} thin/></g></Full>}
  </>;
};

// ---- S2 ----
const RQ = ["How can computer-aided methods", "help scientists find and assess", "potential cancer drug candidates?"];
const RQY = [380, 470, 560], WS = [6, 22, 6];
const G202 = ({f, out}) => {
  const t = [wf(2.728) - 5, wf(5.292) - 5, wf(7.795) - 5];
  const circ = (before, word, t0, seed) => {
    if (f < t0) return null;
    const x0 = 1000 + textW(before, T2) + (before.match(/ /g) || []).length * WS[1], w = textW(word, T2);
    return <InkPath points={loopPts(x0 + w / 2, RQY[1] - T2 * 0.3, w / 2 + 6, T2 * 0.52, {seed, turns: 1.1})} seed={seed} size={5} color={RED}
      progress={outCubic(ramp(f, t0, t0 + 10))} pressure="marker"/>;
  };
  return <Full opacity={exitK(f, out)}>
    <Word x={1000} y={290} size={T3} f={f} t0={wf(1.025) - 5} opacity={0.6}>Our research question</Word>
    {RQ.map((s, i) => <g key={i} style={{wordSpacing: WS[i]}}><Word x={1000} y={RQY[i]} size={T2} f={f} t0={t[i]}>{s}</Word></g>)}
    {circ("help scientists ", "find", wf(6.614) - 5, 221)}
    {circ("help scientists find and ", "assess", wf(7.315) - 5, 222)}
  </Full>;
};
const G204 = ({f, out}) => {
  const t1 = wf(1.808) - 5, t2 = t1 + 9, tl = t2 + 10;
  return <Full opacity={exitK(f, out)}>
    {[0, 1].map(i => <Word key={i} x={1000 + i * 380} y={380} size={T1} f={f} t0={[t1, t2][i]}>{i + 1}</Word>)}
    {f >= tl && [0, 1].map(i => <InkLine key={i} from={[1080 + i * 380, 378]} to={[1300 + i * 380, 375]} bow={2} over={3} color={INK} seed={230 + i} size={6}
      progress={outCubic(ramp(f, tl, tl + 10))} pressure="marker"/>)}
  </Full>;
};

// ---- S3 ----
const G301 = ({f, out}) => {
  const tL = wf(3.696) - 6, tK = wf(5.539) - 6;
  return <Full opacity={exitK(f, out)}>
    {f >= tL && <g transform="translate(1180 470) scale(0.62)"><LockArt progress={outCubic(ramp(f, tL, tL + 11))}/></g>}
    {f >= tK && <g transform="translate(1290 526) scale(0.88)"><Key progress={outCubic(ramp(f, tK, tK + 11))}/></g>}
  </Full>;
};
const G306 = ({f, out}) => {
  const tC = wf(2.435) - 6, tS = wf(2.896) - 5, tN = wf(5.26) - 5, tB = wf(8.645) - 5;
  const kc = outCubic(ramp(f, tC, tC + 11)), ks = outBack(ramp(f, tS, tS + 8), 2.2);
  return <Full opacity={exitK(f, out)}>
    <g opacity={back(f, tN)}>
      {f >= tC && <g opacity={enter(f, tC)}>
        <InkPath points={[[1090, 290], [1510, 290], [1510, 540], [1090, 540], [1090, 290]]} color={INK} seed={301} size={7} progress={kc} pressure="nib"/>
        <text x={1120} y={340} fontFamily={SERIF} fontSize={T3} fill={INK} opacity={0.6}>File</text>
        <text x={1120} y={460} fontFamily={SERIF} fontSize={T1} fill={INK}>CDK20</text>
      </g>}
      {f >= tS && <g transform={`translate(1380 505) rotate(-9) scale(${0.5 + 0.3 * ks})`} opacity={Math.min(1, (f - tS) / 3)}>
        <InkPath points={[[-170, -52], [170, -52], [170, 40], [-170, 40], [-170, -52]]} color={RED} seed={305} size={7} pressure="marker"/>
        <text x={0} y={22} fontFamily={SERIF} fontSize={78} fill={RED} textAnchor="middle" letterSpacing={6}>SUSPECT</text>
      </g>}
    </g>
    <g opacity={back(f, tB)}><Word x={1000} y={620} size={T2} f={f} t0={tN}>not the only cause</Word></g>
    <Word x={1000} y={700} size={T2} f={f} t0={tB}>but a lock worth trying</Word>
  </Full>;
};
const LC = {x: 1300, y: 540};
const G309 = ({f, out}) => {
  const tL = wf(1.392) - 6, tD = wf(1.913) - 5, tK = wf(4.317) - 6, tQ = wf(4.878) - 5;
  const dk = outCubic(ramp(f, tD, tD + 12));
  return <Full opacity={exitK(f, out)}>
    <defs>
      {/* darkest 35 % ink, only in a ring round the prop; fades back to nothing well before the person side */}
      <radialGradient id="v2-309" cx={LC.x} cy={LC.y} r={0.6 * H} gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor={INK} stopOpacity={0}/>
        <stop offset={0.12 / 0.6} stopColor={INK} stopOpacity={0}/>
        <stop offset={0.32 / 0.6} stopColor={INK} stopOpacity={0.35}/>
        <stop offset="1" stopColor={INK} stopOpacity={0}/>
      </radialGradient>
      <radialGradient id="v2-309w" cx={LC.x} cy={LC.y} r={0.12 * H} gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#FFE7B0" stopOpacity={0.45}/><stop offset="1" stopColor="#FFE7B0" stopOpacity={0}/>
      </radialGradient>
      <linearGradient id="v2-309m" x1="960" x2="1300" y1="0" y2="0" gradientUnits="userSpaceOnUse">
        <stop offset="0" stopColor="#fff" stopOpacity={0}/><stop offset="1" stopColor="#fff" stopOpacity={1}/>
      </linearGradient>
      <mask id="v2-309side"><rect x={0} y={0} width={W} height={H} fill="url(#v2-309m)"/></mask>
    </defs>
    {f >= tL && <g transform={`translate(${LC.x} ${LC.y - 85}) scale(0.6)`} opacity={back(f, tK)}><LockArt progress={outCubic(ramp(f, tL, tL + 11))}/></g>}
    {dk > 0 && <g opacity={dk} mask="url(#v2-309side)">
      <rect x={0} y={0} width={W} height={H} fill="url(#v2-309)"/>
      <circle cx={LC.x} cy={LC.y} r={0.12 * H} fill="url(#v2-309w)"/>
    </g>}
    {f >= tK && <g transform="translate(1420 760) rotate(-12)"><Key progress={outCubic(ramp(f, tK, tK + 11))} color={INK} seed={44}/></g>}
    <Word x={1690} y={720} size={T1} f={f} t0={tQ}>?</Word>
  </Full>;
};

// ---- S4 ----
const Null = () => null; // 4-04: no prop, push-in only; 7-01 / 8-01: centred, no graphics
const G405 = ({f, out}) => {
  const tS = wf(0.611) - 10, tA = wf(1.953) - 5, tH = wf(3.576) - 5, tP = wf(4.417) - 4;
  const PX = 1060 + textW("Human: caught the ", T2) + 18; // text block at x 1060: B's shoulder in the new framing
  return <Full opacity={exitK(f, out)}>
    <g opacity={back(f, tA)}><Scissors f={f - tS} x={1470} y={420} s={0.62}/></g>
    <Word x={1060} y={600} size={T2} f={f} t0={tA}>AI: made the guess</Word>
    <Word x={1060} y={690} size={T2} f={f} t0={tH}>Human: caught the</Word>
    <Word x={PX} y={690} size={T2} f={f} t0={tH}>problem</Word>
    {f >= tP && <InkPath points={loopPts(PX + textW("problem", T2) / 2, 690 - 19, textW("problem", T2) / 2 + 8, 36, {seed: 453, turns: 1.1})}
      color={RED} seed={453} size={5} progress={outCubic(ramp(f, tP, tP + 10))} pressure="marker"/>}
  </Full>;
};
const G408 = ({f, out}) => <Full opacity={exitK(f, out)}>
  <Loop f={f} cx={1300} cy={540} r={130} tL={wf(4.376) - 5} tT={wf(7.239) - 5} trailFrom={[1000, 640]}/>
</Full>;
const MON = {cy: 430};
const G411 = ({f, out}) => {
  const tM = wf(0.504) - 5, tT = wf(2.211) - 5, tQ = wf(3.195) - 5, cx = 620;
  return <Full opacity={exitK(f, out)}>
    {f >= tM && <Monitor cx={cx} cy={MON.cy} k={outCubic(ramp(f, tM, tM + 11))} op={enter(f, tM)}/>}
    {f >= tT && <Trophy x={cx - 70} y={MON.cy - 20} k={outCubic(ramp(f, tT, tT + 10))}/>}
    <Word x={cx + 30} y={MON.cy + 40} size={T1} f={f} t0={tQ}>?</Word>
  </Full>;
};
// 4-12 opens on the same monitor, already drawn; the screen now says what a docking score is
const G412 = ({f, out}) => {
  const tD = wf(1.834) - 5, tC = wf(3.676) - 5, tP = wf(4.437) - 5, tU = tP + 9, cx = 1300;
  return <Full opacity={exitK(f, out)}>
    <Monitor cx={cx} cy={MON.cy} op={back(f, tP)}/>
    <Word x={cx - 175} y={MON.cy - 80} size={T3} f={f} t0={tD} opacity={0.7}>docking score</Word>
    <Word x={cx - 175} y={MON.cy + 50} size={T1} f={f} t0={tC}>a clue</Word>
    {f >= tU && <InkLine from={[cx - 178, MON.cy + 74]} to={[cx - 170 + textW("a clue", T1), MON.cy + 70]} seed={421} size={8} color={RED}
      progress={outCubic(ramp(f, tU, tU + 10))} pressure="marker"/>}
    <Word x={1150} y={680} size={T2} f={f} t0={tP}>not proof</Word>
  </Full>;
};

// ---- S5 ----
const G502 = ({f, out}) => {
  const tR = wf(0.534) - 6, tG = wf(1.337) - 6, tS = wf(2.841) - 6, tN = wf(5.508) - 6;
  const d = outCubic(ramp(f, tR, tR + 11)), g = ramp(f, tG, tG + 10), st = outBack(ramp(f, tS, tS + 10), 2);
  return <Full opacity={exitK(f, out)}>
    <g opacity={back(f, tN)}>{f >= tR && Array.from({length: 7}, (_, i) => {
      const x = 1030 + i * 117, y = 430, last = i === 6, sc = last ? 1 + 0.4 * st : 1;
      return <g key={i} opacity={last ? 1 : 1 - 0.72 * g} transform={`translate(${x} ${y}) scale(${sc}) translate(${-x} ${-y})`}>
        <InkPath points={hex(x, y, 34)} color={last && f >= tS ? RED : INK} seed={520 + i} size={5} progress={d} pressure="marker"/>
      </g>;
    })}</g>
    <Word x={1000} y={600} size={T1} f={f} t0={tN}>001</Word>
  </Full>;
};
const G505 = ({f, out}) => {
  const tL = wf(0.673) - 6, tK = wf(1.114) - 6, tT = wf(3.018) - 6, tW = wf(3.699) - 6;
  const ang = 40 * outCubic(ramp(f, tT, tT + 10)) + (f > tT + 10 ? 4 * Math.sin(f * 1.7) * Math.exp(-(f - tT - 10) / 12) : 0);
  return <Full opacity={exitK(f, out)}>
    {f >= tL && <g transform="translate(1300 330) scale(0.62)" opacity={back(f, tW)}><LockArt progress={outCubic(ramp(f, tL, tL + 11))}/>
      {f >= tK && <g transform={`translate(0 90) rotate(${ang})`}><Key progress={outCubic(ramp(f, tK, tK + 10))}/></g>}
    </g>}
    <Word x={1090} y={640} size={T2} f={f} t0={tW}>barely turned</Word>
  </Full>;
};
const G506 = ({f, out}) => {
  const tB = wf(0.452) - 6, tM = wf(2.797) - 6, tQ = wf(3.438) - 6, s = 110, x0 = 160, y0 = 485;
  const d = outCubic(ramp(f, tB, tB + 11)), m = inOut(ramp(f, tM, tM + 11)), px = x0 + s * (3.5 - 3 * m);
  return <Full opacity={exitK(f, out)}>
    {f >= tB && <g opacity={Math.min(1, d * 1.5) * back(f, tQ)}>
      {[0, 1, 2, 3, 4].map(i => <InkPath key={i} points={[[x0 + i * s, y0], [x0 + (i + 1) * s, y0], [x0 + (i + 1) * s, y0 + s], [x0 + i * s, y0 + s], [x0 + i * s, y0]]}
        color={INK} seed={560 + i} size={4} progress={d} pressure="marker"/>)}
      <circle cx={px} cy={y0 + s / 2} r={30} fill={INK}/>
    </g>}
    <Word x={760} y={590} size={T1} f={f} t0={tQ}>?</Word>
  </Full>;
};
const G509 = ({f, out}) => {
  const tL = wf(0.473) - 6, tT = wf(1.417) - 6;
  const ang = 90 * outBack(ramp(f, tT, tT + 12), 1.6), lit = ramp(f, tT + 10, tT + 18), up = 34 * outBack(ramp(f, tT + 12, tT + 20), 2);
  return <Full opacity={exitK(f, out)}>
    {f >= tL && <g transform="translate(1300 450) scale(0.62)">
      <LockArt progress={outCubic(ramp(f, tL, tL + 11))} color={lit > 0.5 ? RED : INK} up={up}/>
      <g transform={`translate(0 90) rotate(${ang})`}><Key progress={outCubic(ramp(f, tL + 4, tL + 12))}/></g>
    </g>}
  </Full>;
};

// ---- S6 ----
const NDOT = 220;
const DOTS = Array.from({length: NDOT}, (_, i) => [410 + hash(i, 1) * 420, 270 + hash(i, 2) * 320, 5 + hash(i, 3) * 5]);
const KEEP = Array.from({length: 13}, (_, i) => Math.floor(i * NDOT / 13 + 7));
const G604 = ({f, out}) => {
  const tD = wf(0.503) - 6, tC = wf(4.916) - 6, tN = wf(5.317) - 5;
  const kd = outCubic(ramp(f, tD, tD + 10)), kc = inOut(ramp(f, tC, tC + 12));
  return <Full opacity={exitK(f, out)}>
    <g opacity={back(f, tN)}>{f >= tD && DOTS.map(([x, y, r], i) => {
      const k = KEEP.indexOf(i);
      if (k < 0) return kc >= 1 ? null : <circle key={i} cx={x} cy={y} r={r * kd * (1 - kc)} fill={INK} opacity={1 - kc}/>;
      const a = k * 2.399963, rr = Math.sqrt((k + 0.5) / 13) * 90;
      return <circle key={i} cx={x + (620 + Math.cos(a) * rr - x) * kc} cy={y + (430 + Math.sin(a) * rr * 0.8 - y) * kc} r={(r + 6 * kc) * kd} fill={INK}/>;
    })}</g>
    <Word x={160} y={620} size={T1} f={f} t0={tN} color={RED}>13</Word>
    <Word x={300} y={620} size={T2} f={f} t0={tN + 8}>made</Word>
  </Full>;
};
const G605 = ({f, out}) => {
  const t0 = wf(0.435) - 6, tJ = wf(2.504) - 5, hop = f < tJ ? 0 : Math.sin(Math.PI * Math.min(1, (f - tJ) / 9)) * 24;
  return <Full opacity={exitK(f, out)}><g transform={`translate(0 ${-hop})`}><Word x={1000} y={380} size={T1} f={f} t0={t0} color={RED}>13</Word></g></Full>;
};
const G612 = ({f, out}) => {
  const tT = 10, tW = wf(5.306) - 6, tY = wf(5.968) - 6, tX = wf(6.188) - 3, x0 = 1000, x1 = 1760, y = 540;
  const kt = enter(f, tT), yx = 1500;
  return <Full opacity={exitK(f, out)}>
    <g opacity={back(f, tW)}>
      <Road x0={x0} x1={x1} y={y} f={f} t0={0} size={T3}/>
      {kt > 0 && <g opacity={kt}>
        <InkPath points={[[x0 + 45, y - 92], [x0 + 145, y - 92], [x0 + 145, y - 44], [x0 + 45, y - 44], [x0 + 45, y - 92]]} color={RED} seed={620} size={4} pressure="marker"/>
        <text x={x0 + 95} y={y - 55} fontFamily={SERIF} fontSize={T3} fill={RED} textAnchor="middle">048</text>
      </g>}
    </g>
    <Word x={x0} y={380} size={T2} f={f} t0={tW}>weeks</Word>
    <Word x={yx} y={380} size={T2} f={f} t0={tY} opacity={0.6}>years</Word>
    {f >= tX && <InkLine from={[yx - 6, 362]} to={[yx + textW("years", T2) + 6, 358]} seed={621} size={6} color={RED} progress={outCubic(ramp(f, tX, tX + 9))} pressure="marker"/>}
  </Full>;
};

// ---- S8 ----
const G804 = ({f, out}) => {
  const tR = wf(0.45) - 6, tL = wf(1.411) - 8, tN = wf(2.112) - 6, tE = wf(7.716) - 6, x0 = 1000, x1 = 1760, y = 430;
  return <Full opacity={exitK(f, out)}>
    <g opacity={back(f, tE)}>
      <Road x0={x0} x1={x1} y={y} f={f} t0={tR} litT={[tL, tL + 3, tL + 6]} grey={[3, 4]} greyK={ramp(f, tN, tN + 10)} size={T3}/>
      <Word x={x0 + (x1 - x0) * 0.875} y={y - 50} size={T3} f={f} t0={tN} anchor="middle" color={RED}>not yet</Word>
    </g>
    <Word x={1000} y={600} size={T2} f={f} t0={tE}>Experiments still decide.</Word>
  </Full>;
};
// two-line bar, 580 wide, starting at x 1200 (B holds his real phone up to about x 1080 in the new framing)
const BAR = {y: 540, h: 180, w: 580};
const Bar = ({x0, k = 1, op = 1, dy = 0}) => <g opacity={op * k} transform={`translate(0 ${dy})`}>
  <rect x={x0} y={BAR.y - BAR.h / 2} width={BAR.w} height={BAR.h} fill={INK}/>
  <text x={x0 + 32} y={BAR.y - 14} fontFamily={SERIF} fontSize={T2} fill={PAPER}>AI discovers</text>
  <text x={x0 + 32} y={BAR.y + 62} fontFamily={SERIF} fontSize={T2} fill={PAPER}>a cancer drug</text>
</g>;
const G805 = ({f, out}) => {
  const tH = wf(1.486) - 6;
  return <Full opacity={exitK(f, out)}>{f >= tH && <Bar x0={1200} k={enter(f, tH)}/>}</Full>;
};
// 8-06 opens on the same headline bar (mirrored zone); on "road" the bar lifts and steps back, the road slides out from under it
const G806 = ({f, out}) => {
  const tR = wf(2.365) - 6, k = outCubic(ramp(f, tR, tR + 11));
  const lt = [3.627, 4.97, 6.372, 7.815, 9.278].map(s => wf(s) - 5);
  return <Full opacity={exitK(f, out)}>
    <Bar x0={W - 1200 - BAR.w} op={1 - 0.6 * k} dy={-190 * k}/>
    {f >= tR && <g transform={`translate(0 ${-60 * (1 - k)})`} opacity={k}><Road x0={190} x1={890} y={560} f={f} t0={tR - 11} litT={lt} size={T3}/></g>}
  </Full>;
};
const G807 = ({f, out}) => <Full opacity={exitK(f, out)}>
  <Loop f={f} cx={1300} cy={430} r={110} tL={wf(3.695) - 5} tT={wf(5.057) - 5} trailFrom={[1000, 560]}/>
  <Word x={1000} y={700} size={T3} f={f} t0={wf(6.438) - 6} opacity={0.75}>Thanks for watching</Word>
</Full>;

// ---- configs: graphic, push-in start (frame) ----
const V2G = {
  "1-01": [G101], "1-03": [G103], "1-05": [G105], "1-06": [G106, wf(0.51) - 10], "1-07": [G107], "2-02": [G202], "2-04": [G204],
  "3-01": [G301], "3-06": [G306], "3-09": [G309], "4-04": [Null, wf(0.463) - 10], "4-05": [G405], "4-08": [G408], "4-11": [G411],
  "4-12": [G412, wf(0.512) - 10], "5-02": [G502], "5-05": [G505], "5-06": [G506], "5-09": [G509], "6-04": [G604], "6-05": [G605, wf(0.435) - 10],
  "6-12": [G612], "7-01": [Null], "8-01": [Null], "8-04": [G804, wf(0.45) - 10], "8-05": [G805], "8-06": [G806], "8-07": [G807, wf(0.512) - 10],
};
const CENTRED = ["7-01", "8-01"];
// Ink at the beat ends (11-14 review: no black hold). Animation -> on-cam: 30 f, frame 0 fully inked, the edge leaves at once
// (ease-out) so the person shows within a few frames. On-cam -> animation: 36 f from the motion side, ease-in, the last frame is
// exactly covered and the cut comes there; it starts before the last word ends + 15 f (tails are 13-25 f).
const INK_IN = 30, INK_OUT2 = 36;
const LAST_END = {"1-01": 153, "1-03": 139, "1-05": 97, "1-06": 70, "1-07": 96, "2-02": 306, "2-04": 91, "3-01": 173, "3-06": 324, "3-09": 155, "4-04": 51, "4-05": 143, "4-08": 236, "4-11": 111, "4-12": 205, "5-02": 168, "5-05": 121, "5-06": 111, "5-09": 83, "6-04": 169, "6-05": 90, "6-12": 196, "7-01": 134, "8-01": 73, "8-04": 278, "8-05": 139, "8-06": 297, "8-07": 220};

const BeatV2 = ({seg, frames, inkIn, inkOut, G, push}) => {
  const f = useCurrentFrame(), left = seg.side !== "right";
  const z = push == null ? 1 : 1 + 0.18 * outCubic(ramp(f, push, push + 60));
  const ox = CENTRED.includes(seg.id) ? 0.5 * W : left ? 0.28 * W : 0.72 * W, oy = 0.45 * H;
  const pIn = outCubic(ramp(f, 0, INK_IN)), inEdge = left ? -110 + pIn * 2300 : W + 110 - pIn * 2300;
  const dur = Math.max(INK_OUT2, frames - (LAST_END[seg.id] + 15)), T0 = frames - dur;
  const pOut = ramp(f, T0, frames - 1) ** 2, outEdge = left ? W + 110 - pOut * (W + 220) : -110 + pOut * (W + 220);
  return <AbsoluteFill style={{background: PAPER, overflow: "hidden"}}>
    <AbsoluteFill style={{transform: `scale(${z})`, transformOrigin: `${ox}px ${oy}px`}}>
      <OffthreadVideo src={staticFile(seg.src)} volume={edgeVol(frames, 2)}/>
    </AbsoluteFill>
    <G f={f} out={seg.id === "1-07" ? frames : seg.out} ink={inkOut && f >= T0 ? {T0, edge: outEdge} : null}/>
    {inkIn && f < INK_IN && <InkSheet edgeX={inEdge} fromRight={left} t={f} id="b2-in" seed={4}/>}
    {inkOut && seg.id !== "1-07" && f >= T0 && <InkSheet edgeX={outEdge} fromRight={left} t={f - T0} id="b2-out" seed={9}/>}
  </AbsoluteFill>;
};

export const V2_SEGS = [...S12_SEGS, ...S34_SEGS, ...S58_SEGS].map(seg => ({seg, ...BEATS[seg.id], G: V2G[seg.id][0], push: V2G[seg.id][1]}));
export const BEAT2_COMPS = V2_SEGS.map(s => ({id: "V3-OnCam2-Beat2-" + s.seg.id, frames: s.frames, component: () => <BeatV2 {...s}/>}));
