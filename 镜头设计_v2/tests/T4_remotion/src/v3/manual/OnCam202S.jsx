// HKBU SCIE1007 课程作业的科普视频：出镜 2-02 简版（11-23，18 号文档 2-02 一节的"简版"）。
// 在 v9 样片 OnCam202.jsx（导演检查_20261118/7_样片_2-02_人出镜_v2_跟踪放稳.mp4）上只改参数，不重新设计：
//   ① 两个带圈编号 ⑬ ㉒ 删掉；② 芯片、钥匙放大到屏上高 ≥ 380 px（芯片外框 420 → 实体约 393 px；钥匙 1.9 倍、
//      转台帧收在接近竖直的 48–72 帧之间轻摆，屏上高约 400–437 px），位置跟着让开（芯片下移到牌子下面、钥匙浮在手的右上方，
//      底边不进 y > 930 的字幕区）；③ 背景白纱去掉，大板压暗到整段平均亮度和 1-03 一样（约 0.61）。
// 段长照 master_v2：666 帧。素材只有 639 帧，master 里词比素材晚 4 帧（段帧 = 素材帧 + 4）；
//   段首 4 帧、段尾 23 帧没有素材，用来回放（4,3,2,1 / 637,636,…），每帧都是真实素材帧，不冻结、不变速、不混帧。
// 声音：2-02.wav 前面垫 4 帧静音、尾巴垫到 11.1 秒，由 ffmpeg 合成时做（--sequence 不出声音）。
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/manual/OnCam202S.jsx OnCam202S <帧目录> --sequence --image-format=png --public-dir=<映射/_cache/oc202/public>
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, Img, Sequence, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import T from "./track_2-02.json";

const PAPER = "#EDE9DF", INK = "#1F1E1C", SOFT = "#6E6B63";
const LEN = 666, OFF = 4;                       // master_v2 的段长；段帧 = 素材帧 + OFF
const BG_BRIGHT = 0.87;                         // 大板压暗：第一遍 0.80 出片量得整段 0.570（1-03 是 0.607），抬到 0.87
const CHIP = 420;                               // 芯片外框边长（贴图实体占 654/699 → 屏上约 393 px）
const KS = 1.9;                                 // 钥匙在讲解位和手上方的缩放（转台 48–72 帧实体高 202–230 → 屏上 ≥ 384 px）
const W = Object.fromEntries(T.words.map((w, i) => [i + 1, w]));
const ease = Easing.bezier(0.33, 0, 0.2, 1);
const out = Easing.out(Easing.cubic);
const io = Easing.inOut(Easing.cubic);
const span = (f, a, b, fn = (x) => x) => (f <= a ? 0 : f >= b ? 1 : fn((f - a) / Math.max(1, b - a)));
const mix = (a, b, p) => a + (b - a) * p;
const NSRC = T.len_f;                                                   // 639
const mirror = (s) => (s < 0 ? -s : s > NSRC - 1 ? 2 * (NSRC - 1) - s : s);   // 素材外的帧来回放

const fh = typeof window !== "undefined" ? delayRender("fonts") : null;
if (typeof window !== "undefined") {
  Promise.all([["Serif", "InstrumentSerif-Regular.ttf", "normal"], ["Serif", "InstrumentSerif-Italic.ttf", "italic"], ["Hand", "Caveat.ttf", "normal"]]
    .map(([n, file, st]) => new FontFace(n, `url(${staticFile("fonts/" + file)})`, {style: st}).load().then((x) => document.fonts.add(x))))
    .then(() => continueRender(fh)).catch(() => continueRender(fh));
}

const SC = 1728 / T.src[0], PX = -301, PY = 108;
const at = (arr, f) => {
  const n = arr.length, c = Math.max(0, Math.min(n - 1, f));
  const g = (i) => { let j = i; while (j < n - 1 && !arr[j]) j++; while (j > 0 && !arr[j]) j--; return arr[j]; };
  const a = g(Math.floor(c)), b = g(Math.ceil(c)), t = c - Math.floor(c);
  return [mix(a[0], b[0], t) * SC + PX, mix(a[1], b[1], t) * SC + PY];
};
const fill = (arr) => { const o = []; let last = arr.find(Boolean); for (const p of arr) { if (p) last = p; o.push(last); } return o; };
const gauss = (arr, sig) => { const a = fill(arr), n = a.length, R = Math.ceil(sig * 3), o = [];
  for (let i = 0; i < n; i++) { let x = 0, y = 0, w = 0; for (let k = -R; k <= R; k++) { const j = Math.max(0, Math.min(n - 1, i + k)), g = Math.exp(-(k * k) / (2 * sig * sig)); x += a[j][0] * g; y += a[j][1] * g; w += g; } o.push([x / w, y / w]); }
  return o; };
const NOSE_S = gauss(T.nose, 10), PALM_S = gauss(T.palm_l, 8), SH_S = gauss(T.shoulder_l, 14);
const PALM_M = (() => { const a = PALM_S.slice(T.words[13].f0); let x = 0, y = 0; for (const p of a) { x += p[0]; y += p[1]; } return [x / a.length, y / a.length]; })();
const FOLLOW = 0.6, HEAD = 0.2;
const NOSE0 = (() => { let x = 0, y = 0, n = 0; for (const p of T.nose) if (p) { x += p[0]; y += p[1]; n++; } return [(x / n) * SC + PX, (y / n) * SC + PY]; })();

const Scene = () => {
  const f = useCurrentFrame() - OFF;            // 素材时间（词帧都按素材写），可为负、可超过 638
  const m = mirror(f);                          // 画面和跟踪数据用的真实素材帧
  const nose = at(NOSE_S, m);
  const hx = (nose[0] - NOSE0[0]) * HEAD, hy = (nose[1] - NOSE0[1]) * HEAD;

  // ---- 字牌：research question（不动）----
  const pl = span(f, W[3].f0 - 2, W[3].f0 + 14, out);
  const plBump = f > W[3].f0 + 14 ? 0.03 * Math.exp(-(f - W[3].f0 - 14) / 5) * Math.cos((f - W[3].f0 - 14) / 3) : 0;
  const wr = span(f, W[3].f0 + 4, W[4].f1);

  // ---- 芯片：computer-aided methods（放大到 420 外框，挪到牌子下面靠右）----
  const cAt = W[8].f0;
  const cl = span(f, cAt - 2, cAt + 10, out), cc = span(f, cAt + 3, cAt + 27, Easing.inOut(Easing.quad));
  const cr = cc * 150;
  const cBump = f > cAt + 27 ? 0.03 * Math.exp(-(f - cAt - 27) / 5) * Math.cos((f - cAt - 27) / 3.2) : 0;
  const bob = Math.sin(f / 31) * 5;
  const CX = 1440, CY = 256;                    // 芯片外框左上角：右沿 1860，下沿 676

  // ---- 钥匙：find 时从肩后出来，assess 时落到手的右上方并跟着手走 ----
  const sh = at(SH_S, m);
  const pr = at(PALM_S, m), pm = [PALM_M[0] * SC + PX, PALM_M[1] * SC + PY];
  const palm = [mix(pm[0], pr[0], FOLLOW), mix(pm[1], pr[1], FOLLOW)];
  const k0 = [sh[0] - 70, sh[1] + 40];
  const k1 = [1215 + hx, 452 + hy + Math.sin(f / 23) * 6];
  const k2 = [palm[0] + 170, palm[1] - 460 + Math.sin(f / 19) * 4];   // 放大后底边 ≤ 930，不进字幕区（贴图实体偏下 ~90 px，试渲量过）；离开人的肩
  const a = span(f, W[12].f0 - 6, W[12].f0 + 30, io);
  const b = span(f, W[14].f0 - 4, W[14].f0 + 34, io);
  const arcUp = Math.sin(Math.PI * a) * -70 + Math.sin(Math.PI * b) * -40;
  const kx = mix(mix(k0[0], k1[0], a), k2[0], b);
  const ky = mix(mix(k0[1], k1[1], a), k2[1], b) + arcUp;
  const ks = mix(mix(0.9, KS, a), KS, b);
  const kShow = f >= W[12].f0 - 6;
  const front = kx > 1190 || b > 0;
  const kf = String(Math.round(60 + 12 * Math.sin(f / 45))).padStart(4, "0");   // 转台收在接近竖直的一段轻摆，屏上高一直 ≥ 380
  const settle = f > W[14].f0 + 34 ? Math.exp(-(f - W[14].f0 - 34) / 7) * Math.cos((f - W[14].f0 - 34) / 3.4) * 10 : 0;
  const Key = (
    <Img src={staticFile(`key/${kf}.png`)} style={{position: "absolute", left: kx - 320, top: ky - 320 + settle, width: 640, height: 640,
         transform: `scale(${ks}) rotate(${mix(-24, 0, a) + mix(0, -8, b)}deg)`, filter: "drop-shadow(0 26px 18px rgba(60,40,10,0.28))"}} />
  );

  const ar = span(f, W[10].f0 - 2, W[11].f0 + 14, ease);
  const arOut = 1 - span(f, W[12].f0 + 20, W[12].f0 + 40);
  const head = [nose[0] + 210, nose[1] - 40];

  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Sequence from={OFF}><Audio src={staticFile("2-02.wav")} /></Sequence>
      <Img src={staticFile("bg.jpg")} style={{position: "absolute", width: 1920, height: 1080, filter: `brightness(${BG_BRIGHT})`}} />
      {/* 白纱去掉（18 的 1.9 G1：veil = 0） */}

      {kShow && !front && Key}
      <Img src={staticFile(`person/${String(m).padStart(4, "0")}.png`)} style={{position: "absolute", left: PX, top: PY, width: 1728, height: 972}} />

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
      <div style={{position: "absolute", left: CX + hx, top: CY + hy + bob, width: CHIP, height: CHIP, transform: `scale(${1 + cBump})`, filter: "drop-shadow(0 26px 18px rgba(30,25,15,0.28))"}}>
        <Img src={staticFile("parts/chip_c.png")} style={{position: "absolute", width: CHIP, height: CHIP,
             WebkitMaskImage: `radial-gradient(circle at 50% 0%,#000 ${cr - 6}%,transparent ${cr}%)`, maskImage: `radial-gradient(circle at 50% 0%,#000 ${cr - 6}%,transparent ${cr}%)`}} />
        <Img src={staticFile("parts/chip_l.png")} style={{position: "absolute", width: CHIP, height: CHIP, opacity: 1 - cc,
             WebkitMaskImage: `linear-gradient(90deg,#000 ${cl * 112 - 11}%,transparent ${cl * 112 - 6}%)`, maskImage: `linear-gradient(90deg,#000 ${cl * 112 - 11}%,transparent ${cl * 112 - 6}%)`}} />
      </div>
      <div style={{position: "absolute", left: CX + CHIP / 2 - 200 + hx, top: CY + CHIP + 8 + hy + bob, width: 400, textAlign: "center", font: "40px Hand", color: INK, opacity: span(f, W[9].f0, W[9].f0 + 10)}}>
        computer-aided methods
      </div>

      {/* 箭头：方法帮到人（起点跟着芯片挪到它的左沿中间） */}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, opacity: arOut}}>
        {ar > 0 && (
          <g fill="none" stroke={INK} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round">
            <path d={`M${CX - 10 + hx},${CY + CHIP / 2 + hy + bob} C${1300},${360} ${head[0] + 190},${head[1] - 40} ${head[0] + 14},${head[1]}`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - ar} />
            <g transform={`translate(${head[0]},${head[1]}) rotate(${168}) scale(${span(ar, 0.82, 1)})`}><path d="M-24,-13 L0,0 L-24,13" /></g>
          </g>
        )}
      </svg>

      {kShow && front && Key}
      <div style={{position: "absolute", left: kx + 240, top: ky + 170 + settle, width: 320, font: "40px Hand", color: INK, opacity: span(f, W[18].f0, W[18].f0 + 10)}}>
        a candidate
      </div>
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="OnCam202S" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
