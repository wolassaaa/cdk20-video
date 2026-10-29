// s104 entry (S1 visual pass v2): 1-04 five options x 3 frames, 1-05..1-07 four layouts x 3 frames.
// Stills: O{n}{a|b|c} at frame 0; L{n}{D|B|C} at frame 40 (card grown, timeline drawn).
import React from "react";
import {registerRoot, Composition} from "remotion";
import {BoilProvider} from "../../core";
import {OPTIONS_104} from "./S104";
import {LAYOUTS} from "./Talk";
import {Mask} from "./Masks";

const wrap = (El, props) => () => <BoilProvider rate={2.5} frozen><El {...props}/></BoilProvider>;
const Root = () => <>
  {OPTIONS_104.flatMap(o => ["a", "b", "c"].map(p =>
    <Composition key={o.id + p} id={o.id + p} component={wrap(o.C, {part: p})} durationInFrames={60} fps={30} width={1920} height={1080}/>))}
  {LAYOUTS.flatMap(o => ["D", "B", "C"].map(w =>
    <Composition key={o.id + w} id={o.id + w} component={wrap(o.C, {who: w})} durationInFrames={60} fps={30} width={1920} height={1080}/>))}
  {[["O4", "a"], ["O4", "b"], ["O4", "c"], ["O2", "a"]].map(([o, p]) => <Composition key={o + p + "2"} id={o + p + "2"}
    component={wrap(OPTIONS_104.find(x => x.id === o).C, {part: p, v: 2})} durationInFrames={60} fps={30} width={1920} height={1080}/>)}
  {["a", "b", "c"].map(p => <Composition key={"M" + p} id={"Mask" + p} component={wrap(Mask, {part: p})} durationInFrames={1} fps={30} width={1920} height={1080}/>)}
</>;
registerRoot(Root);
