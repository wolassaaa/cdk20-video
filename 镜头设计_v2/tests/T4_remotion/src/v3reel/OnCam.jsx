import React from "react";
import {AbsoluteFill, Sequence, useCurrentFrame} from "remotion";
import {C, W, H, BoilProvider, clamp01, outCubic, outBack, loopPts, hash} from "../v3/core";
import {InkPath} from "../v3/ink";
import {HandText, Mono} from "../v3/type";
import {InkDefs, Grain} from "../v3/texture";
import {HandCircle, ScribbleBurst, Highlight} from "../v3/marks";

// Talking-head + motion-graphics sample: the speaker's card takes one half of the frame, and the other half draws the
// numbers and icons the line is about, on the keyword. Three ON-CAM lines from script v3.3. Speaker = placeholder card.
const FPS = 30;
export const ONCAM_FRAMES = 3 * 4 * FPS + 30;

const Speaker = ({side, who, f}) => {
  const x = side === "left" ? 60 : 1000, y = 90, w = 860, h = 900;
  const p = outBack(f / 10, 1.1), s = 0.92 + 0.08 * p;
  const cx = x + w / 2, cy = y + h * 0.55;
  return <g transform={`translate(${cx} ${y + h / 2}) scale(${s}) translate(${-cx} ${-(y + h / 2)}) rotate(${side === "left" ? -0.8 : 0.8} ${cx} ${cy})`}>
    <rect x={x} y={y} width={w} height={h} fill={C.ink}/>
    <InkPath points={loopPts(cx, cy - 170, 120, 145, {seed: who.charCodeAt(0), turns: 1.08})} size={7} color={C.bg} seed={11}/>
    <InkPath points={[[cx - 330, y + h - 4], [cx - 200, cy + 40], [cx, cy - 20], [cx + 200, cy + 40], [cx + 330, y + h - 4]]} size={7} color={C.bg} seed={12}/>
    <Mono x={x + 30} y={y + 60} size={44} color={C.bg} weight={800}>{who}</Mono>
    <Mono x={x + w - 30} y={y + 50} size={18} color={C.bg} anchor="end" opacity={0.6}>TALKING HEAD · PLACEHOLDER</Mono>
  </g>;
};

const Subtitle = ({text}) => <g>
  <rect x={W / 2 - 700} y={1000} width={1400} height={52} fill={C.bg} opacity={0.85}/>
  <Mono x={W / 2} y={1035} size={26} anchor="middle">{text}</Mono>
</g>;

// 1-01  A (left): "Every day in Hong Kong, about four people die of liver cancer."
const Shot1 = () => {
  const f = useCurrentFrame(), k = 45; // "four" lands about 1.5 s in
  const person = (i, x) => {
    const p = clamp01((f - k - 8 - i * 6) / 10);
    if (p <= 0) return null;
    return <g key={i} opacity={p}>
      <InkPath points={loopPts(x, 560, 26, 30, {seed: i + 3})} size={5} color={C.verm} seed={i + 20} progress={p}/>
      <InkPath points={[[x, 595], [x, 700]]} size={6} color={C.verm} seed={i + 30} progress={p}/>
      <InkPath points={[[x - 45, 640], [x, 615], [x + 45, 640]]} size={5} color={C.verm} seed={i + 40} progress={p}/>
      <InkPath points={[[x - 35, 790], [x, 700], [x + 35, 790]]} size={5} color={C.verm} seed={i + 50} progress={p}/>
    </g>;
  };
  return <svg width={W} height={H} style={{position: "absolute"}}><InkDefs/>
    <Speaker side="left" who="A" f={f}/>
    <Mono x={1080} y={200} size={26} color={C.cyan} letterSpacing={4} reveal={clamp01((f - 10) / 12)}>LIVER CANCER · HONG KONG</Mono>
    {f >= k ? <g transform={`translate(1500 400) scale(${0.6 + 0.4 * outBack((f - k) / 6, 2.2)}) translate(-1500 -400)`}>
      <HandText x={1420} y={470} size={300} split={5}>4</HandText>
      <ScribbleBurst cx={1500} cy={360} r0={170} r1={260} n={12} phase={(f - k) / 12} color={C.verm} seed={7}/>
    </g> : null}
    {f >= k ? <HandText x={1640} y={440} size={64} reveal={clamp01((f - k - 4) / 8)}>a day</HandText> : null}
    {[1150, 1330, 1510, 1690].map((x, i) => person(i, x))}
    <Mono x={1080} y={900} size={16} color={C.dim}>HK Cancer Registry 2022: 1,412 liver cancer deaths ≈ 3.9 a day</Mono>
    <Subtitle text="Every day in Hong Kong, about four people die of liver cancer."/>
  </svg>;
};

// 6-04 D (right): "Millions of compounds screened before. Here? Thirteen made."  then 6-05 B: "Thirteen. That's honestly wild."
const Shot2 = () => {
  const f = useCurrentFrame(), squeeze = outCubic((f - 50) / 18), slam = 78;
  const dots = [];
  for (let i = 0; i < 2600; i++) {
    const keep = i < 13;
    const x0 = 120 + hash(i, 1) * 760, y0 = 170 + hash(i, 2) * 700;
    const ang = i / 13 * Math.PI * 2, x1 = 500 + Math.cos(ang) * 150, y1 = 520 + Math.sin(ang) * 150;
    const show = clamp01((f - 4 - hash(i, 3) * 20) / 6);
    if (!keep && squeeze >= 1) continue;
    const x = keep ? x0 + (x1 - x0) * squeeze : x0 + (500 - x0) * squeeze;
    const y = keep ? y0 + (y1 - y0) * squeeze : y0 + (520 - y0) * squeeze;
    dots.push(<circle key={i} cx={x} cy={y} r={keep ? 3 + 9 * squeeze : 2.2} fill={keep ? C.verm : C.cyan} opacity={show * (keep ? 1 : 1 - squeeze)}/>);
  }
  return <svg width={W} height={H} style={{position: "absolute"}}><InkDefs/>
    <Speaker side="right" who={f < slam ? "D" : "B"} f={f < slam ? f : f - slam}/>
    {dots}
    <Mono x={120} y={140} size={26} color={C.cyan} letterSpacing={3} reveal={clamp01(f / 10)}>{squeeze < 0.5 ? "SCREENED BEFORE: MILLIONS" : "MADE HERE: 13"}</Mono>
    {f >= slam ? <g><HandText x={500} y={580} size={220} anchor="middle" split={6}>13</HandText>
      <ScribbleBurst cx={500} cy={510} r0={190} r1={280} n={14} phase={(f - slam) / 12} color={C.acid} seed={9}/></g> : null}
    <Mono x={120} y={940} size={15} color={C.dim}>Wang 2023: screening by the millions · Ren 2023: 7 + 6 made</Mono>
    <Subtitle text={f < slam ? "Millions of compounds screened before. Here? Thirteen made." : "Thirteen. That's honestly wild."}/>
  </svg>;
};

// 5-09 C (left): "This time, the key turned."
const Shot3 = () => {
  const f = useCurrentFrame(), turnAt = 36, p = outBack((f - turnAt) / 14, 1.6), lit = clamp01((f - turnAt - 8) / 10);
  const lx = 1440, ly = 420;
  return <svg width={W} height={H} style={{position: "absolute"}}><InkDefs/>
    <Speaker side="left" who="C" f={f}/>
    <circle cx={lx} cy={ly} r={250} fill={C.verm} opacity={0.18 * lit}/>
    <InkPath points={[[lx - 150, ly - 40], [lx + 150, ly - 40], [lx + 150, ly + 210], [lx - 150, ly + 210], [lx - 150, ly - 40]]} size={8} color={lit > 0.5 ? C.verm : C.ink} seed={3}/>
    <InkPath points={loopPts(lx, ly - 40, 100, 120, {a0: Math.PI, turns: 0.5, seed: 5})} size={8} color={lit > 0.5 ? C.verm : C.ink} seed={4}/>
    <g transform={`rotate(${90 * (f < turnAt ? 0 : p)} ${lx} ${ly + 90})`}>
      <InkPath points={loopPts(lx, ly + 20, 30, 30, {seed: 8})} size={7} color={C.cyan} seed={6}/>
      <InkPath points={[[lx, ly + 50], [lx, ly + 150], [lx + 30, ly + 150]]} size={7} color={C.cyan} seed={7}/>
    </g>
    {f >= turnAt + 10 ? <g>
      <Mono x={1180} y={830} size={24} color={C.dim} reveal={clamp01((f - turnAt - 10) / 8)}>001: IC50 &gt; 6,000 nM</Mono>
      <Highlight x={1165} y={862} w={560} h={74} progress={clamp01((f - turnAt - 14) / 8)}/>
      <Mono x={1190} y={913} size={40} color={C.bg} weight={800} reveal={clamp01((f - turnAt - 16) / 6)}>048: IC50 33.4 nM</Mono>
    </g> : null}
    {f >= turnAt + 4 ? <HandCircle cx={lx} cy={ly + 80} rx={300} ry={250} color={C.acid} progress={clamp01((f - turnAt - 4) / 12)}/> : null}
    <Mono x={1180} y={200} size={22} color={C.dim}>MEASURED · Ren et al. 2023, Fig. 9A</Mono>
    <Subtitle text="This time, the key turned."/>
  </svg>;
};

export const V3OnCam = () => <BoilProvider rate={2.5}>
  <AbsoluteFill style={{background: C.bg}}>
    <Sequence durationInFrames={120}><Shot1/></Sequence>
    <Sequence from={120} durationInFrames={150}><Shot2/></Sequence>
    <Sequence from={270} durationInFrames={120}><Shot3/></Sequence>
    <Grain opacity={0.1}/>
  </AbsoluteFill>
</BoilProvider>;
