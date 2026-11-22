// HKBU SCIE1007 课程作业的科普视频：B 档 8-03（C 画外音）"And our second?"
// our second?：目标牌 2 落位，红色问号；These methods：目标牌缩到左上角，三块芯片（PandaOmics、Chemistry42、AlphaFold）依次落位，
// 候选插头在下面的料杆上快速走过（fast）；Screening by the millions：一大盘料珠，手写 millions；
// became thirteen molecules made：十三个插头依次掉进盘里，数字轮停在 13，标 molecules made；
// a road measured in years：一条长路带刻度，手写 years；the first hit came in 30 days：001 落在路的起点附近，标 30 days；
// round two made the key turn：048 插进小插座、拧 90°、红卡扣、灯灭（T7 一抖），左上角目标牌 2 打勾。
// 接点：开头 T2 从右甩进（8-02 是 B 页），结尾 T5 料杆擦除（8-04–07 出镜段）。L0 第 8 区大板。数字照旁白：thirteen、30 days、two。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_8-03.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, camBreath, Stage, Sprite, Slab, Runner, Label, Pen, Source, Counter, Engrave, Tick, Lamp, anchorOf, pathOf, evMapB, T5Out, whipX, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 8;

const GOAL0 = {x: 760, y: 280, w: 400, h: 330, fs: 270}, GOAL1 = {x: 70, y: 60, w: 170, h: 140, fs: 116};
const CHIPS = ["pandaomics", "chemistry42", "alphafold"];
const CHIP_X = [500, 960, 1420], CHIP_Y = 450, CHIP_W = 400;
const CONV_Y = 760;
// 十三个插头掉进盘（7 + 6）
const TRAY = {x: 1080, y: 470, w: 640, h: 230};
const SLOT = (i) => ({x: TRAY.x + 70 + (i < 7 ? i : i - 7 + 0.5) * 83, y: TRAY.y + (i < 7 ? 70 : 160)});
const ROAD_Y = 800, ROAD_X0 = 150, ROAD_X1 = 1770;
const SOCK = {x: 1240, y: 420, w: 400};
const PLUG_IN = 0.29;                           // 小插座正面图里插头端面的直径 / 插座宽

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("goal", 0, 1, E.goal.l);
    X.tw("badge", 0, 1, E.badge.s - 6, E.badge.l + 16, "power2.inOut");
    X.group(CHIPS.map((_, i) => `c${i}`), 0, 1, E.chips.l, {step: RULE.stagger * 2});
    X.tw("conv", 0, 1, E.conv.s, E.conv.s + 30, "power2.out");
    X.tw("clear1", 0, 1, E.pile.s - 6, E.pile.l + 10, "power3.in");
    X.land("pile", 0, 1, E.pile.l + 8);
    X.tw("tray", 0, 1, E.mil.l, E.mil.l + 30, "power2.out");
    [...Array(13)].forEach((_, i) => X.tw(`d${i}`, 0, 1, E.n13.l - 52 + i * 4 - 14, E.n13.l - 52 + i * 4 + 4, "power2.in"));
    [...Array(13)].forEach((_, i) => X.jiggle(`dj${i}`, E.n13.l - 52 + i * 4 + 4, 3, 0));
    X.count("n13", 0, 13, E.n13.l, 52);
    X.tw("clear2", 0, 1, E.road.s - 4, E.road.l + 16, "power3.in");
    X.tw("road", 0, 1, E.road.s + 6, E.road.e, "power2.out");
    X.tw("hop1", 0, 1, E.road.s + 10, E.hit.l, "power2.inOut");
    X.land("hit", 0, 1, E.hit.l);
    X.land("sock", 0, 1, E.road.l + 30, {antic: false});
    X.tw("r2", 0, 1, E.r2.s, E.r2.l, "power2.inOut");
    X.tw("twist", 0, 1, E.turn.s, E.turn.l, "power2.in");
    X.tw("tick", 0, 1, E.turn.l, E.turn.l + 20, "power2.out");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const whip = f < 7 ? whipX(f, 0, "in", -1) : 0;
  const shake = impact(f, E.turn.l);
  const g = {x: mix(GOAL0.x, GOAL1.x, S.badge), y: mix(GOAL0.y, GOAL1.y, S.badge), w: mix(GOAL0.w, GOAL1.w, S.badge), h: mix(GOAL0.h, GOAL1.h, S.badge),
             fs: mix(GOAL0.fs, GOAL1.fs, S.badge)};
  const c1 = -2000 * S.clear1 * S.clear1, c2 = -2000 * S.clear2 * S.clear2;
  // 料杆上走过的候选插头：每帧 15 px（每秒 0.47 个画面宽）
  const convX = (i) => ((f - E.conv.s) * 15 + i * 230) % (8 * 230) - 160;
  const convRim = (x) => Math.max(0, ...CHIP_X.map((cx) => 1 - Math.abs(x - cx) / 60));
  const pileBreath = 1 + 0.025 * Math.sin((2 * Math.PI * f) / 70);
  const T0 = SLOT(0), H1 = [ROAD_X0 + 110, ROAD_Y - 80];
  // 048：从右上飞到插座口，越飞越"远"（变小到插座口的尺寸），再拧 90°
  const mouth = (() => { const [dx, dy] = anchorOf("mini/mface_on", "mouth", SOCK.w); return [SOCK.x + dx, SOCK.y + dy]; })();
  const R2 = pathOf([[1760, 210], [1560, 200], mouth]);
  const rp = R2.at(S.r2);
  const plugW = mix(220, SOCK.w * PLUG_IN, S.r2);
  const clamped = f >= E.turn.l;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s3"])} whip={whip} shakeX={shake} shakeY={shake * 0.5} over={<T5Out name="runner" f={f} len={LEN} />}>
        <Layer id="goal">
          {S.goal > 0.01 && (
            <Slab x={g.x} y={g.y - 40 * (1 - Math.min(1, S.goal))} w={g.w} h={g.h} r={mix(34, 18, S.badge)} color={C.bone} depth={mix(12, 7, S.badge)} op={Math.min(1, S.goal * 1.5)}
                  sheen={S.badge > 0 && S.badge < 1 ? S.badge : -1} id="goal">
              <div style={{width: g.w, height: g.h, display: "flex", alignItems: "center", justifyContent: "center"}}><Engrave size={g.fs}>2</Engrave></div>
            </Slab>
          )}
          <Tick x={GOAL1.x + GOAL1.w + 50} y={GOAL1.y + 60} s={80} p={S.tick} sw={13} />
        </Layer>

        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${c1}px)`}}>
          <Layer id="chips">
            {CHIPS.map((n, i) => {
              const a = S[`c${i}`];
              return a > 0.01 && <Sprite key={i} name={`chip_${n}/34`} x={CHIP_X[i]} y={CHIP_Y - 40 * (1 - Math.min(1, a)) + id(1 + i).y} w={CHIP_W} op={Math.min(1, a * 1.6)} rot={id(1 + i).r} />;
            })}
          </Layer>
          <Layer id="conv">
            {S.conv > 0.001 && <Runner d={`M100,${CONV_Y} L1820,${CONV_Y}`} draw={S.conv} width={18} />}
            {S.conv > 0.5 && [...Array(8)].map((_, i) => {
              const x = convX(i), out = i % 3 === 1 && x > CHIP_X[1];
              return <Sprite key={i} name="plug/blank_34" x={x} y={CONV_Y - 46 + (out ? Math.min(60, (x - CHIP_X[1]) * 0.25) : 0)} w={120} op={Math.min(1, (S.conv - 0.5) * 3) * (out ? 0.55 : 1)}
                             rim={out ? 0 : convRim(x)} style={out ? {filter: "grayscale(0.9)"} : undefined} />;
            })}
          </Layer>
        </div>

        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${c2}px)`}}>
          <Layer id="pile">
            {S.pile > 0.01 && <Sprite name="beads/34" x={560} y={500 + id(5).y} w={700} op={Math.min(1, S.pile * 1.5)} sx={(0.85 + 0.15 * S.pile) * pileBreath} sy={(0.85 + 0.15 * S.pile) * (2 - pileBreath)} />}
          </Layer>
          <Layer id="tray">
            {S.tray > 0.01 && <Slab x={TRAY.x} y={TRAY.y} w={TRAY.w} h={TRAY.h} r={24} color={C.bone} depth={10} op={S.tray} id="tray" />}
            {[...Array(13)].map((_, i) => {
              const d = S[`d${i}`];
              if (d <= 0.001 || (i === 0 && S.hop1 > 0)) return null;
              const s = SLOT(i);
              // 从料珠堆顶上跳出来，划一道弧进盘
              return <Sprite key={i} name="plug/A_34" x={mix(640, s.x, Math.min(1, d * 1.1))} y={mix(380, s.y, d) - 220 * Math.sin(Math.PI * d) + (S[`dj${i}`] || 0)} w={80} lift={30 * (1 - d)} />;
            })}
          </Layer>
        </div>

        <Layer id="road">
          {S.road > 0.001 && <Runner d={`M${ROAD_X0},${ROAD_Y} L${ROAD_X1},${ROAD_Y}`} draw={S.road} width={20} />}
          {S.road > 0.3 && [...Array(17)].map((_, i) => {
            const x = ROAD_X0 + 30 + i * 98, a = Math.max(0, Math.min(1, (S.road * 1.2 - i / 17) * 3));
            return a > 0 && <Slab key={i} x={x - 3} y={ROAD_Y + 16} w={6} h={i % 4 === 0 ? 34 : 20} r={3} color={C.bone} depth={3} shadow={false} op={a} id={`rt${i}`} />;
          })}
          {S.hop1 > 0 && (() => {
            // 盘里第一个插头（001）跳到路的起点；路走的是年，001 只走了 30 天
            const u = S.hop1, sx = T0.x, sy = T0.y;   // 盘往左清场时 001 自己留下
            return <Sprite name="plug/001_34" x={mix(sx, H1[0], u)} y={mix(sy, H1[1], u) - 260 * Math.sin(Math.PI * u) + (u >= 1 ? id(6).y : 0)} w={mix(80, 220, u)} lift={30 * Math.sin(Math.PI * u)} />;
          })()}
        </Layer>

        <Layer id="socket">
          {S.sock > 0.01 && (
            <>
              <Sprite name={clamped ? "mini/mface_048clamp" : "mini/mface_on"} x={SOCK.x} y={SOCK.y + id(7).y - 40 * (1 - Math.min(1, S.sock))} w={SOCK.w}
                      op={Math.min(1, S.sock * 1.5)} />
              <Lamp name="mini/mface_on" x={SOCK.x} y={SOCK.y + id(7).y} w={SOCK.w} on={clamped ? 0 : Math.min(1, S.sock) * (0.8 + 0.2 * Math.sin((2 * Math.PI * f) / 36))} r={22} />
            </>
          )}
          {S.r2 > 0 && !clamped && <Sprite name="plug/048_end" x={rp[0]} y={rp[1] + id(7).y * S.r2} w={plugW} rot={90 * S.twist} lift={40 * (1 - S.r2)} shadow={S.r2 < 0.9} />}
        </Layer>

        <Layer id="txt" exempt>
          <Pen text="?" x={1190} y={200} at={E.q.l - 4} out={E.badge.s} size={220} color={C.red} rot={8} dur={24} />
          <Pen text="fast" x={1500 + c1} y={610} at={E.fast.l} out={E.pile.s} size={80} />
          <Pen text="millions" x={330 + c2} y={240} at={E.mil.l} size={80} />
          {S.n13 > 0.05 && (
            <div style={{position: "absolute", left: TRAY.x + 40 + c2, top: TRAY.y - 150}}>
              <Counter value={S.n13} digits={2} size={110} x={0} y={0} />
            </div>
          )}
          <Label text="molecules made" size={56} x={TRAY.x + 220 + c2} y={TRAY.y - 112} at={E.made.l} />
          <Pen text="years" x={1560} y={700} at={E.years.l - 4} size={80} />
          <Label text="30 days" size={56} x={ROAD_X0 + 110} y={ROAD_Y - 230} at={E.d30.l} align="center" />
          <Label text="round two" size={56} x={SOCK.x} y={SOCK.y - 250} at={E.r2.s} align="center" />
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B803" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
