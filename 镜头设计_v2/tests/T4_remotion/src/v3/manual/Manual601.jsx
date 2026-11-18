// HKBU SCIE1007 课程作业的科普视频：第 6 章二维说明书页 6-01（画外音）：大问题字牌 The big question 落在中央，问句写出后缩小上移成标题；记分板从中缝向两边推开，Before / Now 表头写出，空行一行行画出。
// 记分板组（6-01 到 6-08 同一张表、同一套坐标）；前面几段已画完的行在这里直接按画完的样子摆好，本段的行跟着旁白画。
// 时间全读 keys_6-01.json（事件表 映射/events/6-01.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_6-01.json";
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


const Scene = () => {
  const f = useCurrentFrame();
  const sh = span(f, E.shrink.s, E.shrink.l, Easing.inOut(Easing.cubic));
  const plate = span(f, E.bigq.s, E.bigq.l + 8, out) * (1 - span(f, E.shrink.s, E.shrink.l));
  const ul = span(f, E.help.l + 10, E.help.e + 8, ease);
  const bead = [[0, 130, 96], [E.bigq.l, 470, 400], [E.how.l, 560, 640], [E.shrink.l, 1150, 100], [E.help.l, 1080, 150], [E.seam.l, 1030, 205], [E.frame.l, 1850, 215],
                [E.bef.l, 860, 205], [E.rows.l, 235, 330], [E.now.l, 1550, 210], [K.len_f, 1551, 211]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("6-01.wav")} />
      <PageFrame />
      <Plate x={460} y={290} w={1000} p={plate}><span style={{fontSize: 120}}><Write p={span(f, E.bigq.s, E.bigq.e)}>The big question</Write></span></Plate>
      <div style={{position: "absolute", left: 435 - 339 * sh, top: 480 - 418 * sh, fontSize: 64 - 8 * sh, whiteSpace: "nowrap"}}>
        <Write p={span(f, E.how.s, E.how.e)}>How much did the </Write>
        <Write p={span(f, E.shrink.l - 6, E.shrink.l + 14)}>computers </Write>
        <span style={{position: "relative", display: "inline-block"}}>
          <Write p={span(f, E.help.s, E.help.e)}>actually help?</Write>
          <span style={{position: "absolute", left: 0, bottom: 2, height: 4, width: `${ul * 100}%`, background: RED}} />
        </span>
      </div>
      <Board f={f} E={E} />
      <Source p={span(f, E.bigq.l, E.bigq.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual601" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
