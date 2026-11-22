// HKBU SCIE1007 课程作业的科普视频：B 档 5-10（C 画外音）"Then, the big step: living cells."
// 路上三站（小插座 = 抓力测过、烧瓶 = 酶测过、第三站空着），048 插头一大步跳到第三站，第三站长出培养皿；
// 皿移到画面中间当 Huh7 皿：日历翻三下，048 插进皿里，皿里的细胞插满 CDK20 小插座，信号表掉一半，剂量条滚到 210 nM；
// HEK293 皿从右边进来，048 也插进去，它的剂量条长到 1,700 nM；八段 Huh7 的长度铺满 HEK 的条（≈ 8×）。
// 接点：开头 T5 插座擦除（上一段 W4 是 A 段），结尾 T2 往左甩（下一段 6-01 是 B 页）。L0 用第 5 区大板。
// 时间全读 keys_5-10.json（事件表由 映射/b_events.py 生成）。数字照旁白：210、1,700、eight times。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_5-10.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Calendar1, camBreath, Stage, Sprite, Slab, Gate, Runner, Label, Pen, Source, Counter, Tick, Engrave, pathOf, evMapB, T5In, whipX, shade} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 5;

// ---- 布局（1920×1080，y > 940 留给字幕，出处行在 892）
const RUN_Y = 720;                                   // 第一幕的料杆
const ST = [320, 830, 1600];                         // 三站中心 x
const HOP = pathOf([[1000, 676], [1165, 470], [1330, 676]]);       // 048 一大步
const SOLO = [670, 440], LEFT = [390, 440], RIGHT = [1310, 440], OFF_R = [2350, 440];
const DISH_W = 470;
// 皿里细胞上的小插座（相对皿中心），9 个，4 个会变灰（失去信号的一半）
const ICONS = [[-120, -40], [-40, -78], [52, -60], [-150, 32], [-62, 14], [30, 22], [118, 6], [-80, 84], [24, 92]];
const DIM = [1, 4, 6, 7];
const HEK_ICONS = [2, 4, 7];                          // HEK293：CDK20 少得多（Gemini 初审：对照皿里插座和 Huh7 一样多，看不出区别）
const IN_DX = 40, IN_DY = -30;                        // 048 落进皿里液面的位置（相对皿中心），不卡在皿沿
const BAR_X = 260, NM = 0.72, ROW1 = 744, ROW2 = 806, BAR_H = 26;   // 剂量条：1 nM = 0.72 px，1,700 → 1,224 px（审查批 1："1,700 nM" 整个标签右沿 ≤ x 1700，210 那条同比例）
const GAUGE = {dx: 290, top: -170, h: 360, w: 60};                  // 信号表（相对皿中心）

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    // 第一幕：路
    X.tw("road", 0, 1, E.road.s, E.road.s + 60, "power2.out");
    X.group(["st0", "st1"], 0, 1, E.road.s + 24, {step: RULE.stagger * 3});
    X.tw("tick0", 0, 1, E.road.s + 34, E.road.s + 58, "power2.inOut");
    X.tw("tick1", 0, 1, E.road.s + 46, E.road.s + 70, "power2.inOut");
    X.tw("plugIn", 0, 1, E.road.s + 30, E.road.s + 52, "power2.out");
    X.tw("hop", 0, 1, E.hop.s, E.hop.l, "power2.inOut");
    X.jiggle("hopJ", E.hop.l, 3);
    X.land("dish", 0, 1, E.cells.l);
    // 换场：路往左滑走，第三站的皿移到中间
    X.tw("shift", 0, 1, E.shift.s - 4, E.shift.s + 66, "power2.inOut");
    X.land("cal", 0, 1, E.cal.s + RULE.cross + RULE.antic);
    ["calB0", "calB1", "calB2"].forEach((k, i) => X.jiggle(k, E.cal.l + [-6, 4, 14][i], 8, 0));
    // 048 插进 Huh7 皿
    X.tw("dose", 0, 1, E.dose.s, E.dose.l, "power2.inOut");
    X.jiggle("doseJ", E.dose.l, 3);
    X.group(ICONS.map((_, i) => `ic${i}`), 0, 1, E.packed.l, {step: 7, antic: false});
    // 信号掉一半：细胞一半变灰
    X.land("gauge", 0, 1, E.lost.l, {antic: false});
    X.tw("g1", 1, 0.5, E.lost.l, E.half.l, "power2.inOut");
    DIM.forEach((d, i) => X.tw(`dim${d}`, 0, 1, E.lost.l + i * 12, E.lost.l + i * 12 + 20, "power2.inOut"));
    // 剂量条 210
    X.tw("rail", 0, 1, E.d210.s, E.d210.s + 30, "power2.out");
    X.count("n210", 0, 210, E.d210.l, 60);
    X.tw("calOut", 0, 1, E.dose.s, E.dose.s + 30, "power2.in");
    X.tw("nm1", 0, 1, E.nm.s, E.nm.l, "power2.out");
    // 对照：Huh7 往左让，HEK293 从右边进来
    X.tw("cmp", 0, 1, E.hek.s, E.hek.l, "power3.inOut");
    X.tw("dose2", 0, 1, E.hneed.s - 6, E.hneed.l, "power2.inOut");
    X.jiggle("dose2J", E.hneed.l, 3);
    X.tw("g2", 1, 0.5, E.hneed.l, E.hneed.e + 20, "power2.inOut");
    DIM.forEach((d, i) => X.tw(`dimH${d}`, 0, 1, E.hneed.l + i * 8, E.hneed.l + i * 8 + 20, "power2.inOut"));
    X.count("n1700", 0, 1700, E.d1700.l, 90);
    X.tw("nm2", 0, 1, E.d1700.l + 6, E.d1700.l + 22, "power2.out");
    // 八段：每段错开 4 帧，最后一段落在 eight
    X.group([...Array(8)].map((_, i) => `seg${i}`), 0, 1, E.eight.l - 28, {step: RULE.stagger, antic: false});
  });

  // ---- 读状态
  const shift = S.shift, cmp = S.cmp;
  const mix = (a, b, t) => a + (b - a) * t;
  // 第三站的皿 → Huh7 皿 → 左边
  const dishX = cmp > 0 ? mix(SOLO[0], LEFT[0], cmp) : mix(ST[2], SOLO[0], shift);
  const dishY = cmp > 0 ? SOLO[1] : mix(500, SOLO[1], shift);
  const dishW = mix(400, DISH_W, shift);
  const k = dishW / DISH_W;                                  // 皿上的东西跟着缩放
  const hekX = mix(OFF_R[0], RIGHT[0], cmp);
  const roadX = -1500 * shift * shift, roadOp = 1 - shift;
  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});

  // 048 插头：第二站 → 跳到第三站旁 → 换场时停到右下 → 插进 Huh7 皿
  const hopP = HOP.at(S.hop);
  let plug = {x: hopP[0], y: hopP[1] + S.hopJ, w: 220, rot: -8 * Math.sin(Math.PI * S.hop), op: S.plugIn};
  if (shift > 0) plug = {...plug, x: mix(1330, 1340, shift), y: mix(676, 740, shift)};
  const dosePath = pathOf([[1340, 740], [1120, 300], [SOLO[0] + IN_DX, SOLO[1] + IN_DY]]);
  if (S.dose > 0) {
    const p = dosePath.at(S.dose);
    plug = {x: p[0], y: p[1] + S.doseJ, w: mix(220, 130, S.dose), rot: mix(0, -38, S.dose), op: 1};
  }
  if (cmp > 0) plug = {...plug, x: dishX + IN_DX, y: SOLO[1] + IN_DY + S.doseJ};
  const dose2Path = pathOf([[1990, 110], [1700, 160], [RIGHT[0] + IN_DX, RIGHT[1] + IN_DY]]);
  // 落进液面：一圈水纹往外扩
  const ripple = (cx, cy, at) => {
    const t = (f - at) / 40;
    return t > 0 && t < 1 && <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
      <ellipse cx={cx} cy={cy + 30} rx={30 + 120 * t} ry={(30 + 120 * t) * 0.42} fill="none" stroke={C.bone} strokeWidth={5} opacity={0.8 * (1 - t)} />
    </svg>;
  };
  const p2 = dose2Path.at(S.dose2);

  const dish = (cx, cy, w, tag, dimKey, only) => {
    const kk = w / DISH_W;
    return (
      <>
        <Sprite name="dish/34" x={cx + id(tag === "h" ? 3 : 7).y * 0} y={cy + id(tag === "h" ? 3 : 7).y} w={w} />
        {ICONS.map(([ix, iy], i) => {
          const a = S[`ic${i}`];
          if (a <= 0.01 || (only && !only.includes(i))) return null;
          const g = DIM.includes(i) ? S[`${dimKey}${i}`] || 0 : 0;
          return <Sprite key={i} name="mini/m34_on" x={cx + ix * kk} y={cy + iy * kk + id(tag === "h" ? 3 : 7).y} w={74 * kk * a} shadow={false}
                         style={{filter: g > 0.01 ? `grayscale(${g}) brightness(${1 - 0.25 * g})` : undefined}} op={Math.min(1, a) * (1 - 0.45 * g)} />;
        })}
      </>
    );
  };

  const gauge = (cx, cy, lvl, op) => {
    const x = cx + GAUGE.dx, y = cy + GAUGE.top, h = GAUGE.h, w = GAUGE.w;
    const ih = (h - 24) * lvl;
    return (
      <div style={{position: "absolute", left: 0, top: 0, opacity: op, transform: `translateY(${(1 - op) * 30}px)`}}>
        <Slab x={x} y={y} w={w} h={h} r={18} color={C.bone} depth={8} id={`gauge${cx}`} />
        <Slab x={x + 12} y={y + 12 + (h - 24 - ih)} w={w - 24} h={Math.max(4, ih)} r={10} color={C.blue} depth={0} shadow={false} id={`gfill${cx}`} />
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
          {[0, 0.5].map((t) => (
            <line key={t} x1={x + w} x2={x + w + 18} y1={y + 12 + (h - 24) * t} y2={y + 12 + (h - 24) * t} stroke={C.ink} strokeWidth={3} strokeLinecap="round" />
          ))}
        </svg>
      </div>
    );
  };

  const segs = [...Array(8)].map((_, i) => S[`seg${i}`]);
  const w210 = 210 * NM, w1700 = S.n1700 * NM;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2", "s3"])} whip={whipX(f, LEN - 7, "out", -1)}
             over={<T5In name="socket_bore" f={f} />}>
        {/* 第一幕：路和三站 */}
        <Layer id="road">
          <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${roadX}px)`, opacity: roadOp}}>
            <Runner d={`M150,${RUN_Y} L1770,${RUN_Y}`} draw={S.road} width={18} />
            {ST.map((x, i) => S.road > (x - 150) / 1620 && <Gate key={i} x1={x} y1={RUN_Y} x2={x} y2={RUN_Y - 62} w={14} broken={shift > 0 && i === 2 ? Math.min(1, shift * 3) : 0} />)}
            <Sprite name="mini/m34_on" x={ST[0]} y={505 + id(1).y - 30 * (1 - S.st0)} w={310} op={Math.min(1, S.st0)} rot={id(1).r} />
            <Sprite name="flask/34" x={ST[1]} y={490 + id(2).y - 30 * (1 - S.st1)} w={235} op={Math.min(1, S.st1)} rot={id(2).r} />
            <Slab x={ST[2] - 190} y={RUN_Y - 74} w={380} h={22} r={11} color={C.bone} depth={6} op={S.road > 0.85 ? 1 : 0} id="pad3" />
            <Tick x={ST[0] + 185} y={370} s={64} p={S.tick0} />
            <Tick x={ST[1] + 150} y={370} s={64} p={S.tick1} />
          </div>
        </Layer>

        {/* Huh7 皿（第一幕是第三站的皿） */}
        <Layer id="huh7">
          {S.dish > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: Math.min(1, S.dish * 1.4),
                         transform: `scale(${0.6 + 0.4 * S.dish})`, transformOrigin: `${dishX}px ${dishY}px`}}>
              {dish(dishX, dishY, dishW, "u", "dim")}
            </div>
          )}
        </Layer>

        <Layer id="plug">
          {plug.op > 0.01 && <Sprite name="plug/048_34" x={plug.x} y={plug.y} w={plug.w} rot={plug.rot} op={plug.op} shadow={S.dose < 0.5} />}
          {ripple(SOLO[0] + IN_DX, SOLO[1] + IN_DY, E.dose.l)}
        </Layer>

        <Layer id="cal">
          {S.cal > 0.01 && S.calOut < 1 && (
            <Calendar1 x={1450 + 700 * cmp} y={300 + S.calB0 * -1 + S.calB1 * -1 + S.calB2 * -1 + id(4).y} w={340}
                    op={Math.min(1, S.cal) * (1 - S.calOut)} sx={0.7 + 0.3 * S.cal} sy={0.7 + 0.3 * S.cal} rot={id(4).r} />
          )}
        </Layer>

        <Layer id="hek">
          {cmp > 0.001 && dish(hekX, RIGHT[1], DISH_W, "h", "dimH", HEK_ICONS)}
          {S.dose2 > 0.001 && <Sprite name="plug/048_34" x={p2[0] + (hekX - RIGHT[0])} y={p2[1] + S.dose2J} w={mix(200, 130, S.dose2)} rot={mix(10, -38, S.dose2)} shadow={false} />}
          {ripple(RIGHT[0] + IN_DX, RIGHT[1] + IN_DY, E.hneed.l)}
        </Layer>

        <Layer id="gauge">
          {S.gauge > 0.01 && gauge(dishX, SOLO[1], S.g1, Math.min(1, S.gauge))}
          {cmp > 0.01 && gauge(hekX, RIGHT[1], S.g2, 1)}
        </Layer>

        {/* 剂量条：一条骨白横杆，两行蓝条（Huh7 210、HEK293 1,700），八段铺满 */}
        <Layer id="bars">
          {S.rail > 0.001 && <Runner d={`M${BAR_X - 30},${ROW2 + BAR_H + 26} L${BAR_X + 1700 * NM + 30},${ROW2 + BAR_H + 26}`} draw={S.rail} width={12} />}
          {S.n210 > 0.5 && <Slab x={BAR_X} y={ROW1} w={Math.max(8, S.n210 * NM)} h={BAR_H} r={8} color={C.blue} depth={6} sheen={S.n210 / 210} id="bar1" />}
          {S.n1700 > 0.5 && <Slab x={BAR_X} y={ROW2} w={Math.max(8, w1700)} h={BAR_H} r={8} color={C.grey} depth={6} sheen={S.n1700 / 1700} id="bar2" />}
          {segs.map((a, i) => a > 0.01 && (
            <Slab key={i} x={BAR_X + i * w210 + 1} y={ROW2 - 22 * (1 - Math.min(1, a))} w={w210 - 3} h={BAR_H} r={8} color={C.blueHi} depth={6}
                  op={Math.min(1, a)} sheen={Math.min(1, a)} shadow={false} id={`seg${i}`} />
          ))}
        </Layer>

        {/* 字：豁免层 */}
        <Layer id="txt" exempt>
          <Label text="living cells" x={ST[2]} y={250} size={56} at={E.cells.l} out={E.shift.s} align="center" />
          <Label text="3 days" x={1450} y={420} size={56} at={E.cal.e - 14} out={E.dose.s + 10} align="center" />
          <Label text="Huh7" x={dishX} y={168} size={56} at={E.huh7.l} align="center" />
          <Pen text="liver cancer cells" x={1050} y={480} at={E.liver.l - 4} out={E.lost.s - 12} />
          <Label text="half" size={52} x={dishX + GAUGE.dx + GAUGE.w + 32} y={SOLO[1] + GAUGE.top + (GAUGE.h - 24) * 0.5 - 14} at={E.half.l} out={E.hek.s} />
          <Pen text="living-cell signal" x={1060} y={600} at={E.half.e - 70} out={E.hek.s} rot={-2} />
          <Label text="HEK293" x={hekX} y={168} size={56} at={E.hekl.l} align="center" />
          {S.n210 > 0.5 && (
            <div style={{position: "absolute", left: BAR_X + S.n210 * NM + 18, top: ROW1 - 18, display: "flex", alignItems: "baseline"}}>
              <Counter value={S.n210} digits={3} size={60} x={0} y={0} />
              <div style={{position: "absolute", left: 3 * 30 + 10, top: 14, opacity: S.nm1, transform: `translateY(${(1 - S.nm1) * 12}px)`}}><Engrave size={44}>nM</Engrave></div>
            </div>
          )}
          {S.n1700 > 0.5 && (
            <div style={{position: "absolute", left: BAR_X + w1700 + 18, top: ROW2 - 18}}>
              <Counter value={S.n1700} digits={4} comma size={60} x={0} y={0} />
              <div style={{position: "absolute", left: 4 * 30 + 26, top: 14, opacity: S.nm2, transform: `translateY(${(1 - S.nm2) * 12}px)`}}><Engrave size={44}>nM</Engrave></div>
            </div>
          )}
          <Pen text="≈ 8×" x={760} y={652} at={E.eight.l} dur={24} size={60} rot={-3} />
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B510" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
