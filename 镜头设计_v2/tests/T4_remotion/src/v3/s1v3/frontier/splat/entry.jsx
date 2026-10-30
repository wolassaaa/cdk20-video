// SPLAT frontier test (S1 1-01 -> 1-02): type layers only, rendered as transparent stills and
// composited over the Cycles splat frames in numpy (镜头设计_v3/styleframes/S1/v3_frontier/splat/code/post.py).
// "num" is also the mask the splat digits condense into, so the crisp type and the splats share one geometry.
import React from "react";
import {registerRoot, Composition, AbsoluteFill} from "remotion";
import {loadFont as loadGrot} from "@remotion/google-fonts/InterTight";
import {loadFont as loadSerif} from "@remotion/google-fonts/InstrumentSerif";
import {loadFont as loadMono} from "@remotion/google-fonts/MartianMono";

const GROT = loadGrot("normal", {weights: ["200", "300", "400"], subsets: ["latin"]}).fontFamily;
const SERIF = loadSerif("italic", {weights: ["400"], subsets: ["latin"]}).fontFamily;
const MONO = loadMono("normal", {weights: ["300", "400"], subsets: ["latin"]}).fontFamily;
const BONE = "#EDEBE4", RED = "#E8190F";
const W = 1920, H = 1080;

const T = ({x, y, size, weight = 300, font = GROT, ls = 0, color = BONE, opacity = 1, children, anchor = "start"}) =>
  <text x={x} y={y} fontFamily={font} fontSize={size} fontWeight={weight} letterSpacing={ls} fill={color} opacity={opacity}
    textAnchor={anchor} style={{fontVariantNumeric: "tabular-nums", fontFeatureSettings: '"tnum" 1'}}>{children}</text>;

const Layer = ({which}) => <AbsoluteFill style={{background: "transparent"}}>
  <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
    {which === "num" && <T x={96} y={566} size={262} weight={200} ls={-9}>1,412</T>}
    {which === "sub" && <g>
      <T x={108} y={664} size={44} weight={300}>deaths in Hong Kong, 2022</T>
      <rect x={110} y={696} width={64} height={3} fill={RED}/>
    </g>}
    {which === "src" && <g>
      <T x={80} y={1036} size={14} weight={300} font={MONO} ls={0.8} opacity={0.62}>Hong Kong Cancer Registry, Hospital Authority</T>
      <T x={1840} y={1036} size={13} weight={300} font={MONO} ls={0.8} opacity={0.42} anchor="end">BodyParts3D © DBCLS, CC BY 4.0 · 3D Gaussian splats</T>
    </g>}
    {which === "extra" && <g>
      <T x={80} y={910} size={15} weight={300} font={MONO} ls={2.5} opacity={0.72}>AlphaFold DB v6 · predicted</T>
      <T x={78} y={972} size={46} weight={300}>Nobel Prize in Chemistry 2024</T>
      <T x={1840} y={1036} size={13} weight={300} font={MONO} ls={0.8} opacity={0.42} anchor="end">CDK20 · AF-Q8IZL9-F1 · CC BY 4.0 · confidence = coherence</T>
    </g>}
  </svg>
</AbsoluteFill>;

const Root = () => <>
  {["num", "sub", "src", "extra"].map(k =>
    <Composition key={k} id={`splat-${k}`} component={Layer} defaultProps={{which: k}} width={W} height={H} fps={30} durationInFrames={1}/>)}
</>;
registerRoot(Root);
