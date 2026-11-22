// HKBU SCIE1007 课程作业的科普视频：2-08，预告前三站（简版无托盘）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_2-08.json";
import {Lens, guidePlan} from "../manual/kit.jsx";
import {C, Stage, Sprite, Slab, Source, evMapB, spriteMeta} from "./bkit.jsx";
import {X,Y,start,RoadWorld,pathAt,pos,run,hit,glow,clamp,mix} from "./x3Road.jsx";

const ZONE = 2;
const E=evMapB(K);
const GP=guidePlan(K);
const follow=(cam,pulse)=>({...cam,s:pulse.s+6});
const Scene=()=>{
  const f=useCurrentFrame();
  const [cx,z]=pathAt(f,[493,.97],[[E.cam_est,[567,.96]],[follow(E.cam1,E.pulse1),[276,1.12]],[follow(E.cam2,E.pulse2),[563,1.12]],[follow(E.cam3,E.pulse3),[890,1.12]],
    [E.cam_up,[1180,.82]],[E.far_focus,[1220,.81]]]);
  const pulse=pathAt(f,[start],[[E.pulse1,[X[0]]],[E.pulse2,[X[1]]],[E.pulse3,[X[2]]]])[0];
  const lock=hit(f,E.red1),rise=run(f,E.lock_rise),dive=pos(f,E.dive);
  // 低分辨率锁图只到套件容许宽度，最后靠近锁芯的部分由矢量件继续。
  const cap=Math.floor(.8*spriteMeta("lock/closed").w);
  const face=clamp((dive-.65)/.35);
  const lockX=mix(390,960,dive),lockY=mix(585,540,dive);
  const faceW=mix(cap,2920,face),faceH=mix(489,2080,face);
  const wave=(e,rate=8)=>f<e.l || f>e.e?0:Math.sin((f-e.l)/rate);
  return <Lens plan={GP} f={f}>
    <Stage zone={ZONE} f={f} tray={false}>
      <div style={{position:"absolute",inset:0,background:"rgba(244,241,234,.20)"}}/>
      <RoadWorld cx={cx+5.6*Math.sin(f*.15)} zoom={z} y={mix(600,650,pos(f,E.cam_up))}
        red={{0:Math.max(glow(f,E.red1),.16*hit(f,E.red1)),1:Math.max(glow(f,E.red2),.16*hit(f,E.red2)),2:Math.max(glow(f,E.red3),.16*hit(f,E.red3))}}
        pulse={f>=E.pulse1.s && f<=E.cam_up.l?pulse:undefined}>
        {lock>0 && dive===0 && <Sprite name="lock/closed" x={X[0]} y={Y+98-85*rise-15*wave(E.red1)}
          w={166} rot={-3+3*wave(E.red1)} op={lock}/>}
        {f>=E.key_glint.s && <div style={{position:"absolute",left:X[1]-96,top:Y+48,width:192,height:74,
          transform:`rotate(${3*wave(E.key_glint)}deg)`,transformOrigin:"center"}}>
          <svg width={192} height={74}><circle cx={41} cy={37} r={27} fill={C.gold}/><circle cx={41} cy={37} r={10} fill={C.table}/>
          <path d="M 63 28 H 177 V 48 H 158 V 57 H 142 V 47 H 62 Z" fill={C.gold}/>
          <path d="M 78 33 H 162" fill="none" stroke={C.inkLight} opacity={.35+.2*wave(E.key_glint)} strokeWidth={3}/></svg>
        </div>}
        {f>=E.red3.l && <><Sprite name="flask/34" x={X[2]} y={Y+92} w={140}/>
          {[0,1,2].map(i=><span key={i} style={{position:"absolute",left:X[2]+13*i-15,
            top:Y+58-((f-E.red3.l+i*19)%52),border:`1px solid ${C.inkLight}`,borderRadius:12,
            width:8+2*i,height:8+2*i,opacity:.24+.16*wave(E.red3)}}/>)}</>}
        {["pandaomics","alphafold","chemistry42"].map((n,i)=>{
          const op=clamp((f-E.chips.l-i*8+1)/10);
          return op>0 && <Sprite key={n} name={`chip_${n}/34`} x={X[1]+i*157} y={Y-221} w={118} op={op}/>;
        })}
      </RoadWorld>
      {dive>0 && dive<.72 && <Sprite name="lock/closed" x={lockX} y={lockY} w={Math.min(cap,mix(180,2300,dive))}
        rot={mix(-3,0,dive)} hero/>}
      {face>0 && <Slab x={lockX-faceW/2} y={lockY-faceH/2} w={faceW} h={faceH} color={C.gold} id="diveLock">
        <div style={{position:"absolute",left:"41%",top:"17%",width:"18%",height:"62%",borderRadius:"44%",background:C.black,border:`20px solid ${C.gold}`}}/>
      </Slab>}
      {dive<.85 && <Source>Illustration · our route through this review</Source>}
    </Stage>
  </Lens>;
};
const Root=()=> <Composition id="B208" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080}/>;
registerRoot(Root);
