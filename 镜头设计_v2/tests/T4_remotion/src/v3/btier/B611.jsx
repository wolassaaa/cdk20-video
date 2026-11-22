// HKBU SCIE1007 课程作业的科普视频：6-11，从 6-10 末机位接到长路终点，再回到 048。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-11.json";
import Previous from "./keys_6-10.json";
import {Lens, guidePlan} from "../manual/kit.jsx";
import {C, Stage, Sprite, Slab, Engrave, Plate, Gate, Source, Person1, evMapB, shade} from "./bkit.jsx";
import {X,Y,start,end610,ZS,ZF,TagBody,RoadWorld,Status,pathAt,pos,run,hit,clamp,tween,mix,glow} from "./x3Road.jsx";

const ZONE = 6;
const E=evMapB(K);
const GP=guidePlan(K);
// 审查批 1（11-23）：容器缩放 ×1.8（ZS = 2.0）跟着蓝色吊牌和 048 走；cam_end、cam_back 拉回 ZF = 1.2；share 起 ×3.0 以 048 吊牌为中心。
// 机位三个数 [cx, 缩放, 路在屏上的 y]；dest 可以是函数（逐帧跟着吊牌）。
const BIN={x:X[4],top:Y+110,w:180,h:100,rim:14,front:Y+178};     // Animals 站下的骨白敞口料盒（世界坐标）
const camAt=(f,init,list)=>{
  let v=init;
  for (const [e,d] of list) {
    if (f<e.s) break;
    const dest=typeof d==="function"?d(f):d;
    v=v.map((x,j)=>mix(x,dest[j],tween(f,e.s,e.l)));
  }
  return v;
};
const Scene=()=>{
  const f=useCurrentFrame(), continuous=f+Previous.len_f-1;
  const dive=pos(f,E.dive);
  const nudge=run(f,E.nudge);
  const blueAt=(g)=>mix(mix(start,X[5]-70,run(g,E.tagB_run)),X[6],pos(g,E.tagB_arrive));
  const blueX=blueAt(f);
  const [cx,z,ry]=camAt(f,[...end610,600],[
    [E.cam_end,[1820,ZF,600]],
    [{s:166,l:192},(g)=>[blueAt(g)+100,ZS,600]],                    // 甩到路起点，跟着蓝色吊牌走
    [{s:372,l:400},[1975,ZS,480]],                                  // 蓝牌停在 Trials 后，Sep 2026 牌和 Approval 入画；路上移给左下的字让位
    [{s:E.tagB_arrive.s,l:E.tagB_arrive.l+6},[X[6]-260,ZS,480]],    // 到 Approval：站在画面右半，左下是 lirafugratinib 三行字
    [{s:906,l:950},[X[4]+60,ZS,420]],                               // Others failed：Animals 站和下面的料盒
    [E.cam_back,[X[3],ZF,600]],
    [{s:E.cam_back.e+1,l:E.nudge.s},[X[3],ZS,600]],                // 回到 048
    [{s:E.share.s,l:E.share.s+40},[X[3],3.0,96]],                  // share：×3.0 以 048 为中心
  ]);
  const blueOn=clamp((f-E.tagB_run.s)/10);
  const fail=run(f,E.tagC_fail);
  const otherX=mix(mix(start,X[4]+125,run(f,E.tagC_run)),BIN.x,fail);
  const otherOn=clamp((f-E.tagC_run.s)/8)*(1-tween(f,E.cam_back.s-6,E.cam_back.l));   // 料盒和掉进去的灰牌在 And 048? 拉回时退场，不再挂到段尾
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
      <RoadWorld cx={mix(cx+5.6*Math.sin(continuous*.15),X[3],dive)} zoom={z} y={ry} red={{6:glow(f,E.approved)}} ticks={{0:1,1:1,3:1,6:hit(f,E.approved)}}>
        <Status/>
        <Sprite name="dish/34" x={X[3]+142} y={Y+57+3*Math.sin(continuous*.22)} w={108}/>
        {gate>0 && <Slab x={X[3]+172} y={Y-25-60*(1-gate)} w={33} h={53} r={6} color={C.bone} op={gate} id="gate"/>}
        {dates>0 && <Plate x={X[6]-98} y={Y-193} w={196} h={52} size={36} text="Sep 2026" color={C.bone} op={dates} id="date"/>}
        {blueOn>0 && <TagBody x={blueX} color={C.blue} op={blueOn} rot={Math.sin(f*.26)*4} id="approvedTag"/>}
        {otherOn>0 && <Slab x={BIN.x-BIN.w/2} y={BIN.top} w={BIN.w} h={BIN.h} r={16} color={C.bone} depth={12} op={otherOn} id="binBack">
          <div style={{position:"absolute",left:BIN.rim,top:BIN.rim,width:BIN.w-2*BIN.rim,height:BIN.h-2*BIN.rim,borderRadius:10,
            background:shade(C.bone,.12),boxShadow:`inset 0 6px 10px ${shade(C.bone,.35)}`}}/></Slab>}
        {otherOn>0 && <TagBody x={otherX} y={mix(Y+18,BIN.top+30,fail*fail)} color={fail>.05?C.grey:C.blue} op={otherOn} rot={25*Math.min(1,fail*1.15)} id="failedTag"/>}
        {otherOn>0 && <Slab x={BIN.x-BIN.w/2} y={BIN.front} w={BIN.w} h={BIN.top+BIN.h-BIN.front} r={12} color={C.bone} depth={12} op={otherOn} id="binFront"/>}
        {share>0 && [-1,0,1].map((i)=>{
          const x=X[3]+i*177,y=Y+196;
          return <React.Fragment key={i}>
            <Gate x1={X[3]} y1={Y+97} x2={mix(X[3],x,share)} y2={mix(Y+97,y,share)} w={6}/>
            <Plate x={mix(X[3],x,share)-37} y={mix(Y+97,y,share)} w={74} h={42} size={29} text="048" color={C.gold} op={share} id={`share${i}`}/>
            {people>0 && <Person1 x={x+64} y={y+4+16*(1-people)} w={130} op={people}/>}
          </React.Fragment>;
        })}
        <TagBody x={X[3]+53*Math.sin(Math.PI*nudge)} y={Y+18} text="048" rot={Math.sin(continuous*.16)*1.7} id="gold048"/>
      </RoadWorld>
      {labelLines.length>0 && <div data-role="label" data-rid="lira" style={{position:"absolute",left:130,top:672,
        background:"rgba(244,241,234,.8)", borderRadius:12,padding:"12px 22px",fontFamily:"InstrumentSerifB",fontSize:60,lineHeight:1,color:C.ink}}>
        {labelLines.map(([s])=><div key={s}>{s}</div>)}</div>}
      <Source>Illustration · Wang et al. 2023; FDA, Sep 2026; GEN, Jan 2023</Source>
      {dive>0 && <Slab x={mix(960-66*z,-1000,dive)} y={mix(ry+18*z,-800,dive)} w={mix(132*z,3900,dive)} h={mix(77*z,2700,dive)}
        color={C.gold} id="diveGold" depth={8}/>}
    </Stage>
  </Lens>;
};
const Root=()=> <Composition id="B611" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080}/>;
registerRoot(Root);
