// HKBU SCIE1007 课程作业的科普视频：B 档 8-02 "How can computer-aided methods help scientists find and assess cancer drug candidates?
// In this case, at four points. Picking a target from data. Predicting the lock's shape. Designing new keys. And ranking which ones to make.
// That's our first objective, met for this case."
// 规则 v2：第 8 区台面。How：目标牌 OBJECTIVE 1 落在画面中间，右边一个空的勾选框；computer-aided：下面一条骨白路展开；methods：目标牌缩到左上角；
// scientists：路的起点落下实验台的件（培养皿 + 样本管），名牌 scientists' lab；find / assess：路一段一段亮成蓝色；candidates：一排候选插头沿路排开。
// In this case：插头退开；four points：路上方挂下四个工具节点（PandaOmics 芯片、AlphaFold 芯片、Chemistry42 芯片、打分排名板），落在 points。
// target：PandaOmics 亮，上方弹出 Top 20 牌；data：名牌 target from data。Predicting：AlphaFold 亮；lock's：CDK20 插座升起；shape：上方长出蓝色预测模型。
// Designing：Chemistry42 亮；keys：芯片吐出一个 001 插头。ranking：排名板五根分数条长出，游标往高分端推；make：前两名变绿。
// first：四个件缩回、四个节点之间连线亮起，目标牌回到中间；objective：目标牌外框亮；met：勾选框里描出绿勾（T7 一抖）；case：名牌 for this case。
// 开头 T5 runner（8-01 出镜），结尾 T2 往左甩（8-03）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_8-02.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Label, Stage, Sprite, Slab, Runner, Tag, Tick, Engrave, Source, evMapB, whipX, impact, T5In, camBreath} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 8;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const ROAD_Y = 800;
const ROADD = `M 100 ${ROAD_Y} L 1820 ${ROAD_Y}`;
const GOAL = {x: 960, y: 250, w: 640, h: 150};
const NODE = [360, 800, 1240, 1640];
const NODE_Y = 610;
const CHIPS = ["chip_pandaomics/34", "chip_alphafold/34", "chip_chemistry42/34"];
const POPY = 300;
const SCORES = [0.92, 0.84, 0.66, 0.52, 0.38];

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("goal", 0, 1, E.goal1.l, {antic: false, dur: 18});
    X.tw("road", 0, 1, E.road.s, E.road.l + 30, "power2.out");
    X.tw("badge", 0, 1, E.badge.s, E.badge.l + 12, "power2.inOut");
    X.tw("lab", 0, 1, E.sci.s, E.sci.l, "power2.out");
    X.tw("find", 0, 1, E.find.s, E.find.l + 8, "power2.out");
    X.tw("assess", 0, 1, E.assess.s, E.assess.l + 8, "power2.out");
    X.tw("cand", 0, 1, E.cand.s, E.cand.l + 20, "none");
    X.tw("clear", 0, 1, E.case_in.s, E.case_in.l + 10, "power2.out");
    [0, 1, 2, 3].forEach((k) => X.land(`n${k}`, 0, 1, E.pts.s + 8 * k + 6, {antic: false, dur: 14}));
    X.tw("p0", 0, 1, E.panda.s, E.panda.l, "back.out(1.6)");
    X.tw("p1", 0, 1, E.lock_in.s, E.lock_in.l, "power2.out");
    X.tw("grow", 0, 1, E.shape.s, E.shape.l + 10, "power1.inOut");
    X.tw("p2", 0, 1, E.key.s, E.key.l, "power2.out");
    X.tw("bars", 0, 1, E.rank.s, E.rank.l + 20, "power2.out");
    X.tw("cursor", 0, 1, E.rank.l, E.make.s, "power2.inOut");
    X.tw("pick", 0, 1, E.make.s, E.make.l, "power2.out");
    X.tw("tuck", 0, 1, E.focus.s - 10, E.focus.s + 20, "power2.in");
    X.tw("links", 0, 1, E.focus.s, E.focus.l, "power2.inOut");
    X.tw("back", 0, 1, E.focus.s + 6, E.focus.l, "power2.inOut");
    X.tw("ring", 0, 1, E.obj.s, E.obj.l, "power2.out");
    X.tw("tick", 0, 1, E.met.s, E.met.l, "power2.out");
    X.jiggle("gj", E.met.l, 7, 0);
  });
  const whip = f > LEN - 8 ? whipX(f, LEN - 7, "out", -1) : 0;
  const id = (s) => idle(f, s, {rot: 0.5, bob: 1.5});
  const corner = S.badge * (1 - S.back);
  const GS_MIN = 0.55;                      // 角标最小缩放：Objective 1 刻字 64 × 0.55 ≈ 35 px（≥ 30）
  const gs = mix(1, GS_MIN, corner);
  const gx = mix(GOAL.x, 70 + (GOAL.w * GS_MIN) / 2, corner), gy = mix(GOAL.y, 60 + (GOAL.h * GS_MIN) / 2, corner);
  const lit = [S.p0 * (f < E.af.s ? 1 : 0.35), f >= E.af.s ? (f < E.chem42.s ? 1 : 0.35) : 0, f >= E.chem42.s ? (f < E.rank.s ? 1 : 0.35) : 0];
  const tuck = 1 - S.tuck;
  const node = (k) => S[`n${k}`] || 0;
  const plugs = [...Array(9)].map((_, k) => {
    const u = cl(S.cand * 9 - k);
    if (u <= 0) return null;
    return <Sprite key={k} name={k===4&&f>=E.find.l?"plug/048_34":"plug/001_34"} x={mix(150, 520 + k * 150, u) + 200 * S.clear} y={ROAD_Y - 40 - 30 * Math.sin(Math.PI * u)} w={90} op={1 - S.clear} />;
  });
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2", "s3", "s4", "s5", "s6", "s7"], 36)} whip={whip} shakeX={impact(f, E.met.l)} over={<T5In name="runner" f={f} />}>
        <Layer id={["road", "pts", "panda", "af", "chem42", "rank"]}>
          <Runner d={ROADD} width={60} draw={S.road} />
          {S.find > 0.01 && <div style={{position: "absolute", left: 130, top: ROAD_Y - 10, width: (560 * S.find + 600 * S.assess) * (1 - S.clear * 0), height: 20, borderRadius: 10, background: C.blueHi,
                                         opacity: 0.85 * (1 - 0.6 * S.clear), boxShadow: "0 0 14px rgba(61,107,230,0.8)"}} />}
          {S.lab > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, opacity: cl(S.lab * 2) * (1 - S.clear)}}>
              <Sprite name="dish/34" x={190} y={ROAD_Y - 70 - 40 * (1 - Math.min(1, S.lab))} w={150} />
              <Sprite name="tube/34" x={170} y={ROAD_Y - 170 - 40 * (1 - Math.min(1, S.lab))} w={110} />
            </div>
          )}
          {plugs}
          {/* 四个工具节点 */}
          {NODE.map((x, k) => node(k) > 0.01 && (
            <div key={k} style={{position: "absolute", left: 0, top: 0, opacity: cl(node(k) * 2)}}>
              <div style={{position: "absolute", left: x - 3, top: NODE_Y + 70, width: 6, height: (ROAD_Y - NODE_Y - 80) * Math.min(1, node(k)), background: C.bone, opacity: 0.8}} />
              {k < 3 ? <Sprite name={CHIPS[k]} x={x} y={NODE_Y - 70 * (1 - Math.min(1, node(k))) + id(k).y} w={340} rim={lit[k] > 0.5 ? 0.7 : 0} />
                : (
                  <Slab x={x - 160} y={NODE_Y - 100 - 70 * (1 - Math.min(1, node(k)))} w={340} h={228} r={14} color={C.bone} depth={10} id="rankboard">
                    <div style={{position:"absolute",left:24,top:16}}><Engrave size={38}>ranking</Engrave></div>
                    {SCORES.map((v, j) => (
                      <React.Fragment key={j}>
                        <div style={{position: "absolute", left: 24, top: 65 + j * 28, width: 240, height: 20, borderRadius: 5, background: "rgba(0,0,0,0.10)"}} />
                        <div style={{position: "absolute", left: 24, top: 65 + j * 28, width: 240 * v * S.bars, height: 20, borderRadius: 5, background: S.pick > 0.5 && j < 2 ? C.green : C.blueHi, opacity: 0.9}} />
                      </React.Fragment>
                    ))}
                    {S.bars > 0.5 && <div style={{position: "absolute", left: 274, top: mix(65 + 4 * 28, 65, S.cursor) - 1, width: 0, height: 0, borderTop: "11px solid transparent", borderBottom: "11px solid transparent", borderRight: `16px solid ${C.ink}`}} />}
                  </Slab>
                )}
            </div>
          ))}
          {/* 节点之间的连线（first） */}
          {S.links > 0.01 && <div style={{position: "absolute", left: NODE[0], top: NODE_Y + 100, width: (NODE[3] - NODE[0]) * S.links, height: 8, borderRadius: 4, background: C.blueHi, boxShadow: "0 0 12px rgba(61,107,230,0.85)"}} />}
          {/* 各节点弹出的件 */}
          {S.p0 > 0.01 && tuck > 0.01 && <Sprite name="top20/34" x={NODE[0]} y={mix(NODE_Y - 60, POPY, Math.min(1, S.p0)) + id(5).y} w={330 * Math.min(1, S.p0) * tuck} op={cl(S.p0 * 2)} />}
          {S.p1 > 0.01 && tuck > 0.01 && <Sprite name="socket/hero_34" x={NODE[1] - 120} y={mix(NODE_Y - 40, POPY + 60, S.p1)} w={130 * tuck} op={cl(S.p1 * 2)} />}
          {S.grow > 0.01 && tuck > 0.01 && <Sprite name="af/front305" x={NODE[1] + 40} y={POPY - 10 + id(6).y} w={280 * tuck} style={{clipPath: `inset(${((1 - S.grow) * 100).toFixed(1)}% 0 0 0)`}} />}
          {S.p2 > 0.01 && tuck > 0.01 && <Sprite name="plug/001_34" x={NODE[2]} y={mix(NODE_Y - 40, POPY + 20, S.p2) - 80 * Math.sin(Math.PI * S.p2) + id(7).y} w={210 * tuck} op={cl(S.p2 * 2)} rot={-10} />}
        </Layer>
        <Layer id={["goal1"]}>
          {S.goal > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, opacity: cl(S.goal * 2), transformOrigin: `${GOAL.x}px ${GOAL.y}px`,
                         transform: `translate(${(gx - GOAL.x).toFixed(1)}px, ${(gy - GOAL.y - 50 * (1 - Math.min(1, S.goal)) - (S.gj || 0)).toFixed(1)}px) scale(${gs.toFixed(3)})`}}>
              <Slab x={GOAL.x - GOAL.w / 2} y={GOAL.y - GOAL.h / 2} w={GOAL.w} h={GOAL.h} r={20} color={C.bone} depth={12} id="goal">
                <div style={{position: "absolute", left: 40, top: 0, height: GOAL.h, display: "flex", alignItems: "center"}}><Engrave size={64}>Objective 1</Engrave></div>
                <div style={{position: "absolute", left: GOAL.w - 150, top: 25, width: 100, height: 100, borderRadius: 14, border: `6px solid ${C.ink}`, boxSizing: "border-box"}} />
              </Slab>
              {S.ring > 0.01 && <div style={{position: "absolute", left: GOAL.x - GOAL.w / 2 - 10, top: GOAL.y - GOAL.h / 2 - 10, width: GOAL.w + 20, height: GOAL.h + 22, borderRadius: 26,
                                                 boxShadow: `0 0 0 6px ${C.blue}`, opacity: S.ring}} />}
              <Tick x={GOAL.x + GOAL.w / 2 - 100} y={GOAL.y} s={90} p={S.tick} sw={16} />
            </div>
          )}
        </Layer>
        <Layer id="txt" exempt>
          <Tag x={1300} y={ROAD_Y + 40} op={cl((f - E.cand.l) / 10) * (1 - S.clear)}>candidates</Tag>
          <Tag x={200} y={ROAD_Y - 290} op={cl((f - E.sci.s) / (E.sci.l - E.sci.s + 2)) * (1 - S.clear)} on="dish">scientists' lab</Tag>
          {[[E.data,"target"],[E.shape,"structure"],[E.key,"design"],[E.rank,"ranking"]].map(([e,t],i,a)=>e && <Label key={t} x={NODE[i]} y={NODE_Y+117} text={t} at={e.l} out={a[i+1]?.[0]?.s-9||E.met.s} align="center"/>)}
          {f>=E.data.l && <Source>Illustration · the four tools as used in Ren et al., Chem. Sci. 2023</Source>}
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B802" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
