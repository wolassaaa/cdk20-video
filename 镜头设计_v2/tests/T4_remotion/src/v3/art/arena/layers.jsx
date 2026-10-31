// HKBU SCIE1007 coursework science video. Arena direction: type layers. Strings are verbatim from the brief. Coordinates come from the Blender anchors written to _work/*.json.
import React from "react";
import {AbsoluteFill} from "remotion";

export const BIG = "Big Shoulders";
export const BAR = "Barlow Semi Condensed";
const ink = "#F1F3F5";

const T = ({x, y, size, weight = 600, font = BAR, color = ink, spacing = 0, align = "left", w, lh = 1.12, shadow, style, children}) => (
  <div style={{position: "absolute", left: x, top: y, width: w, fontFamily: font, fontWeight: weight, fontSize: size, lineHeight: lh, letterSpacing: spacing, color, textAlign: align,
    whiteSpace: w ? "normal" : "nowrap", textShadow: shadow, ...style}}>{children}</div>
);

// evidence, told apart by fill and line as in the rest of the film: solid; solid with a dotted ring; hollow; thin dashes
const Plate = ({x, y, kind, size = 34, children, right}) => {
  const base = {position: "absolute", top: y, padding: "9px 20px 11px", fontFamily: BAR, fontWeight: 600, fontSize: size, lineHeight: 1.1, whiteSpace: "nowrap", letterSpacing: "0.02em"};
  if (right !== undefined) base.right = right; else base.left = x;
  const k = {
    measured: {background: ink, color: "#07090C"},
    ai: {background: "rgba(5,8,14,.86)", color: ink, outline: `3px dotted ${ink}`, outlineOffset: 5},
    ours: {background: "rgba(5,8,14,.55)", color: ink, border: `3px solid ${ink}`},
    schematic: {color: ink, border: `2px dashed ${ink}`},
  }[kind];
  return <div style={{...base, ...k}}>{children}</div>;
};

const Fill = ({children}) => <AbsoluteFill style={{background: "transparent"}}>{children}</AbsoluteFill>;
const anchor = {shadow: "0 0 18px rgba(0,0,0,.9), 0 2px 6px rgba(0,0,0,.9)"};

// floor numeral of T1, drawn on a 100 x 50 m plane, 20 px per metre
const T1floor = () => <Fill>
  <T x={0} w={2000} y={-30} size={640} font={BIG} weight={900} align="center" color="#fff" lh={1}>1,412</T>
  <T x={0} y={690} w={2000} size={176} font={BIG} weight={800} align="center" color="#fff" lh={1} style={{whiteSpace: "nowrap"}}>deaths in Hong Kong, 2022</T>
</Fill>;

const T1over = () => <Fill>
  <T x={1130} y={688} size={40} {...anchor}>10 cm</T>
</Fill>;

// T2, on the LED wall itself: frame px, right half of the wall (wall x 166-1754, y 190-818)
const T2wall = () => <Fill>
  <T x={984} y={268} w={716} size={73} weight={600} color="#fff" lh={1.13}>How can computer-aided methods help scientists find and assess potential cancer drug candidates?</T>
</Fill>;

const T3over = () => <Fill>
  <T x={110} y={452} w={620} size={72} font={BIG} weight={700} color="#D5DCF2" lh={1.06}>no one had measured CDK20's shape</T>
  <Plate x={112} y={622} kind="schematic" size={34}>schematic</Plate>
</Fill>;

const T4over = () => <Fill>
  <Plate x={84} y={84} kind="ai" size={38}>AlphaFold DB v6 · predicted</Plate>
  <T x={800} y={966} size={40} {...anchor}>1 nm</T>
</Fill>;

// T5, on the LED wall: frame px (wall x 123-1797, y 201-858)
const T5wall = () => <Fill>
  <T x={186} y={222} size={84} font={BIG} weight={800} color="#fff" lh={1}>Enzyme IC50</T>
  <T x={182} y={326} size={170} font={BIG} weight={900} color="#fff" lh={1}>048 = 33.4 ± 22.6 nM</T>
  <T x={186} y={518} w={760} size={62} weight={600} color="#fff" lh={1.1}>Just this much cuts the enzyme's activity in half.</T>
</Fill>;

const T5over = () => <Fill>
  <Plate x={188} y={684} kind="measured" size={38}>MEASURED · Ren 2023, Fig. 9A</Plate>
  <Plate x={1096} y={964} kind="ours" size={38}>OUR RE-DOCKING</Plate>
</Fill>;

// T6: labels over the gates, frame px from the T6 anchors. Dark stations stay readable but step back.
const stops = [[165, 525], [475, 507], [785, 488], [1088, 471], [1378, 454], [1651, 438]];
const stn = ["Target", "Hit", "Improve", "Cells & animals", "Clinical trials 1-2-3", "Approval"];
const T6over = () => <Fill>
  {stn.map((n, i) => <div key={n} style={{position: "absolute", left: stops[i][0] - 260 + (i === 3 ? -14 : i === 4 ? 20 : i === 5 ? 34 : 0), top: stops[i][1] - (i > 2 ? 112 : 64), width: 520, textAlign: "center", fontFamily: BAR}}>
    <div style={{fontSize: 46, fontWeight: 600, color: i < 3 ? "#FFF6E4" : "#CFD3D8", lineHeight: 1.1, textShadow: anchor.shadow}}>{n}</div>
    {i > 2 ? <div style={{fontSize: 36, fontWeight: 500, color: "#AEB4BA", lineHeight: 1.15}}>not reported</div> : null}
  </div>)}
  <T x={990} y={700} size={66} font={BIG} weight={800} color="#FFF6E4" {...anchor}>048</T>
</Fill>;

// colour script type: section, running time, the two lamps
const cs = [["S1", "2:21", 141, "#E3172D", "#C9CFD6"], ["S2", "2:22", 142, "#7F6BFF", "#9A3FD0"], ["S3", "2:09", 129, "#1F2BFF", "#C8D4FF"], ["S4", "3:33", 213, "#1E6BFF", "#DCF3FF"],
  ["S5", "2:19", 139, "#00C4AE", "#F2FFFB"], ["S6", "2:31", 151, "#3BC9A5", "#FFC85A"], ["S7", "0:49", 49, "#FFC85A", "#FF9E3D"], ["S8", "1:39", 99, "#FF9E3D", "#FFE3C2"]];
const CS = () => { let x = 0; const tot = cs.reduce((a, c) => a + c[2], 0); return <Fill>
  {cs.map(([s, t, d, a, b]) => { const w = d / tot * 1920; const el = <div key={s} style={{position: "absolute", left: x, top: 396, width: w, height: 84, borderLeft: x ? "1px solid #3a3a3a" : "none", boxSizing: "border-box", padding: "8px 0 0 10px", color: ink, fontFamily: BAR, background: "#0A0A0B"}}>
    <div style={{fontSize: 26, fontWeight: 600, lineHeight: 1}}>{s}{w > 70 ? <span style={{fontWeight: 500, color: "#AEB4BA"}}> {t}</span> : null}</div>
    <div style={{display: "flex", marginTop: 10}}><div style={{width: 30, height: 26, background: a}} /><div style={{width: 30, height: 26, background: b}} /></div>
  </div>; x += w; return el; })}
</Fill>; };

export const Layers = {
  T1floor: {w: 2000, h: 1000, C: T1floor},
  T1over: {w: 1920, h: 1080, C: T1over},
  T2wall: {w: 1920, h: 1080, C: T2wall},
  T3over: {w: 1920, h: 1080, C: T3over},
  T4over: {w: 1920, h: 1080, C: T4over},
  T5wall: {w: 1920, h: 1080, C: T5wall},
  T5over: {w: 1920, h: 1080, C: T5over},
  T6over: {w: 1920, h: 1080, C: T6over},
  CS: {w: 1920, h: 480, C: CS},
};
