// HKBU SCIE1007 课程作业的科普视频：第 6 章二维说明书页 6-09（B 画外音）"further down the road"。
// 一条透视路伸向远处（近处左下，远处右上）；路边四个虚线框（= 可能，还没量过）依次亮起：钥匙打叉、钞票、小鼠、废料桶，每个由三变一、红色向下箭头；
// Computing 机柜和插头用 SOFT 色（代价），电线一跳一跳；real prize 路尽头红色虚线圈加问号；New treatments 问号变成 hospital，两个病人，路中线变红通到尽头。
// 时间全读 keys_6-09.json（事件表 映射/events/6-09.json，用 ev_make.py 简写生成）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_6-09.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
// 透视路：左边线、右边线、中线，近端 y=1000，远端 y=330
const L0 = [300, 1000], L1 = [1545, 330], R0 = [820, 1000], R1 = [1575, 330], C0 = [560, 1000], C1 = [1560, 330];
const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
const DASH = [0, 0.2, 0.36, 0.49, 0.6, 0.69, 0.765, 0.83, 0.88, 0.92, 0.95, 0.975];
const END = {x: 1560, y: 288, r: 64};

// 四个路边框：中心、宽高、标签、缩放（越远越小）
const BOX = [
  {cx: 1270, cy: 820, w: 240, h: 170, s: 1, txt: "fewer failed molecules", lab: 30},
  {cx: 620, cy: 600, w: 210, h: 150, s: 0.88, txt: "lower costs", lab: 30},
  {cx: 1580, cy: 560, w: 180, h: 130, s: 0.76, txt: "fewer animal tests", lab: 28},
  {cx: 1060, cy: 400, w: 160, h: 115, s: 0.66, txt: "less chemical waste", lab: 26},
];

const DBox = ({b, p}) => (
  <rect x={b.cx - b.w / 2} y={b.cy - b.h / 2} width={b.w} height={b.h} rx={12} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="10 8"
        opacity={0.8} style={{clipPath: `inset(0 ${100 - 100 * p}% 0 0)`}} />
);
const Down = ({x, y, h, p}) => p <= 0 ? null : (
  <g stroke={RED} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" fill="none">
    <path d={`M${x},${y} L${x},${y + h * p}`} />
    {p > 0.7 && <path d={`M${x - 11},${y + h - 13} L${x},${y + h} L${x + 11},${y + h - 13}`} opacity={span(p, 0.7, 1)} />}
  </g>
);
const Mouse = ({x, y, s, op}) => (
  <g transform={`translate(${x} ${y}) scale(${s})`} opacity={op} stroke={INK} strokeWidth={2.5} strokeLinejoin="round">
    <path d="M-24,4 C-40,4 -46,-6 -40,-14" fill="none" strokeLinecap="round" />
    <ellipse cx={0} cy={0} rx={24} ry={14} fill="#E2DED4" />
    <circle cx={22} cy={-6} r={10} fill="#E2DED4" />
    <circle cx={18} cy={-16} r={6} fill="#E2DED4" />
    <circle cx={27} cy={-7} r={1.8} fill={INK} stroke="none" />
  </g>
);
const Barrel = ({x, y, s, op}) => (
  <g transform={`translate(${x} ${y}) scale(${s})`} opacity={op} stroke={INK} strokeWidth={2.5}>
    <rect x={-16} y={-22} width={32} height={44} rx={6} fill="#B9B4A8" />
    <path d="M-16,-8 L16,-8 M-16,8 L16,8" fill="none" />
    <ellipse cx={0} cy={-22} rx={16} ry={4} fill="#CFCAC0" />
  </g>
);
const X = ({x, y, sz, p}) => p <= 0 ? null : (
  <g stroke={RED} strokeWidth={4.5} strokeLinecap="round">
    <path d={`M${x - sz},${y - sz} L${x - sz + 2 * sz * span(p, 0, 0.5)},${y - sz + 2 * sz * span(p, 0, 0.5)}`} />
    {p > 0.5 && <path d={`M${x + sz},${y - sz} L${x + sz - 2 * sz * span(p, 0.5, 1)},${y - sz + 2 * sz * span(p, 0.5, 1)}`} />}
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const road = span(f, E.road.s, E.road.e, ease);
  const pat = span(f, E.pat.s, E.pat.e, ease);
  const io = Easing.inOut(Easing.cubic);
  // 每个框：画框、东西出现、三变一
  const bx = [span(f, E.m_box.s, E.m_box.l + 8, ease), span(f, E.c_box.s, E.c_box.l + 8, ease), span(f, E.a_box.s, E.a_box.l + 8, ease), span(f, E.w_box.s, E.w_box.l + 8, ease)];
  const dn = [span(f, E.m_d.s, E.m_d.e, io), span(f, E.c_d.s, E.c_d.e, io), span(f, E.a_d.s, E.a_d.e, io), span(f, E.w_d.s, E.w_d.e, io)];
  const ax = span(f, E.a_x.s, E.a_x.l + 6, out), wx = span(f, E.w_x.s, E.w_x.l + 6, out);
  const plug = span(f, E.plug.s, E.plug.l + 10, ease);
  const zap = f >= E.too.s ? Math.exp(-Math.max(0, f - E.too.l) / 10) * span(f, E.too.s, E.too.l) : 0;
  const ring = span(f, E.prize.s, E.prize.l, ease);
  const q = span(f, E.prize.s + 8, E.prize.l + 10) * (1 - span(f, E.hosp.s, E.hosp.l));
  const bead = [[0, 150, 600], [E.road.l, 230, 960], [E.m_box.l, 1520, 960], [E.m_x.l, 1500, 720], [E.m_d.l, 1600, 860],
                [E.c_box.l, 450, 520], [E.c_d.l, 620, 470], [E.a_box.l, 1760, 470], [E.a_x.l, 1580, 455], [E.a_d.l, 1760, 700],
                [E.w_box.l, 890, 340], [E.w_x.l, 1060, 305], [E.w_d.l, 1220, 290], [E.srv.l, 200, 520], [E.cost2.l, 790, 245],
                [E.plug.l, 660, 450], [E.too.l, 640, 300], [E.prize.l, 1720, 200], [E.hosp.l, 1730, 330], [E.treat.l, 1700, 420],
                [E.pat.l, 1780, 390], [K.len_f, 1781, 391]];
  const keyOp = (i) => (i === 1 ? 1 : 1 - span(dn[0], 0, 0.8));
  const keyDy = (i) => (i === 1 ? 0 : 34 * dn[0]);
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("6-09.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.road.s, E.road.e + 20)}>Further down the road</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 路面 */}
        <path d={`M${L0[0]},${L0[1]} L${L1[0]},${L1[1]} L${R1[0]},${R1[1]} L${R0[0]},${R0[1]} Z`} fill="rgba(31,30,28,0.06)" opacity={span(road, 0.4, 1)} />
        {[[L0, L1], [R0, R1]].map(([a, b], i) => (
          <path key={i} d={`M${a[0]},${a[1]} L${b[0]},${b[1]}`} stroke={INK} strokeWidth={5} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - road} />
        ))}
        {DASH.slice(0, -1).map((u, i) => {
          const v = u + 0.5 * (DASH[i + 1] - u), a = lerp(C0, C1, u), b = lerp(C0, C1, v);
          return <path key={i} d={`M${a[0]},${a[1]} L${b[0]},${b[1]}`} stroke={INK} strokeWidth={5 * (1 - 0.75 * u)} strokeLinecap="round" opacity={span(road, u * 0.8, u * 0.8 + 0.2)} />;
        })}
        {/* 结尾：中线变红，从近到远 */}
        {pat > 0 && (() => { const b = lerp(C0, C1, pat); return <path d={`M${C0[0]},${C0[1]} L${b[0]},${b[1]}`} stroke={RED} strokeWidth={6} strokeLinecap="round" opacity={0.85} />; })()}

        {BOX.map((b, i) => <DBox key={i} b={b} p={bx[i]} />)}
        {/* 框 1：钥匙打叉 */}
        {[0, 1, 2].map((i) => <X key={i} x={1352} y={770 + 50 * i + keyDy(i)} sz={11} p={span(f, E.m_x.s + 3 * i, E.m_x.l + 3 * i) * keyOp(i)} />)}
        <Down x={1420} y={765} h={110} p={dn[0]} />
        {/* 框 2：钞票 */}
        <Down x={746} y={548} h={100} p={dn[1]} />
        {/* 框 3：小鼠 */}
        {[0, 1, 2].map((i) => <Mouse key={i} x={1530 + 50 * i} y={565 + (i === 1 ? 0 : 26 * dn[2])} s={1.1 * span(ax, i * 0.25, i * 0.25 + 0.5, out)} op={i === 1 ? 1 : 1 - span(dn[2], 0, 0.8)} />)}
        <Down x={1690} y={515} h={88} p={dn[2]} />
        {/* 框 4：废料桶 */}
        {[0, 1, 2].map((i) => <Barrel key={i} x={1018 + 42 * i} y={400 + (i === 1 ? 0 : 22 * dn[3])} s={1.2 * span(wx, i * 0.25, i * 0.25 + 0.5, out)} op={i === 1 ? 1 : 1 - span(dn[3], 0, 0.8)} />)}
        <Down x={1158} y={360} h={78} p={dn[3]} />

        {/* 电：插头、电线一跳一跳、闪电 */}
        {plug > 0 && (
          <g stroke={SOFT} fill="none" strokeLinecap="round" strokeLinejoin="round">
            <path d="M488,402 C400,402 330,470 236,440" strokeWidth={4} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - plug} />
            {f > E.plug.l && <path d="M488,402 C400,402 330,470 236,440" strokeWidth={7} strokeDasharray="6 26" strokeDashoffset={(f - E.plug.l) * 1.6} opacity={0.75} />}
            <g opacity={span(plug, 0.4, 1)}>
              <rect x={488} y={380} width={46} height={44} rx={8} fill={PAPER} strokeWidth={3.5} />
              <path d="M534,392 L554,392 M534,412 L554,412" strokeWidth={4} />
            </g>
          </g>
        )}
        {f >= E.plug.l && (
          <path d="M585,318 L566,352 L582,352 L564,388" fill="none" stroke={zap > 0.05 ? RED : SOFT} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round"
                transform={`translate(574 352) scale(${1 + 0.45 * zap}) translate(-574 -352)`} opacity={span(f, E.plug.l, E.plug.l + 10)} />
        )}

        {/* 路尽头：红圈，先虚线后实线 */}
        {ring > 0 && <circle cx={END.x} cy={END.y} r={END.r} fill="none" stroke={RED} strokeWidth={4} strokeDasharray={pat > 0.5 ? undefined : "9 8"}
                             pathLength={pat > 0.5 ? undefined : 1} style={{clipPath: `inset(0 ${100 - 100 * ring}% 0 0)`}} />}
      </svg>

      {/* 框 1 的钥匙（在叉的下面一层，用 div 包住好沉下去） */}
      {[0, 1, 2].map((i) => (
        <div key={i} style={{position: "absolute", left: 0, top: keyDy(i), width: 1920, height: 1080, opacity: keyOp(i)}}>
          <Part name="key" cx={1250} cy={770 + 50 * i} w={128} at={E.m_box.l + 2 + 3 * i} f={f} gate={[0.1, 0.5]} flood={14} />
        </div>
      ))}
      {/* 框 2 的钞票：上面两张滑下去淡出 */}
      {[0, 1, 2].map((i) => (
        <div key={i} style={{position: "absolute", left: 0, top: i === 0 ? 0 : 30 * dn[1], width: 1920, height: 1080, opacity: i === 0 ? 1 : 1 - span(dn[1], 0, 0.8)}}>
          <Part name="banknote" cx={598 + 18 * i} cy={630 - 30 * i} w={112} at={E.c_box.s + 6 + 4 * i} f={f} gate={[0.5, 0.5]} flood={14} />
        </div>
      ))}
      {BOX.map((b, i) => (
        <Label key={i} x={b.cx} y={b.cy + b.h / 2 + 12} w={360} size={b.lab} italic p={span(f, [E.m_d, E.c_d, E.a_d, E.w_d][i].s, [E.m_d, E.c_d, E.a_d, E.w_d][i].e)}>{b.txt}</Label>
      ))}

      {/* 机柜（SOFT：代价） */}
      <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, filter: "grayscale(1)", opacity: 0.7}}>
        <Part name="tower" cx={200} cy={330} w={64} at={E.srv.s + 2} f={f} gate={[0.5, 1]} flood={18} />
      </div>
      <div style={{position: "absolute", left: 262, top: 212, fontSize: 32, color: SOFT, fontStyle: "italic", whiteSpace: "nowrap"}}>
        <Write p={span(f, E.srv.s + 6, E.srv.l + 14)}>Computing </Write><Write p={span(f, E.cost2.s, E.plug.l + 16)}>costs electricity too</Write>
      </div>

      {/* 路尽头：问号 → 医院和病人 */}
      <div style={{position: "absolute", left: END.x - 40, top: END.y - 52, width: 80, textAlign: "center", fontSize: 92, lineHeight: "100px", color: RED, opacity: q,
                   transform: `scale(${1.3 - 0.3 * span(f, E.prize.s + 8, E.prize.l + 6, out)})`}}>?</div>
      <Part name="hospital" cx={END.x} cy={END.y + 4} w={68} at={E.hosp.s + 4} f={f} gate={[0.5, 1]} flood={16} />
      <Part name="person_w" cx={1666} cy={312} w={44} at={E.pat.s} f={f} gate={[0.5, 1]} flood={12} />
      <Part name="person_w" cx={1720} cy={312} w={44} at={E.pat.s + 5} f={f} gate={[0.5, 1]} flood={12} />
      <div style={{position: "absolute", left: 1080, top: 214, width: 400, textAlign: "right", fontSize: 34, lineHeight: "42px", fontStyle: "italic"}}>
        <div><Write p={span(f, E.treat.s - 6, E.treat.e)}>new treatments</Write></div>
        <div style={{color: RED}}><Write p={span(f, E.pat.s, E.pat.e)}>for patients</Write></div>
      </div>

      <Source p={span(f, E.road.l, E.road.l + 20)}>Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual609" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
