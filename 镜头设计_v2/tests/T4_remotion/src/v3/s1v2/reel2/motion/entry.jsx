// test entry for reel2/motion (not the reel): each beat on its own, plus W0+1-01 back to back.
import React from "react";
import {registerRoot, Composition, Sequence, AbsoluteFill} from "remotion";
import {BoilProvider} from "../../../core";
import {BeatW0, Beat101Bg, DUR_W0, DUR_101, Beat108, DUR_108, Beat109, DUR_109} from "./index";

const B = ({children}) => <BoilProvider rate={2.5}><AbsoluteFill style={{background: "#000"}}>{children}</AbsoluteFill></BoilProvider>;
const Open = () => <B><Sequence durationInFrames={DUR_W0}><BeatW0/></Sequence><Sequence from={DUR_W0} durationInFrames={DUR_101}><Beat101Bg/></Sequence></B>;
const c = (id, C, d) => <Composition key={id} id={id} component={() => <B><C/></B>} durationInFrames={d} fps={30} width={1920} height={1080}/>;
const Root = () => <>
  <Composition id="MOpen" component={Open} durationInFrames={DUR_W0 + DUR_101} fps={30} width={1920} height={1080}/>
  {c("MW0", BeatW0, DUR_W0)}
  {c("M101", Beat101Bg, DUR_101)}
  {c("M108", Beat108, DUR_108)}
  {c("M109", Beat109, DUR_109)}
</>;
registerRoot(Root);
