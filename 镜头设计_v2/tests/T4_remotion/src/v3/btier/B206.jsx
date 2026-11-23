// HKBU SCIE1007 课程作业的科普视频：B 档 2-06（C 画外音）"So how did we check all this? We read. A lot. No lab work of our own: this is a literature review…"
// how did we check：红问号；We read：一本书落下；A lot：右边书一本本摞起来；No lab work of our own：烧瓶落下、变灰、画叉；literature review：标签。
// At the centre：清场，中心一块底座；one original study：主论文落到中心；Ren … 2023：名牌；supplementary data：数据架落在下面，浇口连上；
// Around it：六根料杆从中心往外长（左三右三，像板件的料杆框）；每说到一种来源，一张来源卡挂到一根料杆头上；
// a 2026 expert Perspective, which we read only as an abstract：最后那张卡大半变磨砂，只有顶上一条清楚，手写 abstract only。
// 接点：开头 T2 从右甩进（2-05 是 B 页），结尾 T2 往左甩（2-07 是 B 页）。L0 第 2 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_2-06.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, SERIF, Tag, camBreath, Stage, Sprite, Slab, Runner, Plate, Label, Pen, Source, evMapB, whipX} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";
import {REFS, RefCard} from "./refcards.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 2;

const BOOK0 = {x: 700, y: 430, w: 520};
const STACK = [...Array(8)].map((_, i) => ({x: 1130 + ((i * 37) % 50) - 25, y: 690 - i * 52, w: 330 - (i % 3) * 20, c: [C.bone, C.blue, C.grey][i % 3], r: ((i * 53) % 10) - 5}));
const FLASK = {x: 1620, y: 470, w: 220};
const HUB = {x: 960, y: 410};
// 审查批 1（11-23）：主论文放大 ×2.1 当英雄件（book/34x2，430 → 903 宽，屏上约 495 px 高），居中；名牌抬到 40 px 放在书下；
// 数据架挪到右下（书下面放不下），supplementary data 牌在它左边、右对齐、离架 20 px；original study 放在书下，数据架落下前收。
const MAIN = {x: 960, y: 380, w: 903};
const RACK = {x: 1180, y: 785, w: 200};
const RACK_H = Math.round(200 * 571 / 928);
const QM = {x: 960, y: 500, size: 316};               // 问号：托盘正中，字高 240 px（Instrument Serif "?" 墨迹 0.76 em）
const CW = 440, CH = 112;   // P02：卡 440×112，两列 x=100 / 1380
const CARDS = [
  {x: 100, y: 160, ev: "hk"},
  {x: 1380, y: 160, ev: "tools", k: 0},
  {x: 100, y: 420, ev: "tools", k: 1},
  {x: 1380, y: 420, ev: "rev"},
  {x: 100, y: 680, ev: "text"},
  {x: 1380, y: 680, ev: "persp"},
];
const armD = (c) => {
  const ex = c.x < HUB.x ? c.x + CW : c.x, ey = c.y + CH / 2, sx = HUB.x + (c.x < HUB.x ? -230 : 230);
  return `M${sx},${HUB.y} C${(sx + ex) / 2},${HUB.y} ${(sx + ex) / 2},${ey} ${ex + (c.x < HUB.x ? 10 : -10)},${ey}`;
};

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("book", 0, 1, E.read.l, {antic: false});
    X.group(STACK.map((_, i) => `s${i}`), 0, 1, E.lot.l, {antic: false, step: 4});
    X.land("flask", 0, 1, E.lab.l, {antic: false});
    X.tw("no", 0, 1, E.nolab.s, E.nolab.l + 16, "power2.out");
    X.tw("clear", 0, 1, E.centre.s - 6, E.centre.l + 20, "power2.in");
    X.land("hub", 0, 1, E.centre.l + 8, {antic: false});
    X.land("main", 0, 1, E.study.l, {antic: false});
    X.land("rack", 0, 1, E.supp.l, {antic: false});
    X.tw("arms", 0, 1, E.around.s, E.around.e + 10, "power2.out");
    X.tw("slot01", 0, 1, E.papers.s, E.papers.l + 12, "power2.out");
    CARDS.forEach((c, i) => X.land(`c${i}`, 0, 1, E[c.ev].l + (c.k || 0) * 10, {antic: false}));
    X.tw("frost", 0, 1, E.abs.s, E.abs.l + 30, "power2.inOut");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const whip = f < 7 ? whipX(f, 0, "in", -1) : whipX(f, LEN - 7, "out", -1);
  const cx = -2000 * S.clear;
  // 中心主论文一直轻轻发亮：它是中心
  const mainRim = f > E.ren.l ? 0.25 + 0.2 * Math.sin((2 * Math.PI * (f - E.ren.l)) / 90) : 0;
  // 主论文：放大 ×2.1 演到 Around it，六根料杆长出来时缩到 780 宽给两边的来源卡让位（不和卡片边相压）
  const shrink = clamp01((f - E.around.s) / 48), bookW = MAIN.w + (700 - MAIN.w) * shrink * shrink * (3 - 2 * shrink);

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} cam={camBreath(f, K, ["s1", "s4"])}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${cx}px)`}}>
          <Layer id="books">
            {S.book > 0.01 && <Sprite name="book/34" x={BOOK0.x} y={BOOK0.y - 40 * (1 - Math.min(1, S.book)) + id(1).y} w={BOOK0.w} op={Math.min(1, S.book * 1.5)} rot={id(1).r} />}
            {STACK.map((b, i) => S[`s${i}`] > 0.01 && (
              <Slab key={i} x={b.x - b.w / 2} y={b.y - 80 * (1 - Math.min(1, S[`s${i}`]))} w={b.w} h={42} r={8} color={C.bone} depth={12} rot={b.r+(i-3.5)*5*(1-S.no)} op={Math.min(1, S[`s${i}`] * 2)} id={`bk${i}`} />
            ))}
          </Layer>
          <Layer id="flask">
            {S.flask > 0.01 && <Sprite name="flask/34" x={FLASK.x+222*S.no} y={FLASK.y - 40 * (1 - Math.min(1, S.flask)) + id(2).y} w={FLASK.w} op={Math.min(1, S.flask * 1.5) * (1 - S.no)}
                                     style={{filter: S.no > 0.01 ? `grayscale(${S.no})` : undefined}} />}
          </Layer>
        </div>

        <Layer id="frame">
          {CARDS.map((c, i) => {
            // 左边两根（AI 工具论文）在说到 papers 时才长出来，其余四根在 Around it 时长
            const a = i === 1 || i === 2 ? clamp01(S.slot01 * 1.2 - 0.1 * (i - 1)) : clamp01(S.arms * 1.3 - 0.05 * i);
            return a > 0.001 && <Runner key={i} d={armD(c)} draw={a} width={16} />;
          })}
          {S.hub > 0.01 && <Slab x={HUB.x - 240} y={HUB.y - 170 + 30 * (1 - Math.min(1, S.hub))} w={480} h={380} r={30} color={C.bone} depth={14} op={Math.min(1, S.hub * 1.5) * 0.9} id="hub" />}
          {S.rack > 0.01 && (
            <>
              <Runner d={`M${HUB.x + 200},${HUB.y + 150} Q${RACK.x},${HUB.y + 150} ${RACK.x},${RACK.y - RACK_H / 2 - 6}`} draw={Math.min(1, S.rack)} width={12} />
              <Sprite name="dbrack/34" x={RACK.x} y={RACK.y - 30 * (1 - Math.min(1, S.rack)) + id(4).y} w={RACK.w} op={Math.min(1, S.rack * 1.5)} />
            </>
          )}
        </Layer>
        <Layer id="main">
          {S.main>.01&&<Slab x={MAIN.x-bookW/2} y={MAIN.y-182-50*(1-Math.min(1,S.main))} w={bookW} h={486*Math.min(1,bookW/903)} r={18} depth={14} op={Math.min(1,S.main*1.5)} sheen={mainRim>0?mainRim:-1} id="primaryPaper">
            <div data-role="engrave" data-on="primaryPaper" style={{position:"absolute",left:"7%",top:"9%",fontFamily:SERIF,fontSize:Math.max(32,48*bookW/903),whiteSpace:"nowrap",color:C.ink}}>Ren et al. · Chem. Sci., 2023</div>
            {Array.from({length:24},(_,i)=><div key={i} style={{position:"absolute",left:(7+i%2*49)+"%",top:(28+Math.floor(i/2)*5)+"%",width:(i%6===4?31:36)+"%",height:8,borderRadius:4,background:C.grey,opacity:.54}}/>)}
          </Slab>}
        </Layer>
        <Layer id="cards">
          {CARDS.slice(0, 5).map((c, i) => S[`c${i}`] > 0.01 && (
            <RefCard key={i} x={c.x} y={c.y - 30 * (1 - Math.min(1, S[`c${i}`])) + id(10 + i).y} w={CW} h={CH} ref2={REFS[i]} op={Math.min(1, S[`c${i}`] * 1.5)} id={`cd${i}`} />
          ))}
        </Layer>
        <Layer id="card6">
          {S.c5 > 0.01 && <RefCard x={CARDS[5].x} y={CARDS[5].y - 30 * (1 - Math.min(1, S.c5)) + id(15).y} w={CW} h={CH} ref2={REFS[5]} op={Math.min(1, S.c5 * 1.5)} id="cd5" />}
        </Layer>

        <Layer id="txt" exempt>
          {(() => {
            // 红问号落到托盘正中：13 帧落下，落定后往下过冲 8%（字高的 8% ≈ 19 px）再回位；书落下前收掉
            const L = E.q.l, out = E.read.s - 14;
            if (f < L - 13 || f > out + 12) return null;
            const p = Math.min(1, (f - (L - 13)) / 13);
            const dy = f < L ? -220 * (1 - p * p) : f < L + 12 ? 0.08 * 240 * Math.sin((Math.PI * (f - L)) / 12) : 0;
            const op = Math.min(1, p * 3) * (f > out ? 1 - (f - out) / 12 : 1);
            return <div data-role="label" data-rid="?" style={{position: "absolute", left: QM.x - 0.16 * QM.size, top: QM.y - 0.62 * QM.size + dy, opacity: op,
                                                           fontFamily: SERIF, fontSize: QM.size, lineHeight: 1, color: C.red, whiteSpace: "nowrap"}}>?</div>;
          })()}
          <Label text="literature review" size={60} x={900 + cx} y={760} at={E.review.l} out={E.centre.s} align="center" />
          <Label text="original study" size={52} x={MAIN.x} y={712} at={E.study.l + 8} out={E.supp.s - 12} align="center" />
          {S.rack > 0.5 && <Tag x={RACK.x - RACK.w / 2 - 20} y={RACK.y - 28} align="right" op={Math.min(1, (S.rack - 0.5) * 2)}>supplementary data</Tag>}
          <Pen text="abstract only" x={1420} y={812} at={E.abs.l} size={56} rot={-3} />
          <Source>Illustration · the sources this review is built on</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B206" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
