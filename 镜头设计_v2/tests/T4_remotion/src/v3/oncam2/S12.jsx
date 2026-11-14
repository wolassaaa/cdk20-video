// HKBU SCIE1007 coursework video: on-camera segments of S1-S2 in the approved layout (sample v2), one config per segment.
// Copy: 镜头设计_v3/script/oncam_graphics_v33.py. Word times: 素材流程_out/<who>/5_place/place.json .
// Times below are clip frames at 30 fps; each graphic starts 3-8 f before its word.
import React from "react";
import {AbsoluteFill} from "remotion";
import {ramp, outCubic, inOut, handLine, loopPts} from "../core";
import {InkPath, InkLine} from "../ink";
import {W, H, INK, RED, CYAN, SERIF, wf, enter, exitK, Word, Full, textW, Segment, Reel, reelLen, segLen, InkSheet, inkPoly, toD, INK_OUT} from "./kit";

// ---- 1-01 A (left): "Every day in Hong Kong, about four people die of liver cancer." ----
// pulse line before "Every"; HK outline then "Hong Kong" on "Hong Kong"; red 4 before "four", then 4 ink figures one by one; "every day" before "die".
const PULSE = {x: 1060, y: 735, w: 640};
const Pulse = ({f, t0, beat0}) => {
  const d = outCubic(ramp(f, t0, t0 + 11));
  if (d <= 0) return null;
  const amp = ramp(f, beat0, beat0 + 6), head = (((f - beat0) % 30 + 30) % 30) / 30 * (PULSE.w + 300) - 150;
  const k = u => -60 * Math.exp(-((u / 9) ** 2)) + 18 * Math.exp(-(((u + 28) / 10) ** 2)) + 26 * Math.exp(-(((u - 26) / 12) ** 2));
  const pts = [];
  for (let px = 0; px <= PULSE.w; px += 5) pts.push([PULSE.x + px, PULSE.y + amp * k(px - head)]);
  return <InkPath points={pts} seed={140} size={6} color={RED} progress={d} pressure="marker" spacing={5}/>;
};
// Hong Kong outer coast simplified by hand to 38 lon/lat points (mainland + Kowloon, HK Island, Lantau); no small islands.
const HK_MAIN = [[113.90, 22.50], [113.97, 22.51], [114.04, 22.53], [114.10, 22.54], [114.16, 22.56], [114.22, 22.56], [114.27, 22.55], [114.34, 22.52],
  [114.36, 22.47], [114.30, 22.44], [114.37, 22.40], [114.33, 22.34], [114.28, 22.31], [114.29, 22.27], [114.24, 22.29], [114.20, 22.31],
  [114.17, 22.30], [114.12, 22.34], [114.04, 22.36], [113.96, 22.37], [113.92, 22.40], [113.90, 22.45], [113.90, 22.50]];
const HK_ISL = [[114.12, 22.28], [114.18, 22.29], [114.23, 22.28], [114.25, 22.24], [114.20, 22.21], [114.15, 22.22], [114.12, 22.25], [114.12, 22.28]];
const HK_LAN = [[113.85, 22.28], [113.95, 22.30], [114.05, 22.31], [114.06, 22.27], [113.98, 22.22], [113.88, 22.21], [113.84, 22.24], [113.85, 22.28]];
const MAP = {x: 1060, y: 250, k: 560};
const geo = pts => pts.map(([lo, la]) => [MAP.x + (lo - 113.83) * MAP.k * 0.925, MAP.y + (22.57 - la) * MAP.k]);
export const HKMap = ({f, t0}) => {
  const d = outCubic(ramp(f, t0, t0 + 11));
  if (d <= 0) return null;
  return <g>
    <InkPath points={geo(HK_MAIN)} color={INK} seed={150} size={5} progress={d} pressure="nib"/>
    <InkPath points={geo(HK_ISL)} color={INK} seed={151} size={5} progress={d} pressure="nib"/>
    <InkPath points={geo(HK_LAN)} color={INK} seed={152} size={5} progress={d} pressure="nib"/>
  </g>;
};
// simple ink figure, feet at (x, y), about 96 px tall
const Person = ({x, y, f, t0, seed}) => {
  const d = outCubic(ramp(f, t0, t0 + 8));
  if (d <= 0) return null;
  const P = (pts, i, sz = 6) => <InkPath points={pts} color={INK} seed={seed + i} size={sz} progress={d} pressure="marker"/>;
  return <g>
    {P(loopPts(x, y - 82, 13, 13, {seed, turns: 1.05}), 0, 5)}
    {P([[x, y - 66], [x, y - 32]], 1)}
    {P([[x - 22, y - 44], [x, y - 58], [x + 22, y - 44]], 2)}
    {P([[x - 16, y], [x, y - 32], [x + 16, y]], 3)}
  </g>;
};
const G101 = ({f, out}) => {
  const t4 = wf(2.692) - 7;
  return <Full opacity={exitK(f, out)}>
    <Pulse f={f} t0={8} beat0={124}/>
    <HKMap f={f} t0={wf(1.329) - 6}/>
    <Word x={1410} y={420} size={76} f={f} t0={wf(1.329) + 6}>Hong Kong</Word>
    <Word x={1060} y={660} size={240} f={f} t0={t4} color={RED}>4</Word>
    {[0, 1, 2, 3].map(i => <Person key={i} x={1250 + i * 72} y={650} f={f} t0={t4 + 10 + i * 5} seed={160 + i * 5}/>)}
    <Word x={1555} y={650} size={76} f={f} t0={wf(3.555) - 5}>every day</Word>
    <Word x={1062} y={815} size={30} f={f} t0={wf(4.196)} opacity={0.72}>Source: HKCaR 2022</Word>
  </Full>;
};

// ---- 1-03 A (left): "Here's the thing. We already have medicines. Just not good enough ones." ----
const BOT = {x: 1290, y: 360}; // top-left of the bottle cap; A's hand reaches x 1130 at 'medicines'
const Bottle = ({f, t0}) => {
  const d = ramp(f, t0, t0 + 10);
  if (d <= 0) return null;
  const {x, y} = BOT, bw = 150, bh = 200;
  const body = [[x + 10, y + 70], [x + bw - 10, y + 70], [x + bw, y + 90], [x + bw, y + 70 + bh], [x, y + 70 + bh], [x, y + 90], [x + 10, y + 70]];
  return <g opacity={enter(f, t0)}>
    <InkPath points={[[x + 18, y], [x + bw - 18, y], [x + bw - 18, y + 52], [x + 18, y + 52], [x + 18, y]]} color={INK} seed={201} size={7} progress={d} pressure="nib"/>
    <InkPath points={body} color={INK} seed={202} size={8} progress={d} pressure="nib"/>
    <InkPath points={[[x + 22, y + 140], [x + bw - 22, y + 140], [x + bw - 22, y + 210], [x + 22, y + 210], [x + 22, y + 140]]} color={INK} seed={203} size={4} progress={ramp(f, t0 + 4, t0 + 10)} pressure="marker"/>
  </g>;
};
const CHECK = [[1540, 470], [1590, 525], [1720, 385]];
const G103 = ({f, out}) => {
  const tB = wf(1.971) - 5, tC = wf(2.592) - 5, tT = wf(3.676) - 7, tS = wf(3.896) - 3; // place.json words (14:12 re-run)
  return <Full opacity={exitK(f, out)}>
    <Bottle f={f} t0={tB}/>
    {f >= tC && <InkPath points={CHECK} color={INK} seed={210} size={12} progress={outCubic(ramp(f, tC, tC + 10))} pressure="marker"/>}
    <Word x={1290} y={740} size={88} f={f} t0={tT}>not good enough</Word>
    {f >= tS && <InkLine from={[1510, 560]} to={[1760, 330]} bow={-6} over={4} seed={211} size={11} color={RED}
      progress={outCubic(ramp(f, tS, tS + 10))} pressure="marker"/>}
  </Full>;
};

// ---- 1-05 D (right), 1-06 B, 1-07 C: same graphics as the approved sample v2 ----
const G105 = ({f, out}) => <Full opacity={exitK(f, out)}>
  <Word x={170} y={540} size={132} f={f} t0={73}>a better</Word>
  <Word x={170} y={680} size={132} f={f} t0={83}>one?</Word>
</Full>;
const G106 = ({f, out}) => <Full opacity={exitK(f, out)}>
  <Word x={1110} y={560} size={150} f={f} t0={27}>way harder</Word>
  <InkPath points={handLine([1105, 600], [1700, 590], {bow: 5, over: 6})} seed={61} size={11} color={RED}
    progress={outCubic(ramp(f, 37, 48))} pressure="marker"/>
</Full>;
const TL = {x0: 1060, x1: 1740, y: 600};
const Timeline = ({f, thin}) => {
  const L = TL.x1 - TL.x0, d = outCubic(ramp(f, 0, 11));
  if (thin) return <g>
    <InkPath points={handLine([TL.x0, TL.y], [TL.x1, TL.y - 6], {bow: -4, over: 3})} seed={100} size={3} color={CYAN} pressure="nib"/>
    {Array.from({length: 17}, (_, i) => { const tx = TL.x0 + L * (i + 1) / 17.4, h = i >= 9 ? 22 : 13;
      return <InkLine key={i} from={[tx, TL.y - h]} to={[tx, TL.y + h]} seed={110 + i} size={2} color={CYAN} pressure="marker"/>; })}
  </g>;
  return <g>
    <InkPath points={handLine([TL.x0, TL.y], [TL.x1, TL.y - 6], {bow: -4, over: 3})} seed={100} size={7} progress={d} color={INK} pressure="nib"/>
    {Array.from({length: 17}, (_, i) => {
      const tx = TL.x0 + L * (i + 1) / 17.4, late = i >= 9;
      if (tx > TL.x0 + L * d) return null;
      const h = late ? 22 : 13;
      return <InkLine key={i} from={[tx, TL.y - h]} to={[tx, TL.y + h]} seed={110 + i} size={late ? 5 : 3.5} color={late ? RED : INK} pressure="marker"/>;
    })}
    <InkPath points={[[TL.x0 + L * 10 / 17.4, TL.y - 44], [TL.x0 + L * 10 / 17.4, TL.y - 58], [TL.x0 + L * 17 / 17.4, TL.y - 60], [TL.x0 + L * 17 / 17.4, TL.y - 46]]}
      seed={130} size={5} color={RED} progress={outCubic(ramp(f, 24, 34))} pressure="marker"/>
  </g>;
};
// 1-07 ends like sample v2: ink floods in from the motion side over the last 21 f; under the ink the timeline turns thin cyan.
const G107 = ({f, out}) => {
  const lf = f - 35;
  if (lf < 0) return null;
  const k = enter(lf, 12), T0 = out - INK_OUT;
  const inkOn = f >= T0, edge = 2080 - inOut(ramp(f, T0, out - 1)) * 2350, it = f - T0;
  const poly = inkPoly(edge, true, it);
  const wet = inkOn ? toD(poly) : "M0 0 Z";
  const dry = inkOn ? toD(poly.map(([x, y], i, a) => i === 0 || i === a.length - 1 ? [-400, y] : [x, y])) : `M0 0 H${W} V${H} H0 Z`;
  return <>
    <Full>
      <defs><clipPath id="s12-dry"><path d={dry}/></clipPath></defs>
      <g clipPath="url(#s12-dry)">
        <Timeline f={lf}/>
        <text x={(TL.x0 + TL.x1) / 2 + 40} y={TL.y - 90} fontFamily={SERIF} fontSize={120} fill={INK} textAnchor="middle"
          opacity={k} transform={`translate(0 ${(1 - k) * 26})`}>10–17 years</text>
      </g>
    </Full>
    {inkOn && <InkSheet edgeX={edge} fromRight t={it} id="s12-ink" seed={9}/>}
    {inkOn && <Full><defs><clipPath id="s12-wet"><path d={wet}/></clipPath></defs><g clipPath="url(#s12-wet)"><Timeline f={99} thin/></g></Full>}
  </>;
};

// ---- 2-02 A (left): the research question, phrase by phrase on three lines; find / assess circled in red ----
const RQ = {x: 1000, size: 60, ys: [430, 520, 610], ws: [8, 26, 8]}; // line 2 wider: each red circle keeps a full space clear of its neighbours
const RQ_LINES = ["How can computer-aided methods", "help scientists find and assess", "potential cancer drug candidates?"];
const Circle = ({line, before, word, f, t0, seed}) => {
  if (f < t0) return null;
  const sp = (before.match(/ /g) || []).length * RQ.ws[line];
  const x0 = RQ.x + textW(before, RQ.size) + sp, w = textW(word, RQ.size), y = RQ.ys[line];
  return <InkPath points={loopPts(x0 + w / 2, y - RQ.size * 0.3, w / 2 + 6, RQ.size * 0.54, {seed, turns: 1.1})} seed={seed}
    size={5} color={RED} progress={outCubic(ramp(f, t0, t0 + 10))} pressure="marker"/>;
};
const G202 = ({f, out}) => {
  const t = [wf(2.728) - 5, wf(5.292) - 5, wf(7.795) - 5];
  return <Full opacity={exitK(f, out)}>
    <Word x={RQ.x} y={335} size={38} f={f} t0={wf(1.025) - 5} opacity={0.6}>Our research question</Word>
    {RQ_LINES.map((s, i) => <g key={i} style={{wordSpacing: RQ.ws[i]}}><Word x={RQ.x} y={RQ.ys[i]} size={RQ.size} f={f} t0={t[i]}>{s}</Word></g>)}
    <Circle line={1} before="help scientists " word="find" f={f} t0={wf(6.614) - 5} seed={221}/>
    <Circle line={1} before="help scientists find and " word="assess" f={f} t0={wf(7.315) - 5} seed={222}/>
  </Full>;
};

// ---- 2-04 C (left): "We set ourselves two objectives." -> serif 1 and 2 with blank lines for the next beat ----
const NUM = [{x: 1250}, {x: 1560}];
const G204 = ({f, out}) => {
  const t1 = wf(1.808) - 5, t2 = t1 + 10, tl = t2 + 11;
  return <Full opacity={exitK(f, out)}>
    <Word x={NUM[0].x} y={640} size={300} f={f} t0={t1} anchor="middle">1</Word>
    <Word x={NUM[1].x} y={640} size={300} f={f} t0={t2} anchor="middle">2</Word>
    {f >= tl && NUM.map((n, i) => <InkLine key={i} from={[n.x - 95, 700]} to={[n.x + 95, 697]} bow={2} over={3} color={INK} seed={230 + i} size={7}
      progress={outCubic(ramp(f, tl, tl + 10))} pressure="marker"/>)}
  </Full>;
};

// ---- segment configs, script order. src = 1080p30 copies of 5_place/<name>_wide.mp4 (1-05/06/07 reuse the sample copies) ----
export const S12_SEGS = [
  {id: "1-01", who: "A", side: "left", src: "oncam2/s12/A_cam_1-01.mp4", in: 0, out: 164, G: G101, trig: "Hong / four / people"},
  {id: "1-03", who: "A", side: "left", src: "oncam2/s12/A_cam_1-03.mp4", in: 0, out: 149, G: G103, trig: "already / medicines / not / good"},
  {id: "1-05", who: "D", side: "right", src: "oncam2/s12/D_cam_1-05.mp4", in: 0, out: 100, G: G105, trig: "better / one"},
  {id: "1-06", who: "B", side: "left", src: "oncam2/s12/B_cam_1-06.mp4", in: 9, out: 74, G: G106, trig: "way harder"},
  {id: "1-07", who: "C", side: "left", src: "oncam2/s12/C_cam_1-07.mp4", in: 9, out: 110, G: G107, trig: "ten-to-seventeen-years"},
  {id: "2-02", who: "A", side: "left", src: "oncam2/s12/A_cam_2-02.mp4", in: 9, out: 316, G: G202, trig: "research / how / help / find / assess / potential"},
  {id: "2-04", who: "C", side: "left", src: "oncam2/s12/C_cam_2-04.mp4", in: 0, out: 101, G: G204, trig: "two"},
];
export const S12_GAP = 15; // 0.5 s black between segments
export const S12_FRAMES = reelLen(S12_SEGS, S12_GAP);
export const V3OnCam2S12 = () => <Reel segs={S12_SEGS} gap={S12_GAP}/>;
export const S12_SINGLE = S12_SEGS.map(s => ({id: "V3-OnCam2-S12-" + s.id, frames: segLen(s), component: () => <Segment seg={s}/>}));
