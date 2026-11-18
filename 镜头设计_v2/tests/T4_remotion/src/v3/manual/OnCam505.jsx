// HKBU SCIE1007 课程作业的科普视频：出镜 5-05+5-06（C）"The key went into the lock. But it barely turned. So was that it? Back to square one?"（第 2 版，重写）
// 讲解卡：和 3-01 同一套锁和钥匙、同一个位置（钥匙在锁后面滑进去）；barely turned 钥匙绕自己的长轴只转一点点（柄压扁一点）就卡住，钥匙杆上红弧箭头和顿挫线；
// So was that it? 红问号，钥匙再试一下又卡住；Back to square one 钥匙退回起点，红笔 back to square one?。时间全读 oncam_5-05_5-06.json。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_5-05_5-06.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Part, Label, Pen} from "./kit.jsx";
import {OnCamFrame, useOnCam, PersonFront} from "./oncam.jsx";

const FX1 = 1290, FY1 = 230, FX2 = 1870, FY2 = 880;
const LOCK = {cx: 1700, cy: 520, w: 240};
const PV = [1700, 568];                                           // 锁孔（转轴）
const KW = 240, KS = {cx: 1425, cy: 770}, KE = {cx: 1580, cy: 568};
const back = Easing.out(Easing.back(1.8));
const polar = (a, r) => [PV[0] + r * Math.cos(a * Math.PI / 180), PV[1] + r * Math.sin(a * Math.PI / 180)];

// 钥匙"转"：钥匙绕自己的长轴转，侧面看就是钥匙柄压扁（scaleY = cos 转角）；红色弧箭头绕在钥匙杆上
const TurnArrow = ({cx, cy, p, op = 1, dash}) => {
  if (p <= 0.01 || op <= 0) return null;
  const rx = 22, ry = 40, t0 = -105, t1 = t0 + 210 * p;
  const P = (t) => [cx + rx * Math.cos(t * Math.PI / 180), cy + ry * Math.sin(t * Math.PI / 180)];
  const pts = [];
  for (let t = t0; t <= t1 + 0.01; t += 6) pts.push(P(Math.min(t, t1)));
  const [ex, ey] = P(t1), dx = -rx * Math.sin(t1 * Math.PI / 180), dy = ry * Math.cos(t1 * Math.PI / 180), a = Math.atan2(dy, dx) * 180 / Math.PI;
  return (
    <g opacity={op} stroke={RED} strokeWidth={6} fill="none" strokeLinecap="round" strokeLinejoin="round">
      <path d={"M" + pts.map((q) => q.join(",")).join(" L")} strokeDasharray={dash} />
      {p > 0.6 && <g transform={`translate(${ex},${ey}) rotate(${a})`}><path d="M-15,-12 L0,0 L-15,12" /></g>}
    </g>
  );
};

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const mv = span(f, E.slide.s, E.slide.l, Easing.inOut(Easing.cubic));
  const bk = span(f, E.back.s, E.back.l, ease);
  const m = Math.min(mv, 1 - bk);
  const kcx = KS.cx + (KE.cx - KS.cx) * m, kcy = KS.cy + (KE.cy - KS.cy) * m - Math.sin(Math.PI * m) * 40;
  const wob = f > E.slide.l ? Math.exp(-(f - E.slide.l) / 5) * Math.sin((f - E.slide.l) / 1.6) * 1.6 : 0;
  const tp = span(f, E.turn.s, E.turn.l, ease);
  const sh = f > E.stuck.l ? 2.4 * Math.exp(-(f - E.stuck.l) / 6) * Math.sin((f - E.stuck.l) * 1.4) : 0;
  const tryP = Math.sin(Math.PI * span(f, E.jolt.s, E.jolt.l + 8));
  const sh2 = f > E.jolt.l + 8 ? 2.4 * Math.exp(-(f - E.jolt.l - 8) / 6) * Math.sin((f - E.jolt.l - 8) * 1.4) : 0;
  const theta = (14 * tp + sh + 5 * tryP + sh2) * (1 - span(f, E.back.s, E.back.s + 16));
  const arcA = 182 + 18 * tp;
  const arcOp = (1 - span(f, E.back.s, E.back.s + 14)) * span(f, E.turn.s, E.turn.s + 6);
  const jl = span(f, E.stuck.l, E.stuck.l + 8, out) * (1 - span(f, E.back.s, E.back.s + 10));
  const q1 = span(f, E.q1.s, E.q1.l + 8, back), q2 = span(f, E.q2.s, E.q2.l + 10, back);
  const qOp = q1 * (1 - span(f, E.back.s, E.back.s + 12));
  const [ax0, ay0] = polar(182, 270), [ax1, ay1] = polar(arcA, 270);
  const tipAng = arcA + 90;
  return (
    <OnCamFrame D={D} f={f} wav="5-05_5-06.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
        </svg>
        {/* 钥匙在锁后面，绕锁孔转 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `scaleY(${Math.cos(Math.min(60, theta * 2.4) * Math.PI / 180)})`, transformOrigin: `${kcx}px ${kcy}px`}}>
          <Part name="key" cx={kcx} cy={kcy} w={KW} at={E.key.l} f={f} gate={[0, 0.5]} flood={14} />
        </div>
        <Label x={kcx - 85} y={kcy + 52} w={200} p={span(f, E.key.l, E.key.l + 16, out)} size={28} italic color={INK}>key</Label>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `rotate(${wob}deg)`, transformOrigin: `${LOCK.cx}px ${LOCK.cy}px`}}>
          <Part name="lock" cx={LOCK.cx} cy={LOCK.cy} w={LOCK.w} at={E.lock.l} f={f} gate={[0.5, 1]} />
        </div>
        <Label x={LOCK.cx} y={715} w={220} p={span(f, E.lockl.l - 4, E.lockl.l + 14, out)} size={28} italic color={INK}>lock</Label>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <TurnArrow cx={1488} cy={PV[1]} p={0.5 * tp + 0.12 * tryP} op={arcOp} />
          {jl > 0 && [200, 230, 260].map((a, i) => { const c = Math.cos(a * Math.PI / 180), sn = Math.sin(a * Math.PI / 180), r0 = 54 + 4 * jl, r1 = 54 + 30 * jl; const [x0, y0] = [1488 + r0 * c, PV[1] + r0 * sn], [x1, y1] = [1488 + r1 * c, PV[1] + r1 * sn]; return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1} stroke={RED} strokeWidth={5} strokeLinecap="round" />; })}
        </svg>
        {qOp > 0 && <div style={{position: "absolute", left: 1650, top: 236, width: 100, textAlign: "center", font: "italic 110px/110px Serif", color: RED, opacity: qOp, transform: `scale(${(0.6 + 0.4 * q1) * (1 + 0.35 * q2)})`}}>?</div>}
        <Pen x={1330} y={246} p={span(f, E.pen.s, E.pen.e)} size={46} rot={-3}>back to square one?</Pen>
      </div>
      <PersonFront D={D} f={f} x0={FX1} />
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam505" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
