// HKBU SCIE1007 课程作业的科普视频：出镜 8-04 组（C "This works in cells, not yet in people…" → B headline → D "where it really is on the road" → A "AI didn't replace the scientists… Thanks"）。
// 讲解卡（右侧纸色卡片，x 1440–1870：B 举手机的手伸到 x≈1426，卡片从 1440 起才不盖人）：一条竖着的五站路 computer、protein、cells、animals、patients。
// C：cells 打勾、patients 写 not yet 并变灰；computer 旁漏斗，一片点落进去只漏出两三个；cells 旁 flask，红虚线箭头往下指（experiments still decide）。
// B：报纸从右边滑进来盖下，标题 AI discovers a cancer drug 写出、划红线。D：报纸上红问号，缩到卡顶；红光沿路扫下，五站随着说的词依次闪。
// A：漏斗淡出，科学家站到 computer 旁；computer 外一个循环箭头转起来，light speed 快转带残影；Thanks 五站从上往下全亮、路变红。
// 时间全读 oncam_8-04_8-05_8-06_8-07.json（事件表 映射/events/8-04+8-05+8-06+8-07.json）。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_8-04_8-05_8-06_8-07.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Part, Write, Pen} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const FX1 = 1440, FY1 = 150, FX2 = 1870, FY2 = 960;      // 讲解卡
const RX = 1500, IX = 1565, LX = 1610;                     // 路、图标、站名
const SY = [330, 460, 590, 720, 850];
const ST = ["computer", "protein", "cells", "animals", "patients"];
const NP = {cx: 1655, cy: 520, w: 380, h: 250}, NPS = {cx: 1655, cy: 222, s: 0.42};   // 报纸：大、缩小后
const rnd = (k) => { const v = Math.sin(k * 12.9898) * 43758.5453; return v - Math.floor(v); };
const DOTS = [...Array(16)].map((_, i) => ({x: 1776 + rnd(i + 3) * 68, y: 196 + rnd(i + 77) * 70, d: Math.floor(rnd(i + 51) * 12)}));

const Mouse = ({x, y, s}) => (
  <g transform={`translate(${x} ${y}) scale(${s})`} stroke={INK} strokeWidth={2.5} strokeLinejoin="round">
    <path d="M-24,4 C-40,4 -46,-6 -40,-14" fill="none" strokeLinecap="round" />
    <ellipse cx={0} cy={0} rx={24} ry={14} fill="#E2DED4" />
    <circle cx={22} cy={-6} r={10} fill="#E2DED4" /><circle cx={18} cy={-16} r={6} fill="#E2DED4" />
    <circle cx={27} cy={-7} r={1.8} fill={INK} stroke="none" />
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.card.s, E.card.s + 36, ease);
  const route = span(f, E.card.s + 20, E.card.e, ease);
  const io = Easing.inOut(Easing.cubic);
  const flashEv = [E.s1, E.s2, E.s3, E.s4, E.s5];
  const flash = (i) => { const e = flashEv[i]; return f >= e.s ? Math.exp(-Math.max(0, f - e.l) / 14) * span(f, e.s, e.l) : 0; };
  const thx = span(f, E.thx.s, E.thx.e, ease);
  const lit = (i) => span(thx, i * 0.15, i * 0.15 + 0.3);
  const cellsOn = span(f, E.cells.s, E.cells.l);
  const ppl = span(f, E.ppl.s, E.ppl.l + 10);
  const compJ = f > E.comp.s ? Math.exp(-(f - E.comp.s) / 8) * Math.abs(Math.sin((f - E.comp.s) / 3)) : 0;
  const funnel = span(f, E.narr.s, E.narr.l + 10, out) * (1 - span(f, E.rep.s, E.rep.l, ease));
  const fall = span(f, E.narr.l, E.srch.l + 20, Easing.in(Easing.quad));
  const leak = span(f, E.srch.s, E.srch.e + 10, ease);
  const dec = span(f, E.dec.s, E.dec.e + 10, ease);
  // 报纸
  const slide = span(f, E.see.s, E.see.l + 8, ease), stamp = span(f, E.head.s, E.head.l + 8, Easing.out(Easing.back(1.6)));
  const shr = span(f, E.shr.s, E.shr.l, io);
  const npx = NP.cx + 520 * (1 - slide) + (NPS.cx - NP.cx) * shr, npy = NP.cy + (NPS.cy - NP.cy) * shr;
  const nps = (1 + 0.12 * (1 - stamp) * (f >= E.head.s ? 1 : 0)) * (1 + (NPS.s - 1) * shr);
  const nprot = -2 * (1 - shr);
  const sweep = span(f, E.road.s, E.road.e + 20, ease);
  // 循环
  const loopP = span(f, E.loop.s, E.loop.l + 10, ease);
  const fastP = span(f, E.fast.s, E.fast.l + 6, ease);
  const spin = f < E.loop.l ? 0 : (f - E.loop.l) * 4 + Math.max(0, f - E.fast.s) * 18 * fastP;
  const sciP = span(f, E.sci.s, E.sci.l + 8, out);
  const col = (i) => (lit(i) > 0.5 || flash(i) > 0.35 ? RED : i === 4 && ppl > 0.5 ? SOFT : INK);
  return (
    <OnCamFrame D={D} f={f} wav="8-04_8-05_8-06_8-07.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
          {/* 路：竖线，Thanks 时从上往下变红 */}
          <path d={`M${RX},${SY[0] - 30} L${RX},${SY[0] - 30 + (SY[4] - SY[0] + 60) * route}`} stroke={INK} strokeWidth={6} strokeLinecap="round" />
          {thx > 0 && <path d={`M${RX},${SY[0] - 30} L${RX},${SY[0] - 30 + (SY[4] - SY[0] + 60) * thx}`} stroke={RED} strokeWidth={6} strokeLinecap="round" />}
          {/* road：一段红光从上往下扫 */}
          {sweep > 0 && sweep < 1 && (() => { const y = SY[0] - 30 + (SY[4] - SY[0] + 60) * sweep; return <path d={`M${RX},${Math.max(SY[0] - 30, y - 90)} L${RX},${y}`} stroke={RED} strokeWidth={8} strokeLinecap="round" />; })()}
          {SY.map((y, i) => {
            const p = span(route, i * 0.18, i * 0.18 + 0.2, out);
            const fill = lit(i) > 0.5 || (i === 2 && cellsOn > 0.5) ? RED : PAPER;
            const fl = flash(i);
            return (
              <g key={i}>
                {fl > 0.02 && <circle cx={RX} cy={y} r={16 + 26 * (1 - fl)} fill="none" stroke={RED} strokeWidth={4} opacity={fl} />}
                <circle cx={RX} cy={y} r={13 * p * (1 + 0.35 * fl + (i === 0 ? 0.4 * compJ : 0))} fill={fill} stroke={i === 4 && ppl > 0.5 && lit(4) < 0.5 ? SOFT : INK} strokeWidth={4}
                        strokeDasharray={i === 4 && ppl > 0.5 && lit(4) < 0.5 ? "5 4" : undefined} />
              </g>
            );
          })}
          {/* 图标：computer（画的显示器）、cells（三个细胞）、animals（小鼠） */}
          <g opacity={span(route, 0.05, 0.25)} transform={`translate(${IX} ${SY[0]}) scale(${1 + 0.15 * compJ}) translate(${-IX} ${-SY[0]})`}>
            <rect x={IX - 24} y={SY[0] - 22} width={48} height={34} rx={4} fill={PAPER} stroke={INK} strokeWidth={3} />
            <path d={`M${IX},${SY[0] + 12} L${IX},${SY[0] + 20} M${IX - 12},${SY[0] + 21} L${IX + 12},${SY[0] + 21}`} stroke={INK} strokeWidth={3} strokeLinecap="round" />
          </g>
          <g opacity={span(route, 0.4, 0.6)} stroke={INK} strokeWidth={2.5} fill="#E2DED4">
            {[[-12, -8], [12, -8], [0, 11]].map(([dx, dy], k) => <g key={k}><circle cx={IX + dx} cy={SY[2] + dy} r={11} /><circle cx={IX + dx} cy={SY[2] + dy} r={3.5} fill={INK} stroke="none" /></g>)}
          </g>
          <g opacity={span(route, 0.6, 0.8)}><Mouse x={IX + 2} y={SY[3] + 4} s={0.82} /></g>
          {/* cells 打勾 */}
          <path d={`M1752,${SY[2] - 2} L1764,${SY[2] + 12} L1786,${SY[2] - 16}`} fill="none" stroke={RED} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(f, E.cells.s, E.cells.l + 10)} />
          {/* 漏斗 + 点 */}
          {funnel > 0 && (
            <g opacity={funnel}>
              <path d="M1770,288 L1850,288 L1817,340 L1817,366 L1803,366 L1803,340 Z" fill="none" stroke={INK} strokeWidth={3} strokeLinejoin="round" />
              {DOTS.map((d, i) => {
                const keep = i < 3;
                const t = span(fall, d.d / 16, d.d / 16 + 0.35);
                const x = d.x + (1810 - d.x) * t, y = d.y + (330 - d.y) * t;
                const lt = keep ? span(leak, i * 0.2, i * 0.2 + 0.5) : 0;
                const op = keep ? 1 : 1 - span(t, 0.7, 1);
                return <circle key={i} cx={keep && lt > 0 ? 1810 + (i - 1) * 14 * lt : x} cy={keep && lt > 0 ? 330 + 62 * lt : y} r={5} fill={keep && lt > 0.5 ? RED : INK} opacity={span(f, E.narr.s + d.d, E.narr.s + d.d + 8) * op} />;
              })}
            </g>
          )}
          {/* flask 往下的红虚线箭头 */}
          {dec > 0 && (
            <g fill="none" stroke={RED} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round">
              <path d={`M1825,628 L1825,${628 + 200 * dec}`} strokeDasharray="10 8" />
              {dec > 0.9 && <path d="M1813,816 L1825,830 L1837,816" />}
            </g>
          )}
          {/* 循环：computer 外 */}
          {loopP > 0 && [0, 1, 2].map((k) => {
            const ghost = k === 0 ? 1 : fastP * (0.35 - 0.12 * k);
            if (ghost <= 0) return null;
            const a = spin - k * 28;
            return (
              <g key={k} transform={`rotate(${a} ${IX} ${SY[0]})`} opacity={ghost} fill="none" stroke={k === 0 ? INK : RED} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round">
                <path d={`M${IX + 42},${SY[0]} A42,42 0 1 1 ${IX + 42 * Math.cos(-0.6)},${SY[0] + 42 * Math.sin(-0.6)}`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - loopP} />
                {loopP > 0.9 && (() => { const x = IX + 42 * Math.cos(-0.6), y = SY[0] + 42 * Math.sin(-0.6); return <path d={`M${x - 14},${y - 9} L${x},${y} L${x - 15},${y + 8}`} transform={`rotate(58 ${x} ${y})`} />; })()}
              </g>
            );
          })}
        </svg>
        <Part name="cdk20" cx={IX} cy={SY[1]} w={58} at={E.card.s + 30} f={f} gate={[0.5, 0.5]} flood={14} />
        <Part name="person_w" cx={IX} cy={SY[4] - 2} w={32} at={E.card.s + 44} f={f} gate={[0.5, 1]} flood={14} />
        <Part name="flask" cx={1825} cy={590} w={40} at={E.exp.s} f={f} gate={[0.5, 1]} flood={14} />
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: sciP, transform: `translateY(${10 * (1 - sciP)}px)`}}>
          <Part name="person_w" cx={1812} cy={328} w={40} at={E.sci.s} f={f} gate={[0.5, 1]} flood={12} />
        </div>
        {ST.map((s, i) => (
          <div key={s} style={{position: "absolute", left: LX, top: SY[i] - 21, fontSize: 32, lineHeight: "40px", color: col(i), whiteSpace: "nowrap"}}>
            <Write p={span(route, i * 0.15 + 0.06, i * 0.15 + 0.3)}>{s}</Write>
          </div>
        ))}
        <Pen x={LX} y={SY[4] + 26} size={38} p={span(f, E.noty.s, E.noty.e)}>not yet</Pen>

        {/* 报纸 */}
        {f >= E.see.s && (
          <div style={{position: "absolute", left: npx - NP.w / 2, top: npy - NP.h / 2, width: NP.w, height: NP.h, transform: `scale(${nps}) rotate(${nprot}deg)`,
                       background: "#F7F3E8", border: `2.5px solid ${INK}`, borderRadius: 4, boxSizing: "border-box", boxShadow: "0 8px 18px rgba(0,0,0,0.14)"}}>
            <div style={{position: "absolute", left: 18, right: 18, top: 16, height: 10, background: INK}} />
            <div style={{position: "absolute", left: 18, right: 18, top: 32, height: 2, background: INK}} />
            <div style={{position: "absolute", left: 0, right: 0, top: 50, textAlign: "center", fontSize: 50, lineHeight: "56px", whiteSpace: "nowrap"}}>
              <div><Write p={span(f, E.hl1.s, E.hl1.e)}>AI discovers</Write></div>
              <div><Write p={span(f, E.hl2.s, E.hl2.l + 30)}>a cancer drug</Write></div>
            </div>
            <div style={{position: "absolute", left: 70, top: 166, height: 4, width: 240 * span(f, E.hl2.l + 10, E.hl2.e), background: RED}} />
            {[0, 1, 2].map((k) => <div key={k} style={{position: "absolute", left: 18, top: 188 + k * 14, width: k === 2 ? 180 : 250, height: 5, background: "#C9C4B8"}} />)}
            <div style={{position: "absolute", right: 22, top: 150, fontSize: 92, lineHeight: "92px", color: RED, opacity: span(f, E.ask.s, E.ask.l + 6),
                         transform: `scale(${1.3 - 0.3 * span(f, E.ask.s, E.ask.l + 6, out)})`}}>?</div>
          </div>
        )}
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Ren et al., Chem. Sci. 2023; Ivanenkov et al., J. Chem. Inf. Model. 2023 · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam804" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
