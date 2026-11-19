// HKBU SCIE1007 课程作业的科普视频：第 8 章二维说明书页 8-02（画外音）总结目标 1。
// 主线：七站路线（照 2-08）回来，find / assess 两段括出；路起点上方四个格子依次填进四个工具的小动图
// （漏斗挑出 CDK20、珠子串折叠、循环吐出钥匙、长条排序打勾）；最后 Our objectives 便签落下，1 打勾，红批注 for this case。
// 时间全读 keys_8-02.json（事件表 映射/events/8-02.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_8-02.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, evMap, Label, Pen, PageFrame, Source, Lens, guidePlan} from "./kit.jsx";

const E = evMap(K);
const GP = guidePlan(K);   // 视线引导（11-20，替代红色料珠）：事件表 guide 字段 → resolve.py → keys.guides
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"];
const RX0 = 230, RX1 = 1690, RY = 720;
const sx = (i) => RX0 + ((RX1 - RX0) * i) / (ST.length - 1);
const CXS = [250, 480, 710, 940], CY = 450, CW = 200, CH = 176;
const CAP = ["a target from data", "the lock's shape", "new keys", "which ones to make"];
const BARS = [0.5, 0.92, 0.3, 0.72];
const FOLD = [[-40, 20], [-20, 34], [2, 26], [12, 6], [-6, -12], [-28, -18], [-10, -36]];

const Scene = () => {
  const f = useCurrentFrame();
  const road = span(f, E.road.s, E.road.e, ease);
  const io = Easing.inOut(Easing.cubic);
  const fold = span(f, E.shape.s, E.shape.l, io);
  const sort = span(f, E.make.s, E.make.l, io);
  const order = [...BARS.keys()].sort((a, b) => BARS[b] - BARS[a]);
  let rot = 0;
  for (let t = E.design.s; t <= f; t++) rot += 3;
  const note = span(f, E.obj.s, E.obj.l + 8, Easing.out(Easing.back(1.3)));
  return (
    <Lens plan={GP} f={f}>
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("8-02.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 58, fontSize: 44, lineHeight: "54px"}}>
        <Write p={span(f, E.q.s, E.help.e)}>How can computer-aided methods <span style={{borderBottom: `3px solid rgba(200,16,46,${span(f, E.help.s, E.help.l)})`}}>help</span> scientists</Write><br />
        <Write p={span(f, E.road.s, E.cand.l)}>find and assess cancer drug candidates?</Write>
      </div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 路 */}
        <path d={`M${RX0 - 110},${RY} L${RX1 + 60},${RY}`} stroke={INK} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - road} />
        {ST.map((s, i) => {
          const p = span(road, (i + 0.4) / (ST.length + 0.6), (i + 1.2) / (ST.length + 0.6), out);
          const lit = f >= E.met.l && i < 2;
          return <circle key={s} cx={sx(i)} cy={RY} r={16 * p} fill={lit ? RED : PAPER} stroke={i < 4 ? INK : "#9A968C"} strokeWidth={4} />;
        })}
        {/* find / assess 括号 */}
        {[[E.find, 0, 1, RED], [E.assess, 2, 3, SOFT]].map(([ev, a, b, c], i) => {
          const p = span(f, ev.s, ev.l + 10, ease), x0 = sx(a) - 50, x1 = sx(b) + 50;
          return <path key={i} d={`M${x0},${RY + 72} L${x0},${RY + 84} L${x0 + (x1 - x0) * p},${RY + 84}${p > 0.98 ? ` L${x1},${RY + 72}` : ""}`} fill="none" stroke={c} strokeWidth={3.5} />;
        })}
        {/* 四个格子 */}
        {CXS.map((cx, i) => {
          const g = span(f, E.four.s + 4 * i, E.four.l + 4 * i, out);
          return g > 0 && <rect key={i} x={cx - CW / 2} y={CY - CH / 2} width={CW} height={CH} rx={10} fill="#F4F1EA" stroke={INK} strokeWidth={3}
                                transform={`translate(${cx} ${CY}) scale(${g}) translate(${-cx} ${-CY})`} />;
        })}
        {/* 1 漏斗 */}
        {f >= E.pick.s && (() => { const cx = CXS[0], p = span(f, E.pick.s, E.pick.l + 6, ease); return (
          <g>
            <path d={`M${cx - 56},${CY - 36} L${cx + 56},${CY - 36} L${cx + 14},${CY + 22} L${cx + 14},${CY + 40} L${cx - 14},${CY + 40} L${cx - 14},${CY + 22} Z`}
                  fill="none" stroke={INK} strokeWidth={3.5} strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
            {[-30, 0, 30].map((dx, k) => { const q = span(f, E.data.s + 5 * k, E.data.l + 5 * k, Easing.in(Easing.quad)); return f >= E.pick.l && (
              <rect key={k} x={cx + dx * (1 - 0.6 * q) - 14} y={CY - 76 + 40 * q} width={28} height={20} rx={3} fill="#F4F1EA" stroke={INK} strokeWidth={2.5} opacity={1 - span(q, 0.75, 1)} />); })}
            {f >= E.target.s && <circle cx={cx} cy={CY + 58} r={10 * span(f, E.target.s, E.target.l + 6, Easing.out(Easing.back(2)))} fill={RED} />}
          </g>); })()}
        {/* 2 珠子串折叠 */}
        {f >= E.pred.s && FOLD.map(([x, y], k) => {
          const cx = CXS[1], a = span(f, E.pred.s + 3 * k, E.pred.s + 3 * k + 8, out);
          const px = cx - 66 + k * 22 + (cx + x - (cx - 66 + k * 22)) * fold, py = CY + (CY + y - CY) * fold;
          return <g key={k}>
            {k > 0 && <line x1={cx - 66 + (k - 1) * 22 + (cx + FOLD[k - 1][0] - (cx - 66 + (k - 1) * 22)) * fold} y1={CY + FOLD[k - 1][1] * fold} x2={px} y2={py} stroke={INK} strokeWidth={2.5} opacity={a} />}
            <circle cx={px} cy={py} r={9 * a} fill={fold > 0.9 ? INK : "#F4F1EA"} stroke={INK} strokeWidth={2.5} />
          </g>;
        })}
        {/* 3 循环 */}
        {f >= E.design.s && (() => { const cx = CXS[2], p = span(f, E.design.s, E.design.l + 8, ease); return (
          <g>
            <circle cx={cx} cy={CY} r={44} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
            {p >= 1 && [0, 120, 240].map((a) => { const t = (a + rot) * Math.PI / 180; return (
              <path key={a} d="M-7,-6 L3,0 L-7,6" fill="none" stroke={INK} strokeWidth={3} strokeLinecap="round" transform={`translate(${cx + 44 * Math.cos(t)} ${CY + 44 * Math.sin(t)}) rotate(${a + rot + 90})`} />); })}
          </g>); })()}
        {/* 4 长条排序 */}
        {f >= E.rank.s && BARS.map((w, k) => {
          const cx = CXS[3], g = span(f, E.rank.s + 4 * k, E.rank.l + 4 * k, out);
          const y0 = CY - 54 + k * 30, y1 = CY - 54 + order.indexOf(k) * 30, y = y0 + (y1 - y0) * sort;
          const tick = order.indexOf(k) < 2 ? span(f, E.make.l - 4 + 6 * order.indexOf(k), E.make.l + 6 + 6 * order.indexOf(k)) : 0;
          return <g key={k}>
            <rect x={cx - 70} y={y} width={120 * w * g} height={18} fill={tick > 0 ? RED : INK} opacity={0.85} />
            {tick > 0 && <path d={`M${cx + 60},${y + 9} l6,7 l12,-14`} fill="none" stroke={RED} strokeWidth={3.5} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - tick} />}
          </g>;
        })}
      </svg>
      {ST.map((s, i) => (
        <Label key={s} x={sx(i)} y={RY + 26} w={180} size={28} color={i < 4 ? INK : "#8A867C"} p={span(road, (i + 0.6) / (ST.length + 0.6), (i + 1.4) / (ST.length + 0.6))}>{s}</Label>
      ))}
      <Label x={(sx(0) + sx(1)) / 2} y={RY + 92} w={200} size={30} italic color={RED} p={span(f, E.find.s, E.find.e)}>find</Label>
      <Label x={(sx(2) + sx(3)) / 2} y={RY + 92} w={200} size={30} italic color={SOFT} p={span(f, E.assess.s, E.assess.e)}>assess</Label>
      {[0, 1, 2].map((k) => <Part key={k} name="key" cx={RX0 - 60 + k * 6} cy={RY - 44 - k * 22} w={70} at={E.cand.s + 4 * k} f={f} gate={[0.1, 0.5]} />)}
      <Label x={595} y={300} w={760} size={32} italic p={span(f, E.case.s, E.points.e)}>in this case, at four points</Label>
      {CXS.map((cx, i) => (
        <React.Fragment key={i}>
          <div style={{position: "absolute", left: cx - CW / 2 - 14, top: CY - CH / 2 - 14, width: 34, height: 34, borderRadius: 17, background: INK, color: PAPER,
                       textAlign: "center", font: "24px/34px Serif", transform: `scale(${span(f, E.points.s + 3 * i, E.points.l + 6 + 3 * i, Easing.out(Easing.back(2)))})`}}>{i + 1}</div>
          <Label x={cx} y={CY + CH / 2 + 10} w={220} size={22} italic p={span(f, [E.pick, E.pred, E.design, E.rank][i].s, [E.target, E.shape, E.keys, E.make][i].e)}>{CAP[i]}</Label>
        </React.Fragment>
      ))}
      <div style={{position: "absolute", left: CXS[0] + 16, top: CY + 46, fontSize: 18, color: RED, opacity: span(f, E.target.l, E.target.l + 10)}}>CDK20</div>
      {[0, 1, 2].map((k) => <Part key={k} name="key" cx={CXS[2] + 72} cy={CY - 52 + k * 26} w={40} at={E.keys.s + 3 * k} f={f} gate={[0.1, 0.5]} />)}

      {/* Our objectives 便签 */}
      {note > 0 && (
        <div style={{position: "absolute", left: 1220, top: 210, width: 560, height: 300, background: "#F7F3E8", boxShadow: "0 6px 18px rgba(0,0,0,0.12)",
                     border: "1.5px solid rgba(31,30,28,0.25)", transform: `translateY(${-240 * (1 - note)}px) rotate(-2deg)`, opacity: Math.min(1, note * 1.5)}}>
          <div style={{position: "absolute", left: 32, top: 22, fontSize: 40}}>Our objectives</div>
          {[0, 1].map((r) => (
            <div key={r} style={{position: "absolute", left: 32, top: 100 + r * 84, width: 44, height: 44, borderRadius: 22, border: `3px solid ${r ? "#9A968C" : RED}`,
                                 color: r ? "#9A968C" : RED, textAlign: "center", font: "28px/38px Serif",
                                 transform: `scale(${r ? 1 : span(f, E.first.s, E.first.l + 6, Easing.out(Easing.back(2.2)))})`}}>{r + 1}</div>
          ))}
          <div style={{position: "absolute", left: 92, top: 104, fontSize: 28}}><Write p={span(f, E.objtxt.s, E.objtxt.e)}>computer-aided methods help</Write></div>
          <div style={{position: "absolute", left: 92, top: 200, width: 400, borderBottom: "2px dashed #B9B4A8", height: 24}} />
          {f >= E.met.s && <svg width={90} height={80} style={{position: "absolute", left: 460, top: 70}}>
            <path d="M10,40 L34,64 L82,8" fill="none" stroke={RED} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1"
                  strokeDashoffset={1 - span(f, E.met.s, E.met.l + 6, out)} /></svg>}
        </div>
      )}
      <Pen x={1300} y={530} p={span(f, E.thiscase.s, E.thiscase.e)} size={40}>(for this case)</Pen>

      <Source p={span(f, E.q.l, E.q.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
    </AbsoluteFill>
    </Lens>
  );
};

const Root = () => <Composition id="Manual802" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
