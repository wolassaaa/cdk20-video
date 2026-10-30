// Still 03 · 3-08. A full spec sheet with one missing thing, the largest cell: the shape. The sequence runs below it, known all along.
// No colour field in this act. The only colour is the 36 ticks, at the dim level of a row already read.
import React from "react";
import {Stage, SpecSheet, Foot, Plate, K, DIM, FAINT, MONO, SEQUENCE, M, colW} from "../kit";

const SHEET = colW(12), STRIP_Y = 984;  // strip baseline sits on the bottom margin

// Feng 2011 (E31): raised in 36 of 52 tumours, one tick each, no curve. Keeps "69%" tied to this one cohort.
const Tally = ({n = 52, raised = 36, pitch = 6}) => <svg width={n * pitch} height={26} shapeRendering="crispEdges" style={{marginLeft: 24}}>
  {Array.from({length: n}, (_, i) => <rect key={i} x={i * pitch} width={3} height={26} fill={i < raised ? K.red : FAINT} opacity={i < raised ? .55 : 1}/>)}
</svg>;

const ROWS = [
  {value: "CCRK = CDK20"},
  {value: "target (a protein)"},
  {value: <>69%<Tally/></>},
  {value: "later stage"},
  {value: "shorter survival"},
  {value: "10 data sets / 1,133 tumour / 674 healthy"},
  {value: "no one had measured CDK20's shape"},  // 3-08 dialogue, not a script screen text: needs director approval (F24). Delete this row to drop it; the frame still reads.
];

// Empty outline only. Generic keyhole, drawn here, not a protein shape.
const Keyhole = () => <svg width={1} height={1} style={{position: "absolute", left: "50%", top: "50%", overflow: "visible"}}>
  <path d="M-67 -15.1A156 156 0 1 1 67 -15.1L132 312H-132Z" fill="none" stroke={K.bone} strokeWidth={3}/>
</svg>;

// All 346 real letters, one line across the 12 columns. Not read, so it sits outside the six type settings, like the barcode.
// Drawn at 3x and scaled down so no browser minimum font size can touch it; textLength locks it to the grid. Sharp at --scale=2.
const Sequence = () => <svg width={SHEET} height={10} style={{position: "absolute", left: M, top: STRIP_Y - 10, overflow: "visible"}}>
  <g transform="scale(0.33333)"><text y={30} fontFamily={MONO} fontWeight={400} fontSize={20} fill={K.bone} textLength={SHEET * 3} lengthAdjust="spacing">{SEQUENCE}</text></g>
</svg>;

export default () => <Stage>
  <SpecSheet x={M} y={M} w={SHEET} rowsW={colW(5)} rows={ROWS} active={6} cell={{h: 830, children: <Keyhole/>}}/>
  {/* the sheet merges two studies, so the frame says which rows came from which */}
  <Foot x={M} y={848} color={DIM}>Feng 2011 (tumour rows)<br/>Ren 2023 (data sets)</Foot>
  <div style={{position: "absolute", right: M + 24, top: M + 24}}><Plate kind="illustrative">schematic</Plate></div>
  <Foot x={M} y={938} color={DIM}>CDK20 sequence · 346 residues · UniProt Q8IZL9</Foot>
  <Sequence/>
</Stage>;
