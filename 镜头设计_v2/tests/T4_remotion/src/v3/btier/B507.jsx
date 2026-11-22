// HKBU SCIE1007 课程作业的科普视频：B 档 5-07（C 画外音）"Not at all. This is where the loop kicks in again, now with real lab data inside…"
// s1 Not at all：手写。s2 the loop：设计循环圈落下；kicks in again：一颗亮珠沿圈跑起来；now with：圈亮一下；real lab data：左边烧瓶落下；inside：烧瓶里的数据珠倒进圈里。
// s3 The results went back in：数据珠沿圈走；a predicted pose：圈收到左上，右边小插座插着 001；001：标 001；sat in the pocket：插头往里一推、灯亮。
// s4 Sixteen new designs：十六个新插头两排落下，数字轮 16。s5 Six made and tested：六个跳进烧瓶，其余变灰。
// s6 within 30 days：日历落下，数字轮停 30；that first hit：001 打勾。
// 接点：开头 T5 料杆擦除（上一段 5-05+06 是出镜段），结尾 T2 往左甩（下一段 5-08 是 B 页）。L0 第 5 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_5-07.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Calendar1, camBreath, shade, tint, Stage, Sprite, Label, Pen, Source, Counter, Engrave, Tick, Lamp, pathOf, evMapB, T5In, whipX} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 5;

const LOOP = {x: 960, y: 450, w: 560};
const RING_R = 70;                                // 圈上箭头那一环的半径（显示像素）
const FLASK = {x: 380, y: 470, w: 300};
const POUR = pathOf([[FLASK.x + 10, FLASK.y - 200], [620, 230], [820, 300], [LOOP.x, LOOP.y]]);
const MINI = {x: 1300, y: 470, w: 470};
const NAMES = ["A", "B", "C", "D", "E", "F"];
const NEW = [...Array(16)].map((_, i) => [520 + (i % 8) * 125, 380 + Math.floor(i / 8) * 150]);
const SIX = [1, 3, 6, 9, 12, 14];
const FLASK2 = {x: 1640, y: 470, w: 300};
const CAL = {x: 720, y: 420, w: 440};
const HIT = {x: 1320, y: 450, w: 380};

const clamp01 = (v) => Math.max(0, Math.min(1, v));
const mix = (a, b, t) => a + (b - a) * t;
const sm = (t) => { const x = clamp01(t); return x * x * (3 - 2 * x); };

const Dot = ({x, y, r = 11, op = 1, fill}) => (
  <g opacity={op}>
    <circle cx={x} cy={y} r={r} fill={fill || C.blue} />
    <circle cx={x - r * 0.3} cy={y - r * 0.35} r={r * 0.32} fill="#fff" opacity={0.7} />
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("loop", 0, 1, E.loop.l, {antic: false});
    X.tw("kick", 0, 1, E.kick.s, E.kick.l, "power2.out");
    X.tw("now", 0, 1, E.now.s, E.now.e, "none");
    X.land("flask", 0, 1, E.data.l, {antic: false});
    X.tw("pour", 0, 1, E.inside.s, E.inside.e, "none");
    X.tw("res", 0, 1, E.results.s, E.results.e, "power1.inOut");
    X.tw("aside", 0, 1, E.pose.s - 16, E.pose.l + 10, "power2.inOut");
    X.land("mini", 0, 1, E.pose.l, {antic: false});
    X.tw("push", 0, 1, E.pocket.s, E.pocket.l, "power2.in");
    X.jiggle("pushJ", E.pocket.l, 4, 0);
    X.tw("clear1", 0, 1, E.n16.s - 10, E.n16.l + 10, "power1.in");
    X.tw("new", 0, 1, E.n16.s, E.n16.s + 40, "none");
    S.n16 = 0;
    X.count("n16", 0, 16, E.n16.l + 16, 22, "power2.out");
    X.land("flask2", 0, 1, E.six.l - 4, {antic: false});
    X.tw("six", 0, 1, E.six.s, E.six.e, "power2.inOut");
    X.tw("clear2", 0, 1, E.d30.s - 10, E.d30.s + 30, "power1.in");
    X.land("cal", 0, 1, E.d30.s + 7, {antic: false});
    S.n30 = 0;
    X.count("n30", 0, 30, E.d30.l, 40, "power2.out");
    X.land("p001", 0, 1, E.d30.l + 30, {antic: false});
    X.tw("tick", 0, 1, E.hit.s, E.hit.l + 14, "power2.out");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const whip = whipX(f, LEN - 7, "out", -1);
  const a = S.aside, c1 = S.clear1, c2 = S.clear2;
  // 圈：s3 收到左上（0.55 倍），s4 出画
  const lp = {x: mix(LOOP.x, 420, a) - 1400 * sm(c1 * 1.2), y: mix(LOOP.y, 300, a), s: mix(1, 0.55, a)};
  const ringC = [lp.x, lp.y + 6];
  const orbit = (u, r = RING_R) => [ringC[0] + r * lp.s * Math.cos(2 * Math.PI * u - Math.PI / 2), ringC[1] + r * lp.s * Math.sin(2 * Math.PI * u - Math.PI / 2) * 0.62];
  const flash = Math.sin(Math.PI * clamp01(S.now * 2));

  // 亮珠：kick 之后一直绕圈
  const runU = S.kick > 0 ? ((f - E.kick.s) / 90) % 1 : 0;
  // 数据珠：倒进圈（pour），再沿圈走（res）
  const data = [...Array(8)].map((_, k) => {
    const u = clamp01(S.pour * 1.7 - k * 0.09);
    let p = POUR.at(sm(u));
    let op = clamp01(u * 8);
    if (S.res > 0) {
      const o = orbit(k / 8 + S.res * 1.5);
      const t = sm(S.res * 3);
      p = [mix(p[0], o[0], t), mix(p[1], o[1], t)];
    }
    if (a > 0) { const o = orbit(k / 8 + 1.5); p = [o[0], o[1]]; }
    op *= 1 - sm(c1 * 2);
    return {x: p[0], y: p[1], op};
  });

  const newP = NEW.map((p, i) => {
    const v = sm((S.new * 40 - i * 2) / 8);
    let x = p[0], y = p[1] - 40 * (1 - v), op = v, rot = 0, dim = 0;
    const k = SIX.indexOf(i);
    if (k >= 0 && S.six > 0) {
      const u = sm(S.six * 1.4 - k * 0.08);
      x = mix(x, FLASK2.x - 10, u); y = mix(y, FLASK2.y - 140, u) - 160 * Math.sin(Math.PI * u); op *= 1 - sm((u - 0.85) * 7); rot = 160 * u;
    } else dim = S.six;
    op *= 1 - sm(c2 * 1.5);
    return {i, x: x - 300 * sm(c2 * 1.2) * 0, y, op, rot, dim, n: NAMES[i % 6]};
  });

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, [])} whip={whip} over={<T5In name="runner" f={f} />}>
        <Layer id="loop">
          {S.loop > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translate(${lp.x}px, ${lp.y}px) scale(${lp.s}) translate(${-lp.x}px, ${-lp.y}px)`}}>
              <Sprite name="loop/34" x={lp.x} y={lp.y - 50 * (1 - Math.min(1, S.loop)) + id(1).y} w={LOOP.w} op={Math.min(1, S.loop * 1.5)} rot={id(1).r} rim={flash} />
            </div>
          )}
          {S.kick > 0.01 && c1 < 1 && (
            <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
              {[0, 0.04, 0.08].map((d, k) => { const p = orbit(runU - d, RING_R + 2); return <circle key={k} cx={p[0]} cy={p[1]} r={(12 - 3 * k) * lp.s} fill={C.bone} opacity={(0.95 - 0.3 * k) * clamp01(S.kick * 3) * (1 - c1)} />; })}
              {data.map((d, k) => d.op > 0.01 && <Dot key={k} x={d.x} y={d.y} r={11 * (a > 0 ? lp.s + 0.2 : 1)} op={d.op} fill={k % 3 === 2 ? C.red : C.blue} />)}
            </svg>
          )}
        </Layer>
        <Layer id="flask">
          {S.flask > 0.01 && <Sprite name="flask/34" x={FLASK.x - 900 * a} y={FLASK.y - 50 * (1 - Math.min(1, S.flask)) + id(2).y} w={FLASK.w} op={Math.min(1, S.flask * 1.5)}
                                     rot={-14 * Math.sin(Math.PI * clamp01(S.pour * 1.3)) + id(2).r} />}
        </Layer>
        <Layer id="pose">
          {S.mini > 0.01 && c1 < 1 && (
            <>
              <Sprite name="mini/m34_001" x={MINI.x - 1500 * sm(c1 * 1.2) + 10 * S.push * (1 - S.push) * 4} y={MINI.y - 50 * (1 - Math.min(1, S.mini)) + id(3).y + (S.pushJ || 0)} w={MINI.w}
                      op={Math.min(1, S.mini * 1.5)} rot={id(3).r} />
              <Lamp name="mini/m34_001" x={MINI.x - 1500 * sm(c1 * 1.2)} y={MINI.y + id(3).y} w={MINI.w} on={S.push} />
            </>
          )}
        </Layer>
        <Layer id="new">
          {newP.map((p) => p.op > 0.01 && (
            <Sprite key={p.i} name={`plug/${p.n}_34`} x={p.x} y={p.y + id(10 + p.i).y} w={110} sx={-1} rot={p.rot + id(10 + p.i).r} op={p.op * (1 - 0.4 * p.dim)}
                    style={p.dim > 0.01 ? {filter: `grayscale(${p.dim})`} : undefined} />
          ))}
          {S.flask2 > 0.01 && c2 < 1 && <Sprite name="flask/34" x={FLASK2.x} y={FLASK2.y - 50 * (1 - Math.min(1, S.flask2)) + id(4).y} w={FLASK2.w} op={Math.min(1, S.flask2 * 1.5) * (1 - sm(c2 * 1.5))} rot={id(4).r} />}
        </Layer>
        <Layer id="cal">
          {S.cal > 0.01 && <Calendar1 x={CAL.x} y={CAL.y - 50 * (1 - Math.min(1, S.cal)) + id(5).y} w={CAL.w} op={Math.min(1, S.cal * 1.5)} rot={id(5).r} />}
          {S.p001 > 0.01 && <Sprite name="plug/001_34" x={HIT.x} y={HIT.y - 50 * (1 - Math.min(1, S.p001)) + id(6).y} w={HIT.w} sx={-1} op={Math.min(1, S.p001 * 1.5)} rot={id(6).r} />}
          {S.tick > 0.01 && <Tick x={HIT.x + 230} y={HIT.y - 120} s={110} p={S.tick} sw={14} />}
        </Layer>

        <Layer id="txt" exempt>
          <Pen text="Not at all." x={720} y={420} at={E.not.s} out={E.loop.s} dur={26} size={110} />
          <Label text="lab data" size={52} x={FLASK.x} y={690} at={E.data.l + 6} out={E.results.s} align="center" />
          <Label text="predicted pose" size={52} x={MINI.x} y={740} at={E.pose.l + 4} out={E.n16.s} align="center" />
          <Label text="001" size={64} x={MINI.x + 210} y={250} at={E.p001.l} out={E.n16.s} align="center" />
          {S.n16 > 0.05 && c2 < 1 && (
            <div style={{position: "absolute", left: 960, top: 130, opacity: 1 - sm(c2 * 1.5), display: "flex", alignItems: "baseline"}}>
              <Counter value={S.n16} digits={2} size={110} x={0} y={0} align="center" />
            </div>
          )}
          <Label text="new designs" size={52} x={960} y={270} at={E.n16.l + 30} out={E.six.s} align="center" />
          <Label text="made and tested" size={52} x={FLASK2.x - 40} y={700} at={E.six.l + 10} out={E.d30.s} align="center" />
          {S.n30 > 0.05 && (
            <div style={{position: "absolute", left: CAL.x - 90, top: 610}}>
              <Counter value={S.n30} digits={2} size={96} x={0} y={0} />
              <div style={{position: "absolute", left: 120, top: 34, opacity: clamp01((f - E.d30.l) / 12)}}><Engrave size={56}>days</Engrave></div>
            </div>
          )}
          <Label text="first hit" size={52} x={HIT.x} y={650} at={E.hit.l} align="center" />
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B507" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
