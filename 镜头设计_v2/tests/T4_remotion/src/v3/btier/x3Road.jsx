// HKBU SCIE1007 课程作业的科普视频：2.5 简版长路的共用台面和吊牌。
import React from "react";
import {C, Slab, Plate, Runner, Engrave, Gate, Tick} from "./bkit.jsx";

export const X = [250,570,890,1210,1530,1850,2170];
export const Y = 602;
export const names = ["Target","Hit","Improve","Cells","Animals","Trials","Approval"];
// 审查批 1（11-23）：长路页停站时容器缩放 ZS（原 1.09 × 1.8 ≈ 2.0），拉回看路 ZF = 1.2；6-10 末机位留在拉回的 1.2，6-11 从这里接
export const ZS = 2.0, ZF = 1.2;
export const start = 40, end610 = [1510, ZF];
const road = `M -220 ${Y} H 2520`;
export const clamp = (x) => Math.max(0,Math.min(1,x));
export const mix = (a,b,t) => a+(b-a)*t;
export const ease = (t) => t*t*(3-2*t);
export const tween = (f,a,b) => ease(clamp((f-a)/Math.max(1,b-a)));
export const pos = (f,e) => tween(f,e.s,e.l);
export const run = (f,e) => tween(f,e.s,e.e);
export const hit = (f,e) => clamp((f-e.l+1)/6);
export const glow = (f,e) => f<e.l || f>e.e ? 0 : .36*(.7+.3*Math.cos((f-e.l)/8));

export function pathAt(f, initial, events) {
  let v=initial;
  for (const [e,dest] of events) {
    if (f<e.s) break;
    v = v.map((x,j)=>mix(x,dest[j],pos(f,e)));
  }
  return v;
}
export function TagBody({x,y=Y+18,color=C.gold,text,rot=0,op=1,zoom=1,id="tag"}) {
  return <div style={{position:"absolute",left:x-66,top:y,width:132,height:114,transform:`rotate(${rot}deg) scale(${zoom})`,
    transformOrigin:"66px 0", opacity:op}}>
    <span style={{position:"absolute",border:`5px solid ${color}`,width:24,height:36,boxSizing:"border-box",borderRadius:16,left:54,top:-29}}/>
    <Plate x={0} y={0} w={132} h={77} text={text} size={44} color={color} light={color===C.blue} id={id} />
  </div>;
}
export function RoadWorld({cx,zoom,y=600,children,red={},ticks={},pulse}) {
  return <div style={{position:"absolute",width:1920,height:1080,left:0,top:0,transformOrigin:"0 0",
    transform:`translate(960px,${y}px) scale(${zoom}) translate(${-cx}px,${-Y}px)`}}>
    <Runner d={road} width={20}/>
    {X.map((x,i)=><React.Fragment key={i}>
      <Gate x1={x} y1={Y-1} x2={x} y2={Y-42} w={9}/>
      <Plate id={`station${i}`} x={x-113} y={Y-132} w={226} h={86} text={names[i]} size={44}>
        {red[i]>0 && <div style={{position:"absolute",inset:6,border:`3px solid ${C.red}`,borderRadius:11,opacity:red[i]}}/>}
      </Plate>
      {ticks[i]>0 && <Tick x={x+91} y={Y-134} s={56} p={ticks[i]} sw={9}/>}
    </React.Fragment>)}
    {Number.isFinite(pulse) && <div style={{position:"absolute",left:pulse-22,top:Y-11,height:22,width:44,
      background:C.red,opacity:.40,borderRadius:14}}/>}
    {children}
  </div>;
}
export function Pending({x,label,amount,id,dy=0}) {
  return amount>0 && <Plate x={x-76} y={Y-183-dy-22*(1-amount)} w={152} h={52} text={label} size={36}
    color={C.bone} op={amount} depth={6} id={id}/>;
}
export function Status({started=1,n1=1,n2=1,dy=0}) {
  return <><Pending x={X[2]} label="started" amount={started} id="started" dy={dy}/>
    <Pending x={X[4]} label="not yet" amount={n1} id="notyetA" dy={dy}/>
    <Pending x={X[5]} label="not yet" amount={n2} id="notyetB" dy={dy}/></>;
}
