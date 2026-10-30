// Still 04 · W2: confidence is sharpness. Dots at pLDDT 70+ stay on the real ribbon in bone, lower ones scatter in blue; the 346 bars below are the same scores.
// The tail falls lower right, over its own bars at the end of the barcode. W2 is "one label only", so the pLDDT legend waits for 4-01.
// --props with {"mode": "blue"} renders the other answer to the director's item 2: all blue, confidence by sharpness alone.
import React from "react";
import {getInputProps} from "remotion";
import {Stage, Plate, Barcode, M} from "../kit";
import {ProteinPoints} from "./lib_protein";

export default () => {
  const {mode = "splat"} = getInputProps();
  return <Stage>
    <ProteinPoints mode={mode} tight={1.1}/>{/* 1.1 closes dense edges up to full bone, so the sure part is the brightest thing on the frame */}
    <Plate kind="ai" x={M} y={M}>AlphaFold DB v6 · predicted</Plate>
    <Barcode x={M} y={936} height={48} bar={2} mode={mode}/>{/* a data strip under the protein, bottom on the 984 margin */}
  </Stage>;
};
