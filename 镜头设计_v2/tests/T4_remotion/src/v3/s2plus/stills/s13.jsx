// Still 13 · 7-03: what is still unfilled. Everything measured for 048 reads dim; only the empty cells are lit. Values as on screen in 5-08 and 5-10 (E18, E20, E21).
// S3's big cell comes back with still 4's model in it. The ghost is a plain dashed blob clear of every dot, so it hints at no result; the blue plate keeps the bone model from reading as measured (2.1).
// The MEASURED plate is what keeps the sheet from reading as predicted too. No figure number: the values come from several figures. Its fill is DIM, like everything measured here.
import React from "react";
import {Stage, SpecSheet, Body, Plate, DIM, M, GUT, colW} from "../kit";
import {ProteinPoints, Ghost} from "./lib_protein";

const ROWS = [
  {value: "048", state: "on"},
  {label: "Kd", value: "566.7 ± 256.2 nM", state: "read"},
  {label: "Enzyme IC50", value: "33.4 ± 22.6 nM", state: "read"},
  {label: "Huh7", value: "208.7 ± 3.3 nM", state: "read"},
  {label: "HEK293", value: "1,706.7 ± 670.0 nM", state: "read"},
  {label: "ADME · selectivity", empty: true, state: "on"},
];
const FIT = {scale: 0.74, x: 372, y: 178};  // still 4's frame placed inside the cell, with room for the ghost: its line spans x 913-1736, y 211-829

export default () => <Stage>
  <SpecSheet x={M} y={M} rowsW={colW(5)} rows={ROWS} cell={{h: 888, children: <Body x={24} y={760}>measured structure?</Body>}}/>{/* Body, not Voice: Voice would be a fourth setting on this frame */}
  <Plate kind="measured" x={M} y={592} style={{background: DIM}}/>
  <ProteinPoints {...FIT} tight={1.0} loose={1.5}/>
  <Ghost {...FIT}/>
  <Plate kind="ai" x={M + colW(5) + GUT + 24} y={M + 24}>AlphaFold DB v6 · predicted</Plate>
</Stage>;
