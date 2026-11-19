// Render: npx remotion render src/v3/mascots/entry.jsx MascotShow out.mp4 --gl=angle --concurrency=2
import React from "react";
import {registerRoot, Composition} from "remotion";
import {MascotShow, WinkLoop, TOTAL_FRAMES, WINK_FRAMES, FPS} from "./Show";

const Root = () => (
  <>
    <Composition id="MascotShow" component={MascotShow} durationInFrames={TOTAL_FRAMES} fps={FPS} width={1920} height={1080} />
    {["Claude", "GPT", "DeepSeek"].map((w) => (
      <Composition key={w} id={`Wink-${w}`} component={WinkLoop} defaultProps={{who: w}} durationInFrames={WINK_FRAMES} fps={FPS} width={1920} height={1080} />
    ))}
  </>
);
registerRoot(Root);
