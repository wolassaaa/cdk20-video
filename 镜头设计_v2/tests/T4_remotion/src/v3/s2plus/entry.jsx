// s2plus concept stills S01..S14 plus the KitSheet review frame: 1 frame each at 1920x1080, final 4K through --scale=2.
// Builders overwrite stills/sNN.jsx only, so this list stays fixed. Render commands: 镜头设计_v3/styleframes/S2plus/README.md.
import React from "react";
import {registerRoot, Composition} from "remotion";
import {W, H} from "./kit";
import {KitSheet} from "./KitSheet";
import S01 from "./stills/s01";
import S02 from "./stills/s02";
import S03 from "./stills/s03";
import S04 from "./stills/s04";
import S05 from "./stills/s05";
import S06 from "./stills/s06";
import S07 from "./stills/s07";
import S08 from "./stills/s08";
import S09 from "./stills/s09";
import S10 from "./stills/s10";
import S11 from "./stills/s11";
import S12 from "./stills/s12";
import S13 from "./stills/s13";
import S14 from "./stills/s14";

const COMPS = {S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13, S14, KitSheet};

const Root = () => <>
  {Object.entries(COMPS).map(([id, c]) => <Composition key={id} id={id} component={c} durationInFrames={1} fps={30} width={W} height={H}/>)}
</>;
registerRoot(Root);
