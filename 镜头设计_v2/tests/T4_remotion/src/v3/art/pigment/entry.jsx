// HKBU SCIE1007 coursework science video. Pigment direction: text only, one still per shot, read back by styleframes/art/pigment/code/comp.py as ink masks.
// Black ground. Red text goes on plate A, green on plate B, blue is knocked out to paper. The printing itself happens in comp.py with a real multiply.
// Fonts, all SIL OFL on Google Fonts: Fraunces, IBM Plex Mono, Caveat. Wording copied from 00_总简报.md, do not edit it here.
import React from "react";
import {Composition, registerRoot} from "remotion";
import {loadFont as loadF} from "@remotion/google-fonts/Fraunces";
import {loadFont as loadM} from "@remotion/google-fonts/IBMPlexMono";
import {loadFont as loadC} from "@remotion/google-fonts/Caveat";

const SERIF = loadF("normal", {weights: ["500", "600", "700", "900"], subsets: ["latin"]}).fontFamily;
const MONO = loadM("normal", {weights: ["500", "600"], subsets: ["latin"]}).fontFamily;
const HAND = loadC("normal", {weights: ["600", "700"], subsets: ["latin"]}).fontFamily;
const A = "#f00", B = "#0f0", K = "#00f";

const T = ({x, y, w, f = SERIF, s, wt = 600, lh = 1.1, ls = 0, c = A, align = "left", children}) => (
  <div style={{position: "absolute", left: x, top: y, width: w, fontFamily: f, fontSize: s, fontWeight: wt, lineHeight: lh, letterSpacing: ls, color: c, textAlign: align,
    whiteSpace: w ? "normal" : "nowrap", fontVariantNumeric: "lining-nums"}}>{children}</div>
);
const STRIP_Y = 1080 - 40 - 44;
const Strip = ({c = A, children}) => <T x={310} y={STRIP_Y} f={MONO} s={36} wt={500} lh={1.3} ls={0.5} c={c}>{children}</T>;
const Tag = ({c = A, x = 1872, y = STRIP_Y, children}) => <T x={x - 1000} y={y} w={1000} f={MONO} s={36} wt={500} lh={1.3} c={c} align="right">{children}</T>;
const Station = ({x, y, children, c = A, f = SERIF, s = 56, wt = 600, w = 300, lh = 1.05}) => <T x={x - w / 2} y={y} w={w} f={f} s={s} wt={wt} lh={lh} c={c} align="center">{children}</T>;

export const STATIONS = [170, 480, 790, 1120, 1430, 1740];

const Frames = {
  T1: () => <>
    <T x={1090} y={560} f={SERIF} s={250} wt={900} lh={1} ls={-7}>1,412</T>
    <T x={1098} y={836} f={SERIF} s={58} wt={600} lh={1.08}>deaths in Hong Kong, 2022</T>
    <Strip>THIS RED: HAEM · THIS YELLOW: BILIRUBIN</Strip>
  </>,
  T2: () => <>
    <T x={92} y={92} w={770} f={SERIF} s={88} wt={600} lh={1.13} ls={-0.5}>How can computer-aided methods help scientists find and assess potential cancer drug candidates?</T>
    <T x={1610} y={886} f={HAND} s={50} wt={700} lh={1} c={B}>placeholder</T>
    <Strip>THIS PINK: EOSIN · THIS BROWN: MELANIN</Strip>
  </>,
  T3: () => <>
    <Strip c={K}>THIS BLACK: CARBON</Strip>
    <T x={1656} y={STRIP_Y - 10} f={HAND} s={56} wt={700} lh={1.2} c={K}>schematic</T>
  </>,
  T4: () => <>
    <Strip>THIS BLUE: PRUSSIAN BLUE</Strip>
    <Tag x={1872} y={STRIP_Y}>AlphaFold DB v6 · predicted</Tag>
  </>,
  T5: () => <>
    <T x={92} y={196} f={MONO} s={46} wt={500} lh={1.2} c={K}>Enzyme IC50</T>
    <T x={86} y={252} f={SERIF} s={132} wt={900} lh={1.05} ls={-2} c={K}>048 =</T>
    <T x={86} y={386} f={SERIF} s={132} wt={900} lh={1.05} ls={-2} c={K}>33.4 ± 22.6 nM</T>
    <T x={92} y={560} w={900} f={SERIF} s={54} wt={600} lh={1.14} c={K}>Just this much cuts the enzyme's activity in half.</T>
    <T x={146} y={912} f={MONO} s={36} wt={500} lh={1.3} c={K}>MEASURED · Ren 2023, Fig. 9A</T>
    <T x={1040} y={912} f={MONO} s={36} wt={500} lh={1.3} c={K}>OUR RE-DOCKING</T>
    <Strip>THIS RED: HAEM · THIS BLUE: INDIGO</Strip>
  </>,
  T6: () => <>
    <Station x={STATIONS[0]} y={562}>Target</Station>
    <Station x={STATIONS[1]} y={562}>Hit</Station>
    <Station x={STATIONS[2]} y={562}>Improve</Station>
    <T x={600} y={656} w={380} f={SERIF} s={170} wt={900} lh={1} ls={-3} align="right">048</T>
    <Station x={STATIONS[3]} y={530} c={B} f={HAND} s={60} wt={700} w={290} lh={1}>Cells & animals</Station>
    <Station x={STATIONS[4]} y={530} c={B} f={HAND} s={60} wt={700} w={290} lh={1}>Clinical trials 1-2-3</Station>
    <Station x={STATIONS[5]} y={530} c={B} f={HAND} s={60} wt={700} w={290} lh={1}>Approval</Station>
    <Station x={STATIONS[3]} y={668} c={B} f={HAND} s={54} wt={600} w={300}>not reported</Station>
    <Station x={STATIONS[4]} y={668} c={B} f={HAND} s={54} wt={600} w={300}>not reported</Station>
    <Station x={STATIONS[5]} y={668} c={B} f={HAND} s={54} wt={600} w={300}>not reported</Station>
    <Strip>THIS BLUE: INDIGO · THIS YELLOW: BILIRUBIN</Strip>
  </>,
  CS: () => {
    const dur = [141, 142, 129, 213, 139, 151, 49, 99];
    const names = [["S1 2:21", "HAEM", "BILIRUBIN"], ["S2 2:22", "EOSIN", "MELANIN"], ["S3 2:09", "HAEMATOXYLIN", "CARBON BLACK"], ["S4 3:33", "PRUSSIAN BLUE", "HAEM"], ["S5 2:19", "HAEM", "INDIGO"], ["S6 2:31", "INDIGO", "BILIRUBIN"], ["S7 0:49", "BILIRUBIN", "IRON OXIDE"], ["S8 1:39", "HAEM", "CELLULOSE"]];
    const total = dur.reduce((a, b) => a + b, 0);
    let x = 0;
    const ticks = [[0, 0.42, "T1"], [1, 0.2, "T2"], [2, 0.84, "T3"], [3, 0.3, "T4"], [4, 0.8, "T5"], [5, 0.74, "T6"]];
    const left = dur.map((d) => { const v = x; x += d; return v / total * 1920; });
    return <>
      {names.map((n, i) => <div key={i} style={{position: "absolute", left: left[i] + 6, top: 354, width: dur[i] / total * 1920 - 6}}>
        <div style={{fontFamily: MONO, fontWeight: 600, fontSize: i === 6 ? 14 : 22, lineHeight: 1.25, color: A}}>{n[0]}</div>
        <div style={{fontFamily: MONO, fontWeight: 500, fontSize: i === 6 ? 13 : 19, lineHeight: 1.3, color: A}}>{n[1]}</div>
        <div style={{fontFamily: MONO, fontWeight: 500, fontSize: i === 6 ? 13 : 19, lineHeight: 1.3, color: A}}>{n[2]}</div>
      </div>)}
      {ticks.map(([i, u, t]) => <div key={t} style={{position: "absolute", left: left[i] + u * dur[i] / total * 1920 - 15, top: 442, fontFamily: MONO, fontWeight: 600, fontSize: 22, color: A}}>{t}</div>)}
    </>;
  },
};

const Frame = ({id}) => {
  const F = Frames[id];
  return <div style={{position: "absolute", inset: 0, background: "#000"}}><F /></div>;
};

const Root = () => <>{Object.keys(Frames).map((id) => <Composition key={id} id={id} component={Frame} width={1920} height={1080} fps={30} durationInFrames={1} defaultProps={{id}} />)}</>;
registerRoot(Root);
