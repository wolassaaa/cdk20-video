// HKBU SCIE1007 课程作业的科普视频：B 档 7-04 "Three: race them. An AI route and a classic route, same target, same budget, same definition of a hit.
// Then we'd know exactly how much faster AI really is."
// 规则 v2：第 7 区台面，左上角 3 号步骤牌落下。race：两条并排跑道件落到台面上，右端两块秒表立起；
// AI：上道起跑线上落一块 Chemistry42 芯片（AI 路线），名牌 AI route；classic：下道起跑线上落一块孔板（传统高通量筛选），名牌 classic route；
// same target / budget / definition of a hit：上方三块条件牌依次翻起，每翻一块，两条道上同一位置各亮一个一样的件（CDK20 插座、金币、绿勾）；hit：三块牌一起轻抖锁定；
// know：两件在起跑线上往后一蹲（蓄势），秒表指针归零；faster：两件沿跑道起跑，两块秒表开始走；
// is：手写 how much faster?（终点线还没人到——这一步还没做过）。结尾 T5 runner 擦除接下一段。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_7-04.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, shade, Stage, Sprite, Slab, Plate, Dial, Tag, Pen, Tick, Engrave, Source, evMapB, whipX, impact, T5Out, camBreath} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";
import {MiniPlate} from "./board6.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 7;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
// 跑道自己画（贴图是斜透视，件对不上道）：两条骨白道，中间虚线，左端起跑线，右端黑白格终点
const TRK = {x0: 250, x1: 1500};
const LANE = [500, 690];                             // 两条道的中线
const LH = 140;
const X0 = 380, XF = 1400;                           // 起跑线、终点线
const DIAL = {x: 1650, r: 66};
const COND = ["same target", "same budget", "same hit definition"];
const CX = (k) => 640 + k * 230;

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.tw("plate", 0, 1, E.p3.s, E.p3.l + 8, "power3.out");
    X.land("trk", 0, 1, E.tracks.l, {antic: false, dur: 20});
    X.tw("ai", 0, 1, E.ai.s, E.ai.l, "power2.out");
    X.tw("cls", 0, 1, E.classic.s, E.classic.l, "power2.out");
    ["t1", "t2", "t3"].forEach((k, i) => {
      X.tw(`c${i}`, 0, 1, E[k].s, E[k].l, "power2.inOut");
      X.tw(`i${i}`, 0, 1, E[k].l - 4, E[k].l + 12, "back.out(2)");
    });
    X.jiggle("cj", E.t3_lbl.l, 6, 0);
    X.tw("crouch", 0, 1, E.ready.s, E.ready.l, "power2.inOut");
    X.tw("zero", 0, 1, E.ready.s, E.ready.l, "power2.inOut");
    X.tw("run", 0, 1, E.run.s, LEN - 10, "power1.in");
  });
  const id = (s) => idle(f, s, {rot: 0.5, bob: 1.4});
  const run = S.run;
  const crouch = S.crouch * (1 - cl(run * 6));
  // 两件跑：AI 道和传统道跑法一样（结果没人知道），只到半路
  const pos = (k) => mix(X0, mix(X0, XF, 0.42 - 0.03 * k), run) - 26 * crouch;
  const needle = (k) => (S.zero < 1 ? mix(k ? 140 : 210, 0, S.zero) : 0) + run * 300;
  const card = (k) => {
    const p = S[`c${k}`] || 0;
    if (p < 0.01) return null;
    const flip = Math.abs(Math.cos(Math.PI * p)), front = p >= 0.5;
    return (
      <div key={k} style={{position: "absolute", left: 330 + k * 400, top: 190 - (S.cj || 0), width: 370, height: 110, transform: `scaleY(${Math.max(0.04, flip).toFixed(3)})`, transformOrigin: "50% 100%"}}>
        <Slab x={0} y={0} w={370} h={110} r={14} color={front ? C.bone : C.black} depth={10} id={`cond${k}`}>
          {front && <div style={{width: 370, height: 110, display: "flex", alignItems: "center", justifyContent: "center"}}><Engrave size={42}>{COND[k]}</Engrave></div>}
        </Slab>
      </div>
    );
  };
  const icon = (k, lane) => {
    const u = S[`i${k}`] || 0;
    if (u < 0.01) return null;
    const x = CX(k), y = LANE[lane] - 4, sc = 1.3 * Math.min(1.15, u);
    const body = k === 0 ? <Sprite name="socket/hero_34" x={x} y={y} w={74 * sc} shadow={false} />
      : k === 1 ? <div style={{position: "absolute", left: x - 26 * sc, top: y - 26 * sc, width: 52 * sc, height: 52 * sc, borderRadius: 26 * sc,
                               background: `radial-gradient(circle at 35% 30%, ${C.bone}, ${C.gold} 45%, ${shade(C.gold, 0.3)})`, boxShadow: "0 3px 5px rgba(0,0,0,0.4)"}} />
      : <Tick x={x} y={y} s={56 * sc} p={cl(u * 1.4)} sw={10} />;
    return <React.Fragment key={`${k}${lane}`}>{body}</React.Fragment>;
  };
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2"], 36)} whip={f < 7 ? whipX(f, 0, "in", -1) : 0} shakeX={impact(f, E.tracks.l)} over={<T5Out name="runner" f={f} len={LEN} />}>
        <Layer id={["tracks", "conds", "race"]}>
          {S.trk > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, opacity: cl(S.trk * 2), transform: `translateY(${(-60 * (1 - Math.min(1, S.trk))).toFixed(1)}px)`}}>
              {LANE.map((ly, l) => (
                <Slab key={l} x={TRK.x0} y={ly - LH / 2} w={TRK.x1 - TRK.x0} h={LH} r={18} color={C.bone} depth={12} id={`lane${l}`}>
                  <div style={{position: "absolute", left: 40, top: LH / 2 - 3, width: TRK.x1 - TRK.x0 - 120, height: 6, backgroundImage: `repeating-linear-gradient(90deg, ${C.grey} 0 26px, transparent 26px 46px)`, opacity: 0.6}} />
                  <div style={{position: "absolute", left: X0 - TRK.x0 - 4, top: 12, width: 8, height: LH - 24, borderRadius: 4, background: C.ink}} />
                  {[...Array(10)].map((_, q) => <div key={q} style={{position: "absolute", left: XF - TRK.x0 + (q % 2) * 22, top: 14 + Math.floor(q / 2) * 22.4, width: 22, height: 22.4, background: C.ink}} />)}
                </Slab>
              ))}
            </div>
          )}
          {[0, 1, 2].map(card)}
          {[0, 1, 2].map((k) => [0, 1].map((l) => icon(k, l)))}
          {S.ai > 0.01 && <Sprite name="chip_chemistry42/34" x={pos(0)} y={LANE[0] - 4 - 50 * (1 - Math.min(1, S.ai)) + id(1).y * (1 - run)} w={180} op={cl(S.ai * 2)} />}
          {S.cls > 0.01 && <MiniPlate x={pos(1)} y={LANE[1] - 6 - 50 * (1 - Math.min(1, S.cls)) + id(2).y * (1 - run)} s={0.8} op={cl(S.cls * 2)} seed={4} />}
          {S.trk > 0.3 && [0, 1].map((k) => (
            <Dial key={k} cx={DIAL.x} cy={LANE[k]} r={DIAL.r} op={cl(S.trk * 2 - 0.6)} needle={needle(k)} color={C.bone}
                  ticks={[0, 90, 180, 270].map((a) => [a, null, true])} />
          ))}
        </Layer>
        <Layer id="txt" exempt>
          <div style={{position: "absolute", left: 0, top: 0, opacity: cl(S.plate * 2), transform: `translateY(${(-80 * (1 - S.plate)).toFixed(1)}px)`}}>
            <Plate x={70} y={60} w={110} h={110} text="3" size={80} color={C.bone} id="step3" />
          </div>
          <Tag x={X0} y={LANE[0] - LH / 2 - 52} op={cl((f - E.ai.l) / 8) * (1 - cl(run * 4))} on="chip">AI route</Tag>
          <Tag x={X0} y={LANE[1] + LH / 2 + 18} op={cl((f - E.clbl.l) / 8) * (1 - cl(run * 4))} on="mp">classic route</Tag>
          <Pen text="how much faster?" x={1180} y={790} at={E.run.l + 10} rot={-3} />
          <Source>Illustration · a fair head-to-head test that has not been run yet</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B704" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
