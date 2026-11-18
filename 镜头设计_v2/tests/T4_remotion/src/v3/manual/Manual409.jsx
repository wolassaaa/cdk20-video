// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-09（B 画外音）"The team gave it the pocket's shape and one rule …"
// 主线物件：锁（口袋）和从芯片里出来的一串钥匙。团队、芯片 Chemistry42 → 锁长出、外形虚线复制进芯片 → 规则卡片 →
// 钥匙插进锁、红点 hinge、must grip the hinge → 三道筛子、传送线 → 钥匙一把把过筛：两把打叉掉进 toss 槽 →
// 其余落到右下一列，score 条按 drug-like、easy to make 两段涨 → 逐个打勾。只是示意，不画分子结构。
// 时间全读 keys_4-09.json（事件表 映射/events/4-09.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-09.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const io = Easing.inOut(Easing.cubic);
const LX = 480, LY = 430, LW = 170, LH = LW * 743 / 520, HOLE = LY + 0.143 * LH;
const CX = 820, CY = 430;                        // 芯片
const LINE = 430, X0 = 960, XEND = 1760, V = 5;  // 传送线
const GATE = [1100, 1380, 1660];
const KW = 130, KH = KW * 312 / 1096;
const REJ = new Set([0, 5]);
const SURV = [1, 2, 3, 4, 6, 7];
const SC1 = [0.45, 0.3, 0.5, 0.25, 0.4, 0.35], SC2 = [0.35, 0.4, 0.2, 0.45, 0.3, 0.4];
const SX = 1490, SY = (j) => 640 + 50 * j, BX = 1590, BW = 160;

const Gate = ({x, p, glow}) => p <= 0 ? null : (
  <g opacity={p}>
    <rect x={x - 14} y={350} width={28} height={160 * p} rx={4} fill="none" stroke={glow > 0.05 ? RED : INK} strokeWidth={3} />
    {[...Array(9)].map((_, k) => 360 + k * 17 < 350 + 160 * p && <line key={k} x1={x - 14} y1={360 + k * 17} x2={x + 14} y2={360 + k * 17} stroke={SOFT} strokeWidth={1.8} />)}
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const t0 = (k) => E.built.s + 32 * k;
  const rejT = (k) => (k === 0 ? E.toss.l : E.possibly.l);
  // 钥匙 k 的位置、转角、透明度、是否打叉
  const keyState = (k) => {
    const s = t0(k);
    if (f < s) return null;
    const x = X0 + V * (f - s);
    if (REJ.has(k)) {
      const arrive = s + (GATE[0] - 30 - X0) / V;
      if (f < arrive) return {x, y: LINE, r: 0};
      const fall = span(f, rejT(k), rejT(k) + 22, Easing.in(Easing.quad));
      const slot = k === 0 ? -26 : 26;
      return {x: GATE[0] - 30 + slot * fall, y: LINE + (880 - LINE) * fall, r: 70 * fall * (k ? 1 : -1), x_: span(f, rejT(k) - 6, rejT(k) + 2)};
    }
    const end = s + (XEND - X0) / V;
    if (f < end) return {x, y: LINE, r: 0};
    const j = SURV.indexOf(k), d = span(f, end, end + 30, io);
    return {x: XEND + (SX - XEND) * d, y: LINE + (SY(j) - LINE) * d - Math.sin(Math.PI * d) * 30, r: 0};
  };
  const gateGlow = (g) => Math.max(0, ...[...Array(8)].map((_, k) => {
    if (REJ.has(k) && g > 0) return 0;
    const pass = t0(k) + (GATE[g] - X0) / V;
    return f > pass - 4 && f < pass + 10 ? 1 : 0;
  }));
  const shapeP = span(f, E.shape.s, E.shape.l + 10, ease);
  const fly = span(f, E.one.s, E.one.l, io);
  const kIn = span(f, E.grip.s, E.grip.l, io);
  const binShake = f > E.groups.s ? 3 * Math.exp(-(f - E.groups.s) / 8) * Math.sin((f - E.groups.s) / 2) : 0;
  const lineP = span(f, E.filters.s, E.filters.l + 10, ease);
  const bead = [[0, 130, 96], [E.title.l, 700, 96], [E.gave.l, 820, 300], [E.pocket.l, 640, 300], [E.shape.l, 300, 230], [E.one.l, 680, 560],
                [E.rule.l, 880, 640], [E.key.l, 240, 560], [E.grip.l, 620, 560], [E.spot.l, 250, 640], [E.hinge.l, 880, 900],
                [E.filters.l, 1240, 220], [E.built.l, 960, 330], [E.toss.l, 1240, 640], [E.designs.l, 1000, 560], [E.reactive.l, 950, 280],
                [E.possibly.l, 1260, 760], [E.toxic.l, 950, 330], [E.groups.l, 1300, 900], [E.score.l, 1480, 580], [E.drug.l, 1520, 300],
                [E.easy.l, 1800, 300], [E.each.l, 1840, 950], [K.len_f, 1841, 951]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-09.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>The pocket's shape and one rule</Write></div>

      {/* 团队、锁、芯片 */}
      <Part name="person_w" cx={160} cy={330} w={90} at={E.title.s + 4} f={f} gate={[0.5, 1]} />
      <Label x={160} y={415} w={160} size={24} italic color={SOFT} p={span(f, E.title.l, E.title.l + 16)}>the team</Label>
      {/* 钥匙在锁下面一层 */}
      {f >= E.key.s && (
        <div style={{position: "absolute", left: 300 + (405 - 300) * kIn - 75, top: HOLE - 150 / (1096 / 312) / 2, width: 150, height: 150 * 312 / 1096}}>
          <Part name="key" cx={75} cy={150 * 312 / 1096 / 2} w={150} at={E.key.s} f={f} gate={[0.1, 0.5]} />
        </div>
      )}
      <Part name="lock" cx={LX} cy={LY} w={LW} at={E.pocket.s} f={f} gate={[0.5, 1]} />
      <Part name="chip" cx={CX} cy={CY} w={130} at={E.gave.s} f={f} gate={[0.5, 0.5]} />
      <div style={{position: "absolute", left: CX - 72, top: CY - 17, width: 144, height: 34, background: "#2B2B2D", borderRadius: 4, opacity: span(f, E.gave.s + 8, E.gave.s + 14)}} />
      <div style={{position: "absolute", left: CX - 72, top: CY - 17, width: 144, textAlign: "center", font: "21px/34px Serif", color: "#E8E4DA"}}>
        <Write p={span(f, E.gave.s + 10, E.gave.l + 12)}>Chemistry42</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 锁外形虚线，和飞进芯片的那份 */}
        {shapeP > 0 && <rect x={LX - 100} y={LY - LH / 2 - 14} width={200} height={LH + 28} rx={40} fill="none" stroke={RED} strokeWidth={2.5} strokeDasharray="8 7" opacity={0.9 * shapeP} />}
        {f >= E.one.s && fly < 1 && (() => { const s = 1 - 0.75 * fly, x = LX + (CX - LX) * fly, y = LY - Math.sin(Math.PI * fly) * 90; return (
          <rect x={x - 100 * s} y={y - (LH / 2 + 14) * s} width={200 * s} height={(LH + 28) * s} rx={40 * s} fill="none" stroke={RED} strokeWidth={2.5} strokeDasharray="8 7" opacity={1 - span(fly, 0.8, 1)} />); })()}
        {/* hinge 红点和引线 */}
        {f >= E.spot.s && (() => { const p = span(f, E.spot.s, E.spot.l + 6, out); return (
          <g>
            <circle cx={LX - 52} cy={HOLE} r={9 * p} fill={RED} />
            <line x1={LX - 58} y1={HOLE + 8} x2={LX - 58 - (LX - 58 - 360) * span(f, E.spot.l, E.hinge.l, ease)} y2={HOLE + 8 + (586 - HOLE - 8) * span(f, E.spot.l, E.hinge.l, ease)} stroke={RED} strokeWidth={2} />
          </g>); })()}
        {/* 规则卡片 */}
        {f >= E.rule.s && <rect x={200} y={700} width={560} height={180} rx={10} fill="#F4F1EA" stroke={INK} strokeWidth={2.5} pathLength={1} strokeDasharray="1 1"
                                strokeDashoffset={1 - span(f, E.rule.s, E.rule.l + 10, ease)} />}
        {/* 卡片 → 芯片 */}
        {f >= E.hinge.l && (() => { const p = span(f, E.hinge.l, E.hinge.l + 20, ease); return (
          <g stroke={SOFT} strokeWidth={2.5} fill="none" strokeLinecap="round">
            <path d={`M764,790 Q850,720 ${764 + (812 - 764) * p},${790 + (512 - 790) * p}`} strokeDasharray="6 7" />
            {p > 0.95 && <path d="M790,522 L800,510 L810,524" />}
          </g>); })()}
        {/* 传送线和三道筛子 */}
        {lineP > 0 && <line x1={X0 - 10} y1={LINE + 16} x2={X0 - 10 + (XEND + 40 - X0) * lineP} y2={LINE + 16} stroke={SOFT} strokeWidth={2} />}
        {GATE.map((x, g) => <Gate key={g} x={x} p={span(f, E.filters.s + 6 * g, E.filters.l + 6 * g + 10, ease)} glow={gateGlow(g)} />)}
        {/* toss 槽 */}
        {f >= E.filters.s && (() => { const p = span(f, E.filters.s + 10, E.filters.l + 20, ease); return (
          <path d={`M1000,${860 + binShake} L1022,${930 + binShake} L1178,${930 + binShake} L1200,${860 + binShake}`} fill="none" stroke={INK} strokeWidth={3} strokeLinejoin="round"
                pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />); })()}
        {/* 分数条 */}
        {f >= E.score.s && SURV.map((k, j) => {
          const p = span(f, E.score.s + 3 * j, E.score.l + 3 * j + 8, ease), y = SY(j);
          const a = span(f, E.drug.s + 3 * j, E.drug.l + 3 * j + 10, ease), b = span(f, E.easy.s + 3 * j, E.easy.l + 3 * j + 10, ease);
          const c = span(f, E.each.s + 5 * j, E.each.s + 5 * j + 8, ease);
          return <g key={k}>
            <rect x={BX} y={y - 9} width={BW * p} height={18} rx={4} fill="none" stroke={INK} strokeWidth={2} />
            <rect x={BX + 3} y={y - 6} width={(BW - 6) * SC1[j] * a} height={12} rx={2} fill={RED} opacity={0.85} />
            <rect x={BX + 3 + (BW - 6) * SC1[j]} y={y - 6} width={(BW - 6) * SC2[j] * b} height={12} rx={2} fill={INK} opacity={0.7} />
            {c > 0 && <path d={`M${BX + BW + 18},${y} L${BX + BW + 26},${y + 8} L${BX + BW + 42},${y - 10}`} fill="none" stroke={RED} strokeWidth={3.5} strokeLinecap="round"
                            strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - c} />}
          </g>;
        })}
      </svg>

      {/* 钥匙流 */}
      {[...Array(8)].map((_, k) => {
        const st = keyState(k);
        if (!st) return null;
        return <React.Fragment key={k}>
          <div style={{position: "absolute", left: st.x - KW / 2, top: st.y - KH / 2, width: KW, height: KH, transform: `rotate(${st.r}deg)`, opacity: span(f, t0(k), t0(k) + 6)}}>
            <Part name="key" cx={KW / 2} cy={KH / 2} w={KW} at={-100} f={0} />
          </div>
          {st.x_ > 0 && <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, transform: `translate(${st.x - (GATE[0] - 30)}px, ${st.y - LINE}px)`}}>
            <g stroke={RED} strokeWidth={4} strokeLinecap="round">
              <line x1={GATE[0] - 44} y1={LINE - 14} x2={GATE[0] - 44 + 28 * st.x_} y2={LINE - 14 + 28 * st.x_} />
              <line x1={GATE[0] - 16} y1={LINE - 14} x2={GATE[0] - 16 - 28 * st.x_} y2={LINE - 14 + 28 * st.x_} />
            </g></svg>}
        </React.Fragment>;
      })}

      {/* 字（全部取自旁白） */}
      <Label x={LX} y={250} w={300} size={26} italic color={RED} p={span(f, E.shape.s, E.shape.l + 12)}>the pocket's shape</Label>
      <Label x={480} y={720} w={300} size={30} italic color={SOFT} p={span(f, E.rule.s + 4, E.rule.l + 12)}>one rule</Label>
      <Label x={480} y={780} w={520} size={48} p={span(f, E.hinge.s, E.hinge.l + 16)}>must grip the hinge</Label>
      <Label x={360} y={586} w={120} size={28} color={RED} p={span(f, E.hinge.s, E.hinge.l + 8)}>hinge</Label>
      <Label x={1380} y={200} w={300} size={32} italic p={span(f, E.filters.s, E.filters.l + 12)}>filters</Label>
      <Label x={GATE[0]} y={268} w={260} size={26} p={span(f, E.reactive.s, E.reactive.l + 10)}>reactive or</Label>
      <Label x={GATE[0]} y={300} w={260} size={26} p={span(f, E.toxic.s - 30, E.toxic.l + 10)}>possibly toxic</Label>
      <Label x={GATE[1]} y={300} w={240} size={26} p={span(f, E.drug.s, E.drug.l + 10)}>drug-like?</Label>
      <Label x={GATE[2]} y={300} w={240} size={26} p={span(f, E.easy.s, E.easy.l + 10)}>easy to make?</Label>
      <Label x={980} y={462} w={200} size={24} italic color={SOFT} p={span(f, E.designs.s, E.designs.l + 10)}>designs</Label>
      <Label x={1100} y={944} w={160} size={30} color={RED} p={span(f, E.groups.s, E.groups.l + 10)}>toss</Label>
      <Label x={BX + BW / 2} y={588} w={200} size={28} italic p={span(f, E.score.s, E.score.l + 10)}>score</Label>

      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023; Ivanenkov et al., J. Chem. Inf. Model. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual409" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
