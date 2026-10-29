// s110 entry (S1 visual pass v2): 1-10, 1-11, W1 style frames. Public dir = 镜头设计_v3/styleframes/S1/v2/_code/s110/public
import React from "react";
import {registerRoot, Composition} from "remotion";
import {BoilProvider} from "../../core";
import {OPTIONS_110} from "./F110";
import {OPTIONS_111} from "./F111";
import {OPTIONS_W1} from "./FW1";

const wrap = (El, props) => () => <BoilProvider rate={2.5} frozen><El {...(props || {})}/></BoilProvider>;
const Root = () => <>
  {[...OPTIONS_110, ...OPTIONS_111, ...OPTIONS_W1].map(o =>
    <Composition key={o.id} id={o.id} component={wrap(o.C, o.p)} durationInFrames={1} fps={30} width={1920} height={1080}/>)}
</>;
registerRoot(Root);
