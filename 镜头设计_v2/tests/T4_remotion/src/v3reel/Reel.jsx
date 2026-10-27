import React from "react";
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from "remotion";
import {C, W, H, BoilProvider, clamp01, outCubic, outBack, loopPts, quad} from "../v3/core";
import {InkPath} from "../v3/ink";
import {HandText, Mono} from "../v3/type";
import {InkDefs, Grain} from "../v3/texture";
import {HandUnderline, ScribbleBurst} from "../v3/marks";
import {V3Demo} from "../v3/Demo";
import {V3LockKey} from "../v3/frames/LockKey";
import {V3Ladder} from "../v3/frames/Ladder";

// v3 style test reel (~49 s): TD stage visuals, the hand-drawn Remotion system and the four-corner speaker system,
// cut to the Sacrifice hook. Speaker cards are placeholders until real talking-head footage exists.
// Audio starts on a downbeat at song time 112.73 s; the TD clips were rendered against song time 116.66 s, so each
// TD excerpt starts at an offset whose bar phase matches the music under it.
const FPS = 30, BEAT = 60 / 123.05 * FPS, B = n => Math.round(n * BEAT);
export const REEL_FRAMES = B(100) + 8;

// speaker cards: home corners, and when each one is small (vo), big (on), or in the closing grid
const HOME = {A: [40, 40], B: [1580, 40], C: [40, 850], D: [1580, 850]};
const GRID = {A: [425, 150], B: [975, 150], C: [425, 520], D: [975, 520]};
const SMALL = [300, 190], BIG = [760, 480], GRIDSZ = [520, 330];
const SCHEDULE = [
  // [who, from, to, mode]
  ["A", B(4), B(8), "vo"], ["B", B(5), B(8), "vo"], ["C", B(6), B(8), "vo"], ["D", B(7), B(28), "vo"],
  ["A", B(28), B(52), "vo"], ["B", B(52), B(64), "vo"], ["C", B(64), B(80), "vo"],
  ["D", B(84), B(92), "on"], ["A", B(92), B(100) + 8, "grid"], ["B", B(92), B(100) + 8, "grid"],
  ["C", B(92), B(100) + 8, "grid"], ["D", B(92), B(100) + 8, "grid"],
];
const rectFor = (who, mode) => mode === "on" ? [(W - BIG[0]) / 2, 150, ...BIG] : mode === "grid" ? [...GRID[who], ...GRIDSZ] : [...HOME[who], ...SMALL];

const Card = ({who, f}) => {
  const list = SCHEDULE.filter(s => s[0] === who && f >= s[1] - 0 && f < s[2]);
  if (!list.length) return null;
  const [, from, , mode] = list[list.length - 1];
  const prev = SCHEDULE.filter(s => s[0] === who && s[2] <= from).pop();
  const p = outBack((f - from) / 10, 1.2);
  const a = prev && from - prev[2] < 2 ? rectFor(who, prev[3]) : [HOME[who][0] + SMALL[0] / 2, HOME[who][1] + SMALL[1] / 2, 0, 0];
  const b = rectFor(who, mode);
  const r = a.map((v, i) => v + (b[i] - v) * (prev && from - prev[2] < 2 ? outCubic((f - from) / 12) : p));
  const [x, y, w, h] = r;
  if (w < 4) return null;
  const s = w / 300, cx = x + w / 2, cy = y + h * 0.58;
  const head = loopPts(cx, cy - 34 * s, 30 * s, 36 * s, {seed: who.charCodeAt(0), turns: 1.08});
  const shoulders = quad([cx - 92 * s, y + h - 2], [cx, cy - 10 * s], [cx + 92 * s, y + h - 2], 30);
  const talk = mode === "vo" ? Math.max(0, Math.sin((f - from) * 0.9) * Math.sin((f - from) * 0.37)) : 0;
  const tilt = {A: -1.2, B: 1.0, C: 0.8, D: -0.9}[who];
  return <g transform={`rotate(${tilt} ${x + w / 2} ${y + h / 2})`}>
    <rect x={x} y={y} width={w} height={h} fill={C.ink} opacity={0.94}/>
    <InkPath points={[[x, y], [x + w, y + 2], [x + w - 1, y + h], [x + 2, y + h - 1], [x, y]]} size={2.2 * Math.max(1, s * 0.7)} color={C.bg} seed={who.charCodeAt(0) + 3}/>
    <InkPath points={head} size={3.2 * s} color={C.bg} seed={11}/>
    <InkPath points={shoulders} size={3.2 * s} color={C.bg} seed={12}/>
    <Mono x={x + 12 * s} y={y + 26 * s} size={20 * s} color={C.bg} weight={800}>{who}</Mono>
    <Mono x={x + w - 12 * s} y={y + 22 * s} size={11 * s} color={C.bg} anchor="end" opacity={0.7}>TALKING HEAD · PLACEHOLDER</Mono>
    {mode === "vo" ? <HandUnderline x={x + 8} y={y + h + 14} w={(w - 16) * (0.35 + 0.65 * talk)} size={6} color={C.verm} seed={31 + (f >> 2)}/> : null}
  </g>;
};

const Caption = ({text, f, from, to}) => {
  if (f < from || f >= to) return null;
  // captions live between the bottom corner cards (x 380-1540), so long lines shrink rather than run under a card
  const reveal = clamp01((f - from) / Math.max(8, text.length * 0.6));
  const size = Math.min(25, 1080 / (text.length * 0.7));
  const w = Math.min(1120, text.length * size * 0.7 + 40);
  return <g>
    <rect x={(W - w) / 2} y={958} width={w} height={54} fill={C.bg} opacity={0.82}/>
    <Mono x={W / 2} y={993} size={size} anchor="middle" reveal={reveal}>{text}</Mono>
  </g>;
};

const Tag = ({text, f, from, to}) => f >= from && f < to
  ? <Mono x={W / 2} y={34} size={15} anchor="middle" color={C.cyan} letterSpacing={2}>{text}</Mono> : null;

// TD excerpt that starts `inSec` into the clip
const TD = ({src, from, dur, inSec}) => <Sequence from={from} durationInFrames={dur}>
  <OffthreadVideo src={staticFile(src)} trimBefore={Math.round(inSec * FPS)} muted style={{width: "100%", height: "100%"}}/>
</Sequence>;

const Slam = ({word, at, f, size = 230}) => {
  if (f < at || f >= at + B(1)) return null;
  const k = outBack((f - at) / 5, 2.2);
  return <g transform={`translate(${W / 2} ${H / 2 + 70}) scale(${0.6 + 0.4 * k}) translate(${-W / 2} ${-H / 2 - 70})`}>
    <HandText x={W / 2} y={H / 2 + 70} size={size} anchor="middle" split={6}>{word}</HandText>
    <ScribbleBurst cx={W / 2} cy={H / 2} r0={300} r1={420} n={14} phase={(f - at) / 10} color={C.verm} seed={at}/>
  </g>;
};

export const V3Reel = () => {
  const f = useCurrentFrame();
  const invert = (f < 2) || (f >= B(84) && f < B(84) + 2);
  return <BoilProvider rate={2.5}>
    <AbsoluteFill style={{background: C.bg, filter: invert ? "invert(1)" : undefined}}>
      <Audio src={staticFile("mv/song_b.wav")} trimBefore={Math.round(112.73 * FPS)}
        volume={fr => Math.min(1, fr / 6, (REEL_FRAMES - fr) / 20)}/>

      {/* stage visuals */}
      <TD src="v3/td_vessels_red.mp4" from={B(8)} dur={B(28) - B(8)} inSec={0}/>
      <TD src="v3/td_liver_real_red.mp4" from={B(28)} dur={B(40) - B(28)} inSec={3.886}/>
      <Sequence from={B(40)} durationInFrames={B(52) - B(40)}><V3Demo grain={0}/></Sequence>
      <TD src="v3/td_protein.mp4" from={B(52)} dur={B(64) - B(52)} inSec={3.88}/>
      <Sequence from={B(64)} durationInFrames={B(72) - B(64)}><Sequence from={-120}><V3Demo grain={0}/></Sequence></Sequence>
      <Sequence from={B(72)} durationInFrames={B(80) - B(72)}><V3LockKey/></Sequence>
      <Sequence from={B(80)} durationInFrames={B(92) - B(80)}><AbsoluteFill style={{opacity: f >= B(84) ? 0.25 : 1}}><V3Ladder/></AbsoluteFill></Sequence>

      {/* overlay: words, cards, captions, evidence tags */}
      <svg width={W} height={H} style={{position: "absolute"}}>
        <InkDefs/>
        <Slam word="WHICH" at={B(0)} f={f}/>
        <Slam word="MOLECULE" at={B(1)} f={f} size={200}/>
        <Slam word="FIRST?" at={B(2)} f={f}/>
        {f >= B(4) && f < B(8) ? <g>
          <HandText x={W / 2} y={560} size={190} anchor="middle" split={4} reveal={clamp01((f - B(4)) / 8)}>WORTH TESTING?</HandText>
          <Mono x={W / 2} y={640} size={22} anchor="middle" color={C.cyan} letterSpacing={3} reveal={clamp01((f - B(5)) / 10)}>CDK20 × LIVER CANCER · STYLE TEST v3</Mono>
        </g> : null}
        {f >= B(92) ? <g>
          <HandText x={W / 2} y={1000} size={96} anchor="middle" split={3} reveal={clamp01((f - B(94)) / 8)}>WORTH TESTING?</HandText>
        </g> : null}
        {f >= B(84) && f < B(92) ? <Mono x={W / 2} y={720} size={34} anchor="middle" reveal={clamp01((f - B(85)) / 30)}>So 048 is a drug candidate. It is not a medicine.</Mono> : null}

        <Tag text="ILLUSTRATIVE · TOUCHDESIGNER" f={f} from={B(8)} to={B(28)}/>
        <Tag text="LIVER + VESSELS: BODYPARTS3D (REAL ANATOMY, CC BY 4.0) · FLOW: ILLUSTRATIVE" f={f} from={B(28)} to={B(40)}/>
        <Tag text="AI PREDICTED · ALPHAFOLD DB MODEL V6 · 048 POSE: OUR RE-DOCKING" f={f} from={B(52)} to={B(64)}/>

        <Caption f={f} from={B(10)} to={B(27)} text="Every drug starts with an early choice: which molecule to make and test first?"/>
        <Caption f={f} from={B(30)} to={B(39)} text="Primary liver cancer: 6th most common, 3rd in cancer deaths (GLOBOCAN 2020)"/>
        <Caption f={f} from={B(41)} to={B(51)} text="8,918 designs. 54 shortlisted. Seven actually made."/>
        <Caption f={f} from={B(53)} to={B(63)} text="AlphaFold's least confident part sat in the pocket. So they cut it off."/>
        <Caption f={f} from={B(65)} to={B(71)} text="Round two: 048 grips about fifteen times more tightly."/>

        {["A", "B", "C", "D"].map(w => <Card key={w} who={w} f={f}/>)}
      </svg>
      <Grain opacity={0.1}/>
    </AbsoluteFill>
  </BoilProvider>;
};
