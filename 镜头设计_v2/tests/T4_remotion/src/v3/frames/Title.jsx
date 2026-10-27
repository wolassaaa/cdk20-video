// V3-Title: hand lettering + a hatched liver, with the computer's scan box locking onto the target.
import React from "react";
import {C, W, H, catmull} from "../core";
import {InkPath, Hatch, Scribble} from "../ink";
import {HandArrow, HandCircle, ScanBox, Highlight, HandUnderline, Ruler} from "../marks";
import {HandText, Mono} from "../type";
import {Stage, InkDefs, Halftone, radial, Dust} from "../texture";
import {Chrome} from "../chrome";

// liver silhouette (anterior view), normalised to width 1; right lobe on the viewer's left, left lobe tapering right
const LIVER_N = [[0.0, 0.30], [0.04, 0.14], [0.13, 0.05], [0.27, 0.01], [0.42, 0.02], [0.55, 0.05], [0.68, 0.09], [0.80, 0.15], [0.90, 0.22], [1.0, 0.30],
  [0.92, 0.335], [0.80, 0.365], [0.69, 0.40], [0.635, 0.425], [0.61, 0.47], [0.55, 0.475], [0.44, 0.52], [0.33, 0.58], [0.22, 0.63], [0.12, 0.62], [0.04, 0.52], [0.0, 0.41]];
export const liverPts = (x, y, w) => catmull(LIVER_N.map(([u, v]) => [x + u * w, y + v * w]), true, 8);

/** Hand-drawn liver: shaded hatching (cross-hatched toward the lower left), boiling ink outline, ligament line. */
export const Liver = ({x, y, w, progress = 1, hatch = 1, seed = 300}) => {
  const pts = liverPts(x, y, w);
  const P = (u, v) => [x + u * w, y + v * w];
  const lig = catmull([P(0.555, 0.055), P(0.575, 0.2), P(0.61, 0.34), P(0.625, 0.44)], false, 8);
  const shade = (px, py) => Math.min(1, Math.max(0, ((py - y) / w - 0.22) * 3.2 + (0.45 - (px - x) / w) * 1.6));
  return <g>
    <Hatch poly={pts} angle={-0.95} gap={13} size={2.6} color={C.verm} seed={seed} progress={hatch}/>
    <Hatch poly={pts} angle={0.55} gap={15} size={2.2} color={C.verm} seed={seed + 50} progress={hatch} keep={shade} opacity={0.9}/>
    <InkPath points={pts} seed={seed + 1} size={10} progress={progress} pressure="brush" thinning={0.55} jitter={2.2} ghost={0.25}/>
    <InkPath points={lig} seed={seed + 2} size={5} progress={progress} pressure="nib" jitter={1.5}/>
  </g>;
};

export const V3Title = () => {
  const lx = 1010, ly = 300, lw = 820;
  const tx = 1290, ty = 520; // tumour / target
  return <Stage>
    <svg width={W} height={H} style={{position: "absolute"}}>
      <InkDefs/>
      <Halftone bounds={[860, 120, 1060, 860]} field={radial(1380, 480, 560, 1.6)} cell={15} angle={0.5} color={C.verm} opacity={0.34}/>
      <g filter="url(#v3-ink)">
        <Liver x={lx} y={ly} w={lw}/>
        <Scribble poly={catmull([[tx - 58, ty - 30], [tx - 10, ty - 58], [tx + 52, ty - 40], [tx + 62, ty + 18], [tx + 18, ty + 52], [tx - 48, ty + 38]], true, 6)}
          angle={0.35} gap={10} size={8} color={C.verm} seed={77}/>
        <HandCircle cx={tx + 4} cy={ty} rx={108} ry={88} size={7} seed={23}/>
      </g>
      <ScanBox x={tx - 150} y={ty - 128} w={300} h={256} label="TARGET · CDK20" sub="kinase that drives liver cancer"/>
      <line x1={tx - 150} y1={ty} x2={tx - 178} y2={ty} stroke={C.cyan} strokeWidth={2}/>
      <line x1={tx + 150} y1={ty} x2={tx + 178} y2={ty} stroke={C.cyan} strokeWidth={2}/>

      {/* headline */}
      <Mono x={120} y={232} size={22} weight={700} color={C.cyan} letterSpacing={6}>AI × DRUG DISCOVERY</Mono>
      <HandText x={112} y={390} size={140} seed={2} split={5}>THE AI-MADE</HandText>
      <g filter="url(#v3-ink)"><Highlight x={78} y={466} w={650} h={250} seed={5}/></g>
      <HandText x={128} y={672} size={290} seed={3} color={C.bg} filter={false} wob={0.6}>KEY</HandText>
      <g filter="url(#v3-ink)">
        <HandArrow from={[720, 560]} to={[tx - 185, ty + 6]} bend={-0.2} size={8} head={34} seed={41}/>
      </g>
      <Mono x={122} y={800} size={28} color={C.ink}>How generative AI found</Mono>
      <Mono x={122} y={846} size={28} color={C.ink}>a CDK20 inhibitor for liver cancer</Mono>
      <Mono x={122} y={892} size={28} color={C.ink}>— first hit in 30 days.</Mono>
      <g filter="url(#v3-ink)">
        <HandUnderline x={290} y={908} w={290} size={6} color={C.verm} seed={33} kind="wave"/>
      </g>
      <Ruler x={1010} y={900} len={820} color={C.ink} opacity={0.35}/>
      <Mono x={1830} y={936} size={17} color={C.dim} anchor="end" letterSpacing={1}>8,918 designed → 54 picked → 7 made → 1 hit</Mono>
      <Dust/>
      <Chrome fig="00" counter={false}/>
    </svg>
  </Stage>;
};
