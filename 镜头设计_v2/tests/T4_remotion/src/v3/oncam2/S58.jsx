// HKBU SCIE1007 coursework video: on-camera segments of S5-S8 in the approved layout (same kit as S12.jsx / S34.jsx).
// Copy: 镜头设计_v3/script/oncam_graphics_v33.py, then the script's Visual lines; no numbers or claims beyond the script.
// Word times: 素材流程_out/<who>/5_place/place.json. Times are clip frames at 30 fps; graphics start 3-8 f before their word.
import React from "react";
import {ramp, outCubic, outBack, inOut, handLine, loopPts, hash} from "../core";
import {InkPath, InkLine} from "../ink";
import {W, H, INK, RED, SERIF, wf, enter, exitK, Word, Full, textW, Segment, Reel, reelLen, segLen} from "./kit";
import {Key, TrialLoop} from "./S34";
import {HKMap} from "./S12";

const GREY = 0.28; // opacity for greyed-out items

// lock with a shackle that can pop up and a colour (from PropLock); origin = lock centre-top, art spans x -150..150
export const LockArt = ({progress = 1, color = INK, up = 0}) => <g>
  <InkPath points={[[-150, -40], [150, -40], [150, 210], [-150, 210], [-150, -40]]} seed={3} size={9} color={color} progress={progress} pressure="brush"/>
  <InkPath points={loopPts(0, -40 - up, 100, 130, {a0: Math.PI, turns: 0.5, seed: 5, spiral: 0, wob: 0.02})} seed={4} size={9} color={color} progress={progress}/>
  <InkPath points={loopPts(0, 80, 16, 16, {seed: 6})} seed={6} size={6} color={color} progress={ramp(progress, 0.5, 1)}/>
</g>;

// five-station road (computer / protein / cells / animals / patients)
const STATIONS = ["computer", "protein", "cells", "animals", "patients"];
export const Road = ({x0, x1, y, f, t0, grey = [], greyK = 1, litT = [], size = 42, r = 26}) => {
  const d = outCubic(ramp(f, t0, t0 + 11));
  if (d <= 0) return null;
  const xs = STATIONS.map((_, i) => x0 + (x1 - x0) * i / 4);
  return <g>
    <InkPath points={handLine([x0, y], [x1, y], {bow: -3})} color={INK} seed={600} size={5} progress={d} pressure="nib"/>
    {xs.map((x, i) => {
      const g = grey.includes(i) ? 1 - (1 - GREY) * greyK : 1;
      const k = litT[i] != null ? outCubic(ramp(f, litT[i], litT[i] + 8)) : 0;
      return <g key={i} opacity={g * Math.min(1, d * 1.5)}>
        <circle cx={x} cy={y} r={r} fill="#EAEAE1"/>
        <InkPath points={loopPts(x, y, r, r, {seed: 610 + i, turns: 1.05})} color={INK} seed={610 + i} size={5} pressure="marker"/>
        {k > 0 && <circle cx={x} cy={y} r={(r - 5) * k} fill={RED}/>}
        <text x={x} y={y + r + size + 6} fontFamily={SERIF} fontSize={size} fill={INK} textAnchor="middle">{STATIONS[i]}</text>
      </g>;
    })}
  </g>;
};

// ---- 5-02 C (left): seven ink molecule rings, six go grey on "barely held on", the seventh stands out, "001" written on "001." ----
export const hex = (cx, cy, r) => Array.from({length: 7}, (_, i) => { const a = Math.PI / 6 + i * Math.PI / 3; return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; });
const G502 = ({f, out}) => {
  const tR = wf(0.534) - 6, tG = wf(1.337) - 6, tS = wf(2.841) - 6, tN = wf(5.508) - 6;
  const d = outCubic(ramp(f, tR, tR + 11)), g = ramp(f, tG, tG + 10), st = outBack(ramp(f, tS, tS + 10), 2);
  return <Full opacity={exitK(f, out)}>
    {f >= tR && Array.from({length: 7}, (_, i) => {
      const x = 1080 + i * 108, y = 430, last = i === 6;
      const sc = last ? 1 + 0.45 * st : 1;
      return <g key={i} opacity={last ? 1 : 1 - (1 - GREY) * g} transform={`translate(${x} ${y}) scale(${sc}) translate(${-x} ${-y})`}>
        <InkPath points={hex(x, y, 34)} color={last && f >= tS ? RED : INK} seed={520 + i} size={5} progress={d} pressure="marker"/>
      </g>;
    })}
    <Word x={1400} y={720} size={220} f={f} t0={tN} anchor="middle">001</Word>
  </Full>;
};

// ---- 5-05 C (left): lock drawn, key goes in on "went into", turns about 40 degrees and sticks on "barely" ----
const G505 = ({f, out}) => {
  const tL = wf(0.673) - 6, tK = wf(1.114) - 6, tT = wf(3.018) - 6, tW = wf(3.699) - 6;
  const ang = 40 * outCubic(ramp(f, tT, tT + 10)) + (f > tT + 10 ? 4 * Math.sin(f * 1.7) * Math.exp(-(f - tT - 10) / 12) : 0);
  return <Full opacity={exitK(f, out)}>
    {f >= tL && <g transform="translate(1440 360) scale(0.8)"><LockArt progress={outCubic(ramp(f, tL, tL + 11))}/>
      {f >= tK && <g transform={`translate(0 90) rotate(${ang})`}><Key progress={outCubic(ramp(f, tK, tK + 10))}/></g>}
    </g>}
    <Word x={1290} y={720} size={64} f={f} t0={tW}>barely turned</Word>
  </Full>;
};

// ---- 5-06 B (right, quiet question): a row of squares, the piece slides back to square 1 on "Back", "?" on "one?" ----
const SQ = {x: 200, y: 470, s: 110};
const G506 = ({f, out}) => {
  const tB = wf(0.452) - 6, tM = wf(2.797) - 6, tQ = wf(3.438) - 6;
  const d = outCubic(ramp(f, tB, tB + 11)), m = inOut(ramp(f, tM, tM + 11));
  const px = SQ.x + SQ.s * (3.5 - 3 * m), py = SQ.y + SQ.s / 2;
  return <Full opacity={exitK(f, out)}>
    {f >= tB && <g opacity={Math.min(1, d * 1.5)}>
      {[0, 1, 2, 3, 4].map(i => <InkPath key={i} points={[[SQ.x + i * SQ.s, SQ.y], [SQ.x + (i + 1) * SQ.s, SQ.y], [SQ.x + (i + 1) * SQ.s, SQ.y + SQ.s], [SQ.x + i * SQ.s, SQ.y + SQ.s], [SQ.x + i * SQ.s, SQ.y]]}
        color={INK} seed={560 + i} size={4} progress={d} pressure="marker"/>)}
      <text x={SQ.x + SQ.s / 2} y={SQ.y + SQ.s + 52} fontFamily={SERIF} fontSize={40} fill={INK} textAnchor="middle" opacity={0.6}>1</text>
      <circle cx={px} cy={py} r={30} fill={INK}/>
    </g>}
    <Word x={810} y={570} size={170} f={f} t0={tQ}>?</Word>
  </Full>;
};

// ---- 5-09 C (left): the key turns all the way on "key turned", the shackle pops open and the lock lights vermilion ----
const G509 = ({f, out}) => {
  const tL = wf(0.473) - 6, tT = wf(1.417) - 6;
  const ang = 90 * outBack(ramp(f, tT, tT + 12), 1.6), lit = ramp(f, tT + 10, tT + 18), up = 34 * outBack(ramp(f, tT + 12, tT + 20), 2);
  return <Full opacity={exitK(f, out)}>
    {f >= tL && <g transform="translate(1440 360) scale(0.8)">
      {lit > 0 && <circle cx={0} cy={80} r={250} fill={RED} opacity={0.14 * lit}/>}
      <LockArt progress={outCubic(ramp(f, tL, tL + 11))} color={lit > 0.5 ? RED : INK} up={up}/>
      <g transform={`translate(0 90) rotate(${ang})`}><Key progress={outCubic(ramp(f, tL + 4, tL + 12))}/></g>
    </g>}
  </Full>;
};

// ---- 6-04 D (right): a field of ink dots on "Millions", shrinking to 13 on "Thirteen", vermilion 13 on "made" ----
const NDOT = 260;
const DOTS = Array.from({length: NDOT}, (_, i) => [160 + hash(i, 1) * 480, 300 + hash(i, 2) * 420, 3 + hash(i, 3) * 4]);
const KEEP = Array.from({length: 13}, (_, i) => Math.floor(i * NDOT / 13 + 7));
const G604 = ({f, out}) => {
  const tD = wf(0.503) - 6, tM = wf(0.503) + 8, tC = wf(4.916) - 6, tN = wf(5.317) - 5;
  const kd = outCubic(ramp(f, tD, tD + 10)), kc = inOut(ramp(f, tC, tC + 12));
  return <Full opacity={exitK(f, out)}>
    {f >= tD && DOTS.map(([x, y, r], i) => {
      const k = KEEP.indexOf(i);
      if (k < 0) return kc >= 1 ? null : <circle key={i} cx={x} cy={y} r={r * kd * (1 - kc)} fill={INK} opacity={1 - kc}/>;
      const a = k * 2.399963, rr = Math.sqrt((k + 0.5) / 13) * 70;
      const tx = 270 + Math.cos(a) * rr, ty = 520 + Math.sin(a) * rr * 0.8;
      return <circle key={i} cx={x + (tx - x) * kc} cy={y + (ty - y) * kc} r={(r + 5 * kc) * kd} fill={INK}/>;
    })}
    <g opacity={1 - ramp(f, tC, tC + 8)}><Word x={160} y={800} size={48} f={f} t0={tM} opacity={0.7}>millions screened</Word></g>
    <Word x={400} y={590} size={220} f={f} t0={tN} color={RED}>13</Word>
  </Full>;
};

// ---- 6-05 B (left): vermilion 13 on "Thirteen", a small hop on "wild" ----
const G605 = ({f, out}) => {
  const t0 = wf(0.435) - 6, tJ = wf(2.504) - 5;
  const hop = f < tJ ? 0 : Math.sin(Math.PI * Math.min(1, (f - tJ) / 9)) * 30;
  return <Full opacity={exitK(f, out)}>
    <g transform={`translate(0 ${-hop})`}><Word x={1380} y={650} size={280} f={f} t0={t0} color={RED} anchor="middle">13</Word></g>
  </Full>;
};

// ---- 6-12 B (left): five-station road, a red "048" tag near the start; "weeks" by the start, "years" struck far off ----
const R612 = {x0: 1010, x1: 1790, y: 560};
const G612 = ({f, out}) => {
  const tR = 0, tT = 10, tW = wf(5.306) - 6, tY = wf(5.968) - 6, tX = wf(6.188) - 3;
  const kt = enter(f, tT);
  const yx = R612.x0 + (R612.x1 - R612.x0) * 0.75;
  return <Full opacity={exitK(f, out)}>
    <Road x0={R612.x0} x1={R612.x1} y={R612.y} f={f} t0={tR}/>
    {kt > 0 && <g opacity={kt} transform={`translate(0 ${(1 - kt) * 20})`}>
      <InkPath points={[[R612.x0 + 50, R612.y - 90], [R612.x0 + 170, R612.y - 90], [R612.x0 + 170, R612.y - 38], [R612.x0 + 50, R612.y - 38], [R612.x0 + 50, R612.y - 90]]} color={RED} seed={620} size={4} pressure="marker"/>
      <text x={R612.x0 + 110} y={R612.y - 50} fontFamily={SERIF} fontSize={46} fill={RED} textAnchor="middle">048</text>
    </g>}
    <Word x={R612.x0 + 105} y={430} size={64} f={f} t0={tW} anchor="middle">weeks</Word>
    <Word x={yx} y={430} size={64} f={f} t0={tY} anchor="middle" opacity={0.6}>years</Word>
    {f >= tX && <InkLine from={[yx - textW("years", 64) / 2 - 6, 412]} to={[yx + textW("years", 64) / 2 + 6, 408]} seed={621} size={7} color={RED}
      progress={outCubic(ramp(f, tX, tX + 9))} pressure="marker"/>}
  </Full>;
};

// ---- 7-01 A (left): numerals 1 2 3 on "three things", then three blank lines (like 2-04) ----
const N3 = [1180, 1420, 1660];
const G701 = ({f, out}) => {
  const t1 = wf(3.515) - 6, tl = t1 + 27;
  return <Full opacity={exitK(f, out)}>
    {N3.map((x, i) => <Word key={i} x={x} y={640} size={260} f={f} t0={t1 + i * 9} anchor="middle">{i + 1}</Word>)}
    {f >= tl && N3.map((x, i) => <InkLine key={i} from={[x - 85, 700]} to={[x + 85, 697]} bow={2} over={3} color={INK} seed={710 + i} size={7}
      progress={outCubic(ramp(f, tl, tl + 9))} pressure="marker"/>)}
  </Full>;
};

// ---- 8-01 C (left): "back to where we started": the Hong Kong outline and the red 4 from 1-01 come back faintly ----
const G801 = ({f, out}) => {
  const tM = wf(1.125) - 6, t4 = wf(1.867) - 6;
  return <Full opacity={exitK(f, out)}>
    <g opacity={0.45}><HKMap f={f} t0={tM}/></g>
    <Word x={1060} y={660} size={240} f={f} t0={t4} color={RED} opacity={0.45}>4</Word>
  </Full>;
};

// ---- 8-04 C (left): road lit up to "cells" on "cells"; animals / patients grey with "not yet" on "not yet";
// "Experiments still decide." on "Experiments" ----
const R804 = {x0: 1000, x1: 1780, y: 520};
const G804 = ({f, out}) => {
  const tR = wf(0.45) - 6, tL = wf(1.411) - 8, tN = wf(2.112) - 6, tE = wf(7.716) - 6;
  const g = ramp(f, tN, tN + 10);
  const xa = R804.x0 + (R804.x1 - R804.x0) * 0.875;
  return <Full opacity={exitK(f, out)}>
    <Road x0={R804.x0} x1={R804.x1} y={R804.y} f={f} t0={tR} litT={[tL, tL + 3, tL + 6]} grey={[3, 4]} greyK={g}/>
    <Word x={xa} y={R804.y - 50} size={46} f={f} t0={tN} anchor="middle" color={RED}>not yet</Word>
    <Word x={R804.x0 - 20} y={740} size={66} f={f} t0={tE}>Experiments still decide.</Word>
  </Full>;
};

// ---- 8-05 B (left): an ink phone slides in on "headline"; the headline bar reads "AI discovers a cancer drug" (no real outlet) ----
const G805 = ({f, out}) => {
  const tP = wf(1.486) - 6, tH = wf(2.831) - 6;
  const kp = outCubic(ramp(f, tP, tP + 11)), kh = enter(f, tH);
  if (f < tP) return null;
  const x = 1500 + (1 - kp) * 160, y = 540;
  const rr = (x0, y0, x1, y1) => [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]];
  return <Full opacity={exitK(f, out)}>
    <g transform={`translate(${x} ${y}) rotate(-5) scale(0.75)`} opacity={kp}>
      <InkPath points={rr(-165, -320, 165, 320)} color={INK} seed={80} size={9} progress={kp}/>
      <InkLine from={[-40, -292]} to={[40, -292]} color={INK} seed={81} size={7}/>
      {[0, 1, 2, 3, 4].map(i => <InkLine key={i} from={[-125, 40 + i * 40]} to={[-125 + [240, 210, 250, 170, 220][i], 40 + i * 40]}
        seed={90 + i} size={5} color={INK} opacity={0.3} pressure="marker"/>)}
      {kh > 0 && <g opacity={kh}>
        <rect x={-135} y={-240} width={270} height={220} fill={INK}/>
        <text x={-115} y={-170} fontFamily={SERIF} fontSize={52} fill="#EAEAE1">AI discovers</text>
        <text x={-115} y={-110} fontFamily={SERIF} fontSize={52} fill="#EAEAE1">a cancer</text>
        <text x={-115} y={-50} fontFamily={SERIF} fontSize={52} fill="#EAEAE1">drug</text>
      </g>}
    </g>
  </Full>;
};

// ---- 8-06 D (right): road on "road", each station lights as he names it ----
const R806 = {x0: 170, x1: 810, y: 560};
const G806 = ({f, out}) => {
  const tR = wf(2.365) - 6;
  const lt = [3.627, 4.97, 6.372, 7.815, 9.278].map(s => wf(s) - 5);
  return <Full opacity={exitK(f, out)}>
    <Road x0={R806.x0} x1={R806.x1} y={R806.y} f={f} t0={tR} litT={lt} size={38}/>
  </Full>;
};

// ---- 8-07 A (left): the 4-08 trial-and-error loop returns, cyan trail on "light speed"; small "Thanks for watching" ----
const G807 = ({f, out}) => <>
  <TrialLoop f={f} out={out} tL={wf(3.695) - 5} tT={wf(5.057) - 5}/>
  <Full opacity={exitK(f, out)}><Word x={1520} y={800} size={44} f={f} t0={wf(6.438) - 6} anchor="middle" opacity={0.75}>Thanks for watching</Word></Full>
</>;

export const S58_SEGS = [
  {id: "5-02", who: "C", side: "left", src: "oncam2/s58/C_cam_5-02.mp4", in: 0, out: 178, G: G502, trig: "Six / barely / one / 001"},
  {id: "5-05", who: "C", side: "left", src: "oncam2/s58/C_cam_5-05.mp4", in: 0, out: 131, G: G505, trig: "key / went / barely / turned"},
  {id: "5-06", who: "B", side: "right", src: "oncam2/s58/B_cam_5-06.mp4", in: 0, out: 114, G: G506, trig: "So / Back / one"},
  {id: "5-09", who: "C", side: "left", src: "oncam2/s58/C_cam_5-09.mp4", in: 0, out: 93, G: G509, trig: "This / key"},
  {id: "6-04", who: "D", side: "right", src: "oncam2/s58/D_cam_6-04.mp4", in: 0, out: 179, G: G604, trig: "Millions / Thirteen / made"},
  {id: "6-05", who: "B", side: "left", src: "oncam2/s58/B_cam_6-05.mp4", in: 0, out: 100, G: G605, trig: "Thirteen / wild"},
  {id: "6-12", who: "B", side: "left", src: "oncam2/s58/B_cam_6-12.mp4", in: 0, out: 206, G: G612, trig: "048 / weeks / not / years"},
  {id: "7-01", who: "A", side: "left", src: "oncam2/s58/A_cam_7-01.mp4", in: 0, out: 144, G: G701, trig: "three"},
  {id: "8-01", who: "C", side: "left", src: "oncam2/s58/C_cam_8-01.mp4", in: 0, out: 83, G: G801, trig: "back / we"},
  {id: "8-04", who: "C", side: "left", src: "oncam2/s58/C_cam_8-04.mp4", in: 0, out: 288, G: G804, trig: "This / cells / not / Experiments"},
  {id: "8-05", who: "B", side: "left", src: "oncam2/s58/B_cam_8-05.mp4", in: 0, out: 149, G: G805, trig: "headline / AI"},
  {id: "8-06", who: "D", side: "right", src: "oncam2/s58/D_cam_8-06.mp4", in: 0, out: 300, G: G806, trig: "road / five station names"},
  {id: "8-07", who: "A", side: "left", src: "oncam2/s58/A_cam_8-07.mp4", in: 0, out: 230, G: G807, trig: "trial / light / Thanks"},
];
export const S58_GAP = 15;
export const S58_FRAMES = reelLen(S58_SEGS, S58_GAP);
export const V3OnCam2S58 = () => <Reel segs={S58_SEGS} gap={S58_GAP}/>;
export const S58_SINGLE = S58_SEGS.map(s => ({id: "V3-OnCam2-S58-" + s.id, frames: segLen(s), component: () => <Segment seg={s}/>}));
