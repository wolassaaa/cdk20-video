// Still 12 · 6-11: the end of the road. Six stations in six outlines (section 2.2 replaces 1-09's six identical dots); each drug's lane is as long as the road it walked and ends over its stop, so no drop lines.
// Stations 1-3 solid and 4-6 dashed is the state 6-10 leaves them in: 048's progress, so the road goes dashed at the door of station 4.
// Blue route = the script's cyan tag. It is a line, not an AI plate: 2.3 keeps that plate for AI predicted or generated results, and lirafugratinib is neither (F20), and it would rank an approved drug below 048.
// So both drug labels are plain bone text, none of the four evidence plates. 048 is bone because its plate flipped at 5-01, when the lab numbers came back. No red flow on this frame: red with blue would break one colour per screen.
// The stops are sourced. lirafugratinib: Approval (F20). EXS-21546: Phase 1 in Wang 2023 Table 8, then wound down (F20), so it ends on the first gate of station 5, past 048. 048: door of station 4 (5-10, 6-10).
// 1-09's illustrative numbers are not used here.
import React from "react";
import {Stage, Body, PlateText, Foot, Plate, K, DIM, W, H, M, colX, colW} from "../kit";

const G = 160, GY = 540, RY = GY + G / 2, NY = GY + G + 24;     // glyph height and top, road y, name y
const X = [0, 2, 4, 6, 8, 10].map(colX);                        // one station every two columns
const LANE = [306, 378, 450], LANE_H = 54, TEXT_X = M + 18;     // stacked right above the glyphs; TEXT_X lines the labels up with the text inside 048's plate
const STOP = [X[5] + colW(2), X[4] + 44, X[3]];                 // far edge of Approval, first gate, door of station 4
const GATES = [[0, 72], [58, 116], [116, 160]];                 // x, height: three phases, three gates on the road
const ROAD = [[X[0] + 110, X[1] + 2], [X[1] + 158, X[2] + 10], [X[2] + 150, X[3]]];  // solid runs, tucked into each glyph's edge
const EXS = "EXS-21546 · stopped 2023", EXS_W = EXS.length * 18.2;  // PlateText is 18.2 px a character

const ON = {fill: K.bone}, OFF = {fill: K.bg, stroke: DIM, strokeWidth: 5, strokeDasharray: "12 9"};
const STATIONS = [
  ["Target", <><circle cx="80" cy="56" r="52" {...ON}/><path d="M58 92H102L122 160H38Z" {...ON}/></>],  // keyhole: the lock of S3
  ["Hit", <path d="M160 80L120 11H40L0 80L40 149H120Z" {...ON}/>],                                      // one ring: a first molecule
  ["Improve", <><path d="M130.8 44.4A62 62 0 1 1 58.8 21.7" fill="none" stroke={K.bone} strokeWidth="22"/><path d="M96.4 8L49.9 -2.7L67.7 46.1Z" {...ON}/></>],  // the chemist's loop of 4-06
  ["Cells & animals", <><circle cx="80" cy="80" r="77" {...OFF}/><circle cx="104" cy="60" r="26" {...OFF}/></>],  // cell and nucleus
  ["Clinical trials 1-2-3", GATES.map(([x, h]) => <rect key={x} x={x} y={80 - h / 2} width="44" height={h} {...OFF}/>)],
  ["Approval", <><rect width={colW(2)} height={G} {...OFF}/><path d="M74 84L116 122L198 36" {...OFF} fill="none"/></>],  // a licence with a tick
];

// A route from Target to where the drug stopped, 3 px of blue along the bottom of its lane.
const Route = ({lane, end}) => <div style={{position: "absolute", left: M, top: lane + LANE_H - 3, width: end - M, height: 3, background: K.blue}}/>;

export default () => <Stage>
  <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
    {ROAD.map(([a, b]) => <line key={a} x1={a} y1={RY} x2={b} y2={RY} stroke={K.bone} strokeWidth="4"/>)}
    <line x1={X[3] + G} y1={RY} x2={X[5]} y2={RY} stroke={DIM} strokeWidth="4" strokeDasharray="12 9"/>
    {STATIONS.map(([name, art], i) => <g key={name} transform={`translate(${X[i]} ${GY})`}>{art}</g>)}
  </svg>

  <PlateText x={TEXT_X} y={LANE[0] + 6} style={{whiteSpace: "nowrap"}}>lirafugratinib (RLY-4008) · FDA approved, 23 Sep 2026 · bile duct cancer</PlateText>
  <Route lane={LANE[0]} end={STOP[0]}/>

  {/* the strike comes first, so it runs behind the letters and leaves them open */}
  <div style={{position: "absolute", left: TEXT_X - 10, top: LANE[1] + 23, width: EXS_W + 20, height: 3, background: DIM}}/>
  <PlateText x={TEXT_X} y={LANE[1] + 6} style={{whiteSpace: "nowrap"}}>{EXS}</PlateText>
  <Route lane={LANE[1]} end={STOP[1]}/>

  <Plate kind="measured" x={M} y={LANE[2]} style={{width: STOP[2] - M, boxSizing: "border-box"}}>048</Plate>
  <Foot x={STOP[2] + 24} y={LANE[2] + 12}>made public for other researchers</Foot>

  {STATIONS.map(([name], i) => <Body key={name} x={X[i]} y={NY} color={i < 3 ? K.bone : DIM}>
    {name.split(/ (?=1-2-3)/).map(line => <div key={line} style={{whiteSpace: "nowrap"}}>{line}</div>)}
  </Body>)}

  <Foot x={M} y={953} color={DIM}>Wang 2023 Table 8 · FDA (23 Sep 2026) · Business Wire, 3 Oct 2023 · GEN, 24 Jan 2023</Foot>
</Stage>;
