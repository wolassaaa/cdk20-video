// HKBU SCIE1007 coursework science video. Art direction "darkroom": renders each on-screen string as a transparent ink layer, which the Blender papers then print.
import React from "react";
import {registerRoot, Composition} from "remotion";
import {loadFont as loadSerif} from "@remotion/google-fonts/Fraunces";
import {loadFont as loadMono} from "@remotion/google-fonts/CourierPrime";
import {loadFont as loadHand} from "@remotion/google-fonts/Caveat";

const SERIF = loadSerif("normal", {weights: ["400", "600", "800"], subsets: ["latin"]}).fontFamily;
const MONO = loadMono("normal", {weights: ["400", "700"], subsets: ["latin"]}).fontFamily;
const HAND = loadHand("normal", {weights: ["600", "700"], subsets: ["latin"]}).fontFamily;

const S = [
  ["t1-num", "1,412", SERIF, 800, 420],
  ["t1-rest", "deaths in Hong Kong, 2022", SERIF, 600, 170],
  ["t2-q", "How can computer-aided methods help scientists find and assess potential cancer drug candidates?", SERIF, 600, 190, 2300],
  ["t3-tag", "schematic", HAND, 700, 200],
  ["t4-tag", "AlphaFold DB v6 · predicted", MONO, 700, 170],
  ["t5-a", "Enzyme IC50", MONO, 700, 170],
  ["t5-n", "048 = 33.4 ± 22.6 nM", SERIF, 800, 330],
  ["t5-b", "Just this much cuts the enzyme's activity in half.", SERIF, 600, 170, 2500],
  ["t5-c", "MEASURED · Ren 2023, Fig. 9A", MONO, 700, 170],
  ["t5-d", "OUR RE-DOCKING", HAND, 700, 260],
  ["t6-1", "Target", SERIF, 600, 200],
  ["t6-2", "Hit", SERIF, 600, 200],
  ["t6-3", "Improve", SERIF, 600, 200],
  ["t6-4", "Cells & animals", SERIF, 600, 200, 800],
  ["t6-5", "Clinical trials 1-2-3", SERIF, 600, 200, 1100],
  ["t6-6", "Approval", SERIF, 600, 200],
  ["t6-048", "048", MONO, 700, 240],
  ["t6-nr", "not reported", HAND, 700, 190],
  ...["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"].map((n) => ["cs-" + n, n, MONO, 700, 200]),
  ...["2:21", "2:22", "2:09", "3:33", "2:19", "2:31", "0:49", "1:39"].map((n, i) => ["cs-t" + (i + 1), n, MONO, 400, 170]),
];

const Ink = ({text, font, weight, size, width}) => (
  <div style={{position: "absolute", left: 40, top: 40, width: width || undefined, whiteSpace: width ? "normal" : "nowrap", fontFamily: font, fontWeight: weight, fontSize: size, lineHeight: 1.12, color: "#000", fontVariationSettings: font === SERIF ? '"opsz" 144, "SOFT" 0, "WONK" 0' : undefined}}>{text}</div>
);

const Root = () => (
  <>
    {S.map(([id, text, font, weight, size, width]) => (
      <Composition key={id} id={id} component={Ink} width={4400} height={width ? 1500 : 560} fps={30} durationInFrames={1} defaultProps={{text, font, weight, size, width}} />
    ))}
  </>
);
registerRoot(Root);
