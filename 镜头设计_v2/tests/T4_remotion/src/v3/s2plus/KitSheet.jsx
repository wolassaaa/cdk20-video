// Review frame: every kit piece at once. It breaks the one-colour and three-settings rules on purpose; it is a sheet, not a still.
// Sample strings are verbatim from script_v3.3.md or section 2.3. Mono and sans fits are measured from the local TTFs, the serif line is not; check it all on the first render.
import React from "react";
import {Stage, Giant, Big, Voice, Body, PlateText, Foot, Plate, Barcode, SpecSheet, PersonPlaceholder, colX, colW} from "./kit";

const ROWS = [
  {label: "Kd", value: "566.7 ± 256.2 nM"},
  {label: "IC50", value: "33.4 ± 22.6 nM"},
  {label: "Huh7", value: "208.7 ± 3.3 nM"},
  {label: "HEK293", value: "1,706.7 ± 670.0 nM"},
  {label: "ADME · selectivity", empty: true, state: "on"},
];
const BARS = [
  {note: "splat · cut 302", cutAt: 302},
  {note: "blue", mode: "blue"},
  {note: "red · tail lit", mode: "red", highlight: [[303, 346]]},
];

export const KitSheet = () => <Stage>
  <Giant x={colX(0)} y={96} size={280}>13</Giant>
  <Big x={colX(0)} y={352} size={64}>later stage</Big>
  <Voice x={colX(0)} y={432} size={56}>a clue, not proof</Voice>
  <Body x={colX(0)} y={512}>millions → 13</Body>
  <PlateText x={colX(0)} y={576}>Objective 2 / Results</PlateText>
  <Foot x={colX(0)} y={628}>~8x = our calculation</Foot>

  <SpecSheet x={colX(3)} y={96} w={colW(4)} labelW={190} rows={ROWS} active={2} cell={{x: 0, y: 430, w: colW(4), h: 230, label: "measured structure?"}}/>

  <Plate x={colX(7)} y={96} kind="measured" fig="9A"/>
  <Plate x={colX(7)} y={168} kind="ai"/>
  <Plate x={colX(7)} y={240} kind="ai">AI GENERATED · Chemistry42</Plate>
  <Plate x={colX(7)} y={312} kind="ours"/>
  <Plate x={colX(7)} y={384} kind="illustrative"/>
  <PersonPlaceholder who="A" x={colX(7)} y={464} w={colW(5)} h={292}/>

  {BARS.map(({note, ...b}, i) => <React.Fragment key={note}>
    <Barcode x={colX(0)} y={800 + i * 66} width={1384} height={52} {...b}/>
    <Foot x={1560} y={814 + i * 66}>{note}</Foot>
  </React.Fragment>)}
</Stage>;
