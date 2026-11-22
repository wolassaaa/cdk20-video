// HKBU SCIE1007 课程作业的科普视频：B 档 5-03（C 画外音）"001's Kd: 9.2 micromolar."
// Kd 横尺（左低右高；越往左抓得越紧）：001 的分子（我们自己的重对接图，标 OUR RE-DOCKING）和金插头，插头沿尺走到 9.2，数字轮停在 9.2 µM；
// The other six：右上角六个插头依次落位（A–F 只是画面代号）；All above 30：30 的立柱升起，六个插头落到 30 右边；Much weaker：六个变灰往下沉；
// wild part：尺往左滑走，001 留下，日历落下（T7）；30 days：数字轮停在 30；
// from picking the target：PandaOmics 芯片弹出一个小插座（CDK20 被选为靶），沿路走到 001；first confirmed hit：打勾。
// 接点：开头 T5 料杆擦除（5-02 出镜段），结尾 T5 插座擦除（5-04 是 A 段插座）。L0 第 5 区大板。数字照旁白：9.2、30、30 days。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_5-03.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Calendar1, SERIF, Tag, camBreath, Stage, Sprite, Slab, Gate, Runner, Label, Pen, Source, Counter, Engrave, Tick, anchorOf, pathOf, evMapB, T5In, T5Out, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 5;

const RAIL_Y = 700;
const X = (v) => 300 + v * 22;                  // 0–60 µM → x 300–1620
const SIX = ["A", "B", "C", "D", "E", "F"];
const SIX_V = [34, 38, 43, 48, 53, 58];         // 示意位置：都在 30 右边（论文只说都 > 30 µM）
const SIX_W = 170;
const tipDX = (n, w) => -anchorOf(`plug/${n}_34`, "tip", w)[0];
const HIT = {x: 1560, y: 620, w: 320}, ROAD_Y = 770, CHIP = {x: 340, y: 600, w: 420};
const DOCK = {x: HIT.x - 150, y: 590, w: 300};
const TRAVEL = pathOf([[CHIP.x, 400], [700, 470], [1100, 540], [HIT.x - 260, 600]]);

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X_) => {
    X_.tw("mol", 0, 1, E.mol.s, E.mol.l + 16, "power2.out");
    X_.count("k", 0, 9.2, E.p001.l, 46);
    X_.tw("rail", 0, 1, E.mol.s + 4, E.mol.s + 40, "power2.out");
    X_.tw("um", 0, 1, E.um.s, E.um.l + 6, "power2.out");
    X_.group(SIX.map((_, i) => `s${i}`), 0, 1, E.six.l - 10, {step: RULE.stagger});
    X_.land("post", 0, 1, E.post.l);
    SIX.forEach((_, i) => X_.tw(`d${i}`, 0, 1, E.drop.s + i * 4, E.drop.l + i * 4, "back.out(1.4)"));
    X_.tw("weak", 0, 1, E.weak.s, E.weak.l + 10, "power2.inOut");
    X_.tw("clear", 0, 1, E.clear.s, E.clear.e, "power3.in");
    X_.tw("go", 0, 1, E.clear.s, E.wild.l, "power3.inOut");
    X_.land("cal", 0, 1, E.wild.l, {antic: false});
    X_.jiggle("calJ", E.clock.l, 6, 0);
    X_.tw("road", 0, 1, E.clock.s, E.clock.e, "power2.out");
    X_.land("chip", 0, 1, E.clock.l + 10);
    X_.count("n30", 0, 30, E.n30.l, 60);
    X_.tw("days", 0, 1, E.n30.l + 10, E.n30.l + 24, "power2.out");
    X_.land("pick", 0, 1, E.pick.l);
    X_.tw("travel", 0, 1, E.travel.s, E.travel.l - 4, "power2.inOut");
    X_.tw("tick", 0, 1, E.hit.l, E.hit.l + 24, "power2.out");
    X_.jiggle("hitJ", E.hit.l, 4, 0);
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const clearX = -2000 * S.clear * S.clear;
  const shake = impact(f, E.wild.l) + impact(f, E.hit.l - 1);

  // 001：尺上 9.2 → 去右边当命中
  const p001 = {x: mix(X(S.k) + tipDX("001", 260), HIT.x, S.go), y: mix(610, HIT.y, S.go) + (S.hitJ || 0), w: mix(260, HIT.w, S.go)};
  const tr = TRAVEL.at(S.travel);
  const docked = f >= E.hit.l - 1;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2", "s5"])} shakeX={shake} shakeY={shake * 0.5}
             over={<><T5In name="runner" f={f} /><T5Out name="socket" f={f} len={LEN} /></>}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${clearX}px)`}}>
          <Layer id="mol">
            {S.mol > 0.01 && <Sprite name="mol001/34" x={560} y={310 + id(1).y} w={480} op={S.mol} rot={id(1).r} />}
          </Layer>
          <Layer id="rail">
            <Runner d={`M240,${RAIL_Y} L1700,${RAIL_Y}`} draw={S.rail} width={18} />
            {S.rail > 0.6 && [0, 10, 20, 30, 40, 50, 60].map((v) => (
              <Slab key={v} x={X(v) - 3} y={RAIL_Y + 14} w={6} h={v % 30 === 0 ? 30 : 18} r={3} color={C.bone} depth={3} shadow={false} op={Math.min(1, (S.rail - 0.6) * 3)} id={`tk${v}`} />
            ))}
            {S.post > 0.01 && (
              <>
                <Slab x={X(30) - 11} y={RAIL_Y - 250 * Math.min(1.05, S.post)} w={22} h={250 * Math.min(1.05, S.post)} r={8} color={C.bone} depth={6} id="post" />
                <Slab x={X(30) - 80} y={RAIL_Y - 250 * Math.min(1.05, S.post) - 70} w={160} h={62} r={14} color={C.bone} depth={8} op={Math.min(1, S.post)} id="post30">
                  <div style={{width: 160, height: 62, display: "flex", alignItems: "center", justifyContent: "center"}}><Engrave size={48}>30 µM</Engrave></div>
                </Slab>
              </>
            )}
          </Layer>
          <Layer id="six">
            {SIX.map((n, i) => {
              const a = S[`s${i}`];
              if (a <= 0.01) return null;
              const d = S[`d${i}`];
              const tier = i % 2 ? 480 : 610;
              const x = mix(1270 + (i % 3) * 190, X(SIX_V[i]) + tipDX(n, SIX_W), d);
              const y = mix(i < 3 ? 210 : 330, tier, d) - 40 * (1 - Math.min(1, a)) + 16 * S.weak + id(10 + i).y;
              const g = S.weak;
              return (
                <React.Fragment key={i}>
                  {d > 0.9 && <Gate x1={X(SIX_V[i])} y1={RAIL_Y} x2={X(SIX_V[i])} y2={tier + 16 * S.weak + 20} w={10} />}
                  <Sprite name={`plug/${n}_34`} x={x} y={y} w={SIX_W} op={Math.min(1, a * 1.6) * (1 - 0.25 * g)} rot={id(10 + i).r + 6 * g}
                          style={{filter: g > 0.01 ? `grayscale(${0.85 * g})` : undefined}} />
                </React.Fragment>
              );
            })}
          </Layer>
        </div>

        <Layer id="p001">
          {S.mol > 0.01 && <Gate x1={p001.x - tipDX("001", p001.w)} y1={mix(RAIL_Y, ROAD_Y, S.go)} x2={p001.x - tipDX("001", p001.w)} y2={p001.y + 30} w={12} />}
          {S.mol > 0.01 && !docked && <Sprite name="plug/001_34" x={p001.x} y={p001.y + id(2).y} w={p001.w} op={S.mol} rot={id(2).r} />}
          {docked && <Sprite name="mini/m34_001" x={DOCK.x} y={DOCK.y + id(2).y + (S.hitJ || 0)} w={DOCK.w} rot={id(2).r} />}
        </Layer>

        <Layer id="cal">
          {S.cal > 0.01 && <Calendar1 x={900} y={mix(-260, 290, Math.min(1, S.cal)) + (S.calJ || 0) * -1 + id(3).y} w={440} rot={id(3).r} />}
        </Layer>

        <Layer id="road">
          {S.road > 0.001 && <Runner d={`M${CHIP.x},${ROAD_Y} L${HIT.x},${ROAD_Y}`} draw={S.road} width={18} />}
          {S.chip > 0.01 && <Sprite name="chip_pandaomics/34" x={CHIP.x} y={CHIP.y - 30 * (1 - Math.min(1, S.chip)) + id(4).y} w={CHIP.w} op={Math.min(1, S.chip * 1.5)} />}
          {S.pick > 0.01 && S.travel <= 0 && <Sprite name="mini/m34_on" x={CHIP.x} y={mix(CHIP.y, 400, S.pick)} w={160 * Math.min(1, S.pick)} lift={10} />}
        </Layer>
        <Layer id="hit">
          {S.travel > 0 && !docked && <Sprite name="mini/m34_on" x={tr[0]} y={tr[1]} w={160} lift={20 * Math.sin(Math.PI * S.travel)} />}
          <Tick x={HIT.x + 60} y={440} s={90} p={S.tick} sw={13} />
        </Layer>

        <Layer id="txt" exempt>
          {S.mol > 0.01 && (
            <Tag x={560 + clearX} y={96} op={S.mol}>OUR RE-DOCKING (AutoDock Vina)</Tag>
          )}
          {S.k > 0.05 && (
            <div style={{position: "absolute", left: 830 + clearX, top: 170}}>
              <Counter value={S.k} digits={1} decimals={1} size={120} x={0} y={0} />
              <div style={{position: "absolute", left: 172, top: 50, opacity: S.um, transform: `translateY(${(1 - S.um) * 12}px)`}}><Engrave size={64}>µM</Engrave></div>
            </div>
          )}
          <Pen text="much weaker" x={1180 + clearX} y={780} at={E.weak.l - 6} size={64} />
          {S.n30 > 0.05 && (
            <div style={{position: "absolute", left: 1150, top: 200}}>
              <Counter value={S.n30} digits={2} size={120} x={0} y={0} />
              <div style={{position: "absolute", left: 132, top: 50, opacity: S.days, transform: `translateY(${(1 - S.days) * 12}px)`}}><Engrave size={64}>days</Engrave></div>
            </div>
          )}
          <Label text="target" size={52} x={CHIP.x} y={808} at={E.target.l} align="center" />
          <Label text="first confirmed hit" size={52} x={HIT.x - 120} y={808} at={E.hit.l - 34} align="center" />
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B503" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
