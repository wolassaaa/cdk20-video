// M04 · W2, second pass. CDK20 engraved: line width is light times real pLDDT, and below 70 the fill drops out so the tail is only broken rings.
// Behind it the barcode as a supergraphic: 346 real bars round a ring, bleeding off the top and bottom. Tail bars in bone sit at the same side as the tail.
// One readable label, as the script asks. The residue numbers and the letters are the barcode's own scale, not labels.
import React from "react";
import {Img, staticFile} from "remotion";
import {Stage, K, M} from "../kit";
import {FieldPlate, Micro, Reg, Cross, RingCode, RingLetters, RingTicks} from "../kit_m";

const CX = 1010, CY = 540, START = 54;

export default () => <Stage bg={K.blue}>
  <RingCode cx={CX} cy={CY} r0={488} len={290} start={START}/>
  <RingLetters cx={CX} cy={CY} r={470} start={START} size={8.5}/>
  <Img src={staticFile("cdk20_lines.png")} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080}}/>
  <RingTicks cx={CX} cy={CY} start={START}/>
  <Cross x={CX} y={CY - 470} s={18}/><Cross x={CX - 470} y={CY} s={18}/>
  <FieldPlate x={M} y={M}>AlphaFold DB v6 · predicted</FieldPlate>
  <Reg x={44} y={1000 - 4}/><Reg x={1836} y={44} flip/>
  <Micro x={M} y={940} size={14}>{"bars 001-302  mean pLDDT 91.5\nbars 303-346  mean pLDDT 47.2"}</Micro>
</Stage>;
