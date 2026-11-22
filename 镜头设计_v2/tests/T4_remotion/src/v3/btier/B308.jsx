// HKBU SCIE1007 课程作业的科普视频：B 档 3-08（画外音）"But here's the problem. To design a key, you need to see the lock…"
// the problem：手写；To design a key：空插头落位（尖朝右）；see the lock：右边插座出现，磨砂看不清；no one had measured：插座更虚；CDK20's shape：红问号；
// That takes：插头、插座、问号往右退场；hard lab work：烧瓶和样本管落下，work 时烧瓶晃；only a small fraction：四十台磨砂小插座铺开；proteins：标签；
// have ever been measured：其中三台变清楚、灯亮，手写 measured；
// Without a 3D shape：清场，磨砂插座回来；computer predictions：一块黑芯片（不带牌子，标 computer）；of binding：插头去试，对不准，滑开；
// expensive：钞票；slow：日历；difficult：红问号 + 手写。
// 接点：开头 T2 从右甩进（3-07 是 B 页），结尾 T5 料杆擦除（3-09 出镜段）。L0 第 3 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_3-08.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Calendar1, camBreath, Stage, Sprite, Slab, Label, Pen, Engrave, Source, anchorOf, frost, evMapB, T5Out, whipX, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 3;

const PLUG = {x: 480, y: 560, w: 300};
const SOCK = {x: 1360, y: 520, w: 620};
const [mdx, mdy] = anchorOf("socket/hero_34", "mouth", SOCK.w);
const [tipOX, tipOY] = anchorOf("plug/blank_34", "tip", PLUG.w);   // 翻过来以后尖在 (x − tipOX, y + tipOY)
const FLASK = {x: 760, y: 500, w: 380};
const TUBE = {x: 1160, y: 580, w: 440};
const COLS = 8, ROWS = 5;
const GRID = [...Array(COLS * ROWS)].map((_, i) => ({x: 440 + (i % COLS) * 150, y: 220 + Math.floor(i / COLS) * 120}));
const CLEAR = [11, 22, 37];
const MINI_W = 124;
// 第 5 句：插座在右，芯片左上，插头在左
const SOCK2 = {x: 1380, y: 500, w: 600};
const [m2x, m2y] = anchorOf("socket/hero_34", "mouth", SOCK2.w);
const MOUTH2 = [SOCK2.x + m2x, SOCK2.y + m2y];
const PLUG2 = {x: 520, y: 640};

const mix = (a, b, t) => a + (b - a) * t;

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("plug", 0, 1, E.key.l, {antic: false});
    X.land("sock", 0, 1, E.lock.l, {antic: false});
    X.tw("blur", 0.5, 1, E.nobody.s - 4, E.nobody.e, "power2.out");
    X.tw("out1", 0, 1, E.takes.s - 6, E.takes.l + 20, "power2.in");
    X.land("flask", 0, 1, E.lab.l, {antic: false});
    X.land("tube", 0, 1, E.lab.l + 8, {antic: false});
    X.tw("work", 0, 1, E.work.s, E.work.e + 40, "none");
    X.tw("out2", 0, 1, E.grid.s - 8, E.grid.l + 10, "power3.in");
    X.group(GRID.map((_, i) => `g${i}`), 0, 1, E.grid.l, {step: 2, antic: false});
    X.tw("clr", 0, 1, E.meas.s, E.meas.l + 10, "power2.out");
    X.tw("out3", 0, 1, E.noshape.s - 8, E.noshape.l + 10, "power3.in");
    X.land("sock2", 0, 1, E.noshape.l + 6, {antic: false});
    X.land("plug2", 0, 1, E.noshape.l + 16, {antic: false});
    X.land("chip", 0, 1, E.comp.l, {antic: false});
    X.tw("try", 0, 1, E.bind.s, E.bind.l, "power2.in");
    X.tw("slip", 0, 1, E.bind.l, E.bind.e, "power2.out");
    X.tw("shrink", 0, 1, E.exp.s - 8, E.exp.l + 10, "power2.inOut");
    X.land("bill", 0, 1, E.exp.l + 4, {antic: false});
    X.land("cal", 0, 1, E.slow.l, {antic: false});
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const whip = f < 7 ? whipX(f, 0, "in", -1) : 0;
  const o1 = 2200 * S.out1, o2 = -2200 * S.out2, o3 = -2200 * S.out3;
  const shake = impact(f, E.bind.l);
  // 第 5 句收到左边、缩小，给 expensive / slow / difficult 让位
  const g5 = {s: mix(1, 0.62, S.shrink), x: mix(0, -330, S.shrink), y: mix(0, 40, S.shrink)};

  // 插头试插：尖从起点去插孔，差一点，碰到边沿滑下去
  const tip0 = [PLUG2.x - tipOX, PLUG2.y + tipOY];
  const miss = [MOUTH2[0] - 40, MOUTH2[1] + 70];
  const tipX = mix(tip0[0], miss[0], S.try) + 40 * S.slip;
  const tipY = mix(tip0[1], miss[1], S.try) + 150 * S.slip - 60 * Math.sin(Math.PI * S.try);
  const pRot = 20 * S.slip;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, [])} whip={whip} shakeX={shake} over={<T5Out name="runner" f={f} len={LEN} />}>
        {/* 第 1–3 句：插头和磨砂插座 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${o1}px)`}}>
          <Layer id="plug">
            {S.plug > 0.01 && S.out1 < 1 && <Sprite name="plug/blank_34" x={PLUG.x} y={PLUG.y - 40 * (1 - Math.min(1, S.plug)) + id(1).y} w={PLUG.w} sx={-1} op={Math.min(1, S.plug * 1.5)} rot={id(1).r} />}
          </Layer>
          <Layer id="socket">
            {S.sock > 0.01 && S.out1 < 1 && (
              <Sprite name="socket/hero_34" x={SOCK.x} y={SOCK.y - 40 * (1 - Math.min(1, S.sock)) + id(2).y} w={SOCK.w * (1 - 0.05 * (S.blur - 0.5))}
                      op={Math.min(1, S.sock * 1.5)} style={frost(S.blur)} />
            )}
          </Layer>
          <Layer id="txt1" exempt>
            <Pen text="the problem" x={760} y={150} at={E.prob.s - 6} out={E.key.s} size={92} />
            <Pen text="?" x={SOCK.x + mdx + 90} y={SOCK.y + mdy - 330} at={E.q.s - 8} dur={30} size={200} color={C.red} rot={6} />
          </Layer>
        </div>

        {/* 第 4 句：实验室，再是四十台小插座 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${o2}px)`}}>
          <Layer id="lab">
            {S.flask > 0.01 && <Sprite name="flask/34" x={FLASK.x} y={FLASK.y - 60 * (1 - Math.min(1, S.flask))} w={FLASK.w} op={Math.min(1, S.flask * 1.5)}
                                       rot={6 * Math.sin(2 * Math.PI * 3 * S.work) * (1 - S.work) + id(3).r} />}
            {S.tube > 0.01 && <Sprite name="tube/34" x={TUBE.x} y={TUBE.y - 60 * (1 - Math.min(1, S.tube)) + id(4).y} w={TUBE.w} op={Math.min(1, S.tube * 1.5)} rot={id(4).r} />}
          </Layer>
        </div>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${o3}px)`}}>
          <Layer id="grid">
            {GRID.map((g, i) => {
              const a = S[`g${i}`];
              if (a <= 0.01) return null;
              const on = CLEAR.includes(i) ? S.clr : 0;
              const y = g.y - 30 * (1 - Math.min(1, a)) + id(10 + i).y;
              return (
                <React.Fragment key={i}>
                  <Sprite name="mini/mface_off" x={g.x} y={y} w={MINI_W} op={Math.min(1, a * 1.5) * (1 - on)} style={frost(1 - on)} shadow={on < 0.5} />
                  {on > 0.01 && <Sprite name="mini/mface_on" x={g.x} y={y - 6 * on} w={MINI_W} op={on} lift={6 * on} />}
                </React.Fragment>
              );
            })}
          </Layer>
          <Layer id="txt4" exempt>
            <Label text="proteins" size={56} x={960} y={790} at={E.prot.l} align="center" />
            <Pen text="measured" x={1640} y={300} at={E.meas.s} size={72} />
          </Layer>
        </div>

        {/* 第 5 句 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translate(${g5.x}px, ${g5.y}px) scale(${g5.s})`, transformOrigin: "0px 540px"}}>
          <Layer id="socket">
            {S.sock2 > 0.01 && <Sprite name="socket/hero_34" x={SOCK2.x} y={SOCK2.y - 40 * (1 - Math.min(1, S.sock2)) + id(5).y} w={SOCK2.w} op={Math.min(1, S.sock2 * 1.5)} style={frost(0.85)} />}
          </Layer>
          <Layer id="chip">
            {S.chip > 0.01 && S.shrink < 1 && (
              <Slab x={330} y={210 - 40 * (1 - Math.min(1, S.chip)) + id(6).y} w={300} h={190} r={18} color={C.black} depth={16} op={Math.min(1, S.chip * 1.5) * (1 - S.shrink)} id="chipslab">
                <div style={{position: "absolute", left: 0, top: 0, width: 300, height: 190, display: "flex", alignItems: "center", justifyContent: "center"}}><Engrave size={48} light>computer</Engrave></div>
              </Slab>
            )}
          </Layer>
          <Layer id="plug2">
            {S.plug2 > 0.01 && <Sprite name="plug/blank_34" x={tipX + tipOX} y={tipY - tipOY - 40 * (1 - Math.min(1, S.plug2)) + id(7).y} w={PLUG.w} sx={-1} rot={pRot + id(7).r}
                                       op={Math.min(1, S.plug2 * 1.5)} lift={20 * Math.sin(Math.PI * S.try)} />}
          </Layer>
        </div>

        <Layer id="cost">
          {S.bill > 0.01 && <Sprite name="bill/34" x={1190} y={360 - 50 * (1 - Math.min(1, S.bill)) + id(8).y} w={380} op={Math.min(1, S.bill * 1.5)} rot={-4 + id(8).r} />}
          {S.cal > 0.01 && <Calendar1 x={1560} y={360 - 50 * (1 - Math.min(1, S.cal)) + id(9).y} w={380} op={Math.min(1, S.cal * 1.5)} rot={id(9).r} />}
        </Layer>
        <Layer id="txt5" exempt>
          <Label text="expensive" size={52} x={1190} y={520} at={E.exp.l} align="center" />
          <Label text="slow" size={52} x={1560} y={520} at={E.slow.l} align="center" />
          <Pen text="?" x={1330} y={600} at={E.diff.s - 8} dur={24} size={170} color={C.red} rot={6} />
          <Pen text="difficult" x={1420} y={680} at={E.diff.s} dur={30} size={80} />
          <Source>Illustration · data: Wang et al., Pharmaceuticals 2023; Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B308" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
