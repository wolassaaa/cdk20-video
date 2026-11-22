// HKBU SCIE1007 课程作业的科普视频：B 档 6-01（第 6 章第一页）"So, the big question. How much did the computers actually help? Let's line up before and now."
// 规则 v2 重做：整页是第 6 章共用的实体翻牌记分板（board6.jsx）。开头 T2 甩进 + T6 光扫；board：平躺在台面上的记分板绕底边立起来（≥ 18 帧连续翻转）；
// title：板一立起来顶栏 37 块字牌就开始哗哗乱翻，每个词的字牌停在念到这个词的那一帧（HOW MUCH DID COMPUTERS ACTUALLY HELP）；help：问号牌翻成红色；
// cols：四行的翻牌槽和左右凹位一行行推出来；before / now：两块栏头翻出 BEFORE、NOW（NOW 的蓝框亮起）；段尾镜头推向第 1 行，T2 往左甩出（6-02 接着填第 1 行）。
// 全程机位慢推（0.92 → 1.0），空白牌在 cols、before、now 各轻抖一次（待命）。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-01.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {Stage, Source, evMapB, whipX, impact, T6Sweep} from "./bkit.jsx";
import {useGsapTimeline} from "./gsapFrame.jsx";
import {Board6, FOCUS, TITLE} from "./board6.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 6;
const mix = (a, b, t) => a + (b - a) * t;
// 顶栏每个字牌落在它那个词开口的帧（Gemini 初审：标题整句一次翻出和声音对不上；actually 也上牌）
const wf = (k) => K.words.find((w) => w.key === k).f0;
const TLAND = (() => {
  const keys = ["how#1", "much#1", "did#1", "computers#1", "actually#1", "help#1"];
  const out = [];
  let wi = 0, j = 0;
  const words = TITLE.replace("?", "").trim().split(" ");
  for (const ch of TITLE) {
    if (ch === " ") { out.push(null); wi += 1; j = 0; continue; }
    if (ch === "?") { out.push(null); continue; }
    const L = words[wi].length;
    out.push(wf(keys[wi]) - (L - 1 - j));
    j += 1;
  }
  return out;
})();

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    S.stand = 0;
    tl.fromTo(S, {stand: 0}, {stand: 1, duration: (E.board.l - 14) / 60, ease: "back.out(1.25)", immediateRender: false}, 14 / 60);   // 立起：14 → board.l
    X.tw("push", 0, 1, 0, E.cols.s, "sine.inOut");
    X.tw("cols", 0, 1, E.cols.s, E.cols.l + 30, "power2.out");
    X.tw("focus", 0, 1, E.now.l + 4, LEN - 7, "power2.inOut");
  });
  const whip = f < 7 ? whipX(f, 0, "in", -1) : whipX(f, LEN - 7, "out", -1);
  const F0 = FOCUS(0, "B", 1.25);
  const z0 = mix(0.92, 1.0, S.push);
  const cam = {x: mix(960, F0.x, S.focus), y: mix(540, F0.y, S.focus), z: mix(z0, F0.z, S.focus)};
  const th = 62 * (1 - S.stand);
  const jig = f >= E.now.l ? E.now.l : f >= E.before.l ? E.before.l : f >= E.cols.l ? E.cols.l : null;
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} shakeX={impact(f, E.board.l)} over={<T6Sweep f={f} at={E.sweep.s} />}>
        <Layer id={["header", "cols", "board"]}>
          <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: "960px 880px", transform: `perspective(1900px) rotateX(${th.toFixed(2)}deg)`}}>
            <Board6 f={f} cam={cam} rise={Math.min(1, 0.35 + S.stand)} titleLand={TLAND} titleFrom={null} help={E.help.l + 8} hdr={{B: E.before.l, N: E.now.l - 3}} cols={S.cols}
                    rows={[false, false, false, false]} jig={jig} nowFrame={(f - E.now.l + 10) / 10} />
          </div>
        </Layer>
        <Layer id="txt" exempt>
          <Source>Illustration · before and now, as reported in the studies we reviewed</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B601" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
