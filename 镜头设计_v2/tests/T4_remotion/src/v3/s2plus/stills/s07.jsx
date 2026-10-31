// Still 07 · 5-01 · the first flip. Seven first-round compounds, plates already bone (measured), 001 the only one that held.
// Screen text verbatim from marathon_refs_20261031.md section 4 still 7 and script_v3.3.md 5-01:
// "Objective 2 / Results", "Kd: lower = tighter", "001: 9.2 µM", "> 30 µM". The Kd labels ARE the seven flipped plates (section 3 S5).
// Structures come from data/fig5_seven.json (code/make_fig5.py). Only 001 is drawable: Ren 2023 prints the other six
// as the Fig. 5 bitmap only, so they render as pending slots rather than guessed structures (section 5 rule 5).
import React from "react";
import {Stage, Body, Foot, Plate, Tag, DashBox, SANS, K, DIM, FAINT, M, W, H} from "../kit";
import {Mol} from "./lib_s5";
import FIG5 from "../data/fig5_seven.json";

// Seven cells across the 12 columns; 001 takes the wide one so its longer plate fits and it reads as the standout.
// 280 + 6*217 + 6*24 = 1726 px, leaving 96 left and 98 right of the 1920 frame.
const LEAD = 280, CELL = 217, GAP = 24;
const cellX = i => M + (i === 0 ? 0 : LEAD + GAP + (i - 1) * (CELL + GAP));
const cellW = i => (i === 0 ? LEAD : CELL);
const ROW_Y = 300, ROW_H = 280, PLATE_Y = 624;

export default () => <Stage>
  <Tag x={M} y={M}>Objective 2 / Results</Tag>
  {/* right-anchored so the plate's own width sets its edge; no width arithmetic to drift */}
  <div style={{position: "absolute", right: M, top: M}}><Plate kind="measured" fig="5"/></div>

  <svg width={W} height={H} style={{position: "absolute", inset: 0, fontFamily: SANS}}>
    {FIG5.compounds.map((c, i) => c.sourced
      ? <Mol key={c.id} mol={c} x={cellX(i)} y={ROW_Y} w={cellW(i)} h={ROW_H} color={K.bone}/>
      : null)}
  </svg>

  {FIG5.compounds.map((c, i) => c.sourced ? null :
    <DashBox key={c.id} x={cellX(i)} y={ROW_Y} w={cellW(i)} h={ROW_H} color={FAINT} weight={2}/>)}

  {/* all seven stay solid, so all seven read as measured; only 001 is full bone (section 4). Black text on DIM is about 5.4:1 */}
  {FIG5.compounds.map((c, i) =>
    <Plate key={c.id} kind="measured" x={cellX(i)} y={PLATE_Y} style={c.sourced ? null : {background: DIM}}>{c.kd}</Plate>)}

  <Body x={M} y={702}>Kd: lower = tighter</Body>{/* the key to the row, so it sits directly under it */}
  <Body x={M} y={750}>Six barely held on. 001 stood out.</Body>{/* plain-language line, script 5-02 verbatim; "barely held on" is not "did not hold" */}
  {/* placeholder marker, same class as the kit's PersonPlaceholder tag: delete it once the six structures are drawn */}
  {FIG5.unsourced.length
    ? <Foot x={M} y={936} color={DIM}>PLACEHOLDER · {FIG5.unsourced.length} structures pending Fig. 5</Foot>
    : null}
</Stage>;
