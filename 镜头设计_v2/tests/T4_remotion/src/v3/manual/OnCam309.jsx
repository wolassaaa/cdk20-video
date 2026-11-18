// HKBU SCIE1007 课程作业的科普视频：出镜 3-09（B）"So you've got a lock nobody can see. How do you cut a key in the dark?"（第 2 版，重写）
// 讲解卡：一把锁；nobody 黑幕从上往下盖住锁，can see 黑幕上只剩一个问号；cut a key 钥匙在左边长出；
// in the dark 钥匙往黑幕里探（尖端渐隐进黑里），红笔写 in the dark。时间全读 oncam_3-09.json（事件表 映射/events/3-09.json）。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_3-09.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Part, Label, Pen} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const FX1 = 1290, FY1 = 230, FX2 = 1870, FY2 = 880;
const PX1 = 1545, PY1 = 242, PX2 = 1858, PY2 = 868;      // 黑幕
const LOCK = {cx: 1700, cy: 520, w: 200};
const back = Easing.out(Easing.back(1.6));

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const cur = span(f, E.curtain.s, E.curtain.l, Easing.in(Easing.quad));
  const q = span(f, E.qmark.s, E.qmark.l + 8, back);
  const jp = span(f, E.see.s, E.see.s + 20);
  const qy = -22 * Math.sin(Math.PI * jp);
  const pr = span(f, E.probe.s, E.probe.e, Easing.inOut(Easing.quad));
  const kx = 1405 + 150 * pr + (pr > 0 && pr < 1 ? 7 * Math.sin(pr * 22) : 0);
  const ky = 625 + (pr > 0 && pr < 1 ? 5 * Math.sin(pr * 17) : 0);
  const kmask = "linear-gradient(90deg,#000 1560px,transparent 1700px)";
  return (
    <OnCamFrame D={D} f={f} wav="3-09.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
        </svg>
        <Part name="lock" cx={LOCK.cx} cy={LOCK.cy} w={LOCK.w} at={E.lock.l} f={f} gate={[0.5, 1]} />
        {/* 黑幕：从上往下盖 */}
        <div style={{position: "absolute", left: PX1, top: PY1, width: PX2 - PX1, height: (PY2 - PY1) * cur, background: INK, borderRadius: 18}} />
        <div style={{position: "absolute", left: PX1, top: PY1 + 160 + qy, width: PX2 - PX1, textAlign: "center", font: "italic 300px/300px Serif", color: PAPER, opacity: q, transform: `scale(${0.6 + 0.4 * q})`}}>?</div>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, WebkitMaskImage: kmask, maskImage: kmask}}>
          <Part name="key" cx={kx} cy={ky} w={200} at={E.key.l} f={f} gate={[0, 0.5]} flood={14} />
        </div>
        <Label x={1405} y={548} w={200} p={span(f, E.key.l, E.key.l + 16, out)} size={28} italic color={INK}>a key</Label>
        <Pen x={1318} y={730} p={span(f, E.pen.s, E.pen.l + 14)} size={46} rot={-3}>in the dark</Pen>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam309" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
