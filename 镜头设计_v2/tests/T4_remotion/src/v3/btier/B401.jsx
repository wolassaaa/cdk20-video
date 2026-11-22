// HKBU SCIE1007 课程作业的科普视频：B 档 4-01（B 画外音）"So the team did something that once sounded like science fiction…"
// s1 So the team：三个小人落位；did something：往左让开；science fiction：手写。
// s2 asked an AI：AlphaFold 芯片落位；guess the shape：右边磨砂插座（看不清）加红问号。
// s3 Imagine a protein：清场；as a chain：十六颗蓝珠子一颗颗排出来；building blocks：珠子挨个鼓一下；that folds：链从两头往中间折起来；
//    into a 3D shape：珠子化成 AlphaFold 预测模型。
// s4 The order：模型缩到右上，链重新排直；of the blocks：珠子上出字母（CDK20 真实序列前 16 个，UniProt Q8IZL9：MDQYCILGRIGEGAHG）；is the sequence：标 sequence。
// s5 AlphaFold：链收成左下一小条，芯片落到中间；known structures：数据库架落下；how sequences fold：料杆连上，数据珠沿料杆流进芯片。
// s6 Give it one：序列条沿路送进芯片；it predicts：芯片一顿；the shape：模型从芯片右边出来；how sure：图例 sure / unsure；each part：手画圈住红尾巴。
// 接点：开头 T5 插座擦除（上一段 W2 是 A 段），结尾 T2 往左甩（下一段 4-02 是 B 页）。L0 第 4 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_4-01.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Tag, camBreath, shade, tint, Stage, Sprite, Label, Pen, Source, Engrave, Runner, Person1, pathOf, evMapB, T5In, whipX, impact, frost} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 4;

const SEQ = "MDQYCILGRIGEGAHG".split("");
const N = SEQ.length;
const TEAM = [[760, 520], [960, 540], [1160, 520]];
const P_W = 510;
const CHIP1 = {x: 1000, y: 470, w: 400};
const SOCK = {x: 1500, y: 470, w: 420};
// 链：排直（s3、s4）、折起（s3）、收成小条（s5、s6）
const STRAIGHT = (i) => [960 + (i - (N - 1) / 2) * 68, 500];
const FOLD_P = pathOf([[860, 400], [1060, 400], [1070, 470], [860, 480], [850, 550], [1060, 560]]);
const FOLDED = (i) => { const p = FOLD_P.at(i / (N - 1)); return [p[0], p[1]]; };
const STRIP = (i) => [170 + i * 30, 760];
const AF_C = {x: 960, y: 480, w: 460};          // s3 模型（和折好的链同一处）
const AF_R = {x: 1600, y: 380, w: 300};          // s4 模型让到右上
const CHIP = {x: 960, y: 450, w: 420};
const RACK = {x: 360, y: 330, w: 380};
const FEED = pathOf([[545, 345], [640, 318], [720, 372], [780, 440]]);
const GIVE = pathOf([[395, 760], [640, 720], [820, 600], [CHIP.x, CHIP.y]]);
const MODEL = {x: 1480, y: 450, w: 440};
const TAIL = [1476, 326];                         // 模型上红尾巴（af/front305 贴图上部那一段）

const clamp01 = (v) => Math.max(0, Math.min(1, v));
const mix = (a, b, t) => a + (b - a) * t;
const lerp2 = (a, b, t) => [mix(a[0], b[0], t), mix(a[1], b[1], t)];
const sm = (t) => { const x = clamp01(t); return x * x * (3 - 2 * x); };

const BeadDefs = () => (
  <defs>
    <radialGradient id="bblue" cx="0.38" cy="0.34" r="0.7">
      <stop offset="0" stopColor={tint(C.blueHi, 0.25)} />
      <stop offset="0.55" stopColor={C.blue} />
      <stop offset="1" stopColor={shade(C.blue, 0.4)} />
    </radialGradient>
    <radialGradient id="bred" cx="0.38" cy="0.34" r="0.7">
      <stop offset="0" stopColor={tint(C.red, 0.35)} />
      <stop offset="0.55" stopColor={C.red} />
      <stop offset="1" stopColor={shade(C.red, 0.38)} />
    </radialGradient>
  </defs>
);
const Ball = ({x, y, r, fill = "url(#bblue)", op = 1}) => (
  <g opacity={op}>
    <ellipse cx={x + 3} cy={y + r * 0.92} rx={r * 0.95} ry={r * 0.3} fill="rgba(40,30,20,0.22)" />
    <circle cx={x} cy={y} r={r} fill={fill} />
    <ellipse cx={x - r * 0.32} cy={y - r * 0.38} rx={r * 0.34} ry={r * 0.22} fill="rgba(255,255,255,0.7)" />
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    // s1
    X.group(TEAM.map((_, i) => `t${i}`), 0, 1, E.team.l, {antic: false});
    X.tw("left", 0, 1, E.some.s, E.some.e, "power2.out");
    // s2
    X.land("chip1", 0, 1, E.ai.l, {antic: false});
    X.land("sock", 0, 1, E.guess.l, {antic: false});
    // s3
    X.tw("clear1", 0, 1, E.prot.s - 4, E.prot.e, "power1.in");
    X.tw("chain", 0, 1, E.chain.s, E.chain.s + 2 * N + 8, "none");
    X.tw("bulge", 0, 1, E.blocks.s, E.blocks.e, "none");
    X.tw("fold", 0, 1, E.folds.s, E.folds.e + 16, "power1.inOut");
    X.tw("morph", 0, 1, E.shape3d.s, E.shape3d.l + 12, "power2.out");
    // s4
    X.tw("order", 0, 1, E.order.s, E.order.e + 30, "power2.out");
    X.tw("letters", 0, 1, E.letters.s, E.letters.s + 2 * N + 6, "none");
    X.tw("brk", 0, 1, E.seq.s, E.seq.l + 20, "power2.out");
    // s5
    X.tw("pack", 0, 1, E.af.s - 4, E.af.l + 26, "power2.inOut");
    X.land("chip", 0, 1, E.af.l + 4, {antic: false});
    X.land("rack", 0, 1, E.known.l, {antic: false});
    X.tw("feed", 0, 1, E.learn.s, E.learn.l, "power2.out");
    X.tw("flow", 0, 1, E.learn.l - 6, E.give.s + 10, "none");
    // s6
    X.tw("give", 0, 1, E.give.s, E.give.l, "power1.inOut");
    X.tw("lift", 0, 1, E.predicts.s, E.predicts.l, "power2.out");
    X.jiggle("chipJ", E.predicts.l, 5, 0);
    X.tw("pred", 0, 1, E.pred.s, E.pred.l + 14, "power2.out");
    X.tw("leg", 0, 1, E.sure.s, E.sure.l + 10, "power2.out");
    X.tw("ring", 0, 1, E.part.s, E.part.s + 26, "power1.inOut");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const shake = impact(f, E.predicts.l);
  const out1 = -2200 * S.clear1;

  // 链：每颗珠子的位置和大小
  const fold = S.fold, morph = S.morph, ord = S.order, pack = S.pack, give = S.give;
  const beads = SEQ.map((ch, i) => {
    const vis = sm((S.chain * (2 * N + 8) - 2 * i) / 8);
    // 折：两头先折、往中间合（拉链式）
    const zi = Math.min(i, N - 1 - i) / ((N - 1) / 2);
    const fk = sm(fold * 1.6 - (1 - zi) * 0.6);
    // 排回直：从中间往两头
    const uk = sm(ord * 1.6 - zi * 0.6);
    let p = lerp2(STRAIGHT(i), FOLDED(i), fk * (1 - uk));
    let r = mix(31, 22, fk * (1 - uk));
    // 鼓一下：一道波从左走到右
    const wv = S.bulge * (N + 3) - i;
    r *= 1 + 0.3 * Math.max(0, Math.sin(Math.PI * clamp01(wv / 3)));
    // 收成左下小条
    p = lerp2(p, STRIP(i), sm(pack * 1.3 - (i / N) * 0.3));
    r = mix(r, 13, pack);
    // 送进芯片：整条沿路走，越走越小
    if (give > 0) {
      const c = GIVE.at(give), c0 = GIVE.at(0);
      const k = mix(1, 0.3, give);
      p = [c[0] + (p[0] - c0[0]) * k, c[1] + (p[1] - c0[1]) * k];
      r *= k;
    }
    const op = vis * (1 - sm((morph - 0.1) * 2.2) * (1 - sm(ord * 3))) * (1 - sm((give - 0.8) * 5));
    return {ch, i, x: p[0] + id(30 + i).y * 0.6, y: p[1] + id(40 + i).y, r, op};
  });
  const letterOp = (i) => sm((S.letters * (2 * N + 6) - 2 * i) / 6);

  // 模型（s3 中间，s4 让到右上，s5 出画）
  const afP = lerp2([AF_C.x, AF_C.y], [AF_R.x, AF_R.y], ord);
  const afW = mix(AF_C.w, AF_R.w, ord) * (0.86 + 0.14 * morph);
  const afOut = 900 * sm(pack * 1.5);
  const afOp = clamp01(morph * 1.4) * (1 - sm(pack * 1.6));

  // 数据珠：沿料杆流进芯片
  const flowBeads = S.flow > 0 && S.flow < 1 ? [...Array(7)].map((_, k) => {
    const u = ((f - E.learn.l) / 40 + k / 7) % 1;
    const p = FEED.at(u);
    return {x: p[0], y: p[1], op: clamp01(u * 6) * clamp01((1 - u) * 6) * clamp01((1 - S.flow) * 20)};
  }) : [];
  const chipLift = 14 * S.lift * (1 - sm((f - E.predicts.l) / 6));
  const chipGlow = Math.max(0, Math.sin(Math.PI * clamp01((f - E.predicts.l + 4) / 30)));

  // 新模型从芯片右边出来
  const mp = lerp2([CHIP.x + 120, CHIP.y], [MODEL.x, MODEL.y], S.pred);
  const ringLen = 2 * Math.PI * 126;

  const whip = whipX(f, LEN - 7, "out", -1);

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, [])} whip={whip} shakeX={shake} over={<T5In name="socket_bore" f={f} />}>
        {/* s1–s2 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${out1}px)`}}>
          <Layer id="team">
            {TEAM.map(([x, y], i) => {
              const a = S[`t${i}`];
              if (a <= 0.01) return null;
              return <Person1 key={i} red={i === 1} x={x - 420 * S.left + 40 * (i - 1) * S.left * -0.5} y={y - 50 * (1 - Math.min(1, a)) + id(1 + i).y} w={P_W}
                              op={Math.min(1, a * 1.5)} rot={id(1 + i).r} />;
            })}
          </Layer>
          <Layer id="chip">
            {S.chip1 > 0.01 && <Sprite name="chip_alphafold/34" x={CHIP1.x} y={CHIP1.y - 50 * (1 - Math.min(1, S.chip1)) + id(5).y} w={CHIP1.w} op={Math.min(1, S.chip1 * 1.5)} rot={id(5).r} />}
          </Layer>
          <Layer id="sock">
            {S.sock > 0.01 && <Sprite name="socket/hero_face" x={SOCK.x} y={SOCK.y - 50 * (1 - Math.min(1, S.sock)) + id(6).y} w={SOCK.w} op={Math.min(1, S.sock * 1.5)} style={frost(0.9)} />}
          </Layer>
          <Layer id="txt1" exempt>
            <Pen text="science fiction" x={1000} y={300} at={E.scifi.s} out={E.ai.s} size={92} />
            <Pen text="?" x={SOCK.x + 150} y={SOCK.y - 330} at={E.guess.l} dur={26} size={190} color={C.red} rot={6} />
          </Layer>
        </div>

        {/* s3–s4 模型 */}
        <Layer id="model">
          {afOp > 0.01 && <Sprite name="af/front305" x={afP[0] + afOut} y={afP[1] + id(7).y} w={afW} op={afOp} rot={id(7).r} />}
          {S.pred > 0.01 && <Sprite name="af/front305" x={mp[0]} y={mp[1] + id(8).y} w={MODEL.w * (0.5 + 0.5 * S.pred)} op={clamp01(S.pred * 3)} rot={id(8).r} lift={10 * (1 - S.pred)} />}
          {S.ring > 0.01 && (
            <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: id(8).y, overflow: "visible"}}>
              <ellipse cx={TAIL[0]} cy={TAIL[1]} rx={138} ry={112} fill="none" stroke={C.ink} strokeWidth={6} strokeLinecap="round" transform={`rotate(-20 ${TAIL[0]} ${TAIL[1]})`}
                       strokeDasharray={`${ringLen * 1.08} ${ringLen * 2}`} strokeDashoffset={ringLen * 1.08 * (1 - S.ring)} />
            </svg>
          )}
        </Layer>

        {/* 链 */}
        <Layer id="chain">
          <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
            <BeadDefs />
            {beads.map((b, j) => j > 0 && b.op > 0.01 && beads[j - 1].op > 0.01 && (
              <line key={`l${j}`} x1={beads[j - 1].x} y1={beads[j - 1].y} x2={b.x} y2={b.y} stroke={shade(C.blue, 0.3)} strokeWidth={Math.max(3, b.r * 0.3)} strokeLinecap="round" opacity={Math.min(b.op, beads[j - 1].op)} />
            ))}
            {beads.map((b) => b.op > 0.01 && <Ball key={b.i} x={b.x} y={b.y} r={b.r} op={b.op} />)}
            {S.brk > 0.01 && (
              <path d={`M${STRAIGHT(0)[0] - 30},572 L${STRAIGHT(0)[0] - 30},584 L${STRAIGHT(N - 1)[0] + 30},584 L${STRAIGHT(N - 1)[0] + 30},572`} fill="none" stroke={C.ink} strokeWidth={4}
                    strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - S.brk} opacity={1 - pack} />
            )}
          </svg>
          {beads.map((b) => {
            const lo = letterOp(b.i) * b.op;
            return lo > 0.01 && b.r > 16 && (
              <div key={`t${b.i}`} style={{position: "absolute", left: b.x, top: b.y, transform: "translate(-50%, -54%)", opacity: lo}}>
                <Engrave size={Math.round(b.r * 1.45)} light style={{textShadow: "0 1px 1px rgba(0,0,0,0.55)"}}>{b.ch}</Engrave>
              </div>
            );
          })}
        </Layer>

        {/* s5–s6 芯片、数据库架 */}
        <Layer id="chip">
          {S.chip > 0.01 && (
            <Sprite name="chip_alphafold/34" x={CHIP.x} y={CHIP.y - 50 * (1 - Math.min(1, S.chip)) - chipLift + (S.chipJ || 0) + id(9).y} w={CHIP.w} op={Math.min(1, S.chip * 1.5)}
                    rot={id(9).r} lift={chipLift} rim={chipGlow * 0.9} />
          )}
        </Layer>
        <Layer id="rack">
          {S.rack > 0.01 && <Sprite name="dbrack/34" x={RACK.x} y={RACK.y - 50 * (1 - Math.min(1, S.rack)) + id(10).y} w={RACK.w} op={Math.min(1, S.rack * 1.5)} rot={id(10).r} />}
          {S.feed > 0.01 && <Runner d={FEED.d} width={14} draw={S.feed} />}
          {flowBeads.length > 0 && (
            <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
              <BeadDefs />
              {flowBeads.map((b, k) => <Ball key={k} x={b.x} y={b.y - 10} r={10} op={b.op} />)}
            </svg>
          )}
        </Layer>

        <Layer id="legend">
          {S.leg > 0.01 && (
            <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 30 * (1 - S.leg), overflow: "visible", opacity: Math.min(1, S.leg * 1.6)}}>
              <BeadDefs />
              <Ball x={1290} y={800} r={20} />
              <Ball x={1530} y={800} r={20} fill="url(#bred)" />
            </svg>
          )}
        </Layer>

        <Layer id="txt" exempt>
          <Label text="sequence" size={56} x={960} y={610} at={E.seq.l} out={E.af.s} align="center" />
          {afOp > 0.01 && ord < 0.2 && <Tag x={AF_C.x} y={760} op={afOp * (1 - ord * 5)}>PREDICTED MODEL (AlphaFold DB v6)</Tag>}
          {S.pred > 0.3 && <Tag x={MODEL.x} y={706} op={clamp01((S.pred - 0.3) * 2)}>PREDICTED MODEL (AlphaFold DB v6)</Tag>}
          <Label text="sure" size={48} x={1322} y={772} at={E.sure.l} />
          <Label text="unsure" size={48} x={1562} y={772} at={E.sure.l + 6} />
          <Source>Illustration · sequence: UniProt Q8IZL9 · model: AlphaFold DB, colours = confidence</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B401" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
