// HKBU SCIE1007 课程作业的科普视频：B 档 6-07 "Improving the key. Before: every change meant another costly lab round.
// Now: a predicted picture of the first key guided sixteen designs, and the grip got about fifteen times tighter."
// 规则 v2：第 6 章翻牌记分板，第 1–3 行已填（凹位里留着各自的小件）。第 4 行在板底，弹出台改在它上面（前三行盖暗纱，DimUp）。
// 开头：接 6-06 的 T2 甩出，机位从第 3 行 NOW 斜移到第 4 行 BEFORE；row4：行名 4. IMPROVING THE KEY。
// bef：栏头翻出 BEFORE，凹位里的"想—做—测—改"实验循环环升起放大，001 插头顺着环跑；chg / cost / rnd：每跑完一圈（一轮实验）
// 硬币堆飞出一枚金币进环心（花钱），右边圈数计数器 +1；rnd：主翻牌 ANOTHER COSTLY LAB ROUND。
// now：环缩回凹位，机位横移到 NOW 栏，栏头翻出 NOW；pic：凹位里的小插座（插着 001，预测出来的结合图）升起放大，名牌 predicted picture；
// first key：001 那一圈描亮、轻抖；sixteen：16 个设计（插头）从图上一个个弹出来排成两排，计数器停在 16（开口念 sixteen 时）；des：16 GUIDED DESIGNS；
// grip：最后一个设计换成 048，飞进第二个小插座卡紧；fifteen：两根握力尺，001 一格，048 长到 15 格，停在念 fifteen 的帧；~15× TIGHTER GRIP；
// tight：卡紧一抖。说完件缩回凹位，镜头拉回整块板（6-08 从整块板开始）。
// 不用人、日历、钞票（规则 v2 黑名单）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-07.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, shade, Stage, Sprite, Slab, Tag, Counter, Engrave, Source, evMapB, whipX, impact} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";
import {Board6, FOCUS, DimUp, cell, SlotDeco} from "./board6.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 6;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const wf = (k) => K.words.find((w) => w.key === k);
const B = cell(3, "B").slot, N = cell(3, "N").slot;
// 机位：第 4 行在画面下部（屏幕 y 660–880），上面 290–680 是弹出台
const CB = {x: 640, y: 620, z: 1.45}, CN = {x: 1440, y: 620, z: 1.45}, WIDE = {x: 960, y: 540, z: 1};
// BEFORE 版面
const LOOP = {x: 540, y: 470, w: 540};
const RING = 123;                                   // 环上跑道半径
const COINS = {x: 1010, y: 560, w: 170};
const LAPC = {x: 1010, y: 300};
// NOW 版面
const PIC = {x: 950, y: 440, w: 250};
const GRID = (k) => ({x: 1210 + (k % 8) * 60, y: 330 + Math.floor(k / 8) * 72});
const PLUG16 = [...Array(16)].map((_, k) => (k === 15 ? "048" : ["A", "B", "C", "D", "E", "F"][k % 6]));
const CLAMP = {x: 1170, y: 600, w: 130};
const BAR = {x: 1370, y: 590, u: 24};               // 握力尺：一格 24 px
const C16 = {x: 1722, y: 335};

const Scene = () => {
  const f = useCurrentFrame();
  const w16 = wf("sixteen#1"), w15 = wf("fifteen#1");
  const LAPS = [E.chg.l, E.cost.l, E.rnd.l];           // 三圈各自跑完的帧（落在 change / costly / round 开口）
  const S = useGsapTimeline((tl, S, X) => {
    X.tw("move", 0, 1, 0, E.focus4.l + 18, "power2.inOut");
    X.tw("popB", 0, 1, E.bef.s - 4, E.bef.l + 22, "power3.inOut");
    S.lap = 0;
    tl.fromTo(S, {lap: 0}, {lap: 1, duration: (LAPS[0] - E.bef.l - 4) / 60, ease: "power1.inOut", immediateRender: false}, (E.bef.l + 4) / 60);
    tl.fromTo(S, {lap: 1}, {lap: 2, duration: (LAPS[1] - LAPS[0]) / 60, ease: "power1.inOut", immediateRender: false}, LAPS[0] / 60);
    tl.fromTo(S, {lap: 2}, {lap: 3, duration: (LAPS[2] - LAPS[1]) / 60, ease: "power1.inOut", immediateRender: false}, LAPS[1] / 60);
    LAPS.forEach((a, k) => X.tw(`coin${k}`, 0, 1, a - 14, a + 6, "power2.in"));
    X.jiggle("lj", E.rnd.l, 6, 0);
    X.tw("backB", 0, 1, E.now.s - 28, E.now.s + 4, "power2.inOut");
    X.tw("pan", 0, 1, E.now.s - 14, E.now.l + 12, "power2.inOut");
    X.tw("popN", 0, 1, E.pic.s, E.pic.l, "power3.out");
    X.tw("k1", 0, 1, E.k1.s, E.k1.l, "power2.out");
    X.jiggle("kj", E.k1.l, 6, 0);
    X.tw("fan", 0, 1, E.n16.s, w16.f0 + 4, "none");
    S.c16 = 0;
    X.count("c16", 0, 16, w16.f0, w16.f0 - E.n16.s, "power1.out");
    X.tw("cl", 0, 1, E.grip.s - 20, E.grip.l, "power2.out");
    X.tw("fly", 0, 1, E.grip.s - 10, E.grip.l + 2, "power2.inOut");
    X.tw("bars", 0, 1, E.n15.s - 30, E.n15.s, "power2.out");
    S.g = 1;
    tl.fromTo(S, {g: 1}, {g: 15, duration: (w15.f0 - E.n15.s) / 60, ease: "power2.inOut", immediateRender: false}, E.n15.s / 60);
    X.jiggle("tj", E.tight.l, 7, 0);
    X.tw("backN", 0, 1, E.tight.l + 6, E.tight.l + 32, "power2.inOut");
    X.tw("wide", 0, 1, E.tight.l + 14, LEN - 2, "power2.inOut");
  });
  const F0 = {x: 1440, y: 460, z: 1.45};                 // 接 6-06 结尾的机位（第 3 行 NOW，弹出台在行上面）
  const drift = 0.04 * (f / LEN);
  const c1 = {x: mix(mix(F0.x, CB.x, S.move), CN.x, S.pan), y: mix(F0.y, CB.y, S.move), z: mix(F0.z, CB.z, S.move) + drift};
  const cam = {x: mix(c1.x, WIDE.x, S.wide), y: mix(c1.y, WIDE.y, S.wide), z: mix(c1.z, WIDE.z, S.wide)};
  const whip = f < 7 ? whipX(f, 0, "in", -1) : 0;
  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const popB = S.popB * (1 - S.backB), popN = S.popN * (1 - S.backN);
  // BEFORE：环 + 插头沿环跑
  const lp = {x: mix(B.cx, LOOP.x, popB), y: mix(B.cy, LOOP.y, popB), w: mix(140, LOOP.w, popB)};
  const ang = -Math.PI / 2 + S.lap * Math.PI * 2;
  const pl = {x: lp.x + Math.cos(ang) * RING * (lp.w / LOOP.w), y: lp.y + Math.sin(ang) * RING * (lp.w / LOOP.w) * 0.92};
  const laps = Math.floor(S.lap + 0.02);
  const plugName = ["001", "A", "B", "C"][Math.min(3, laps)];
  const spent = LAPS.reduce((m, _, k) => m + ((S[`coin${k}`] || 0) >= 1 ? 1 : 0), 0);
  const coins = LAPS.map((a, k) => {
    const u = S[`coin${k}`] || 0;
    if (u <= 0 || u >= 1 || popB < 0.5) return null;
    const x = mix(COINS.x, LOOP.x, u), y = mix(COINS.y - 120, LOOP.y, u) - 110 * Math.sin(Math.PI * u);
    return <div key={k} style={{position: "absolute", left: x - 30, top: y - 30, width: 60, height: 60, borderRadius: 30, background: `radial-gradient(circle at 35% 30%, ${C.bone}, ${C.gold} 45%, ${shade(C.gold, 0.3)})`,
                                 boxShadow: "0 4px 6px rgba(0,0,0,0.5)", transform: `scale(${(1 - 0.5 * u).toFixed(3)}) rotate(${(u * 300).toFixed(0)}deg)`, opacity: 1 - 0.6 * Math.max(0, u - 0.7) / 0.3}} />;
  });
  // NOW：预测图 + 16 个设计 + 048 卡进第二个小插座 + 握力尺
  const pic = {x: mix(N.cx, PIC.x, popN), y: mix(N.cy, PIC.y, popN), w: mix(118, PIC.w, popN)};
  const fan = PLUG16.map((nm, k) => {
    const u = cl((S.fan * 16 - k) / 1.6);
    if (u <= 0 || popN < 0.3) return null;
    const g = GRID(k);
    let x = mix(PIC.x + 40, g.x, u), y = mix(PIC.y - 20, g.y, u) - 60 * Math.sin(Math.PI * u), w = mix(30, 58, u);
    if (k === 15 && S.fly > 0) { x = mix(g.x, CLAMP.x + 30, S.fly); y = mix(g.y, CLAMP.y + 10, S.fly) - 70 * Math.sin(Math.PI * S.fly); w = mix(58, 0, cl(S.fly * 1.2 - 0.2)); }
    if (w < 2) return null;
    return <Sprite key={k} name={`plug/${nm}_34`} x={x} y={y + (k === 15 ? 0 : id(k + 5).y * 0.5)} w={w} op={popN} shadow={u > 0.9} />;
  });
  const bar = (len, y, name, col) => (
    <div style={{position: "absolute", left: 0, top: 0, opacity: cl(S.bars * 2) * popN}}>
      <div style={{position: "absolute", left: BAR.x - 12, top: y - 2, transform: "translateX(-100%)"}}><Engrave size={30} light>{name}</Engrave></div>
      <div style={{position: "absolute", left: BAR.x + len * BAR.u + 10, top: y - 2}}><Engrave size={30} light>{len < 1.5 ? "1×" : `${Math.round(len)}×`}</Engrave></div>
      <div style={{position: "absolute", left: BAR.x, top: y, width: 15 * BAR.u, height: 26, borderRadius: 6, background: "rgba(255,255,255,0.08)", boxShadow: "inset 0 0 0 1px rgba(255,255,255,0.14)"}} />
      <div style={{position: "absolute", left: BAR.x, top: y, width: len * BAR.u, height: 26, borderRadius: 6, background: col, boxShadow: "0 3px 4px rgba(0,0,0,0.45), inset 0 3px 3px rgba(255,255,255,0.45)"}} />
      {[...Array(16)].map((_, k) => <div key={k} style={{position: "absolute", left: BAR.x + k * BAR.u - 1, top: y + 26, width: 2, height: k % 5 === 0 ? 10 : 5, background: "rgba(255,255,255,0.4)"}} />)}
    </div>
  );
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} shakeX={impact(f, E.tight.l)}>
        <Layer id={["board", "loop4", "now4", "fan16", "ruler15"]}>
          <Board6 f={f} cam={cam} cols={1} hdr={{B: E.bef.l, N: E.now.l}}
                  rows={[true, true, true, {name: E.row4.l, B: E.rnd.l, Bs: [], N: E.des.l, Ns: [w15.f0]}]}
                  lit={{"3B": cl((f - E.focus4.s) / 12) * (1 - S.pan) * (popB > 0.5 ? 0 : 1), "3N": S.pan * (popN > 0.5 ? 0 : 1) * (1 - S.wide)}}>
            <DimUp i={3} v={Math.max(popB, popN, S.move * 0.75) * (1 - S.wide)} />
            {/* BEFORE：想—做—测—改 实验循环 */}
            {popB > 0.01 && (
              <>
                <Sprite name="loop/34" x={lp.x} y={lp.y + id(1).y} w={lp.w} shadow={popB > 0.5} />
                {S.lap > 0.001 && <Sprite name={`plug/${plugName}_34`} x={pl.x} y={pl.y - (S.lj || 0)} w={92 * popB} />}
                <Sprite name="coins/34" x={COINS.x} y={COINS.y + 40 * (1 - popB)} w={COINS.w} sy={1 - 0.16 * spent} op={cl(popB * 2)} />
                {coins}
                <div style={{position: "absolute", left: LAPC.x, top: LAPC.y, opacity: cl(popB * 2)}}>
                  <Slab x={-90} y={-12} w={180} h={110} r={14} color={C.bone} depth={8} id="lapslab" />
                  <Counter value={laps} digits={1} size={80} x={0} y={-4} align="center" />
                </div>
                <Tag x={LAPC.x} y={LAPC.y + 112} op={cl(popB * 3 - 2)} on="lapslab">lab rounds</Tag>
              </>
            )}
            {/* NOW：预测出来的结合图（插着 001 的小插座）→ 16 个设计 → 048 卡紧 → 握力尺 */}
            {popN > 0.01 && (
              <>
                <Sprite name="mini/m34_001" x={pic.x} y={pic.y + id(2).y - (S.kj || 0)} w={pic.w} shadow={popN > 0.5} rim={S.k1 > 0 && f < E.k1.l + 40 ? 0.8 * S.k1 : 0} />
                <Tag x={PIC.x} y={PIC.y + 135} op={cl(popN * 3 - 2)} on="mini">predicted picture</Tag>
                {S.fan > 0.01 && (
                  <div style={{position: "absolute", left: C16.x, top: C16.y, opacity: cl(S.fan * 4) * cl(popN * 2 - 0.6)}}>
                    <Slab x={-70} y={-10} w={140} h={60} r={10} color={C.bone} depth={6} id="c16slab" />
                    <Counter value={S.c16} digits={2} size={46} x={0} y={-2} align="center" />
                  </div>
                )}
                {fan}
                {S.cl > 0.01 && <Sprite name={S.fly >= 1 ? "mini/m34_048clamp" : "mini/m34_on"} x={CLAMP.x} y={CLAMP.y + 30 * (1 - S.cl) - (S.tj || 0)} w={CLAMP.w} op={cl(S.cl * 2) * popN} />}
                {S.bars > 0.01 && bar(1, BAR.y - 44, "key 001", C.gold)}
                {S.bars > 0.01 && bar(S.g, BAR.y, "key 048", C.blueHi)}
              </>
            )}
            {S.backN > 0.01 && <SlotDeco i={3} side="N" op={S.backN} />}
          </Board6>
        </Layer>
        <Layer id="txt" exempt>
          <Source>{f < E.now.s ? "Illustration · the design–make–test–change cycle" : "Illustration · numbers from Ren et al., Chem. Sci. 2023"}</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B607" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
