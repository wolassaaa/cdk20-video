// PULSE, 1,412 lights: type layer over the Blender frames. Palette and fonts as the rest of S1.
// Wall-label logic: quiet, no motion but a fade, set in the empty wedge under the left lobe.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate, Easing} from "remotion";
import {loadFont as loadGrot} from "@remotion/google-fonts/InterTight";
import {loadFont as loadSerif} from "@remotion/google-fonts/InstrumentSerif";
import {loadFont as loadMono} from "@remotion/google-fonts/MartianMono";

const GROT = loadGrot("normal", {weights: ["300", "400"], subsets: ["latin"]}).fontFamily;
const SERIF = loadSerif("normal", {weights: ["400"], subsets: ["latin"]}).fontFamily;
const MONO = loadMono("normal", {weights: ["400"], subsets: ["latin"]}).fontFamily;
const BONE = "#EDEBE4";
const W = 1920, H = 1080, FPS = 30;

const pad = n => String(n).padStart(4, "0");
const fade = (f, a, n = 18) => interpolate(f, [a, a + n], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.3, 0, 0.3, 1)});

const Source = ({children, op = 1, style}) => <div style={{fontFamily: MONO, fontSize: 15, letterSpacing: 0.6, color: BONE, opacity: 0.62 * op, ...style}}>{children}</div>;

// frames 240-: the number, then the rest of the line, then the source.
const Label = ({f}) => <div style={{position: "absolute", right: 96, bottom: 118, textAlign: "right", color: BONE}}>
  <div style={{display: "flex", alignItems: "baseline", justifyContent: "flex-end", gap: 22}}>
    <span style={{fontFamily: SERIF, fontSize: 132, lineHeight: 1, letterSpacing: 3, opacity: fade(f, 240), fontVariantNumeric: "lining-nums"}}>1,412</span>
    <span style={{fontFamily: GROT, fontWeight: 300, fontSize: 44, letterSpacing: 0.2, opacity: fade(f, 250)}}>deaths in Hong Kong, 2022</span>
  </div>
  <Source op={fade(f, 262)} style={{marginTop: 18}}>Hong Kong Cancer Registry, Hospital Authority</Source>
</div>;

const PulseTest = () => {
  const f = useCurrentFrame(), {fps} = useVideoConfig();
  return <AbsoluteFill style={{background: "#060606"}}>
    <Img src={staticFile(`frames/p_${pad(f)}.png`)} style={{position: "absolute", width: W, height: H}}/>
    <Label f={f * FPS / fps}/>
  </AbsoluteFill>;
};

// extra beat, 1-04: ten bulbs, three still lit
const PulseExtra = () => <AbsoluteFill style={{background: "#060606"}}>
  <Img src={staticFile("extra.png")} style={{position: "absolute", width: W, height: H}}/>
  <div style={{position: "absolute", left: 96, bottom: 96, color: BONE}}>
    <div style={{display: "flex", alignItems: "baseline", gap: 22}}>
      <span style={{fontFamily: GROT, fontWeight: 300, fontSize: 44}}>5-year relative survival</span>
      <span style={{fontFamily: SERIF, fontSize: 104, lineHeight: 1}}>~3 in 10</span>
      <span style={{fontFamily: GROT, fontWeight: 300, fontSize: 44}}>(HK, 2010-2021)</span>
    </div>
    <Source style={{marginTop: 16}}>Hong Kong Cancer Registry, Hospital Authority</Source>
  </div>
</AbsoluteFill>;

const Root = () => <>
  <Composition id="PulseTest" component={PulseTest} width={W} height={H} fps={FPS} durationInFrames={300}/>
  <Composition id="PulseTest60" component={PulseTest} width={W} height={H} fps={60} durationInFrames={600}/>
  <Composition id="PulseExtra" component={PulseExtra} width={W} height={H} fps={FPS} durationInFrames={1}/>
</>;
registerRoot(Root);
