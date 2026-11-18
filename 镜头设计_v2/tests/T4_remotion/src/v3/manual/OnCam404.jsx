// HKBU SCIE1007 课程作业的科普视频：出镜 4-04+4-05（C）"So what did they do? They cut the tail off. The AI made the guess. A human caught the problem."（第 2 版，重写）
// 讲解卡：一串珠子折成蛋白，尾巴三颗松垂的珠子长出；cut 红虚线加剪刀，tail 剪刀合拢，off 尾巴飘走变灰；
// 再写出 The AI made the guess. 和 A human caught the problem.（后半红色下划线）。时间全读 oncam_4-04_4-05.json。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_4-04_4-05.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam, PersonFront} from "./oncam.jsx";

const FX1 = 1290, FY1 = 200, FX2 = 1870, FY2 = 900;
const CX = 1530, CY = 440, SC = 1.7, BR = 22, BLUE = "#2C40A6";
const RAW = [[-80, 50], [-40, 70], [0, 54], [22, 16], [-14, -14], [-54, -24], [-86, -58], [-46, -92], [-4, -72], [36, -48], [74, -10], [112, 28], [146, 60]];
const P = RAW.map(([x, y]) => [CX + x * SC, CY + y * SC]);
const NB = 10;                                        // 前 10 颗是蛋白，后 3 颗是尾巴
const MID = [(P[9][0] + P[10][0]) / 2, (P[9][1] + P[10][1]) / 2];
const back = Easing.out(Easing.back(1.8));
const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const chainIn = span(f, E.chain.s, E.chain.l + 24, ease);
  const tailIn = span(f, E.tail.s, E.tail.l + 24, ease);
  const shown = (i) => (i < NB ? span(chainIn, i / NB * 0.8, i / NB * 0.8 + 0.2, back) : span(tailIn, (i - NB) / 3 * 0.7, (i - NB) / 3 * 0.7 + 0.3, back));
  const cutP = span(f, E.cutline.s, E.cutline.l + 10, ease);
  const snip = span(f, E.snip.s, E.snip.l, Easing.in(Easing.quad));
  const fl = span(f, E.float.s, E.float.l + 8, ease);
  const pulseP = span(f, E.pulse.s, E.pulse.s + 24);
  const pulse = 1 + 0.07 * Math.sin(Math.PI * pulseP);
  const sciA = (1 - snip) * 0.9 + 0.04 * Math.sin(f / 2) * (1 - snip) * cutP;     // 剪刀张口（弧度）
  const sci = cutP * (1 - span(f, E.snip.l + 6, E.snip.l + 22));
  const tailGrey = mix([200, 16, 46], [140, 138, 130], fl);
  const tailStroke = `rgb(${tailGrey.join(",")})`;
  const tx = 40 * fl, ty = -95 * fl, rot = 26 * fl;
  const TC = [(P[10][0] + P[12][0]) / 2, (P[10][1] + P[12][1]) / 2];
  const ux = -0.72, uy = 0.70;                                                  // 沿链方向到切口：切口法线
  const px = 0.72, py = -0.70;
  const pivot = [MID[0] + px * 92, MID[1] + py * 92];       // 刀尖合拢时正好落在切口上
  const ang = Math.atan2(-py, -px) * 180 / Math.PI;
  const l1 = span(f, E.ai.l, E.ai.e), l2 = span(f, E.human.l, E.human.e), ul = span(f, E.under.s, E.under.e, ease);
  const link = (i, extra) => {
    const a = P[i], b = P[i + 1], s = Math.min(shown(i), shown(i + 1));
    return s > 0 ? <line key={i} x1={a[0]} y1={a[1]} x2={a[0] + (b[0] - a[0]) * s} y2={a[1] + (b[1] - a[1]) * s} stroke={INK} strokeWidth={4} strokeLinecap="round" {...extra} /> : null;
  };
  const bead = (i) => {
    const s = shown(i);
    if (s <= 0) return null;
    const t = i >= NB;
    return <circle key={i} cx={P[i][0]} cy={P[i][1]} r={BR * s} fill={t ? "#E9E4D6" : BLUE} stroke={t ? tailStroke : INK} strokeWidth={t ? 3.5 : 3} strokeDasharray={t ? "6 4" : undefined} />;
  };
  return (
    <OnCamFrame D={D} f={f} wav="4-04_4-05.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
          {/* 蛋白（10 颗）整串一跳 */}
          <g style={{transformOrigin: `${CX}px ${CY}px`, transform: `scale(${pulse})`}}>
            {[...Array(NB - 1)].map((_, i) => link(i))}
            {[...Array(NB)].map((_, i) => bead(i))}
            {snip < 1 && link(NB - 1, {opacity: 1 - snip, strokeDasharray: snip > 0 ? "6 5" : undefined})}
          </g>
          {/* 尾巴：飘走变灰 */}
          <g style={{transformOrigin: `${TC[0]}px ${TC[1]}px`, transform: `translate(${tx}px,${ty}px) rotate(${rot}deg)`}} opacity={1 - 0.62 * fl}>
            {link(10, {stroke: tailStroke})}{link(11, {stroke: tailStroke})}
            {[10, 11, 12].map((i) => bead(i))}
          </g>
          {/* 红虚线 + 剪刀 */}
          {cutP > 0 && (
            <g opacity={sci}>
              <line x1={MID[0] - px * 50} y1={MID[1] - py * 50} x2={MID[0] - px * 50 + px * 100 * cutP} y2={MID[1] - py * 50 + py * 100 * cutP} stroke={RED} strokeWidth={4.5} strokeDasharray="9 7" strokeLinecap="round" />
              <g transform={`translate(${pivot[0]},${pivot[1]}) rotate(${ang}) scale(1.45)`} stroke={INK} strokeWidth={4.5} strokeLinecap="round" fill="none">
                {[1, -1].map((s) => (
                  <g key={s} transform={`rotate(${s * sciA * 180 / Math.PI * 0.5})`}>
                    <path d={`M-2,${-6 * s} C24,${-8 * s} 50,${-5 * s} 70,0 C48,${1 * s} 22,${2 * s} -2,${2 * s} Z`} fill={INK} stroke="none" />
                    <line x1={0} y1={0} x2={-22} y2={s * 3} />
                    <ellipse cx={-36} cy={s * 7} rx={15} ry={11} fill={PAPER} />
                  </g>
                ))}
                <circle cx={0} cy={0} r={4} fill={INK} />
              </g>
            </g>
          )}
        </svg>
        <div style={{position: "absolute", left: 1326, top: 700, fontSize: 42, whiteSpace: "nowrap"}}><Write p={l1}>The AI made the guess.</Write></div>
        <div style={{position: "absolute", left: 1326, top: 770, fontSize: 42, whiteSpace: "nowrap"}}>
          <Write p={l2}>
            <span>A human </span>
            <span style={{position: "relative"}}>caught the problem.<span style={{position: "absolute", left: 0, bottom: -2, height: 5, width: `${ul * 100}%`, background: RED, borderRadius: 3}} /></span>
          </Write>
        </div>
      </div>
      <PersonFront D={D} f={f} x0={FX1} />
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam404" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
