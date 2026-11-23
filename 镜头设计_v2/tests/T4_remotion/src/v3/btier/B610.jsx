// HKBU SCIE1007 课程作业的科普视频：6-10，048 走到 Cells（简版无托盘）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-10.json";
import {Lens, guidePlan} from "../manual/kit.jsx";
import {Stage, Sprite, Source, evMapB} from "./bkit.jsx";
import {X,Y,start,end610,ZS,ZF,TagBody,RoadWorld,Status,pathAt,pos,tween,hit,clamp} from "./x3Road.jsx";

const ZONE = 6;
const E=evMapB(K);
const GP=guidePlan(K);
const delayed=(e,n)=>({s:e.s+n,l:e.l,e:e.e});
const Scene=()=>{
  const f=useCurrentFrame();
  // 审查批 1（11-23）：容器缩放 ×1.8 跟着吊牌走（ZS = 2.0：站牌 226 → 452 px ≥ 430，吊牌 132 → 264 px ≥ 260），每站停下时该站站牌在横向正中；
  // 只有 cam_road、cam_ahead 拉回 ZF = 1.2 看路（cam_ahead 之后一直留在 1.2，6-11 从 end610 接着走）。
  // 开头"where's 048"：先贴近吊牌（×3.0，吊牌屏上高 ≥ 240，长路页 G3），cam_road 再拉回。第三个数是路在屏上的 y。
  const [cx,zoom,ry]=pathAt(f,[60,3.0,480],[
    [E.cam_road,[701,ZF,600]],
    [delayed(E.slide1,6),[X[0],ZS,600]],
    [delayed(E.slide2,6),[X[1],ZS,600]],
    [delayed(E.slide3,6),[X[2],ZS,600]],
    [delayed(E.slide4,6),[X[3],ZS,600]],
    [E.cam_ahead,[...end610,600]],
  ]);
  const tag=pathAt(f,[start],[[E.slide1,[X[0]]],[E.slide2,[X[1]]],[E.slide3,[X[2]]],[E.slide4,[X[3]]]])[0];
  const drop=pos(f,E.tag_drop);
  const swing=(f>=E.tag_drop.l? Math.sin((f-E.tag_drop.l)*.40)*12*Math.exp(-(f-E.tag_drop.l)/19):0)+Math.sin(f*.16)*1.7;
  const dish=clamp((f-E.dish.s)/12);
  return <Lens plan={GP} f={f}>
    <Stage zone={ZONE} f={f} tray={false}>
      <RoadWorld cx={cx+5.6*Math.sin(f*.15)} zoom={zoom} y={ry}
        ticks={{0:hit(f,E.tick1),1:hit(f,E.tick2),3:hit(f,E.tick4)}}>
        <Status started={hit(f,E.started)} n1={hit(f,E.notyet)} n2={clamp((f-E.notyet.l-5)/6)}/>
        {drop>0 && <TagBody x={tag} y={Y+18-390*(1-drop)} text="048" rot={swing} id="gold048"/>}
      </RoadWorld>
      <Source>Illustration · status of 048: Ren et al., Chem. Sci. 2023</Source>
    </Stage>
  </Lens>;
};
const Root=()=> <Composition id="B610" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080}/>;
registerRoot(Root);
