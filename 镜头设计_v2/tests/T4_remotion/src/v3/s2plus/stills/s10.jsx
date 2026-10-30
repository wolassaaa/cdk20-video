// Still 10 · 5-10 · two dishes of lights. The cell test: same compound, two cell lines, very different concentrations.
// Screen text verbatim from marathon_refs_20261031.md section 4 still 10 and script_v3.3.md 5-10:
// "Huh7 208.7 ± 3.3 nM vs HEK293 1,706.7 ± 670.0 nM" (set across the two panels, in order), "~8x = our calculation",
// "HEK293 is not normal liver tissue", "schematic". Values are E21 / Fig. 9B; ~8x is 1706.7 / 208.7 = 8.18 (flag F5, ours).
// Both dishes are HALF lit, and that is the science: IC50 is the half-signal point, so both cell lines reach it.
// What differs is the concentration it took, which is the bar under each dish, on still 8's nM scale (the script's 5-10 asks for bars).
// Never draw one dish emptier than the other — that would claim a difference in effect rather than in potency.
import React from "react";
import {Stage, Big, PlateText, Foot, Plate, K, DIM, W, M, colX} from "../kit";
import {Dish, DISH_N, NmBar, halfLit} from "./lib_s5";

const CY = 360, R = 190, BAR_Y = 806, BAR_H = 24;
// Dish, name, value and bar share one left edge, because the bars start from zero. Columns 1 and 7 leave the longest whisker inside the margin.
const CELLS = [
  {name: "Huh7", value: "208.7 ± 3.3 nM", nm: 208.7, sd: 3.3, x: colX(1), seed: 1, bar: K.bone},
  {name: "HEK293", value: "1,706.7 ± 670.0 nM", nm: 1706.7, sd: 670.0, x: colX(7), seed: 2, bar: DIM},  // needing more is worse here, so the long bar is the dim one, as on still 8
];
const MID = (colX(1) + 2 * R + colX(7)) / 2;  // halfway across the gap between the dishes

export default () => <Stage>
  <div style={{position: "absolute", right: M, top: 906}}><Plate kind="measured" fig="9B"/></div>

  <svg width={W} height={BAR_Y + BAR_H + 20} style={{position: "absolute", left: 0, top: 0}}>
    {CELLS.map(c => <Dish key={c.name} cx={c.x + R} cy={CY} r={R} lit={halfLit(DISH_N, c.seed)} on={K.red}/>)}
    <g shapeRendering="crispEdges">{CELLS.map(c => <NmBar key={c.name} x={c.x} y={BAR_Y} h={BAR_H} value={c.nm} sd={c.sd} color={c.bar}/>)}</g>
  </svg>

  {/* the dishes are the only illustrative thing on the frame, so the plate sits between them, not in a corner */}
  <div style={{position: "absolute", left: MID - 150, top: CY - 27, width: 300, display: "flex", justifyContent: "center"}}>
    <Plate kind="illustrative">schematic</Plate>
  </div>

  {/* emitted left to right with "vs" in the gap, so the markup order is the reading order of the frame */}
  {CELLS.map((c, i) => <React.Fragment key={c.name}>
    {i ? <Big x={MID - 50} y={726} w={100} size={64} color={DIM} style={{textAlign: "center"}}>vs</Big> : null}
    <PlateText x={c.x} y={690}>{c.name}</PlateText>
    <Big x={c.x} y={726} size={64} style={{whiteSpace: "nowrap"}}>{c.value}</Big>
  </React.Fragment>)}

  {/* section 3 S5: neither footnote may be shrunk, so both stay full bone at the Foot setting, not dimmed */}
  <Foot x={M} y={890} color={K.bone}>~8x = our calculation</Foot>
  <Foot x={M} y={926} color={K.bone}>HEK293 is not normal liver tissue</Foot>
</Stage>;
