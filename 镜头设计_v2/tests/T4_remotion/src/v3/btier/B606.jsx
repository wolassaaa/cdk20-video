// HKBU SCIE1007 课程作业的科普视频：B 档 6-06 "Time. Before: a ten-to-seventeen-year road, with finding a hit just the opening stretch.
// Now: 30 days to the first hit, and a better key within another 30."
// 规则 v2：第 6 章翻牌记分板，第 1、2 行已填（凹位里留着各自的小件）。开头 T5 runner（上一段 6-04+05 出镜）。
// row3：行名 3. TIME；bef：栏头翻出 BEFORE，凹位里的卷尺盒飞到行下面放大；tape：金色尺带从盒里拉出来，一路拉到 10 年，主翻牌 10–17 YEARS；
// road：继续拉到 17 年，刻度一格一格过；hit：尺带最前面 2 年处卡上一个黑色卡子；open：卡子前面那一小段描红；strch：HIT = OPENING STRETCH。
// now：尺带卷回盒里、盒子缩回凹位，机位横移到 NOW 栏，栏头翻出 NOW；30 days：30 块日子小翻牌一块接一块翻出来（6 × 5），主翻牌 30 DAYS (1ST HIT)；
// first hit：001 插头落在第 30 块上，打绿勾；better key：048 插头滑进来；another 30：第一组往左让，再翻出 30 块，048 落在新的第 30 块上，副翻牌 +30 DAYS (BETTER KEY)。
// 不用日历贴图（规则 v2 黑名单）。结尾 T2 往左甩（6-07 填第 4 行）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-06.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Stage, Sprite, Slab, Tag, Tick, Source, evMapB, whipX, impact, T5In} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";
import {Board6, DimUp, cell, Flap, TapeCase} from "./board6.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 6;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const B = cell(2, "B").slot, N = cell(2, "N").slot;
// 第 3 行靠板底，弹出台改在它上面（前两行盖暗纱）：机位 z 1.45 对准 y 460，行在屏幕 656–877，弹出台世界 y 180–525
export const CAM3 = {yB: 460, z: 1.45};
const CASE = {x: 260, y: 400};
const YR = 44, T0 = CASE.x + 70;           // 一年 44 px，尺带从盒右边出来
const TW = 6, TH = 5, TS = 58, TG = 6;     // 日子小翻牌 6 × 5
const GRID = (k) => ({x: 1180, y: 215});   // P56：第二个日历放到第一个的位置
const SHIFT = 290;

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.tw("pop", 0, 1, E.bef.s - 4, E.bef.l + 16, "power3.inOut");
    S.len = 0;
    tl.fromTo(S, {len: 0}, {len: 10, duration: (E.tape.l - E.tape.s) / 60, ease: "power2.out", immediateRender: false}, E.tape.s / 60);
    tl.fromTo(S, {len: 10}, {len: 17, duration: (E.road.l + 30 - E.road.s) / 60, ease: "power1.inOut", immediateRender: false}, E.road.s / 60);
    X.land("clip", 0, 1, E.hit.l, {antic: false, dur: 14});
    X.tw("red", 0, 1, E.open.s, E.open.l, "power2.out");
    X.tw("rewind", 0, 1, E.now.s - 34, E.now.s - 4, "power2.in");
    X.tw("back", 0, 1, E.now.s - 6, E.now.s + 14, "power2.inOut");
    X.tw("pan", 0, 1, E.now.s - 12, E.now.l + 14, "power2.inOut");
    X.tw("shift", 0, 1, E.d30b.s - 20, E.d30b.s + 4, "power2.inOut");
    X.land("p1", 0, 1, E.hit1.l, {antic: false, dur: 18});
    X.tw("t1", 0, 1, E.hit1.l + 4, E.hit1.l + 24, "power2.out");
    X.tw("k48", 0, 1, E.bkey.s, E.bkey.l, "power2.out");
    X.tw("p2", 0, 1, E.bkey.s, E.bkey.l, "power2.inOut");
    X.jiggle("gj", E.d30b.l, 5, 0);
    X.tw("t2", 0, 1, E.d30b.l + 4, E.d30b.l + 24, "power2.out");
  });
  const drift = 0.04 * (f / LEN);
  const transition = cl((f-LEN+36)/28);
  const cam = {x: mix(mix(640,1440,S.pan),640,transition), y: mix(CAM3.yB,620,transition), z: mix(CAM3.z+drift,1.45,transition)};
  const whip = f > LEN - 8 ? whipX(f, LEN - 7, "out", -1) : 0;
  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const pop = S.pop * (1 - S.back);
  const len = S.len * (1 - S.rewind);
  const cs = {x: mix(B.cx, CASE.x, pop), y: mix(B.cy, CASE.y, pop), s: mix(0.72, 1, pop)};
  const tape = len > 0.02 && pop > 0.5;
  // 30 块日子牌：第 k 组，第 j 块落在 at0 + j × 0.66
  const grid = (k, at0) => {
    const g = GRID(k);
    const gx = g.x;
    return [...Array(TW * TH)].map((_, j) => {
      const at = Math.round(at0 + j * 0.66);
      if (f < at - 18) return null;
      return <Flap key={`${k}-${j}`} f={f} x={gx + (j % TW) * (TS + TG)} y={g.y + Math.floor(j / TW) * (TS - 10 + TG) - (S.gj || 0) * (k === 1 ? 1 : 0)} w={TS} h={TS - 10}
                   text={String(j + 1)} at={at} fs={28} seed={k * 40 + j} hot={j === 29 && f >= at ? 1 : 0} />;
    });
  };
  const slot30 = (k) => {
    const g = GRID(k);
    return {x: g.x + 5 * (TS + TG) + TS / 2, y: g.y + 4 * (TS - 10 + TG) + (TS - 10) / 2};
  };
  const s0 = slot30(0), s1 = slot30(1);
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} shakeX={impact(f, E.hit1.l)} over={<T5In name="runner" f={f} />}>
        <Layer id={["board", "tape", "stretch", "cal"]}>
          <Board6 f={f} cam={cam} cols={1} hideB={cl((S.pan - 0.15) / 0.35)} hdr={{B: E.bef.l, N: E.now.l}}
                  rows={[true, true, {name: E.row3.l, B: E.tape.l, Bs: [E.strch.l], N: E.d30a.l, Ns: [E.d30b.l]}, false]}
                  lit={{"2B": cl(f / 12) * (1 - S.pan), "2N": S.pan}}>
            <DimUp i={2} v={Math.max(pop, S.pan, 0.6)} />
            {/* BEFORE：卷尺 */}
            {tape && (
              <div style={{position: "absolute", left: 0, top: 0}}>
                <Tag x={1108} y={400} op={cl(S.len / 10)}>years</Tag>
                <Slab x={T0} y={CASE.y - 27} w={len * YR + 18} h={54} r={8} color={C.gold} depth={6} id="tapeband" sheen={S.len < 17 ? (S.len / 17) : -1} />
                {S.red > 0.01 && <div style={{position: "absolute", left: T0 + 4, top: CASE.y - 24, width: Math.min(len, 2) * YR * S.red, height: 48, borderRadius: 6, background: C.red, opacity: 0.82}} />}
                {[...Array(Math.floor(len) + 1)].map((_, y) => (
                  <React.Fragment key={y}>
                    <div style={{position: "absolute", left: T0 + 9 + y * YR - 1.5, top: CASE.y - 27, width: 3, height: y % 5 === 0 ? 26 : 14, background: C.ink, opacity: 0.85}} />
                    {(y % 5 === 0 || y === 17) && <div data-role="engrave" style={{position: "absolute", left: T0 + 9 + y * YR - 20, top: CASE.y - 2, width: 40, textAlign: "center",
                                                                       fontFamily: "'InstrumentSerifB', serif", fontSize: 26, color: y < 2 && S.red > 0.5 ? C.inkLight : C.ink, lineHeight: 1}}>{y}</div>}
                  </React.Fragment>
                ))}
                {S.clip > 0.01 && (
                  <Slab x={T0 + 9 + 2 * YR - 9} y={CASE.y - 40 - 24 * (1 - Math.min(1, S.clip))} w={18} h={80} r={5} color={C.black} depth={5} op={cl(S.clip * 2)} id="tclip" />
                )}
              </div>
            )}
            {(pop > 0.02 || S.back < 1) && <TapeCase x={cs.x} y={cs.y + id(1).y} s={cs.s} spin={len * 40} />}
            {/* NOW：日子小翻牌 + 001 / 048 */}
            <div style={{position: "absolute", left: 0, top: 0, opacity: 1 - S.shift}}>
              {S.pan > 0.3 && grid(0, E.d30a.l - 19)}
              {S.p1 > 0.01 && <Tag x={s0.x + 124 + 72} y={s0.y - 89 * (1 - Math.min(1, S.p1)) - 20} align="left" op={cl(S.p1 * 2)} on="plug1">001</Tag>}
            </div>
            {f >= E.d30b.s - 6 && grid(1, E.d30b.l - 19)}
            {S.p1 > 0.01 && <Sprite name="plug/001_34" x={s0.x + 124} y={s0.y - 89 * (1 - Math.min(1, S.p1)) + id(2).y} w={104} op={cl(S.p1 * 2) * (1 - S.shift)} rot={-8} />}
            <div style={{position: "absolute", left: 0, top: 0, opacity: 1 - S.shift}}><Tick x={s0.x + 86} y={s0.y - 66} s={44} p={S.t1} sw={9} /></div>
            <Tick x={s1.x + 86} y={s1.y - 66} s={44} p={S.t2} sw={9} />
            {S.k48 > 0.01 && (
              <Sprite name="plug/048_34" x={mix(mix(1900, 1700, S.k48), s1.x + 135, S.p2)} y={mix(470, s1.y-52, S.p2) - 70 * Math.sin(Math.PI * S.p2) + id(3).y}
                      w={mix(150, 104, S.p2)} op={cl(S.k48 * 2)} rot={-8} rim={0.8} />
            )}
            {S.k48 > 0.3 && <Tag x={mix(mix(1900, 1700, S.k48), s1.x + 135, S.p2) + 72} y={mix(470, s1.y-52, S.p2) - 70 * Math.sin(Math.PI * S.p2) - 20} align="left" op={cl(S.k48 * 2 - 0.6)} on="plug">048</Tag>}
          </Board6>
        </Layer>
        <Layer id="txt" exempt>
          <Source>{f < E.now.s ? "Illustration · 10–17 years: Wang et al., Pharmaceuticals 2023 (review)" : "Illustration · data: Ren et al., Chem. Sci. 2023"}</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B606" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
