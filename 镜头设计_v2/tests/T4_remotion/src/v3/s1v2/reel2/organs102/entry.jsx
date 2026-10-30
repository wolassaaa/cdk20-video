// test entry for organs102 (1-02 v2). Bundle with --public-dir = 镜头设计_v3/styleframes/S1/v2/_code/reel/public
import React from "react";
import {registerRoot, Composition, AbsoluteFill} from "remotion";
import {BoilProvider} from "../../../core";
import {Beat102, DUR_102} from "./index";
const B = () => <BoilProvider rate={2.5}><AbsoluteFill style={{background: "#000"}}><Beat102/></AbsoluteFill></BoilProvider>;
const Root = () => <Composition id="Beat102" component={B} durationInFrames={DUR_102} fps={30} width={1920} height={1080}/>;
registerRoot(Root);
