// Render v3: npx remotion render src/v3/mascots/entry.jsx MascotShow3 <frames dir> --sequence --gl=angle --concurrency=2 --public-dir=D:/cdk20_work/mascots/pub
import React from "react";
import {registerRoot, Composition} from "remotion";
import {MascotShow2, TOTAL2, FPS} from "./Show2";
import {MascotShow3, TOTAL3} from "./Show3";

// v1 (SVG characters, edge-tts) lives in Show.jsx / Stage.jsx / Character.jsx (11_AI角色插段_v1.mp4).
// v2 (one fixed three-shot, three.js stage) is Show2.jsx / Stage2.jsx (11_AI角色插段_v2.mp4). v3 = shot-based drama staging.
const Root = () => (
  <>
    <Composition id="MascotShow3" component={MascotShow3} durationInFrames={TOTAL3} fps={FPS} width={1920} height={1080} />
    <Composition id="MascotShow2" component={MascotShow2} durationInFrames={TOTAL2} fps={FPS} width={1920} height={1080} />
  </>
);
registerRoot(Root);
