// HKBU SCIE1007 课程作业的科普视频：B 档 6-02 "Seeing the lock. Before: hard lab experiments, and without a 3D shape, design was expensive, slow and difficult.
// Now: a free prediction, downloaded from a public database."
// 规则 v2：第 6 章翻牌记分板（board6.jsx），镜头推在第 1 行（行在画面上部，下面空着的几行盖暗纱当弹出台）。
// row1：行名 1. SEEING THE LOCK；lock：BEFORE 凹位里升起 CDK20 插座（"锁"），飞到行下面放大，标 CDK20 = the lock；
// before：栏头翻出 BEFORE，插座褪成一团磨砂的灰影（没解出来的结构，只知道个大概）；lab：结晶皿、样本管、X 光源和探测板滑进来（名牌 e.g. X-ray crystallography），
// 主翻牌 HARD LAB EXPERIMENTS；每做一次实验：管子往皿里倒一下 → 皿里多长出几粒晶体 → X 光打过晶体 → 探测板上多出一圈衍射点 → 灰影清楚一点点（但始终没解完）；
// exp / slow / diff：三块副翻牌依次翻出，每翻一块再做一次（又贵又慢）。
// now：BEFORE 的件缩回凹位，机位横移到 NOW 栏，栏头翻出 NOW；数据库机架滑进来，pred：FREE PREDICTION；dl：一串数据珠从机架流进 NOW 凹位上方，
// 蓝色预测模型（AlphaFold 带状模型贴图）从下往上一层层长出来——完整的三维形状；pub：PUBLIC DATABASE，机架的灯一格格亮；说完模型缩回凹位。T2 甩进、T2 甩出。
// Gemini 初审（11-21）改：去掉放大镜、红问号；栏头按词翻；PUBLIC DATABASE 提前到 public；数据珠不穿过模型；出处行跟着画面换。
// Gemini 二审（11-21）改：黑块拼图换成真的结构测定实验（结晶 + X 光衍射），没解出来的结构画成磨砂灰影。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-02.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Stage, Sprite, Slab, Label, Tag, Source, evMapB, whipX, impact, pathOf} from "./bkit.jsx";
import {useGsapTimeline, idle, rand} from "./gsapFrame.jsx";
import {Board6, FOCUS, POP, Dim, cell} from "./board6.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 6;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const wf = (k) => K.words.find((w) => w.key === k).f0;
const B = cell(0, "B").slot, N = cell(0, "N").slot;
const PB = POP(0, "B"), PN = POP(0, "N");
// BEFORE 版面（世界坐标；机位 z 1.6 对准 y 477，能用的竖向带 380–680）
const SOCK = {x: 1080, y: 515, w: 492};
const XS = {x: 215, y: 560, w: 96, h: 64};          // X 光源
const DISH = {x: 420, y: 590, w: 190};               // 结晶皿
const DET = {x: 600, y: 450, w: 200, h: 200};        // 探测板
const BEAM_Y = 592;
// 衍射点：四次实验各加一圈（同心环 + 抖动），位置在探测板内
const SPOTS = [...Array(64)].map((_, k) => {
  const ring = Math.floor(k / 16), a = (k % 16) / 16 * Math.PI * 2 + ring * 0.4 + (rand(k + 3) - 0.5) * 0.3;
  const r = 26 + ring * 19 + (rand(k + 11) - 0.5) * 8;
  return {x: DET.w / 2 + r * Math.cos(a), y: DET.h / 2 + r * Math.sin(a), s: 4 + rand(k + 5) * 5, ring};
});
const XTAL = [...Array(12)].map((_, k) => ({x: DISH.x - 55 + rand(k + 21) * 110, y: DISH.y - 28 + rand(k + 41) * 50, s: 9 + rand(k + 61) * 7, r: rand(k + 81) * 90}));

const Scene = () => {
  const f = useCurrentFrame();
  const L = wf("lock#1");
  const ATT = [E.lab.l - 6, E.exp.l - 6, E.slow.l - 6, E.diff.l - 6];     // 四次实验（倒一下）落在这几个词上
  const S = useGsapTimeline((tl, S, X) => {
    X.tw("push", 0, 1, 0, E.focus1.l + 16, "power2.inOut");
    X.tw("rise", 0, 1, L - 14, L, "power2.out");
    X.tw("popB", 0, 1, L, L + 30, "power3.inOut");
    X.tw("dark", 0, 1, E.no3d.s, E.shape.l, "power2.inOut");     // 说到 without a 3D shape 才褪成灰影（Gemini：早了）
    X.tw("lab", 0, 1, E.lab.s, E.lab.l - 8, "power2.out");
    ATT.forEach((a, k) => {
      X.tw(`pour${k}`, 0, 1, a - 16, a + 10, "sine.inOut");
      X.tw(`pc${k}`, 0, 1, a, a + 18, "power2.out");
    });
    X.tw("backB", 0, 1, E.now.s - 26, E.now.s + 4, "power2.inOut");
    X.tw("pan", 0, 1, E.now.s - 12, E.now.l + 12, "power2.inOut");
    X.tw("popN", 0, 1, E.now.l - 4, E.now.l + 18, "power3.out");
    X.tw("rack", 0, 1, E.now.l, E.pred.s, "power2.out");
    X.tw("dl", 0, 1, E.dl.s - 10, E.dl.l + 30, "power1.inOut");
    X.tw("grow", 0, 1, E.dl.s + 6, E.dl.l + 44, "power1.inOut");
    X.jiggle("afj", E.pub.l, 6, 0);
    X.tw("leds", 0, 1, E.pub.s, E.db.l, "none");
    X.tw("backN", 0, 1, E.db.l + 4, LEN - 12, "power2.inOut");
  });
  const whip = f < 7 ? whipX(f, 0, "in", -1) : whipX(f, LEN - 7, "out", -1);
  const FB = FOCUS(0, "B"), FN = FOCUS(0, "N"), F0 = FOCUS(0, "B", 1.25);
  const drift = 0.05 * (f / LEN);
  const cam = {x: 960, y: 550-24*S.pan, z: 1.015 + .002*drift};
  const id = (s) => idle(f, s, {rot: 0.8, bob: 1.8});
  const popB = S.popB * (1 - S.backB), popN = S.popN * (1 - S.backN);
  const sock = {x: mix(B.cx, SOCK.x, popB), y: mix(B.cy - 8 * S.rise, SOCK.y, popB), w: mix(118, SOCK.w, popB)};
  const pour = ATT.reduce((m, _, k) => Math.max(m, Math.sin(Math.PI * (S[`pour${k}`] || 0))), 0);
  const done = ATT.reduce((m, _, k) => m + (S[`pc${k}`] || 0), 0);        // 做完了几次（0–4，连续）
  const scatter = Math.max(0,Math.min(1,(f-E.diff.s)/Math.max(1,E.diff.l-E.diff.s)));
  const beam = ATT.reduce((m, _, k) => Math.max(m, Math.sin(Math.PI * (S[`pc${k}`] || 0))), 0);
  const rig = S.lab * popB;
  const AFP = {x: PN.x + 120, y: PN.y - 40, w: 250};
  const af = {x: mix(N.cx, AFP.x, popN), y: mix(N.cy, AFP.y, popN), w: mix(104, AFP.w, popN)};
  const RK = {x: PN.x - 200, y: PN.y + 40};
  const path = pathOf([[RK.x + 60, RK.y - 70], [mix(RK.x, AFP.x, 0.45), RK.y - 120], [AFP.x - 60, AFP.y + 150]]);
  const beads = [...Array(12)].map((_, k) => {
    const u = S.dl * 1.7 - k * 0.06;
    if (u <= 0 || u >= 1 || popN < 0.5) return null;
    const [x, y] = path.at(u);
    return <div key={k} style={{position: "absolute", left: x - 9, top: y - 9, width: 18, height: 18, borderRadius: 9, background: C.blueHi, opacity: 1 - Math.max(0, (u - 0.85) / 0.15),
                                 boxShadow: "0 3px 4px rgba(0,0,0,0.45), inset 0 3px 3px rgba(255,255,255,0.55)"}} />;
  });
  // 插座：没解出来的结构 = 磨砂灰影，每做一次实验清楚一点（模糊 11 → 5 px，始终没解完）
  const blurPx = S.dark * (11 - 1.5 * done);
  const darkF = `grayscale(${S.dark.toFixed(3)}) brightness(${(1 + 0.35 * S.dark).toFixed(3)}) blur(${blurPx.toFixed(1)}px)`;
  const grown = S.backN > 0 ? 1 : S.grow;
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} shakeX={impact(f, E.pred.l)}>
        <Layer id={["board", "before1", "tags1", "now1"]}>
          <Board6 f={f} cam={cam} title={-999} help={-999} hdr={{B: E.bef.l, N: E.now.l}} cols={1}
                  rows={[{name: L, B: E.lab.l, Bs: [E.exp.l, E.slow.l, E.diff.l], N: E.pred.l, Ns: [E.pub.l]}, false, false, false]}
                  lit={{"0B": cl((f - E.focus1.s) / 12) * (1 - S.pan), "0N": S.pan}}>
            <Dim i={0} v={Math.max(popB, popN, S.push * 0.6)} />
            {S.rise > 0.01 && (
              <Sprite name="socket/hero_34" x={sock.x} y={sock.y + id(1).y} w={sock.w} op={cl(S.rise * 2) * (1 - 0.4 * S.dark + 0.06 * done)} rot={id(1).r} shadow={popB > 0.5 && S.dark < 0.5}
                      style={{filter: S.dark > 0.001 ? darkF : undefined}} />
            )}
            {/* BEFORE：结构测定实验——结晶皿 + 样本管 + X 光源 + 探测板（衍射点一圈圈多起来） */}
            {rig > 0.01 && (
              <div style={{position: "absolute", left: 0, top: 0, opacity: cl(rig * 2), transform: `translateX(${(-220 * (1 - S.lab)).toFixed(1)}px)`}}>
                <Slab x={XS.x - XS.w / 2} y={XS.y} w={XS.w} h={XS.h} r={10} color={C.black} depth={8} id="xsrc">
                  <div style={{position: "absolute", right: 8, top: XS.h / 2 - 7, width: 14, height: 14, borderRadius: 7, background: C.blueHi, opacity: 0.4 + 0.6 * beam,
                               boxShadow: `0 0 ${(6 + 14 * beam).toFixed(0)}px rgba(61,107,230,0.9)`}} />
                </Slab>
                {f>=E.exp.s&&<Sprite name="coins/34" x={XS.x+72} y={XS.y+113-60*(1-cl((f-E.exp.s)/Math.max(1,E.exp.l-E.exp.s)))} w={98} op={cl((f-E.exp.s)/6)}/>}
                <Sprite name="dish/34" x={DISH.x} y={DISH.y} w={DISH.w} rot={-3} />
                {XTAL.map((c, k) => k < done * 3 && (
                  <div key={k} style={{position: "absolute", left: c.x - c.s / 2, top: c.y - c.s / 2, width: c.s, height: c.s, transform: `rotate(45deg) scale(${cl(done * 3 - k).toFixed(2)})`,
                                       background: `linear-gradient(135deg, ${C.inkLight}, ${C.blueHi} 60%, ${C.blue})`, boxShadow: "0 1px 2px rgba(0,0,0,0.5)", opacity: 0.95}} />
                ))}
                <Sprite name="tube/34" x={DISH.x - 70} y={DISH.y - 120 - 30 * pour} w={120} rot={8 - 38 * pour} />
                {beam > 0.02 && (
                  <div style={{position: "absolute", left: XS.x + XS.w / 2, top: BEAM_Y - 4, width: DET.x + DET.w / 2 - XS.x - XS.w / 2, height: 8, borderRadius: 4,
                               background: "linear-gradient(90deg, rgba(120,160,255,0.95), rgba(120,160,255,0.35))", opacity: beam, boxShadow: "0 0 16px rgba(61,107,230,0.9)"}} />
                )}
                <Slab x={DET.x} y={DET.y} w={DET.w} h={DET.h} r={12} color={C.black} depth={10} id="det">
                  <div style={{position: "absolute", left: DET.w / 2 - 6, top: DET.h / 2 - 6, width: 12, height: 12, borderRadius: 6, background: C.black, boxShadow: "0 0 0 2px #333"}} />
                  {SPOTS.map((p, k) => {
                    const v = cl(done * 16 - k);
                    return v > 0 && <div key={k} style={{position: "absolute", left: p.x + scatter*22*Math.sin(k*11) - p.s / 2, top: p.y + scatter*21*Math.cos(k*9) - p.s / 2, width: p.s, height: p.s, borderRadius: p.s,
                                                         background: C.inkLight, opacity: v * (0.55 + 0.45 * rand(k + 7)), boxShadow: `0 0 ${(4 + 6 * beam).toFixed(0)}px rgba(160,190,255,0.9)`}} />;
                  })}
                </Slab>
                <Tag x={XS.x} y={690} op={cl(rig * 2)}>X-rays</Tag>
                <Tag x={DISH.x} y={690} op={cl(rig * 2)}>crystals</Tag>
                <Tag x={DET.x + DET.w / 2} y={690} op={cl(rig * 2)}>pattern</Tag>
                <Tag x={DET.x + DET.w / 2 - 40} y={DET.y - 118} op={cl(S.lab * 3 - 2) * cl(popB * 3 - 2)} on="det">e.g. X-ray crystallography</Tag>
              </div>
            )}
            {/* NOW：数据库机架 + 数据珠 + 从下往上长出来的蓝色预测模型 */}
            {S.rack > 0.01 && popN > 0.05 && <Sprite name="dbrack/34" x={RK.x} y={RK.y + 30 * (1 - S.rack)} w={300 * popN} op={cl(S.rack * 2) * popN} />}
            {/* 下载进度条：机架下面一条骨白槽，蓝色一格格填满（从公开数据库下载） */}
            {S.dl > 0.01 && popN > 0.3 && (
              <Slab x={RK.x-135-90*S.dl} y={RK.y-86} w={270} h={132} r={14} color={C.bone} depth={8} op={cl(S.dl*4)*popN} id="predictionCard"/>
            )}
            {grown > 0.001 && (
              <Sprite name="af/front305" x={S.backN > 0 ? af.x : mix(RK.x + 40, af.x, grown)} y={(S.backN > 0 ? af.y : mix(RK.y - 60, af.y, grown)) + id(2).y - (S.afj || 0)}
                      w={S.backN > 0 ? af.w : af.w * (0.2 + 0.8 * grown)} rot={id(2).r} shadow={popN > 0.5} op={cl(grown * 4)} rim={S.grow > 0 && S.grow < 1 ? 0.7 : 0} />
            )}
            {false && [0, 1, 2, 3, 4].map((k) => (
              <div key={k} style={{position: "absolute", left: RK.x - 80 + k * 36, top: RK.y - 112, width: 14, height: 14, borderRadius: 7, background: C.blueHi,
                                   opacity: cl(S.leds * 5 - k) * (0.6 + 0.4 * Math.sin(f / 5 + k)) * popN, boxShadow: "0 0 10px rgba(61,107,230,0.9)"}} />
            ))}
          </Board6>
        </Layer>
        <Layer id="txt" exempt>
          <Label text="CDK20, the lock" size={44} x={1500} y={860} at={L + 18} out={E.lab.s} align="center" />
          <Source>{f < E.now.s ? f < E.lab.s ? "Illustration · CDK20 drawn as a lock" : "Illustration · lab structure methods, e.g. X-ray crystallography" : "Illustration · prediction from AlphaFold DB v6 (free, public)"}</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B602" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
