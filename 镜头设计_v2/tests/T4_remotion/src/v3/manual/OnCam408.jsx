// HKBU SCIE1007 课程作业的科普视频：出镜 4-08（A）"AI didn't replace the scientists. It ran their trial and error inside a computer, at light speed."（第 2 版，重写）
// 讲解卡：AI 牌的箭头指向下方，红叉盖住（没替换），小人站着，字牌 scientists；循环箭头长出，trial / error 标签，循环转起来；
// inside a computer 屏幕框把循环框住；light speed 循环加速，出现拖影、红色光圈和加速线。时间全读 oncam_4-08.json。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_4-08.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Part, Label, Arrow} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const FX1 = 1290, FY1 = 200, FX2 = 1870, FY2 = 900;
const PL = {cx: 1400, cy: 290, w: 130, h: 70};          // AI 牌
const PER = {cx: 1400, cy: 715, w: 150};                 // 小人
const LC = [1667, 555], LR = 95;                         // 循环中心、半径
const SX1 = 1497, SX2 = 1837, SY1 = 330, SY2 = 780;      // 屏幕框
const back = Easing.out(Easing.back(1.6));

const pt = (a, r = LR) => [LC[0] + r * Math.cos(a * Math.PI / 180), LC[1] + r * Math.sin(a * Math.PI / 180)];
const arc = (a0, a1) => { const [x0, y0] = pt(a0), [x1, y1] = pt(a1); return `M${x0},${y0} A${LR},${LR} 0 0 1 ${x1},${y1}`; };

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const pl = span(f, E.plate.s, E.plate.l, back);
  const cr = span(f, E.cross.s, E.cross.l, ease);
  const fadeA = 1 - span(f, E.loop.s, E.loop.s + 18);
  const lp = span(f, E.loop.s, E.loop.l + 18, ease);
  const sc = span(f, E.screen.s, E.screen.l + 14, ease);
  const blur = span(f, E.blur.s, E.blur.l + 10, ease);
  // 转速：trial 开始慢转，light 起加速
  const speed = (i) => (i < E.trial.l ? 0 : 3 + 20 * span(i, E.fast.s, E.fast.l + 16, Easing.in(Easing.quad)));
  let ang = 0;
  for (let i = 0; i <= f; i++) ang += speed(i);
  const v = speed(f);
  const bump = f > E.person.l ? 0.05 * Math.exp(-(f - E.person.l) / 6) * Math.cos((f - E.person.l) / 3) : 0;
  const loopSvg = (a, op) => lp < 0.03 ? null : (
    <g transform={`rotate(${a} ${LC[0]} ${LC[1]})`} opacity={op} fill="none" stroke={INK} strokeWidth={9} strokeLinecap="round">
      <path d={arc(200, 340)} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - lp} />
      <path d={arc(20, 160)} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - lp} />
      {[340, 160].map((e, i) => { const [x, y] = pt(e); return <g key={i} transform={`translate(${x},${y}) rotate(${e + 90}) scale(${span(lp, 0.8, 1)})`}><path d="M-20,-18 L0,0 L-20,18" strokeWidth={9} /></g>; })}
    </g>
  );
  return (
    <OnCamFrame D={D} f={f} wav="4-08.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <defs><filter id="bl"><feGaussianBlur stdDeviation="9" /></filter></defs>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
          {/* AI 牌的箭头和红叉 */}
          <g opacity={fadeA}>
            <Arrow d="M1400,340 L1400,622" tip={[1400, 622]} ang={90} a={E.arrow.s} b={E.arrow.l + 10} f={f} sw={5} />
            {cr > 0 && (
              <g stroke={RED} strokeWidth={9} strokeLinecap="round">
                <line x1={1376} y1={456} x2={1376 + 48 * Math.min(1, cr * 2)} y2={456 + 48 * Math.min(1, cr * 2)} />
                {cr > 0.5 && <line x1={1424} y1={456} x2={1424 - 48 * (cr - 0.5) * 2} y2={456 + 48 * (cr - 0.5) * 2} />}
              </g>
            )}
          </g>
          {pl > 0 && (<g transform={`translate(${PL.cx},${PL.cy}) scale(${pl})`}>
            <rect x={-PL.w / 2} y={-PL.h / 2} width={PL.w} height={PL.h} rx={14} fill={INK} />
            <text x={0} y={16} textAnchor="middle" fontFamily="Serif" fontSize={50} fill={PAPER}>AI</text>
          </g>)}
          {/* 屏幕框 */}
          {sc > 0 && (
            <g fill="none" stroke={INK} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round">
              <rect x={SX1} y={SY1} width={SX2 - SX1} height={SY2 - SY1} rx={20} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - sc} />
              <path d={`M${(SX1 + SX2) / 2 - 40},${SY2 + 28} L${(SX1 + SX2) / 2 + 40},${SY2 + 28} M${(SX1 + SX2) / 2},${SY2} L${(SX1 + SX2) / 2},${SY2 + 28}`} opacity={span(sc, 0.7, 1)} />
            </g>
          )}
          {/* 光圈和加速线 */}
          {blur > 0 && (<g>
            <circle cx={LC[0]} cy={LC[1]} r={LR + 4} fill="none" stroke={RED} strokeWidth={22} opacity={0.42 * blur} filter="url(#bl)" />
            {[0, 60, 120, 180, 240, 300].map((a, i) => {
              const a0 = a + (i % 2 ? 14 : 0) - ang * 0.5, [x0, y0] = pt(a0, LR + 34), [x1, y1] = pt(a0 + 26, LR + 34);
              return <path key={i} d={`M${x0},${y0} A${LR + 34},${LR + 34} 0 0 1 ${x1},${y1}`} stroke={INK} strokeWidth={5} strokeLinecap="round" fill="none" opacity={0.55 * blur} />;
            })}
          </g>)}
          {/* 循环：高速时叠几层拖影 */}
          {v > 8 && [4, 3, 2, 1].map((k) => <g key={k}>{loopSvg(ang - k * v * 0.4, 0.17 * Math.min(1, (v - 8) / 10))}</g>)}
          {loopSvg(ang, 1)}
        </svg>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `scale(${1 + bump})`, transformOrigin: `${PER.cx}px ${PER.cy}px`}}>
          <Part name="person" cx={PER.cx} cy={PER.cy} w={PER.w} at={E.person.l} f={f} gate={[0.5, 1]} />
        </div>
        <Label x={PER.cx} y={790} w={220} p={span(f, E.person.l, E.person.l + 16)} size={28} italic color={INK}>scientists</Label>
        <Label x={LC[0]} y={348} w={200} p={span(f, E.trial.l - 4, E.trial.l + 14)} size={28} italic color={INK}>trial</Label>
        <Label x={LC[0]} y={708} w={200} p={span(f, E.error.l - 4, E.error.l + 14)} size={28} italic color={INK}>error</Label>
        <Label x={LC[0]} y={826} w={220} p={span(f, E.comp.l - 4, E.comp.l + 14)} size={28} italic color={INK}>computer</Label>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam408" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
