// Render v2: npx remotion render src/v3/mascots/entry.jsx MascotShow2 <out> --gl=angle --concurrency=2 --public-dir=D:/cdk20_work/mascots/pub
import React from "react";
import {registerRoot, Composition} from "remotion";
import {MascotShow2, TOTAL2, FPS} from "./Show2";

// v1 (SVG characters, edge-tts) lives in Show.jsx / Stage.jsx / Character.jsx, kept for reference (11_AI角色插段_v1.mp4).
const Root = () => (
  <>
    <Composition id="MascotShow2" component={MascotShow2} durationInFrames={TOTAL2} fps={FPS} width={1920} height={1080} />
  </>
);
registerRoot(Root);
