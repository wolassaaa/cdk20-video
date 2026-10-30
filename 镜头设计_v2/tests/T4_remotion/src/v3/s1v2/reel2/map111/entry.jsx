// test entry for map111 (1-11 v2). Bundle with --public-dir = 镜头设计_v3/styleframes/S1/v2/_code/reel/public
import React from "react";
import {registerRoot, Composition} from "remotion";
import {Beat111, DUR_111} from "./index";
const Root = () => <Composition id="Beat111" component={Beat111} durationInFrames={DUR_111} fps={30} width={1920} height={1080}/>;
registerRoot(Root);
