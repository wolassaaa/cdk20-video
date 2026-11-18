// HKBU SCIE1007 课程作业的科普视频：第 3 章二维说明书页 3-07（B 画外音）"In 2023, an AI platform called PandaOmics backed that hunch …"
// 主线物件：漏斗（PandaOmics）→ 排名表。漏斗画出、芯片盖牌 PandaOmics → 十张数据集卡片落进漏斗口，计数跳到 10 →
// 卡片上实心点（tumour）、空心点（healthy）长满，计数跳到 1,133、674 → 一叠论文飞进漏斗 →
// 小人、出口箭头、top 20 表一行行画出 → 逐行打勾 → CDK20 那一行从中间升到第一 → 红批注 no approved drug yet，药丸打斜杠，第一行红框。
// 数字 1,133 / 674 取自剧本 Visual 行（R23 Target selection）。时间全读 keys_3-07.json（事件表 映射/events/3-07.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_3-07.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const io = Easing.inOut(Easing.cubic);
// 漏斗
const MY = 360, ML = 130, MR = 830, NY = 600, NL = 440, NR = 520, SY = 690;
const FUN = `M${ML},${MY} L${NL},${NY} L${NL + 12},${SY} M${MR},${MY} L${NR},${NY} L${NR - 12},${SY}`;
const CX = 480, CY = 520;
// 卡片
const CW = 56, CH = 76, CX0 = 148, CG = 68, CTOP = 272;
const cardLand = (i) => E.ten.l + i * 8;
// 排名表
const TX = 1060, TW = 700, TY = 240, RH = 33, N = 20, C0 = 8;   // CDK20 一开始在第 9 行
const BARS = [...Array(N)].map((_, i) => 180 + ((i * 97) % 230));
const fmt = (n) => Math.round(n).toLocaleString("en-US");

const Scene = () => {
  const f = useCurrentFrame();
  const fun = span(f, E.ai.s, E.ai.l + 10, ease);
  const glow = f > E.backed.s ? Math.max(0, Math.sin(Math.PI * span(f, E.backed.s, E.backed.s + 40))) : 0;
  const comb = span(f, E.backed.s, E.backed.l + 14, out);
  const landed = [...Array(10)].filter((_, i) => f >= cardLand(i)).length;
  const tum = span(f, E.thou.s, E.thou.l + 24, out), hea = span(f, E.hund.s, E.hund.l + 24, out);
  const pap = span(f, E.papers.s, E.papers.l, io), sink = span(f, E.papers.l, E.papers.l + 22, Easing.in(Easing.quad));
  const arrow = span(f, E.checked.s, E.checked.l + 10, ease);
  const frame = span(f, E.top.s, E.top.l + 12, ease);
  const pop = span(f, E.came.s, E.came.l, out) * (1 - span(f, E.top2.l, E.top2.l + 16, ease));
  const rise = span(f, E.top2.s, E.top2.l, io);
  // 第 r 行（行号 r = 原始位置）当前在第几位
  const slot = (r) => (r === C0 ? C0 - C0 * rise : r < C0 ? r + rise : r);
  const tickAt = (k) => E.hand.l + k * 3;           // 按位置逐行打勾
  const yetBox = span(f, E.yet.s, E.yet.l + 6, ease);
  const bead = [[0, 130, 96], [E.title.l, 800, 96], [E.ai.l, 1000, 420], [E.panda.l, 720, 560], [E.backed.l, 360, 640], [E.ten.l, 930, 300],
                [E.sets.l, 940, 200], [E.thou.l, 930, 420], [E.hund.l, 980, 300], [E.papers.l, 230, 560], [E.people.l, 760, 900], [E.checked.l, 800, 760],
                [E.top.l, 1000, 190], [E.twenty.l, 1820, 600], [E.hand.l, 1000, 700], [E.cdk.l, 1820, 520], [E.top2.l, 1820, 257],
                [E.no.l, 1000, 205], [E.drug.l, 1810, 150], [E.yet.l, 1820, 330], [K.len_f, 1821, 331]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("3-07.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>In 2023, an AI platform</Write></div>

      {/* 计数行 */}
      <div style={{position: "absolute", left: 140, top: 186, fontSize: 28, whiteSpace: "nowrap", opacity: span(f, E.ten.s, E.ten.l)}}>
        <span style={{color: RED}}>{landed}</span> <Write p={span(f, E.sets.s, E.sets.l + 14)}>data sets</Write></div>
      <div style={{position: "absolute", left: 345, top: 186, fontSize: 28, whiteSpace: "nowrap", opacity: span(f, E.thou.s, E.thou.s + 6)}}>
        <span style={{color: RED}}>{fmt(1133 * tum)}</span> <Write p={span(f, E.samp.s, E.samp.l + 12)}>tumour</Write></div>
      <div style={{position: "absolute", left: 555, top: 186, fontSize: 28, whiteSpace: "nowrap", opacity: span(f, E.hund.s, E.hund.s + 6)}}>
        <span style={{color: RED}}>{fmt(674 * hea)}</span> <Write p={span(f, E.healthy.s, E.healthy.l + 12)}>healthy</Write></div>
      <div style={{position: "absolute", left: 750, top: 186, fontSize: 28, whiteSpace: "nowrap"}}>
        <Write p={span(f, E.plus.s, E.plus.l + 4)}>+</Write> <Write p={span(f, E.papers.s, E.papers.l)}>papers</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 漏斗 */}
        <path d={FUN} fill="none" stroke={glow > 0.05 ? RED : INK} strokeWidth={4} strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fun} />
        {/* 梳齿：漏斗口一排短线 */}
        {comb > 0 && [...Array(9)].map((_, i) => {
          const x = CX0 + CW + 6 + i * CG, y = MY + 16;
          return <line key={i} x1={x} y1={y} x2={x} y2={y + 26 * span(comb, i * 0.05, i * 0.05 + 0.5)} stroke={SOFT} strokeWidth={3} strokeLinecap="round" />;
        })}
        {/* 卡片 */}
        {[...Array(10)].map((_, i) => {
          const t = span(f, cardLand(i) - 14, cardLand(i), Easing.in(Easing.quad));
          if (t <= 0) return null;
          const x = CX0 + i * CG, y = CTOP - 90 * (1 - t), rot = (1 - t) * (i % 2 ? 14 : -14);
          const nT = Math.round(12 * span(tum, i * 0.05, i * 0.05 + 0.55)), nH = Math.round(8 * span(hea, i * 0.05, i * 0.05 + 0.55));
          return (
            <g key={i} transform={`rotate(${rot} ${x + CW / 2} ${y + CH / 2})`} opacity={span(t, 0, 0.3)}>
              <rect x={x} y={y} width={CW} height={CH} rx={5} fill="#F4F1EA" stroke={INK} strokeWidth={2.5} />
              {[...Array(nT)].map((_, k) => <circle key={k} cx={x + 10 + (k % 4) * 12} cy={y + 12 + Math.floor(k / 4) * 12} r={3.6} fill={INK} />)}
              {[...Array(nH)].map((_, k) => <circle key={k} cx={x + 10 + (k % 4) * 12} cy={y + 48 + Math.floor(k / 4) * 12} r={3.6} fill="none" stroke={INK} strokeWidth={1.6} />)}
            </g>
          );
        })}
        {/* 出口箭头 → 表 */}
        {arrow > 0 && (
          <g fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round">
            <path d={`M${CX},${SY + 14} C${CX},800 860,800 ${TX - 30},560`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - arrow} />
            {arrow > 0.95 && <path d={`M${TX - 52},562 L${TX - 30},560 L${TX - 40},580`} />}
          </g>
        )}
        {/* 表框和行 */}
        {frame > 0 && (
          <g fill="none" stroke={INK} strokeWidth={2.5}>
            <rect x={TX} y={TY - 8} width={TW} height={N * RH + 16} rx={8} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - frame} />
          </g>
        )}
        {[...Array(N)].map((_, r) => {
          const g = span(f, E.twenty.s + r * 3, E.twenty.s + r * 3 + 10, out);
          if (g <= 0) return null;
          const y = TY + slot(r) * RH + RH / 2;
          const k = Math.round(slot(r));
          const tick = r === C0 ? span(f, tickAt(C0), tickAt(C0) + 6) : span(f, tickAt(r), tickAt(r) + 6);
          const isC = r === C0;
          return (
            <g key={r} transform={`translate(${isC ? 24 * pop : 0} 0)`}>
              {!isC && <line x1={TX + 80} y1={y} x2={TX + 80 + BARS[r] * g} y2={y} stroke={SOFT} strokeWidth={6} strokeLinecap="round" opacity={0.55} />}
              {tick > 0 && <path d={`M${TX + TW - 60},${y} L${TX + TW - 52},${y + 8} L${TX + TW - 36},${y - 10}`} fill="none" stroke={RED} strokeWidth={3.5}
                                 strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - tick} />}
              {k === 0 && yetBox > 0 && <rect x={TX + 10} y={y - RH / 2 + 1} width={(TW - 20) * yetBox} height={RH - 2} rx={4} fill="none" stroke={RED} strokeWidth={3} />}
            </g>
          );
        })}
      </svg>
      {/* 行号（固定）和 CDK20 字 */}
      {[...Array(N)].map((_, i) => (
        <div key={i} style={{position: "absolute", left: TX + 14, top: TY + i * RH + 4, width: 40, textAlign: "right", fontSize: 20, color: SOFT,
                             opacity: span(f, E.twenty.s + i * 3, E.twenty.s + i * 3 + 8)}}>{i + 1}</div>
      ))}
      {f >= E.cdk.s && (
        <div style={{position: "absolute", left: TX + 80 + 24 * pop, top: TY + slot(C0) * RH + 1, fontSize: 27, lineHeight: "31px", color: INK,
                     background: `rgba(200,16,46,${0.12 * span(f, E.cdk.s, E.cdk.l)})`, padding: "0 10px", borderRadius: 4}}>
          <Write p={span(f, E.cdk.s, E.cdk.l + 8)}>CDK20</Write></div>
      )}
      <Label x={TX} y={TY - 62} w={200} size={30} align="left" p={span(f, E.top.s, E.twenty.l)}>top 20</Label>

      {/* 芯片 + 盖牌 */}
      <div style={{filter: glow > 0.02 ? `drop-shadow(0 0 ${16 * glow}px rgba(200,16,46,0.6))` : "none"}}>
        <Part name="chip" cx={CX} cy={CY} w={120} at={E.ai.s + 8} f={f} gate={[0.5, 0.5]} />
      </div>
      <div style={{position: "absolute", left: CX - 74, top: CY - 17, width: 148, height: 34, background: "#2B2B2D", borderRadius: 4, opacity: span(f, E.panda.s, E.panda.s + 6)}} />
      <div style={{position: "absolute", left: CX - 74, top: CY - 17, width: 148, textAlign: "center", font: "22px/34px Serif", color: "#E8E4DA"}}>
        <Write p={span(f, E.panda.s + 2, E.panda.l + 8)}>PandaOmics</Write></div>

      {/* 论文 */}
      {f >= E.papers.s && sink < 1 && (
        <div style={{position: "absolute", left: 0, top: 0, opacity: 1 - span(sink, 0.6, 1),
                     transform: `translate(${(60 - CX) * (1 - pap)}px, ${(820 - 440) * (1 - pap) + 80 * sink}px) scale(${1 - 0.6 * sink})`, transformOrigin: `${CX}px 440px`}}>
          <Part name="paper1" cx={CX} cy={440} w={70} at={-100} f={0} />
          <Part name="paper1" cx={CX + 10} cy={432} w={70} at={-100} f={0} />
        </div>
      )}

      {/* 小人和他的勾 */}
      <Part name="person_w" cx={950} cy={880} w={80} at={E.people.s} f={f} gate={[0.5, 1]} />
      <Label x={950} y={958} w={200} size={24} color={SOFT} p={span(f, E.hand.s, E.hand.l + 12)}>by hand</Label>

      {/* 批注 */}
      <Pen x={1290} y={168} p={span(f, E.no.s, E.drug.s)} size={40} rot={-3}>no approved drug yet</Pen>
      <Part name="capsule" cx={1700} cy={190} w={70} at={E.drug.s} f={f} gate={[0.5, 0.5]} />
      {f >= E.drug.l - 4 && (
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <line x1={1668} y1={222} x2={1668 + 64 * span(f, E.drug.l - 4, E.drug.l + 6, out)} y2={222 - 64 * span(f, E.drug.l - 4, E.drug.l + 6, out)} stroke={RED} strokeWidth={5} strokeLinecap="round" />
        </svg>
      )}

      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual307" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
