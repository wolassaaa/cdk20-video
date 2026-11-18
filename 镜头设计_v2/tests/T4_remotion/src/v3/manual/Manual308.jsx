// HKBU SCIE1007 课程作业的科普视频：第 3 章二维说明书页 3-08（B 画外音）"But here's the problem."
// 上排：钥匙 → 眼睛看锁（CDK20）→ CDK20 淡成虚线轮廓加问号，盖章 never measured。
// 下排：烧瓶 + 日历翻页（hard lab work）；一大片蛋白点，只有少数变实（不写比例）。
// 右边：没有三维形状 → 虚线箭头到芯片（盖牌 predictions）→ expensive / slow / difficult 依次写出。
// 时间全读 keys_3-08.json（事件表 映射/events/3-08.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_3-08.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const GX = 1000, GY = 380;                      // CDK20 / 虚线轮廓中心
const CHX = 1640, CHY = 330, CHW = 220;          // 芯片
const COLS = 22, ROWS = 7, DX0 = 676, DY0 = 690, DS = 26, DR = 26;
// 测过的少数几个蛋白点（固定位置）
const FEW = [[2, 1], [7, 4], [11, 0], [15, 5], [19, 2], [4, 6], [13, 3], [20, 6], [9, 2]];

const Eye = ({x, y, p}) => (
  <g transform={`translate(${x} ${y})`} stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round">
    <path d="M-62,0 Q0,-48 62,0 Q0,48 -62,0 Z" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(p, 0, 0.7)} />
    <circle r={17 * span(p, 0.5, 1, out)} fill={INK} stroke="none" />
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const eye = span(f, E.eye.s, E.eye.l + 10);
  const sight = span(f, E.eye.l - 4, E.eye.e, ease);
  const hide = span(f, E.hide.s, E.hide.l + 14, Easing.inOut(Easing.quad));
  const ghost = span(f, E.hide.l - 6, E.hide.e, ease);
  const q = span(f, E.hide.l, E.hide.l + 16, Easing.out(Easing.back(1.6)));
  const stamp = span(f, E.stamp.s, E.stamp.l + 4, out);
  // 日历：从 cal 落地到句中 "small" 前翻好几页
  const flips = Math.max(0, Math.floor((f - E.cal.l) / 14));
  const flipP = f > E.cal.l && f < E.dots.s ? ((f - E.cal.l) % 14) / 14 : 0;
  const dots = span(f, E.dots.s, E.dots.l, ease);
  const few = span(f, E.few.s, E.few.l, ease);
  const dim = span(f, E.few.l, E.few.e, ease);
  const flash = f >= E.no3d.s && f < E.no3d.l + 40 ? 0.5 + 0.5 * Math.cos((f - E.no3d.s) / 6) : 0;
  const arrow = span(f, E.chip.s, E.chip.l + 6, ease);
  const words = [["expensive", E.exp], ["slow", E.slow], ["difficult", E.diff]];
  const bead = [[0, 130, 96], [E.title.l, 470, 96], [E.key.l, 260, 290], [E.eye.l, 560, 300], [E.hide.l, GX, 210], [E.stamp.l, 1180, 250],
                [E.lab.l, 230, 660], [E.cal.l, 430, 676], [E.dots.l, DX0 - 24, 650], [E.few.l, DX0 + COLS * DS + 6, 650], [E.no3d.l, 830, 560],
                [E.chip.l, CHX, CHY - CHW / 2 - 34], [E.exp.l, 1470, 562], [E.slow.l, 1470, 642], [E.diff.l, 1470, 722], [K.len_f, 1471, 723]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("3-08.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>The problem</Write></div>

      {/* 钥匙 → 眼睛 → 锁 */}
      <Part name="key" cx={260} cy={380} w={300} at={E.key.s + 2} f={f} gate={[0.1, 0.5]} />
      <Label x={260} y={440} w={300} size={28} italic p={span(f, E.key.l, E.key.e)}>design a key</Label>
      <div style={{opacity: 1 - hide}}>
        <Part name="cdk20" cx={GX} cy={GY} w={300} at={E.eye.s + 6} f={f} gate={[0.5, 0.5]} />
      </div>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {eye > 0 && <Eye x={560} y={380} p={eye} />}
        {sight > 0 && <path d={`M636,380 L${636 + (836 - 636) * sight},380`} stroke={INK} strokeWidth={3} strokeDasharray="4 10" strokeLinecap="round" />}
        {/* 虚线轮廓：CDK20 没人测过 */}
        {ghost > 0 && (
          <path d={`M${GX - 140},${GY - 30} C${GX - 150},${GY - 120} ${GX - 40},${GY - 135} ${GX + 20},${GY - 110} C${GX + 110},${GY - 130} ${GX + 160},${GY - 60} ${GX + 140},${GY + 10}
                    C${GX + 160},${GY + 90} ${GX + 60},${GY + 130} ${GX - 10},${GY + 110} C${GX - 90},${GY + 130} ${GX - 165},${GY + 60} ${GX - 140},${GY - 30} Z`}
                fill="none" stroke={flash > 0 ? RED : INK} strokeWidth={4} strokeDasharray="12 10" opacity={ghost * (0.75 + 0.25 * flash)} />
        )}
        {/* 没有三维形状 → 预测：虚线箭头 */}
        {arrow > 0 && (
          <g stroke={SOFT} strokeWidth={3} fill="none" strokeLinecap="round">
            <path d={`M${GX + 170},${GY - 60} L${GX + 170 + (CHX - CHW / 2 - 30 - GX - 170) * arrow},${GY - 60}`} strokeDasharray="8 8" />
            {arrow > 0.9 && <path d={`M${CHX - CHW / 2 - 44},${GY - 74} L${CHX - CHW / 2 - 30},${GY - 60} L${CHX - CHW / 2 - 44},${GY - 46}`} />}
          </g>
        )}
      </svg>
      {q > 0 && <div style={{position: "absolute", left: GX - 60, top: GY - 90, width: 120, textAlign: "center", fontSize: 150, lineHeight: "170px", color: RED,
                              transform: `scale(${q})`}}>?</div>}
      <Label x={GX} y={520} w={300} size={30} p={span(f, E.eye.l, E.eye.e)}>CDK20</Label>
      <Label x={GX} y={558} w={300} size={26} italic color={RED} p={span(f, E.no3d.s, E.no3d.l + 10)}>no 3D shape</Label>
      <Label x={560} y={440} w={240} size={28} italic p={span(f, E.eye.l, E.eye.e)}>see the lock</Label>
      {stamp > 0 && (
        <div style={{position: "absolute", left: 1170, top: 430, padding: "6px 16px", border: `4px solid ${RED}`, borderRadius: 6, color: RED, fontSize: 34,
                     transform: `rotate(-7deg) scale(${1.5 - 0.5 * stamp})`, opacity: stamp, whiteSpace: "nowrap"}}>never measured</div>
      )}

      {/* 下排左：实验室的活 */}
      <Part name="flask" cx={220} cy={790} w={150} at={E.lab.s + 2} f={f} gate={[0.5, 1]} />
      <div style={{position: "absolute", left: 0, top: 0, transformOrigin: "430px 720px", transform: `scaleY(${1 - 0.25 * Math.sin(Math.PI * flipP)})`}}>
        <Part name="cal" cx={430} cy={790} w={150} at={E.cal.s + 2} f={f} gate={[0.5, 0.2]} />
      </div>
      <Label x={325} y={900} w={360} size={30} italic p={span(f, E.lab.l, E.cal.e)}>hard lab work</Label>

      {/* 下排中：一大片蛋白，只有少数测过 */}
      <Label x={DX0 + (COLS - 1) * DS / 2} y={630} w={300} size={28} p={span(f, E.dots.l - 20, E.dots.e)}>proteins</Label>
      {[...Array(COLS * ROWS)].map((_, i) => {
        const c = i % COLS, r = Math.floor(i / COLS);
        const a = span(dots, 0.8 * (c + r) / (COLS + ROWS - 2), 0.8 * (c + r) / (COLS + ROWS - 2) + 0.2);
        const isFew = FEW.some(([x, y]) => x === c && y === r);
        const fi = FEW.findIndex(([x, y]) => x === c && y === r);
        const k = isFew ? span(few, 0.8 * fi / FEW.length, 0.8 * fi / FEW.length + 0.2) : 0;
        return <div key={i} style={{position: "absolute", left: DX0 + c * DS - 8, top: DY0 + r * DR - 8, width: 16, height: 16, borderRadius: 8, boxSizing: "border-box",
                                    border: `2px solid ${INK}`, background: k > 0 ? INK : "transparent", opacity: a * (isFew ? 1 : 1 - 0.45 * dim), transform: `scale(${a * (1 + 0.5 * k * (1 - k) * 4)})`}} />;
      })}
      <Label x={DX0 + (COLS - 1) * DS / 2} y={DY0 + (ROWS - 1) * DR + 26} w={460} size={28} italic p={span(f, E.few.s, E.few.e)}>only a few ever measured</Label>

      {/* 右：电脑预测 → 贵、慢、难 */}
      <Part name="chip" cx={CHX} cy={CHY} w={CHW} at={E.chip.s + 2} f={f} gate={[0.5, 0.5]} />
      <div style={{position: "absolute", left: CHX - 68, top: CHY - 18, width: 136, height: 36, background: "#2B2B2D", color: "#C9C6BE", fontSize: 20, textAlign: "center",
                   lineHeight: "36px", opacity: span(f, E.chip.s + 8, E.chip.s + 16)}}>predictions</div>
      <Label x={CHX} y={CHY + CHW / 2 + 12} w={340} size={26} italic color={SOFT} p={span(f, E.chip.l, E.chip.e)}>computer predictions of binding</Label>
      {words.map(([w, ev], i) => (
        <div key={w} style={{position: "absolute", left: 1510, top: 530 + i * 80, fontSize: 52, color: RED, fontStyle: "italic", transform: `scale(${1.15 - 0.15 * span(f, ev.s, ev.l, out)})`, transformOrigin: "left center"}}>
          <Write p={span(f, ev.s, ev.l + 4)}>{w}</Write>
        </div>
      ))}

      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023; Wang et al., Pharmaceuticals 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual308" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
