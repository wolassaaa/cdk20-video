// Still 08 · 5-08 · the bar that does not close. Both values are enzyme IC50, so they share one axis, and the axis says so. 001's bound comes from the body text with no figure number (E15); 048 is Fig. 9A (E20). Each carries its own plate.
// Screen text verbatim from marathon_refs_20261031.md section 4 still 8: "001 > 6,000 nM", "048 = 33.4 ± 22.6 nM". "Enzyme IC50" is the wording of script 5-04.
// Kd stays off this frame on purpose (section 3 S5 and section 4): 048's Kd 566.7 ± 256.2 nM and 049's 360.0 ± 14.1 nM
// belong to the earlier Kd row, never to an IC50 axis. The ± is never dropped.
// Shorter is better here, so the long bar is the loser: 001 is DIM and 048 is the only full-bone data on screen.
import React from "react";
import {Stage, Big, Body, Foot, Plate, K, DIM, M, W} from "../kit";
import {NmBar, PX_PER_NM} from "./lib_s5";

// --- one real linear axis, in nM. Scale and bar live in lib_s5.jsx, shared with still 10 ---
const AX = M;
const nmX = nm => AX + nm * PX_PER_NM;
// 048:   33.4 nM x 0.27 = 9.0 px.  ± 22.6 nM x 0.27 = 6.1 px, so the whisker spans
//        10.8..56.0 nM = 2.9..15.1 px — wider than the bar itself, because the SD is 68% of the value.
// 001: 6,000 nM x 0.27 = 1620 px, so the 6,000 tick stands on the frame at x = 1716 and the bar runs past it and out.
//        It is a lower bound (E15, flag F26: no exact value exists), so the bar is never capped — it
//        leaves the frame and Stage's overflow clips it. Do not add an end cap or an arrow head.
// The two drawn lengths are not a ratio: 001 has no exact value, so the gap is a floor, not a measurement.
const IC50 = {
  n001: {bound: 6000, label: "001 > 6,000 nM", y: 368},            // E15, body text, no figure
  n048: {value: 33.4, sd: 22.6, label: "048 = 33.4 ± 22.6 nM", y: 692},  // E20, n = 3
};
const BAR_H = 48, AXIS_Y = 800;
// ticks every 1,000 nM; only the majors get a label. No gridlines: the labels sit between the bars.
const MAJOR = [0, 2000, 4000, 6000], MINOR = [1000, 3000, 5000];
const comma = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");  // "6,000" style, as section 4 writes it

const one = IC50.n001, forty8 = IC50.n048;

export default () => <Stage>
  <svg width={W} height={AXIS_Y + 60} style={{position: "absolute", left: 0, top: 0}} shapeRendering="crispEdges">
    {/* the shared axis both bars are measured against */}
    <line x1={AX} y1={AXIS_Y} x2={W} y2={AXIS_Y} stroke={DIM} strokeWidth={2}/>
    {[...MAJOR, ...MINOR].map(nm => <line key={`t${nm}`} x1={nmX(nm)} y1={AXIS_Y} x2={nmX(nm)} y2={AXIS_Y + (MAJOR.includes(nm) ? 14 : 8)} stroke={MAJOR.includes(nm) ? K.bone : DIM} strokeWidth={2}/>)}

    {/* 001: a lower bound, so no right edge is ever drawn */}
    <rect x={AX} y={one.y} width={W - AX} height={BAR_H} fill={DIM}/>

    {/* 048: the whole point is how short it is; the error bar is wider than the bar */}
    <NmBar x={AX} y={forty8.y} h={BAR_H} value={forty8.value} sd={forty8.sd}/>
  </svg>

  {/* plain-language lines sit under their own number and take its colour. 001's is script 5-05. 048's starts past the whisker, on the bar's own band */}
  <Big x={M} y={216} size={64} color={DIM}>{one.label}</Big>
  <div style={{position: "absolute", right: M, top: 222}}><Plate kind="measured" style={{background: DIM}}/></div>
  <Body x={M} y={296} color={DIM}>The key went in. It barely turned.</Body>

  <Big x={M} y={576} size={96}>{forty8.label}</Big>
  <div style={{position: "absolute", right: M, top: 599}}><Plate kind="measured" fig="9A"/></div>
  <Body x={M + 40} y={693} style={{whiteSpace: "nowrap"}}>Far less molecule, same job done. The key turned.</Body>

  {MAJOR.map(nm => <Foot key={`l${nm}`} x={nm ? nmX(nm) - 60 : AX} y={AXIS_Y + 26} w={120} style={{textAlign: nm ? "center" : "left"}}>
    {comma(nm)}
  </Foot>)}
  <Foot x={AX} y={AXIS_Y + 70}>Enzyme IC50 (nM)</Foot>{/* still 7 has just taught Kd; this keeps the bars from being read as Kd */}
</Stage>;
