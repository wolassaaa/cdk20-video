// HKBU SCIE1007 课程作业的科普视频：出镜 5-09（C）"This time, the key turned."（第 2 版，重写）
// 讲解卡：同一把锁和钥匙、同一个位置（钥匙已插在锁孔，尖端在锁后面）；the 红色虚弧线箭头画出要转的方向，key 标签；
// turned 钥匙绕锁孔转到底，锁梁弹起（锁梁一块上移并向外转开）、几道红线。时间全读 oncam_5-09.json。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_5-09.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Part, Label} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const FX1 = 1290, FY1 = 230, FX2 = 1870, FY2 = 880;
const LOCK = {cx: 1700, cy: 520, w: 240};
const PV = [1700, 568];
const KW = 240, KE = {cx: 1580, cy: 568};
const SPLIT = 484;                                           // 锁梁和锁身的分界（页面 y）
const ELBOW = [1640, SPLIT];                                 // 锁梁左脚（转开的轴）
const pop = Easing.out(Easing.back(2.2));
const polar = (a, r) => [PV[0] + r * Math.cos(a * Math.PI / 180), PV[1] + r * Math.sin(a * Math.PI / 180)];

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const ang = 55 * span(f, E.turn.s, E.turn.l, Easing.inOut(Easing.cubic));
  const op = span(f, E.open.s, E.open.l + 8, pop);
  const arcP = span(f, E.arc.s, E.arc.l + 14, ease);
  const [ax1, ay1] = polar(182 + 55 * arcP, 270), [ax0, ay0] = polar(182, 270);
  const burst = span(f, E.open.l, E.open.l + 8, out);
  const lockPart = <Part name="lock" cx={LOCK.cx} cy={LOCK.cy} w={LOCK.w} at={E.lock.l} f={f} gate={[0.5, 1]} />;
  return (
    <OnCamFrame D={D} f={f} wav="5-09.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
        </svg>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `rotate(${ang}deg)`, transformOrigin: `${PV[0]}px ${PV[1]}px`}}>
          <Part name="key" cx={KE.cx} cy={KE.cy} w={KW} at={E.key.l} f={f} gate={[0, 0.5]} flood={14} />
        </div>
        <Label x={KE.cx - 85} y={KE.cy + 52} w={200} p={span(f, E.keyl.l, E.keyl.l + 16, out)} size={28} italic color={INK}>key</Label>
        {/* 锁身 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, clipPath: `inset(${SPLIT}px 0 0 0)`}}>{lockPart}</div>
        {/* 锁梁：弹起并向外转开 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, clipPath: `inset(0 0 ${1080 - SPLIT}px 0)`, transform: `translateY(${-62 * op}px) rotate(${-17 * op}deg)`, transformOrigin: `${ELBOW[0]}px ${ELBOW[1]}px`}}>{lockPart}</div>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          {arcP > 0 && (
            <g stroke={RED} strokeWidth={6} fill="none" strokeLinecap="round" strokeLinejoin="round" opacity={1 - 0.0 * op}>
              <path d={`M${ax0},${ay0} A270,270 0 0 1 ${ax1},${ay1}`} strokeDasharray="14 12" />
              <g transform={`translate(${ax1},${ay1}) rotate(${182 + 55 * arcP + 90})`} opacity={span(arcP, 0.7, 1)}><path d="M-15,-12 L0,0 L-15,12" /></g>
            </g>
          )}
          {burst > 0 && [235, 270, 305].map((a, i) => { const [x0, y0] = [LOCK.cx + 150 * Math.cos(a * Math.PI / 180), 440 + 105 * Math.sin(a * Math.PI / 180)], [x1, y1] = [LOCK.cx + (150 + 34 * burst) * Math.cos(a * Math.PI / 180), 440 + (105 + 30 * burst) * Math.sin(a * Math.PI / 180)]; return <line key={i} x1={x0} y1={y0} x2={x1} y2={y1} stroke={RED} strokeWidth={6} strokeLinecap="round" />; })}
        </svg>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam509" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
