// HKBU SCIE1007 课程作业的科普视频：B 档 4-09（B 画外音）"The team gave it the pocket's shape and one rule…"
// s1 The team gave it：Chemistry42 芯片落位；the pocket's shape：右边插座正面落位；one rule：标 one rule；every key：一个金插头从芯片飞到插孔前；
//    must grip a spot：插头尖卡到孔边左侧那一点（T7 一抖）；called the hinge：那一点亮一圈，手写 hinge。
// s2 Its filters：清场，筛子落位，上面一排六个金插头；to toss：插头落到筛子上；reactive：带红点的一个被甩出去；possibly toxic groups：又一个；
//    to score：剩下四个漏过筛子，两块表盘进来；how drug-like：左表指针摆高；easy to make：右表指针摆高。
// 接点：开头 T5 料杆擦除（上一段 4-08 是出镜段），结尾 T5 芯片擦除（下一段 W3 是 A 段芯片）。L0 第 4 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_4-09.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Tick, camBreath, Stage, Sprite, Slab, Label, Pen, Source, Engrave, anchorOf, pathOf, evMapB, T5In, T5Out, impact} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 4;

const CHIP = {x: 400, y: 330, w: 420};
const SOCK = {x: 1300, y: 504, w: 694};
const [mdx, mdy] = anchorOf("socket/hero_face", "mouth", SOCK.w);
const M = [SOCK.x + mdx, SOCK.y + mdy];
const HOLE_R = 205 * (SOCK.w / 1312);
const HINGE = [M[0] - HOLE_R * 0.8, M[1] - HOLE_R * 0.18];
const KEY_W = 200;
const [tipOX, tipOY] = anchorOf("plug/A_34", "tip", KEY_W);   // 翻过来以后尖在 (x − tipOX, y + tipOY)
const FLY = pathOf([[CHIP.x + 150, CHIP.y + 90], [640, 520], [880, 560], [M[0] - 40, M[1] + 10]]);

// s2：筛子、六个插头
const SIEVE = {x: 980, y: 505, w: 700};
const NAMES = ["A", "B", "C", "D", "E", "F"];
const PW = 150;
const TOP = NAMES.map((_, i) => [610 + i * 140, 150]);
const ON = NAMES.map((_, i) => [740 + i * 66, 352 + (i % 2) * 22]);
const BELOW = NAMES.map((_, i) => [690 + i * 110, 740]);
const BAD_R = 1, BAD_T = 4;                       // 带红点的两个
// 两根竖分数条（圆表盘像时钟，见 5-08 初审）：骨白槽，蓝色从下往上涨
const DIALS = [{cx: 1210, cy: 430}, {cx: 1570, cy: 430}];   // 两个 Label 的中心（左移 80，让 easy to make 后的勾留在托盘里）
const MT = {w: 80, h: 300, top: 270};

const clamp01 = (v) => Math.max(0, Math.min(1, v));
const mix = (a, b, t) => a + (b - a) * t;

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("chip", 0, 1, E.chip.l, {antic: false});
    X.land("sock", 0, 1, E.pocket.l, {antic: false});
    X.tw("fly", 0, 1, E.key.s, E.key.l, "power1.inOut");
    X.tw("grip", 0, 1, E.grip.s, E.grip.l, "power3.in");
    X.jiggle("gripJ", E.grip.l, 5, 0);
    X.tw("hinge", 0, 1, E.hinge.s, E.hinge.l + 20, "power2.out");
    X.tw("clear", 0, 1, E.filt.s - 6, E.filt.l + 20, "power1.in");
    X.land("sieve", 0, 1, E.filt.l, {antic: false});
    X.group(NAMES.map((_, i) => `p${i}`), 0, 1, E.filt.l, {antic: false, step: 4});
    X.tw("toss", 0, 1, E.toss.s, E.toss.l + 8, "power2.in");
    X.tw("react", 0, 1, E.react.s, E.react.e + 20, "power2.out");
    X.tw("toxic", 0, 1, E.toxic.s, E.toxic.e + 20, "power2.out");
    X.tw("drop", 0, 1, E.score.s - 30, E.score.s + 10, "power2.in");
    X.tw("shift", 0, 1, E.score.s, E.score.l + 24, "power2.out");
    X.tw("dials", 0, 1, E.score.s, E.score.l + 10, "power2.out");
    X.tw("n1", 0, 1, E.drug.s, E.drug.l + 16, "back.out(1.4)");
    X.tw("n2", 0, 1, E.easy.s, E.easy.l + 16, "back.out(1.4)");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const shake = impact(f, E.grip.l);
  const out1 = -2200 * S.clear;

  // 插头尖：沿路飞到孔口，再一下卡到孔边的铰点
  const fp = FLY.at(S.fly);
  const tip = [mix(fp[0], HINGE[0] + 6, S.grip), mix(fp[1], HINGE[1], S.grip) + (S.gripJ || 0)];
  const hingeRing = S.hinge > 0.01 ? Math.sin(Math.PI * clamp01(S.hinge * 1.4)) : 0;

  // s2：每个插头的位置
  const plugs = NAMES.map((n, i) => {
    const a = S[`p${i}`];
    let p = [TOP[i][0], TOP[i][1] - 50 * (1 - Math.min(1, a))];
    const ti = clamp01(S.toss * 1.25 - i * 0.05);
    p = [mix(p[0], ON[i][0], ti), mix(p[1], ON[i][1], ti * ti)];
    let rot = 0, op = Math.min(1, a * 1.5);
    if (i === BAD_R && S.react > 0) { p = [p[0] + 900 * S.react, p[1] - 420 * Math.sin(Math.PI * 0.6 * S.react)]; rot = 220 * S.react; op *= 1 - clamp01((S.react - 0.7) * 3.3); }
    if (i === BAD_T && S.toxic > 0) { p = [p[0] - 1000 * S.toxic, p[1] - 380 * Math.sin(Math.PI * 0.6 * S.toxic)]; rot = -220 * S.toxic; op *= 1 - clamp01((S.toxic - 0.7) * 3.3); }
    if (i !== BAD_R && i !== BAD_T) p = [mix(p[0], BELOW[i][0], S.drop), mix(p[1], BELOW[i][1], S.drop * S.drop)];
    return {n, i, x: p[0] - 470 * S.shift, y: p[1], rot, op, bad: i === BAD_R || i === BAD_T};
  });


  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, [])} shakeX={shake} over={<><T5In name="runner" f={f} /><T5Out name="runner" f={f} len={LEN} /></>}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${out1}px)`}}>
          <Layer id="chip">
            {S.chip > 0.01 && <Sprite name="chip_chemistry42/34" x={CHIP.x} y={CHIP.y - 50 * (1 - Math.min(1, S.chip)) + id(1).y} w={CHIP.w} op={Math.min(1, S.chip * 1.5)} rot={id(1).r} />}
          </Layer>
          <Layer id="socket">
            {S.sock > 0.01 && <Sprite name="socket/hero_face" hero x={SOCK.x} y={SOCK.y - 50 * (1 - Math.min(1, S.sock)) + id(2).y} w={SOCK.w} op={Math.min(1, S.sock * 1.5)} />}
            {hingeRing > 0.01 && (
              <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: id(2).y, overflow: "visible"}}>
                <circle cx={HINGE[0]} cy={HINGE[1]} r={16 + 22 * S.hinge} fill="none" stroke={C.bone} strokeWidth={6} opacity={hingeRing} />
                <circle cx={HINGE[0]} cy={HINGE[1]} r={11} fill={C.bone} opacity={0.9 * clamp01(S.hinge * 3)} />
              </svg>
            )}
          </Layer>
          <Layer id="key">
            {S.fly > 0.001 && (
              <Sprite name="plug/A_34" x={tip[0] + tipOX} y={tip[1] - tipOY + id(3).y * (1 - S.grip)} w={KEY_W} sx={-1} rot={8 * Math.sin(Math.PI * S.fly) * (1 - S.grip)}
                      lift={22 * Math.sin(Math.PI * S.fly) * (1 - S.grip)} op={clamp01(S.fly * 5)} />
            )}
          </Layer>
          <Layer id="txt1" exempt>
            <Label text="one rule" size={56} x={CHIP.x} y={530} at={E.rule.l} out={E.hinge.l} align="center" />
            <Label text="rule: must grip the hinge" size={56} x={CHIP.x} y={530} at={E.hinge.l} align="center" />
            <Pen text="hinge" x={HINGE[0] - 120} y={150} at={E.hinge.s} size={88} />
          </Layer>
        </div>

        <Layer id="sieve">
          {S.sieve > 0.01 && <Sprite name="sieve/34" x={SIEVE.x - 470 * S.shift} y={SIEVE.y - 50 * (1 - Math.min(1, S.sieve)) + id(4).y + 10*Math.sin((f-E.filt.l)*.65)*Math.max(0,1-Math.abs(f-E.filt.l)/21)} w={SIEVE.w} op={Math.min(1, S.sieve * 1.5)} rot={id(4).r} />}
          {plugs.map((p) => S[`p${p.i}`] > 0.01 && p.op > 0.01 && (
            <Sprite key={p.i} name={`plug/${p.n}_34`} x={p.x} y={p.y + id(10 + p.i).y} w={PW} sx={-1} rot={p.rot + id(10 + p.i).r} op={p.op}>
              {p.bad && <div style={{position: "absolute", left: PW * 0.62, top: PW * 0.12, width: 26, height: 26, borderRadius: 13, background: C.red,
                                     boxShadow: "inset -3px -4px 0 rgba(0,0,0,0.25), inset 3px 3px 0 rgba(255,255,255,0.35)"}} />}
            </Sprite>
          ))}
        </Layer>
        <Layer id="dials">
          {[[E.drug.l, DIALS[0].cx + 153], [E.easy.l, DIALS[1].cx + 190]].map(([at, x], i) => <Tick key={i} x={x} y={272} s={50} p={clamp01((f - at) / 14)} />)}
        </Layer>
        <Layer id="txt2" exempt>
          <Pen text="reactive" x={1480} y={150} at={E.react.l} out={E.score.s} size={76} />
          <Pen text="possibly toxic" x={150} y={150} at={E.toxic.l} out={E.score.s} size={76} />
          <Label text="drug-like" size={52} x={DIALS[0].cx} y={248} at={E.drug.l} align="center" />
          <Label text="easy to make" size={52} x={DIALS[1].cx} y={248} at={E.easy.l} align="center" />
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023 (Chemistry42 design rules)</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B409" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
