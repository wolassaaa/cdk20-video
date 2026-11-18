// HKBU SCIE1007 课程作业的科普视频：第 3 章二维说明书页 3-05（D 画外音）"Why this lock?"
// 三个步骤框：1 肿瘤样本（52 个点，36 个变红，计数跳到 36）；2 高水平 → 晚期、生存短（因果链，不画曲线）；
// 3 调低 CDK20（旋钮）→ 肝癌细胞长得慢（两团细胞对比）。数字全照旁白，出处 Feng et al. 2011。
// 时间全读 keys_3-05.json（事件表 映射/events/3-05.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_3-05.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Step, Bead, evMap, Title, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const BY = 180, BH = 640, BW = 560, BX = [96, 680, 1264];
// 52 个样本点：13 列 × 4 行；变红的 36 个按固定的乱序选出
const DOTS = [...Array(52)].map((_, i) => ({c: i % 13, r: Math.floor(i / 13)}));
const ORDER = [...Array(52).keys()].sort((a, b) => ((a * 37) % 52) - ((b * 37) % 52));
const RED36 = new Set(ORDER.slice(0, 36));
const rank = Object.fromEntries(ORDER.slice(0, 36).map((d, k) => [d, k]));

const Scene = () => {
  const f = useCurrentFrame();
  const grid = span(f, E.grid.s, E.grid.e, ease);
  const redP = span(f, E.red.s, E.red.e, Easing.inOut(Easing.quad));
  const count = Math.round(36 * redP);
  const bump = (() => { const k = Math.floor(36 * redP); return k > 0 && k < 36 ? 0.04 : 0; })();
  const cmp = span(f, E.cmp.s, E.cmp.e, ease);
  const knob = span(f, E.knob.s, E.knob.l + 10, Easing.out(Easing.back(1.4)));
  const turn = span(f, E.down.s, E.down.e, Easing.inOut(Easing.cubic));
  const cells = span(f, E.cells.s, E.cells.e, out);
  const slow = span(f, E.slow.s, E.slow.e, ease);
  const bead = [[0, 130, 96], [E.title.l, 440, 96], [E.hk.l, 1500, 96], [E.grid.l, BX[0] + 46, BY + 46], [E.red.l, BX[0] + 280, BY + 420],
                [E.cmp.l, BX[0] + 280, BY + 560], [E.high.l, BX[1] + 46, BY + 46], [E.late.l, BX[1] + 280, BY + 330], [E.surv.l, BX[1] + 280, BY + 520],
                [E.knob.l, BX[2] + 46, BY + 46], [E.down.l, BX[2] + 140, BY + 160], [E.cells.l, BX[2] + 280, BY + 360], [E.slow.l, BX[2] + 520, BY + 480], [K.len_f, BX[2] + 521, BY + 481]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("3-05.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>Why this lock?</Write></div>
      <Part name="hk" cx={1240} cy={98} w={110} at={E.hk.s + 2} f={f} gate={[0, 0]} wipe={8} flood={14} />
      <Pen x={1310} y={66} p={span(f, E.hk.s + 4, E.hk.e)} size={42}>the Hong Kong team</Pen>

      {/* 1 肿瘤样本 */}
      <Step n="1" x={BX[0]} y={BY} w={BW} h={BH} at={E.grid.s} f={f}>
        <Title p={span(f, E.grid.s, E.grid.e)} size={40}>Liver tumours</Title>
        {DOTS.map((d, i) => {
          const app = span(grid, (d.c + d.r * 2) / 22, (d.c + d.r * 2) / 22 + 0.15);
          const isRed = RED36.has(i) && rank[i] < count;
          return <div key={i} style={{position: "absolute", left: 48 + d.c * 36, top: 150 + d.r * 46, width: 24, height: 24, borderRadius: 12, boxSizing: "border-box",
                                      border: `2.5px solid ${isRed ? RED : INK}`, background: isRed ? RED : "transparent", opacity: app, transform: `scale(${app})`}} />;
        })}
        <div style={{position: "absolute", left: 0, width: BW, top: 360, textAlign: "center", opacity: span(f, E.grid.l, E.grid.l + 10)}}>
          <span style={{fontSize: 88, color: RED, display: "inline-block", transform: `scale(${1 + bump})`}}>{count}</span>
          <span style={{fontSize: 52}}> of 52</span>
        </div>
        <Label x={BW / 2} y={470} w={480} size={24} italic color={SOFT} p={span(f, E.red.l, E.red.e)}>CDK20 higher than in nearby non-tumour tissue</Label>
        {/* tumour vs nearby tissue 两个小柱 */}
        <svg width={BW} height={BH} style={{position: "absolute", left: 0, top: 0}}>
          <line x1={150} y1={612} x2={410} y2={612} stroke={INK} strokeWidth={3} opacity={cmp} />
          <rect x={180} y={612 - 70 * cmp} width={60} height={70 * cmp} fill="none" stroke={INK} strokeWidth={3} />
          <rect x={320} y={612 - 34 * cmp} width={60} height={34 * cmp} fill="none" stroke={INK} strokeWidth={3} />
          <rect x={180} y={612 - 70 * cmp} width={60} height={70 * cmp} fill={RED} opacity={0.85} />
        </svg>
        <Label x={210} y={518} w={120} size={20} p={cmp}>tumour</Label>
        <Label x={350} y={540} w={120} size={20} color={SOFT} p={cmp}>nearby</Label>
      </Step>

      {/* 2 高水平 → 晚期、生存短 */}
      <Step n="2" x={BX[1]} y={BY} w={BW} h={BH} at={E.high.s} f={f}>
        <Title p={span(f, E.high.s, E.high.e)} size={40}>High levels went with</Title>
        <div style={{position: "absolute", left: 60, top: 150, width: 440, height: 90, border: `3px solid ${RED}`, borderRadius: 12, boxSizing: "border-box",
                     textAlign: "center", font: "44px/84px Serif", color: RED, opacity: span(f, E.high.s, E.high.e), transform: `scale(${0.9 + 0.1 * span(f, E.high.s, E.high.e, out)})`}}>high CDK20</div>
        <svg width={BW} height={BH} style={{position: "absolute", left: 0, top: 0}}>
          {[[E.late, 330], [E.surv, 520]].map(([ev, y], i) => {
            const p = span(f, ev.s, ev.l, ease);
            return <g key={i} stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round">
              <path d={`M280,${i ? 420 : 248} L280,${y - 46}`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
              {p > 0.85 && <path d={`M266,${y - 60} L280,${y - 44} L294,${y - 60}`} />}
            </g>;
          })}
        </svg>
        <Label x={280} y={300} w={460} size={40} p={span(f, E.late.l - 4, E.late.e)}>later-stage tumours</Label>
        <Label x={280} y={490} w={460} size={40} p={span(f, E.surv.l - 4, E.surv.e)}>shorter survival</Label>
      </Step>

      {/* 3 调低 CDK20 → 长得慢 */}
      <Step n="3" x={BX[2]} y={BY} w={BW} h={BH} at={E.knob.s} f={f}>
        <Title p={span(f, E.knob.s, E.knob.e)} size={40}>Turn CDK20 down</Title>
        <svg width={BW} height={BH} style={{position: "absolute", left: 0, top: 0}}>
          {knob > 0 && (
            <g transform={`translate(140 220) scale(${knob})`}>
              {[...Array(7)].map((_, i) => { const a = (-210 + i * 40) * Math.PI / 180; return <line key={i} x1={66 * Math.cos(a)} y1={66 * Math.sin(a)} x2={78 * Math.cos(a)} y2={78 * Math.sin(a)} stroke={INK} strokeWidth={3} />; })}
              <circle r={52} fill="#F4F1EA" stroke={INK} strokeWidth={4} />
              <line x1={0} y1={0} x2={40 * Math.cos((-30 - 150 * turn) * Math.PI / 180)} y2={40 * Math.sin((-30 - 150 * turn) * Math.PI / 180)} stroke={RED} strokeWidth={6} strokeLinecap="round" />
            </g>
          )}
        </svg>
        <Label x={340} y={190} w={260} size={30} p={span(f, E.knob.l, E.knob.e)} align="left">CDK20</Label>
        <Label x={340} y={232} w={260} size={26} italic color={RED} p={span(f, E.down.l - 6, E.down.e)} align="left">turned down</Label>
        {/* 两团细胞：左边照常长，右边 CDK20 调低后长得慢 */}
        {[0, 1].map((side) => {
          const n = side === 0 ? Math.round(6 + 12 * span(f, E.cells.s, E.slow.e)) : Math.round(6 + 3 * span(f, E.cells.s, E.slow.e));
          const cx = side === 0 ? 150 : 410, cy = 450;
          return [...Array(n)].map((_, k) => {
            const a = k * 2.399, r = 14 * Math.sqrt(k);
            return <div key={`${side}-${k}`} style={{position: "absolute", left: cx + r * Math.cos(a) - 13, top: cy + r * Math.sin(a) - 13, width: 26, height: 26, borderRadius: 13,
                                                     border: `2.5px solid ${side ? RED : INK}`, boxSizing: "border-box", background: "rgba(246,243,236,0.9)", opacity: cells}} />;
          });
        })}
        <Label x={150} y={560} w={220} size={22} color={SOFT} p={cells}>liver cancer cells</Label>
        <Label x={410} y={560} w={220} size={22} color={RED} p={cells}>CDK20 turned down</Label>
        <Label x={280} y={596} w={480} size={30} italic p={span(f, E.slow.l - 10, E.slow.e)}>growth slowed</Label>
      </Step>

      <Source p={span(f, E.title.l, E.title.l + 20)}>Feng et al., J. Clin. Invest. 2011 · Illustration (dots and cells not to scale)</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual305" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
