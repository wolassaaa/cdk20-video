// HKBU SCIE1007 课程作业的科普视频：人出镜样片 2-02（A 出镜，研究问题那一句）。
// 版式照 全局统筹_板件与资产_v1 第四节：人在左，身后是同一块大板的近景，右边是讲解位。
// 这条样片测两件事（导演 11-18）：① 零件从肩后绕到身前（靠抠像通道分前后层）；② 零件跟着手和头走（靠程序跟踪，不用 AE）。
// 跟踪数据：G:/cdk20/work/track/2-02_landmarks.json（mediapipe，已平滑），连同素材时间轴上的词帧导出成 track_2-02.json。
// 画面和声音都是素材原速 639 帧，不变速。
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/manual/OnCam202.jsx OnCam202 <帧目录> --sequence --public-dir=<映射/_cache/oc202/public>
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, Img, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import T from "./track_2-02.json";

const PAPER = "#EDE9DF", INK = "#1F1E1C", SOFT = "#6E6B63", RED = "#C8102E";
const W = Object.fromEntries(T.words.map((w, i) => [i + 1, w]));
const ease = Easing.bezier(0.33, 0, 0.2, 1);
const out = Easing.out(Easing.cubic);
const io = Easing.inOut(Easing.cubic);
const span = (f, a, b, fn = (x) => x) => (f <= a ? 0 : f >= b ? 1 : fn((f - a) / Math.max(1, b - a)));
const mix = (a, b, p) => a + (b - a) * p;

const fh = typeof window !== "undefined" ? delayRender("fonts") : null;
if (typeof window !== "undefined") {
  Promise.all([["Serif", "InstrumentSerif-Regular.ttf", "normal"], ["Serif", "InstrumentSerif-Italic.ttf", "italic"], ["Hand", "Caveat.ttf", "normal"]]
    .map(([n, file, st]) => new FontFace(n, `url(${staticFile("fonts/" + file)})`, {style: st}).load().then((x) => document.fonts.add(x))))
    .then(() => continueRender(fh)).catch(() => continueRender(fh));
}

// 人物摆位：素材 3328×1872 缩到 1728×972，底边贴画面底，人的中线在画面宽度约三分之一处
const SC = 1728 / T.src[0], PX = -301, PY = 108;
const at = (arr, f) => {                       // 素材坐标 → 画面坐标；帧可为小数；丢点时用最近的有效点
  const n = arr.length, c = Math.max(0, Math.min(n - 1, f));
  const g = (i) => { let j = i; while (j < n - 1 && !arr[j]) j++; while (j > 0 && !arr[j]) j--; return arr[j]; };
  const a = g(Math.floor(c)), b = g(Math.ceil(c)), t = c - Math.floor(c);
  return [mix(a[0], b[0], t) * SC + PX, mix(a[1], b[1], t) * SC + PY];
};
// 跟踪平滑：先补齐丢点，再做高斯平滑（导演 11-18：跟得太灵敏，手一动幅度太大）
const fill = (arr) => { const o = []; let last = arr.find(Boolean); for (const p of arr) { if (p) last = p; o.push(last); } return o; };
const gauss = (arr, sig) => { const a = fill(arr), n = a.length, R = Math.ceil(sig * 3), o = [];
  for (let i = 0; i < n; i++) { let x = 0, y = 0, w = 0; for (let k = -R; k <= R; k++) { const j = Math.max(0, Math.min(n - 1, i + k)), g = Math.exp(-(k * k) / (2 * sig * sig)); x += a[j][0] * g; y += a[j][1] * g; w += g; } o.push([x / w, y / w]); }
  return o; };
const NOSE_S = gauss(T.nose, 10), PALM_S = gauss(T.palm_l, 8), SH_S = gauss(T.shoulder_l, 14);
const PALM_M = (() => { const a = PALM_S.slice(T.words[13].f0); let x = 0, y = 0; for (const p of a) { x += p[0]; y += p[1]; } return [x / a.length, y / a.length]; })();
const FOLLOW = 0.6, HEAD = 0.2;
const NOSE0 = (() => { let x = 0, y = 0, n = 0; for (const p of T.nose) if (p) { x += p[0]; y += p[1]; n++; } return [(x / n) * SC + PX, (y / n) * SC + PY]; })();

const Tag = ({n, x, y, at: a, f}) => {
  const p = span(f, a, a + 6, out);
  return p <= 0 ? null : (
    <div style={{position: "absolute", left: x - 25, top: y - 25, width: 50, height: 50, borderRadius: 25, border: `2.5px solid ${INK}`, boxSizing: "border-box",
                 font: "30px/45px Serif", textAlign: "center", color: INK, opacity: p, transform: `scale(${1.25 - 0.25 * p})`, background: PAPER}}>{n}</div>
  );
};

const Scene = () => {
  const f = useCurrentFrame();
  // ---- 跟头：讲解位的东西按头的摆动带一点（0.35 倍），像和人处在同一个空间 ----
  const nose = at(NOSE_S, f);
  const hx = (nose[0] - NOSE0[0]) * HEAD, hy = (nose[1] - NOSE0[1]) * HEAD;

  // ---- 字牌：research question ----
  const pl = span(f, W[3].f0 - 2, W[3].f0 + 14, out);
  const plBump = f > W[3].f0 + 14 ? 0.03 * Math.exp(-(f - W[3].f0 - 14) / 5) * Math.cos((f - W[3].f0 - 14) / 3) : 0;
  const wr = span(f, W[3].f0 + 4, W[4].f1);

  // ---- 芯片：computer-aided methods ----
  const cAt = W[8].f0;
  const cl = span(f, cAt - 2, cAt + 10, out), cc = span(f, cAt + 3, cAt + 27, Easing.inOut(Easing.quad));
  const cr = cc * 150;
  const cBump = f > cAt + 27 ? 0.03 * Math.exp(-(f - cAt - 27) / 5) * Math.cos((f - cAt - 27) / 3.2) : 0;
  const bob = Math.sin(f / 31) * 5;

  // ---- 钥匙：find 时从肩后出来，assess 时落到手心上方并跟着手走 ----
  const sh = at(SH_S, f);
  const pr = at(PALM_S, f), pm = [PALM_M[0] * SC + PX, PALM_M[1] * SC + PY];
  const palm = [mix(pm[0], pr[0], FOLLOW), mix(pm[1], pr[1], FOLLOW)];
  const k0 = [sh[0] - 70, sh[1] + 40];                          // 藏在肩后
  const k1 = [1255 + hx, 452 + hy + Math.sin(f / 23) * 6];      // 浮在讲解位，和眼睛差不多高
  const k2 = [palm[0] + 6, palm[1] - 235 + Math.sin(f / 19) * 4];   // 手心上方
  const a = span(f, W[12].f0 - 6, W[12].f0 + 30, io);           // 肩后 → 讲解位
  const b = span(f, W[14].f0 - 4, W[14].f0 + 34, io);           // 讲解位 → 手心上方
  const arcUp = Math.sin(Math.PI * a) * -70 + Math.sin(Math.PI * b) * -40;
  const kx = mix(mix(k0[0], k1[0], a), k2[0], b);
  const ky = mix(mix(k0[1], k1[1], a), k2[1], b) + arcUp;
  const ks = mix(mix(0.55, 1, a), 0.8, b);
  const kShow = f >= W[12].f0 - 6;
  const front = kx > 1190 || b > 0;                             // 完全出了人的轮廓才换到前层
  const kf = String(Math.floor((f * 0.8 + 36) % 240)).padStart(4, "0");
  const settle = f > W[14].f0 + 34 ? Math.exp(-(f - W[14].f0 - 34) / 7) * Math.cos((f - W[14].f0 - 34) / 3.4) * 10 : 0;
  const Key = (
    <Img src={staticFile(`key/${kf}.png`)} style={{position: "absolute", left: kx - 320, top: ky - 320 + settle, width: 640, height: 640,
         transform: `scale(${ks}) rotate(${mix(-24, 0, a) + mix(0, -8, b)}deg)`, filter: "drop-shadow(0 26px 18px rgba(60,40,10,0.28))"}} />
  );

  // ---- help scientists：芯片 → 人 的手画箭头 ----
  const ar = span(f, W[10].f0 - 2, W[11].f0 + 14, ease);
  const arOut = 1 - span(f, W[12].f0 + 20, W[12].f0 + 40);
  const head = [nose[0] + 210, nose[1] - 40];

  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("2-02.wav")} />
      <Img src={staticFile("bg.jpg")} style={{position: "absolute", width: 1920, height: 1080}} />
      <AbsoluteFill style={{background: "linear-gradient(90deg, rgba(237,233,223,0.0) 0%, rgba(237,233,223,0.42) 62%, rgba(237,233,223,0.6) 100%)"}} />

      {kShow && !front && Key}
      <Img src={staticFile(`person/${String(Math.min(f, T.len_f - 1)).padStart(4, "0")}.png`)} style={{position: "absolute", left: PX, top: PY, width: 1728, height: 972}} />

      {/* 字牌 */}
      <div style={{position: "absolute", left: 1090 + hx, top: 112 + hy, width: 640, height: 116, borderRadius: 14, opacity: span(f, W[3].f0 - 2, W[3].f0 + 4),
                   transform: `translateY(${(1 - pl) * 46}px) scale(${0.96 + 0.04 * pl + plBump})`,
                   background: "linear-gradient(180deg,#FBF9F4 0%,#F3EFE6 55%,#E6E0D3 100%)",
                   boxShadow: "inset 0 2px 0 rgba(255,255,255,0.95), inset 0 -10px 16px rgba(0,0,0,0.06), 0 22px 26px rgba(60,45,20,0.22)"}}>
        <div style={{position: "absolute", left: 0, top: 0, width: 640, textAlign: "center", fontSize: 70, lineHeight: "112px", fontStyle: "italic",
                     WebkitMaskImage: `linear-gradient(90deg,#000 ${wr * 116 - 14}%,transparent ${wr * 116 - 8}%)`, maskImage: `linear-gradient(90deg,#000 ${wr * 116 - 14}%,transparent ${wr * 116 - 8}%)`}}>
          Research question
        </div>
      </div>

      {/* 芯片 */}
      <div style={{position: "absolute", left: 1500 + hx, top: 300 + hy + bob, width: 260, height: 260, transform: `scale(${1 + cBump})`, filter: "drop-shadow(0 22px 16px rgba(30,25,15,0.25))"}}>
        <Img src={staticFile("parts/chip_c.png")} style={{position: "absolute", width: 260, height: 260,
             WebkitMaskImage: `radial-gradient(circle at 50% 0%,#000 ${cr - 6}%,transparent ${cr}%)`, maskImage: `radial-gradient(circle at 50% 0%,#000 ${cr - 6}%,transparent ${cr}%)`}} />
        <Img src={staticFile("parts/chip_l.png")} style={{position: "absolute", width: 260, height: 260, opacity: 1 - cc,
             WebkitMaskImage: `linear-gradient(90deg,#000 ${cl * 112 - 11}%,transparent ${cl * 112 - 6}%)`, maskImage: `linear-gradient(90deg,#000 ${cl * 112 - 11}%,transparent ${cl * 112 - 6}%)`}} />
      </div>
      <Tag n="13" x={1790 + hx} y={330 + hy + bob} at={cAt + 24} f={f} />
      <div style={{position: "absolute", left: 1460 + hx, top: 566 + hy + bob, width: 340, textAlign: "center", font: "40px Hand", color: SOFT, opacity: span(f, W[9].f0, W[9].f0 + 10)}}>
        computer-aided methods
      </div>

      {/* 箭头：方法帮到人 */}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, opacity: arOut}}>
        {ar > 0 && (
          <g fill="none" stroke={INK} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round">
            <path d={`M${1490 + hx},${430 + hy + bob} C${1320},${330} ${head[0] + 190},${head[1] - 40} ${head[0] + 14},${head[1]}`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - ar} />
            <g transform={`translate(${head[0]},${head[1]}) rotate(${168}) scale(${span(ar, 0.82, 1)})`}><path d="M-24,-13 L0,0 L-24,13" /></g>
          </g>
        )}
      </svg>

      {kShow && front && Key}
      <Tag n="22" x={kx + 128} y={ky - 70 + settle} at={W[12].f0 + 34} f={f} />
      <div style={{position: "absolute", left: kx + 96, top: ky + 8 + settle, width: 320, font: "40px Hand", color: INK, opacity: span(f, W[18].f0, W[18].f0 + 10)}}>
        a candidate
      </div>
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="OnCam202" component={Scene} durationInFrames={T.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
