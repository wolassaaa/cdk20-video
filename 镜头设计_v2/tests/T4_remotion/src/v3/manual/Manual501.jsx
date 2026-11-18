// HKBU SCIE1007 课程作业的科普视频：第 5 章二维说明书页 5-01（C 画外音）"So, the moment of truth …"
// 主线物件：七个小瓶一排。Seven 依次落下计数到 7 → 烧瓶在瓶后，made in a real lab → 问号变成虚的 CDK20，七个瓶各连虚线 →
// Grip 线闪 → 右边量杯式刻度 Kd，指针落下、晃一下 → 第一个瓶的小点流向 CDK20，两波，贴住 → 左半边变实（half the protein）→
// Lower 指针往下走，lower = tighter，第一个瓶的线变粗变红。
// 时间全读 keys_5-01.json（事件表 映射/events/5-01.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_5-01.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const io = Easing.inOut(Easing.cubic);
const TX = (i) => 220 + i * 105, TY = 760, TW = 46, TTOP = 692;
const PX = 1080, PY = 430, PW = 230;          // CDK20
const end = (i) => [1020 + i * 20, 520];       // 线落在 CDK20 下沿
const GX = 1600, G0 = 330, G1 = 800;           // 刻度
const DOTS = [...Array(18)].map((_, k) => ({a: (115 + (k * 137) % 130) * Math.PI / 180, r: 112 + (k % 3) * 10, wave: k < 10 ? 0 : 1, j: k < 10 ? k : k - 10}));

const Scene = () => {
  const f = useCurrentFrame();
  const landT = (i) => E.seven.l + i * 6;
  const landed = [...Array(7)].filter((_, i) => f >= landT(i)).length;
  const lineP = (i) => span(f, E.cdk.s + 3 * i, E.cdk.s + 3 * i + 16, ease);
  const flash = f > E.grip.s ? Math.max(0, Math.sin(Math.PI * span(f, E.grip.s, E.grip.s + 30))) : 0;
  const q = span(f, E.any.s, E.any.l, Easing.out(Easing.back(1.6))) * (1 - span(f, E.grab.s, E.grab.l));
  const half = span(f, E.half.s, E.half.l + 10, ease);
  const gauge = span(f, E.meas.s, E.meas.l + 8, ease);
  let py = 450 + 270 * span(f, E.lower.s, E.lower.l, io);
  if (f > E.rough.s) py += 14 * Math.exp(-(f - E.rough.s) / 12) * Math.sin((f - E.rough.s) / 2.5);
  const ptr = span(f, E.kd.s, E.kd.l, Easing.out(Easing.back(1.5)));
  const thick = span(f, E.tight.s, E.tight.l + 6, ease);
  const snap = span(f, E.grab2.s, E.grab2.l + 4, out);
  const bead = [[0, 130, 96], [E.title.l, 700, 96], [E.sub.l, 1100, 96], [E.seven.l, 120, 650], [E.mol.l, 900, 880], [E.made.l, 760, 560],
                [E.lab.l, 760, 480], [E.any.l, 1250, 300], [E.grab.l, 1300, 430], [E.cdk.l, 1250, 600], [E.grip.l, 1250, 650], [E.meas.l, 1480, 330],
                [E.kd.l, 1720, 300], [E.rough.l, 1720, 560], [E.how.l, 420, 560], [E.molec.l, 900, 330], [E.takes.l, 300, 600], [E.grab2.l, 1260, 520],
                [E.half.l, 1250, 380], [E.prot.l, 1300, 610], [E.lower.l, 1740, 850], [E.means.l, 1480, 880], [E.tight.l, 1800, 880], [K.len_f, 1801, 881]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("5-01.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.l + 20)}>The moment of truth</Write></div>
      <div style={{position: "absolute", left: 680, top: 82, fontSize: 30, fontStyle: "italic", color: SOFT}}><Write p={span(f, E.sub.s, E.sub.l + 16)}>Objective 2 · Results</Write></div>

      {/* 烧瓶在瓶后 */}
      <div style={{opacity: 0.45}}><Part name="flask" cx={535} cy={680} w={260} at={E.made.s} f={f} gate={[0.5, 1]} /></div>
      <Label x={535} y={470} w={360} size={26} italic p={span(f, E.lab.s - 14, E.lab.l + 8)}>made in a real lab</Label>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 七条线 */}
        {[...Array(7)].map((_, i) => {
          const p = lineP(i);
          if (p <= 0) return null;
          const [ex, ey] = end(i), x0 = TX(i), y0 = TTOP;
          const t = i === 0 ? thick : 0;
          return <line key={i} x1={x0} y1={y0} x2={x0 + (ex - x0) * p} y2={y0 + (ey - y0) * p} stroke={t > 0.5 ? RED : INK} strokeWidth={2.5 + 4 * t + 2 * flash}
                       strokeDasharray={t > 0.5 ? "none" : "7 8"} opacity={0.75 + 0.25 * Math.max(flash, t)} />;
        })}
        {/* 刻度 */}
        {gauge > 0 && (
          <g>
            <rect x={GX - 30} y={G1 - (G1 - G0) * gauge} width={60} height={(G1 - G0) * gauge} rx={8} fill="#F4F1EA" stroke={INK} strokeWidth={3} />
            {[...Array(9)].map((_, k) => { const y = G0 + 30 + k * 52; return y > G1 - (G1 - G0) * gauge && <line key={k} x1={GX - 30} y1={y} x2={GX - (k % 2 ? 14 : 4)} y2={y} stroke={INK} strokeWidth={2.5} />; })}
          </g>
        )}
        {ptr > 0 && <path d={`M${GX + 36},${py} L${GX + 62},${py - 14} L${GX + 62},${py + 14} Z`} fill={RED} transform={`translate(${GX + 50} ${py}) scale(${ptr}) translate(${-GX - 50} ${-py})`} />}
        {f >= E.means.s && (() => { const p = span(f, E.means.s, E.means.l + 10, ease); return (
          <g stroke={RED} strokeWidth={4} fill="none" strokeLinecap="round">
            <line x1={GX + 100} y1={440} x2={GX + 100} y2={440 + 290 * p} />
            {p > 0.95 && <path d={`M${GX + 88},${714} L${GX + 100},${732} L${GX + 112},${714}`} />}
          </g>); })()}
        {/* 小点：沿第一条线流向 CDK20，围在左半边 */}
        {DOTS.map((d, k) => {
          const w0 = d.wave ? E.takes.s : E.how.s, w1 = d.wave ? E.grab2.s : E.molec.l + 20;
          const t0 = w0 + d.j * ((w1 - w0) / 12);
          const t = span(f, t0, t0 + 36, io);
          if (t <= 0) return null;
          const [ex, ey] = end(0);
          const r = d.r - 14 * snap;
          const tx = PX + r * Math.cos(d.a), ty = PY + r * Math.sin(d.a) * 0.8;
          let x, y;
          if (t < 0.7) { const u = t / 0.7; x = TX(0) + (ex - TX(0)) * u; y = TTOP + (ey - TTOP) * u; }
          else { const u = (t - 0.7) / 0.3; x = ex + (tx - ex) * u; y = ey + (ty - ey) * u; }
          return <circle key={k} cx={x} cy={y} r={6} fill={INK} />;
        })}
      </svg>

      {/* 小瓶 */}
      {[...Array(7)].map((_, i) => {
        const t = span(f, landT(i) - 12, landT(i), Easing.in(Easing.quad));
        const bump = f > landT(i) ? 6 * Math.exp(-(f - landT(i)) / 5) * Math.sin((f - landT(i)) / 2) : 0;
        return t <= 0 ? null : (
          <div key={i} style={{position: "absolute", left: 0, top: -110 * (1 - t) + bump, opacity: span(t, 0, 0.4)}}>
            <Part name="tube" cx={TX(i)} cy={TY} w={TW} at={-100} f={0} />
          </div>
        );
      })}
      <div style={{position: "absolute", left: 535 - 160, top: 852, width: 320, textAlign: "center", fontSize: 30, opacity: span(f, E.seven.s, E.seven.l)}}>
        <span style={{color: RED}}>{landed}</span> <Write p={span(f, E.mol.s, E.mol.l + 14)}>real molecules</Write></div>

      {/* 问号 → CDK20 */}
      {q > 0 && <div style={{position: "absolute", left: PX - 60, top: PY - 90, width: 120, textAlign: "center", fontSize: 150, lineHeight: "180px", color: RED, opacity: q,
                             transform: `scale(${q})`}}>?</div>}
      <div style={{opacity: 0.3, filter: "grayscale(1)"}}><Part name="cdk20" cx={PX} cy={PY} w={PW} at={E.grab.s} f={f} gate={[0.5, 0.5]} /></div>
      {half > 0 && <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, clipPath: `inset(0 ${1920 - (PX - PW / 2) - PW / 2 * half}px 0 0)`}}>
        <Part name="cdk20" cx={PX} cy={PY} w={PW} at={-100} f={0} /></div>}
      {f >= E.grab.s && <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <ellipse cx={PX} cy={PY} rx={PW / 2 + 18} ry={PW * 0.4 + 18} fill="none" stroke={SOFT} strokeWidth={2.5} strokeDasharray="8 8" opacity={span(f, E.grab.s, E.grab.l)} />
        {half > 0 && <line x1={PX} y1={PY - PW * 0.4 - 12} x2={PX} y2={PY - PW * 0.4 - 12 + (PW * 0.8 + 24) * half} stroke={RED} strokeWidth={2.5} strokeDasharray="5 6" />}
      </svg>}
      <Label x={PX} y={278} w={200} size={30} p={span(f, E.cdk.s, E.cdk.l + 8)}>CDK20</Label>
      <Label x={1240} y={412} w={260} size={26} italic align="left" p={span(f, E.prot.s - 20, E.prot.l + 8)}>half the protein</Label>

      {/* Kd 刻度的字 */}
      <Label x={GX} y={262} w={120} size={44} p={span(f, E.kd.s, E.kd.l + 6)}>Kd</Label>
      <Label x={1410} y={736} w={260} size={30} color={RED} p={span(f, E.means.s, E.tight.l + 6)}>lower = tighter</Label>

      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual501" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
