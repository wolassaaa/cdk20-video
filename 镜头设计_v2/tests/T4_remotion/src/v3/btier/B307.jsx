// HKBU SCIE1007 课程作业的科普视频：B 档 3-07（B 画外音）"In 2023, an AI platform called PandaOmics backed that hunch…"
// In 2023：年份牌；PandaOmics：芯片落下；backed that hunch：右边 CDK20 小插座落下打勾，手写 hunch；
// ten liver cancer data sets：芯片挪到右边，左边十个数据架依次落下，数字轮 10，数据沿料杆流进芯片；
// over a thousand tumour samples：蓝点长满，数字轮 1,133；hundreds of healthy ones：灰点长满，数字轮 674；plus research papers：一叠书飞进芯片；
// People checked its top 20 by hand：清场，右边 Top 20 表一行行画出，两个小人，逐行打勾；and CDK20：蓝色那一行亮一下；came out on top：升到第一，别的行往下让；
// no approved drug against it yet：胶囊落下、变灰、画斜杠，手写 no approved drug yet。
// 数字 1,133 / 674 取自剧本 Visual 行（论文 target selection 部分）。
// 接点：开头 T5 料杆擦除（3-06 出镜段），结尾 T2 往左甩（3-08 是 B 页）。L0 第 3 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_3-07.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Slab, Runner, Plate, Label, Pen, Source, Counter, Engrave, Tick, Capsule1, Person1, camBreath, Stage, Sprite, pathOf, evMapB, T5In, whipX} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 3;

const YEAR = {x: 90, y: 70, w: 270, h: 110};
const CHIP0 = {x: 900, y: 450, w: 560}, CHIP1 = {x: 1460, y: 360, w: 460}, CHIP2 = {x: 300, y: 330, w: 340};
const MINI = {x: 1500, y: 470, w: 280};
const RACK = (i) => ({x: 170 + (i % 5) * 150, y: 230 + Math.floor(i / 5) * 160});
const RACK_W = 140;
const DOT_T = [...Array(120)].map((_, i) => [150 + (i % 20) * 30, 590 + Math.floor(i / 20) * 26]);
const DOT_H = [...Array(80)].map((_, i) => [150 + (i % 20) * 30, 760 + Math.floor(i / 20) * 26]);
const NT = 113, NH = 67;                                  // 一个点 ≈ 10 个样本
const TAB = {x: 760, y: 120, colW: 500, gap: 40, rowH: 66};
const CDK_FROM = 6;                                       // 示意：CDK20 起先排在第 7 行
const PIL = {x: 420, y: 690, w: 300};
const FEEDS = [...Array(10)].map((_, i) => pathOf([[RACK(i).x + 60, RACK(i).y], [CHIP1.x - 180, CHIP1.y + (i - 4.5) * 8]]));
const PAP = pathOf([[1850, 120], [1600, 140], [CHIP1.x, CHIP1.y - 40]]);

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("year", 0, 1, E.y23.l, {antic: false});
    X.land("chip", 0, 1, E.panda.l, {antic: false});
    X.land("mini", 0, 1, E.hunch.l, {antic: false});
    X.tw("tick0", 0, 1, E.hunch.l + 8, E.hunch.l + 28, "power2.out");
    X.tw("mv", 0, 1, E.ten.s - 6, E.ten.l + 20, "power2.inOut");
    X.group([...Array(10)].map((_, i) => `r${i}`), 0, 1, E.ten.l, {antic: false, step: 4});
    X.count("n10", 0, 10, E.ten.l + 36, 36);
    X.tw("flow", 0, 1, E.ten.l + 30, E.people.s, "none");
    X.tw("dt", 0, 1, E.tum.s, E.tum.l, "power2.out");
    X.count("nt", 0, 1133, E.tum.l, E.tum.l - E.tum.s);
    X.tw("dh", 0, 1, E.hl.s, E.hl.l, "power2.out");
    X.count("nh", 0, 674, E.hl.l, E.hl.l - E.hl.s);
    X.tw("pap", 0, 1, E.papers.s, E.papers.e, "power2.inOut");
    X.tw("clear", 0, 1, E.people.s - 6, E.people.l + 20, "power2.in");
    X.group(["pp0", "pp1"], 0, 1, E.people.l, {antic: false, step: 8});
    X.tw("rows", 0, 1, E.top20.s, E.top20.l + 40, "power2.out");
    X.tw("ticks", 0, 1, E.top20.l + 20, E.cdkl.s, "none");
    X.tw("rise", 0, 1, E.cdk.s, E.cdk.l + 10, "power2.inOut");
    X.land("pill", 0, 1, E.nodrug.l, {antic: false});
    X.tw("slash", 0, 1, E.nodrug.l + 10, E.nodrug.l + 30, "power2.out");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const whip = whipX(f, LEN - 7, "out", -1);
  const cx = -2000 * S.clear;
  // 芯片：中间 → 右边（数据流进来）→ 清场后到左上
  const ch = S.clear > 0 ? {x: mix(CHIP1.x, CHIP2.x, S.clear), y: mix(CHIP1.y, CHIP2.y, S.clear), w: mix(CHIP1.w, CHIP2.w, S.clear)}
                         : {x: mix(CHIP0.x, CHIP1.x, S.mv), y: mix(CHIP0.y, CHIP1.y, S.mv), w: mix(CHIP0.w, CHIP1.w, S.mv)};
  const mi = {x: MINI.x + 400 * S.mv, op: 1 - S.mv};
  // 表格：两列各 10 行；CDK20 那一行从第 7 行升到第 1 行
  const rowPos = (k) => {
    const col = k < 10 ? 0 : 1, r = k % 10;
    return [TAB.x + col * (TAB.colW + TAB.gap), TAB.y + r * TAB.rowH];
  };
  const order = (k) => {           // k = 原排名（0 起）；返回当前位置（可以是小数）
    if (k === CDK_FROM) return mix(CDK_FROM, 0, S.rise);
    if (k < CDK_FROM) return k + S.rise;
    return k;
  };
  const rowsShown = S.rows * 20;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} cam={camBreath(f, K, ["s1"])} over={<T5In name="runner" f={f} />}>
        <Layer id="year">
          {S.year > 0.01 && <Plate x={YEAR.x} y={YEAR.y - 30 * (1 - Math.min(1, S.year))} w={YEAR.w} h={YEAR.h} text="2023" size={90} r={22} depth={12} op={Math.min(1, S.year * 1.5) * (1 - S.clear)} id="year" />}
        </Layer>
        <Layer id="chip">
          {S.chip > 0.01 && <Sprite name="chip_pandaomics/34" x={ch.x} y={ch.y - 40 * (1 - Math.min(1, S.chip)) + id(1).y} w={ch.w} op={Math.min(1, S.chip * 1.5)}
                                   rim={S.flow > 0 && S.flow < 1 && S.clear === 0 ? 0.4 + 0.3 * Math.sin(f / 6) : 0} />}
          {S.mini > 0.01 && mi.op > 0.01 && <Sprite name="mini/m34_on" x={mi.x} y={MINI.y - 40 * (1 - Math.min(1, S.mini)) + id(2).y} w={MINI.w} op={Math.min(1, S.mini * 1.5) * mi.op} />}
          <Tick x={MINI.x + 170 + 400 * S.mv} y={MINI.y - 160} s={80} p={S.tick0 * (1 - S.mv)} sw={12} />
        </Layer>

        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${cx}px)`}}>
          <Layer id="sets">
            {S.flow > 0 && S.flow < 1 && [...Array(10)].map((_, i) => S[`r${i}`] > 0.9 && <Runner key={`f${i}`} d={`M${RACK(i).x + 60},${RACK(i).y} L${CHIP1.x - 180},${CHIP1.y + (i - 4.5) * 8}`} width={6} op={0.75} />)}
            {S.flow > 0 && S.flow < 1 && (
              <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
                {[...Array(10)].map((_, i) => [0, 0.33, 0.66].map((o) => {
                  const u = ((f - E.ten.l) / 70 + o + i * 0.07) % 1;
                  const p = FEEDS[i].at(u);
                  return <circle key={`${i}${o}`} cx={p[0]} cy={p[1]} r={7} fill={C.blueHi} opacity={Math.min(1, u * 6, (1 - u) * 6)} />;
                }))}
              </svg>
            )}
            {[...Array(10)].map((_, i) => S[`r${i}`] > 0.01 && <Sprite key={i} name="dbrack/34" x={RACK(i).x} y={RACK(i).y - 40 * (1 - Math.min(1, S[`r${i}`])) + id(10 + i).y} w={RACK_W} op={Math.min(1, S[`r${i}`] * 1.5)} />)}
          </Layer>
          <Layer id="dots">
            <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
              {DOT_T.slice(0, Math.round(NT * S.dt)).map(([x, y], i) => <circle key={`t${i}`} cx={x} cy={y} r={10} fill={C.blue} />)}
              {DOT_H.slice(0, Math.round(NH * S.dh)).map(([x, y], i) => <circle key={`h${i}`} cx={x} cy={y} r={10} fill={C.grey} />)}
            </svg>
            {S.pap > 0.001 && S.pap < 0.98 && (() => {
              const p = PAP.at(S.pap);
              return <Sprite name="book/34" x={p[0]} y={p[1]} w={mix(320, 120, S.pap)} op={Math.min(1, (1 - S.pap) * 4)} lift={20} rot={-10 * S.pap} />;
            })()}
          </Layer>
        </div>

        <Layer id="table">
          {[...Array(20)].map((_, k) => {
            const a = clamp01(rowsShown - k);
            if (a <= 0.01) return null;
            const pos = order(k);
            const xx = rowPos(k)[0], yy = k < 10 ? TAB.y + pos * TAB.rowH : rowPos(k)[1];
            const isC = k === CDK_FROM;
            const lit = isC && f > E.cdkl.s && f < E.cdk.s + 10 ? 0.5 + 0.5 * Math.sin((f - E.cdkl.s) / 5) : 0;
            const rank = Math.round(pos) + 1;
            return (
              <Slab key={k} x={xx + 30 * (1 - a)} y={yy} w={TAB.colW} h={TAB.rowH - 12} r={12} color={isC ? C.blue : C.bone} depth={7} op={a} lift={isC ? 14 * Math.sin(Math.PI * S.rise) : 0}
                    sheen={lit > 0 ? lit : -1} id={`row${k}`}>
                <div style={{position: "absolute", left: 18, top: 6}}><Engrave size={40} light={isC}>{rank}</Engrave></div>
                {isC ? <div style={{position: "absolute", left: 90, top: 6}}><Engrave size={40} light>CDK20</Engrave></div>
                     : <div style={{position: "absolute", left: 90, top: 22, width: 180 + ((k * 71) % 160), height: 12, borderRadius: 6, background: "rgba(154,150,140,0.55)"}} />}
              </Slab>
            );
          })}
          {[...Array(20)].map((_, k) => {
            const p = clamp01(S.ticks * 20 - k);
            const [x, y] = rowPos(k);
            return p > 0 && <Tick key={`k${k}`} x={x + TAB.colW - 40} y={y + 22} s={36} p={p} sw={7} />;
          })}
        </Layer>
        <Layer id="people">
          {["pp0", "pp1"].map((k, i) => S[k] > 0.01 && <Person1 key={k} x={170 + i * 170} y={560 - 40 * (1 - Math.min(1, S[k])) + id(40 + i).y} w={300} op={Math.min(1, S[k] * 1.5)} />)}
          {S.pill > 0.01 && (
            <>
              <Capsule1 x={PIL.x} y={PIL.y - 30 * (1 - Math.min(1, S.pill)) + id(42).y} w={PIL.w} op={Math.min(1, S.pill * 1.5)} style={{filter: `grayscale(${S.slash})`}} />
              <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
                <path d={`M${PIL.x - 120},${PIL.y + 70} L${PIL.x + 120},${PIL.y - 70}`} stroke={C.ink} strokeWidth={12} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - S.slash} />
              </svg>
            </>
          )}
        </Layer>

        <Layer id="txt" exempt>
          <Pen text="hunch" x={1610} y={250} at={E.hunch.l} out={E.ten.s} size={64} />
          {S.n10 > 0.05 && S.clear < 1 && (
            <div style={{position: "absolute", left: 820 + cx, top: 140, display: "flex", alignItems: "baseline", gap: 16}}>
              <Counter value={S.n10} digits={2} size={96} x={0} y={0} />
              <div style={{position: "relative", left: 120, top: 30}}><Engrave size={52}>data sets</Engrave></div>
            </div>
          )}
          {S.nt > 1 && <div style={{position: "absolute", left: 780 + cx, top: 586}}><Counter value={S.nt} digits={4} comma size={60} x={0} y={0} /></div>}
          {S.nh > 1 && <div style={{position: "absolute", left: 780 + cx, top: 756}}><Counter value={S.nh} digits={3} size={60} x={0} y={0} /></div>}
          <Label text="tumour" size={48} x={1000 + cx} y={596} at={E.tum.l} align="left" />
          <Label text="healthy" size={48} x={1000 + cx} y={766} at={E.hl.l} align="left" />
          <Label text="top 20" size={56} x={TAB.x + TAB.colW + TAB.gap / 2} y={40} at={E.top20.l} align="center" />
          <Pen text="no approved drug yet" x={110} y={780} at={E.nodrug.l + 8} size={60} />
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023 (PandaOmics target selection)</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B307" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
