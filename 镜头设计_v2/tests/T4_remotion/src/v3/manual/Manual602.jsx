// HKBU SCIE1007 课程作业的科普视频：第 6 章二维说明书页 6-02（画外音）：第一行 Seeing the lock。左栏烧瓶加 expensive / slow / difficult，右栏文件落进格子 a free prediction，再从 public database 下载，两栏之间一个右箭头。
// 记分板组（6-01 到 6-08 同一张表、同一套坐标）；前面几段已画完的行在这里直接按画完的样子摆好，本段的行跟着旁白画。
// 时间全读 keys_6-02.json（事件表 映射/events/6-02.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_6-02.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Arrow, Write, Bead, evMap, Label, Pen, PageFrame, Source, Plate} from "./kit.jsx";

const E = evMap(K);
const FZ = new Proxy({}, {get: () => ({s: 0, l: 0, e: 0})});   // 前几段已经画完的内容：时间全 0，f 取很大，直接是画完的样子
const DONE = 1e6;
const RT0 = 245, RH = 165, T = (i) => RT0 + RH * i;          // 记分板四行：行顶 245 / 410 / 575 / 740，行高 165
const rnd = (k) => { const v = Math.sin(k * 12.9898) * 43758.5453; return v - Math.floor(v); };
const PAPER2 = "#F4F1EA";

const Tint = ({x, y, w, h, p}) => <div style={{position: "absolute", left: x, top: y, width: w, height: h, background: "rgba(31,30,28,0.06)", opacity: p, borderRadius: 4}} />;
const Svg = ({children}) => <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>{children}</svg>;
const draw = (p) => ({pathLength: 1, strokeDasharray: "1 1", strokeDashoffset: 1 - p});

// 记分板外框：中缝竖线先长出，外框从中缝向两边推开，表头线、行线、Before / Now 表头
const Board = ({f, E, dash = 0}) => {
  const sp = span(f, E.seam.s, E.seam.l, ease);
  const fr = span(f, E.frame.s, E.frame.l, ease);
  const x0 = 960 - 864 * fr, x1 = 960 + 860 * fr;
  return (
    <>
      <Svg>
        {sp > 0 && <line x1={960} x2={960} y1={540 - 365 * sp} y2={540 + 365 * sp} stroke={INK} strokeWidth={3} />}
        {dash > 0 && <g><line x1={960} x2={960} y1={175} y2={905} stroke={PAPER} strokeWidth={7} />
          <line x1={960} x2={960} y1={175} y2={175 + 730 * dash} stroke={RED} strokeWidth={3.5} strokeDasharray="14 10" /></g>}
        {fr > 0 && <g fill="none" stroke={INK} strokeWidth={3} strokeLinecap="round">
          <rect x={x0} y={175} width={x1 - x0} height={730} rx={6} />
          <line x1={x0} x2={x1} y1={245} y2={245} />
          {x0 <= 362 && <line x1={360} x2={360} y1={175} y2={905} opacity={span(fr, 0.7, 0.8)} />}
        </g>}
        {[1, 2, 3].map((i) => {
          const p = span(f, E.rows.s + 7 * (i - 1), E.rows.s + 7 * (i - 1) + 14, ease);
          return p > 0 ? <line key={i} x1={96} x2={96 + 1724 * p} y1={T(i)} y2={T(i)} stroke={INK} strokeWidth={2} opacity={0.7} /> : null;
        })}
      </Svg>
      <Label x={660} y={181} w={200} size={44} p={span(f, E.bef.s, E.bef.l + 6)}>Before</Label>
      <Label x={1390} y={181} w={200} size={44} p={span(f, E.now.s, E.now.l + 8)}>Now</Label>
    </>
  );
};

const TitleFinal = () => (
  <div style={{position: "absolute", left: 96, top: 62, fontSize: 56, whiteSpace: "nowrap"}}>
    How much did the computers <span style={{position: "relative"}}>actually help?<span style={{position: "absolute", left: 0, right: 0, bottom: 2, height: 4, background: RED}} /></span>
  </div>
);

// ---- 第一行：Seeing the lock ----
const Row1 = ({f, E}) => {
  const t = T(0), c = t + 82;
  const dash = span(f, E.dash.s, E.dash.l + 6, out), cr = span(f, E.cross.s, E.cross.l + 6, out);
  const fp = span(f, E.file.s, E.file.l, Easing.out(Easing.back(1.3))), pub = span(f, E.pub.s, E.pub.l + 8, Easing.out(Easing.back(1.4)));
  return (
    <>
      <Tint x={372} y={t + 3} w={576} h={RH - 6} p={span(f, E.bef.s, E.bef.l + 10)} />
      <Tint x={972} y={t + 3} w={836} h={RH - 6} p={span(f, E.now.s, E.now.l + 10)} />
      <Label x={110} y={t + 12} w={250} align="left" size={32} p={span(f, E.lbl.s, E.lbl.l)}>Seeing the lock</Label>
      <Part name="flask" cx={445} cy={t + 78} w={84} at={E.flask.s} f={f} gate={[0.5, 1]} />
      <Label x={378} y={t + 134} w={200} align="left" size={22} italic color={SOFT} p={span(f, E.cap.s, E.cap.l + 20)}>hard lab experiments</Label>
      <Label x={655} y={t + 134} w={160} size={22} italic color={SOFT} p={span(f, E.d3.s, E.d3.l + 8)}>3D shape</Label>
      {[["expensive", E.exp, 22], ["slow", E.slow, 66], ["difficult", E.dif, 110]].map(([w, ev, dy]) =>
        <Label key={w} x={745} y={t + dy} w={170} align="left" size={36} p={span(f, ev.s, ev.l + 10)}>{w}</Label>)}
      <Svg>
        {dash > 0 && <g transform={`translate(655 ${t + 84}) scale(${dash})`} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5">
          <rect x={-30} y={-8} width={60} height={46} rx={6} /><path d="M-18,-8 L-18,-24 A18,18 0 0 1 18,-24 L18,-8" /></g>}
        {cr > 0 && <path d={`M${655 - 38},${t + 84 - 40} L${655 + 38},${t + 84 + 40} M${655 + 38},${t + 84 - 40} L${655 - 38},${t + 84 + 40}`} stroke={RED} strokeWidth={6} strokeLinecap="round" {...draw(cr)} fill="none" />}
        <Arrow d={`M915,${c} L1005,${c}`} tip={[1005, c]} ang={0} a={E.now.s} b={E.now.l + 8} f={f} color={RED} sw={4} />
        {fp > 0 && <g transform={`translate(1050 ${t + 78 - 150 * (1 - fp)})`} opacity={Math.min(1, fp * 2)} strokeLinejoin="round">
          <path d="M-26,-34 L10,-34 L26,-18 L26,34 L-26,34 Z" fill={PAPER2} stroke={INK} strokeWidth={3} />
          <path d="M10,-34 L10,-18 L26,-18 M-14,-4 H14 M-14,8 H14 M-14,20 H6" fill="none" stroke={INK} strokeWidth={2.5} /></g>}
        <Arrow d={`M1560,${c} L1400,${c}`} tip={[1400, c]} ang={180} a={E.dl.s} b={E.dl.l} f={f} sw={3.5} />
        {pub > 0 && <g transform={`translate(1655 ${c - 6}) scale(${pub})`} stroke={INK} strokeWidth={3} fill={PAPER2}>
          <path d="M-42,-30 V30 A42,14 0 0 0 42,30 V-30" /><ellipse cy={-30} rx={42} ry={14} /><path d="M-42,0 A42,14 0 0 0 42,0" fill="none" /></g>}
      </Svg>
      <Label x={1096} y={t + 50} w={300} align="left" size={40} p={span(f, E.txt.s, E.txt.e)}>a free prediction</Label>
      <Label x={1480} y={t + 44} w={150} size={24} italic color={SOFT} p={span(f, E.dl.s + 6, E.dl.l + 14)}>downloaded</Label>
      <Label x={1655} y={t + 128} w={200} size={24} p={span(f, E.dbl.s, E.dbl.e)}>public database</Label>
    </>
  );
};

const Scene = () => {
  const f = useCurrentFrame();
  const t = T(0);
  const bead = [[0, 1551, 211], [E.lbl.l, 235, t + 110], [E.bef.l, 545, t + 50], [E.flask.l, 545, t + 90], [E.cap.l, 585, t + 146], [E.dash.l, 715, t + 110], [E.d3.l, 725, t + 150],
                [E.cross.l, 715, t + 60], [E.exp.l, 722, t + 40], [E.slow.l, 722, t + 84], [E.dif.l, 722, t + 128], [E.now.l, 990, t + 30], [E.file.l, 1100, t + 22],
                [E.txt.l, 1300, t + 22], [E.dl.l, 1480, t + 20], [E.pub.l, 1740, t + 60], [E.dbl.l, 1765, t + 136], [K.len_f, 1766, t + 137]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("6-02.wav")} />
      <PageFrame />
      <TitleFinal />
      <Board f={DONE} E={FZ} />
      <Row1 f={f} E={E} />
      <Source p={span(f, E.lbl.l, E.lbl.l + 20)}>Wang et al., Pharmaceuticals 2023; Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual602" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
