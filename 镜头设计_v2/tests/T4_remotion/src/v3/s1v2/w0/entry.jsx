// S1 v2 / W0+1-01 options: renders A's existing on-cam card alone on a transparent stage,
// so the Python style frames in 镜头设计_v3/styleframes/S1/v2/_code/w0 can composite their worlds around the real card.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, Sequence, staticFile} from "remotion";
import {BoilProvider} from "../../core";
import {OnCamCard} from "../../oncam/Card";

const CardOnly = ({grow = 1}) => <BoilProvider rate={2.5}>
  <AbsoluteFill style={{background: "transparent"}}>
    <Sequence from={0} durationInFrames={180}>
      <OnCamCard who="A" src={staticFile("placeholder_hand.mp4")} videoStart={40} dur={180}/>
    </Sequence>
  </AbsoluteFill>
</BoilProvider>;

const Root = () => <>
  <Composition id="W0-CardA" component={CardOnly} durationInFrames={180} fps={30} width={1920} height={1080}/>
</>;
registerRoot(Root);
