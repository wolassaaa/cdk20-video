// HKBU SCIE1007 课程作业的科普视频：B 档 4-10（A 画外音）"It came back with 8,918 brand-new designs…"
// s1 8,918：数字轮转到 8,918；brand-new designs：小金插头一波一波铺满。s2 Way too many to make：手写。
// s3 each key：中间一个插头升起来，别的退下；a virtual lock：右边蓝线描出的线框插座。
// s4 That's docking：标 docking；the computer：一道扫描线扫过线框；a molecule：插头转向插孔；might sit in the pocket：插头尖进孔；scores the fit：表盘指针摆到高分。
// s5 Similar designs get grouped：插头回来，聚成六堆；54：数字轮滚到 54，每堆只留下几个；chemists：两个小人；pick just seven：七个插头飞进托盘；to make：烧瓶落下。
// 接点：开头 T5 芯片擦除（上一段 W3 是 A 段芯片），结尾 T5 料杆擦除（下一段 4-11+12 是出镜段）。L0 第 4 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_4-10.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Engrave, camBreath, Stage, Sprite, Slab, Label, Pen, Source, Counter, Person1, anchorOf, evMapB, T5In, T5Out, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, rand} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 4;

const mix = (a,b,p)=>a+(b-a)*p;
const clamp=x=>Math.max(0,Math.min(1,x));
const points = Array.from({length:8918},(_,i)=>[226+15.15*(i%98),207+6.45*Math.floor(i/98)]);
const inBox = ([x,y]) => x>1360 && y<400;   // P48：计数框里不画格点（框取到 y<400，单位标签也在里面）
const dotsPath = (p,r) => p.filter(q=>!inBox(q)).map(([x,y])=>`M${Math.round(x)} ${Math.round(y)}h.2`).join("");
const groups = Array.from({length:54},(_,i)=>[280+170*(i%9),244+65*Math.floor(i/9)]);
const fullDots = dotsPath(points,1);
const clustered = dotsPath(points.map((_,i)=>{
  const [x,y]=groups[i%54], a=i*2.39996, d=4+Math.sqrt(i/54)*2.1;
  return [x+d*Math.cos(a),y+d*.59*Math.sin(a)];
}),1);
const winners = [1,8,13,28,34,45,52];
const Scene=()=>{
  const f=useCurrentFrame();
  const pr=(a,b)=>clamp((f-a)/Math.max(1,b-a));
  const pile=pr(E.n8918.s,E.n8918.l), rise=pr(E.each.s,E.each.l+24);
  const lock=pr(E.vlock.s,E.vlock.l), back=pr(E.group.s-26,E.group.s);
  const group=pr(E.group.s,E.group.l+28), cut=pr(E.n54.s,E.n54.l);
  const seven=pr(E.seven.s,E.seven.l);
  const fit=pr(E.scorefit.s,E.scorefit.l);
  const starting=1-pr(E.each.s,E.each.l);
  const opacity=starting+back*(1-starting);
  const moving=Math.sin(Math.PI*pr(E.comp.s,E.sit.l)*6)*(1-pr(E.sit.s,E.sit.l));
  const [ox,oy]=[0,0];
  const near=pr(E.sit.s,E.sit.l);
  return <Lens plan={GP} f={f}>
    <Stage zone={ZONE} f={f} cam={camBreath(f,K,[])} shakeX={impact(f,E.sit.l)} over={<><T5In name="key" f={f}/><T5Out name="runner" f={f} len={LEN}/></>}>
      <Layer id="pile">
        {pile>0 && opacity>0 && <svg width={1920} height={1080} style={{position:"absolute",inset:0,opacity:opacity}}>
          <defs><clipPath id="growpoints"><rect x={190} y={184} width={1570*pile} height={626}/></clipPath></defs>
          <g clipPath="url(#growpoints)" fill="none" strokeLinecap="round" strokeWidth={3.4}>
            <path d={fullDots} stroke={C.blue} opacity={(1-group)*(.94-.72*cut)}/>
            {group>0 && <path d={clustered} stroke={seven>0?C.grey:C.blue} opacity={group*(.96-.68*cut)}/>}
          </g>
          {cut>0 && groups.map(([x,y],i)=>inBox([x,y])?null:<circle key={i} cx={x} cy={y-12*cut} r={4+4*cut} fill={winners.includes(i)?C.blue:C.grey} opacity={cut*(1-.78*seven)}/>)}
        </svg>}
      </Layer>
      <Layer id="socket">
        {lock>0&&back<1&& <Sprite name="socket/hero_face" x={1300} y={514-60*(1-lock)} w={336} op={lock*.45*(1-back)} rim={lock}/>}
      </Layer>
      <Layer id="hero">
        {rise>0 && back<1 && <Sprite name="plug/A_34" x={mix(mix(960,782,rise),1300+ox-80,near)} y={mix(mix(392,512,rise),514+oy,near)+38*moving} w={mix(12,344,rise)} sx={-1} op={rise*(1-back)} rot={moving*19}/>}
      </Layer>
      <Layer id="dial">
        {fit>0&&back<1&&<Slab x={440} y={679} w={415} h={46} r={13} id="scoreSlot" op={1-back}>
          <div style={{position:"absolute",left:8,top:8,bottom:8,width:385*.83*fit,borderRadius:8,background:C.blue}}/>
        </Slab>}
      </Layer>
      <Layer id="tray">
        {seven>0 && winners.map((i,k)=>{
          const [x,y]=groups[i];
          const a=clamp(seven*1.34-k*.047);
          return <Sprite key={i} name={`plug/${"ABCDEF"[k%6]}_34`} x={mix(x,248+232*k,a)} y={mix(y,694,a)-53*Math.sin(Math.PI*a)} w={mix(14,239,a)} op={a} rot={-90*a}/>;
        })}
      </Layer>
      <Layer id="txt" exempt>
        {((pile>0&&starting>.8)||cut>0)&&!(f>=E.group.s&&f<E.n54.s)&&<Counter value={f>=E.seven.l?7:f>=E.n54.l?54:Math.round(8918*pile)} size={140} digits={f>=E.seven.l?1:cut>0?2:4} comma x={1467} y={164}/>}
        <Label text="designs" size={36} x={1780} y={320} at={E.n8918.l} out={E.each.s} align="right" />
        <Label text="shortlisted" size={36} x={1780} y={320} at={E.n54.l} out={E.seven.s} align="right" />
        <Label text="chosen to make" size={36} x={1780} y={320} at={E.seven.l} align="right" />
        <Pen text="way too many" x={1190} y={749} at={E.many.l} out={E.each.s} size={62}/>
        <Label text="fit score" x={648} y={745} at={E.scorefit.l} out={E.group.s-29} align="center"/>
        <Label text="docking" x={1300} y={685} at={E.dock.l} out={E.group.s-29} align="center"/>
        <Source>Illustration · numbers: Ren et al., Chem. Sci. 2023</Source>
      </Layer>
    </Stage>
  </Lens>;
};

const Root = () => <Composition id="B410" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
