// Still 05 · 4-05: the cut. Left half black (S4's one colour field is W3), ribbon 1-302, barcode broken after 302; right half is B.
// The ribbon plate comes from bl_ribbon302.py. Until it has run, the stipple stands in and says so on screen.
import React from "react";
import {Img, staticFile} from "remotion";
import {Stage, Plate, PlateText, Foot, Barcode, PersonPlaceholder, M, W, H} from "../kit";
import {ProteinPoints, useStaticFile} from "./lib_protein";

const RIBBON = "ribbon302.png";  // 1920x2160: the left half at --scale=2

export default () => {
  const ribbon = useStaticFile(RIBBON);
  return <Stage>
    {ribbon ? <Img src={staticFile(RIBBON)} style={{position: "absolute", left: 0, top: 0, width: W / 2, height: H}}/> : null}
    {ribbon === false ? <>
      <ProteinPoints last={302} scale={0.85} x={-528} y={117}/>
      <Foot x={M} y={768}>FALLBACK · {RIBBON} not rendered yet</Foot>
    </> : null}
    <PersonPlaceholder who="B" side="right" lean={-120} eye/>
    <PlateText x={M} y={M} style={{whiteSpace: "nowrap"}}>Objective 1 / Tool: structure prediction</PlateText>
    <Plate kind="ai" x={M} y={822}>AlphaFold DB v6 · predicted</Plate>
    {/* kept bars end at x 851, the tail lands flat on B's half at x 984: the frame's own divider is the cut, and B's scissors have to meet it */}
    <Barcode x={M} y={900} width={864} height={84} cutAt={302} gap={133}/>
  </Stage>;
};
