// HKBU SCIE1007 课程作业的科普视频：B 档 2-05（C 画外音）"One: to identify the major computer-aided methods used in cancer drug discovery. Two: …"
// 上栏 Aim 1：编号牌 1；identify：放大镜从左扫过来；computer-aided methods：三块 AI 芯片依次落位（放大镜停在中间那块上）；cancer drug discovery：玻璃肝。
// 下栏 Aim 2：编号牌 2；evaluate：料杆和检测门长出来；these methods：上栏芯片一块块亮；scientists：小人；
// assess：五个金插头沿料杆走过检测门，过门时各长一根分数条；potential drug candidates：插头排好，分数最高的打勾。
// 导演 11-18 看二维样片 2-05 时要求加说明文字：两栏各一行 Aim 1 / Aim 2 的标签。
// 接点：开头 T5 料杆擦除（2-04 出镜段），结尾 T2 往左甩（2-06 是 B 页）。L0 第 2 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_2-05.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, SERIF, Tag, camBreath, Stage, Sprite, Slab, Runner, Plate, Label, Source, Tick, LoupeRing, Person1, evMapB, T5In, whipX} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 2;

const CHIPS = ["pandaomics", "chemistry42"];   // P25：两个 AI 引擎（AlphaFold 不是 Insilico 的，去掉）
const PW = 200;
const POINTS = [1100,1340,1580];
const TARGET = ["1  identify the major computer-aided methods","2  evaluate how these methods help"];
const Scene = () => {
  const f = useCurrentFrame();
  const F = (key) => K.words.find(w => w.key === key)?.f0 ?? LEN-8;
  const cf = (a,b) => Math.max(0,Math.min(1,(f-a)/Math.max(1,b-a)));
  const discovery = F("discovery#1");
  const show = (n) => cf(n ? E.aim2.s : E.aim1.s,n ? E.aim2.l : E.aim1.l);
  const slide = (n) => n ? cf(E.eval.s,E.eval.e) : cf(E.identify.s,discovery);
  const score = cf(E.assess.s,E.assess.l);
  return <Lens plan={GP} f={f}>
    <Stage zone={ZONE} f={f} whip={whipX(f,LEN-7,"out",-1)} cam={camBreath(f,K,["s1","s2"])} over={<T5In name="runner" f={f}/>}>
      {[0,1].map(n=>{
        const a = show(n), p = slide(n), y = (n ? 560 : 188)-78*(1-a);
        if (!a) return null;
        return <Layer key={n} id={n ? "aim2":"aim1"}>
          <Slab x={210} y={y} w={1500} h={200} r={22} op={a} id={`aim${n}`}>
            <div data-role="engrave" data-on={`aim${n}`} style={{position:"absolute",left:50,right:50,top:60,fontFamily:SERIF,fontSize:64,color:C.ink,whiteSpace:"nowrap"}}>{TARGET[n]}</div>
            {p<1 && <div style={{position:"absolute",left:8+1484*p,top:8,right:8,bottom:8,borderRadius:16,background:C.bone,boxShadow:"-4px 3px 8px rgba(0,0,0,.24), inset 0 1px 0 white"}}/>}
          </Slab>
        </Layer>;
      })}
      <Layer id="chips">
        {CHIPS.map((n,i)=>{
          const a=cf(E.methods.s+i*5,E.methods.l+i*5);
          return a>0 && <React.Fragment key={n}><Tag x={760+400*i} y={500+85*(1-a)} op={a}>{["PandaOmics","Chemistry42"][i]}</Tag><Sprite name={`chip_${n}/34`} x={760+400*i} y={432+85*(1-a)} w={180} op={a} rim={.35*Math.max(0,1-Math.abs(f-E.these.l-i*5)/15)}/></React.Fragment>;
        })}
      </Layer>
      <Layer id="score">
                {POINTS.map((x,i)=>{
          const a=cf(E.cands.s+i*3,E.cands.l+i*3);
          return a>0 && <React.Fragment key={x}>
            <Sprite name={`plug/${"ABC"[i]}_34`} x={x} y={815-68*(1-a)} w={PW} op={a}/>
          </React.Fragment>;
        })}
      </Layer>
      <Layer id="txt" exempt><Label text="potential drug candidates" size={40} x={900} y={790} at={E.cands.l} align="right"/><Source>Illustration · our two aims for this review</Source></Layer>
    </Stage>
  </Lens>;
};

const Root = () => <Composition id="B205" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
