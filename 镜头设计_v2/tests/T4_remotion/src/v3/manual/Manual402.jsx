// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-02（B 画外音）"Before, you'd need a lab-measured structure. Now? …"
// 主线物件：两条"拿到结构"的进度条，左右两栏 Before / Now 共用。
// Before 左条开始慢慢爬 → 烧瓶、lab-measured structure → Now 右栏数据库 → downloaded 文件飞到中间、右条一下满格 →
// a prediction → free 价签打勾 → public database → 论文图标滑到右栏下 → first time 红批注 → AlphaFold 芯片 → 钥匙 a hit → 右栏红框。
// 时间全读 keys_4-02.json（事件表 映射/events/4-02.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-02.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, evMap, Label, Pen, PageFrame, Source, Lens, guidePlan} from "./kit.jsx";

const E = evMap(K);
const GP = guidePlan(K);   // 视线引导（11-20，替代红色料珠）：事件表 guide 字段 → resolve.py → keys.guides
const io = Easing.inOut(Easing.cubic);
const LC = 500, RC = 1420;                  // 两栏中心
const BY = 820, BW = 600, BH = 34;          // 进度条
const FX = RC, FY = 520;                    // 文件图标中心
const DY = 300;                             // 数据库

const Bar = ({cx, p, fill, f}) => p <= 0 ? null : (
  <g>
    <rect x={cx - BW / 2} y={BY - BH / 2} width={BW * p} height={BH} rx={6} fill="none" stroke={INK} strokeWidth={2.5} />
    {fill > 0 && <rect x={cx - BW / 2 + 5} y={BY - BH / 2 + 5} width={(BW - 10) * fill} height={BH - 10} rx={3} fill={RED} opacity={0.85} />}
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const div = span(f, E.before.s, E.before.l + 30, ease);
  // 左条：从 need 起一直慢慢爬，structure 时挪一小格，到段尾也只到 14%
  const pop = f > E.need.l ? 0.05 * Math.exp(-(f - E.need.l) / 9) * Math.cos((f - E.need.l) / 3) : 0;
  const crawl = f < E.need.s ? 0 : 0.015 * span(f, E.need.s, E.need.l, out) + pop + 0.09 * span(f, E.need.l, K.len_f) + 0.035 * span(f, E.struct.s, E.struct.l + 6, out);
  const full = span(f, E.down.l - 6, E.down.l + 4, Easing.out(Easing.quad));
  const fly = span(f, E.down.s, E.down.l, io);
  const fx = RC + (FX - RC) * fly, fy = DY + (FY - DY) * fly - Math.sin(Math.PI * fly) * 40, fs = 0.4 + 0.6 * fly;
  const tag = span(f, E.free.s, E.free.l, Easing.out(Easing.back(1.5)));
  const pm = span(f, E.this1.s, E.this1.l, io);
  const px = 960 + (1250 - 960) * pm;
  const box = span(f, E.this.s, E.this.l + 8, ease);
  return (
    <Lens plan={GP} f={f}>
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-02.wav")} />
      <PageFrame />
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <line x1={960} y1={90} x2={960} y2={90 + (880 - 90) * div} stroke={SOFT} strokeWidth={2.5} />
        <Bar cx={LC} p={span(f, E.you.s, E.you.l, ease)} fill={Math.max(0, crawl)} f={f} />
        <Bar cx={RC} p={span(f, E.now.s, E.now.l + 6, ease)} fill={full} f={f} />
        {f >= E.db.s && f < E.db.l + 34 && (() => { const t = span(f, E.db.s, E.db.l + 30, Easing.inOut(Easing.quad)); return (
          <rect x={RC - BW / 2 + 5 + (BW - 70) * t} y={BY - BH / 2 + 5} width={60} height={BH - 10} fill="#FFFFFF" opacity={0.55 * Math.sin(Math.PI * t)} />); })()}
        {/* 文件 → 钥匙 的虚线 */}
        {f >= E.used.s && <line x1={FX} y1={FY + 50} x2={FX} y2={FY + 50 + 110 * span(f, E.used.s, E.used.l + 6, ease)} stroke={SOFT} strokeWidth={2.5} strokeDasharray="6 7" />}
        {/* 芯片 → 文件 */}
        {f >= E.af.l && (() => { const p = span(f, E.af.l, E.af.l + 16, ease); return (
          <g stroke={INK} strokeWidth={3.5} fill="none" strokeLinecap="round">
            <line x1={1262} y1={FY} x2={1262 + (1368 - 1262) * p} y2={FY} />
            {p > 0.95 && <path d={`M1356,${FY - 10} L1370,${FY} L1356,${FY + 10}`} />}
          </g>); })()}
        {/* first time 箭头 */}
        {f >= E.first.l && (() => { const p = span(f, E.first.l, E.first.l + 16, ease); return (
          <g stroke={RED} strokeWidth={3.5} fill="none" strokeLinecap="round">
            <path d={`M1610,440 Q1540,465 ${1600 + (1472 - 1600) * p},${458 + (494 - 458) * p}`} />
            {p > 0.95 && <path d="M1484,482 L1470,496 L1488,502" />}
          </g>); })()}
        {/* 价签 */}
        {tag > 0 && (
          <g transform={`translate(1630 ${FY}) rotate(${-8}) scale(${tag})`}>
            <path d="M-50,-24 L34,-24 L56,0 L34,24 L-50,24 Z" fill="#F4F1EA" stroke={INK} strokeWidth={2.5} strokeLinejoin="round" />
            <circle cx={36} cy={0} r={5} fill="none" stroke={INK} strokeWidth={2} />
          </g>
        )}
        {f >= E.free.l && (() => { const p = span(f, E.free.l, E.free.l + 10, ease); return (
          <path d="M1642,568 L1654,582 L1678,552" fill="none" stroke={RED} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />); })()}
        {box > 0 && <rect x={1130} y={448} width={600 * box} height={310} rx={12} fill="none" stroke={RED} strokeWidth={3} strokeDasharray="10 7" />}
        {/* 文件图标 */}
        {f >= E.down.s && (
          <g transform={`translate(${fx} ${fy}) scale(${fs})`} opacity={span(f, E.down.s, E.down.s + 6)}>
            <path d="M-35,-45 L18,-45 L35,-28 L35,45 L-35,45 Z" fill="#F4F1EA" stroke={INK} strokeWidth={3} strokeLinejoin="round" />
            <path d="M18,-45 L18,-28 L35,-28" fill="none" stroke={INK} strokeWidth={2.5} />
            {[-14, 0, 14, 28].map((y, i) => <line key={i} x1={-22} y1={y} x2={i === 3 ? 6 : 22} y2={y} stroke={SOFT} strokeWidth={3} strokeLinecap="round" />)}
          </g>
        )}
      </svg>

      {/* 表头 */}
      <Label x={LC} y={150} w={300} size={50} p={span(f, E.before.s, E.before.l + 16)}>Before</Label>
      <Label x={RC} y={150} w={300} size={50} p={span(f, E.now.s, E.now.l + 8)}>Now</Label>

      {/* 左栏 */}
      <Part name="flask" cx={LC} cy={420} w={150} at={E.lab.s} f={f} gate={[0.5, 1]} />
      <Label x={LC} y={530} w={420} size={30} p={span(f, E.lab.s, E.lab.l + 6)}>lab-measured</Label>
      <Label x={LC} y={570} w={420} size={30} p={span(f, E.struct.s, E.struct.l + 10)}>structure</Label>

      {/* 右栏 */}
      <Part name="disks" cx={RC} cy={DY} w={190} at={E.now.s + 4} f={f} gate={[0.5, 0.5]} />
      <Label x={RC} y={DY + 58} w={320} size={28} italic p={span(f, E.public.s, E.public.l + 14)}>public database</Label>
      <Label x={FX} y={FY + 58} w={260} size={28} p={span(f, E.pred.s, E.pred.l + 10)}>a prediction</Label>
      <div style={{position: "absolute", left: 1630 - 46, top: FY - 18, width: 80, textAlign: "center", fontSize: 28, lineHeight: "36px", transform: "rotate(-8deg)",
                   opacity: tag}}><Write p={span(f, E.free.s + 4, E.free.l + 6)}>free</Write></div>
      <Part name="chip" cx={1200} cy={FY} w={100} at={E.af.s} f={f} gate={[0.5, 0.5]} />
      <Label x={1200} y={FY + 58} w={200} size={26} italic p={span(f, E.af.s + 6, E.af.l + 10)}>AlphaFold</Label>
      <Part name="key" cx={FX} cy={700} w={150} at={E.hit.s} f={f} gate={[0.1, 0.5]} />
      <Label x={FX + 92} y={682} w={120} size={30} align="left" p={span(f, E.hit.s + 6, E.hit.l + 8)}>a hit</Label>
      <Pen x={1600} y={376} p={span(f, E.first.s, E.first.l + 6)} size={42} rot={-4}>first time</Pen>

      {/* 论文 */}
      <div style={{position: "absolute", left: px - 960, top: 0, width: 1920, height: 1080}}>
        <Part name="paper" cx={960} cy={940} w={100} at={E.accord.s} f={f} gate={[0.5, 1]} />
        <Label x={1022} y={920} w={200} size={28} align="left" p={span(f, E.paper.s, E.paper.l + 8)}>the paper</Label>
      </div>

      <Source p={span(f, E.before.l, E.before.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
    </AbsoluteFill>
    </Lens>
  );
};

const Root = () => <Composition id="Manual402" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
