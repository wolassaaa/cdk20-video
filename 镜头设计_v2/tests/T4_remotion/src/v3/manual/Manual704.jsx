// HKBU SCIE1007 课程作业的科普视频：第 7 章二维说明书页 7-04（画外音）：把两条路线放在同一条起跑线上赛一场。
// 两条并排的跑道（AI route / classic route）；起跑线前依次写出 same target / same budget / same definition of a hit，
// 每写一个，两道各点亮一个相同的图标（锁 / 钞票 / 清单）；两个小牌子起跑，终点线上画红问号，红批注 how much faster。
// 时间全读 keys_7-04.json（事件表 映射/events/7-04.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_7-04.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const LA = 390, LB = 710, LH = 200;                  // 两条跑道的中线、跑道高度
const IX = [420, 680, 940];                          // 三个图标（和上面的字）的 x
const SL = 1180, FIN = 1700;                         // 起跑线、终点线
const draw = (p) => ({pathLength: 1, strokeDasharray: "1 1", strokeDashoffset: 1 - p});
const ICON = [{name: "lock", w: 90, ev: "tgt"}, {name: "banknote", w: 130, ev: "bud"}, {name: "checklist", w: 90, ev: "def"}];

const Scene = () => {
  const f = useCurrentFrame();
  const lanes = span(f, E.lanes.s, E.lanes.l + 10, ease), start = span(f, E.start.s, E.start.l + 8, ease), fin = span(f, E.fin.s, E.fin.l + 10, ease);
  const ring = span(f, E.hit.s, E.hit.l + 10, ease);
  const run = span(f, E.run.s, K.len_f - 40, Easing.inOut(Easing.quad));
  const tagAi = 1140 + 460 * run, tagCl = 1110 + 220 * run;
  const bead = [[0, 130, 96], [E.title.l, 760, 96], [E.lanes.l, 1830, 240], [E.ai.l, 330, 262], [E.cl.l, 230, 560], [E.start.l, SL, 262], [E.tgt.l, IX[0], 510], [E.bud.l, IX[1], 510],
                [E.def.l, IX[2], 510], [E.hit.l, 1120, 510], [E.fin.l, 1800, 550], [E.run.l, 1250, 560], [E.qm.l, 1500, 545], [K.len_f, 1501, 546]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("7-04.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>Three: race them</Write></div>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {[LA, LB].map((y, i) => <rect key={i} x={100} y={y - LH / 2} width={1680} height={LH} rx={14} fill="none" stroke={INK} strokeWidth={3} {...draw(span(lanes, i * 0.3, 0.7 + i * 0.3))} />)}
        {/* 起跑线、终点线 */}
        {start > 0 && [LA, LB].map((y, i) => <path key={i} d={`M${SL},${y - LH / 2 + 10} L${SL},${y - LH / 2 + 10 + (LH - 20) * start}`} stroke={INK} strokeWidth={5} strokeLinecap="round" fill="none" />)}
        {fin > 0 && [LA, LB].map((y, i) => <path key={i} d={`M${FIN},${y - LH / 2 + 10} L${FIN},${y - LH / 2 + 10 + (LH - 20) * fin}`} stroke={INK} strokeWidth={5} strokeDasharray="12 9" fill="none" />)}
        {/* hit：两张清单各圈一下 */}
        {ring > 0 && [LA, LB].map((y, i) => <ellipse key={i} cx={IX[2]} cy={y} rx={62} ry={82} fill="none" stroke={RED} strokeWidth={4} {...draw(ring)} />)}
        {/* 小牌子 */}
        {f >= E.fin.s && [[LA, tagAi, 80, "AI", INK], [LB, tagCl, 140, "classic", INK]].map(([y, x, w, t], i) => {
          const p = span(f, E.fin.s + i * 4, E.fin.l + i * 4, Easing.out(Easing.back(1.6)));
          return <g key={t} transform={`translate(${x} ${y}) scale(${p})`}>
            <rect x={-w / 2} y={-22} width={w} height={44} rx={8} fill={i === 0 ? RED : INK} />
            <text x={0} y={10} textAnchor="middle" fontFamily="Serif" fontSize={30} fill={PAPER}>{t}</text></g>;
        })}
      </svg>
      <Label x={120} y={LA - 22} w={220} align="left" size={38} p={span(f, E.ai.s, E.ai.l + 12)}>AI route</Label>
      <Label x={120} y={LB - 22} w={220} align="left" size={38} p={span(f, E.cl.s, E.cl.l + 12)}>classic route</Label>
      {/* 起跑线前的三个词，每个词写出时，两道各点亮一个相同图标 */}
      <Label x={IX[0]} y={530} w={200} size={30} p={span(f, E.tgt.s, E.tgt.l + 14)}>same target</Label>
      <Label x={IX[1]} y={530} w={200} size={30} p={span(f, E.bud.s, E.bud.l + 14)}>same budget</Label>
      <Label x={IX[2]} y={530} w={340} size={30} p={span(f, E.def.s, E.hit.l)}>same definition of a hit</Label>
      {ICON.map((ic, k) => [LA, LB].map((y, i) => <Part key={k + "_" + i} name={ic.name} cx={IX[k]} cy={y} w={ic.w} at={E[ic.ev].l + 10 * i} f={f} gate={[0.5, 0.5]} />))}
      {/* 终点：红问号，how much faster */}
      <div style={{position: "absolute", left: FIN - 50, top: 502, width: 100, textAlign: "center", fontSize: 100, lineHeight: "100px", color: RED, opacity: fin, transform: `scale(${0.6 + 0.4 * fin})`}}>?</div>
      <Pen x={1150} y={516} size={46} rot={-2} p={span(f, E.qm.s, E.qm.e)}>how much faster?&nbsp;</Pen>
      <Source p={span(f, E.title.l, E.title.l + 20)}>Our proposal · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual704" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
