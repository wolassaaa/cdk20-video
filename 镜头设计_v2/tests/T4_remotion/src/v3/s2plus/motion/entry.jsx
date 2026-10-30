// s2plus motion tests. W2 and W3 run on seconds, so W2M60 and W3M60 are the same film at 60 fps.
import React from "react";
import {registerRoot, Composition} from "remotion";
import {W, H} from "../kit";
import W2 from "./w2";
import W3 from "./w3";

const COMPS = [["W2M", W2, 10], ["W3M", W3, 8]];

const Root = () => <>
  {COMPS.flatMap(([id, c, s]) => [30, 60].map(fps => <Composition key={id + fps} id={fps === 30 ? id : id + fps} component={c} durationInFrames={s * fps} fps={fps} width={W} height={H}/>))}
</>;
registerRoot(Root);
