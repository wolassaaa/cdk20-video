// M03 · 3-08, second pass. Bone paper means measured in this film, so the whole page is what had been measured about CDK20.
// The only thing missing is cut straight through the paper: a solid black keyhole that bleeds off the bottom edge. Generic keyhole, not a protein shape.
// Tally is Feng 2011: raised in 36 of 52 tumours, one block each. "no one had measured..." is 3-08 dialogue and still needs the director's approval (flag F24).
import React from "react";
import {Stage, Body, Foot, Plate, K, W, H, SEQUENCE, MONO} from "../kit";
import {Disp, Micro, Reg, CrossField} from "../kit_m";

const INK = K.bg, PAD = 64;

const Keyhole = ({x, y, s}) => <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
  <path transform={`translate(${x} ${y}) scale(${s})`} d="M-67 -15.1A156 156 0 1 1 67 -15.1L132 700H-132Z" fill={K.bg}/>
</svg>;

const Tally = ({x, y, w, h, n = 52, raised = 36}) => {
  const p = w / n;
  return <svg style={{position: "absolute", left: x, top: y}} width={w} height={h} shapeRendering="crispEdges">
    {Array.from({length: n}, (_, i) => <rect key={i} x={i * p} width={p * 0.62} height={h} fill={i < raised ? K.red : "none"} stroke={i < raised ? "none" : INK} strokeWidth={1.5}/>)}
  </svg>;
};

const ROWS = ["CCRK = CDK20", "target (a protein)", "later stage", "shorter survival", "10 data sets / 1,133 tumour / 674 healthy"];

export default () => <Stage bg={K.bone}>
  <CrossField x0={656} y0={352} x1={1100} y1={470} step={118} color={INK} s={6} weight={1.25}/>
  <CrossField x0={1760} y0={352} x1={1800} y1={1000} step={118} color={INK} s={6} weight={1.25}/>
  <Disp x={PAD - 8} y={36} size={306} color={INK}>CDK20</Disp>
  <Keyhole x={1466} y={726} s={1.42}/>

  <Disp x={PAD - 4} y={352} size={170} color={K.red}>69%</Disp>
  <Tally x={PAD} y={516} w={980} h={52}/>
  <Micro x={PAD} y={578} size={14} color={INK}>{"raised in 36 of 52 tumours  /  Feng 2011"}</Micro>

  <div style={{position: "absolute", left: PAD, top: 632, width: 1020}}>
    {ROWS.map(r => <div key={r} style={{borderTop: `2px solid ${INK}`, padding: "9px 0 11px"}}><Body on={K.bone} color={INK}>{r}</Body></div>)}
  </div>

  <div style={{position: "absolute", left: 1296, top: 434, width: 340, textAlign: "center"}}><Body color={K.bone}>no one had measured CDK20's shape</Body></div>
  <Plate kind="illustrative" x={1366} y={948}>schematic</Plate>

  {/* all 346 real letters up the right edge, and the source along the foot */}
  <svg width={40} height={H} style={{position: "absolute", left: W - 46, top: 0, overflow: "visible"}}>
    <g transform="scale(0.33333)"><text transform={`rotate(-90) translate(${-H * 3 + 150} 60)`} fontFamily={MONO} fontSize={30} fill={INK} textLength={(H - 100) * 3} lengthAdjust="spacingAndGlyphs">{SEQUENCE}</text></g>
  </svg>
  <Foot x={PAD} y={1010} color={INK} on={K.bone}>Feng 2011 · Ren 2023 · CDK20 sequence, UniProt Q8IZL9</Foot>
  <Reg x={W - 92} y={40} color={INK} flip/>
</Stage>;
