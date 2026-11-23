// HKBU SCIE1007 课程作业的科普视频：2-01 · 香港研究和同一个蛋白（18 §2.8）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_2-01.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, SERIF, Stage, Sprite, Slab, Label, Tag, Source, evMapB, T5In, T5Out, T6Sweep, camBreath} from "./bkit.jsx";
import {Flap} from "./board6.jsx";

const ZONE = 2;
const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const clamp = (x) => Math.max(0, Math.min(1, x));
const tween = (f, start, end) => {
  const p = clamp((f - start) / Math.max(1, end - start));
  return p * p * (3 - 2 * p);
};
const mix = (a, b, p) => a + (b - a) * p;
const drop = (f, e, distance = 70) => distance * (1 - tween(f, e.s, e.l));
const Pins = ({points}) => (
  <svg width={1920} height={1080} style={{position:"absolute", inset:0, pointerEvents:"none"}}>
    {points.map(([x,y,col], i) => <g key={i}><path d={`M${x} ${y}v-12`} stroke={C.ink} strokeWidth={5}/><circle cx={x} cy={y-14} r={10} fill={col||C.blue} stroke={C.bone} strokeWidth={2}/></g>)}
  </svg>
);

const Scene = () => {
  const f = useCurrentFrame();
  const inMap = tween(f, E.map.s, E.map.l);
  const tuck = tween(f, E.tum.s - 20, E.tum.l);
  const back = tween(f, E.hk3.s - 22, E.hk3.l);
  const pan = 18*Math.sin(f/32);
  const mx = mix(mix(920, 407, tuck), 930, back) + pan;
  const my = mix(mix(488, 346, tuck), 458, back) - 86 * (1 - inMap) + 8*Math.sin(f/42);
  // The approved source is 924 px wide; keep the kit's 0.8x cap pending a 2x asset.
  const mw = mix(mix(900, 474, tuck), 900, back);
  const mapPoint = (u, v) => [mx + (u - .5) * mw, my + (v - .5) * mw * 586 / 924];
  const campus = mapPoint(.615, .36), hospital = mapPoint(.60, .41), park = mapPoint(.662, .335);
  const tour = tween(f, E.team.s, E.team.l + 14);
  const liverIn = tween(f, E.tum.s, E.tum.l);
  const liverLeft = tween(f, E.prot.s - 25, E.prot.l + 34);
  const clear = tween(f, E.ai.s - 20, E.ai.l + 20);
  const showPaper = tween(f, E.study.s, E.study.l);
  const hidePaper = tween(f, E.hk3.s - 36, E.hk3.s);
  const slide = tween(f, E.same.s, E.same.l);
  const pwhOn = f >= E.pwh.l && f < E.prot.s;
  const pins = [f >= E.cuhk.l && f < E.pwh.s && campus, pwhOn && hospital, f >= E.sp.l && [park[0], park[1], C.red]].filter(Boolean);
  const yr = 2011 + Math.round(12 * tween(f, E.ff.l - 54, E.ff.l));
  const liverX = mix(mix(campus[0], 1135, liverIn), 399, liverLeft);
  const liverY = mix(478, 565, liverLeft) - 8 * Math.sin(tour * Math.PI) - 16 * Math.sin(tween(f, E.pat.s, E.pat.l + 18) * Math.PI);
  return <Lens plan={GP} f={f}>
    <Stage zone={ZONE} f={f} cam={camBreath(f,K,["s2","s3","s4"])} over={<><T5In name="runner" f={f}/><T6Sweep f={f} at={18}/><T5Out name="runner" f={f} len={LEN}/></>}>
      <Layer id="map">
        {inMap > 0 && <Sprite name="hkmap/34_codex2x" x={mx} y={my} w={mw} op={inMap}/>}
        <Pins points={pins}/>
      </Layer>
      <Layer id="year">
        {f >= E.y2011.s && <Flap f={f} x={1380} y={182} w={230} h={110} at={E.y2011.l} text={String(yr)} fs={89} bg={C.ink} color={C.inkLight}/>}
      </Layer>
      <Layer id="samples">
        {liverIn > 0 && clear < 1 && <Sprite hero name="liver/34" x={liverX} y={liverY - drop(f,E.tum,72) + clear*260} w={mix(636,306,liverLeft)} op={liverIn * (1 - clear)}>
          <div style={{position:"absolute",left:"54%",top:"50%",width:"11%",aspectRatio:"1",borderRadius:"50%",opacity:liverIn,background:`radial-gradient(circle at 35% 26%, ${C.inkLight}, ${C.red} 37%, ${C.red})`,boxShadow:"0 4px 12px rgba(70,0,0,0.4)"}}/>
        </Sprite>}
      </Layer>
      <Layer id="tubes">
        {Array.from({length:6},(_,i)=>{
          const a = tween(f,E.prot.s+i*3,E.prot.l+i*3);
          if (!a || clear === 1) return null;
          const x = 620 + Math.floor(i/2)*238 + (i%2)*86;
          const y = 331 - 120*(1-a) + clear*270;
          const raised = tween(f,E.raised.s+i*3,E.raised.l+14+i*4);
          const h = 112 + (i%2 === 0 ? 175 : 36)*raised + 4*Math.sin(f/7+i)*(1-clear);
          return <Slab key={i} id={`sample${i}`} x={x} y={y} w={69} h={400} r={33} op={a*(1-clear)}>
            <div style={{position:"absolute",left:11,right:11,bottom:25,height:h,background:i%2===1?C.grey:C.blue,borderRadius:"12px 12px 22px 22px",boxShadow:"inset 0 4px 2px rgba(255,255,255,0.45)"}}/>
          </Slab>;
        })}
        {f >= E.ccrk.s && clear < 1 && <div style={{opacity:1-clear}}>
          <Flap f={f} x={738} y={214} w={416} h={88} at={f >= E.cdk20.l-18 ? E.cdk20.l : E.ccrk.l} prev={f >= E.cdk20.l-18 ? "CCRK" : ""} text={f >= E.cdk20.l-18 ? "CDK20" : "CCRK"} fs={64} bg={C.ink} color={C.inkLight}/>
        </div>}
      </Layer>
      <Layer id="book">
        {showPaper > 0 && hidePaper < 1 && <Slab x={661 - hidePaper*360} y={323+drop(f,E.study)} w={520} h={360} op={showPaper*(1-hidePaper)} id="paper" sheen={f>=E.coauth.s && f<E.coauth.l+30 ? tween(f,E.coauth.s,E.coauth.l+30) : -1}>
          <div data-role="engrave" on="paper" style={{position:"absolute",left:28,right:28,top:24,fontFamily:SERIF,fontSize:42,color:C.ink}}>Ren et al., Chem. Sci. 2023</div>
          <div data-role="engrave" style={{position:"absolute",left:30,right:30,top:92,fontFamily:SERIF,fontSize:30,lineHeight:"34px",color:f>=E.coauth.l?C.blue:C.ink}}>Feng Ren, Xiao Ding, Min Zheng … Alex Zhavoronkov</div>
          {Array.from({length:12},(_,i)=><div key={i} style={{position:"absolute",left:30+(i%2)*235,top:185+Math.floor(i/2)*28,width:i>=10?143:205,height:9,borderRadius:4,background:C.grey,opacity:.45}}/>)}
        </Slab>}
        {f >= E.cdk20.s && hidePaper < 1 && <Sprite name="mini/m34_on" x={mix(1471,1320,slide)-hidePaper*360} y={512-drop(f,E.cdk20)-80*Math.sin(Math.PI*slide)} w={228} op={tween(f,E.cdk20.s,E.cdk20.l)*(1-hidePaper)}/>}
      </Layer>
      <Layer id="txt" exempt>
        <Label text="Chinese University of Hong Kong" x={928} y={755} at={E.cuhk.l} out={E.pwh.s-18} align="center"/>
        <Label text="Prince of Wales Hospital" x={417} y={670} at={E.pwh.l} out={E.prot.s-27} align="center"/>
        <Label text="Insilico Medicine Hong Kong Ltd" size={36} x={895} y={748} at={E.ins.l} out={E.hk3.s-35} align="center"/>
        <Label text="Hong Kong Science Park" size={36} x={park[0]} y={785} at={E.sp.l} align="center"/>
        <Tag x={620} y={748} align="left" op={tween(f,E.raised.l-10,E.raised.l)*(1-tween(f,E.ff.s-12,E.ff.s))}>blue = tumour</Tag>
        <Tag x={620} y={808} align="left" op={tween(f,E.raised.l-10,E.raised.l)*(1-tween(f,E.ff.s-12,E.ff.s))}>grey = nearby non-tumour</Tag>
        <Source>{f<E.study.l ? "Illustration · data: Feng et al., J. Clin. Invest. 2011" : "Illustration · Ren et al., Chem. Sci. 2023"}</Source>
      </Layer>
    </Stage>
  </Lens>;
};
const Root = () => <Composition id="B201" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080}/>;
registerRoot(Root);
