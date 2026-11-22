// HKBU SCIE1007 课程作业的科普视频：B 档 6-03 "Finding a hit. Before: screening real compounds by the millions, an approach a 2023 review says has hit a costly bottleneck.
// Now: 8,918 designs inside a computer, and just 13 molecules actually made."
// 规则 v2：第 6 章翻牌记分板，第 1 行已填。row2：行名 2. FINDING A HIT；focus2：机位从第 1 行 NOW 栏移到第 2 行 BEFORE 栏。
// bef：栏头翻出 BEFORE，凹位里升起一块孔板（化合物板，每孔一种真实化合物），飞到行下面放大；comp：后面摞起一叠孔板（化合物库）；
// mil：孔板一块接一块沿料杆送进读板机（高通量筛选），主翻牌 MILLIONS SCREENED；appr：送得越来越慢；rev：综述书滑进来（名牌 2023 review）；
// says：孔板在读板机门口挤成一摞；costly：读板机的灯变红；bn：COSTLY BOTTLENECK。
// now：BEFORE 的件缩回凹位，机位横移到 NOW 栏，栏头翻出 NOW；8,918：数字轮滚到 8,918（开口念这个数时到位）；des：8,918 DESIGNS；
// comp2：Chemistry42 芯片滑进来，芯片上方浮着一大片半透明的设计（插头 = 设计出来的分子）；13：数字轮滚回 13，13 个设计变实、一个个落进托盘；made：13 MOLECULES MADE，T7 一抖。
// 结尾 T5 runner（接 6-04+05 出镜）。Gemini 初审（11-21）改：小球 + 滤网换成孔板 + 读板机；8,918 早到位、到 13 时数字跟着变；空凹位不亮框；名牌收进舞台。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-03.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Stage, Sprite, Slab, Tag, Counter, Runner, Source, evMapB, whipX, impact, T5Out} from "./bkit.jsx";
import {useGsapTimeline, idle, rand} from "./gsapFrame.jsx";
import {Board6, FOCUS, POP, Dim, cell, SlotDeco} from "./board6.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 6;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const wf = (k) => K.words.find((w) => w.key === k);
const B = cell(1, "B").slot, N = cell(1, "N").slot;
const PB = POP(1, "B"), PN = POP(1, "N");
const PW = 200, PH = 134;                                   // 孔板
// 版面按世界坐标排：机位 z 1.6 对准 y 639，能用的竖向带是 545–850（行底 530，出处行 855）
const READER = {x: 1060, y: 715, w: 220, h: 190};
const LANE_Y = 790;
const STACK = {x: 260, y: 700};
const BOOK = {x: 620, y: 650, w: 170};
const CNT = {x: 1250, y: 572};
const CHIP = {x: 1010, y: 745, w: 200};
const TRAY = {x: 1480, y: 735, w: 300, h: 104};
const PLUGS = [...Array(13)].map((_, k) => ({x: TRAY.x + 30 + (k % 7) * 40, y: TRAY.y + 30 + Math.floor(k / 7) * 46, name: ["A", "B", "C", "D", "E", "F", "001"][k % 7]}));
const GHOST = [...Array(40)].map((_, k) => ({x: 1140 + rand(k + 1) * 300, y: 740 + rand(k + 50) * 100, r: (rand(k + 9) - 0.5) * 60}));
const DOTC = [C.blueHi, C.gold, C.green, C.blue, C.grey];

// 孔板：骨白板 + 8 × 12 个孔，孔里一点颜色（每孔一种化合物）
const Plate96 = ({x, y, s = 1, op = 1, seed = 0}) => (
  <div style={{position: "absolute", left: 0, top: 0, opacity: op}}>
    <Slab x={x - (PW * s) / 2} y={y - (PH * s) / 2} w={PW * s} h={PH * s} r={10 * s} color={C.bone} depth={7 * s} id={`p96_${seed}`} shadow={s > 0.5}>
      {[...Array(96)].map((_, k) => {
        const cx = 16 * s + (k % 12) * 15.2 * s, cy = 14 * s + Math.floor(k / 12) * 15.2 * s;
        return <div key={k} style={{position: "absolute", left: cx - 5.5 * s, top: cy - 5.5 * s, width: 11 * s, height: 11 * s, borderRadius: 6 * s,
                                    background: DOTC[Math.floor(rand(k + seed * 97) * 5)], opacity: 0.55 + 0.45 * rand(k * 3 + seed),
                                    boxShadow: `inset 0 ${1.5 * s}px ${2 * s}px rgba(0,0,0,0.45)`}} />;
      })}
    </Slab>
  </div>
);

const Scene = () => {
  const f = useCurrentFrame();
  const n8918 = wf("8,918#1"), n13 = wf("13#1");
  const S = useGsapTimeline((tl, S, X) => {
    X.tw("move", 0, 1, 0, E.focus2.l + 18, "power2.inOut");
    X.tw("rise", 0, 1, E.bef.s - 6, E.bef.l, "power2.out");
    X.tw("popB", 0, 1, E.bef.l, E.bef.l + 30, "power3.inOut");
    X.tw("stack", 0, 1, E.comp.s, E.comp.l + 10, "power2.out");
    X.tw("run", 0, 1, E.mil.s, E.mil.l, "power1.in");
    X.tw("slow", 0, 1, E.appr.s, E.says.l, "power1.inOut");
    X.tw("book", 0, 1, E.rev.s, E.rev.l, "power2.out");
    X.tw("jam", 0, 1, E.says.s, E.says.l + 10, "power2.out");
    X.tw("redl", 0, 1, E.costly.s, E.costly.l, "power2.out");
    X.jiggle("sj", E.bn.l, 6, 0);
    X.tw("backB", 0, 1, E.now.s - 28, E.now.s + 4, "power2.inOut");
    X.tw("pan", 0, 1, E.now.s - 14, E.now.l + 12, "power2.inOut");
    X.tw("popN", 0, 1, E.now.s, E.now.l + 18, "power3.out");
    S.n = 0;
    X.count("n", 0, 8918, n8918.f0 + 10, n8918.f0 + 10 - E.n8918.s, "power3.out");
    tl.fromTo(S, {n: 8918}, {n: 13, duration: (n13.f0 + 6 - E.n13.s) / 60, ease: "power3.inOut", immediateRender: false}, E.n13.s / 60);
    X.jiggle("cj", E.des.l, 6, 0);
    X.tw("chip", 0, 1, E.comp2.s, E.comp2.l + 6, "power2.out");
    X.tw("ghost", 0, 1, E.comp2.l - 4, E.comp2.l + 30, "power2.out");
    X.tw("eject", 0, 1, E.n13.s, n13.f1 + 20, "none");
    X.jiggle("tj", E.made.l, 6, 0);
    X.tw("backN", 0, 1, E.made.l + 8, LEN - 14, "power2.inOut");
  });
  const F0 = FOCUS(0, "N"), FB = FOCUS(1, "B"), FN = FOCUS(1, "N");
  const drift = 0.05 * (f / LEN);
  const cam = {x: mix(mix(F0.x, FB.x, S.move), FN.x, S.pan), y: mix(F0.y, FB.y, S.move), z: FB.z + drift};
  const whip = f < 7 ? whipX(f, 0, "in", -1) : 0;
  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const popB = S.popB * (1 - S.backB), popN = S.popN * (1 - S.backN);
  const keepN = 1 - S.backN;
  const p0 = {x: mix(B.cx, STACK.x + 40, popB), y: mix(B.cy - 8 * S.rise, STACK.y, popB), s: mix(0.6, 1, popB)};
  // 送板：每块板沿料杆从板堆走到读板机，速度随 slow 降下来；jam 后门口排成一摞
  const speed = mix(1, 0.22, S.slow) * (1 - 0.9 * S.jam);
  const conv = [...Array(4)].map((_, k) => {
    if (S.run < 0.01 || popB < 0.3) return null;
    const ph = ((f - E.mil.s) * 0.006 * (0.5 + 0.5 * speed) + k / 4) % 1;
    let x = mix(STACK.x + 60, READER.x - 40, ph), y = LANE_Y;
    const q = Math.min(k, 3);
    if (S.jam > 0) { x = mix(x, READER.x - 150 - q * 18, S.jam); y = mix(y, LANE_Y - q * 14, S.jam); }
    return <Plate96 key={k} x={x} y={y - (S.sj || 0)} s={0.62} seed={k + 3} op={popB * cl(S.run * 3) * (ph > 0.92 && S.jam < 0.5 ? 1 - (ph - 0.92) / 0.08 : 1)} />;
  });
  const plugs = PLUGS.map((p, k) => {
    const u = cl((S.eject * 13 - k) / 2.2);
    if (u <= 0) return null;
    const g = GHOST[k * 3];
    const x = mix(g.x, p.x, u), y = mix(g.y, p.y, u) - 80 * Math.sin(Math.PI * u);
    return <Sprite key={k} name={`plug/${p.name}_34`} x={x} y={y - (S.tj || 0)} w={mix(52, 46, u)} rot={mix(g.r, 0, u)} shadow={u > 0.9} />;
  });
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} shakeX={impact(f, E.made.l)} over={<T5Out name="runner" f={f} len={LEN} />}>
        <Layer id={["board", "hopper", "jam", "now2", "tray13"]}>
          <Board6 f={f} cam={cam} cols={1} hdr={{B: E.bef.l, N: E.now.l}}
                  rows={[true, {name: E.row2.l, B: E.mil.l, Bs: [E.bn.l], N: E.des.l, Ns: [E.made.l]}, false, false]}
                  lit={{"1B": cl((f - E.focus2.s) / 12) * (1 - S.pan) * (popB > 0.5 ? 0 : 1), "1N": S.pan * (popN > 0.5 ? 0 : 1)}}>
            <Dim i={1} v={Math.max(popB, popN, S.move * 0.7)} />
            {/* BEFORE：化合物板堆 → 料杆 → 读板机 */}
            {popB > 0.05 && S.run > 0.01 && <Runner d={`M${STACK.x + 40},${LANE_Y + 30} L${READER.x - 20},${LANE_Y + 30}`} width={14} draw={cl(S.run * 2)} op={popB} />}
            {S.stack > 0.01 && popB > 0.05 && [0, 1, 2, 3, 4].map((k) => (
              <Plate96 key={k} x={STACK.x + 40 + k * 4} y={STACK.y - 30 - k * 16 + 40 * (1 - S.stack)} s={0.9} seed={20 + k} op={cl(S.stack * 2) * popB} />
            ))}
            {S.rise > 0.01 && <Plate96 x={p0.x} y={p0.y + id(1).y} s={p0.s} seed={1} op={cl(S.rise * 2)} />}
            {conv}
            {popB > 0.05 && S.run > 0.01 && (
              <Slab x={READER.x - READER.w / 2} y={READER.y - READER.h / 2} w={READER.w} h={READER.h} r={18} color={C.black} depth={12} op={popB * cl(S.run * 3)} id="reader">
                <div style={{position: "absolute", left: 20, top: READER.h - 70, width: 22, height: 50, borderRadius: 6, background: "rgba(255,255,255,0.08)"}} />
                <div style={{position: "absolute", left: 60, top: 24, width: READER.w - 84, height: 14, borderRadius: 7,
                             background: S.redl > 0.5 ? C.red : C.blueHi, opacity: 0.55 + 0.45 * Math.abs(Math.sin(f / (S.redl > 0.5 ? 5 : 9))),
                             boxShadow: `0 0 14px ${S.redl > 0.5 ? "rgba(200,16,46,0.8)" : "rgba(61,107,230,0.8)"}`}} />
              </Slab>
            )}
            {S.book > 0.01 && popB > 0.05 && <Sprite name="book/34" x={mix(BOOK.x - 260, BOOK.x, S.book)} y={BOOK.y} w={BOOK.w} op={cl(S.book * 2) * popB} rot={-4} />}
            {S.book > 0.5 && popB > 0.5 && <Tag x={BOOK.x + 200} y={BOOK.y - 30} op={cl((S.book - 0.5) * 2) * cl(popB * 2 - 1)} on="book">2023 review</Tag>}
            {/* NOW：数字轮 + Chemistry42 芯片 + 一片半透明的设计 → 13 个做出来的 */}
            <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: keepN, transformOrigin: `${N.cx}px ${N.cy}px`, transform: `scale(${(0.35 + 0.65 * keepN).toFixed(3)})`}}>
              {popN > 0.01 && (
                <div style={{position: "absolute", left: CNT.x, top: CNT.y - (S.cj || 0), opacity: cl(popN * 2)}}>
                  <Slab x={-200} y={-14} w={400} h={128} r={18} color={C.bone} depth={10} id="cntslab" sheen={S.n > 13.5 && S.n < 8917.5 ? (S.n / 8918) : -1} />
                  <Counter value={S.n} digits={4} comma size={100} x={0} y={0} align="center" />
                </div>
              )}
              {S.chip > 0.01 && <Sprite name="chip_chemistry42/34" x={mix(CHIP.x - 300, CHIP.x, S.chip)} y={CHIP.y + id(3).y} w={CHIP.w} op={cl(S.chip * 2)} />}
              {S.ghost > 0.01 && GHOST.map((g, k) => (S.eject * 13 > k / 3 && k % 3 === 0 && k / 3 < 13 ? null :
                <Sprite key={k} name={`plug/${["A", "B", "C", "D", "E", "F"][k % 6]}_34`} x={g.x + 6 * Math.sin(f / 30 + k)} y={g.y + 5 * Math.cos(f / 26 + k)} w={44} rot={g.r}
                        op={S.ghost * 0.5 * (1 - 0.6 * cl(S.eject * 2 - 1))} shadow={false} style={{filter: "saturate(0.15) brightness(1.9)"}} />
              ))}
              {S.chip > 0.01 && <Slab x={TRAY.x} y={TRAY.y + 40 * (1 - S.chip) - (S.tj || 0)} w={TRAY.w} h={TRAY.h} r={16} color={C.bone} depth={10} op={cl(S.chip * 2)} id="tray13" />}
              {plugs}
              {S.eject > 0.3 && <Tag x={TRAY.x + TRAY.w / 2} y={TRAY.y - 56} op={cl(S.eject * 3 - 1)} on="plug">each plug = one molecule</Tag>}
            </div>
            {S.backN > 0.01 && <SlotDeco i={1} side="N" op={S.backN} />}
          </Board6>
        </Layer>
        <Layer id="txt" exempt>
          <Source>{f < E.now.s ? "Illustration · screening bottleneck: Wang et al., Pharmaceuticals 2023 (review)" : "Illustration · data: Ren et al., Chem. Sci. 2023"}</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B603" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
