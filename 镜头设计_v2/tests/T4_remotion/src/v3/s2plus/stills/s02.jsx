// Still 02 · 2-06. One line sweeps down six cards: five read to the end, the Perspective only to its abstract, the rest of that card empty.
// Six slots on the 12-column grid hold seven sheets, because "method paper x2" is a doubled card. Left to right is the VO order.
// The fine lines are drawn marks, not text or page counts. Rough page shapes only: two-column articles, one-column review and chapter.
import React from "react";
import {Stage, Body, Foot, PlateText, DashBox, K, DIM, W, H, M, colX, colW} from "../kit";

const CW = colW(2), TOP = M, BOT = 864, PAD = 20;  // shared top and bottom, so fill reads as height
const TEXT_END = BOT - PAD, PITCH = 10;             // last row of text on a full card
const ABSTRACT = TOP + 176;                         // where the abstract ends on every card
const STEP = colX(10);                              // the scan runs along the card bottoms, then steps up here: the last card was read only to its abstract
const BACK = 12;                                    // offset of the sheet behind a doubled card

const CARDS = [
  {cols: 2, ink: K.bone, frame: K.bone, stamped: true},  // main paper, tagged by its stamp, which replaces its abstract rows
  {tag: "original study", cols: 2},
  {tag: "method paper x2", cols: 2, doubled: true},
  {tag: "review", cols: 1},
  {tag: "book chapter", cols: 1, inset: 20},
  {cols: 1, ink: K.bone, stop: ABSTRACT},           // Perspective, labelled large below
];

const rng = s => () => (s = s * 16807 % 2147483647) / 2147483647;  // Lehmer: the same lines on every render
const snap = v => Math.round(v * 2) / 2;                            // half a CSS px is one device px at --scale=2

// Ragged rows for one text column, a blank row between paragraphs. run = rows left in the paragraph.
const rows = (x, y0, y1, w, r, run = 5 + Math.floor(r() * 8)) => {
  let d = "", left = run;
  for (let y = y0; y + PITCH <= y1; y += PITCH, left--) {
    if (left < 0) { left = 6 + Math.floor(r() * 8); continue; }
    d += `M${x} ${y + .75}H${x + snap(w * (left ? .9 + .1 * r() : .25 + .45 * r()))}`;
  }
  return d;
};

const Card = ({x, cols, ink = DIM, frame = DIM, inset = 0, doubled, stop, stamped, seed}) => {
  const r = rng(seed), off = doubled ? BACK : 0, w = CW - off, top = TOP + off, h = BOT - top;
  const tx = x + PAD + inset, m = w - 2 * (PAD + inset), head = top + PAD, cw = snap((m - 12 * (cols - 1)) / cols);
  const edge = {fill: "none", stroke: frame, strokeWidth: 1.5};
  return <>
    {doubled ? <rect x={x + BACK + .75} y={TOP + .75} width={w - 1.5} height={h - 1.5} {...edge}/> : null}
    {stop ? <path d={`M${x + .75} ${stop}V${TOP + .75}H${x + CW - .75}V${stop}`} {...edge}/>
      : <rect x={x + .75} y={top + .75} width={w - 1.5} height={h - 1.5} {...edge} fill={K.bg}/>}
    <path d={`M${tx} ${head + 2}H${tx + snap(m * .82)}M${tx} ${head + 14}H${tx + snap(m * .5)}`} stroke={ink} strokeWidth={4} fill="none"/>
    {stamped ? null : <path d={rows(tx, head + 36, ABSTRACT - 12, m, r, Infinity)} stroke={ink} strokeWidth={1.5} fill="none"/>}
    {stop ? null : <path d={Array.from({length: cols}, (_, c) => rows(tx + c * (cw + 12), ABSTRACT + 8, TEXT_END + 6, cw, r)).join("")} stroke={ink} strokeWidth={1.5} fill="none"/>}
  </>;
};

export default () => <Stage>
  <svg width={W} height={H} shapeRendering="crispEdges" style={{position: "absolute", left: 0, top: 0}}>
    {CARDS.map(({tag, ...c}, i) => <Card key={i} {...c} x={colX(i * 2)} seed={(i + 1) * 104729}/>)}
  </svg>

  {/* what was not read: the kit's dashed empty cell, the same mark as the S3 keyhole cell */}
  <DashBox x={colX(10) + 1} y={ABSTRACT} w={CW - 2} h={BOT - ABSTRACT - 1}/>

  {/* one line, full bleed: the only thing on the frame that crosses the margin */}
  <svg width={W} height={H} shapeRendering="crispEdges" style={{position: "absolute", left: 0, top: 0}}>
    <path d={`M0 ${BOT}H${STEP}V${ABSTRACT}H${W}`} fill="none" stroke={K.bone} strokeWidth={3}/>
  </svg>

  {/* An ink stamp, not an evidence plate: solid bone stays reserved for measured numbers (section 2.1) */}
  {/* Sized to the card, not to the words: PlateText is fixed at 26 px, so "original research" is 331.5 px and sets over two lines in 190 px of content */}
  <div style={{position: "absolute", left: colX(0) + 20, top: TOP + 58, width: CW - 40, boxSizing: "border-box", padding: "10px 16px", background: K.bg, border: `3px solid ${K.bone}`, transform: "rotate(-4deg)", textAlign: "center"}}>
    <PlateText>original research</PlateText>
  </div>

  <Foot x={colX(0)} y={BOT + 20} w={CW}>Ren et al. 2023<br/>Chemical Science</Foot>{/* the study the film follows, in bone, over the five DIM tags */}
  {CARDS.map(({tag}, i) => tag ? <Foot key={tag} x={colX(i * 2)} y={BOT + 20} w={CW} color={DIM}>{tag}</Foot> : null)}
  <Body x={colX(10)} y={BOT + 9} w={CW}>Perspective (abstract only)</Body>{/* y 9 shares a first baseline with the Foot tags */}
</Stage>;
