// HKBU SCIE1007 课程作业的科普视频：第 5 章二维说明书页 5-04（C 画外音）"But then came a second test … IC50 … For 001? Above 6,000 nanomolar. Weak."
// 主线：左边锁（CDK20）和钥匙 001（同 3-01 的锁和钥匙）+ 锁旁一个齿轮（CDK20 在工作）；右边一张示意图（activity 对 how much you need）。
// grabbing 钥匙滑进锁；isn't the same 红不等号；jamming 钥匙想转只是晃；working 齿轮转、红问号；IC50 一条普通曲线，点往下滑到一半，虚线落到横轴标 IC50；
// For 001 一条红线一直很高，一半处跑到图外，写 above 6,000 nanomolar，红批注 weak，齿轮还在转。数字只写旁白说的 6,000。
// 时间全读 keys_5-04.json（事件表 映射/events/5-04.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_5-04.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const LK = {cx: 440, cy: 540, w: 220};
const KY = 600, KS = 120, KE = 320;              // 钥匙：从 cx 120 滑到 320（尖端在锁后面）
const GR = [640, 420];                            // 齿轮
const OX = 960, OY = 800, XR = 1700, TOP = 360, HALF = 580;   // 图
const gen = (x) => TOP + (OY - TOP) / (1 + Math.exp(-(x - 1250) / 55));
const red = (x) => TOP - 16 + (OY - TOP) / (1 + Math.exp(-(x - 1960) / 55));
const pathOf = (fn, x0, x1) => [...Array(61)].map((_, i) => { const x = x0 + (x1 - x0) * i / 60; return `${i ? "L" : "M"}${x.toFixed(1)},${fn(x).toFixed(1)}`; }).join(" ");

const Gear = ({x, y, a, s}) => (
  <g transform={`translate(${x} ${y}) rotate(${a}) scale(${s})`} fill={PAPER} stroke={INK} strokeWidth={3.5} strokeLinejoin="round">
    <path d={[...Array(10)].map((_, i) => { const a0 = i * Math.PI / 5, a1 = a0 + Math.PI / 10; const p = (r, t) => `${(r * Math.cos(t)).toFixed(1)},${(r * Math.sin(t)).toFixed(1)}`;
      return `${i ? "L" : "M"}${p(36, a0 - 0.12)} L${p(48, a0 - 0.08)} L${p(48, a0 + 0.2)} L${p(36, a0 + 0.24)} L${p(36, a1 + 0.1)}`; }).join(" ") + " Z"} />
    <circle r={13} />
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const io = Easing.inOut(Easing.cubic);
  const grab = span(f, E.grab.s, E.grab.l, io);
  const kx = KS + (KE - KS) * grab;
  const lockJ = f > E.lock.s ? Math.exp(-(f - E.lock.s) / 5) * Math.sin((f - E.lock.s) / 1.6) * 1.8 : 0;
  const jam = f >= E.jam.s ? Math.sin((f - E.jam.s) / 3.2) * 5 * Math.exp(-Math.max(0, f - E.jam.l) / 40) : 0;
  const wob = f >= E.jam.s ? span(f, E.jam.s, E.jam.l + 6) * (0.4 + 0.6 * Math.exp(-Math.max(0, f - E.jam.l) / 50)) : 0;
  const gear = span(f, E.stop.s, E.stop.l + 10, Easing.out(Easing.back(1.6)));
  const ga = f < E.work.s ? 0 : (f - E.work.s) * 2.4;
  const ax = span(f, E.axes.s, E.axes.l + 16, ease);
  const gc = span(f, E.ic.s, E.ic.l + 30, ease);
  const dot = span(f, E.cut.s, E.half.s, io);
  const half = span(f, E.half.s, E.half.l + 14, ease);
  const rc = span(f, E.q.s + 6, E.above.l + 10, ease);
  const arr = span(f, E.above.l, E.above.l + 20, ease);
  const dx = 980 + (1250 - 980) * dot;
  const bead = [[0, 800, 200], [E.title.l, 760, 100], [E.grab.l, 120, 760], [E.lock.l, 600, 760], [E.neq.l, 800, 240], [E.jam.l, 110, 480],
                [E.k001.l, 330, 770], [E.stop.l, 770, 430], [E.cdk.l, 620, 770], [E.work.l, 780, 560], [E.axes.l, 900, 870],
                [E.ic.l, 1520, 225], [E.much.l, 1790, 800], [E.cut.l, 1100, 660], [E.half.l, 880, 660], [E.q.l, 1800, 540],
                [E.above.l, 1810, 240], [E.weak.l, 1800, 620], [K.len_f, 1801, 621]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("5-04.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e + 20)}>A second test</Write></div>

      {/* 钥匙在锁后面 */}
      {f >= E.grab.s - 10 && (
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${kx + 120}px ${KY}px`, transform: `rotate(${jam}deg)`, opacity: span(f, E.grab.s - 10, E.grab.s)}}>
          <Part name="key" cx={kx} cy={KY} w={260} at={E.grab.s - 10} f={f} gate={[0, 0.5]} flood={14} />
        </div>
      )}
      <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${LK.cx}px ${LK.cy}px`, transform: `rotate(${lockJ + jam * 0.25}deg)`}}>
        <Part name="lock" cx={LK.cx} cy={LK.cy} w={LK.w} at={E.grab.s - 30} f={f} gate={[0.5, 1]} />
      </div>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 晃动线 */}
        {wob > 0 && [0, 1, 2].map((k) => (
          <path key={k} d={`M${150 - 14 * k},${560 - 10 * k} q-16,40 0,80`} fill="none" stroke={RED} strokeWidth={3.5} strokeLinecap="round" opacity={wob * (1 - 0.25 * k)} transform={`translate(${-3 * Math.sin(f / 3 + k)} 0)`} />
        ))}
        {/* 不等号 */}
        {f >= E.neq.s && <g stroke={RED} strokeWidth={5} strokeLinecap="round">
          <path d={`M452,236 L${452 + 40 * span(f, E.neq.s, E.neq.s + 8)},236 M452,252 L${452 + 40 * span(f, E.neq.s + 4, E.neq.s + 12)},252`} />
          <path d={`M484,222 L${484 - 24 * span(f, E.neq.s + 10, E.neq.l + 6)},${222 + 44 * span(f, E.neq.s + 10, E.neq.l + 6)}`} />
        </g>}
        {gear > 0 && <Gear x={GR[0]} y={GR[1]} a={ga} s={gear} />}
        {/* 图 */}
        {ax > 0 && <g stroke={INK} strokeWidth={4} strokeLinecap="round" fill="none">
          <path d={`M${OX},${OY - (OY - 300) * span(ax, 0, 0.5)} L${OX},${OY}`} />
          <path d={`M${OX},${OY} L${OX + (XR + 20 - OX) * span(ax, 0.3, 1)},${OY}`} />
        </g>}
        {f >= E.much.s && (() => { const p = span(f, E.much.s, E.much.l + 14, ease), x = OX + 40 + (XR - OX - 20) * p; return (
          <g stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" strokeLinejoin="round"><path d={`M${x - 16},${OY - 12} L${x + 2},${OY} L${x - 16},${OY + 12}`} /></g>); })()}
        {gc > 0 && <path d={pathOf(gen, OX + 10, XR)} fill="none" stroke={rc > 0.3 ? SOFT : INK} strokeWidth={4} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - gc} />}
        {f >= E.cut.s && <circle cx={dx} cy={gen(dx)} r={11} fill={INK} />}
        {half > 0 && <g stroke={INK} strokeWidth={3} strokeDasharray="10 8" fill="none">
          <path d={`M${OX},${HALF} L${OX + (1250 - OX) * span(half, 0, 0.5)},${HALF}`} />
          {half > 0.5 && <path d={`M1250,${HALF} L1250,${HALF + (OY - HALF) * span(half, 0.5, 1)}`} />}
        </g>}
        {rc > 0 && <path d={pathOf(red, OX + 10, XR)} fill="none" stroke={RED} strokeWidth={5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - rc} />}
        {arr > 0 && <g stroke={RED} strokeWidth={4} fill="none" strokeLinecap="round" strokeLinejoin="round">
          <path d={`M${XR + 6},${red(XR)} L${XR + 6 + 90 * arr},${red(XR)}`} strokeDasharray="8 7" />
          {arr > 0.9 && <path d={`M${XR + 82},${red(XR) - 12} L${XR + 98},${red(XR)} L${XR + 82},${red(XR) + 12}`} />}
        </g>}
      </svg>
      <Label x={300} y={212} w={220} size={40} p={span(f, E.grab.s, E.grab.e + 10)}>grabbing</Label>
      <Label x={630} y={212} w={220} size={40} p={span(f, E.jam.s, E.jam.e)}>jamming</Label>
      <Label x={228} y={650} w={120} size={34} color={RED} p={span(f, E.k001.s, E.k001.l + 14)}>001</Label>
      <Label x={LK.cx} y={712} w={200} size={34} p={span(f, E.cdk.s, E.cdk.e)}>CDK20</Label>
      <div style={{position: "absolute", left: 694, top: 300, fontSize: 72, lineHeight: "72px", color: RED, opacity: span(f, E.work.s, E.work.l + 8)}}>?</div>

      <Label x={OX} y={256} w={200} size={32} italic p={span(f, E.axes.s, E.axes.e)}>activity</Label>
      <Label x={1330} y={210} w={220} size={46} p={span(f, E.ic.s, E.ic.e)}>IC50</Label>
      <Label x={1500} y={818} w={300} size={32} italic p={span(f, E.much.s, E.much.e)}>how much you need</Label>
      <Label x={880} y={HALF - 20} w={120} size={30} italic p={span(f, E.half.s, E.half.e)}>in half</Label>
      <Label x={1250} y={818} w={120} size={30} p={span(f, E.half.l, E.half.l + 16)}>IC50</Label>
      <div style={{position: "absolute", left: 1740, top: 400, fontSize: 72, lineHeight: "72px", color: RED, opacity: span(f, E.q.s, E.q.l + 6)}}>?</div>
      <div style={{position: "absolute", left: 1400, top: 290, width: 390, textAlign: "right", fontSize: 34, color: RED}}><Write p={span(f, E.above.s, E.above.e)}>above 6,000 nanomolar</Write></div>
      <Pen x={1560} y={440} size={56} p={span(f, E.weak.s, E.weak.l + 6)}>weak</Pen>

      <Source p={span(f, E.grab.l, E.grab.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual504" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
