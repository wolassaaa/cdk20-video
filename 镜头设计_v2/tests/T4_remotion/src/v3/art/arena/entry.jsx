// HKBU SCIE1007 coursework science video. Arena direction: every line of on-screen type, as transparent layers that grade.py and scene.py pick up.
// Big Shoulders Display and Barlow Semi Condensed, both SIL OFL on Google Fonts.
import React from "react";
import {registerRoot, Composition} from "remotion";
import {loadFont as loadBig} from "@remotion/google-fonts/BigShoulders";
import {loadFont as loadBar} from "@remotion/google-fonts/BarlowSemiCondensed";
import {Layers} from "./layers.jsx";

loadBig("normal", {weights: ["700", "800", "900"], subsets: ["latin"]});
loadBar("normal", {weights: ["500", "600", "700"], subsets: ["latin"]});

const Root = () => <>
  {Object.entries(Layers).map(([id, {w, h, C}]) => <Composition key={id} id={id} component={C} width={w} height={h} durationInFrames={1} fps={30} />)}
</>;
registerRoot(Root);
