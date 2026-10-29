// s102 entry (S1 visual pass v2, beats 1-02 and 1-03). Own root; does not touch src/index.jsx.
import React from "react";
import {registerRoot, Still, Composition} from "remotion";
import {Opt1Tally, Opt1Fog, Opt2Liver, Opt3Year, Opt3Beads, Opt4Ikeda, Opt5Globe, Opt5Globe3D, Opt6Chain} from "./Frames102";
import {O1Capsules, O2Vessel, O2Beaker3D, O3Capsule3D, O4Words, OVitrine, CARD_DUR} from "./Frames103";

const S = {width: 1920, height: 1080};
const V = {durationInFrames: CARD_DUR, fps: 30, width: 1920, height: 1080};
const Root = () => <>
  <Still id="s102-tally" component={Opt1Tally} {...S}/>
  <Still id="s102-fog" component={Opt1Fog} {...S}/>
  <Still id="s102-fog2" component={Opt1Fog} defaultProps={{img: "fog2_full.png"}} {...S}/>
  <Still id="s102-liver2" component={Opt2Liver} defaultProps={{img: "liver_hero.png", xf: "translate(70px, 0px)", fade: 44, hero: true}} {...S}/>
  <Still id="s102-beads" component={Opt3Beads} {...S}/>
  <Still id="s102-liver" component={Opt2Liver} {...S}/>
  <Still id="s102-liver-world" component={Opt2Liver} defaultProps={{line: "world"}} {...S}/>
  <Still id="s102-year" component={Opt3Year} {...S}/>
  <Still id="s102-ikeda" component={Opt4Ikeda} {...S}/>
  <Still id="s102-ikeda-world" component={Opt4Ikeda} defaultProps={{focus: 2}} {...S}/>
  <Still id="s102-globe" component={Opt5Globe} {...S}/>
  <Still id="s102-globe3d" component={Opt5Globe3D} {...S}/>
  <Still id="s102-chain" component={Opt6Chain} {...S}/>
  <Composition id="s103-capsules" component={O1Capsules} {...V}/>
  <Composition id="s103-vessel" component={O2Vessel} {...V}/>
  <Composition id="s103-beaker3d" component={O2Beaker3D} {...V}/>
  <Composition id="s103-capsule3d" component={O3Capsule3D} {...V}/>
  <Composition id="s103-words" component={O4Words} {...V}/>
  <Composition id="s103-vitrine-beaker" component={OVitrine} defaultProps={{obj: "beaker"}} {...V}/>
  <Composition id="s103-vitrine-capsule" component={OVitrine} defaultProps={{obj: "capsule"}} {...V}/>
  <Composition id="s103-vitrine-row" component={OVitrine} defaultProps={{obj: "row"}} {...V}/>
</>;
registerRoot(Root);
