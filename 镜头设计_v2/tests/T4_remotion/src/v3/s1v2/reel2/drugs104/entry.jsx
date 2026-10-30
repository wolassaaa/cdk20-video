// test entry for drugs104 (1-04 v2). Bundle with --public-dir = 镜头设计_v3/styleframes/S1/v2/_code/reel/public
import React from "react";
import {registerRoot, Composition} from "remotion";
import {Beat104, DUR_104} from "./index";
const Root = () => <Composition id="Beat104" component={Beat104} durationInFrames={DUR_104} fps={30} width={1920} height={1080}/>;
registerRoot(Root);
