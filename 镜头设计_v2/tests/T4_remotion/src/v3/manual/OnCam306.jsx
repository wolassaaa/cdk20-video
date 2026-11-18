// HKBU SCIE1007 课程作业的科普视频：出镜 3-06（D）"So: a strong suspect. Not the only cause of liver cancer, but a lock worth trying."（第 2 版，重写）
// 讲解卡：肝在上；一排三张嫌疑犯卡，CDK20 在中间；三张卡依次连箭头到肝；but 时两边卡沉下去，CDK20 卡移到中间放大，
// 蛋白上长出锁梁变成锁（同一样东西变形）；钥匙从右边滑来对准锁。时间全读 oncam_3-06.json（事件表 映射/events/3-06.json）。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_3-06.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Part, Label, Pen, Plate, Arrow} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const FX1 = 1290, FY1 = 200, FX2 = 1870, FY2 = 900;
const LIV = {cx: 1580, cy: 285, w: 170};
const CY = 590, CW = 140, CH = 190, CX = [1385, 1580, 1775];
const back = Easing.out(Easing.back(1.5));

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const hopP = span(f, E.hop.s, E.hop.s + 22);
  const hop = 1 + 0.14 * Math.sin(Math.PI * hopP);
  const stg = span(f, E.strong.s, E.strong.l + 6, back);
  const sink = span(f, E.sink.s, E.sink.s + 34, ease);
  const big = span(f, E.big.s, E.big.l + 6, ease);
  const fade = 1 - span(f, E.sink.s, E.sink.s + 26);
  const cardFade = 1 - span(f, E.lock.s, E.lock.s + 18);
  // 中间卡：往前一步（上移 20，放大 1.15），后来移到 (1480, 600) 放大到 2 倍
  const sc = (1 + 0.15 * stg) * (1 - big) + 2 * big, ty = -20 * stg * (1 - big) + 10 * big, tx = -100 * big;
  const midT = `translate(${tx}px,${ty}px) scale(${sc})`;
  const kmv = span(f, E.key.s, E.key.l + 8, ease), kx = 1780 + (1700 - 1780) * kmv;
  const arrows = [[E.arr1, 1385, 490, 1532], [E.arr2, 1580, 462, 1580], [E.arr3, 1775, 490, 1628]];
  const box = (i) => {
    const p = span(f, E.cards.s + i * 10, E.cards.s + i * 10 + 28, back);
    const mid = i === 1;
    return (
      <div key={i} style={{position: "absolute", left: CX[i] - CW / 2, top: CY - CH / 2 + 30 * (1 - p) + (mid ? 0 : 150 * sink), width: CW, height: CH, boxSizing: "border-box",
                           border: `${mid && stg > 0.5 ? 5 : 3}px solid ${mid && stg > 0.5 ? RED : INK}`, borderRadius: 10, background: "rgba(237,233,223,0.96)",
                           opacity: p * (mid ? cardFade : 1 - span(f, E.sink.s + 6, E.sink.s + 30)),
                           transform: mid ? midT : undefined, transformOrigin: "50% 50%",
                           font: "italic 100px/184px Serif", color: SOFT, textAlign: "center"}}>{mid ? null : "?"}</div>
    );
  };
  return (
    <OnCamFrame D={D} f={f} wav="3-06.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
        </svg>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `scale(${hop})`, transformOrigin: `${LIV.cx}px ${LIV.cy}px`}}>
          <Part name="liver" cx={LIV.cx} cy={LIV.cy} w={LIV.w} at={E.liver.l} f={f} gate={[0.5, 1]} />
        </div>
        <Label x={1760} y={262} w={200} p={span(f, E.liverlab.s, E.liverlab.l + 12)} size={28} italic color={INK}>liver cancer</Label>
        {[0, 1, 2].map(box)}
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <g opacity={fade}>
            {arrows.map(([ev, x0, y0, x1], i) => {
              const ang = Math.atan2(358 - y0, x1 - x0) * 180 / Math.PI;
              return <Arrow key={i} d={`M${x0},${y0} L${x1},358`} tip={[x1, 358]} ang={ang} a={ev.s} b={ev.l + 8} f={f} />;
            })}
          </g>
          {/* 锁梁：画在蛋白后面，蛋白就是锁身 */}
          {[[INK, 20], ["#2C40A6", 12]].map(([c, w], i) => (
            <path key={i} d="M1432,595 L1432,468 A48,48 0 0 1 1528,468 L1528,595" fill="none" stroke={c} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round"
                  pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(f, E.lock.s, E.lock.s + 26, ease)} />
          ))}
        </svg>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: midT, transformOrigin: `1580px ${CY}px`}}>
          <Part name="cdk20" cx={1580} cy={CY} w={100} at={E.cards.s + 24} f={f} gate={[0.5, 0.5]} flood={18} />
        </div>
        <Plate x={1360} y={718} w={440} p={span(f, E.plate.s, E.plate.l + 8, out) * fade}><span style={{fontSize: 44}}>a strong suspect</span></Plate>
        <div style={{opacity: fade}}><Pen x={1340} y={790} p={span(f, E.note.s, E.note.l + 14)} size={40} rot={-3}>not the only cause</Pen></div>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${2 * kx}px) scaleX(-1)`, transformOrigin: "0 0"}}>
          <Part name="key" cx={kx} cy={600} w={170} at={E.key.s + 4} f={f} gate={[0, 0.5]} flood={14} />
        </div>
        <Pen x={1420} y={728} p={span(f, E.try.s, E.try.l + 14)} size={44} rot={-3}>worth trying</Pen>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam306" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
