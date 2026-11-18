// HKBU SCIE1007 课程作业的科普视频：第 3 章二维说明书页 3-02（D 画外音）"Inside your cells …"
// 主线物件：细胞大框里三个在干活的蛋白（cdk20 缩小，各带一个小齿轮在转）。
// cells 框画出 → proteins 长出 → lot 齿轮长出慢转 → work 加速 → drugs 钥匙飞来 → grab 俯冲贴住中间那个 →
// tightly 夹紧 → change 变灰、齿轮停 → does 齿轮打红叉 → slotting 压到底 → pocket 红圈 →
// like 这个蛋白连钥匙复制一份滑到右边放大 → key 写 key = drug → lock 蛋白变成锁，钥匙插在锁孔里，写 lock = protein。
// 时间全读 keys_3-02.json（事件表 映射/events/3-02.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_3-02.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const io = Easing.inOut(Easing.cubic);
const PROT = [
  {cx: 360, cy: 390, w: 170, g: [292, 334]},
  {cx: 640, cy: 480, w: 190, g: [562, 418], target: true},
  {cx: 380, cy: 680, w: 170, g: [312, 624]},
];
const KW = 140, KAR = 1096 / 312;            // 钥匙长度、宽高比
const RX = 1440, RY = 530, RS = 1.7;         // 右边放大的那份
const LW = 210, LH = LW * 743 / 520, LY = RY - 0.143 * LH;   // 锁：锁孔落在 RY

// 齿轮：8 个齿
const Gear = ({x, y, r, ang, p, color, fill = "#F4F1EA"}) => {
  if (p <= 0) return null;
  const teeth = [...Array(8)].map((_, i) => {
    const a = (i * 45 + ang) * Math.PI / 180;
    return <line key={i} x1={x + r * Math.cos(a)} y1={y + r * Math.sin(a)} x2={x + (r + 8) * Math.cos(a)} y2={y + (r + 8) * Math.sin(a)} />;
  });
  return (
    <g stroke={color} strokeWidth={6} strokeLinecap="butt" transform={`translate(${x} ${y}) scale(${p}) translate(${-x} ${-y})`}>
      {teeth}
      <circle cx={x} cy={y} r={r} fill={fill} strokeWidth={3.5} />
      <circle cx={x} cy={y} r={r * 0.35} fill="none" strokeWidth={3} />
    </g>
  );
};

// 钥匙：中心 (x, y)，长 w，转角 rot（0 = 头在左、尖朝右；90 = 头在上、尖朝下）
const Key = ({x, y, w, rot, op = 1}) => (
  <div style={{position: "absolute", left: x - w / 2, top: y - w / KAR / 2, width: w, height: w / KAR, transform: `rotate(${rot}deg)`, opacity: op}}>
    <Part name="key" cx={w / 2} cy={w / KAR / 2} w={w} at={-100} f={0} />
  </div>
);

const Scene = () => {
  const f = useCurrentFrame();
  const cellP = span(f, E.cell.s, E.cell.l + 10, ease);
  const cellP2 = span(f, E.cell.s + 10, E.cell.l + 20, ease);
  // 齿轮转角：lot 起慢转，work 加速；目标蛋白在 change 时停
  const speed = (t, stop) => (t < E.lot.s ? 0 : 1.2 + 4.8 * span(t, E.work.s, E.work.l, ease)) * (stop ? 1 - span(t, E.change.s, E.change.l, ease) : 1);
  let a0 = 0, a1 = 0;
  for (let t = 0; t <= f; t++) { a0 += speed(t, false); a1 += speed(t, true); }
  const gearIn = (i) => span(f, E.lot.s + 5 * i, E.lot.l + 5 * i, Easing.out(Easing.back(1.6)));
  const dim = span(f, E.change.s, E.change.l, ease);
  const squeeze = Math.sin(Math.PI * span(f, E.tight.s, E.tight.l + 14));
  // 药（钥匙）：右边飞进来（横着）→ 竖起来俯冲贴住口袋 → 夹紧压 8 px → slotting 再压 17 px 带回弹
  const k1 = span(f, E.drug.s, E.drug.l, out);
  const k2 = span(f, E.grab.s, E.grab.l, io);
  const k3 = span(f, E.slot.s, E.slot.l, Easing.in(Easing.cubic));
  const kb = f > E.slot.l ? Math.exp(-(f - E.slot.l) / 6) * Math.cos((f - E.slot.l) / 2.6) * 6 : 0;
  const kx0 = 2060 - 760 * k1, ky0 = 300;
  const kx = kx0 + (680 - kx0) * k2, ky = ky0 + 30 * k2 - Math.sin(Math.PI * k2) * 60 + 8 * span(f, E.tight.s, E.tight.l, ease) + 27 * k3 + kb;
  const krot = 90 * k2;
  // 复制一份滑到右边
  const m = span(f, E.like.s, E.like.l, io);
  const cx = 640 + (RX - 640) * m, cy = 480 + (RY - 480) * m - Math.sin(Math.PI * m) * 70, s = 1 + (RS - 1) * m;
  const lk = span(f, E.lock.s, E.lock.l, ease);
  const ckx = 680 + (1199 - 680) * m + 82 * lk, cky = 365 + (RY - 365) * m - Math.sin(Math.PI * m) * 70;
  const ckw = KW * (1 + (RS - 1) * m) + 80 * lk, ckrot = 90 * (1 - m);
  const line = span(f, E.like.s, E.like.l + 6, ease);
  const ring = span(f, E.pocket.s, E.pocket.l, out);
  const cross = span(f, E.does.s, E.does.l + 6, out);
  const bead = [[0, 130, 96], [E.title.l, 560, 96], [E.cell.l, 980, 230], [E.prot.l, 1000, 860], [E.lot.l, 990, 400], [E.work.l, 990, 640],
                [E.drug.l, 1300, 240], [E.grab.l, 820, 250], [E.tight.l, 1000, 420], [E.change.l, 820, 662], [E.does.l, 1000, 560],
                [E.slot.l, 790, 300], [E.pocket.l, 1000, 330], [E.like.l, 1100, 380], [E.key.l, 1000, 640], [E.lock.l, 1680, 440], [K.len_f, 1681, 441]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("3-02.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>Inside your cells</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 细胞：圆角大框，双线膜 */}
        <rect x={140} y={190} width={770} height={640} rx={110} fill="none" stroke={INK} strokeWidth={4} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - cellP} opacity={0.9} />
        <rect x={156} y={206} width={738} height={608} rx={96} fill="none" stroke={INK} strokeWidth={2} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - cellP2} opacity={0.35} />
        {/* 原蛋白到右边那份的虚线 */}
        {line > 0 && <path d={`M745,480 L${745 + (1066 + 42 * lk - 745) * line},${480 + 50 * line}`} stroke={SOFT} strokeWidth={2.5} strokeDasharray="7 8" fill="none" />}
      </svg>

      {/* 三个蛋白；被抓的那个夹紧、变灰、微歪 */}
      {PROT.map((p, i) => {
        const d = p.target ? dim : 0, sq = p.target ? squeeze : 0;
        return (
          <div key={i} style={{position: "absolute", left: 0, top: 0, filter: `grayscale(${0.85 * d}) opacity(${1 - 0.3 * d})`,
                               transform: `rotate(${-3 * d}deg) scaleX(${1 - 0.05 * sq})`, transformOrigin: `${p.cx}px ${p.cy}px`}}>
            <Part name="cdk20" cx={p.cx} cy={p.cy} w={p.w} at={E.prot.s + 8 * i} f={f} gate={[0.5, 1]} />
          </div>
        );
      })}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {PROT.map((p, i) => <Gear key={i} x={p.g[0]} y={p.g[1]} r={20} ang={p.target ? a1 : a0 * (i ? -1 : 1)} p={gearIn(i)} color={p.target && dim > 0.5 ? SOFT : INK} />)}
        {cross > 0 && (
          <g stroke={RED} strokeWidth={5} strokeLinecap="round">
            <line x1={540} y1={396} x2={540 + 44 * cross} y2={396 + 44 * cross} />
            <line x1={584} y1={396} x2={584 - 44 * span(cross, 0.4, 1)} y2={396 + 44 * span(cross, 0.4, 1)} />
          </g>
        )}
        {ring > 0 && <circle cx={680} cy={428} r={38 * (1.3 - 0.3 * ring)} fill="none" stroke={RED} strokeWidth={4} strokeDasharray="8 6" opacity={ring} />}
      </svg>

      {/* 右边那份：灰蛋白 → 锁 */}
      {f >= E.like.s && (
        <div style={{position: "absolute", left: 0, top: 0, filter: "grayscale(0.85) opacity(0.7)", opacity: 1 - lk,
                     transform: `translate(${cx - 640}px, ${cy - 480}px) rotate(${-3 * (1 - m)}deg) scale(${s})`, transformOrigin: "640px 480px"}}>
          <Part name="cdk20" cx={640} cy={480} w={190} at={-100} f={0} />
        </div>
      )}
      {f >= E.like.s && <Key x={ckx} y={cky} w={ckw} rot={ckrot} />}
      {f >= E.lock.s && <Part name="lock" cx={RX} cy={LY} w={LW} at={E.lock.s} f={f} gate={[0.5, 0.75]} />}

      {/* 细胞里的钥匙（药） */}
      {f >= E.drug.s && <Key x={kx} y={ky} w={KW} rot={krot} />}
      <Label x={kx0} y={ky0 + 34} w={160} size={28} italic color={SOFT} p={span(f, E.drug.s + 6, E.drug.s + 22) * (1 - span(f, E.grab.s, E.grab.s + 10))}>drugs</Label>

      {/* 字（全部取自旁白） */}
      {/* 细胞下方两行，取自旁白：proteins 时写第一个词，work 时写完；tightly 时写第二行 */}
      <div style={{position: "absolute", left: 140, top: 850, width: 770, textAlign: "center", fontSize: 34, whiteSpace: "nowrap"}}>
        <Write p={span(f, E.prot.l, E.prot.l + 16)}>proteins</Write><Write p={span(f, E.work.s, E.work.l + 16)}> do a lot of the work</Write></div>
      <div style={{position: "absolute", left: 140, top: 910, width: 770, textAlign: "center", fontSize: 34, whiteSpace: "nowrap", color: SOFT}}>
        <Write p={span(f, E.grab.s, E.grab.l + 14)}>drugs grab one protein</Write><Write p={span(f, E.tight.s, E.tight.l + 10)} style={{color: RED}}> tightly</Write></div>
      <Label x={640} y={572} w={320} size={24} italic p={span(f, E.does.s, E.does.l + 14)}>change what it does</Label>
      <Label x={730} y={392} w={140} size={26} italic color={RED} align="left" p={span(f, E.pocket.l - 4, E.pocket.l + 12)}>pocket</Label>
      <Label x={RX - 60} y={690} w={360} size={44} p={span(f, E.key.s, E.key.l + 14)}>key = drug</Label>
      <Label x={RX - 60} y={760} w={360} size={44} p={span(f, E.lock.l - 6, E.lock.l + 14)}>lock = protein</Label>

      <Source p={span(f, E.title.l, E.title.l + 20)}>Lengauer 2007 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual302" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
