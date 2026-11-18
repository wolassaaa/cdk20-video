// HKBU SCIE1007 课程作业的科普视频：第 6 章二维说明书页 6-03（画外音）：第二行 Finding a hit。左格一大片点（millions）挤进瓶颈（costly bottleneck），右格 8,918 个点计数，收缩成 13 个。
// 记分板组（6-01 到 6-08 同一张表、同一套坐标）；前面几段已画完的行在这里直接按画完的样子摆好，本段的行跟着旁白画。
// 时间全读 keys_6-03.json（事件表 映射/events/6-03.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_6-03.json";
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
        <Arrow d={`M1400,${c} L1560,${c}`} tip={[1560, c]} ang={0} a={E.dl.s} b={E.dl.l} f={f} sw={3.5} />
        {pub > 0 && <g transform={`translate(1655 ${c - 6}) scale(${pub})`} stroke={INK} strokeWidth={3} fill={PAPER2}>
          <path d="M-42,-30 V30 A42,14 0 0 0 42,30 V-30" /><ellipse cy={-30} rx={42} ry={14} /><path d="M-42,0 A42,14 0 0 0 42,0" fill="none" /></g>}
      </Svg>
      <Label x={1096} y={t + 50} w={300} align="left" size={40} p={span(f, E.txt.s, E.txt.e)}>a free prediction</Label>
      <Label x={1480} y={t + 44} w={150} size={24} italic color={SOFT} p={span(f, E.dl.s + 6, E.dl.l + 14)}>downloaded</Label>
      <Label x={1655} y={t + 128} w={200} size={24} p={span(f, E.dbl.s, E.dbl.e)}>public database</Label>
    </>
  );
};

// ---- 第二行：Finding a hit ----
const FUN = {mx: 740, nx: 850, ex: 935, hm: 52, hn: 9};
const funHw = (x) => (x >= FUN.nx ? FUN.hn : FUN.hm - ((FUN.hm - FUN.hn) * (x - FUN.mx)) / (FUN.nx - FUN.mx));
const Row2 = ({f, E}) => {
  const t = T(1), cy = t + 100;
  const fun = span(f, E.fun.s, E.fun.l + 14, ease), scrn = span(f, E.scrn.s, E.scrn.l + 16, ease);
  const cnt = span(f, E.cnt.s, E.cnt.l + 20, out), shrinkAll = (i) => span(f, E.shr.s + (i % 7) * 3, E.shr.e + (i % 7) * 3, ease);
  const made = span(f, E.made.s, E.made.l + 8);
  const thrJ = f >= E.thr.l ? 1 + 0.25 * Math.exp(-(f - E.thr.l) / 6) * Math.cos((f - E.thr.l) / 2.5) : 1;
  const num = f >= E.thr.l ? "13" : Math.round(8918 * cnt).toLocaleString("en-US");
  return (
    <>
      <Tint x={372} y={t + 3} w={576} h={RH - 6} p={span(f, E.lbl.s, E.lbl.l)} />
      <Tint x={972} y={t + 3} w={836} h={RH - 6} p={span(f, E.now.s, E.now.l + 10)} />
      <Label x={110} y={t + 12} w={250} align="left" size={32} p={span(f, E.lbl.s, E.lbl.l)}>Finding a hit</Label>
      <Label x={378} y={t + 10} w={210} align="left" size={20} italic color={SOFT} p={span(f, E.scr.s, E.scr.e)}>screening real compounds</Label>
      <Label x={596} y={t + 10} w={130} align="left" size={20} italic color={SOFT} p={span(f, E.rev.s, E.rev.l + 12)}>(2023 review)</Label>
      <Pen x={745} y={t + 4} size={28} rot={-2} p={span(f, E.cost.s, E.cost.e)}>costly bottleneck&nbsp;</Pen>
      <Svg>
        {fun > 0 && <path d={`M${FUN.mx},${cy - FUN.hm} L${FUN.nx},${cy - FUN.hn} L${FUN.ex},${cy - FUN.hn} M${FUN.mx},${cy + FUN.hm} L${FUN.nx},${cy + FUN.hn} L${FUN.ex},${cy + FUN.hn}`}
          fill="none" stroke={INK} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" {...draw(fun)} />}
        {[...Array(150)].map((_, i) => {
          const dd = Math.floor(rnd(i + 777) * 24), g = span(f, E.mil.s + dd, E.mil.s + dd + 14, out);
          if (g <= 0) return null;
          const x0 = 388 + rnd(i + 1) * 312, y0 = t + 52 + rnd(i + 300) * 96;
          const tx = 752 + rnd(i + 55) * 86, ty = cy + (rnd(i + 91) - 0.5) * 2 * (funHw(tx) - 6);
          const d2 = Math.floor(rnd(i + 5) * 20), q = span(f, E.sq.s + d2, E.sq.e - 20 + d2, ease);
          return <circle key={i} cx={x0 + (tx - x0) * q} cy={y0 + (ty - y0) * q} r={4 * g} fill={INK} opacity={0.85} />;
        })}
        {/* 右格：屏幕框和 8,918 个点 */}
        {scrn > 0 && <rect x={1000} y={t + 16} width={360} height={136} rx={10} fill="none" stroke={INK} strokeWidth={3.5} {...draw(scrn)} />}
        {[...Array(120)].map((_, i) => {
          const d = Math.floor(rnd(i + 401) * 40), g = span(f, E.cnt.s + d, E.cnt.s + d + 14, out);
          if (g <= 0) return null;
          const keep = i < 13, q = shrinkAll(i);
          const x0 = 1020 + rnd(i + 31) * 320, y0 = t + 34 + rnd(i + 211) * 100;
          const x = keep ? x0 + (1034 + i * 24 - x0) * q : x0, y = keep ? y0 + (t + 84 - y0) * q : y0;
          const op = keep ? 1 : 1 - q;
          return <circle key={i} cx={x} cy={y} r={(keep ? 3.5 + 3.5 * q : 3.5) * g} fill={keep && made > 0.5 ? RED : INK} opacity={op * 0.9} />;
        })}
      </Svg>
      <div style={{position: "absolute", left: 1400, top: t + 14, fontSize: 80, lineHeight: "80px", color: f >= E.thr.l ? RED : INK, opacity: span(f, E.cnt.s + 4, E.cnt.s + 18),
                   transform: `scale(${thrJ})`, transformOrigin: "0 50%", whiteSpace: "nowrap"}}>{num}</div>
      <div style={{opacity: 1 - span(f, E.mol.s, E.mol.s + 8)}}><Label x={1400} y={t + 96} w={160} align="left" size={28} p={span(f, E.des.s, E.des.e)}>designs</Label></div>
      <Label x={1400} y={t + 96} w={200} align="left" size={28} p={span(f, E.mol.s, E.mol.e)}>molecules</Label>
      <Label x={1580} y={t + 40} w={220} align="left" size={26} italic color={SOFT} p={span(f, E.thr.l + 4, E.thr.l + 24)}>8,918 designs</Label>
      <Label x={1400} y={t + 126} w={200} align="left" size={24} italic color={SOFT} p={span(f, E.made.s, E.made.e)}>actually made</Label>
    </>
  );
};

const Scene = () => {
  const f = useCurrentFrame();
  const t = T(1);
  const bead = [[0, 1766, 382], [E.lbl.l, 235, t + 110], [E.scr.l, 500, t + 100], [E.mil.l, 680, t + 26], [E.fun.l, 900, t + 26], [E.rev.l, 730, t + 26], [E.sq.l, 900, t + 28],
                [E.cost.l, 962, t + 80], [E.now.l, 1383, t + 60], [E.cnt.l, 1380, t + 150], [E.des.l, 1620, t + 40], [E.scrn.l, 1650, t + 110], [E.shr.l, 1650, t + 50],
                [E.thr.l, 1700, t + 40], [E.mol.l, 1700, t + 100], [E.made.l, 1650, t + 145], [K.len_f, 1651, t + 146]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("6-03.wav")} />
      <PageFrame />
      <TitleFinal />
      <Board f={DONE} E={FZ} />
      <Row1 f={DONE} E={FZ} />
      <Row2 f={f} E={E} />
      <Source p={span(f, E.lbl.l, E.lbl.l + 20)}>Wang et al., Pharmaceuticals 2023; Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual603" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
