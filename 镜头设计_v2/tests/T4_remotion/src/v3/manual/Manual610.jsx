// HKBU SCIE1007 课程作业的科普视频：第 6 章二维说明书页 6-10（画外音）：048 在路上的哪一站。
// 七站路（照 Manual208 的路线）；主线物件是 048 小牌子：落在起点，逐站走到 Target、Hit、Improve、Cells；
// 每到一站，该站上方长出一个图标，前几站打勾、Improve 写 started、Cells 写 first tests 再打勾；Animals 和 Trials 变灰，写 not yet。
// 时间全读 keys_6-10.json（事件表 映射/events/6-10.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_6-10.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"];
const RX0 = 230, RX1 = 1690, RY = 660;
const sx = (i) => RX0 + ((RX1 - RX0) * i) / (ST.length - 1);
const GREY = "#8A867C";
const TAGX = [140, sx(0), sx(1), sx(2), sx(3)];                       // 牌子的站位：起点，Target，Hit，Improve，Cells
const draw = (p) => ({pathLength: 1, strokeDasharray: "1 1", strokeDashoffset: 1 - p});

const Tick = ({x, y, p}) => p > 0 ? <path d="M-16,0 L-5,13 L17,-15" transform={`translate(${x} ${y})`} fill="none" stroke={RED} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" {...draw(p)} /> : null;

const Scene = () => {
  const f = useCurrentFrame();
  const road = span(f, E.road.s, E.road.l, ease);
  const tagP = span(f, E.tag.s, E.tag.l, Easing.out(Easing.back(1.6)));
  let tx = TAGX[0];
  [E.tgt, E.hit, E.imp, E.cells].forEach((ev, i) => { if (f >= ev.s) tx = TAGX[i] + (TAGX[i + 1] - TAGX[i]) * span(f, ev.s, ev.l, ease); });
  const hop = (ev) => (f >= ev.s && f <= ev.l ? Math.sin(Math.PI * span(f, ev.s, ev.l)) * 18 : 0);
  const hy = Math.max(hop(E.tgt), hop(E.hit), hop(E.imp), hop(E.cells));
  const tk = {tgt: span(f, E.tgtk.s, E.tgtk.l + 10, ease), hit: span(f, E.hitk.s, E.hitk.l + 10, ease), cells: span(f, E.done.s, E.done.l + 10, ease)};
  const g1 = f >= E.g1.l, g2 = f >= E.g2.l;
  const grey = [false, false, false, false, g1, g2, false];
  const bracket = span(f, E.ny.s, E.ny.l + 8, ease);
  const bead = [[0, 130, 96], [E.title.l, 700, 96], [E.tag.l, 140, RY - 170], [E.road.l, 1760, RY - 120], [E.tgt.l, sx(0) + 110, RY - 200], [E.tgtk.l, sx(0) + 80, RY + 150],
                [E.hit.l, sx(1) + 120, RY - 200], [E.hitk.l, sx(1) + 80, RY + 150], [E.imp.l, sx(2) + 120, RY - 200], [E.st.l, sx(2) + 110, RY + 150], [E.cells.l, sx(3) + 120, RY - 200],
                [E.ft.l, sx(3) + 100, RY + 105], [E.done.l, sx(3) + 80, RY + 150], [E.g1.l, sx(4), RY - 150], [E.g2.l, sx(5), RY - 150], [E.ny.l, 1325, RY + 190], [K.len_f, 1326, RY + 191]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("6-10.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>Where's 048 on the road?</Write></div>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <path d={`M${RX0 - 110},${RY} L${RX1 + 60},${RY}`} fill="none" stroke={INK} strokeWidth={7} strokeLinecap="round" {...draw(road)} />
        {ST.map((s, i) => {
          const p = span(road, (i + 0.4) / (ST.length + 0.6), (i + 1.2) / (ST.length + 0.6), out);
          return <circle key={s} cx={sx(i)} cy={RY} r={16 * p} fill={i < 3 && f >= [E.tgt, E.hit, E.imp][i].l ? RED : PAPER} stroke={grey[i] ? "#9A968C" : INK} strokeWidth={4} />;
        })}
        <Tick x={sx(0)} y={RY + 148} p={tk.tgt} />
        <Tick x={sx(1)} y={RY + 148} p={tk.hit} />
        <Tick x={sx(3)} y={RY + 148} p={tk.cells} />
        {bracket > 0 && <path d={`M${sx(4) - 40},${RY + 96} L${sx(4) - 40},${RY + 108} L${sx(5) + 40},${RY + 108} L${sx(5) + 40},${RY + 96}`} fill="none" stroke={SOFT} strokeWidth={3} {...draw(bracket)} />}
        {/* 048 小牌子 */}
        {tagP > 0 && <g transform={`translate(${tx} ${RY - 74 - hy}) scale(${tagP})`}>
          <rect x={-62} y={-28} width={124} height={56} rx={9} fill={INK} />
          <path d="M-11,28 L0,44 L11,28 Z" fill={INK} />
          <text x={0} y={13} textAnchor="middle" fontFamily="Serif" fontSize={40} fill={PAPER}>048</text>
        </g>}
      </svg>
      {ST.map((s, i) => (
        <Label key={s} x={sx(i)} y={RY + 30} w={180} size={30} color={grey[i] ? GREY : INK} p={span(road, (i + 0.6) / (ST.length + 0.6), (i + 1.4) / (ST.length + 0.6))}>{s}</Label>
      ))}
      {/* 每到一站，上方长出一个图标 */}
      <Part name="lock" cx={sx(0)} cy={RY - 200} w={120} at={E.tgt.l} f={f} gate={[0.5, 1]} />
      <Part name="key" cx={sx(1)} cy={RY - 190} w={150} at={E.hit.l} f={f} gate={[0, 0.5]} />
      <Part name="flask" cx={sx(2)} cy={RY - 200} w={100} at={E.imp.l} f={f} gate={[0.5, 1]} />
      <Part name="tubes" cx={sx(3)} cy={RY - 200} w={140} at={E.cells.l} f={f} gate={[0.5, 1]} />
      <Label x={sx(0)} y={RY + 84} w={160} size={28} italic color={SOFT} p={span(f, E.tgtk.s, E.tgtk.e)}>found</Label>
      <Label x={sx(1)} y={RY + 84} w={160} size={28} italic color={SOFT} p={span(f, E.hitk.s, E.hitk.e)}>found</Label>
      <Pen x={sx(2) - 60} y={RY + 78} size={42} rot={-3} p={span(f, E.st.s, E.st.e)}>started&nbsp;</Pen>
      <Label x={sx(3)} y={RY + 84} w={200} size={28} italic color={SOFT} p={span(f, E.ft.s, E.ft.e)}>first tests</Label>
      <Pen x={sx(4) + 62} y={RY + 118} size={44} rot={-2} p={span(f, E.ny.s, E.ny.e)}>not yet&nbsp;</Pen>
      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual610" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
