// HKBU SCIE1007 课程作业的科普视频：B 档 2-07（D 画外音）"For every source, we asked: what kind is it, how much did we read, and how strong is the evidence? …"
// For every source：左边七张来源卡落下；we asked：放大镜落到第一张卡上，右边核对表底板滑进来；
// what kind / how much / how strong / Who did the work / controls and repeats：核对表五行逐条刻出，放大镜跟着一张张卡扫过，每行写完打勾；
// One thing worth knowing：清场，主论文落到左边；most authors：一排八个小人；work for Insilico Medicine：底板滑进来，六个小人跳上去；
// which built its AI tools：两块芯片落到底板上；They say so openly：论文下挂 declared 名牌，打勾；Useful evidence：标签；not an independent check：手写。
// 接点：开头 T2 从右甩进（2-06 是 B 页），结尾 T2 往左甩（2-08 是 B 页）。L0 第 2 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_2-07.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, SERIF, Tag, camBreath, Stage, Sprite, Slab, Plate, Label, Pen, Source, Tick, LoupeRing, Person1, evMapB, whipX} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 2;

const CARDS = ["Ren 2023", "Feng 2011", "AI tool", "AI tool", "Review", "Textbook", "Perspective"];
const CXY = (i) => [110 + (i % 2) * 300, 170 + Math.floor(i / 2) * 140];
const CW = 270, CH = 92;
const LIST = {x: 790, y: 150, w: 1010, rowH: 112};
const ROWS = [["What kind is it?", "kind"], ["How much did we read?", "much"], ["How strong is the evidence?", "strong"], ["Who did the work?", "who"], ["Controls and repeats?", "ctrl"]];
const BOOK = {x: 420, y: 430, w: 480};
const AUTH = (i) => ({x: 820 + i * 130, y: 290});
const BASE = {x: 860, y: 640, w: 920, h: 64};
const ON = (i) => ({x: 920 + i * 92, y: 560});
const CHIPS = [{n: "chemistry42", x: 1560}, {n: "pandaomics", x: 1700}];
const STAY = [6, 7];                                       // 示意：八个里两个不在底板上

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.group(CARDS.map((_, i) => `c${i}`), 0, 1, E.src.l, {antic: false, step: 4});
    X.tw("lp", 0, 1, E.asked.s, E.asked.l + 10, "power2.out");
    X.land("list", 0, 1, E.asked.l + 6, {antic: false});
    ROWS.forEach(([, ev], i) => {
      X.tw(`r${i}`, 0, 1, E[ev].s, E[ev].l + 26, "power2.out");
      X.tw(`k${i}`, 0, 1, E[ev].e - 10, E[ev].e + 10, "power2.out");
    });
    X.tw("scan", 0, 6, E.kind.s, E.ctrl.e, "none");
    X.tw("clear", 0, 1, E.worth.s - 6, E.worth.l + 20, "power2.in");
    X.land("book", 0, 1, E.worth.l + 10, {antic: false});
    X.group([...Array(8)].map((_, i) => `a${i}`), 0, 1, E.authors.l, {antic: false, step: 5});
    X.land("base", 0, 1, E.ins.l, {antic: false});
    [...Array(8)].forEach((_, i) => !STAY.includes(i) && X.tw(`j${i}`, 0, 1, E.ins.l + 6 + i * 5, E.ins.l + 30 + i * 5, "power2.inOut"));
    X.group(CHIPS.map((_, i) => `ch${i}`), 0, 1, E.built.l, {antic: false, step: 10});
    X.land("decl", 0, 1, E.open.l, {antic: false});
    X.tw("tick", 0, 1, E.open.l + 6, E.open.l + 26, "power2.out");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const whip = f < 7 ? whipX(f, 0, "in", -1) : whipX(f, LEN - 7, "out", -1);
  const cx = -2000 * S.clear;

  // 放大镜：asked 时落到第一张卡；之后跟着 scan 一张张卡扫过（0 → 6）
  const sc = S.scan;
  const i0 = Math.min(6, Math.floor(sc)), i1 = Math.min(6, i0 + 1), u = sc - Math.floor(sc);
  const ue = u * u * (3 - 2 * u);
  const p0 = CXY(i0), p1 = CXY(i1);
  const lpPos = [mix(p0[0], p1[0], ue) + CW / 2, mix(p0[1], p1[1], ue) + CH / 2];
  const lp = [mix(lpPos[0] + 300, lpPos[0], S.lp), mix(lpPos[1] - 200, lpPos[1], S.lp)];
  const hot = (i) => (S.lp > 0.5 ? Math.max(0, 1 - Math.abs(sc - i) * 1.6) : 0);

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} cam={camBreath(f, K, ["s5"])}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${cx}px)`}}>
          <Layer id="cards">
            {CARDS.map((t, i) => {
              const a = S[`c${i}`];
              if (a <= 0.01) return null;
              const [x, y] = CXY(i);
              return <Plate key={i} x={x} y={y - 30 * (1 - Math.min(1, a)) + id(1 + i).y} w={CW} h={CH} text={t} size={44} op={Math.min(1, a * 1.5)} id={`c${i}`} lift={10 * hot(i)} sheen={hot(i) > 0.3 ? hot(i) : -1} />;
            })}
            {S.lp > 0.01 && <LoupeRing x={lp[0]} y={lp[1]} r={72} op={Math.min(1, S.lp * 3)} />}
          </Layer>
          <Layer id="list">
            {S.list > 0.01 && (
              <Slab x={LIST.x + 200 * (1 - Math.min(1, S.list))} y={LIST.y - 30} w={LIST.w} h={ROWS.length * LIST.rowH + 40} r={26} color={C.bone} depth={14} op={Math.min(1, S.list * 1.5)} id="list">
                {ROWS.map(([t], i) => {
                  const r = S[`r${i}`];
                  return r > 0.001 && (
                    <div key={i} style={{position: "absolute", left: 40, top: 30 + i * LIST.rowH, width: (LIST.w - 180) * r, height: LIST.rowH - 20, overflow: "hidden", display: "flex", alignItems: "center"}}>
                      <span style={{fontFamily: SERIF, fontSize: 58, color: C.ink, whiteSpace: "nowrap", textShadow: "0 1px 0 rgba(255,255,255,0.65)"}}>{t}</span>
                    </div>
                  );
                })}
              </Slab>
            )}
            {ROWS.map((_, i) => <Tick key={i} x={LIST.x + LIST.w - 80} y={LIST.y + 30 + i * LIST.rowH + 20} s={64} p={S[`k${i}`]} sw={11} />)}
          </Layer>
        </div>

        <Layer id="main">
          {S.book > 0.01 && <Sprite name="book/34" x={BOOK.x} y={BOOK.y - 40 * (1 - Math.min(1, S.book)) + id(10).y} w={BOOK.w} op={Math.min(1, S.book * 1.5)} rot={id(10).r} />}
          {S.decl > 0.01 && <Plate x={BOOK.x - 230} y={BOOK.y + 160 + 20 * (1 - Math.min(1, S.decl))} w={460} h={70} text="conflicts of interest: declared" size={36} op={Math.min(1, S.decl * 1.5)} id="decl" />}
          <Tick x={BOOK.x + 290} y={BOOK.y + 190} s={70} p={S.tick} sw={12} />
        </Layer>
        <Layer id="ins">
          {S.base > 0.01 && <Plate x={BASE.x + 300 * (1 - Math.min(1, S.base))} y={BASE.y} w={BASE.w} h={BASE.h} text="Insilico Medicine" size={46} op={Math.min(1, S.base * 1.5)} id="base" />}
          {CHIPS.map((c, i) => S[`ch${i}`] > 0.01 && <Sprite key={i} name={`chip_${c.n}/34`} x={c.x} y={575 - 40 * (1 - Math.min(1, S[`ch${i}`])) + id(20 + i).y} w={190} op={Math.min(1, S[`ch${i}`] * 1.5)} />)}
          {[...Array(8)].map((_, i) => {
            const a = S[`a${i}`];
            if (a <= 0.01) return null;
            const j = S[`j${i}`] || 0, A = AUTH(i), B = ON(i);
            return <Person1 key={i} x={mix(A.x, B.x, j)} y={mix(A.y, B.y, j) - 140 * Math.sin(Math.PI * j) - 40 * (1 - Math.min(1, a)) + id(30 + i).y} w={230} op={Math.min(1, a * 1.5)} />;
          })}
        </Layer>

        <Layer id="txt" exempt>
          <Label text="most authors" size={52} x={1270} y={150} at={E.authors.l + 10} out={E.useful.s} align="center" />
          <Label text="Useful evidence" size={60} x={BOOK.x} y={170} at={E.useful.l} align="center" />
          <Pen text="not an independent check" x={880} y={760} at={E.notind.l} size={64} rot={-3} />
          <Source>Illustration · author affiliations as declared in Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B207" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
