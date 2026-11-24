// HKBU SCIE1007 课程作业的科普视频：B 档 4-07（A 画外音）"Generative AI takes that loop and moves it inside a computer…"
// 4-06 的圆环接着在原位（T2 甩进）；AI：Chemistry42 芯片落在右边；takes that loop：环被拎起；moves it inside a computer：环缩小飞进芯片；
// The platform here, Chemistry42：芯片挪到左下；dozens of AI models：芯片上方 36 个小环一个个长出来，side by side 一起转；known chemistry：芯片底下滑进底板；
// invent new molecules：金插头从芯片冒出来排成一列；this exact keyhole：右边插座落下；score them：每个插头旁长分数条；
// learn from the scores：分数沿料杆流回小环；go again：小环转快，换一批插头；makers say：名牌；new structures within hours：插头一批批冒出来。
// 接点：开头 T2 从右甩进（4-06 是 B 页），结尾 T5 料杆擦除（4-08 出镜段）。L0 第 4 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_4-07.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Tag, Pen, camBreath, Stage, Sprite, Slab, Runner, Plate, Label, Source, anchorOf, pathOf, evMapB, T5Out, whipX, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, rand} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 4;

const LOOP = {cx: 820, cy: 450, r: 230};            // 和 B406 一样
const ST = [["Imagine", -90], ["Make", 0], ["Test", 90], ["Tweak", 180]];
const CHIP0 = {x: 1290, y: 531, w: 640};
const CHIPC = {x: 960, y: 500, w: 640};            // R2-10：芯片居中（帧 205–468），w 沿用 640（原图 844，不会糊）
const CHIP1 = {x: 566, y: 619, w: 640};
const GRID = [...Array(24)].map((_, i) => ({x: 396 + (i % 6) * 180, y: 312 + Math.floor(i / 6) * 62}));   // R2-09：整体下移 40，给 dozens of AI models 标签让出盘面最上一行
const GR = 24;
const BASE = {x: 900, y: 800, w: 600, h: 54};
const SOCK = {x: 1600, y: 470, w: 420};
const PLUGS = ["A", "B", "C", "D", "E"];
const COL_X = 1060, ROW_Y = (i) => 230 + i * 118;
const SCORE = [0.45, 0.62, 0.9, 0.38, 0.55];
const BAR_X = 1150, BAR_W = 260;
const FEED = pathOf([[BAR_X + BAR_W * 0.5, 160], [1000, 70], [820, 70], [620, 92]]);

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("chip", 0, 1, E.chip.l, {antic: false});
    X.tw("lift", 0, 1, E.takes.s, E.takes.e, "power2.out");
    X.tw("into", 0, 1, E.inside.s, E.inside.e, "power2.inOut");
    X.tw("cent", 0, 1, 120, 205, "power2.inOut");                 // R2-10：芯片居中放大
    X.tw("glow", 0, 1, 370, 400, "none");                          // 帧 370（Chemistry42）描亮一次
    X.tw("plat", 0, 1, 462, 500, "power2.inOut");                 // 468（runs）起芯片挪到左下
    X.tw("scr", 0, 1, 468, 486, "power2.out");                    // 白牌 468 起从芯片位置弹出
    X.group(GRID.map((_, i) => `g${i}`), 0, 1, E.dozens.l, {step: 2, antic: false});
    X.tw("spin", 0, 1, E.side.s, E.side.l + 20, "power2.inOut");
    X.land("base", 0, 1, E.known.l, {antic: false});
    X.group(PLUGS.map((_, i) => `p${i}`), 0, 1, E.invent.l, {step: 8, antic: false});
    X.land("sock", 0, 1, E.key.l, {antic: false});
    PLUGS.forEach((_, i) => X.tw(`s${i}`, 0, SCORE[i], E.score.s + i * 5, E.score.l + 18 + i * 5, "power2.out"));
    X.tw("learn", 0, 1, E.learn.s, E.learn.e, "none");
    X.tw("again", 0, 1, E.again.s, E.again.e, "power2.inOut");
    X.land("maker", 0, 1, E.makers.l, {antic: false});
    X.tw("stream", 0, 1, E.new.s, LEN - 20, "none");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const whip = f < 7 ? whipX(f, 0, "in", -1) : 0;
  const shake = impact(f, E.inside.e);

  // 芯片：先在右边，platform 时挪到左下变大
  const c0 = {x: mix(CHIP0.x, CHIPC.x, S.cent), y: mix(CHIP0.y, CHIPC.y, S.cent), w: mix(CHIP0.w, CHIPC.w, S.cent)};
  const ch = {x: mix(c0.x, CHIP1.x, S.plat), y: mix(c0.y, CHIP1.y, S.plat), w: mix(c0.w, CHIP1.w, S.plat)};
  // 圆环：被拎起（上移 40、略放大），再缩小飞进芯片
  const lc = [mix(LOOP.cx, c0.x, S.into), mix(LOOP.cy - 40 * S.lift, c0.y - 20, S.into)];
  const lr = LOOP.r * (1 + 0.06 * S.lift) * (1 - 0.92 * S.into);
  const ringD = (cx, cy, r) => `M${cx},${cy - r} a${r},${r} 0 1,1 -0.01,0`;
  // 小环转速：side 时起转，go again 时加快
  const turn = (f - E.side.s) * (2.2 + 4 * S.again) * S.spin;
  // 第一批插头：从芯片右上冒出，排成一列；go again 时往右滑出，换新一批
  const out1 = S.again;
  const batch2 = (i) => clamp01((f - E.again.l - i * 6) / 16);

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} shakeX={shake} cam={camBreath(f, K, [])} over={<T5Out name="runner" f={f} len={LEN} />}>
        <Layer id="loop">
          {S.into < 1 && (
            // 4-06 的整个环（环、四块站牌、插头）一起被拎起、缩小、飞进芯片
            <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: 1 - clamp01((S.into - 0.85) * 6.6),
                         transform: `translate(${lc[0] - LOOP.cx}px, ${lc[1] - LOOP.cy}px) scale(${lr / LOOP.r})`, transformOrigin: `${LOOP.cx}px ${LOOP.cy}px`}}>
              <Runner d={ringD(LOOP.cx, LOOP.cy, LOOP.r)} width={26} />
              {ST.map(([t, a], i) => {
                const q = (a * Math.PI) / 180;
                return <Plate key={i} x={LOOP.cx + 132 * Math.cos(q) - 100} y={LOOP.cy + 132 * Math.sin(q) - 33} w={200} h={66} text={t} size={46} id={`st${i}`} shadow={S.into < 0.3} />;
              })}
              <Sprite name="plug/A_34" x={LOOP.cx} y={LOOP.cy - LOOP.r - 46} w={170} lift={10 + 20 * S.lift} shadow={S.into < 0.3} />
            </div>
          )}
        </Layer>

        <Layer id="base">
          {S.base > 0.01 && <Plate x={BASE.x} y={BASE.y + 30 * (1 - Math.min(1, S.base))} w={BASE.w} h={BASE.h} text="known chemistry" size={44} op={Math.min(1, S.base * 1.5)} id="base" />}
        </Layer>

        <Layer id="grid">
          {S.scr>.01 && <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${ch.x}px ${ch.y}px`, transform: `scale(${(0.2 + 0.8 * S.scr).toFixed(3)})`, opacity: Math.min(1, S.scr * 2)}}>
            <Slab x={270} y={262} w={1200} h={278} r={22} depth={14} op={.91} id="model-screen"/></div>}
          <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
            {GRID.map((g, i) => {
              const a = S[`g${i}`];
              if (a <= 0.01) return null;
              const r = GR * Math.min(1.08, a);
              const t = ((turn * (0.8 + 0.4 * rand(i)) + rand(i + 9) * 360) * Math.PI) / 180;
              const lit = S.learn > 0 && S.learn < 1 ? Math.max(0, 1 - Math.abs(S.learn * 1.4 - (i % 9) / 9 - 0.2) * 5) : 0;
              return (
                <g key={i} opacity={Math.min(1, a * 1.5)}>
                  <circle cx={g.x + 2} cy={g.y + 4} r={r} fill="none" stroke="rgba(40,30,20,0.18)" strokeWidth={8} />
                  <circle cx={g.x} cy={g.y} r={r} fill="none" stroke={C.bone} strokeWidth={8} />
                  <circle cx={g.x} cy={g.y} r={r} fill="none" stroke={C.blueHi} strokeWidth={8} opacity={0.8 * lit} />
                  <circle cx={g.x + r * Math.cos(t)} cy={g.y + r * Math.sin(t)} r={6} fill={C.gold} />
                </g>
              );
            })}
          </svg>
        </Layer>

        <Layer id="chip">
          {S.chip > 0.01 && <Sprite name="chip_chemistry42/34" x={ch.x} y={ch.y - 40 * (1 - Math.min(1, S.chip)) + id(1).y} w={ch.w} op={Math.min(1, S.chip * 1.5)}
                                   rim={Math.max(S.into > 0.9 && S.into < 1 ? 1 : f > E.inside.e && f < E.inside.e + 20 ? 1 - (f - E.inside.e) / 20 : 0, Math.sin(Math.PI * S.glow))} />}
        </Layer>

        <Layer id="socket">
          {S.sock > 0.01 && <Sprite name="socket/hero_face" x={SOCK.x} y={SOCK.y - 40 * (1 - Math.min(1, S.sock)) + id(3).y} w={SOCK.w} op={Math.min(1, S.sock * 1.5)} />}
        </Layer>

        <Layer id="plugs">
          {S.learn > 0 && S.learn < 1 && [0, 1, 2, 3, 4].map((k) => {
            const u = (S.learn * 2.2 - k * 0.25);
            if (u <= 0 || u >= 1) return null;
            const p = FEED.at(u);
            return <svg key={k} width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}><circle cx={p[0]} cy={p[1]} r={11} fill={C.blueHi} /></svg>;
          })}
          {S.learn > 0 && <Runner d={`M${BAR_X + BAR_W * 0.5},160 C1000,60 820,60 620,92`} draw={Math.min(1, S.learn * 3)} width={12} op={1 - clamp01((S.again - 0.6) * 2.5)} />}
          {PLUGS.map((n, i) => {
            const a = S[`p${i}`];
            if (a <= 0.01 || out1 >= 1) return null;
            const x = mix(ch.x + 120, COL_X, Math.min(1, a)) + 900 * out1 * out1, y = mix(ch.y - 120, ROW_Y(i), Math.min(1, a));
            const sc = S[`s${i}`];
            return (
              <React.Fragment key={i}>
                <Sprite name={`plug/${n}_34`} x={x} y={y + id(10 + i).y} w={130} op={Math.min(1, a * 1.5) * (1 - out1)} sx={-1} />
                {sc > 0.005 && <Slab x={BAR_X + 900 * out1 * out1} y={ROW_Y(i) - 14} w={Math.max(6, BAR_W * sc)} h={28} r={9} color={i === 2 ? C.blue : C.blueHi} depth={5}
                                     op={1 - out1} sheen={sc < SCORE[i] ? sc : -1} id={`sc${i}`} />}
              </React.Fragment>
            );
          })}
          {/* 第二批，以及 new structures 之后一批批冒出来 */}
          {f > E.again.l && PLUGS.map((n, i) => {
            const b = batch2(i);
            if (b <= 0.01) return null;
            const gone = clamp01(S.stream * 12);
            return <Sprite key={`b${i}`} name={`plug/${PLUGS[(i + 2) % 5]}_34`} x={mix(ch.x + 120, COL_X, b) + 600 * gone * gone} y={mix(ch.y - 120, ROW_Y(i), b) + id(20 + i).y} w={130} op={b * (1 - gone)} sx={-1} />;
          })}
        </Layer>

        <Layer id="new">
          {S.stream > 0 && [0, 1, 2, 3, 4, 5].map((k) => {
            const st = (S.stream * 3 + k / 6) % 1;
            const pts = [[ch.x + 160, ch.y - 150], [980, 300], [1180, 420 + (k % 3) * 120]];
            const p = pathOf(pts).at(st);
            return <Sprite key={k} name={`plug/${PLUGS[k % 5]}_34`} x={p[0]} y={p[1]} w={110} op={Math.min(1, st * 8, (1 - st) * 8)} sx={-1} rot={20 * st} />;
          })}
        </Layer>

        <Layer id="txt" exempt>
          <Label text="dozens of AI models" size={52} x={560} y={176} at={E.dozens.l + 20} out={E.invent.s} align="center" />
          <Label text="fit score" size={52} x={BAR_X + BAR_W + 90} y={224} at={E.score.l} out={E.again.s} align="left" />
          {S.maker > 0.01 && <Tag x={BASE.x + BASE.w + 30} y={BASE.y + 10} align="left" op={Math.min(1, S.maker)}>the makers' claim</Tag>}
          <Label text="within hours" size={52} x={1600} y={720} at={E.hours.l} align="center"/>
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023 (Chemistry42)</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B407" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
