// HKBU SCIE1007 课程作业的科普视频：B 档 4-03（C 画外音）"But look closer."
// But look closer：左边 AlphaFold 预测模型（按可信度上色，红色是低可信度），放大镜扣到红尾巴上（放大镜里是同一张贴图，按原图分辨率显示）；
// One end of the protein：右边 CDK20 插座正面滑进来，左上角长出一串红珠子（尾巴），a floppy tail 时晃；really low confidence：标 low confidence；
// in the model it lay across the keyhole：尾巴甩过来横搭在插孔上；one building block：一颗珠子亮一圈；sitting inside the ATP pocket：它落进孔里，标 ATP pocket；
// trust it blindly：模型和放大镜往左收走；cut keys：左边冲出三个金插头；for a blocked door：中间那个飞向插孔，被尾巴挡回来（T7）。
// 接点：开头 T2 从右甩进（4-02 是 B 页），结尾 T5 料杆擦除（4-04+05 出镜段）。L0 第 4 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame, Img, staticFile} from "remotion";
import K from "./keys_4-03.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, SERIF, Tag, camBreath, shade, tint, Stage, Sprite, Label, Pen, Source, anchorOf, pathOf, evMapB, T5Out, whipX, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 4;

// 预测模型：贴图 960×1061，红尾巴重心在贴图 (486, 244)
const AF = {x: 513, y: 514, w: 507}, AF_SRC = {w: 960, h: 1061}, TAIL_SRC = [486, 244];
const afK = AF.w / AF_SRC.w;
const TAIL_SCR = [AF.x + (TAIL_SRC[0] - AF_SRC.w / 2) * afK, AF.y + (TAIL_SRC[1] - AF_SRC.h / 2) * afK];
const LOUPE_R = 165, LOUPE_W = 760;                         // 放大镜里的贴图宽（≤ 原图 0.8 倍）
// 插座正面：贴图 1312×1020，插孔中心 = mouth 锚点，孔半径约 205 px（贴图）
const SOCK = {x: 1320, y: 515, w: 672};
const sk = SOCK.w / 1312;
const [mdx, mdy] = anchorOf("socket/hero_face", "mouth", SOCK.w);
const M = [SOCK.x + mdx, SOCK.y + mdy];
const HOLE_R = 205 * sk;
// 红尾巴：一串珠子，挂在插座左上角
const N = 17, BR = 15, SP = 27;
const A = [1068, 340];
const HANG = pathOf([A, [1020, 390], [985, 460], [975, 540], [980, 620], [965, 700], [950, 770]]);
const ACROSS = pathOf([A, [1130, 330], [1220, 398], [1298, 452], [M[0], M[1] + 2], [M[0] + 78, M[1]], [M[0] + 140, M[1] - 26]]);
const hangAt = (i) => HANG.at((i * SP) / HANG.length);
const acrossAt = (i) => ACROSS.at((i * SP) / ACROSS.length);
const KB = (() => { let b = 0, d = 1e9; for (let i = 0; i < N; i++) { const p = acrossAt(i), q = Math.hypot(p[0] - M[0], p[1] - M[1]); if (q < d) { d = q; b = i; } } return b; })();
// 三把金插头（侧面图翻过来，尖朝右）
const KEYS = [[300, 470], [560, 560], [300, 650]];
const KEY_W = 260;
// 飞的那把：尖朝右（翻过来的侧面图），尖顶到尾巴上（孔心左边一点）就被挡回
const [tipOX, tipOY] = anchorOf("plug/048_34", "tip", KEY_W);
const STOP = [M[0] - 62, M[1] + 4];
const FLY = pathOf([[KEYS[1][0] - tipOX, KEYS[1][1] + tipOY], [880, 560], [1120, 500], STOP]);

const clamp01 = (v) => Math.max(0, Math.min(1, v));
const sm = (a, b, v) => { const t = clamp01((v - a) / (b - a)); return t * t * (3 - 2 * t); };
const mix = (a, b, t) => a + (b - a) * t;

const TailBead = ({x, y, r, k = 0, ring = 0}) => (
  <g>
    <ellipse cx={x + 2} cy={y + r * 0.9} rx={r * 0.95} ry={r * 0.32} fill="rgba(40,30,20,0.22)" />
    <circle cx={x} cy={y} r={r} fill={k > 0.01 ? "url(#beadDeep)" : "url(#bead)"} />
    <ellipse cx={x - r * 0.32} cy={y - r * 0.38} rx={r * 0.34} ry={r * 0.22} fill="rgba(255,255,255,0.75)" />
    {ring > 0.01 && <circle cx={x} cy={y} r={r + 7} fill="none" stroke={C.bone} strokeWidth={5} opacity={ring} />}
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("af", 0, 1, E.af.l, {antic: false});
    X.land("lp", 0, 1, E.closer.l);
    X.land("sock", 0, 1, E.sock.l);
    X.tw("tail", 0, 1, E.tail.s, E.tail.e, "power2.out");
    X.tw("model", 0, 1, E.model.s, E.model.e, "power2.inOut");
    X.tw("lay", 0, 1, E.lay.s, E.lay.l, "power2.inOut");
    X.jiggle("layJ", E.lay.l, 6, 0);
    X.tw("block", 0, 1, E.block.s, E.block.l + 8, "back.out(1.6)");
    X.tw("inside", 0, 1, E.inside.s - 4, E.inside.l, "power1.inOut");
    X.jiggle("inJ", E.inside.l, 4, 0);
    X.land("atp", 0, 1, E.atp.l, {antic: false});
    X.tw("clear", 0, 1, E.trust.s - 8, E.trust.e, "power3.in");
    X.group(KEYS.map((_, i) => `k${i}`), 0, 1, E.cut.l, {step: RULE.stagger});
    X.tw("go", 0, 1, E.go.s - 6, E.go.l, "power2.in");
    X.tw("back", 0, 1, E.go.l, Math.min(E.go.e, LEN - 22), "power2.out");
    X.jiggle("hitJ", E.go.l, 9, 0);
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const whip = f < 7 ? whipX(f, 0, "in", -1) : 0;
  const shake = impact(f, E.go.l);
  const clearX = -1400 * S.clear;

  // 放大镜：从右上落到尾巴上，trust 时跟模型一起往左收走
  const lpP = Math.min(1, S.lp);
  // 放大镜落定后在尾巴上方慢慢打小圈（看的动作），别停住（Gemini 初审：2–6 秒不动）
  const look = lpP >= 1 ? 1 : 0;
  const lc = [mix(TAIL_SCR[0] + 420, TAIL_SCR[0], lpP) + clearX + look * 10 * Math.sin((2 * Math.PI * f) / 150), mix(TAIL_SCR[1] - 360, TAIL_SCR[1], lpP) + id(2).y + look * 7 * Math.cos((2 * Math.PI * f) / 150)];
  const lpS = (0.7 + 0.3 * S.lp) * (1 + 0.05 * Math.sin(Math.PI * S.model));
  const big = LOUPE_W / AF_SRC.w;
  const bigC = [lc[0] - (TAIL_SRC[0] - AF_SRC.w / 2) * big, lc[1] - (TAIL_SRC[1] - AF_SRC.h / 2) * big];

  // 尾巴：flop 包络（floppy 时大晃，之后慢慢收），横搭以后只剩一点余晃
  const flop = 0.12 + 0.88 * sm(E.floppy.s, E.floppy.l + 6, f) * (1 - sm(E.floppy.e + 4, E.low.l, f));
  const beads = [...Array(N)].map((_, i) => {
    const u = i / (N - 1);
    const h = hangAt(i), a = acrossAt(i);
    const sway = (6 + 34 * flop) * Math.pow(u, 1.4) * Math.sin((2 * Math.PI * (f - E.tail.s)) / 52 - i * 0.42);
    const t = clamp01(S.lay * 1.35 - (1 - u) * 0.35);
    const te = t * t * (3 - 2 * t);
    let x = mix(h[0] + sway, a[0] + 3 * u * Math.sin((2 * Math.PI * f) / 90 - i * 0.5) * (1 - S.inside), te);
    let y = mix(h[1], a[1], te) - 70 * Math.sin(Math.PI * te) * u + (S.layJ || 0) * u;
    let r = BR;
    // 落进孔里：这颗到孔心并缩小（往里走），两边的珠子跟着往下坠一点
    const din = S.inside, dk = i - KB;
    if (i === KB) { x = mix(x, M[0], din); y = mix(y, M[1], din) - 40 * Math.sin(Math.PI * din) + (S.inJ || 0); r = BR * (1 + 0.32 * Math.sin(Math.PI * Math.min(1, S.block)) * (1 - din)) * (1 - 0.12 * din); }
    else y += 16 * din * Math.exp(-(dk * dk) / 4) + (S.hitJ || 0) * Math.exp(-(dk * dk) / 6);
    const vis = clamp01(S.tail * (N + 3) - i);
    return {x, y, r: r * gsapBack(vis), on: vis > 0.01, i};
  });

  // low confidence 那段：一道亮圈从尾巴根跑到尖，来回两趟
  const lowRun = (i) => {
    if (f < E.low.s || f > E.lay.s) return 0;
    const ph = ((f - E.low.s) / 40) % 1, pos = ph * (N + 4) - 2;
    return 0.85 * Math.max(0, 1 - Math.abs(i - pos) / 2.2) * sm(E.low.s, E.low.s + 8, f) * (1 - sm(E.lay.s - 10, E.lay.s, f));
  };
  // 落进孔里的那颗：一直一明一暗地圈着，直到三把插头出来
  const kbPulse = f > E.inside.l && f < E.cut.s ? 0.35 + 0.35 * Math.sin((2 * Math.PI * (f - E.inside.l)) / 40) : 0;

  // 金插头飞向插孔，被挡回来
  const fp = FLY.at(S.go);
  // 尖的位置：先沿路飞到挡点，再被弹回左下并翘起
  const tipX = mix(fp[0], STOP[0] - 260, S.back), tipY = mix(fp[1], STOP[1] + 90, S.back) - 90 * Math.sin(Math.PI * S.back);
  const plugRot = mix(0, -28, S.back) + (S.go < 1 ? 4 * Math.sin(Math.PI * S.go) : 0);

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} zoom={1+.35*sm(E.closer.s,E.closer.l,f)*(1-sm(E.model.s,E.model.e,f))} zoomAt={[AF.x,355]} cam={camBreath(f, K, ["s1","s3","s4"], 32)} whip={whip} shakeX={shake} shakeY={shake * 0.5} over={<T5Out name="runner" f={f} len={LEN} />}>
        <Layer id="af">
          {S.af > 0.01 && <Sprite name="af/front305" x={AF.x + clearX} y={AF.y + id(1).y - 30 * (1 - Math.min(1, S.af))} w={AF.w} op={Math.min(1, S.af * 1.5)} rot={id(1).r} />}
        </Layer>

        <Layer id="socket">
          {S.sock > 0.01 && <Sprite name="socket/hero_face" x={mix(2300, SOCK.x, S.sock)} y={SOCK.y + id(3).y} w={SOCK.w} />}
        </Layer>

        <Layer id="keys">
          {KEYS.map(([x, y], i) => {
            const a = S[`k${i}`];
            if (a <= 0.01) return null;
            if (i === 1 && S.go > 0.001) return null;
            return <Sprite key={i} name="plug/048_34" x={x - 60 * (1 - Math.min(1, a))} y={y + id(6 + i).y} w={KEY_W} sx={-1} op={Math.min(1, a * 1.6)} rot={id(6 + i).r} />;
          })}
          {S.go > 0.001 && (
            <Sprite name="plug/048_34" x={tipX + tipOX} y={tipY - tipOY} w={KEY_W} sx={-1} rot={plugRot} lift={24 * Math.sin(Math.PI * S.go) * (1 - S.back)} />
          )}
        </Layer>

        <Layer id="tail">
          <svg width={1920} height={1080} style={{position: "absolute", left: mix(940, 0, Math.min(1, S.sock)), top: id(3).y, overflow: "visible"}}>
            <defs>
              <radialGradient id="bead" cx="0.38" cy="0.34" r="0.7">
                <stop offset="0" stopColor={tint(C.red, 0.35)} />
                <stop offset="0.55" stopColor={C.red} />
                <stop offset="1" stopColor={shade(C.red, 0.38)} />
              </radialGradient>
              <radialGradient id="beadDeep" cx="0.38" cy="0.34" r="0.7">
                <stop offset="0" stopColor={tint(C.red, 0.15)} />
                <stop offset="0.55" stopColor={shade(C.red, 0.2)} />
                <stop offset="1" stopColor={shade(C.red, 0.55)} />
              </radialGradient>
            </defs>
            {S.atp > 0.01 && <circle cx={M[0]} cy={M[1]} r={HOLE_R * 0.62 * (0.8 + 0.2 * Math.min(1, S.atp))} fill={C.bone} opacity={0.42 * Math.min(1, S.atp)} />}
            {S.inside > 0.01 && <circle cx={M[0]} cy={M[1]} r={BR * 1.25} fill="rgba(20,14,8,0.35)" opacity={S.inside} />}
            {beads.filter((b) => b.on).map((b, j, arr) => j > 0 && (
              <line key={`l${b.i}`} x1={arr[j - 1].x} y1={arr[j - 1].y} x2={b.x} y2={b.y} stroke={shade(C.red, 0.3)} strokeWidth={7} strokeLinecap="round" />
            ))}
            {beads.filter((b) => b.on && b.i !== KB).map((b) => <TailBead key={b.i} x={b.x} y={b.y} r={b.r} ring={lowRun(b.i)} />)}
            {beads[KB].on && <TailBead x={beads[KB].x} y={beads[KB].y} r={beads[KB].r} k={S.inside} ring={Math.max(lowRun(KB), clamp01(S.block * 1.4) * (1 - S.inside), kbPulse)} />}
          </svg>
        </Layer>


        <Layer id="loupe">
          {S.lp > 0.01 && (
            <div style={{position: "absolute", left: lc[0], top: lc[1], width: 0, height: 0, transform: `scale(${lpS})`, opacity: Math.min(1, S.lp * 1.6)}}>
              {/* 柄 */}
              <div style={{position: "absolute", left: LOUPE_R * 0.62, top: LOUPE_R * 0.62, width: 150, height: 34, borderRadius: 17, background: C.bone,
                           transform: "rotate(45deg)", transformOrigin: "0 50%", boxShadow: `0 10px 14px rgba(40,30,20,0.25), inset 0 -6px 0 ${shade(C.bone, 0.22)}`}} />
              {/* 镜片：同一张模型贴图放大，裁成圆 */}
              <div style={{position: "absolute", left: -LOUPE_R, top: -LOUPE_R, width: 2 * LOUPE_R, height: 2 * LOUPE_R, borderRadius: LOUPE_R, overflow: "hidden",
                           background: tint(C.table, 0.4)}}>
                <Img src={staticFile("bsprite/af/front305.png")}
                     style={{position: "absolute", left: bigC[0] - lc[0] + LOUPE_R - LOUPE_W / 2, top: bigC[1] - lc[1] + LOUPE_R - (LOUPE_W * AF_SRC.h) / AF_SRC.w / 2,
                             width: LOUPE_W, height: (LOUPE_W * AF_SRC.h) / AF_SRC.w, filter: `brightness(${1 + 0.18 * Math.sin(Math.PI * S.model)})`}} />
                <div style={{position: "absolute", inset: 0, borderRadius: LOUPE_R, background: "radial-gradient(circle at 32% 28%, rgba(255,255,255,0.35), rgba(255,255,255,0) 45%)"}} />
              </div>
              {/* 框 */}
              <div style={{position: "absolute", left: -LOUPE_R - 14, top: -LOUPE_R - 14, width: 2 * LOUPE_R + 28, height: 2 * LOUPE_R + 28, borderRadius: LOUPE_R + 14,
                           border: `14px solid ${C.bone}`, boxSizing: "border-box",
                           boxShadow: `0 14px 22px rgba(40,30,20,0.28), inset 0 3px 0 rgba(255,255,255,0.7), 0 -2px 0 ${shade(C.bone, 0.22)} inset`}} />
            </div>
          )}
        </Layer>

        <Layer id="txt" exempt>
          <Label text="floppy tail" size={52} x={840} y={190} at={E.floppy.l} out={E.lay.s} align="center" />
          <Label text="low confidence" size={60} x={890} y={770} at={E.low.l} out={E.lay.s} align="center" />
          <Label text="ATP pocket" size={52} x={M[0]} y={790} at={E.atp.l} out={E.cut.s} align="center" />
          <Pen text="blocked" x={1500} y={170} at={E.go.l - 8} dur={14} size={76} />
          <Source>{f < E.trust.e ? "Illustration · data: Ren et al., Chem. Sci. 2023 · predicted model (AlphaFold DB v6)" : "Illustration · data: Ren et al., Chem. Sci. 2023"}</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

// 珠子长出来：back.out 的形状（帧值直接算，不另开补间）
function gsapBack(v) {
  if (v <= 0) return 0;
  if (v >= 1) return 1;
  const s = 1.6, t = v - 1;
  return t * t * ((s + 1) * t + s) + 1;
}

const Root = () => <Composition id="B403" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
