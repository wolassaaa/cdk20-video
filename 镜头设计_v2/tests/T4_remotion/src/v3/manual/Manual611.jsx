// HKBU SCIE1007 课程作业的科普视频：第 6 章二维说明书页 6-11（B 画外音）"the end of that road"。
// 同一条七站路（坐标照 Manual208：RX0 230、RX1 1690、RY 600），048 停在 Cells。镜头先往右平移到远端（Approval 外画红虚线圈）；
// 两个 AI-assisted 小牌子从左边走来、走过 048；一个走到 Approval，牌子改写成 lirafugratinib，远端写 September 2026 / approved in the US / for a bile duct cancer；
// 另一个在半路倒下、变灰、打红叉，写 failed along the way；"048" 时镜头拉回全景，048 跳一下；makers 小人；通往 trials 的虚线箭头被红杠挡住；
// shared it 三个研究者长出，048 各连一条线，写 shared with other researchers。
// 时间全读 keys_6-11.json（事件表 映射/events/6-11.json，用 ev_make.py 简写生成）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_6-11.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"];
const RX0 = 230, RX1 = 1690, RY = 600;
const sx = (i) => RX0 + ((RX1 - RX0) * i) / (ST.length - 1);
// 镜头：V0 = 6-10 的取景；V1 = 平移到远端；V2 = 全景（缩到 0.8，远端的字也在画里）
const V0 = [1, 0, 0], V1 = [1, -420, 0], V2 = [0.8, 8, 140];
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const LA = RY - 300, LB = RY - 200, L48 = RY - 110;   // 牌子 A、B、048 的高度（各走各的道）

const Tag = ({x, y, w, h = 64, children, fill = PAPER, stroke = INK, color = INK, size = 30, op = 1, pole = true, rot = 0, sc = 1}) => (
  <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: op}}>
    {pole && <div style={{position: "absolute", left: x - 1.5, top: y + h / 2, width: 3, height: RY - y - h / 2, background: stroke}} />}
    <div style={{position: "absolute", left: x - w / 2, top: y - h / 2, width: w, height: h, boxSizing: "border-box", border: `3px solid ${stroke}`, borderRadius: 10, background: fill,
                 color, fontSize: size, lineHeight: `${h - 6}px`, textAlign: "center", whiteSpace: "nowrap", transform: `rotate(${rot}deg) scale(${sc})`}}>{children}</div>
  </div>
);

const Scene = () => {
  const f = useCurrentFrame();
  const io = Easing.inOut(Easing.cubic);
  const pan = span(f, E.pan.s, E.pan.l, io), back = span(f, E.back.s, E.back.l, io);
  const [s, tx, ty] = mix(mix(V0, V1, pan), V2, back);
  // 牌子 A、B 的位置
  const tin = span(f, E.tags.s, E.tags.l, ease), w1 = span(f, E.walk1.s, E.walk1.l, ease), w2 = span(f, E.walk2.s, E.walk2.l, ease), ag = span(f, E.ago.s, E.ago.l, ease);
  const ax = 120 + 500 * tin + 200 * w1 + (sx(5) - 820) * w2 + (sx(6) - sx(5)) * ag;
  const bxp = 20 + 500 * tin + 180 * w1 + (1325 - 700) * w2;
  const step = (p) => Math.abs(Math.sin(Math.PI * 4 * p)) * 8 * (p > 0 && p < 1 ? 1 : 0);   // 走路时上下一颠一颠
  const ayb = step(w1) + step(w2) + step(ag), byb = step(w1) + step(w2);
  const nm = span(f, E.name.s, E.name.l, ease);
  const appr = span(f, E.appr.s, E.appr.l + 6, out);
  const shake = f >= E.oth.s && f < E.fail.s ? Math.sin((f - E.oth.s) / 1.8) * 5 * Math.exp(-(f - E.oth.s) / 14) : 0;
  const fall = span(f, E.fail.s, E.fail.l + 10, Easing.in(Easing.quad));
  const fx = span(f, E.fail.l + 4, E.fail.l + 20, ease);
  const ring = span(f, E.ring.s, E.ring.l + 8, ease);
  const pulse = f > E.back.l ? 1 + 0.18 * Math.exp(-(f - E.back.l) / 7) * Math.abs(Math.sin((f - E.back.l) / 3)) : 1;
  const nott = span(f, E.nott.s, E.nott.l + 14, ease), bar = span(f, E.nott.l + 10, E.nott.l + 22, out);
  const lines = span(f, E.sh.s + 10, E.sh.l + 30, ease), red = span(f, E.res.s, E.res.l + 10);
  const RES = [[800, 300], [960, 250], [1120, 300]];
  const bead = [[0, 600, 800], [E.title.l, 700, 820], [E.pan.l, 1560, 960], [E.ring.l, 1800, 560], [E.tags.l, 700, 820], [E.ai.l, 820, 760],
                [E.walk1.l, 1000, 800], [E.walk2.l, 1500, 440], [E.date.l, 1490, 720], [E.ago.l, 1860, 300], [E.name.l, 1500, 770],
                [E.appr.l, 1880, 640], [E.bile.l, 1880, 930], [E.oth.l, 1300, 330], [E.fail.l, 1300, 790], [E.back.l, 1090, 560],
                [E.mk.l, 720, 470], [E.nott.l, 1300, 470], [E.sh.l, 680, 240], [E.res.l, 1260, 220], [K.len_f, 1261, 221]];
  const atA = f >= E.ago.l;
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK, overflow: "hidden"}}>
      <Audio src={staticFile("6-11.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: "0 0", transform: `translate(${tx}px, ${ty}px) scale(${s})`}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <path d={`M${RX0 - 110},${RY} L${RX1 + 60},${RY}`} stroke={INK} strokeWidth={7} strokeLinecap="round" />
          {/* 048 走过的一段（6-10 结束时的红线） */}
          <path d={`M${RX0 - 110},${RY} L${sx(3)},${RY}`} stroke={RED} strokeWidth={7} strokeLinecap="round" />
          {ST.map((st, i) => {
            const grey = i >= 4 && !(i === 6 && appr > 0.5);
            const fill = i === 0 || i === 1 || i === 3 || (i === 6 && appr > 0.5) ? RED : PAPER;
            return (
              <g key={st}>
                <circle cx={sx(i)} cy={RY} r={16 * (i === 6 ? 1 + 0.35 * Math.sin(Math.PI * appr) : 1)} fill={fill} stroke={grey ? SOFT : INK} strokeWidth={4} strokeDasharray={i === 4 || i === 5 ? "6 5" : undefined} />
                {i === 2 && <circle cx={sx(2)} cy={RY} r={8} fill={RED} />}
              </g>
            );
          })}
          {/* Approval 外红圈：先虚线，approved 变实 */}
          {ring > 0 && <circle cx={sx(6)} cy={RY} r={38} fill="none" stroke={RED} strokeWidth={4} strokeDasharray={appr > 0.5 ? undefined : "8 7"}
                               transform={`rotate(-90 ${sx(6)} ${RY})`} style={{clipPath: `inset(0 0 ${100 - 100 * ring}% 0)`}} />}
          {/* 048 → trials 的虚线箭头，被红杠挡住 */}
          {nott > 0 && (
            <g fill="none" strokeLinecap="round" strokeLinejoin="round">
              <path d={`M1072,470 L${1072 + 118 * nott},470`} stroke={INK} strokeWidth={4} strokeDasharray="10 9" />
              {nott > 0.85 && <path d="M1176,458 L1192,470 L1176,482" stroke={INK} strokeWidth={4} />}
              <path d={`M1210,${470 - 30 * bar} L1210,${470 + 30 * bar}`} stroke={RED} strokeWidth={7} />
            </g>
          )}
          {/* 048 到三个研究者的连线 */}
          {lines > 0 && RES.map(([x, y], i) => {
            const p = span(lines, i * 0.2, i * 0.2 + 0.6);
            const x0 = 960, y0 = L48 - 42, y1 = y + 42;
            return <path key={i} d={`M${x0},${y0} L${x0 + (x - x0) * p},${y0 + (y1 - y0) * p}`} stroke={red > 0.5 ? RED : INK} strokeWidth={3.5} strokeLinecap="round" />;
          })}
        </svg>
        {ST.map((st, i) => <Label key={st} x={sx(i)} y={RY + 32} w={180} size={30} color={i >= 4 && !(i === 6 && appr > 0.5) ? SOFT : INK} p={1}>{st}</Label>)}

        {/* 牌子 B：AI-assisted，半路倒下变灰 */}
        {tin > 0 && (
          <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translate(${fall * 0}px, ${fall * (530 - LB)}px)`}}>
            <Tag x={bxp} y={LB - byb} w={190} pole={fall < 0.05} rot={shake + 10 * fall} stroke={fall > 0.5 ? SOFT : INK} color={fall > 0.5 ? SOFT : INK}>
              <Write p={span(f, E.ai.s + 4, E.ai.l + 18)}>AI-assisted</Write>
            </Tag>
          </div>
        )}
        {/* 牌子 A：走到 Approval，改写成药名 */}
        {tin > 0 && (
          <Tag x={ax} y={LA - ayb} w={190 + 70 * nm} stroke={atA && appr > 0.5 ? RED : INK} sc={1 + 0.12 * Math.sin(Math.PI * appr)}>
            {nm < 1 && <span style={{opacity: 1 - nm, position: "absolute", left: 0, right: 0}}><Write p={span(f, E.ai.s, E.ai.l + 14)}>AI-assisted</Write></span>}
            {nm > 0 && <span style={{opacity: nm, fontStyle: "italic"}}>lirafugratinib</span>}
          </Tag>
        )}
        {/* A 牌子上的勾 */}
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <path d={`M${sx(6) + 150},${LA - 8} L${sx(6) + 164},${LA + 8} L${sx(6) + 190},${LA - 24}`} fill="none" stroke={RED} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round"
                pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(f, E.appr.l, E.appr.l + 14)} />
          {/* B 上的红叉 */}
          {fx > 0 && <g stroke={RED} strokeWidth={6} strokeLinecap="round">
            <path d={`M1297,504 L${1297 + 56 * span(fx, 0, 0.5)},${504 + 52 * span(fx, 0, 0.5)}`} />
            {fx > 0.5 && <path d={`M1353,504 L${1353 - 56 * span(fx, 0.5, 1)},${504 + 52 * span(fx, 0.5, 1)}`} />}
          </g>}
        </svg>
        <Label x={1300} y={700} w={340} size={30} italic color={SOFT} p={span(f, E.fail.l, E.fail.e)}>failed along the way</Label>

        {/* 远端的字 */}
        <div style={{position: "absolute", left: 1560, top: 700, whiteSpace: "nowrap", lineHeight: 1}}>
          <div style={{fontSize: 30, color: SOFT}}><Write p={span(f, E.date.s, E.date.e)}>September 2026</Write></div>
          <div style={{fontSize: 46, marginTop: 8, fontStyle: "italic"}}><Write p={span(f, E.name.s, E.name.l + 30)}>lirafugratinib</Write></div>
          <div style={{fontSize: 34, marginTop: 10, color: RED}}><Write p={span(f, E.appr.s, E.appr.e)}>approved in the US</Write></div>
          <div style={{fontSize: 30, marginTop: 10}}><Write p={span(f, E.bile.s, E.bile.e)}>for a bile duct cancer</Write></div>
        </div>

        {/* 048 */}
        <div style={{position: "absolute", left: 958.5, top: L48 + 42, width: 3, height: RY - L48 - 42, background: INK}} />
        <div style={{position: "absolute", left: 860, top: L48 - 42, width: 200, height: 84, background: INK, color: PAPER, borderRadius: 12, textAlign: "center",
                     fontSize: 60, lineHeight: "86px", transform: `scale(${pulse})`}}>048</div>
        <Part name="person_r" cx={820} cy={500} w={44} at={E.mk.s} f={f} gate={[0.5, 1]} flood={14} />
        <Label x={820} y={544} w={160} size={24} italic color={SOFT} p={span(f, E.mk.l, E.mk.e)}>its makers</Label>
        <Pen x={1078} y={384} size={40} p={span(f, E.nott.l, E.nott.e)}>not to trials</Pen>
        {RES.map(([x, y], i) => <Part key={i} name="person_w" cx={x} cy={y} w={48} at={E.sh.s + 4 * i} f={f} gate={[0.5, 1]} flood={14} />)}
        <Label x={960} y={150} w={560} size={34} italic p={span(f, E.res.s, E.res.e)}>shared with other researchers</Label>
        <Bead K={bead} f={f} />
      </div>
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>The end of that road</Write></div>
      <Source p={1}>Wang et al., Pharmaceuticals 2023; FDA, Sep 2026; GEN, Jan 2023 · Illustration</Source>
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual611" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
