// HKBU SCIE1007 课程作业的科普视频：6-10，048 走到 Cells（简版无托盘）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-10.json";
import {Lens, guidePlan} from "../manual/kit.jsx";
import {Stage, Sprite, Source, evMapB} from "./bkit.jsx";
import {X,Y,start,end610,TagBody,RoadWorld,Status,pathAt,pos,tween,hit,clamp} from "./x3Road.jsx";

const ZONE = 6;
const E=evMapB(K);
const GP=guidePlan(K);
const delayed=(e,n)=>({s:e.s+n,l:e.l,e:e.e});
const Scene=()=>{
  const f=useCurrentFrame();
  const [cx,zoom]=pathAt(f,[460,1.08],[
    [E.cam_road,[701,.88]],
    [delayed(E.slide1,6),[540,1.09]],
    [delayed(E.slide2,6),[650,1.09]],
    [delayed(E.slide3,6),[875,1.09]],
    [delayed(E.slide4,6),[1110,1.09]],
    [E.cam_ahead,end610],
  ]);
  const tag=pathAt(f,[start],[[E.slide1,[X[0]]],[E.slide2,[X[1]]],[E.slide3,[X[2]]],[E.slide4,[X[3]]]])[0];
  const drop=pos(f,E.tag_drop);
  const swing=(f>=E.tag_drop.l? Math.sin((f-E.tag_drop.l)*.40)*12*Math.exp(-(f-E.tag_drop.l)/19):0)+Math.sin(f*.16)*1.7;
  const dish=clamp((f-E.dish.s)/12);
  return <Lens plan={GP} f={f}>
    <Stage zone={ZONE} f={f} tray={false}>
      <div style={{position:"absolute",inset:0,background:"rgba(244,241,234,.20)"}}/>
      <RoadWorld cx={cx+5.6*Math.sin(f*.15)} zoom={zoom}
        ticks={{0:hit(f,E.tick1),1:hit(f,E.tick2),3:hit(f,E.tick4)}}>
        <Status started={hit(f,E.started)} n1={hit(f,E.notyet)} n2={clamp((f-E.notyet.l-5)/6)}/>
        {dish>0 && <Sprite name="dish/34" x={X[3]+142} y={Y+57+3*Math.sin(f*.22)} w={108} op={dish}/>}
        {drop>0 && <TagBody x={tag} y={Y+18-390*(1-drop)} text="048" rot={swing} id="gold048"/>}
      </RoadWorld>
      <Source>Illustration · status of 048: Ren et al., Chem. Sci. 2023</Source>
    </Stage>
  </Lens>;
};
const Root=()=> <Composition id="B610" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080}/>;
registerRoot(Root);
