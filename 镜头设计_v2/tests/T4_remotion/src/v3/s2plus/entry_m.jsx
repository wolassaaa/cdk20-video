// HKBU SCIE1007 coursework science video. Second-pass stills M03, M04, M06, M09 beside the first pass, so both stay renderable for a before and after.
import React from "react";
import {registerRoot, Composition} from "remotion";
import {W, H} from "./kit";
import M03 from "./stills_m/m03";
import M04 from "./stills_m/m04";
import M06, {Mask} from "./stills_m/m06";
import M09 from "./stills_m/m09";

const COMPS = {M03, M04, M06, M06mask: Mask, M09};
const Root = () => <>
  {Object.entries(COMPS).map(([id, c]) => <Composition key={id} id={id} component={c} durationInFrames={1} fps={30} width={W} height={H}/>)}
</>;
registerRoot(Root);
