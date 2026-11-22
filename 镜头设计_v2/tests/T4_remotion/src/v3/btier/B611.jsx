// HKBU SCIE1007 课程作业的科普视频：6-11，从 6-10 末机位接到长路终点，再回到 048。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-11.json";
import Previous from "./keys_6-10.json";
import {Lens, guidePlan} from "../manual/kit.jsx";
import {C, Stage, Sprite, Slab, Engrave, Plate, Gate, Source, evMapB} from "./bkit.jsx";
import {X,Y,start,end610,TagBody,RoadWorld,Status,pathAt,pos,run,hit,clamp,tween,mix,glow} from "./x3Road.jsx";

const ZONE = 6;
const E=evMapB(K);
const GP=guidePlan(K);
const Scene=()=>{
  const f=useCurrentFrame(), continuous=f+Previous.len_f-1;
  const [cx,z]=pathAt(f,end610,[[E.cam_end,[1820,1.07]],[E.cam_back,[X[3],1.08]]]);
  const dive=pos(f,E.dive);
  const nudge=run(f,E.nudge);
  const blueX=mix(mix(start,X[5]-70,run(f,E.tagB_run)),X[6],pos(f,E.tagB_arrive));
  const blueOn=clamp((f-E.tagB_run.s)/10);
  const fail=run(f,E.tagC_fail);
  const otherX=mix(start,X[4]+125,run(f,E.tagC_run));
  const otherOn=clamp((f-E.tagC_run.s)/8);
  const dates=hit(f,E.date);
  const share=run(f,E.share);
  const people=hit(f,E.people);
  const gate=hit(f,E.gate);
  const labelLines=[
    ["lirafugratinib",E.label_lira],["approved in the US, Sep 2026",E.label_us],["for a bile duct cancer",E.label_bile],
  ].filter(([,e])=>f>=e.l && f<=E.label_bile.e);
  return <Lens plan={GP} f={f}>
    <Stage zone={ZONE} f={continuous} tray={false}>
      <div style={{position:"absolute",inset:0,background:"rgba(244,241,234,.20)"}}/>
      <RoadWorld cx={mix(cx+5.6*Math.sin(continuous*.15),X[3],dive)} zoom={z} red={{6:glow(f,E.approved)}} ticks={{0:1,1:1,3:1,6:hit(f,E.approved)}}>
        <Status/>
        <Sprite name="dish/34" x={X[3]+142} y={Y+57+3*Math.sin(continuous*.22)} w={108}/>
        {gate>0 && <Slab x={X[3]+172} y={Y-25-60*(1-gate)} w={33} h={53} r={6} color={C.bone} op={gate} id="gate"/>}
        {dates>0 && <Plate x={X[6]-98} y={Y-193} w={196} h={52} size={36} text="Sep 2026" color={C.bone} op={dates} id="date"/>}
        {blueOn>0 && <TagBody x={blueX} color={C.blue} op={blueOn} rot={Math.sin(f*.26)*4} id="approvedTag"/>}
        {otherOn>0 && <TagBody x={otherX} y={Y+18+198*fail*fail} color={fail>.35?C.grey:C.blue} op={otherOn*(1-fail)} rot={fail*65} id="failedTag"/>}
        {otherOn>0 && <Slab x={X[4]+68} y={Y+179} w={120} h={75} color={C.bone} depth={12} op={otherOn} id="scrap"/>}
        {share>0 && [-1,0,1].map((i)=>{
          const x=X[3]+i*177,y=Y+196;
          return <React.Fragment key={i}>
            <Gate x1={X[3]} y1={Y+97} x2={mix(X[3],x,share)} y2={mix(Y+97,y,share)} w={6}/>
            <Plate x={mix(X[3],x,share)-37} y={mix(Y+97,y,share)} w={74} h={42} size={29} text="048" color={C.gold} op={share} id={`share${i}`}/>
            {people>0 && <Sprite name="person/34" x={x+47} y={y-12+24*(1-people)} w={85} op={people}/>}
          </React.Fragment>;
        })}
        <TagBody x={X[3]+53*Math.sin(Math.PI*nudge)} y={Y+18} text="048" rot={Math.sin(continuous*.16)*1.7} id="gold048"/>
      </RoadWorld>
      {labelLines.length>0 && <div data-role="label" data-rid="lira" style={{position:"absolute",left:130,top:146,
        background:"rgba(244,241,234,.8)", borderRadius:12,padding:"12px 22px",fontFamily:"InstrumentSerifB",fontSize:60,lineHeight:1,color:C.ink}}>
        {labelLines.map(([s])=><div key={s}>{s}</div>)}</div>}
      <Source>Illustration · Wang et al. 2023; FDA, Sep 2026; GEN, Jan 2023</Source>
      {dive>0 && <Slab x={mix(903,-1000,dive)} y={mix(625,-800,dive)} w={mix(132,3900,dive)} h={mix(77,2700,dive)}
        color={C.gold} id="diveGold" depth={8}/>}
    </Stage>
  </Lens>;
};
const Root=()=> <Composition id="B611" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080}/>;
registerRoot(Root);
