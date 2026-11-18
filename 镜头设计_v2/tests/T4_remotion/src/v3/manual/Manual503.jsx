// HKBU SCIE1007 课程作业的科普视频：第 5 章二维说明书页 5-03（C 画外音）"001's Kd: 9.2 micromolar … The clock read just 30 days"。
// 主线：七个小瓶（同 5-01、5-02）和一根 Kd 刻度。001 的红点从小瓶落到 9.2 micromolar；另外六个的灰点飞到 30 那条虚线上面，六个瓶变灰下沉（much weaker）；
// wild part 右边画出一个钟，指针转，计数跳到 30 days；下方七站路画出，Target 变红，001 小瓶飞到 Hit，Hit 变红，Target 到 Hit 红括号 30 days。
// 数字只写旁白里说的（9.2 micromolar、30、30 days）。时间全读 keys_5-03.json（事件表 映射/events/5-03.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_5-03.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const TX = (i) => 220 + 80 * i, TY = 380;                 // 七个小瓶
const AX = 860, AY0 = 220, AY1 = 640, Y92 = 600, Y30 = 440;  // Kd 刻度：越往上越弱
const SIX = [[920, 330], [975, 372], [1030, 306], [1085, 352], [1140, 318], [1195, 384]];
const CK = [1520, 470], CR = 110;                          // 钟
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"];
const RX0 = 230, RX1 = 1690, RY = 820;
const sx = (i) => RX0 + ((RX1 - RX0) * i) / (ST.length - 1);

const Scene = () => {
  const f = useCurrentFrame();
  const io = Easing.inOut(Easing.cubic);
  const kd = span(f, E.kd.s, E.kd.l + 14, ease);
  const val = span(f, E.val.s, E.val.l + 20, io);
  const line = span(f, E.line.s, E.line.l + 12, ease);
  const weak = span(f, E.weak.s, E.weak.l + 16, ease);
  const ck = span(f, E.wild.s, E.wild.l + 14, ease);
  const hand = span(f, E.clock.s, E.d30.l + 10, Easing.inOut(Easing.quad));
  const cnt = Math.round(30 * span(f, E.clock.s, E.d30.l, Easing.out(Easing.quad)));
  const road = span(f, E.road.s, E.road.l + 20, ease);
  const fly = span(f, E.fly.s, E.fly.l + 8, io);
  const hit = span(f, E.hit.s, E.hit.l + 6, out);
  const br = span(f, E.hit.l, E.hit.l + 24, ease);
  // 001 小瓶：从排头飞到 Hit
  const t0 = [TX(0) + (sx(1) - TX(0)) * fly, TY + (742 - TY) * fly - Math.sin(Math.PI * fly) * 120], tw = 40 - 10 * fly;
  const lab = [TX(0) + (sx(1) - TX(0)) * fly, 446 + (662 - 446) * fly - Math.sin(Math.PI * fly) * 120];
  const vp = [TX(0) + (AX + 25 - TX(0)) * val, 324 + (Y92 - 324) * val - Math.sin(Math.PI * val) * 90];
  const bead = [[0, 700, 200], [E.t001.l, 140, 300], [E.kd.l, 780, 200], [E.val.l, 1190, 650], [E.six.l, 770, 470], [E.line.l, 1290, 440],
                [E.up.l, 1260, 330], [E.weak.l, 1250, 235], [E.wild.l, 1720, 320], [E.clock.l, 1720, 560], [E.d30.l, 1760, 700],
                [E.road.l, 1790, 760], [E.tgt.l, 160, 760], [E.fly.l, 360, 700], [E.hit.l, 660, 960], [K.len_f, 661, 961]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("5-03.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.t001.s, E.val.l)}>001's Kd</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* Kd 刻度 */}
        <path d={`M${AX},${AY1} L${AX},${AY1 - (AY1 - AY0) * kd}`} stroke={INK} strokeWidth={4} strokeLinecap="round" />
        {[...Array(8)].map((_, i) => <path key={i} d={`M${AX - 12},${AY1 - i * 60} L${AX},${AY1 - i * 60}`} stroke={INK} strokeWidth={2.5} opacity={span(kd, i / 8, i / 8 + 0.2)} />)}
        {/* 30 那条虚线 */}
        {line > 0 && <path d={`M${AX - 20},${Y30} L${AX - 20 + 410 * line},${Y30}`} stroke={INK} strokeWidth={3} strokeDasharray="12 9" />}
        {/* 六个灰点：从各自的瓶飞到虚线上面 */}
        {f >= E.up.s && SIX.map(([x, y], k) => {
          const p = span(f, E.up.s + 3 * k, E.up.l + 18 + 3 * k, io);
          const x0 = TX(k + 1) - 80 * fly, y0 = 324 + 22 * weak;
          return <circle key={k} cx={x0 + (x - x0) * p} cy={y0 + (y - y0) * p - Math.sin(Math.PI * p) * 70} r={11} fill={SOFT} stroke={INK} strokeWidth={2} />;
        })}
        {/* 001 的红点 */}
        {f >= E.val.s && <circle cx={vp[0]} cy={vp[1]} r={13} fill={RED} stroke={INK} strokeWidth={2} />}
        {/* 钟 */}
        {ck > 0 && (
          <g>
            <circle cx={CK[0]} cy={CK[1]} r={CR} fill="none" stroke={INK} strokeWidth={4} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - ck} />
            {[...Array(12)].map((_, i) => { const a = i * Math.PI / 6; return <path key={i} d={`M${CK[0] + 92 * Math.cos(a)},${CK[1] + 92 * Math.sin(a)} L${CK[0] + 104 * Math.cos(a)},${CK[1] + 104 * Math.sin(a)}`} stroke={INK} strokeWidth={3} opacity={span(ck, 0.5, 1)} />; })}
            {(() => { const a = -Math.PI / 2 + hand * Math.PI * 2 * 3; return <path d={`M${CK[0]},${CK[1]} L${CK[0] + 84 * Math.cos(a)},${CK[1] + 84 * Math.sin(a)}`} stroke={RED} strokeWidth={5} strokeLinecap="round" opacity={span(ck, 0.6, 1)} />; })()}
            {(() => { const a = -Math.PI / 2 + hand * Math.PI * 2 * 0.25; return <path d={`M${CK[0]},${CK[1]} L${CK[0] + 56 * Math.cos(a)},${CK[1] + 56 * Math.sin(a)}`} stroke={INK} strokeWidth={7} strokeLinecap="round" opacity={span(ck, 0.6, 1)} />; })()}
            <circle cx={CK[0]} cy={CK[1]} r={8} fill={INK} opacity={span(ck, 0.6, 1)} />
          </g>
        )}
        {/* 路 */}
        {road > 0 && <path d={`M${RX0 - 110},${RY} L${RX0 - 110 + (RX1 - RX0 + 170) * road},${RY}`} stroke={INK} strokeWidth={7} strokeLinecap="round" />}
        {hit > 0 && <path d={`M${RX0 - 110},${RY} L${RX0 - 110 + (sx(1) - RX0 + 110) * hit},${RY}`} stroke={RED} strokeWidth={7} strokeLinecap="round" />}
        {ST.map((s, i) => {
          const p = span(road, (i + 0.3) / 7.6, (i + 1.1) / 7.6, out);
          const on = i === 0 ? span(f, E.tgt.s, E.tgt.l) : i === 1 ? hit : 0;
          const j = i === 0 && f > E.tgt.s ? 1 + 0.4 * Math.exp(-(f - E.tgt.s) / 8) : i === 1 && f > E.hit.s ? 1 + 0.4 * Math.exp(-(f - E.hit.s) / 8) : 1;
          return <circle key={s} cx={sx(i)} cy={RY} r={16 * p * j} fill={on > 0.5 ? RED : PAPER} stroke={i < 2 ? INK : "#9A968C"} strokeWidth={4} />;
        })}
        {/* Target → Hit 红括号 */}
        {br > 0 && <path d={`M${sx(0)},892 L${sx(0)},904 L${sx(0) + (sx(1) - sx(0)) * br},904${br > 0.97 ? ` L${sx(1)},892` : ""}`} fill="none" stroke={RED} strokeWidth={4} />}
      </svg>
      <Label x={AX} y={170} w={120} size={40} p={span(f, E.kd.s, E.kd.l + 10)}>Kd</Label>
      <Label x={AX + 50} y={Y92 - 22} w={300} size={34} align="left" color={RED} p={span(f, E.val.l, E.val.e)}>9.2 micromolar</Label>
      <Label x={AX - 70} y={Y30 - 20} w={60} size={32} p={span(f, E.line.s + 4, E.line.l + 14)}>30</Label>
      <Label x={1060} y={236} w={300} size={32} italic color={SOFT} p={span(f, E.weak.s, E.weak.e)}>much weaker</Label>

      {/* 六个瓶：变灰下沉 */}
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div key={i} style={{position: "absolute", left: 0, top: 22 * weak, width: 1920, height: 1080, opacity: 1 - 0.55 * weak, filter: `grayscale(${weak})`}}>
          <Part name="tube" cx={TX(i) - 80 * fly} cy={TY} w={40} at={E.six.s + 3 * i} f={f} gate={[0.5, 1]} flood={14} />
        </div>
      ))}
      {/* 001 小瓶 */}
      <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${TX(0)}px ${TY}px`,
                   transform: `translate(${t0[0] - TX(0)}px, ${t0[1] - TY}px) scale(${tw / 40})`}}>
        <Part name="tube" cx={TX(0)} cy={TY} w={40} at={E.t001.s} f={f} gate={[0.5, 1]} flood={14} />
      </div>
      <Label x={lab[0]} y={lab[1]} w={100} size={32} color={RED} p={span(f, E.t001.s + 4, E.t001.l + 20)}>001</Label>

      <Pen x={1420} y={290} size={44} p={span(f, E.wild.s, E.wild.e)}>the wild part</Pen>
      <div style={{position: "absolute", left: CK[0] - 160, top: 600, width: 320, textAlign: "center", fontSize: 64, color: RED, opacity: span(f, E.clock.s, E.clock.s + 10),
                   transform: `scale(${1 + 0.18 * (f > E.d30.l ? Math.exp(-(f - E.d30.l) / 7) : 0)})`}}>{cnt} days</div>

      {ST.map((s, i) => <Label key={s} x={sx(i)} y={RY + 30} w={180} size={30} color={i < 2 ? INK : "#8A867C"} p={span(road, (i + 0.5) / 7.6, (i + 1.3) / 7.6)}>{s}</Label>)}
      <Label x={(sx(0) + sx(1)) / 2} y={912} w={200} size={30} color={RED} p={span(f, E.hit.l + 10, E.hit.e)}>30 days</Label>
      <Label x={510} y={724} w={330} size={32} italic align="left" color={RED} p={span(f, E.hit.s, E.hit.e)}>first confirmed hit</Label>

      <Source p={span(f, E.kd.l, E.kd.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual503" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
