// S1 v2 / 1-08 + 1-09 option stills (agent s108). Plates come from 镜头设计_v3/styleframes/S1/v2/_code/s108/public.
import React from "react";
import {registerRoot, Still} from "remotion";
import {RoadMetro, RoadGlass, RoadType, RoadVessel, RoadGates, RoadRecorder, StripFlat} from "./road";
import {RoadNeon, RoadType3D, RoadRecorder3D, Stair, FogTime, FogTally, Counter} from "./over3d";
import {LedgerTime, LedgerMoney, LedgerTen, DotYears, Vials, Growth} from "./cost";

const roads = {Metro: RoadMetro, Glass: RoadGlass, Type: RoadType, Vessel: RoadVessel, Gates: RoadGates, Recorder: RoadRecorder,
  Neon: RoadNeon, Type3D: RoadType3D, Recorder3D: RoadRecorder3D};
const S = p => <Still width={1920} height={1080} {...p}/>;
const Root = () => <>
  {Object.entries(roads).flatMap(([k, C]) => [
    <S key={k} id={`R-${k}`} component={C} defaultProps={{lit: 6}}/>,
    <S key={k + "4"} id={`R-${k}-lit4`} component={C} defaultProps={{lit: 4}}/>,
  ])}
  <Still id="StripFlat" component={StripFlat} width={5200} height={600} defaultProps={{lit: 6}}/>
  <Still id="StripFlat-lit4" component={StripFlat} width={5200} height={600} defaultProps={{lit: 4}}/>
  <S id="C-LedgerTime" component={LedgerTime}/>
  <S id="C-LedgerMoney" component={LedgerMoney}/>
  <S id="C-LedgerTen" component={LedgerTen}/>
  <S id="C-DotYears" component={DotYears}/>
  <S id="C-Vials" component={Vials}/>
  <S id="C-Growth" component={Growth}/>
  <S id="C-Stair" component={Stair}/>
  <S id="C-FogTime" component={FogTime}/>
  <S id="C-FogTally" component={FogTally}/>
  <S id="C-Counter" component={Counter}/>
</>;
registerRoot(Root);
