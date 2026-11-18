// HKBU SCIE1007 课程作业的科普视频：出镜 3-01（D）"Okay. To get this, picture a lock and a key."（第 2 版，重写）
// 讲解卡（右侧纸色卡片）：okay 落红点，this 红点跑到卡的起笔角；picture 外框一笔画出（实线）；lock 锁长出；
// key 钥匙在锁左下长出，字牌 a key 跟着钥匙走；钥匙在锁后面（先画钥匙再画锁）从左边滑过去，尖端被锁挡住，像插进孔里，锁一颤。
// 全片"锁 = 蛋白，钥匙 = 分子"的比喻从这里开始；5-05/5-09 用同一套锁和钥匙、同一个位置。
// 时间全读 oncam_3-01.json（事件表 映射/events/3-01.json）。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_3-01.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Part, Label} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const FX1 = 1290, FY1 = 230, FX2 = 1870, FY2 = 880;       // 讲解卡
const LOCK = {cx: 1700, cy: 520, w: 240};                  // 锁，约 1580–1820 × 348–692
const KW = 240, KS = {cx: 1425, cy: 770}, KE = {cx: 1585, cy: 575};   // 钥匙：起点、终点（尖端 x≈1705，在锁后面）
const SLIDE = 34;

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const dot = span(f, E.dot.s, E.dot.l, Easing.out(Easing.back(2)));
  const dmv = span(f, E.dot2.s, E.dot2.l, ease);
  const dx = 1580 + (1316 - 1580) * dmv, dy = 540 + (256 - 540) * dmv - Math.sin(Math.PI * dmv) * 40;
  const fr = span(f, E.frame.s, E.frame.e, ease);
  const dotA = dot * (1 - span(f, E.frame.s + 6, E.frame.s + 20));
  const mv = span(f, E.slide.s, E.slide.s + SLIDE, Easing.inOut(Easing.cubic));
  const kcx = KS.cx + (KE.cx - KS.cx) * mv, kcy = KS.cy + (KE.cy - KS.cy) * mv - Math.sin(Math.PI * mv) * 40;
  const t1 = E.slide.s + SLIDE;
  const wob = f > t1 ? Math.exp(-(f - t1) / 5) * Math.sin((f - t1) / 1.6) * 1.6 : 0;
  const llab = span(f, E.lock.l, E.lock.l + 16, out);
  const klab = span(f, E.key.l, E.key.l + 16, out);
  return (
    <OnCamFrame D={D} f={f} wav="3-01.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5}
                           pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
          {dotA > 0 && <circle cx={dx} cy={dy} r={9 * dotA} fill={RED} />}
        </svg>
        {/* 钥匙在锁后面：锁面挡住尖端 */}
        <Part name="key" cx={kcx} cy={kcy} w={KW} at={E.key.l} f={f} gate={[0, 0.5]} flood={14} />
        <Label x={kcx - 85} y={kcy + 52} w={200} p={klab} size={28} italic color={INK}>a key</Label>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `rotate(${wob}deg)`, transformOrigin: `${LOCK.cx}px ${LOCK.cy}px`}}>
          <Part name="lock" cx={LOCK.cx} cy={LOCK.cy} w={LOCK.w} at={E.lock.l} f={f} gate={[0.5, 1]} />
        </div>
        <Label x={LOCK.cx} y={715} w={220} p={llab} size={28} italic color={INK}>a lock</Label>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Lengauer 2007 · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam301" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
