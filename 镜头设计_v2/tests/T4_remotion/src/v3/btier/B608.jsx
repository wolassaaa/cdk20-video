// HKBU SCIE1007 课程作业的科普视频：B 档 6-08 "To be fair, these pairs come from different studies: they compare scale and speed, not one race run side by side.
// But the paper itself calls the work cost- and time-efficient."
// 规则 v2：第 6 章翻牌记分板，四行全填（接 6-07 拉回的整块板）。
// pairs：四行的 BEFORE 和 NOW 一行一行框成一对（金框 + 中间一道连线），第一对落在 pairs；
// seam：BEFORE、NOW 两栏中间亮起一道红缝，从上往下划开；镜头稍拉远（板上方露出台面），手写批注 different studies 写在板上方；
// scale：第 2 行（8,918 vs millions）那一对的框加粗发光；speed：第 3 行（30 days vs 10–17 years）那一对加粗发光；
// race：板盖暗纱，跑道件落到板前面；side by side：跑道两条道一上一下错开（不是同一场比赛），手写批注 not one race；
// paper：跑道退开，论文书从左边滑进来；calls：引文牌立起来 "cost- and time-efficient"（Ren et al. 2023 原话）；
// cost / time-efficient：两个词下面先后划金线，绿勾。结尾 T2 往左甩（6-09 接路）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-08.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, SERIF, Stage, Sprite, Slab, Pen, Tick, Source, evMapB, whipX, impact, camBreath} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";
import {Board6, DimUp, cell, COL, ROW_Y, ROW_H} from "./board6.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 6;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const wf = (k) => K.words.find((w) => w.key === k);
const SEAM_X = (COL.B.x + COL.B.w + COL.N.x) / 2;
const TRACK = {x: 960, y: 520, w: 980};
const BOOK = {x: 560, y: 520, w: 400};
const QUOTE = {x: 516, y: 691, w: 902, h: 174};

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.tw("push", 0, 1, 0, E.pairs.s, "sine.inOut");
    [0, 1, 2, 3].forEach((i) => X.tw(`pr${i}`, 0, 1, E.pairs.l - 14 + i * 6, E.pairs.l + i * 6, "power2.out"));
    X.tw("seam", 0, 1, E.seam.s - 6, E.seam.l, "power2.inOut");
    X.tw("back", 0, 1, E.seam.s - 10, E.note1.l + 10, "power2.inOut");
    X.tw("sc", 0, 1, E.scale.s, E.scale.l, "power2.out");
    X.tw("sp", 0, 1, E.speed.s, E.speed.l, "power2.out");
    X.tw("dim", 0, 1, E.race.s - 16, E.race.l, "power2.inOut");
    X.land("trk", 0, 1, E.race.l, {antic: false, dur: 18});
    X.tw("split", 0, 1, E.side.s - 10, E.side.l, "power3.inOut");
    X.tw("trkOut", 0, 1, E.paper.s - 24, E.paper.s + 2, "power2.in");
    X.tw("book", 0, 1, E.paper.s - 6, E.paper.l, "power2.out");
    X.tw("quote", 0, 1, E.cost.s, E.cost.l, "power2.out");
    X.tw("u1", 0, 1, E.cost.s, E.cost.l + 4, "power2.out");
    X.tw("u2", 0, 1, E.timeef.s, E.timeef.l + 4, "power2.out");
    X.tw("tk", 0, 1, E.timeef.l + 6, E.timeef.l + 26, "power2.out");
    X.jiggle("qj", E.timeef.l, 6, 0);
  });
  const z = mix(mix(1.0, 1.03, S.push), 0.84, S.back) * (1 + 0.05 * f / LEN);      // 全程慢推（不停在一处）
  const cam = {x: 960 + 24 * Math.sin(f / 70), y: mix(540, 500, S.back), z};          // 1 倍时 y 540：板底 878 在出处行上面
  const whip = f < 4 ? 0 : f > LEN - 8 ? whipX(f, LEN - 7, "out", -1) : 0;
  const id = (s) => idle(f, s, {rot: 0.5, bob: 1.4});
  // 一对的框：BEFORE 主翻牌左边到 NOW 主翻牌右边，两个框中间一道连线
  const pair = (i) => {
    const p = S[`pr${i}`] || 0;
    if (p < 0.01) return null;
    const hot = i === 1 ? S.sc : i === 2 ? S.sp : 0;
    const B = cell(i, "B"), N = cell(i, "N"), y = ROW_Y(i);
    const bw = 4 + 4 * hot, glow = hot > 0.01 ? `0 0 ${(18 * hot).toFixed(0)}px rgba(226,207,160,0.95)` : "none";
    const box = (x, w, k) => <div key={k} style={{position: "absolute", left: x - 6, top: y + 4, width: w + 12, height: ROW_H - 8, borderRadius: 14,
                                                  border: `${bw}px solid ${C.gold}`, boxShadow: glow, opacity: p * (1 - 0.65 * S.dim), transform: `scale(${(1.06 - 0.06 * p).toFixed(3)})`}} />;
    return (
      <React.Fragment key={i}>
        {box(B.main.x, B.main.w, "b")}
        {box(N.main.x, N.main.w, "n")}
        <div style={{position: "absolute", left: B.main.x + B.main.w + 6, top: y + ROW_H / 2 - 2, width: (N.main.x - B.main.x - B.main.w - 12) * p, height: 4, background: C.gold, opacity: p * (1 - 0.65 * S.dim)}} />
      </React.Fragment>
    );
  };
  const split = S.split;
  const trk = cl(S.trk) * (1 - S.trkOut);
  const under = (p) => ({backgroundImage: `linear-gradient(${C.gold}, ${C.gold})`, backgroundRepeat: "no-repeat", backgroundPosition: "0 92%", backgroundSize: `${(p * 100).toFixed(1)}% 7px`});
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2"], 30)} whip={whip} shakeX={impact(f, E.race.l) + impact(f, E.calls.l)}>
        <Layer id={["board", "pairs", "seam", "nowcol", "quote"]}>
          <Board6 f={f} cam={cam} cols={1} rows={[true, true, true, true]}>
            {[0, 1, 2, 3].map(pair)}
            {(S.seam > 0.01 || f>=E.race.s) && (
              <div style={{position: "absolute", left: SEAM_X - 3, top: 150, width: 6, height: 700 * S.seam, borderRadius: 3, background: f>=E.race.s ? `repeating-linear-gradient(${C.blue} 0 12px,transparent 12px 26px)` : C.red,
                           boxShadow: "0 0 14px rgba(200,16,46,0.85)", opacity: 1 - 0.6 * S.dim}} />
            )}
            <DimUp i={4} v={S.dim * 0.92} />
          </Board6>
        </Layer>
        <Layer id={["track", "quote", "seam", "nowcol", "pairs"]}>
          {S.quote > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, opacity: cl(S.quote * 2), transform: `translateY(${(40 * (1 - Math.min(1, S.quote))).toFixed(1)}px)`}}>
              <Slab x={QUOTE.x} y={QUOTE.y - (S.qj || 0)} w={QUOTE.w} h={QUOTE.h} r={18} color={C.bone} depth={12} id="quote">
                <div data-role="label" data-on="plug,socket,mini,af,loop,tcase,thub,mp,slab" style={{position: "absolute", left: 40, top: 40, fontFamily: SERIF, fontSize: 66, color: C.ink, whiteSpace: "nowrap", fontStyle: "italic", lineHeight: 1.1}}>
                  “<span style={under(S.u1)}>cost-</span> and <span style={under(S.u2)}>time-efficient</span>”
                </div>
                <div data-role="source" style={{position: "absolute", left: 44, top: 110, fontFamily: SERIF, fontSize: 34, color: C.soft, whiteSpace: "nowrap"}}>
                  Ren et al., Chem. Sci. 2023
                </div>
              </Slab>
              <Tick x={QUOTE.x + QUOTE.w - 70} y={QUOTE.y - 40} s={70} p={S.tk} sw={12} />
            </div>
          )}
        </Layer>
        <Layer id="txt" exempt>
          <Pen text="different studies" x={SEAM_X * 0.84 + 960 * 0.16 - 120} y={56} at={E.note1.l} out={E.race.s - 10} rot={-2} />
          <Pen text="not one race" x={760} y={56} at={E.race.l} out={E.paper.s} rot={-2} />
          <Source>Illustration · before: Wang et al. 2023 · now: Ren et al. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B608" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
