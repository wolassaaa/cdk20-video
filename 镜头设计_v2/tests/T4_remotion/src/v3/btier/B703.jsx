// HKBU SCIE1007 课程作业的科普视频：B 档 7-03 "Two: check the AlphaFold model against a lab-measured structure, once one exists.
// And feed every result, including the failures, back into the next round."
// 规则 v2：第 7 区台面，左上角 2 号步骤牌落下。
// AlphaFold：蓝色预测 CDK20 模型（AlphaFold DB 带状模型）升起；model：名牌 predicted model (AlphaFold DB v6)；
// lab-measured：上方现出一个同形的磨砂白色外形（实验测出来的结构）；structure：它慢慢落下叠在模型上做比对，落定时偏了一点（对不齐的地方几道红色短线）；
// once / exists：磨砂外形半透明慢闪，名牌 lab-measured structure，手写 not measured yet（现在还没有实验结构）。
// feed：模型和外形缩到左边，Chemistry42 芯片从右边滑进来，一条料杆连过去；every result：一串金色插头（做出来测过的分子）沿料杆流进芯片；
// failures：几个灰色打叉的插头也跟着流进去（手写 failures too）；back：最后一个进芯片入口；next round：芯片上的"想—做—测—改"环转一圈，名牌 next round。
// 开头 T2 甩进，结尾 T2 往左甩。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_7-03.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Stage, Sprite, Plate, Runner, Tag, Label, Pen, Source, evMapB, whipX, impact, pathOf, camBreath} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 7;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const AF = {x: 795, y: 499, w: 462};
const AF2 = {x: 420, y: 420, w: 340};
const CHIP = {x: 1440, y: 580, w: 470};
const LANE = pathOf([[60, 860], [500, 850], [900, 800], [1180, 680], [1290, 600]]);
const KEYS = ["A", "B", "C", "D", "E", "F", "001", "048"].map((n, k) => ({n, fail: false, k}));
const FAILS = ["blank", "blank", "blank", "blank"].map((n, k) => ({n, fail: true, k}));
const MISS = [[-80, -60, 30], [60, -110, -20], [110, 40, 70], [-40, 120, 10]];      // 对不齐处的红色短线（相对模型中心）

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.tw("plate", 0, 1, E.p2.s, E.p2.l + 8, "power3.out");
    X.tw("af", 0, 1, E.p2.l + 6, E.af.l, "sine.inOut");
    X.tw("afpop", 0, 1, E.af.s, E.af.l, "back.out(2)");          // 模型从 2 号牌落下就开始慢慢升（不空等）
    X.tw("gin", 0, 1, E.ghost_in.s, E.ghost_in.l, "power2.out");
    X.tw("gdown", 0, 1, E.ghost.s, E.ghost.l, "power1.inOut");
    X.tw("miss", 0, 1, E.ghost.l, E.ghost.l + 16, "power2.out");
    X.tw("shift", 0, 1, E.shift.s - 10, E.shift.l + 14, "power2.inOut");
    X.tw("chip", 0, 1, E.shift.s, E.shift.l + 10, "power3.out");
    X.tw("lane", 0, 1, E.shift.l, E.keys.s + 6, "power2.out");
    X.tw("keys", 0, 1, E.keys.s, E.back.l, "none");
    X.tw("fails", 0, 1, E.fail.s, E.back.l + 6, "none");
    X.tw("loop", 0, 1, E.back.l + 8, Math.max(E.loop.e,LEN-10), "power2.inOut");
    X.jiggle("chj", E.loop.l, 6, 0);
  });
  const whip = f < 7 ? whipX(f, 0, "in", -1) : f > LEN - 8 ? whipX(f, LEN - 7, "out", -1) : 0;
  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const m = {x: mix(AF.x, AF2.x, S.shift), y: mix(AF.y, AF2.y, S.shift), w: mix(AF.w, AF2.w, S.shift)};
  const sc = m.w / AF.w;
  const gy = mix(m.y - 300, m.y, S.gdown), gdx = 16 * sc * S.gdown, grot = 3 * S.gdown;
  const pulse = f > E.once.s ? 0.3 + 0.14 * Math.sin((f - E.once.s) / 9) : 0.42;
  // 插头沿料杆流进芯片：金色 8 个在 keys 段，灰色 4 个在 fails 段；u 走到 1 进芯片
  const flow = (list, prog, gap) => list.map((p) => {
    const u = prog * (1 + gap * (list.length - 1)) - p.k * gap;
    if (u <= 0 || u >= 1) return null;
    const [x, y, a] = LANE.at(u);
    const w = 84 * (1 - 0.4 * Math.max(0, u - 0.8) / 0.2);
    return (
      <div key={`${p.fail}${p.k}`} style={{position: "absolute", left: 0, top: 0}}>
        <Sprite name={`plug/${p.n}_34`} x={x} y={y - 26} w={w} rot={a * 0.5} shadow={false} style={p.fail ? {filter: "grayscale(1) brightness(0.75)"} : undefined} />
        {p.fail && [45, -45].map((r) => <div key={r} style={{position: "absolute", left: x - 26, top: y - 30, width: 52, height: 8, borderRadius: 4, background: C.red, transform: `rotate(${r}deg)`}} />)}
      </div>
    );
  });
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2"], 36)} whip={whip} shakeX={impact(f, E.ghost.l)}>
        <Layer id={["af", "ghost", "keys", "fail"]}>
          {S.lane > 0.01 && <Runner d={LANE.d} width={40} draw={S.lane} />}
          {S.af > 0.01 && <Sprite name="af/front305" x={m.x} y={m.y + 60 * (1 - Math.min(1, S.af)) + id(1).y} w={m.w * (0.86 + 0.14 * S.afpop)} op={cl(S.af * 2)} rot={id(1).r} />}
          {S.gin > 0.01 && (
            <Sprite name="af/front305" x={m.x + gdx} y={gy + id(1).y} w={m.w} rot={grot + id(1).r} shadow={false}
                    op={cl(S.gin * 2) * pulse * 2} style={{filter: "grayscale(1) brightness(2.6) blur(1.5px)"}} />
          )}
          {S.miss > 0.01 && MISS.map(([dx, dy, r], k) => (
            <div key={k} style={{position: "absolute", left: m.x + dx * sc - 22 * sc, top: m.y + dy * sc, width: 44 * sc, height: 6, borderRadius: 3, background: C.red,
                                 transform: `rotate(${r}deg) scaleX(${cl(S.miss * 4 - k).toFixed(2)})`, opacity: 1 - 0.7 * S.shift}} />
          ))}
          {/* 芯片 + 环 */}
          {S.chip > 0.01 && <Sprite name="chip_chemistry42/34" x={mix(CHIP.x + 500, CHIP.x, S.chip)} y={CHIP.y - (S.chj || 0)} w={CHIP.w} op={cl(S.chip * 2)} />}
          {flow(KEYS, S.keys, 0.09)}
          {flow(FAILS, S.fails, 0.14)}
        </Layer>
        <Layer id="txt" exempt>
          <div style={{position: "absolute", left: 0, top: 0, opacity: cl(S.plate * 2), transform: `translateY(${(-80 * (1 - S.plate)).toFixed(1)}px)`}}>
            <Plate x={70} y={60} w={110} h={110} text="2" size={80} color={C.bone} id="step2" />
          </div>
          {/* R2-06：predicted 在模型左侧（右对齐，离模型 24 px），lab-measured 在模型右侧（左对齐，离模型 24 px），两块框不相交 */}
          <Label text="predicted model" size={60} x={AF.x - AF.w / 2 - 24} y={AF.y + 190} at={E.aflbl.l} out={E.once.s} align="right" on="af" />
          <Tag x={AF.x - AF.w / 2 - 24} y={AF.y + 266} align="right" op={cl((f - E.aflbl.l) / 10) * cl(1 - (f - E.once.s) / 10)} on="af">AlphaFold DB v6</Tag>
          <Tag x={AF.x + AF.w / 2 + 24} y={AF.y + 190} align="left" op={(f>=(K.words.find(w=>w.key==="structure#1")?.f0??E.once.l)?1:0) * (1 - cl(S.shift * 4))} on="af">lab-measured structure</Tag>
          <Pen text="not measured yet" x={AF.x + 230} y={250} at={E.q.s} out={E.shift.s} rot={-3} />
          <Pen text="failures too" x={660} y={660} at={E.fail.l} out={E.loop.s} rot={-3} />
          <Tag x={CHIP.x + 10} y={CHIP.y + 170} op={cl((f - E.loop.l) / 10)} on="chip">next round</Tag>
          <Source>{f < E.shift.s ? "Illustration · AlphaFold DB v6 prediction vs. a future lab structure" : "Illustration · design loop of Ren et al., Chem. Sci. 2023"}</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B703" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
